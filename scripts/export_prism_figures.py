#!/usr/bin/env python3
"""Prepare native Prism figure exports and verify their source files and images."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import zipfile
import zlib


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def quoted(path):
    text = str(path)
    if any(character in text for character in '\r\n"'):
        raise ValueError('Prism script paths cannot contain quotes or newlines')
    return '"' + text + '"'


def repository_path(root, name):
    path = (root / name).resolve()
    path.relative_to(root)
    return path


def png_dimensions(data):
    """Check complete PNG chunks, checksums and decompressed scanline lengths."""
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Invalid PNG signature')
    offset, chunks, compressed = 8, [], []
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError('Truncated PNG chunk')
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError('Truncated PNG payload')
        payload = data[offset + 8:offset + 8 + length]
        checksum = struct.unpack('>I', data[offset + 8 + length:end])[0]
        if zlib.crc32(kind + payload) & 0xffffffff != checksum:
            raise ValueError('Invalid PNG chunk checksum')
        chunks.append(kind)
        if kind == b'IHDR':
            if len(chunks) != 1 or length != 13:
                raise ValueError('Invalid PNG image header')
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', payload)
        if kind == b'IDAT':
            compressed.append(payload)
        if kind == b'IEND':
            if length or end != len(data):
                raise ValueError('Invalid PNG end marker')
            break
        offset = end
    if not chunks or chunks[0] != b'IHDR' or chunks[-1] != b'IEND' or not compressed:
        raise ValueError('Incomplete PNG image')
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color)
    if not channels or depth not in [1, 2, 4, 8, 16] or compression or filtering or interlace not in [0, 1]:
        raise ValueError('Unsupported PNG header')
    if min(width, height) < 100 or width * height > 100000000:
        raise ValueError('Unexpected figure dimensions')
    passes = [(0, 0, 1, 1)] if interlace == 0 else [
        (0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4),
        (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2)]
    row_sizes = []
    for x, y, dx, dy in passes:
        columns = max(0, (width - x + dx - 1) // dx)
        rows = max(0, (height - y + dy - 1) // dy)
        if columns and rows:
            row_sizes.extend([1 + (columns * channels * depth + 7) // 8] * rows)
    expected = sum(row_sizes)
    decoder = zlib.decompressobj()
    raw = decoder.decompress(b''.join(compressed), expected + 1)
    if len(raw) != expected or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('Incomplete PNG scanlines')
    position = 0
    for size in row_sizes:
        if raw[position] > 4:
            raise ValueError('Invalid PNG scanline filter')
        position += size
    return width, height


def prepare(args, root):
    manifest = json.loads((root / 'source_data/prism_exports.json').read_text())
    work = args.work.resolve()
    work.mkdir(parents=True, exist_ok=False)
    copies, images = work / 'sources', work / 'images'
    copies.mkdir()
    images.mkdir()
    rows, commands = [], []
    for expected in manifest['exports']:
        row = dict(expected)
        source = ((args.source_dir / row['source_file']).resolve() if args.source_dir
                  else repository_path(root, row['repository_source']))
        copied = copies / Path(row['repository_source']).name
        shutil.copyfile(source, copied)
        source_hash = sha256(copied)
        if sha256(source) != source_hash:
            raise ValueError('Source changed while copying: ' + str(source))
        if source_hash != row['source_sha256'] and not args.allow_source_updates:
            raise ValueError('Source differs from the published snapshot: ' + str(source))
        with zipfile.ZipFile(copied) as archive:
            document = json.loads(archive.read('document.json'))
            index = document['sheets']['layouts'].index(row['layout_id']) + 1
            sheet = json.loads(archive.read('layouts/' + row['layout_id'] + '/sheet.json'))
            linked = sheet.get('linkedGraphSheets', [])
            if linked != row['linked_graphs'] and not args.allow_source_updates:
                raise ValueError('Figure graph bindings changed: ' + str(source))
        output = images / Path(row['image']).name
        row.update(source_sha256=source_hash, source_path=str(source), copy_path=str(copied),
                   staged_image=str(output), layout_index=index, layout_title=sheet['title'],
                   linked_graphs=linked, source_prism_version=document.get('modifiedBy', {}).get('version'))
        rows.append(row)
        commands.extend(['Open ' + quoted(copied), 'GoTo L, ' + str(index),
                         'ExportPNG ' + quoted(output) + ' 300', 'Close'])
    commands.extend(['OpenOutput ' + quoted(work / 'completed.txt'), 'WVersion', 'CloseOutput'])
    (work / 'export.pzc').write_text('\n'.join(commands) + '\n')
    (work / 'plan.json').write_text(json.dumps(dict(exports=rows, update_sources=args.allow_source_updates), indent=2) + '\n')
    print('Run in GraphPad Prism: ' + str(work / 'export.pzc'))


def verify(args, root):
    work = args.work.resolve()
    version = (work / 'completed.txt').read_text().strip()
    if not version:
        raise ValueError('The Prism completion record is empty')
    plan = json.loads((work / 'plan.json').read_text())
    manifest = json.loads((root / 'source_data/prism_exports.json').read_text())
    def identity(row):
        return row['repository_source'], row['image'], row['layout_id']
    expected = {identity(row): row for row in manifest['exports']}
    inventory = [identity(row) for row in plan['exports']]
    if not inventory or len(set(inventory)) != len(inventory) or set(inventory) != set(expected):
        raise ValueError('The export plan must contain every published figure exactly once')
    rows = []
    # Validate the entire export before replacing any repository files.
    for entry in plan['exports']:
        row = dict(entry)
        if not plan.get('update_sources') and row['source_sha256'] != expected[identity(row)]['source_sha256']:
            raise ValueError('The planned source differs from the published snapshot')
        for field in ['source_path', 'copy_path']:
            if sha256(Path(row[field])) != row['source_sha256']:
                raise ValueError('Prism source changed: ' + row[field])
        image = Path(row['staged_image'])
        data = image.read_bytes()
        width, height = png_dimensions(data)
        row.update(image_sha256=hashlib.sha256(data).hexdigest(), width=width, height=height,
                   resolution_dpi=300, original_unchanged=True, copy_unchanged=True)
        for field in ['repository_source', 'image']:
            repository_path(root, row[field])
        rows.append(row)
    public = []
    for row in rows:
        if not args.check_only:
            destination = repository_path(root, row['image'])
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(row['staged_image'], destination)
            if plan.get('update_sources'):
                destination = repository_path(root, row['repository_source'])
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(row['copy_path'], destination)
        public.append({key: value for key, value in row.items()
                       if key not in ['source_path', 'copy_path', 'staged_image']})
    report = dict(exporter='GraphPad Prism', exporter_version=version, format='PNG',
                  export_script_sha256=sha256(work / 'export.pzc'), exports=public)
    (work / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    if not args.check_only:
        (root / 'source_data/prism_exports.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Verified {} Prism figures; all source and copy hashes match'.format(len(rows)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    first = sub.add_parser('prepare', help='Copy figure sources and write a Prism export script')
    first.add_argument('--work', type=Path, required=True)
    first.add_argument('--source-dir', type=Path, help='Optional external CURRENT FIGURES directory')
    first.add_argument('--allow-source-updates', action='store_true',
                       help='Accept explicitly updated sources and preserve them during verification')
    first.set_defaults(func=prepare)
    second = sub.add_parser('verify', help='Check Prism exports and update the figure files')
    second.add_argument('--work', type=Path, required=True)
    second.add_argument('--check-only', action='store_true', help='Validate without changing repository files')
    second.set_defaults(func=verify)
    args = parser.parse_args()
    args.func(args, Path(__file__).resolve().parents[1])


if __name__ == '__main__':
    main()
