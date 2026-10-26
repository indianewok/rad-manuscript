#!/usr/bin/env python3
"""Extract bounded real RAGE-seq and LR-Split-seq rows; never fabricate IDs."""
import argparse, csv, hashlib, itertools, json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--project-root', type=Path, required=True)
p.add_argument('--output', type=Path, default=Path('data/examples/figure_05'))
a = p.parse_args(); a.output.mkdir(parents=True, exist_ok=True)
manifest = []
for relative, name, delimiter, limit in [
    ('rad_blaze_bcrtcr_cellline/rad_per_read.tsv', 'rad_read_assignments.tsv', '\t', 6),
    ('flexiplex_bcrtcr_cellline_20260811/flexiplex_per_barcode_bcrtcr.tsv', 'flexiplex_receptor_input.tsv', '\t', 3),
    ('scratch_preservation_20260921/files/splitseq_shortread_20260727/csv/called_cells_summary.csv', 'splitseq_reference.csv', ',', 3)]:
    src = a.project_root / relative
    with src.open() as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = list(itertools.islice(reader, limit)); fields = reader.fieldnames
    dst = a.output / name
    with dst.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=delimiter); w.writeheader(); w.writerows(rows)
    digest = hashlib.sha256()
    with src.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''): digest.update(block)
    manifest.append(dict(output=name, source=str(src), source_sha256=digest.hexdigest(),
                         selection='first {} data rows; all columns unchanged'.format(limit),
                         source_data_rows=list(range(1, limit+1)), scope='real bounded excerpt; candidate source, not proof of final artwork binding'))
(a.output/'extraction.json').write_text(json.dumps(manifest, indent=2)+'\n')
print('Wrote three bounded real excerpts and source hashes to', a.output)
