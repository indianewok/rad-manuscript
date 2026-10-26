#!/usr/bin/env python3
"""Select the first real reference singlet showing each RAD identity outcome."""
import argparse, csv, hashlib, json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--input', type=Path, required=True)
p.add_argument('--output', type=Path, default=Path('data/examples/figure_06'))
a = p.parse_args(); a.output.mkdir(parents=True, exist_ok=True)
fields = ['cell_barcode', 'illumina_reference_present', 'illumina_reference_state', 'illumina_reference_label']
for prefix in ('rad', 'blaze_panel_matched', 'flexiplex'):
    fields.extend(prefix+'_'+suffix for suffix in ('query_selected','vireo_state','vireo_label'))
found = {}
with a.input.open() as f:
    for ordinal, r in enumerate(csv.DictReader(f), 1):
        if r['illumina_reference_present']!='TRUE' or r['illumina_reference_state']!='named_singlet': continue
        if r['rad_query_selected']!='TRUE': outcome='not_selected'
        elif r['rad_vireo_state']=='named_singlet': outcome='same' if r['rad_vireo_label']==r['illumina_reference_label'] else 'different'
        else: outcome=r['rad_vireo_state']
        if outcome not in found: found[outcome]=(ordinal, r)
        if set(found)==set(('same','different','doublet','unassigned','not_selected')): break
assert len(found)==5
rows = sorted(found.values())
with (a.output/'genotype_input.csv').open('w', newline='') as f:
    w=csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); w.writeheader(); w.writerows(r for _,r in rows)
digest=hashlib.sha256(a.input.read_bytes()).hexdigest()
(a.output/'extraction.json').write_text(json.dumps(dict(source=str(a.input),source_sha256=digest,
    selection='first reference named singlet in source order for each RAD same/different/doublet/unassigned/not_selected outcome; named columns only',
    source_data_rows=[i for i,_ in rows], selected_columns=fields, row_count=5,
    scope='real bounded public cell-line excerpt; selection is illustrative, not random or representative'),indent=2)+'\n')
print('Wrote 5 real cells; excerpt denominator is 5, full reference denominator is 5782')
