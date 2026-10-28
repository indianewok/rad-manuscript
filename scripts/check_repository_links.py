#!/usr/bin/env python3
"""Check the local links readers follow from the repository walkthroughs."""
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
pages = [ROOT/'README.md', ROOT/'SETUP.md', ROOT/'data/README.md']
for directory in ('docs', 'data', 'source_data', 'figures', 'vendor/flexiplex-audit'):
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
            result['repository_target'] = relative
            result['available_in_working_tree'] = result['exists']
        except ValueError:
            result['available_in_working_tree'] = False
        checks.append(result)
targets = sorted({r['repository_target'] for r in checks if 'repository_target' in r})
ignored_result = subprocess.run(['git', 'check-ignore', '--stdin', '-z'],
                                input='\0'.join(targets) + '\0', text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(ROOT))
if ignored_result.returncode not in (0, 1):
    raise RuntimeError(ignored_result.stderr)
ignored = set(ignored_result.stdout.split('\0'))
for result in checks:
    if result.pop('repository_target', None) in ignored:
        result['available_in_working_tree'] = False
failed = [r for r in checks if not r['available_in_working_tree']]
report = dict(status='failed' if failed else 'passed', pages=len(set(pages)), links=len(checks), failures=failed)
report_path = ROOT/'validation/repository_links.json'
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
raise SystemExit(1 if failed else 0)
