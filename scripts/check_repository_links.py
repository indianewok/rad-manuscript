#!/usr/bin/env python3
"""Check the local links readers follow from the repository walkthroughs."""
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
pages = [ROOT/'README.md', ROOT/'SETUP.md', ROOT/'data/README.md']
for directory in ('docs', 'data', 'vendor/flexiplex-audit'):
    pages.extend((ROOT/directory).rglob('*.md'))
checks = []
for page in sorted(set(pages)):
    text = re.sub(r'```.*?```', '', page.read_text(), flags=re.S)
    for match in re.finditer(r'!?\[[^\]]*\]\(([^)]+)\)', text):
        link = match.group(1).strip().strip('<>')
        if urlsplit(link).scheme or link.startswith('#'):
            continue
        target = (page.parent/unquote(link.split('#',1)[0])).resolve()
        result = dict(page=str(page.relative_to(ROOT)), link=link, exists=target.exists())
        try:
            relative = str(target.relative_to(ROOT))
            ignored = subprocess.run(['git','check-ignore','-q',relative], cwd=str(ROOT)).returncode == 0
            result['available_in_working_tree'] = target.exists() and not ignored
        except ValueError:
            result['available_in_working_tree'] = False
        checks.append(result)
failed = [r for r in checks if not r['available_in_working_tree']]
report = dict(status='failed' if failed else 'passed', pages=len(set(pages)), links=len(checks), failures=failed)
(ROOT/'validation/repository_links.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
raise SystemExit(1 if failed else 0)
