#!/usr/bin/env python3
"""Index selected source receipts and panel dependencies without rehashing raw data."""
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/revision'))
from source_paths import resolve_source


def read(name):
    with (ROOT/name).open() as handle:
        return list(csv.DictReader(handle, delimiter='\t'))


def write(name, rows):
    with (ROOT/name).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


assets = []
sources = [
    ('source_data/figure_01/timing_raw_source_registry.tsv','source_path','timing source'),
    ('source_data/figure_02/discovery_callset_manifest.tsv','resolved_path','discovery callset'),
    ('manifests/figure_3_sources.tsv','path','Figure 3 retained source'),
    ('manifests/figures_567_assets.tsv','path','Figures 5–7 source'),
    ('manifests/figures_567_checkpoint_assets.tsv','path','Figures 6–7 checkpoint')]
for index, column, default_role in sources:
    for row in read(index):
        path = resolve_source(row[column])
        assets.append(dict(path=row[column], role=row.get('role',default_role),
            sha256=row.get('sha256','unrecorded'), bytes=row.get('bytes','unrecorded'),
            available_at_index_time=path.is_file(), receipt=index,
            validation_scope='Hash and scientific status inherited from linked receipt; indexing does not revalidate bytes.'))
write('manifests/assets.tsv',assets)

panel_tasks = defaultdict(list)
for task in read('manifests/task_index.tsv'):
    if task['task_id'].startswith('G-') or task['task_id']=='F7-03':
        continue
    for panel in task['panels'].split(','):
        if task['task_id'].startswith('F3-'):
            panel = '3'+panel
        panel_tasks[panel].append(task['task_id'])
panels = []
for panel, tasks in sorted(panel_tasks.items()):
    figure = '2' if panel=='quality-sweep supplement' else panel[0]
    datasets = {
      '1':'LongBench-SN-ONT; LongBench-SC-PB; Visium-HD-3p-mouse-brain',
      '2':'ScTagger-S_flatQ20; ScTagger-L_flatQ20',
      '3':'ScTagger-L_flatQ20; RAGEseq-cell-line; four LongBench inputs',
      '4':'37 inputs in source_data/figure_04/barcode_detection_metrics.tsv',
      '5':'RAGEseq-cell-line; LR-Split-seq',
      '6':'LongBench-SN-ONT; matched Illumina SN and eight bulk genotype references',
      '7':'LongBench-SN-ONT; matched Illumina SN'}[figure]
    if panel in ('1B','1C'):
        datasets='LongBench-SN-ONT; LongBench-SC-PB'
    elif panel=='1D':
        datasets='Visium-HD-3p-mouse-brain / PBC44593'
    elif panel in ('3A','3B','3C'):
        datasets='ScTagger-L_flatQ20; LongBench-SC-ONT; RAGEseq-cell-line'
    elif figure=='3':
        datasets='LongBench-SC-ONT; LongBench-SN-ONT; LongBench-SC-PB; LongBench-SN-PB'
    elif panel in ('5G','5H'):
        datasets='LR-Split-seq; matched short-read reference'
    elif figure=='5':
        datasets='RAGEseq-cell-line; matched cell labels'
    panels.append(dict(panel=panel, experiment_id='figure_'+figure.zfill(2),
        dataset_ids=datasets, guide='docs/figure_'+figure.zfill(2)+'.md',
        source_directory='source_data/figure_'+figure.zfill(2),
        task_ids='; '.join(tasks),
        completion='See task_status.tsv; source-verification proofs do not imply final artwork.'))
write('manifests/panels.tsv',panels)
print('Indexed',len(assets),'source receipts and',len(panels),'current panels/supplements.')
