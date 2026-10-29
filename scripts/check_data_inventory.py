#!/usr/bin/env python3
"""Check the readable dataset inventory and small public data files.

This does not run an analysis. It checks that each of the 37 Figure 4 inputs
appears exactly once and has exactly one RAD/BLAZE/Flexiplex metric row, and
records file hashes and tabular shapes so readers can inspect the deposited data.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
from published_files import published_source_files

# These native exports have no header row. Their first record is data, and the
# column labels below describe the source format rather than changing the file.
HEADERLESS_COLUMNS = {
    'source_data/figure_01/hd_16um_filtered_barcodes.tsv.gz': ['barcode'],
    'source_data/figure_01/hd_16um_raw_barcodes.tsv.gz': ['barcode'],
    'source_data/figure_02/generation_environment.tsv': ['setting', 'value'],
}
for tool in ('RAD', 'BLAZE', 'Flexiplex'):
    HEADERLESS_COLUMNS['source_data/figure_06/'+tool+'_alignment_idxstats.tsv'] = [
        'reference_name', 'reference_length', 'mapped_segments', 'unmapped_segments']


def rows(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))


def digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    registry = root / 'manifests/datasets.tsv'
    inventory = rows(registry) if registry.is_file() else None
    metrics = rows(root / 'source_data/figure_04/barcode_detection_metrics.tsv')
    benchmark_ids = {row['canonical_id'] for row in metrics}
    if inventory is not None:
        registered_ids = [row['dataset_id'] for row in inventory]
        assert len(registered_ids) == len(set(registered_ids)), 'Dataset IDs must be unique'
        benchmark_labels = {row.get('display_dataset', row['canonical_id']) for row in metrics}
        assert benchmark_labels.issubset(set(registered_ids)), 'Every benchmark input must be registered'
        assert all(row['accessions'] for row in inventory)
    ids = sorted(benchmark_ids)
    assert len(ids) == 37, 'Figure 4 must retain exactly 37 distinct input identities'
    assert len(metrics) == 111
    for dataset in ids:
        tools = [row['tool'] for row in metrics if row['canonical_id'] == dataset]
        assert sorted(tools) == ['BLAZE', 'Flexiplex', 'RAD'], (dataset, tools)
    files = []
    for path in published_source_files(root):
        record = {'file': str(path.relative_to(root)), 'bytes': path.stat().st_size,
                  'sha256': digest(path), 'rows': '', 'columns': '', 'header_present': ''}
        suffix = path.name[:-3] if path.suffix == '.gz' else path.name
        if suffix.endswith(('.csv', '.tsv')):
            opener = gzip.open if path.suffix == '.gz' else open
            with opener(str(path), 'rt', newline='') as handle:
                reader = csv.reader(handle, delimiter='\t' if suffix.endswith('.tsv') else ',')
                if record['file'] in HEADERLESS_COLUMNS:
                    columns = HEADERLESS_COLUMNS[record['file']]
                    record['header_present'] = 'no'
                else:
                    columns = next(reader, [])
                    record['header_present'] = 'yes'
                record['columns'] = json.dumps(columns)
                record['rows'] = sum(1 for _ in reader)
        files.append(record)
    destination = root / 'manifests/data_files.tsv'
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['file','bytes','sha256','rows','columns','header_present'], delimiter='\t')
        writer.writeheader()
        writer.writerows(files)
    report = {'status': 'passed', 'figure_04_inputs': len(ids), 'tool_rows': len(metrics),
              'all_registered_inputs': len(inventory) if inventory is not None else None,
              'local_dataset_registry': 'checked' if inventory is not None else 'not supplied',
              'source_data_files': len(files),
              'scope': 'inventory, schema discovery and byte identity; scientific validation is figure-specific'}
    report_path = root / 'validation/data_inventory.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
