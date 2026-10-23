#!/usr/bin/env python3
"""Check that C5 retains the selected direct test's exact raw P values/effects."""
import argparse,csv,gzip,hashlib,json
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--native-tests',type=Path,required=True)
p.add_argument('--common-table',type=Path,default=Path('source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz'))
p.add_argument('--receipt',type=Path,default=Path('validation/figures_567_direct_test_lineage.json'))
a=p.parse_args()
def read(path):
    with gzip.open(str(path),'rt') as f:return list(csv.DictReader(f,delimiter='\t'))
tests=read(a.native_tests);common=read(a.common_table)
lookup={(r['cohort'],r['gene_id']):r for r in tests}
assert len(lookup)==len(tests), 'duplicate native test key'
assert len(common)==24405
errors={}
for current,source in [('tool_p_value','p_value'),('tool_log2FC','avg_log2FC_H146_vs_H526')]:
    errors[current]=max(abs(float(r[current])-float(lookup[r['tool'],r['gene_id']][source])) for r in common)
    assert errors[current]==0, 'Selected direct test mismatch: '+current
receipt=dict(status='passed',native_test_rows=len(tests),common_rows=len(common),max_absolute_errors=errors,
    inputs=[dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in (a.native_tests,a.common_table)],
    scope='exact all-current-gene raw P/effect lineage comparison; does not rerun Wilcoxon')
a.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
print('All24405 common rows retain exact selected native direct P values and effects')
