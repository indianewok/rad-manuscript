#!/usr/bin/env python3
"""Show recorded Figure4 tool flags without installation/storage wrappers."""
import argparse
import csv
from pathlib import Path, PurePosixPath
import re
import shlex

DATASET_LABELS = {'Measles-P7': 'P7', 'Measles-P8-WTA': 'P8', 'Measles-P8-VDJ-enriched': 'P8-enriched'}


def display_dataset(dataset):
    return DATASET_LABELS.get(dataset, dataset)


FIELDS = ['dataset', 'tool', 'version', 'command']
SEVEN_FIELDS = ['dataset', 'tool', 'version', 'source_commit', 'threads', 'chemistry', 'command']
LEGACY_FIELDS = ['analysis', 'dataset', 'tool', 'replicate', 'version',
                 'source_commit', 'threads', 'chemistry', 'command']
OPERATORS = {';', '&&', '||', '|', '&'}
REDIRECTS = {'>', '>>', '<', '<<', '>&', '&>'}


def shell_tokens(text):
    lexer = shlex.shlex(text, posix=True, punctuation_chars='|;&<>')
    lexer.whitespace_split = True
    lexer.commenters = ''
    return list(lexer)


def command_segments(tokens):
    """Unwrap saved bash -c argv by substitution only; never execute a shell."""
    segments, segment = [], []
    for token in [*tokens, ';']:
        if token in OPERATORS:
            if segment:
                segments.append(segment)
                segment = []
        else:
            segment.append(token)
    output = []
    for segment in segments:
        redirect = next((n for n, token in enumerate(segment) if token in REDIRECTS), len(segment))
        redirected = redirect < len(segment)
        segment = segment[:redirect]
        if redirected and segment and segment[-1] in {'1', '2'}:
            segment = segment[:-1]
        bash = next((n for n, token in enumerate(segment)
                     if PurePosixPath(token).name == 'bash'), None)
        if bash is not None and '-c' in segment[bash + 1:]:
            index = segment.index('-c', bash + 1)
            if index + 1 >= len(segment):
                raise ValueError('Saved bash invocation lacks its command string')
            arguments = segment[index + 2:]
            body = shell_tokens(segment[index + 1])
            pattern = re.compile(r'\$(?:\{(\d+)\}|(\d+))')
            def expand(match):
                number = int(match[1] or match[2])
                if number >= len(arguments):
                    raise ValueError('Saved bash invocation lacks positional argument ' + str(number))
                return arguments[number]
            output.extend(command_segments([pattern.sub(expand, token) for token in body]))
        elif segment:
            output.append(segment)
    return output


def tool_commands(command, tool):
    """Return only the recorded software argv, excluding transport/wrappers."""
    if not command or command.strip().lower() in {'na', 'unrecovered', 'not_recorded'} or command.startswith('unavailable:'):
        return []
    commands = []
    for segment in command_segments(shell_tokens(command)):
        if segment[0] == "cd":
            continue
        for index, token in enumerate(segment):
            name = PurePosixPath(token).name
            prefix = None
            if tool == 'RAD' and (name == 'rad' or name.startswith('rad_')):
                prefix = ['rad']
            elif tool == 'BLAZE' and name == 'blaze':
                prefix = ['blaze']
            elif tool == 'BLAZE' and name == 'reconstruct_expect_sweep.py':
                prefix = ['python', name]
            elif tool == 'Flexiplex':
                if name in {'flexiplex', 'flexiplex-linux', 'flexiplex-audit'}:
                    prefix = ['flexiplex']
                elif name == 'flexiplex-filter' or (name == 'main.py' and 'flexiplex' in token):
                    prefix = ['flexiplex-filter']
                elif name == 'run_flexiplex_selector.py':
                    prefix = ['python', name]
            if prefix is not None:
                args = segment[index + 1:]
                if any(re.search(r'\$[A-Za-z0-9{]', value) for value in args):
                    raise ValueError('Saved tool arguments contain unresolved variables')
                commands.append(prefix + args)
                break
    if not commands:
        raise ValueError('No recorded ' + tool + ' invocation found')
    return commands


def shorten(value):
    """Keep scientific values verbatim; use basenames for recorded file paths."""
    if '=' in value and value.startswith('--'):
        flag, item = value.split('=', 1)
        return flag + '=' + shorten(item)
    return PurePosixPath(value).name if '/' in value else value


def compact_command(command, tool, version=''):
    commands = tool_commands(command, tool)
    return '; '.join(shlex.join(display_argv(argv, version)) for argv in commands) or 'NA'


def display_argv(argv, version=''):
    """Keep recorded tool options; omit file inputs and output destinations."""
    io_flags = {'--input', '-i', '--output-prefix', '--output-fastq', '--outfile',
                '--output', '--counts', '--raw-bc', '--cellranger-reference',
                '--preserved-design-whitelist', '--output-root'}
    if argv[0] == 'rad':
        io_flags.add('-o')
    elif argv[0] == 'flexiplex':
        io_flags.add('-n')
    elif argv[0] == 'flexiplex-filter':
        io_flags.add('-o')
    boolean_flags = {'--minimal_stdout', '--no-demultiplexing', '--no-emtpy-drops',
                     '--no-empty-drops', '--overwrite', '--verbose', '-v', '--hs-bcs'}
    tool = argv[0]
    io_flags.add('--threads')
    if tool == 'rad':
        io_flags.update({'-t', '--chunk-size', '--chunks', '-k'})
    elif tool == 'flexiplex':
        io_flags.add('-p')
    defaults = {}
    if tool == 'rad':
        defaults = {'--max-error': '0.3', '-e': '0.3', '--barcode-length': '16', '-n': '16', '--left-margin': '0', '--right-margin': '0'}
    elif tool == 'blaze':
        defaults = {'--minQ': '15', '--max-edit-distance': '2'}
        if re.search(r'2\.(?:5|6)\.', version):
            defaults.update({'--10x-kit-version': '3v3', '--kit-version': '3v3', '--umi-len': '12', '--batch-size': '1000'})
    elif tool == 'flexiplex' and re.search(r'1\.02\.(?:6|7)(?:\D|$)', version):
        defaults = {'-e': '2', '-f': '8', '-d': '10x3v3'}
    prefix = 2 if argv[0] == 'python' else 1
    output = argv[:prefix]
    index = prefix
    while index < len(argv):
        flag = argv[index]
        if flag == 'scan-wl' and argv[0] == 'rad':
            output.append(flag);index += 1;continue
        if tool == 'rad' and flag == '--hs-bcs':
            index += 1;continue
        if flag in defaults and index+1 < len(argv) and argv[index+1] == defaults[flag]:
            index += 2;continue
        if any(flag == key+'='+value for key, value in defaults.items()):
            index += 1;continue
        if flag in io_flags:
            index += 2;continue
        if any(flag.startswith(key+'=') for key in io_flags):
            index += 1;continue
        if flag.startswith('-'):
            output.append(shorten(flag))
            if flag not in boolean_flags and '=' not in flag and index+1 < len(argv) and not argv[index+1].startswith('-'):
                output.append(shorten(argv[index+1]));index += 1
        index += 1
    return output



def compact_chemistry(dataset, chemistry, same_input_chemistry=''):
    """Name the input library chemistry; retain tool-specific presets in flags."""
    if dataset.startswith('section') or dataset == 'LeBrigand-MOB':
        return 'Visium'
    for value in [chemistry, same_input_chemistry]:
        if re.search(r'10x[_ ]?3v2', value, re.I):
            return '10x3v2'
        if re.search(r'10x[_ ]?3v3', value, re.I):
            return '10x3v3'
        if 'visium' in value.lower():
            return 'Visium'
    return 'not_recorded'


def recorded_threads(command, tool):
    """Move an explicitly recorded thread count into its dedicated column."""
    flags = {'--threads'}
    if tool == 'RAD': flags.add('-t')
    if tool == 'Flexiplex': flags.add('-p')
    values = set()
    for argv in tool_commands(command, tool):
        for index, token in enumerate(argv):
            if token in flags and index+1 < len(argv):
                values.add(argv[index+1])
            elif any(token.startswith(flag+'=') for flag in flags):
                values.add(token.split('=',1)[1])
    if len(values)>1:
        raise ValueError('Conflicting recorded thread counts')
    return next(iter(values)) if values else None


def display_version(value):
    """Keep the software version alone when projecting a supported input table."""
    match = re.search(r'\b\d+\.\d+(?:\.\d+)+(?:[a-z]+\d*)?\b', value)
    return match.group(0) if match else 'NA'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('source_data/figure_04/tool_parameters.tsv'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.input.open(newline='') as handle:
        reader = csv.DictReader(handle, delimiter='\t')
        if reader.fieldnames not in (FIELDS, SEVEN_FIELDS, LEGACY_FIELDS):
            raise ValueError('Require the four-column table or a seven/nine-column input format')
        rows = list(reader)
    projected = []
    for source in rows:
        row = {key: source[key] for key in FIELDS}
        row['dataset'] = display_dataset(row['dataset'])
        row['version'] = display_version(row['version'])
        row['command'] = compact_command(row['command'], row['tool'], row['version'])
        projected.append(row)
    rows = projected
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, FIELDS, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    print('Wrote', len(rows), 'tool-parameter rows:', args.output)


if __name__ == '__main__':
    main()
