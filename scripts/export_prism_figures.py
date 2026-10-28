#!/usr/bin/env python3
"""Prepare read-only Prism exports, then verify their source and image hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import zipfile


SELECTIONS = [
    ('figure_1/Figure 1.prism', '8525848D-FB3C-42CC-9F1C-6F7F5A67F4CE', 'figure_01'),
    ('Figure 2.prism', '30A33090-FD85-4730-B1A1-CDE05A559C52', 'figure_02'),
    ('Figure 3.prism', '4B74E124-3EC5-4749-A164-AA426B306E0C', 'figure_03'),
    ('Figure 4.prism', 'A832BFDA-4E92-4AB6-BA27-1DC54997A075', 'figure_04'),
    ('Figure 5.prism', '5D32AC1F-A6CB-47FA-929D-4FF453617D61', 'figure_05'),
    ('Figure 6.prism', '2DD8E8CE-1D8F-41E1-A0CF-8B152558EA0C', 'figure_06'),
    ('Figure 7.prism', 'C3B5C198-E4BA-4C34-9580-B55EA23BE9C3', 'figure_07'),
    ('Supplemental 2ish V2.prism', '0EA6984E-96DB-4417-AB20-179C0558851D', 'figure_02_supplement'),
    ('Supplemental Related to Figure 4.prism', '59488B30-603A-4CD5-A1CF-9EEC86EFAC02', 'figure_04_supplement'),
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quoted(path):
    value = str(path)
    if any(c in value for c in '\n\r"'):
        raise ValueError('Prism script paths cannot contain quotes or newlines')
    return '"' + value + '"'


def prepare(args, root):
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    copies = work / 'sources'
    copies.mkdir()
    images = work / 'images'
    images.mkdir()
    rows, commands = [], []
    for source_name, uid, stem in SELECTIONS:
        source = (args.source_dir / source_name).resolve()
        copied = copies / source.name
        shutil.copyfile(source, copied)
        source_hash = sha256(source)
        if sha256(copied) != source_hash:
            raise ValueError('Source changed during copying: ' + source_name)
        with zipfile.ZipFile(copied) as archive:
            document = json.loads(archive.read('document.json'))
            layouts = document['sheets']['layouts']
            index = layouts.index(uid) + 1
            sheet = json.loads(archive.read('layouts/' + uid + '/sheet.json'))
            attributes = document.get('sheetAttributesMap', {})
        relative_output = 'figures/' + stem[:9] + '/prism/' + stem + '.png'
        output = images / (stem + '.png')
        rows.append({
            'source_file': source_name, 'source_sha256': source_hash,
            'source_path': str(source), 'copy_path': str(copied),
            'source_prism_version': document.get('modifiedBy', {}).get('version'),
            'layout_id': uid, 'layout_index': index, 'layout_title': sheet['title'],
            'linked_graphs': [{'id': graph, 'title': attributes.get(graph, {}).get('title')}
                              for graph in sheet.get('linkedGraphSheets', [])],
            'image': relative_output, 'staged_image': str(output), 'resolution_dpi': 300,
        })
        commands.extend(['Open ' + quoted(copied), 'GoTo L, ' + str(index),
                         'ExportPNG ' + quoted(output) + ' 300', 'Close'])
    commands.extend(['OpenOutput ' + quoted(work / 'completed.txt'), 'WVersion', 'CloseOutput'])
    (work / 'export.pzc').write_text('\n'.join(commands) + '\n')
    (work / 'plan.json').write_text(json.dumps(rows, indent=2) + '\n')
    print('Run in Prism: ' + str(work / 'export.pzc'))


def verify(args, root):
    work = args.work.resolve()
    version = (work / 'completed.txt').read_text().strip()
    if not version:
        raise ValueError('Prism completion record is empty')
    rows = json.loads((work / 'plan.json').read_text())
    for row in rows:
        for field in ('source_path', 'copy_path'):
            if sha256(Path(row[field])) != row['source_sha256']:
                raise ValueError('Prism source changed: ' + row[field])
        image = Path(row['staged_image'])
        content = image.read_bytes()
        if content[:8] != b'\x89PNG\r\n\x1a\n' or content[12:16] != b'IHDR':
            raise ValueError('Invalid PNG: ' + str(image))
        width, height = struct.unpack('>II', content[16:24])
        if width < 100 or height < 100:
            raise ValueError('Unexpected image dimensions: ' + str(image))
        row.update(image_sha256=sha256(image), width=width, height=height,
                   original_unchanged=True, copy_unchanged=True)
        del row['source_path']
        del row['copy_path']
    for row in rows:
        destination = root / row['image']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(row.pop('staged_image'), destination)
    report = {'exporter': 'GraphPad Prism', 'exporter_version': version,
              'export_script_sha256': sha256(work / 'export.pzc'),
              'source_directory': 'external_data/prism',
              'format': 'PNG', 'exports': rows}
    manifest = root / 'manifests/prism_exports.json'
    manifest.write_text(json.dumps(report, indent=2) + '\n')
    print('Verified {} exports; all source and copy hashes unchanged'.format(len(rows)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    first = sub.add_parser('prepare')
    first.add_argument('--source-dir', type=Path, required=True)
    first.add_argument('--work', type=Path, required=True)
    second = sub.add_parser('verify')
    second.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    (prepare if args.command == 'prepare' else verify)(args, root)


if __name__ == '__main__':
    main()
