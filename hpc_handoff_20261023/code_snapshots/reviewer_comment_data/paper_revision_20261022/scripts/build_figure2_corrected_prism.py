#!/usr/bin/env python3
"""Build a closed task-owned Prism copy. Preserve originals; do not run tests/statistics.

Required --blaze-json contract:
{
  "condition": "nanopore2023 native unadjusted",
  "per_target_csv": "/absolute/path.csv",
  "totals": {"native_correct": N, "corrected_correct": N,
             "all_incorrect": N, "ambiguous": 0, "unassigned": N},
  "four_way_totals": {"native_correct": N, "corrected_correct": N,
                      "native_incorrect": N, "corrected_incorrect": N},
  "field_map": {"barcode": "barcode", "native_correct": "native_correct",
                "corrected_correct": "corrected_correct", "all_incorrect": "all_incorrect",
                "native_incorrect": "native_incorrect", "corrected_incorrect": "corrected_incorrect"}
}
CSV must include EVERY selected target, even if it has zero assigned reads.
Optional selected_whitelist supplies one barcode per line when CSV omits zero targets.
BLAZE unresolved outcomes remain unassigned; ambiguous=0 is an explicit reporting convention.
"""
from pathlib import Path
import argparse,csv,hashlib,io,json,re,zipfile,os,datetime
BASE=Path('/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022')
SOURCE=BASE/'evidence/092126_Figure_2_CMV_V18.prism'
OUTPUT=BASE/'prism/Figure2_corrected_20261022.prism'
EXPECTED='d8cc036cdca79d607be863fd15a9bc4721c4e86d09721ea4b368401fa9b3a10c'
STATES=['native_correct','corrected_correct','all_incorrect','ambiguous','unassigned']
TARGET_FIELDS=['native_correct','corrected_correct','native_incorrect','corrected_incorrect','all_incorrect']
PIE_STATES=['native_correct','corrected_correct','corrected_incorrect','native_incorrect','ambiguous','unassigned']
PIE_LABELS=['Native correct','Corrected correct','Corrected incorrect','Native incorrect','Multiple outputs excluded','Unassigned']
PERBC={
 'native_correct':'63D81234-28AC-46E8-8332-CB1AE2FC1AFF',
 'corrected_correct':'66EF3D96-C86B-4FA9-ACE5-53621808DA50',
 'corrected_incorrect':'98505F94-3866-4F00-A8CD-E076CF542357'}
INVALIDATE=['E2C721DC-CF0D-45D4-A198-0E9955653EDC','1692D0EE-34B0-47E1-AA9A-B1A96AD55A39','BB4EB3C9-1C4C-4843-B4D5-72F9942D120C','6868ACFE-05E0-455D-B273-BCB0856BE80B','5BD85BDF-0140-4146-8921-64C4ABC643C5','AA4C6237-DB10-425A-866F-F7E130BDA8F1']

def csv_bytes(rows):
 s=io.StringIO(newline='');csv.writer(s,lineterminator='\n').writerows(rows);return s.getvalue().encode()
def get_rows(p,field_map=None):
 field_map=field_map or {};out={}
 with Path(p).open(newline='') as f:
  for row in csv.DictReader(f):
   bc=row[field_map.get('barcode','barcode')].removesuffix('-1')
   if row.get('selected','1') in ('0','False','false'):continue
   assert bc not in out,('duplicate selected target',p,bc)
   out[bc]={k:int(row[field_map.get(k,k)]) for k in TARGET_FIELDS}
   assert out[bc]['all_incorrect']==out[bc]['native_incorrect']+out[bc]['corrected_incorrect']
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--blaze-json',required=True,type=Path);ap.add_argument('--output',type=Path,default=OUTPUT);ap.add_argument('--replace-closed-copy',action='store_true');args=ap.parse_args()
 assert args.output.resolve()!=SOURCE.resolve()
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
 if args.output.exists() and not args.replace_closed_copy:raise RuntimeError('Output exists; use --replace-closed-copy only after confirming Prism has not opened it.')
 bcfg=json.loads(args.blaze_json.read_text())
 canonical=BASE/'evidence/figure2_canonical_rad_flex'
 tools={t:{'rows':get_rows(canonical/f'{t}_selected_per_barcode.csv'),'totals':{}} for t in ['RAD','Flexiplex']}
 with (canonical/'five_state_pie_counts.csv').open(newline='') as f:
  for row in csv.DictReader(f):
   for t in tools:tools[t]['totals'][row['state']]=int(row[t])
 tools['BLAZE']={'rows':get_rows(bcfg['per_target_csv'],bcfg.get('field_map')),'totals':{k:int(bcfg['totals'][k]) for k in STATES}}
 if bcfg.get('selected_whitelist'):
  selected={x.strip().removesuffix('-1') for x in Path(bcfg['selected_whitelist']).read_text().splitlines() if x.strip()}
  assert set(tools['BLAZE']['rows'])<=selected
  for bc in selected:tools['BLAZE']['rows'].setdefault(bc,{k:0 for k in TARGET_FIELDS})
 for t,d in tools.items():
  assert sum(d['totals'].values())==4993805,(t,'nonexhaustive pie')
  for k in STATES[:3]:assert sum(r[k] for r in d['rows'].values())==d['totals'][k],(t,k,'per-target does not sum to total')
  for k in ['native_incorrect','corrected_incorrect']:d['totals'][k]=sum(r[k] for r in d['rows'].values())
  assert d['totals']['all_incorrect']==d['totals']['native_incorrect']+d['totals']['corrected_incorrect']
  assert sum(d['totals'][k] for k in PIE_STATES)==4993805
  if t=='BLAZE':assert all(d['totals'][k]==int(v) for k,v in bcfg['four_way_totals'].items())
 with zipfile.ZipFile(SOURCE) as z:
  original={n:z.read(n) for n in z.namelist()};infos=z.infolist()
 replaced={};removed=set();history=BASE/'prism/history_before_20261022';history.mkdir(parents=True,exist_ok=True)
 js=lambda p:json.loads(replaced.get(p,original[p]))
 def putj(p,obj):replaced[p]=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
 doc=js('document.json')
 sheets={s:js(f'data/sheets/{s}/sheet.json') for s in doc['sheets']['data']}
 def table(sid):
  s=sheets.get(sid) or js(f'data/sheets/{sid}/sheet.json');return s['table']
 def member(sid):return f"data/tables/{table(sid)['uid']}/data.csv"
 def rows(sid):return list(csv.reader(io.StringIO(replaced.get(member(sid),original[member(sid)]).decode())))
 def edit(sid,rr):
  p=member(sid)
  if p not in replaced:(history/(sid+'.csv')).write_bytes(original[p])
  replaced[p]=csv_bytes(rr)
  # Established project workflow treats data.dt as a fresh 32-hex change token,
  # not an MD5 checksum. See preserved update_raw_longbench_prism.py:286 onward.
  dt=p.rsplit('/',1)[0]+'/data.dt'
  if dt in original:replaced[dt]=hashlib.sha256(replaced[p]).hexdigest()[:32].encode('ascii')
  cp=p.rsplit('/',1)[0]+'/content.json'
  if cp in original:
   c=js(cp);c['numberOfRows']=len(rr);c['numberOfColumns']=max((len(r) for r in rr),default=0);putj(cp,c)
  tab=table(sid);ids=[]
  if tab.get('rowTitlesDataSet'):ids.append(tab['rowTitlesDataSet'])
  if tab.get('xDataSet'):ids.append(tab['xDataSet'])
  ids+=tab['dataSets'];col=0
  for did in ids:
   dp=f'data/sets/{did}.json';ds=js(dp)
   for rep in ds.get('replicates',[]):
    populated=[i for i,r in enumerate(rr) if len(r)>col and r[col]!='']
    rep.pop('firstRow',None);rep.pop('lastRow',None)
    if populated:rep['firstRow']=populated[0];rep['lastRow']=populated[-1]
    col+=1
   putj(dp,ds)
 def set_title(sid,new):
  p=f'data/sheets/{sid}/sheet.json';s=js(p);s['title']=new;putj(p,s)
  doc.setdefault('sheetAttributesMap',{}).setdefault(sid,{})['title']=new
 def dtitle(did,new):
  p=f'data/sets/{did}.json';d=js(p);d['title']=new;putj(p,d)
 truth=[r[0] for r in rows(PERBC['native_correct'])]
 assert len(truth)==5000 and len(set(truth))==5000
 truthset=set(truth)
 for field,sid in PERBC.items():
  rr=rows(sid);assert [r[0] for r in rr]==truth
  for r in rr:
   bc=r[0]
   for t,c in [('BLAZE',1),('RAD',2),('Flexiplex',3)]:r[c]=str(tools[t]['rows'][bc][field]) if bc in tools[t]['rows'] else ''
   # Existing graphs G/I use D. Same-slot replacement avoids guessing opaque graph references.
   # Original fixed5K D survives in the source copy and history CSV, not as a false current comparison.
   if field in ['native_correct','corrected_correct']:r[4]=r[3]
  edit(sid,rr)
  if field in ['native_correct','corrected_correct']:
   dtitle(table(sid)['dataSets'][3],'Flexiplex')
  set_title(sid,{'native_correct':'Native correct assignments per selected truth barcode','corrected_correct':'Corrected correct assignments per selected truth barcode','corrected_incorrect':'Corrected incorrect assignments per selected truth target barcode'}[field])
 discovery={}
 for t,d in tools.items():
  selected=set(d['rows']);tp=len(selected&truthset);fp=len(selected-truthset);fn=len(truthset-selected)
  discovery[t]={'tp':tp,'fp':fp,'fn':fn,'precision':tp/(tp+fp),'recall':tp/5000,'f1':2*tp/(2*tp+fp+fn)}
 # Main stacked discovery and older standalone TP/FP sheets.
 sid='9FA3BE17-60E1-4F42-8084-62CD9B3AE250';rr=rows(sid)
 for r in rr:
  if r[0] in discovery:r[1:4]=[str(discovery[r[0]][k]) for k in ['tp','fp','fn']]
 edit(sid,rr)
 for sid,key in [('9100E66C-33E7-4AEE-B921-BC107610957C','tp'),('048B406C-BE30-4A2E-97F9-A72753A121D3','fp')]:
  rr=rows(sid)
  for i,t in enumerate(['RAD','BLAZE','Flexiplex']):rr[i][0]=rr[i][i+1]=str(discovery[t][key])
  edit(sid,rr)
 sid='52A2C540-4929-4698-BB41-5176D0B18C1B';rr=rows(sid)
 for i,k in enumerate(['f1','recall','precision']):
  for j,t in enumerate(['RAD','BLAZE','Flexiplex'],1):rr[i][j]=format(discovery[t][k],'.15g')
 edit(sid,rr)
 # Correction-only headlines; historical fixed5K columns retained.
 for sid,k in [('4B8EFB7D-5961-4D1B-84F1-D6FA39AF32C7','corrected_correct'),('37772031-416B-47A5-AAEF-0FF64BCA23FC','corrected_incorrect')]:
  rr=rows(sid)
  for j,t in enumerate(['BLAZE','RAD','Flexiplex'],1):rr[0][j]=str(tools[t]['totals'][k])
  edit(sid,rr)
  set_title(sid,{'corrected_correct':'Corrected correct assignment totals','corrected_incorrect':'Corrected incorrect assignment totals'}[k])
 # Native bars: preserve the source full-truth 5K reference increment (Flex 222371).
 sid='448995F1-96AC-4614-A785-176A654CEC8E';rr=rows(sid)
 for r in rr:
  if r[0] in tools:
   t=r[0];r[1]=str(tools[t]['totals']['native_correct']);r[3]=str(sum(v['all_incorrect'] for bc,v in tools[t]['rows'].items() if bc not in truthset))
 edit(sid,rr)
 assert {r[0]:r[2] for r in rr if r[0] in tools}=={'BLAZE':'0','Flexiplex':'222371','RAD':'0'}
 dtitle(table(sid)['dataSets'][1],'Full-truth 5K reference increment')
 set_title(sid,'Native correct assignments with full-truth 5K reference increment')
 sid='F77BA3D7-5161-4287-947E-F87AF98DADAF';rr=rows(sid)
 for i,t in enumerate(['RAD','BLAZE','Flexiplex']):rr[i][i+1]=str(tools[t]['totals']['native_correct'])
 edit(sid,rr)
 sid='F6376CA6-885E-415C-9035-E11EB49F448B';rr=rows(sid)
 for i,t in enumerate(['RAD','BLAZE','Flexiplex']):rr[i][i+1]=str(sum(v['all_incorrect'] for bc,v in tools[t]['rows'].items() if bc not in truthset))
 edit(sid,rr)
 # FP observations are selected false targets, not artificial zero observations for tools with none.
 sid='63ED301E-0F74-4D3A-886D-F7F9631B3309';fp=sorted(set().union(*(set(d['rows'])-truthset for d in tools.values())))
 rr=[[bc]+[str(tools[t]['rows'][bc]['all_incorrect']) if bc in tools[t]['rows'] else '' for t in ['BLAZE','RAD','Flexiplex']] for bc in fp]
 edit(sid,rr)
 tab=table(sid)
 for c,did in enumerate([tab['rowTitlesDataSet']]+tab['dataSets']):
  p=f'data/sets/{did}.json';d=js(p);inds=[i for i,r in enumerate(rr) if r[c]!='']
  for rep in d.get('replicates',[]):
   rep.pop('firstRow',None);rep.pop('lastRow',None)
   if inds:rep['firstRow']=inds[0];rep['lastRow']=inds[-1]
  putj(p,d)
 # Six underlying outcomes exhaust all reads; only the two correction outcomes are plotted.
 for t,sid in [('RAD','B3E0F44C-855D-4363-A355-2267133BA781'),('BLAZE','6A891CCF-953F-4BA6-B06C-DA6B6693C7FE'),('Flexiplex','28DC41C5-EC81-4A2B-87F9-2D94E2314B62')]:
  rr=[[label,str(tools[t]['totals'][k])] for label,k in zip(PIE_LABELS,PIE_STATES)];edit(sid,rr)
  for did in [table(sid)['rowTitlesDataSet']]+table(sid)['dataSets']:
   dp=f'data/sets/{did}.json';ds=js(dp)
   for rep in ds['replicates']:
    attrs=[]
    for a in rep.get('cellAttributes',[]):
     a={**a,'attributes':[v for v in a['attributes'] if v!='EXCLUDED']}
     if a['attributes']:attrs.append(a)
    attrs.extend([{'rows':'0','attributes':['EXCLUDED']},{'rows':'3~5','attributes':['EXCLUDED']}])
    rep['cellAttributes']=attrs
   putj(dp,ds)
  correction_total=tools[t]['totals']['corrected_correct']+tools[t]['totals']['corrected_incorrect']
  set_title(sid,f'{t} correction-only outcomes (plotted n={correction_total:,}; all-input table n=4,993,805)')
 # Older aggregate alternatives are made internally consistent for the three current tool columns.
 sid='34E8AE1E-2DCD-4259-95B3-F86294E8E563';rr=rows(sid)
 for i,(label,k) in enumerate([('Corrected correct','corrected_correct'),('Native correct','native_correct'),('All incorrect assignments','all_incorrect'),('Multiple outputs excluded','ambiguous')]):
  rr[i][0]=label
  for j,t in enumerate(['BLAZE','RAD','Flexiplex'],1):rr[i][j]=str(tools[t]['totals'][k])
 edit(sid,rr)
 # Transpose is deterministic data rearrangement, not a statistical test.
 tsid='DCE67226-5717-4515-B51D-5C0D69C5E5B5';old=rows(tsid)
 for i,r in enumerate(old):r[1:]=[rr[j][i+1] for j in range(4)]
 edit(tsid,old)
 for did,label in zip(table(tsid)['dataSets'],[r[0] for r in rr]):dtitle(did,label)
 sid='143E6D76-C580-4FB0-B793-B6F41DB235A9';rr=rows(sid)
 for j,t in enumerate(['BLAZE','RAD','Flexiplex'],1):rr[0][j]=str(tools[t]['totals']['ambiguous'])
 edit(sid,rr);set_title(sid,'Multiple-output exclusion totals (historical alternate graph)')
 sid='CB101D25-303A-4F5F-B259-277B87F4834A';rr=rows(sid)
 for r in rr:
  if r[0] in tools:r[1]=str(tools[r[0]]['totals']['corrected_correct']);r[2]='0';r[3]=''
 edit(sid,rr)
 # Match the existing pending-results archive convention: definitions remain, numeric results removed.
 for aid in INVALIDATE:
  p=f'analyses/{aid}/sheet.json';a=js(p);a['isCalculated']=False
  for res in a.get('resultSheets',[]):
   if '[recalculation required]' not in res['title']:res['title']+=' [recalculation required]'
   rp=f"analyses/{aid}/result_sheets/{res['uid']}.json";v=js(rp);v['name']=res['title'];v['textBlocks']=[{'block':'','fenID':0}];putj(rp,v)
   if v.get('dataSheet'):
    rt=table(v['dataSheet'])
    for n in original:
     if n.startswith(f"data/tables/{rt['uid']}/"):removed.add(n)
  putj(p,a);putj(f'analyses/{aid}/results.json',{'@class':'AnalysisResults'})
 # Exact known percentage text is updated at its original decimal precision and byte length.
 # The original formatting spans and every other graph binary byte remain intact.
 binary_annotation_log=[]
 pie_graph_tools={'B966F8E8-0320-49B2-ACD2-68E5E5FF8904':'RAD','83474767-C51C-4BC1-B6AB-E18E9B70436B':'BLAZE','98FF29A5-EA42-4F66-9919-ABA4DD8B11C4':'Flexiplex'}
 for n,b in original.items():
  if n.startswith('graphs/') and n.endswith('/data.bin'):
   matches=list(re.finditer(rb'([0-9]+\.[0-9]+)( ?% Correct \| )([0-9]+\.[0-9]+)( ?% Incorrect)',b))
   if matches:
    tool=pie_graph_tools[n.split('/')[1]];totals=tools[tool]['totals'];denom=totals['corrected_correct']+totals['corrected_incorrect'];new=bytearray(b)
    for m in matches:
     pc=len(m.group(1).split(b'.')[1]);pi=len(m.group(3).split(b'.')[1])
     text=f"{100*totals['corrected_correct']/denom:.{pc}f}".encode()+m.group(2)+f"{100*totals['corrected_incorrect']/denom:.{pi}f}".encode()+m.group(4)
     action='unchanged' if text==m.group() else 'updated'
     if len(text)!=len(m.group()):text=b' '*len(m.group());action='blanked_length_mismatch'
     new[m.start():m.end()]=text
     binary_annotation_log.append({'member':n,'offset':m.start(),'old_exact_text':m.group().decode(),'new_exact_text':text.decode(),'action':action,'tool':tool,'correction_denominator':denom})
    assert len(new)==len(b);replaced[n]=bytes(new)
    restored=bytearray(new)
    for m in matches:restored[m.start():m.end()]=m.group()
    assert bytes(restored)==b
 assert len(binary_annotation_log)==3
 layout_id='4B74E124-3EC5-4749-A164-AA426B306E0C'
 lp=f'layouts/{layout_id}/sheet.json';layout=js(lp)
 layout['title']='Main Figure — DATA UPDATED; VISUAL AND STATISTICAL REVIEW PENDING';putj(lp,layout)
 doc.setdefault('sheetAttributesMap',{}).setdefault(layout_id,{})['title']=layout['title']
 doc['uiSettings']['currentSheetType']='Layout';doc['uiSettings']['currentSheets']['layout']=layout_id
 putj('document.json',doc)
 args.output.parent.mkdir(parents=True,exist_ok=True)
 stage=args.output.with_suffix('.staging.prism')
 with zipfile.ZipFile(stage,'w') as z:
  for info in infos:
   if info.filename not in removed:z.writestr(info,replaced.get(info.filename,original[info.filename]))
 with zipfile.ZipFile(stage) as z:
  assert z.testzip() is None
  for n,b in replaced.items():assert z.read(n)==b
  for n in removed:assert n not in z.namelist()
 os.replace(stage,args.output)
 changed=[{'member':n,'before_sha256':hashlib.sha256(original[n]).hexdigest(),'after_sha256':hashlib.sha256(b).hexdigest()} for n,b in replaced.items() if b!=original[n]]
 log={
  'source':str(SOURCE),'source_sha256':EXPECTED,'output':str(args.output),
  'output_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
  'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'blaze_manifest':str(args.blaze_json),'blaze_condition':bcfg['condition'],
  'discovery_metrics':discovery,
  'assignment_totals':{t:d['totals'] for t,d in tools.items()},
  'exhaustive_totals':{t:{k:d['totals'][k] for k in PIE_STATES} for t,d in tools.items()},
  'correction_only_totals':{t:{'correct':d['totals']['corrected_correct'],'incorrect':d['totals']['corrected_incorrect'],'total':d['totals']['corrected_correct']+d['totals']['corrected_incorrect']} for t,d in tools.items()},
  'pie_table_row_order':PIE_STATES,'pie_plotted_zero_based_rows':[1,2],
  'pie_excluded_zero_based_rows':[0,3,4,5],
  'native_full_truth_reference_increment':{'RAD':0,'Flexiplex':222371,'BLAZE':0},
  'changed_members':changed,'removed_stale_result_members':sorted(removed),
  'invalidated_analyses':INVALIDATE,'replaced_literal_annotations':binary_annotation_log,
  'history_csv_directory':str(history),
  'graph_binding_strategy':'Native/corrected Flex D graph slots replaced with same verified selected-list Flex values as C, preserving blanks; D histories retained externally. Incorrect-per-truth-target graph binds C unchanged, now corrected incorrect only. Native full-truth reference increment222371 retained. Correction-only pies plot rows1/2 from six-state tables.',
  'required_native_verification':[
   'Open the closed corrected copy in Prism and save as native after checking tables/graphs.',
   'Inspect per-barcode panels for old significance brackets/stars; binary annotation objects were not guessed or deleted. No current statistical result is approved.',
   'Confirm correction-only pie graphs show rows1/2 only. Their denominators are RAD2135825, Flexiplex1680396 and BLAZE2014432; six-state source tables sum4993805.',
   'Inspect manual native/corrected/incorrect totals, percentages, legends, and bar labels for outdated cached/static text.',
   'Distinguish BLAZE corrected-incorrect all-target total133074 from per-truth-target subtotal132166.',
   'Confirm native graph retains Flex222371 full-truth reference increment and label distinguishes the reference from selected-list values.'
  ]}
 (BASE/'prism/Figure2_corrected_20261022_change_log.json').write_text(json.dumps(log,indent=2)+'\n')
 print(json.dumps({'output':str(args.output),'changed_members':len(changed),'invalidated_analyses':len(INVALIDATE),'native_visual_verification_pending':True},indent=2))
if __name__=='__main__':main()
