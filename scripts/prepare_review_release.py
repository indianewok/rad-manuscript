#!/usr/bin/env python3
"""Package the selected working tree for review, without publishing anything.

The archive uses an explicit allowlist, excludes ignored files and never includes
raw sequencing data, manuscript DOCX files, Git history or old recovery material.
Large validated checkpoints are a separate optional archive. Every member is
hashed and every tar member is read back to verify its content.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path
from published_files import published_source_files

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('data', 'docs', 'environments', 'figures', 'manifests', 'scripts',
               'source_data', 'validation', 'vendor')
FILES = ('README.md', 'SETUP.md', 'CITATION.cff', 'LICENSE', 'THIRD_PARTY_NOTICES.md', '.gitignore')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def package(paths, archive):
    if len(paths) != len(set(paths)):
        raise ValueError('Duplicate archive paths')
    entries = [dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=sha(p)) for p in paths]
    manifest = io.StringIO()
    writer = csv.DictWriter(manifest, fieldnames=('path','bytes','sha256'), delimiter='\t')
    writer.writeheader()
    writer.writerows(entries)
    encoded = manifest.getvalue().encode()
    with archive.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', compresslevel=1, mtime=0, filename='') as zipped:
        with tarfile.open(fileobj=zipped, mode='w|') as output:
            for entry, path in zip(entries, paths):
                info = tarfile.TarInfo('rad-manuscript/'+entry['path'])
                info.size = entry['bytes']
                info.mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
                with path.open('rb') as source:
                    output.addfile(info, source)
            info = tarfile.TarInfo('rad-manuscript/ARCHIVE_CONTENTS.tsv')
            info.size = len(encoded)
            info.mode = 0o644
            output.addfile(info, io.BytesIO(encoded))
    expected = {'rad-manuscript/'+e['path']: e['sha256'] for e in entries}
    expected['rad-manuscript/ARCHIVE_CONTENTS.tsv'] = hashlib.sha256(encoded).hexdigest()
    observed = set()
    with tarfile.open(str(archive), 'r:gz') as saved:
        for member in saved:
            if not member.isfile() or member.name not in expected:
                raise ValueError('Unexpected archive member '+member.name)
            if member.name in observed:
                raise ValueError('Duplicate archive member '+member.name)
            digest = hashlib.sha256()
            with saved.extractfile(member) as handle:
                for block in iter(lambda: handle.read(1024*1024), b''):
                    digest.update(block)
            assert digest.hexdigest() == expected[member.name], member.name
            observed.add(member.name)
    assert observed == set(expected)
    return dict(archive=str(archive), bytes=archive.stat().st_size, sha256=sha(archive),
                files=len(entries), verified_members=len(observed))


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=ROOT/'release_staging')
parser.add_argument('--include-checkpoints', action='store_true', help='Include separately indexed current Figure 1/3/5/6/7 checkpoints.')
parser.add_argument('--include-software', action='store_true', help='Include selected source archives for the raw RAGE run.')
parser.add_argument('--include-rage-order', action='store_true', help='Include the verified read-order checkpoint needed to reconstruct the selected RAGE input from ENA.')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
for filename in ('repository_links.json','data_inventory.json','manuscript_claims.json',
                 'figure_3_rage_complete.json','clean_render.json'):
    report = json.loads((ROOT/'validation'/filename).read_text())
    if report['status'] != 'passed':
        raise ValueError('Required current validation has not passed: '+filename)
render_report = json.loads((ROOT/'validation/clean_render.json').read_text())
if sha(ROOT/'scripts/check_render_isolation.py') != render_report['script_sha256']:
    raise ValueError('Isolation checker changed after clean rendering')
if {row['group'] for row in render_report['runs']} != {'124','3','5','567'}:
    raise ValueError('Clean rendering must cover every current figure group')
if not render_report.get('source_files'):
    raise ValueError('Clean rendering must record its source-table hashes')
current_sources = {str(p.relative_to(ROOT)) for p in published_source_files(ROOT)}
if current_sources != {row['path'] for row in render_report['source_files']}:
    raise ValueError('Source-data file inventory changed after clean rendering')
for row in render_report['source_files']:
    if sha(ROOT/row['path']) != row['sha256']:
        raise ValueError('Source changed after clean rendering: '+row['path'])
for row in render_report['runs']:
    if sha(ROOT/row['command'][1]) != row['renderer_sha256']:
        raise ValueError('Renderer changed after clean rendering: '+row['command'][1])
expected_exports = {row['path'] for row in render_report['exports']}
current_exports = {str(p.relative_to(ROOT)) for p in (ROOT/'figures').rglob('*')
                   if p.suffix in ('.png','.pdf','.svg')}
if current_exports != expected_exports:
    raise ValueError('Current figure exports differ from the complete clean-render inventory')
for row in render_report['exports']:
    if sha(ROOT/row['path']) != row['sha256']:
        raise ValueError('Current figure differs from verified export: '+row['path']+'; use clean rendering with --promote')
paths = [ROOT/name for name in FILES if (ROOT/name).is_file()]
for directory in DIRECTORIES:
    paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and not p.is_symlink())
paths = sorted(p for p in set(paths)
               if not p.is_relative_to(ROOT/'source_data') or str(p.relative_to(ROOT)) in current_sources)
relative = [str(p.relative_to(ROOT)) for p in paths]
ignored_result = subprocess.run(['git','check-ignore','--stdin'], input='\n'.join(relative)+'\n',
                                text=True, stdout=subprocess.PIPE, cwd=str(ROOT))
if ignored_result.returncode not in (0,1):
    raise RuntimeError('git check-ignore failed')
ignored = set(ignored_result.stdout.splitlines())
paths = [p for p in paths if str(p.relative_to(ROOT)) not in ignored]
for path in paths:
    if any(part in ('figure_2','figure_3','figure_4','figure_5','figure_3_prism_tables') for part in path.parts):
        raise ValueError('Superseded figure tree or mixed native extraction remains: '+str(path))
    if path.name.startswith('historical_rage'):
        raise ValueError('Superseded RAGE material remains: '+str(path))
    if any(path.name.lower().endswith(s) for s in ('.fastq','.fq','.fastq.gz','.fq.gz')):
        if not path.is_relative_to(ROOT/'data/examples'):
            raise ValueError('Sequencing reads outside bounded examples: '+str(path))
    if path.suffix.lower() in ('.rdata','.rds','.docx','.bam','.bai','.prism'):
        raise ValueError('Review code archive contains excluded payload: '+str(path))
    if '__pycache__' in path.parts or path.suffix == '.pyc':
        raise ValueError('Python cache must be ignored: '+str(path))
result = dict(status='review only; unpublished', archives=[package(paths, args.output/'rad-manuscript-current.tar.gz')])
flex_paths = [p for p in paths if p.is_relative_to(ROOT/'vendor/flexiplex-audit')]
flex_paths += [p for p in (ROOT/'THIRD_PARTY_NOTICES.md', ROOT/'LICENSE',
                          ROOT/'validation/software/flexiplex_audit_build.json') if p.is_file()]
result['archives'].append(package(sorted(flex_paths), args.output/'flexiplex-1.02.6-rad-audit.1.tar.gz'))
if args.include_checkpoints:
    rage_rows = list(csv.DictReader((ROOT/'manifests/figure_03_staged_checkpoints.tsv').open(), delimiter='\t'))
    rage_paths = []
    for row in rage_rows:
        path = (ROOT/row['path']).resolve()
        path.relative_to(ROOT/'checkpoints/figure_03')
        if sha(path) != row['sha256']:
            raise ValueError('Selected RAGE audit checkpoint changed: '+row['path'])
        rage_paths.append(path)
    result['archives'].append(package(sorted(rage_paths), args.output/'rad-manuscript-checkpoints-03.tar.gz'))
    splitseq_rows = list(csv.DictReader((ROOT/'manifests/figure_05_staged_checkpoints.tsv').open(), delimiter='\t'))
    splitseq_paths = []
    for row in splitseq_rows:
        path = (ROOT/row['path']).resolve()
        path.relative_to(ROOT/'checkpoints/figure_05')
        if sha(path) != row['sha256']:
            raise ValueError('Selected Figure 5 checkpoint changed: '+row['path'])
        splitseq_paths.append(path)
    result['archives'].append(package(sorted(splitseq_paths), args.output/'rad-manuscript-checkpoints-05.tar.gz'))
    index = ROOT/'manifests/figures_567_staged_checkpoints.tsv'
    with index.open() as handle:
        rows = list(csv.DictReader(handle, delimiter='\t'))
    checkpoints = []
    for row in rows:
        key = next(k for k in ('staged_path','destination','path') if k in row)
        path = Path(row[key])
        if not path.is_absolute():
            path = ROOT/path
        path = path.resolve()
        path.relative_to(ROOT/'checkpoints')
        assert path.is_file()
        if 'sha256' in row:
            assert sha(path) == row['sha256'], str(path)
        checkpoints.append(path)
    result['archives'].append(package(sorted(checkpoints), args.output/'rad-manuscript-checkpoints-06-07.tar.gz'))
    hd_rows = list(csv.DictReader((ROOT/'manifests/figure_01_staged_checkpoints.tsv').open(), delimiter='\t'))
    hd_paths = []
    for row in hd_rows:
        path = (ROOT/row['path']).resolve()
        path.relative_to(ROOT/'checkpoints/figure_01')
        assert sha(path) == row['sha256'], str(path)
        hd_paths.append(path)
    result['archives'].append(package(sorted(hd_paths), args.output/'rad-manuscript-hd-lineage-under-review.tar.gz'))
if args.include_software:
    rows = list(csv.DictReader((ROOT/'manifests/figure_3_software_archives.tsv').open(), delimiter='\t'))
    paths = []
    for row in rows:
        path = (ROOT/row['path']).resolve()
        path.relative_to(ROOT/'checkpoints/software')
        assert sha(path) == row['sha256'], str(path)
        paths.append(path)
    result['archives'].append(package(sorted(paths), args.output/'rad-manuscript-rage-software.tar.gz'))
if args.include_rage_order:
    identity_path = ROOT/'checkpoints/figure_03/rage_matched/counts/input_id_validation.json'
    identity = json.loads(identity_path.read_text())
    comparison_path = ROOT/'validation/rage_public_payload_comparison.json'
    comparison = json.loads(comparison_path.read_text())
    if identity['status'] != 'passed' or comparison['status'] != 'passed':
        raise ValueError('Complete selected/public RAGE input verification must pass before packaging read order')
    if not comparison.get('full_ordered_stream_verified') or not comparison.get('complete_unique_ID_set_and_payload_identity'):
        raise ValueError('RAGE public comparison did not verify the full input')
    for key in ('records', 'sequence_bases', 'canonical_record_sha256',
                'sequence_quality_order_sha256', 'original_id_order_sha256'):
        if comparison['reconstructed_identity'][key] != identity[key]:
            raise ValueError('Public RAGE comparison is for a different selected input: '+key)
    if comparison['selected_order_hashes']['sha256'] != identity['input_ids_sha256']:
        raise ValueError('Public comparison used a different selected read-order file')
    order_path = ROOT/identity['input_ids_path']
    order_path.resolve().relative_to(ROOT/'checkpoints/figure_03')
    if sha(order_path) != identity['input_ids_sha256']:
        raise ValueError('RAGE read-order checkpoint has changed')
    order_paths = [identity_path, order_path, comparison_path]
    result['archives'].append(package(sorted(order_paths), args.output/'rad-manuscript-rage-input-order.tar.gz'))
(args.output/'release_manifest.json').write_text(json.dumps(result, indent=2)+'\n')
(args.output/'SHA256SUMS').write_text(''.join(a['sha256']+'  '+Path(a['archive']).name+'\n' for a in result['archives']))
print(json.dumps(result, indent=2))
