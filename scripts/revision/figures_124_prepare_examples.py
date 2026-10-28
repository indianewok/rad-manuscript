#!/usr/bin/env python3
"""Extract bounded actual evidence examples; retain source SHA256 and row lineage."""
import sys,csv,gzip,json,hashlib,shutil,itertools
from pathlib import Path
from source_paths import reviewer_root, scratch_root, resolve_source
R=Path(__file__).resolve().parents[2];B=reviewer_root()
sys.path.insert(0,str(R/'scripts/revision'))
from figures_124 import sha,rows,write_rows,write_json
provenance={i:[] for i in (1,2,4)}
def excerpt(i,source,name,predicate=lambda r,n: n<=8,fields=None,limit=None,delimiter=None):
 source=resolve_source(source,base=B);op=gzip.open if source.suffix=='.gz' else open
 delimiter=delimiter or ('\t' if '.tsv' in source.name else ',')
 chosen=[];numbers=[]
 with op(source,'rt') as f:
  for n,r in enumerate(csv.DictReader(f,delimiter=delimiter),1):
   if predicate(r,n):
    chosen.append({k:r[k] for k in fields} if fields else r);numbers.append(n)
    if limit and len(chosen)>=limit:break
 dest=R/f'data/examples/figure_{i:02d}'/name;write_rows(dest,chosen)
 provenance[i].append(dict(file=name,source_path=str(source),source_sha256=sha(source),source_bytes=source.stat().st_size,source_data_row_numbers_1_based=numbers,header_excluded_from_row_count=True,columns=fields or list(chosen[0]),excerpt_sha256=sha(dest),scope='bounded actual source excerpt; not a representative statistical sample'))
 return dest

def copy(i,source,name,**extra):
 source=resolve_source(source,base=B);dest=R/f'data/examples/figure_{i:02d}'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
 provenance[i].append(dict(file=name,source_path=str(source),source_sha256=sha(source),source_bytes=source.stat().st_size,excerpt_sha256=sha(dest),scope='complete compact input, copied byte-identically',**extra))
 return dest

# Timing logs are small real root evidence; the COMPLETE marker may be empty.
registry=rows(R/'source_data/figure_01/timing_raw_source_registry.tsv')
for phase in ('whitelist_detection','demultiplexing'):
 for suffix in ('metrics.tsv','command.sh','status.tsv','COMPLETE'):
  wanted=f'SN_ONT/threads_4/rep_1/RAD/{phase}/attempt_001/{suffix}'
  selected=next((r for r in registry if r['relative_path'].endswith(wanted)),None)
  if selected:copy(1,selected['source_path'],f'raw_timing/{phase}/{suffix}')
excerpt(1,R/'source_data/figure_01/accepted_phase_records.tsv','accepted_phase_example.tsv',lambda r,n:r['threads']=='16' and r['replicate']=='1')
excerpt(1,R/'source_data/figure_01/hd_stage_differences.tsv','hd_stage_example.tsv')
hd_seen={'0':0,'1':0}
def grid_examples(r,n):
 state=r['in_tissue']
 if hd_seen[state]>=4:return False
 hd_seen[state]+=1;return True
excerpt(1,R/'source_data/figure_01/hd_RAD_bins.tsv','hd_grid_example.tsv',grid_examples,fields=['bin_id','array_row','array_col','in_tissue'],limit=8)
# Discovery preview has every barcode for one small public synthetic case.
copy(2,scratch_root()/'sctagger_sl_three_tool_quality_20260731/inputs/S_truth_barcodes.txt','S_truth_barcodes.txt')
for tool,sub in [('RAD','rad/scanwl.txt'),('BLAZE','blaze/whitelist.csv'),('Flexiplex_f0','flex_f0/selected.txt'),('Flexiplex_f8','flex_f8/selected.txt')]:
 copy(2,scratch_root()/f'sctagger_sl_three_tool_quality_20260731/runs/S/shift_p01/{sub}',f'S_shift_p01_{tool}.txt')
# Two actual synthetic reads; no real/controlled FASTQ material enters GitHub.
audit=json.loads((R/'validation/figures_124_fastq_identity.json').read_text())
for key,name in [('L_flatQ20','L_flatQ20_first2.fastq'),('L_native2023','L_native2023_first2.fastq')]:
 if key not in audit['sources']:key=next(k for k in audit['sources'] if 'native' in k.lower())
 info=audit['sources'][key];source=resolve_source(info['path'],base=B);dest=R/'data/examples/figure_02'/name
 with gzip.open(source,'rt') as f:content=''.join(itertools.islice(f,8))
 dest.write_text(content)
 provenance[2].append(dict(file=name,source_path=str(source),source_sha256=info.get('sha256',info.get('compressed_sha256')),source_bytes=source.stat().st_size,source_fastq_record_numbers_1_based=[1,2],excerpt_sha256=sha(dest),scope='public ScTagger synthetic sequences; first two records only; full-stream hash from completed audit9976816'))
excerpt(2,B/'sctagger_L_rad_fixed5000_adapter_fix_20260817/independent_validation/record_audit.tsv.gz','RAD_assignment_records_example.tsv')
excerpt(2,B/'sctagger_flexiplex_audit_20260812/L_flatQ20_audit_reads_barcodes.txt','Flexiplex_assignment_records_example.tsv',delimiter='\t')
excerpt(2,B/'paper_revision_20261022/prism/blaze2023_assignment_replay/assignment_records.tsv.gz','BLAZE_assignment_records_example.tsv')
excerpt(2,R/'source_data/figure_02/paired_50000_barcode_mean_Q.csv.gz','paired_quality_example.tsv')
# Only public/synthetic entries in root-data examples. Complete output has all37.
excerpt(4,R/'source_data/figure_04/barcode_detection_metrics.tsv','three_input_metrics_example.tsv',lambda r,n:r['canonical_id'] in ('ScTagger-S_flatQ20','ScTagger-L_flatQ20','RAGEseq-TNBC-LN'))
source=B/'wl_scan/20260730_rageseq_ERR3268990_tnbc_lymphnode_four_tool/analysis/barcode_level_annotations.tsv'
seen=set()
def label_examples(r,n):
 label=r['deposited_label'];kind='doublet' if label=='T_B_doublet' else 'T' if label.startswith('T_cell') else 'B' if label.startswith('B_cell') else 'other'
 key=(kind,r['in_deposited_shortread_list'])
 if key in seen:return False
 seen.add(key);return True
excerpt(4,source,'immune_reference_annotation_example.tsv',label_examples,fields=['barcode','in_deposited_shortread_list','deposited_label','called_RAD','called_BLAZE_2.6.0a0_expect10433','called_Flexiplex_f8'])
for i,entries in provenance.items():
 write_json(R/f'data/examples/figure_{i:02d}/provenance.json',dict(scope='root evidence excerpts for human inspection; quantitative conclusions use complete source_data tables',sources=entries))
print({i:len(x) for i,x in provenance.items()})
