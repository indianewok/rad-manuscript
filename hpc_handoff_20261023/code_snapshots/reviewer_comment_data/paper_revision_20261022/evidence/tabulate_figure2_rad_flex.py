#!/usr/bin/env python3
import csv,gzip,json,hashlib,time
from pathlib import Path
from collections import Counter,defaultdict
R=Path('/Volumes/rad_data/reviewer_comment_data')
O=R/'paper_revision_20261022/evidence/figure2_canonical_rad_flex'
O.mkdir(exist_ok=True)
N=4993805
TRUTH=R/'sctagger_L_fixed5000_three_tool_20260812/common/L_truth_5000_barcodes.txt'
truth={l.strip() for l in TRUTH.read_text().splitlines() if l.strip()}
assert len(truth)==5000
FIELDS=['native_correct','corrected_correct','native_incorrect','corrected_incorrect']
def state(final,raw,corrected):
 return ('corrected' if corrected else 'native')+('_correct' if final==raw else '_incorrect')
def finish(name,counts,per,selected,source,contract,raw_rows,ids,expected):
 c={k:counts[k] for k in FIELDS}
 c['all_incorrect']=c['native_incorrect']+c['corrected_incorrect']
 c['ambiguous']=counts['ambiguous']
 c['assigned_unambiguous']=sum(c[k] for k in FIELDS)
 c['unassigned']=N-ids
 c['input_reads']=N
 c['observed_input_ids']=ids
 c['audit_records']=raw_rows
 c['correct_total']=c['native_correct']+c['corrected_correct']
 for k,v in expected.items(): assert c[k]==v,(name,k,c[k],v)
 assert sum(c[k] for k in ['native_correct','corrected_correct','all_incorrect','ambiguous','unassigned'])==N
 assert c['assigned_unambiguous']+c['ambiguous']==ids
 assert all(b in selected for b in per),set(per)-selected
 for k in FIELDS: assert sum(v[k] for v in per.values())==c[k]
 header=['barcode','is_truth','selected','native_correct','corrected_correct','native_incorrect','corrected_incorrect','all_incorrect','correct_total','assigned_unambiguous']
 def values(b,include=True):
  if not include:return [b,int(b in truth),0]+['']*7
  x=per[b]
  return [b,int(b in truth),1,x['native_correct'],x['corrected_correct'],x['native_incorrect'],x['corrected_incorrect'],x['native_incorrect']+x['corrected_incorrect'],x['native_correct']+x['corrected_correct'],sum(x[k] for k in FIELDS)]
 with (O/f'{name}_selected_per_barcode.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(header);w.writerows(values(b) for b in sorted(selected))
 with (O/f'{name}_truth5000_aligned_per_barcode.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(header);w.writerows(values(b,b in selected) for b in sorted(truth))
 result={'tool':name,'contract':contract,'source':str(source),'selected_barcodes':len(selected),'truth_selected':len(selected&truth),'false_selected':len(selected-truth),'counts':c,'five_state_pie_order':['native_correct','corrected_correct','all_incorrect','ambiguous','unassigned'],'array_zero_policy':'Every selected target retained, including zero counts. Unselected truth targets blank in aligned table.','validation':'PASS; source scalar categories and exhaustive partition match exactly.'}
 (O/f'{name}_canonical.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result),flush=True)
 return result
start=time.time()
# RAD strict contract: any original input ID with >1 emitted record is excluded.
radsource=R/'sctagger_L_rad_fixed5000_adapter_fix_20260817/independent_validation/record_audit.tsv.gz'
seen={}; counts=Counter(); per=defaultdict(Counter);nr=0
with gzip.open(radsource,'rt',newline='') as f:
 for row in csv.DictReader(f,delimiter='\t'):
  nr+=1
  rid=row['read_id'];final=row['rad_cb']; true=row['truth_barcode'];raw=row['rad_cr']
  assert true==rid[:16] and true in truth and final in truth
  cat=state(final,true,bool(raw))
  old=seen.get(rid,'ABSENT')
  if old=='ABSENT':
   seen[rid]=(final,cat); counts[cat]+=1;per[final][cat]+=1
  elif old is not None:
   prior,pcat=old; counts[pcat]-=1;per[prior][pcat]-=1;counts['ambiguous']+=1;seen[rid]=None
  if nr%1000000==0:print(f'RAD {nr} rows {time.time()-start:.1f}s',flush=True)
rad=finish('RAD',counts,per,truth,radsource,'RAD24d5ce47 adapter-calibration repair; exact5000truth supplied as both global and custom lists; offensive M2/m2; reject every original ID with more than one emitted record; native=emptyCR correction tag.',nr,len(seen),{'native_correct':667965,'corrected_correct':1944306,'all_incorrect':192090,'ambiguous':9048,'unassigned':2180396})
del seen,per
# Flex historical own-selected contract: same-final duplicate collapsed; different-final excluded.
flexsource=R/'sctagger_flexiplex_audit_20260812/L_flatQ20_audit_reads_barcodes.txt'
flexlist=R/'wl_scan/20260731_sctagger_badread_quality_full/runs/flexiplex/L/flatQ20/output/L_flatQ20_barcodes_final.txt'
selected={l.split()[0] for l in flexlist.read_text().splitlines() if l.strip()}
assert len(selected)==3004 and selected<=truth
seen={};counts=Counter();per=defaultdict(Counter);nr=0
with flexsource.open(newline='') as f:
 for row in csv.DictReader(f,delimiter='\t'):
  nr+=1
  rid=row['Read'];final=row['CellBarcode'];raw=row['RawCellBarcode'];true=rid.rsplit('-',1)[0]
  assert true in truth and final in selected
  cat=state(final,true,raw!=final)
  old=seen.get(rid,'ABSENT')
  if old=='ABSENT':
   seen[rid]=(final,cat);counts[cat]+=1;per[final][cat]+=1
  elif old is not None and old[0]!=final:
   prior,pcat=old;counts[pcat]-=1;per[prior][pcat]-=1;counts['ambiguous']+=1;seen[rid]=None
  if nr%1000000==0:print(f'Flex {nr} rows {time.time()-start:.1f}s',flush=True)
# Confirm every preexisting per-barcode native/corrected/pooled incorrect array exactly.
oldfile=R/'sctagger_flexiplex_audit_20260812/L_per_barcode.tsv'
with oldfile.open() as f:
 for row in csv.DictReader(f,delimiter='\t'):
  x=per[row['barcode']]
  assert x['native_correct']==int(row['native'])
  assert x['corrected_correct']==int(row['corrected'])
  assert x['native_incorrect']+x['corrected_incorrect']==int(row['incorrect_in'])
flex=finish('Flexiplex',counts,per,selected,flexsource,'Flexiplex1.02.6 raw-to-assigned audit; native own-selected3004 list; f8/e2; duplicate same-final assignments collapse to first raw observation; different-final original IDs excluded; native=RawCellBarcode equals CellBarcode.',nr,len(seen),{'native_correct':463613,'corrected_correct':1398700,'all_incorrect':282077,'ambiguous':364,'unassigned':2849051})
with (O/'five_state_pie_counts.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['state','RAD','Flexiplex'])
 for k in rad['five_state_pie_order']:w.writerow([k,rad['counts'][k],flex['counts'][k]])
(O/'canonical_results.json').write_text(json.dumps({'input_reads':N,'RAD':rad,'Flexiplex':flex},indent=2)+'\n')
(O/'README.md').write_text('Canonical Figure2 RAD/Flexiplex arrays were tabulated from preserved audit tables, without processing FASTQ sequences. Original input-read denominator is4,993,805. Use five_state_pie_counts.csv for exhaustive native-correct, corrected-correct, ALL incorrect, ambiguous, unassigned states. Per-barcode all_incorrect already includes both native-incorrect and corrected-incorrect; subtract nothing. Selected-list arrays retain zero counts; aligned5000truth arrays leave unselected Flexiplex rows blank. Actual whitelist/collapse contracts are stated in the JSON files and intentionally differ between RAD and Flexiplex. Historical pooled per-barcode Flexiplex arrays match every row exactly. No statistical tests were run.\n')
print('COMPLETE',time.time()-start,flush=True)
