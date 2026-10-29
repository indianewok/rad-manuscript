"""Publish the nine-column tool registry without discarding producer evidence.

The wide evidence tables remain the source of hashes, patches and limitations.
The command column contains shell syntax from recorded commands, never a
parameter summary presented as an executed command. Paths identify portable
repository or external-data locations; this module does not execute producers.
"""
import csv
import hashlib
import json
import re
import shlex
from pathlib import Path


FIELDS = ['analysis', 'dataset', 'tool', 'replicate', 'version',
          'source_commit', 'threads', 'chemistry', 'command']
UNAVAILABLE = 'unavailable: original expanded command was not recorded'
DATASET_LABELS = {'Measles-P7': 'P7', 'Measles-P8-WTA': 'P8', 'Measles-P8-VDJ-enriched': 'P8-enriched'}
CANONICAL_DATASETS = {label: dataset for dataset, label in DATASET_LABELS.items()}


def details_path_name(family):
    return {'124': 'figures_124_run_evidence.tsv',
            '3': 'figure_3_run_evidence.tsv',
            '567': 'figures_567_run_evidence.tsv'}[family]


def prepare_evidence_rows(rows, repo_root):
    """Distinguish original producer hashes from the deposited readable copies."""
    root = Path(repo_root)
    prepared = []
    for source in rows:
        row = dict(source)
        original = row.get('evidence_original_sha256', row.get('evidence_sha256', 'not_recorded'))
        first = row.get('evidence', '').split(';', 1)[0].strip()
        path = root/first
        row['evidence_original_sha256'] = original
        row['evidence_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest() if first and path.is_file() else 'not_available'
        prepared.append(row)
    return prepared


def _text(value):
    return str(value or '').strip()


def _commit(value):
    match = re.search(r'(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])', _text(value))
    return match.group() if match else 'not_recorded'


def _json_command(value):
    try:
        parsed = json.loads(value)
    except (ValueError, TypeError):
        return None
    if isinstance(parsed, str):
        return parsed
    if isinstance(parsed, list) and parsed and all(isinstance(x, str) for x in parsed):
        return shlex.join(parsed)
    if isinstance(parsed, list) and parsed and all(
            isinstance(x, list) and x and all(isinstance(y, str) for y in x)
            for x in parsed):
        return ' | '.join(shlex.join(x) for x in parsed)
    return None


def _lines(value):
    # Some receipts stored literal backslash-n separators rather than newlines.
    value = re.sub(r'\\{1,2}n(?=(?:exec |set |pigz |/usr/|$))', '\n', value)
    value = re.sub(r'\\\s*\n\s*', ' ', value)
    return [line.strip() for line in value.splitlines() if line.strip()]


def _direct(value):
    value = _text(value)
    parsed = _json_command(value)
    if parsed is not None:
        value = parsed
    if value.startswith('Command being timed:'):
        value = value.split(':', 1)[1].strip().strip('"')
    if not value:
        return None
    if any(term in value.lower() for term in (
            'unrecovered', 'not recorded', 'intended wrapper:', 'exact executed',
            'max_edit_distance=', '->', 'direct pair-only eligibility:',
            'native_scan_wl', 'documented_unknown', 'native_expect_cells',
            'complete pertool paths', 'scTransform vst.'.lower())):
        return None
    if re.search(r'\b(?:INPUT|SELECTED|THREADS|PREFIX|RAW_FASTQ(?:_GZ)?)\b', value):
        return None
    if value.startswith(('--', '-d ', 'scan-wl', 'native ', 'expect_cells=', 'kit=')):
        return None
    lines = [line for line in _lines(value)
             if not line.startswith(('#', 'set -', 'umask '))]
    if not lines:
        return None
    if len(lines) > 2 or any(re.match(r'\w+=', line) and len(shlex.split(line)) == 1 for line in lines):
        return None
    return '; '.join(lines)


def _variables(script, overrides=None):
    values = dict(overrides or {})
    for line in _lines(script):
        match = re.fullmatch(r'(?:local )?([A-Za-z_]\w*)=(.+)', line)
        if not match or match[1] in values or '$(' in match[2]:
            continue
        value = match[2].strip().strip('"').strip("'")
        if not re.search(r'\s(?:>|\||&&)', value):
            values[match[1]] = value
    pattern = re.compile(r'\$\{([A-Za-z_]\w*)\}|\$([A-Za-z_]\w*)\b')
    # Resolve variable values before inserting them beside literal suffixes.
    # Otherwise ${prefix}_counts can turn a terminal $sample into the different
    # (unrecorded) variable $sample_counts.
    for _ in range(15):
        resolved = {key: pattern.sub(lambda m: values.get(m[1] or m[2], m[0]), value)
                    for key, value in values.items()}
        if resolved == values:
            break
        values = resolved
    def expand(text):
        for _ in range(15):
            new = pattern.sub(lambda m: values.get(m[1] or m[2], m[0]), text)
            if new == text:
                break
            text = new
        return text
    return expand


def _script_commands(script, tool, overrides=None, flank=None, discovery_only=False):
    """Extract recorded CLI lines; expand only literal saved assignments."""
    expand = _variables(script, overrides)
    aliases = {'RAD': ('rad', 'RAD'), 'BLAZE': ('blaze', 'BLAZE'),
               'Flexiplex': ('flex', 'FLEX', 'flexiplex', 'FLEXIPLEX',
                             'flex_filter', 'FLEX_FILTER', 'filter')}.get(tool, (tool,))
    commands = []
    for line in _lines(script):
        if line.startswith(('#', 'printf ', 'echo ', 'status ', 'test ', 'touch ',
                            'if ', 'elif ', 'while ', 'for ', 'export ', 'exec 9')):
            continue
        if re.match(r'(?:local )?[A-Za-z_]\w*=', line) and not re.search(r'\s(?:/usr/bin/time|\S+/bin/|"?\$)', line):
            continue
        if not any(re.search(r'\$\{?'+re.escape(alias)+r'\b', line) for alias in aliases):
            # Commands with literal executable paths rather than variables.
            if not any(re.search(r'(?:/|\b)'+re.escape(alias)+r'(?:[ _-]|$)', line)
                       for alias in aliases if alias.islower()):
                continue
        expanded = expand(line)
        if discovery_only and tool == 'RAD' and ' demux ' in expanded:
            continue
        if discovery_only and tool == 'Flexiplex' and ('-k ' in expanded or 'flex_audit' in line):
            continue
        if flank is not None and re.search(r'-f\s+0\b', expanded):
            continue
        if re.search(r'\$\{?[A-Za-z_]\w*', expanded) or re.search(r'/\S*\$[1-9]', expanded):
            continue
        if not any(x in expanded for x in (' scan-wl ', ' demux ', '--expect-cells',
                                           '--whitelist', '-d 10x', 'flexiplex-filter', 'flexiplex_filter')):
            continue
        commands.append(expanded)
    return '; '.join(dict.fromkeys(commands)) or None


def _evidence_command(row, root):
    tool = row.get('tool', row.get('component', ''))
    run = row.get('producing_run', '')
    parts = run.split('|', 1)
    run = CANONICAL_DATASETS.get(parts[0], parts[0]) + ('|' + parts[1] if len(parts) == 2 else '')
    candidates = [_text(x) for x in row.get('evidence', '').split(';')]
    discovery = row.get('experiment', '').startswith('barcode discovery')
    if tool == 'CellSNP-lite / Vireo':
        commands = []
        for name in ('executed_cellsnp_commands.tsv', 'executed_vireo_commands.tsv'):
            path = root/'source_data/figure_06'/name
            if path.is_file():
                with path.open() as handle:
                    commands.extend(_direct(r['command']) for r in csv.DictReader(handle, delimiter='\t'))
        return '; '.join(c for c in commands if c) or None
    if tool == 'FLAMES / minimap2 / samtools':
        commands = []
        for name in ('RAD', 'BLAZE', 'Flexiplex'):
            path = root/'source_data/figure_06'/(name+'_alignment_header.sam')
            if path.is_file():
                for line in path.read_text().splitlines():
                    if line.startswith('@PG\t'):
                        fields = dict(x.split(':', 1) for x in line.split('\t')[1:] if ':' in x)
                        if fields.get('PN') in ('minimap2', 'samtools') and fields.get('CL'):
                            commands.append(fields['CL'])
        return '; '.join(commands) or None
    # The extended-quality replay has an explicitly retained batch command.
    if row.get('figure') == '02' and 'exact executed replay source' in row.get('exact_command_or_recorded_settings', ''):
        path = root/'source_data/figure_02/producing_evidence/discovery_blaze_replay_commands.txt'
        if path.is_file():
            for line in path.read_text().splitlines():
                if line.startswith('PYTHONDONTWRITEBYTECODE='):
                    return line.strip()
    for name in candidates:
        path = root/name
        if not path.is_file() or path.suffix not in ('.sh', '.txt', '.md'):
            continue
        text = path.read_text()
        if path.name.endswith('_command.txt') or path.name.endswith('_command.sh'):
            found = _direct(text)
            if found:
                return found
        if path.suffix == '.sh':
            if text.startswith('# RAGE-seq four-tool benchmark commands'):
                # This receipt is Markdown despite its copied .sh extension.
                section = re.search(r'^## '+re.escape(tool)+r'\n(.*?)(?=^## |\Z)', text, re.M|re.S)
                if section:
                    blocks = re.findall(r'```bash\n(.*?)```', section[1], re.S)
                    if blocks and tool != 'Flexiplex':
                        lines = _lines(blocks[0])
                        if discovery and tool == 'RAD':
                            lines = [line for line in lines if ' scan-wl ' in line]
                        return '; '.join(lines)
                    if blocks and tool == 'Flexiplex':
                        # The receipt explicitly documents f0->f8 substitutions.
                        selected = blocks[0].replace('-f 0', '-f 8').replace('f0_', 'f8_')
                        logical = _lines(selected)
                        joined = []
                        for line in logical:
                            if joined and joined[-1].endswith('|'):
                                joined[-1] += ' '+line
                            else:
                                joined.append(line)
                        return '; '.join(line for line in joined if not discovery or '-k ' not in line)
                continue
            overrides = {}
            if 'PromethION_iPSC|Flexiplex' == run:
                # The selected row is the f8 arm; its filter runs after f8
                # discovery, not the otherwise identical earlier f0 filter.
                header = text.split('while true;', 1)[0]
                marker = text.find('flexiplex-f8-discovery')
                if marker >= 0:
                    text = header+'\n'+text[text.find('\n', marker)+1:]
            if 'RAGEseq-TNBC-LN|' in run:
                header = text.split('run_rad() {', 1)[0]
                if tool == 'BLAZE':
                    match = re.search(r'run_blaze\(\) \{(.*?)\n\}', text, re.S)
                    if match:
                        body = match[1].replace('"${overwrite_args[@]}"', '--overwrite')
                        overrides = dict(output_dir='${ROOT}/runs/blaze', expect_cells='10433')
                        return _script_commands(header+'\n'+body, tool, overrides, discovery_only=discovery)
                if tool == 'Flexiplex':
                    match = re.search(r'run_flex\(\) \{(.*?)\n\}', text, re.S)
                    if match:
                        return _script_commands(header+'\n'+match[1], tool, dict(error_setting='8'), discovery_only=discovery)
            if 'Measles-P7|' in run or 'Measles-P8-VDJ-enriched|' in run:
                sample = 'p7' if 'Measles-P7|' in run else 'p8'
                case = re.search(r'^    '+sample+r'\)\n(.*?)        ;;', text, re.M|re.S)
                if case:
                    for key, val in re.findall(r'^\s*([A-Za-z_]\w*)=(.+)$', case[1], re.M):
                        overrides[key] = val.strip().strip('"')
                overrides['sample'] = sample
            found = _script_commands(text, tool, overrides, discovery_only=discovery)
            if found:
                return found
    return None


def _command(row, root):
    if row.get('command'):
        return _text(row['command'])
    value = row.get('argv', row.get('exact_command_or_recorded_settings', ''))
    # Desktop installation location is represented by the same documented root
    # as the deposited LR-Split checkpoint metadata.
    value = re.sub(r'/[U]sers/[^/]+/Desktop/rad/', 'external_data/workstation/', value)
    direct = _direct(value)
    if direct:
        return direct
    recovered = _evidence_command(row, root)
    return recovered or UNAVAILABLE


def project_parameters(rows, family, repo_root):
    """Return the public columns; never guess missing argv or build identity."""
    root = Path(repo_root)
    output = []
    for row in rows:
        if all(key in row for key in FIELDS):
            output.append({key: row[key] for key in FIELDS})
            continue
        if family == '3':
            result = {key: row.get(key, 'not_recorded') for key in FIELDS}
            result['source_commit'] = _commit(row.get('source_commit'))
            if re.fullmatch('[0-9a-f]{40}', result['version']):
                result['version'] = '1.0.2'
        elif family == '124':
            parts = row['producing_run'].split('|')
            analysis = 'Figure '+str(int(row['figure']))+' '+row['experiment']
            if row['experiment'] == 'complete-input timing':
                analysis += ' / '+parts[-1]
            dataset = DATASET_LABELS.get(parts[0], parts[0]) if row['figure'] == '04' else parts[0]
            if row['figure'] == '02' and len(parts) == 4:
                dataset = 'ScTagger-'+parts[0]+' / '+parts[1]+' / '+parts[2]
            result = dict(analysis=analysis, dataset=dataset, tool=row['tool'],
                          replicate=parts[3] if row['experiment'] == 'complete-input timing' else 'not_applicable',
                          version=_text(row['version']), source_commit=_commit(row['commit_or_build']),
                          threads=row['threads'], chemistry=row['chemistry_layout'])
        elif family == '567':
            result = dict(analysis='Figure '+str(int(row['figure']))+' '+row['panels'],
                          dataset='RAGE-seq ERR3268991' if 'receptor' in row['panels'] else
                          ('LR-Split-seq' if 'LR-Split' in row['panels'] else 'LongBench SN-ONT'),
                          tool=row['component'], replicate='not_applicable', version=row['version'],
                          source_commit=_commit(row['commit']), threads=row['threads'],
                          chemistry=row['chemistry_layout'])
        else:
            raise ValueError('Unknown parameter-table family: '+str(family))
        result['command'] = _command(row, root)
        result['version'] = re.sub(r'^rad\s+', '', _text(result['version']), flags=re.I)
        result['chemistry'] = re.sub(
            r';?\s*(?:RAD )?(?:exact )?layout SHA256\s*[0-9a-f]{64}',
            '', result['chemistry']).strip(' ;')
        if family == '567' and row['component'] == 'RAD' and 'candidate receptor' in row['panels']:
            result['threads'] = 'not_recorded'
        if family == '124' and row['tool'] == 'BLAZE' and row['producing_run'].startswith(
                ('Measles-P7|', 'Measles-P8-VDJ-enriched|', 'P7|', 'P8-enriched|')):
            # The executed run_sample.sh sets threads=24. Older summary rows
            # incorrectly said 32; their original values remain in evidence.
            if re.search(r'--threads\s+"?24\b', result['command']):
                result['threads'] = '24'
        output.append({key: result[key] for key in FIELDS})
    return output
