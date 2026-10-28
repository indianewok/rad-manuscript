"""Locations of optional external source archives used by recovery scripts.

Set these variables to your own restored archives. The normal figure walkthroughs
use deposited repository inputs and do not need these external archives.
"""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

def data_root():
    """Parent directory for raw_fastq_datasets and reviewer_comment_data."""
    return Path(os.environ.get('RAD_DATA_ROOT', str(REPO / 'external_data'))).expanduser()

def reviewer_root():
    """Restored reviewer source archive, or reviewer_comment_data below data root."""
    return Path(os.environ.get('RAD_REVIEWER_ROOT', str(data_root() / 'reviewer_comment_data'))).expanduser()

def scratch_root():
    """Restored source packages formerly held on node-local temporary storage."""
    return Path(os.environ.get('RAD_SCRATCH_ROOT', str(reviewer_root() / 'scratch_preservation_20260921/files'))).expanduser()

def scratch_nfs_root():
    """Restored source packages formerly held on shared temporary storage."""
    return Path(os.environ.get('RAD_SCRATCH_NFS_ROOT', str(scratch_root()))).expanduser()


def resolve_source(value, base=None):
    """Resolve repository-relative or external_data-relative manifest locations.

    Literal old absolute paths from external producer receipts can also be read
    after their source archives are restored in the configured roots.
    """
    path = Path(os.path.expandvars(str(value))).expanduser()
    parts = path.parts
    if not path.is_absolute() and parts and parts[0] == 'external_data':
        tail = parts[1:]
        if tuple(tail[:3]) == ('reviewer_comment_data', 'scratch_preservation_20260921', 'files'):
            return scratch_root().joinpath(*tail[3:])
        if tail and tail[0] == 'reviewer_comment_data':
            return reviewer_root().joinpath(*tail[1:])
        return data_root().joinpath(*tail)
    if path.is_absolute():
        if path.is_file() or path.is_dir():
            return path
        if 'reviewer_comment_data' in parts:
            return reviewer_root().joinpath(*parts[parts.index('reviewer_comment_data')+1:])
        if 'rad_data' in parts:
            return data_root().joinpath(*parts[parts.index('rad_data')+1:])
        if len(parts) > 3 and parts[1] in ('scratch', 'scratch-nfs'):
            source_root = scratch_nfs_root() if parts[1] == 'scratch-nfs' else scratch_root()
            return source_root.joinpath(*parts[3:])
        return path
    repository_candidate = REPO / path
    if repository_candidate.exists() or (parts and parts[0] in
            ('source_data', 'data', 'scripts', 'manifests', 'checkpoints', 'validation', 'vendor', 'figures')):
        return repository_candidate
    return (Path(base) if base is not None else REPO) / path
