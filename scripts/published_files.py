"""Select published source files without including unrelated local analyses."""
from pathlib import Path
import shutil
import subprocess


def published_source_files(root):
    """Use the Git index in checkouts, or the included source files in archives."""
    root = Path(root)
    result = None
    if (root / '.git').exists() and shutil.which('git'):
        result = subprocess.run(['git', 'ls-files', '-z', '--', 'source_data'],
                                cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result is not None and result.returncode == 0:
        names = [x.decode() for x in result.stdout.split(b'\0') if x]
    else:
        names = [str(path.relative_to(root)) for path in (root / 'source_data').rglob('*')
                 if path.is_file()]
    files = [root / name for name in names]
    missing = [str(path.relative_to(root)) for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError('Published source files are missing: ' + ', '.join(missing))
    return sorted(files)
