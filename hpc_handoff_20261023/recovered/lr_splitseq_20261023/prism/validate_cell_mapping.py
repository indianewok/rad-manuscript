#!/usr/bin/env python3
"""Validate the original keyed export against every stored Prism numeric cell.

No sorting or rank inference is used. The original export's row order and cell IDs
must match every column of the original numeric table, including two historical
comparators and the duplicate identity-line column.
"""
import argparse,csv,hashlib,json
from pathlib import Path
COLS=['rad_ed2_assigned_reads','flex_component_no_polyt_assigned_reads','flex_component_polyt_assigned_reads','flames_matched_split_polyt_assigned_reads','flames_historical_two_pass_assigned_reads','rad_ed2_assigned_reads']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--prism-csv',required=True,type=Path)
 p.add_argument('--labeled-source',required=True,type=Path)
 p.add_argument('--out',required=True,type=Path)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 rows=list(csv.DictReader(a.labeled_source.open()))
 prism=list(csv.reader(a.prism_csv.open()))
 assert len(prism)==len(rows)==568
 assert sha(a.prism_csv)=='386f9dc0e09128d6d5f86166196473ac2c124d10366b3393951133c5038b4492'
 assert sha(a.labeled_source)=='8a26f5537b50c2f3199f03b5613622d02cf4d0c9dadf5a0091c2fb2a3841a2ff'
 assert prism==[[r[c] for c in COLS] for r in rows]
 assert len(set(r['published_cell_barcode'] for r in rows))==568
 assert [int(r['published_rank']) for r in rows]==list(range(1,569))
 out=a.out/'prism_row_to_cell.csv'
 with out.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['prism_row_1based']+list(rows[0]))
  w.writeheader()
  w.writerows([dict(prism_row_1based=i,**r) for i,r in enumerate(rows,1)])
 report={'validation':'passed','rows':568,'numeric_cells_compared':3408,
 'same_original_row_order':True,'sort_used':False,'unique_published_cell_barcodes':568,
 'published_rank_equals_prism_row_1based':True,
 'source_labeled_export':str(a.labeled_source.resolve()),'source_labeled_export_sha256':sha(a.labeled_source),
 'source_prism_csv':str(a.prism_csv.resolve()),'source_prism_csv_sha256':sha(a.prism_csv),
 'mapping_output':out.name,'mapping_output_sha256':sha(out),
 'prism_numeric_column_to_export_field':dict((str(i),c) for i,c in enumerate(COLS,1)),
 'final_comparison_fields':['rad_ed2_assigned_reads','flex_component_polyt_assigned_reads'],
 'historical_comparison_fields':['flames_matched_split_polyt_assigned_reads','flames_historical_two_pass_assigned_reads'],
 'interpretation':'The saved keyed export recovers each original Prism row identity through exact row-wise equality across all numerical columns. Native Prism alone contains no cell IDs.'}
 (a.out/'cell_mapping_validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
