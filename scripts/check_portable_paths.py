#!/usr/bin/env python3
"""Check that published text has no workstation or cluster storage paths.

Run from any directory. Checks files in Git and this checker; ignores local
checkpoints and separately staged archives. Generic system executables such as
/usr/bin/time remain valid.
"""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
INTERNAL_ROOT = re.compile(
    r"/(?:dartfs(?:-hpc)?|scratch(?:-nfs)?|Volumes|Users|home|tmp|mnt)/"
)


def main():
    # Archived execution records retain their original machine paths. Verify the
    # sealed source before exempting those exact bytes, including duplicate copies.
    from verify_pinned_flames_configs import verify
    archive_validation = verify(ROOT)
    with (ROOT / 'source_data/pinned_flames_configs/files.tsv').open() as handle:
        archived_hashes = {row['sha256'] for row in csv.DictReader(handle, delimiter='\t')}
    listed = subprocess.check_output(
        ['git', 'ls-files', '-z'], cwd=str(ROOT)
    ).decode().split('\0')
    paths = set(filter(None, listed))
    paths.add(str(Path(__file__).resolve().relative_to(ROOT)))
    failures = []
    checked = 0
    archived = []
    for relative in sorted(paths):
        path = ROOT / relative
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() in archived_hashes:
            archived.append(relative)
            continue
        if path.suffix == '.gz':
            raw = gzip.decompress(raw)
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            continue
        checked += 1
        for number, line in enumerate(text.splitlines(), 1):
            if INTERNAL_ROOT.search(line):
                failures.append({'file': relative, 'line': number})
    report = {
        'status': 'failed' if failures else 'passed',
        'text_files_checked': checked,
        'scope': 'Git-indexed text and gzip text; hash-verified historical execution records retain archived paths',
        'verified_archive': archive_validation,
        'archived_files': archived,
        'failures': failures,
    }
    report_path = ROOT / 'validation/portable_paths.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2) + '\n'
    )
    print(json.dumps(report, indent=2))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
