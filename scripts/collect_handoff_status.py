#!/usr/bin/env python3
"""Join current figure-task receipts to the declared scope; never infer success."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
definitions = list(csv.DictReader((ROOT/'manifests/task_index.tsv').open(), delimiter='\t'))
receipts = {}
for filename in ('global_tasks.json', 'figures_124_tasks.json', 'figure_3_tasks.json', 'figures_567_tasks.json'):
    path = ROOT/'manifests'/filename
    content = json.loads(path.read_text())
    if isinstance(content, dict):
        content = content.get('tasks', [])
    for row in content:
        key = row.get('id', row.get('task_id'))
        if key in receipts:
            raise ValueError('Duplicate task receipt: '+key)
        receipts[key] = row

rows = []
for definition in definitions:
    key = definition['task_id']
    if key not in receipts:
        raise ValueError('No receipt for '+key)
    receipt = receipts[key]
    rows.append(dict(definition,
        status=receipt.get('status', 'unreported'),
        completed=receipt.get('completed', receipt.get('summary', 'See linked receipt')),
        evidence=receipt.get('evidence', receipt.get('output', '')),
        remaining=receipt.get('next_dependency', receipt.get('remaining', receipt.get('blocker', '')))))

with (ROOT/'manifests/task_status.tsv').open('w', newline='') as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter='\t')
    writer.writeheader()
    writer.writerows(rows)
print('Recorded', len(rows), 'tasks; statuses are preserved, not collapsed to a completion claim.')
