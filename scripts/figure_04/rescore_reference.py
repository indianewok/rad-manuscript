#!/usr/bin/env python3
"""Score one native selected barcode list against the dataset's stated reference."""
import argparse,csv,gzip,hashlib,json,re
from pathlib import Path

def barcodes(path):
    opener = gzip.open if path.suffix == '.gz' else open
    values = []
    with opener(path, 'rt') as handle:
        for line in handle:
            value = re.split(r'[\s,]+', line.strip())[0].removesuffix('-1')
            if not value or value.lower() == 'barcode':
                continue
            if not re.fullmatch('[ACGT]{16}', value):
                raise ValueError('Expected a 16-base barcode in ' + str(path))
            values.append(value)
    if len(values) != len(set(values)):
        raise ValueError('Duplicate barcodes in ' + str(path))
    return set(values)

def barcode_sha256(values):
    return hashlib.sha256(('\n'.join(sorted(values)) + '\n').encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-record', type=Path, required=True)
    parser.add_argument('--tool', choices=['RAD', 'BLAZE', 'Flexiplex'], required=True)
    parser.add_argument('--selected', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    record = json.loads(args.dataset_record.read_text())
    selected, reference = barcodes(args.selected), barcodes(args.reference)
    if not reference or barcode_sha256(reference) != record['reference_barcode_sha256']:
        raise ValueError('Reference barcodes do not match the dataset record')
    tp, fp, fn = len(selected & reference), len(selected - reference), len(reference - selected)
    row = dict(dataset_id=record['dataset_id'], tool=args.tool, calls=len(selected),
               reference_n=len(reference), tp=tp, fp=fp, fn=fn,
               precision=tp / len(selected) if selected else 0,
               recall=tp / len(reference), f1=2 * tp / (len(selected) + len(reference)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row), delimiter='\t', lineterminator='\n')
        writer.writeheader();writer.writerow(row)
    print(json.dumps(row))

if __name__ == '__main__':main()
