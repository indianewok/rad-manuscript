#!/usr/bin/env python3
"""Verify source-table-only rendering in an empty temporary directory.

This is a validation check, not the reader's analysis entry point. Use the
figure walkthroughs for the individual transformations. Linux strace records
file access so accidental reads of the HPC raw-data project are detectable.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
from published_files import published_source_files


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()



def is_ancestor_metadata(line, ancestors):
    """Allow only metadata lookups of exact runtime-directory ancestors.

    Path.resolve() stats directory ancestors. It does not read their contents;
    opens and metadata lookups of unrelated paths still fail the isolation check.
    """
    match = re.search(r'^(?:\d+\s+|\[pid\s+\d+\]\s+)?(?:lstat|stat|newfstatat|readlink|readlinkat)\((.*)', line)
    if not match:
        return False
    quoted = re.search(r'"(?:\\.|[^"\\])*"', match[1])
    if not quoted:
        return False
    try:
        path = json.loads(quoted[0])
    except ValueError:
        return False
    return path in ancestors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', required=True, type=Path)
    parser.add_argument('--groups', nargs='+', choices=['124','3','5','567'], default=['124','3','5','567'])
    parser.add_argument('--promote', action='store_true', help='Copy all successfully verified exports into the repository figures directory.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    work = Path(tempfile.mkdtemp(prefix='rad-source-only-render-'))
    source_files = published_source_files(root)
    for source in source_files:
        destination = work/source.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    (work / 'validation').mkdir()
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'MPLCONFIGDIR': str(work / 'matplotlib'),
           'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
    commands = {
        '124': [str(args.python), str(root / 'scripts/revision/figures_124.py'), 'render', '--output-root', str(work)],
        '567': [str(args.python), str(root / 'scripts/revision/figures_567.py'), 'render', '--output-root', str(work)],
        '3': [str(args.python), str(root / 'scripts/revision/figure_3.py'), 'render', '--output', str(work / 'source_data/figure_03'), '--figures', str(work / 'figures/figure_03')],
        '5': [str(args.python), str(root / 'scripts/figure_05/render_candidate_counts.py'),
              '--input', str(work/'source_data/figure_05/candidate_receptor_totals.tsv'),
              '--splitseq-input', str(work/'source_data/figure_05/splitseq_reads_umis_568.tsv'),
              '--splitseq-summary', str(work/'source_data/figure_05/splitseq_summary.tsv'),
              '--output-dir', str(work/'figures/figure_05')],
    }
    def portable(value):
        if isinstance(value, str):
            if value == str(args.python):
                return 'python'
            value = value.replace(str(work), 'validation/isolated_render').replace(str(root) + '/', '')
            value = value.replace(str(args.python.absolute().parent.parent), '<render-environment>')
            return re.sub(r'/(?:dartfs|scratch(?:-nfs)?|home|Users|Volumes)/[^\s\"\']*', '<external-path>', value)
        if isinstance(value, list):
            return [portable(item) for item in value]
        if isinstance(value, dict):
            return {key: portable(item) for key, item in value.items()}
        return value

    reports = []
    for group in args.groups:
        trace = work / ('access_' + group + '.strace')
        log = work / ('render_' + group + '.log')
        argv = ['strace', '-f', '-s', '4096', '-e', 'trace=file', '-o', str(trace)] + commands[group]
        with log.open('w') as handle:
            outcome = subprocess.run(argv, cwd=str(work), env=env, stdout=handle, stderr=subprocess.STDOUT)
        forbidden_roots = ('/rad_data/', '/' + 'scratch-nfs' + '/', '/' + 'Volumes' + '/',
                           str(root/'source_data'), str(root/'checkpoints'))
        environment_prefix = str(args.python.absolute().parent.parent)+'/'
        allowed_ancestors = {str(path) for directory in (work, args.python.absolute().parent.parent)
                             for path in directory.parents}
        forbidden = []
        for line in trace.read_text().splitlines():
            if is_ancestor_metadata(line, allowed_ancestors):
                continue
            local_line = line.replace(environment_prefix, '<render-environment>/')
            local_line = local_line.replace('"'+environment_prefix.rstrip('/')+'"', '"<render-environment>"')
            local_line = local_line.replace(str(work)+'/', '<isolated-work>/')
            local_line = local_line.replace('"'+str(work)+'"', '"<isolated-work>"')
            if any(prefix in line for prefix in forbidden_roots):
                forbidden.append(line)
            elif '/' + 'scratch' + '/' in local_line:
                forbidden.append(line)
        reports.append({'group': group, 'command': commands[group], 'exit_code': outcome.returncode,
                        'renderer_sha256': digest(Path(commands[group][1])),
                        'forbidden_project_reads': forbidden, 'log': str(log), 'trace': str(trace)})
        if outcome.returncode or forbidden:
            (root / 'validation/clean_render.json').write_text(json.dumps(portable({'status': 'failed', 'runs': reports}), indent=2) + '\n')
            raise SystemExit('Render isolation failed; inspect ' + str(log))
    files = [{'path': str(path.relative_to(work)), 'sha256': digest(path)}
             for path in sorted((work / 'figures').rglob('*')) if path.suffix in ('.png','.pdf','.svg')]
    if args.promote:
        for path in sorted((work/'figures').rglob('*')):
            if path.is_file():
                destination = root/path.relative_to(work)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(path), str(destination))
        for row in files:
            assert digest(root/row['path']) == row['sha256'], row['path']
    report = {'status': 'passed', 'scope': 'render only; no raw or matrix producer rerun',
              'temporary_tree': str(work), 'environment': env, 'runs': reports, 'exports': files,
              'promoted_verified_exports': args.promote,
              'source_files': [{'path': str(path.relative_to(work)), 'sha256': digest(path)}
                               for path in sorted((work/'source_data').rglob('*')) if path.is_file()],
              'script_sha256': digest(Path(__file__))}
    (root / 'validation/clean_render.json').write_text(json.dumps(portable(report), indent=2) + '\n')
    print('PASS: {} exports; no HPC raw/project inputs accessed'.format(len(files)))


if __name__ == '__main__':
    main()
