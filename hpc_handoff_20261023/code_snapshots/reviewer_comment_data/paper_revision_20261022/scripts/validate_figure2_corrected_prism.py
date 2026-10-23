from pathlib import Path
import csv,io,json,hashlib,zipfile
base=Path('/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022');prism=base/'prism';out=prism/'Figure2_corrected_20261022.prism';source=base/'evidence/092126_Figure_2_CMV_V18.prism'
log=json.loads((prism/'Figure2_corrected_20261022_change_log.json').read_text());inventory=json.loads((base/'evidence/figure2_prism_inventory.json').read_text());checks=[]
def check(name,condition,detail=None):
 checks.append({'check':name,'passed':bool(condition),'detail':detail});assert condition,(name,detail)
with zipfile.ZipFile(source) as z:old={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(out) as z:
 check('native archive CRC',z.testzip() is None);new={n:z.read(n) for n in z.namelist()}
check('source SHA256 preserved',hashlib.sha256(source.read_bytes()).hexdigest()==log['source_sha256'])
check('output SHA256 recorded',hashlib.sha256(out.read_bytes()).hexdigest()==log['output_sha256'])
check('only logged member removals',set(old)-set(new)==set(log['removed_stale_result_members']))
check('no unexpected additions',not(set(new)-set(old)))
changed={n for n in new if old[n]!=new[n]};check('only logged member changes',changed=={r['member'] for r in log['changed_members']})
getj=lambda n:json.loads(new[n])
def table(sid):return getj(f'data/sheets/{sid}/sheet.json')['table']
def rows(sid):return list(csv.reader(io.StringIO(new[f"data/tables/{table(sid)['uid']}/data.csv"].decode())))
# Every changed CSV is verified against its recorded token, storage dimensions and bounds.
for n in sorted(changed):
 if not n.endswith('/data.csv'):continue
 rr=list(csv.reader(io.StringIO(new[n].decode())));prefix=n.rsplit('/',1)[0]
 if prefix+'/data.dt'in new:check('refresh token '+prefix,new[prefix+'/data.dt'].decode()==hashlib.sha256(new[n]).hexdigest()[:32])
 if prefix+'/content.json'in new:
  c=getj(prefix+'/content.json');check('CSV dimensions '+prefix,c['numberOfRows']==len(rr) and c['numberOfColumns']==max(map(len,rr),default=0))
 sid=next(s['uid'] for s in inventory['data_sheets'].values() if s['table_uid']==prefix.split('/')[-1]);t=table(sid);ids=[t[k] for k in ['rowTitlesDataSet','xDataSet'] if k in t]+t['dataSets'];col=0
 for did in ids:
  for rep in getj('data/sets/'+did+'.json').get('replicates',[]):
   indices=[i for i,r in enumerate(rr) if len(r)>col and r[col]!=''];expected=(min(indices),max(indices)) if indices else(None,None)
   check('dataset bounds '+did,(rep.get('firstRow'),rep.get('lastRow'))==expected);col+=1
 history=prism/'history_before_20261022'/f'{sid}.csv';check('original CSV preserved '+sid,history.read_bytes()==old[n])
# Independent expected-row loading uses canonical source CSVs directly.
canon={}
for tool,path in [('RAD',base/'evidence/figure2_canonical_rad_flex/RAD_selected_per_barcode.csv'),('Flexiplex',base/'evidence/figure2_canonical_rad_flex/Flexiplex_selected_per_barcode.csv'),('BLAZE',prism/'blaze2023_assignment_replay/BLAZE_selected_per_barcode.csv')]:
 with path.open(newline='') as f:canon[tool]={r['barcode']:r for r in csv.DictReader(f)}
metrics=['native_correct','corrected_correct','corrected_incorrect'];sids=['63D81234-28AC-46E8-8332-CB1AE2FC1AFF','66EF3D96-C86B-4FA9-ACE5-53621808DA50','98505F94-3866-4F00-A8CD-E076CF542357'];labels=[]
for metric,sid in zip(metrics,sids):
 rr=rows(sid);labels.append([r[0] for r in rr]);check('5000 unique truth barcode rows '+metric,len(rr)==5000 and len(set(labels[-1]))==5000)
 for tool,c in [('BLAZE',1),('RAD',2),('Flexiplex',3)]:
  check('every canonical cell '+metric+' '+tool,all(r[c]==str(canon[tool][r[0]][metric]) if r[0] in canon[tool] else r[c]=='' for r in rr))
 if metric!='corrected_incorrect':check('currently bound Flex graph slot equals selected condition '+metric,all(r[3]==r[4] for r in rr))
 check('Flex nonselected remains missing '+metric,sum(r[3]=='' for r in rr)==1996)
check('truth barcode alignment all panels',labels[0]==labels[1]==labels[2])
for tool,sid in [('RAD','B3E0F44C-855D-4363-A355-2267133BA781'),('BLAZE','6A891CCF-953F-4BA6-B06C-DA6B6693C7FE'),('Flexiplex','28DC41C5-EC81-4A2B-87F9-2D94E2314B62')]:
 rr=rows(sid);check('six exhaustive table states '+tool,len(rr)==6 and sum(int(r[1]) for r in rr)==4993805);check('verified state totals '+tool,[int(r[1]) for r in rr]==[log['exhaustive_totals'][tool][k] for k in ['native_correct','corrected_correct','corrected_incorrect','native_incorrect','ambiguous','unassigned']])
 check('pie row labels '+tool,[r[0] for r in rr]==['Native correct','Corrected correct','Corrected incorrect','Native incorrect','Multiple outputs excluded','Unassigned'])
 for did in [table(sid)['rowTitlesDataSet']]+table(sid)['dataSets']:
  ds=getj(f'data/sets/{did}.json')
  for rep in ds['replicates']:
   excluded=set()
   for a in rep.get('cellAttributes',[]):
    if 'EXCLUDED' in a['attributes']:
     for q in a['rows'].split(','):
      z=list(map(int,q.split('~')));excluded.update(range(z[0],z[-1]+1))
   check('correction-only excluded rows '+tool+' '+did,excluded=={0,3,4,5})
   check('correction-only plotted total '+tool+' '+did,sum(int(r[1]) for i,r in enumerate(rr) if i not in excluded)==log['correction_only_totals'][tool]['total'])
 check('correction-only canonical values '+tool,int(rr[1][1])==sum(int(x['corrected_correct']) for x in canon[tool].values()) and int(rr[2][1])==sum(int(x['corrected_incorrect']) for x in canon[tool].values()))
for metric,sid in [('corrected_correct','4B8EFB7D-5961-4D1B-84F1-D6FA39AF32C7'),('corrected_incorrect','37772031-416B-47A5-AAEF-0FF64BCA23FC')]:
 rr=rows(sid)
 for col,tool in enumerate(['BLAZE','RAD','Flexiplex'],1):check('correction-only headline '+metric+' '+tool,int(rr[0][col])==sum(int(x[metric]) for x in canon[tool].values()))
nr=rows('448995F1-96AC-4614-A785-176A654CEC8E')
check('native full-truth 5K reference increment preserved',{r[0]:int(r[2]) for r in nr if r[0] in canon}=={'RAD':0,'Flexiplex':222371,'BLAZE':0})
check('native reference clearly titled',getj('data/sets/85AEE557-0B12-4586-8DB7-D58EC7FC0971.json')['title']=='Full-truth 5K reference increment')
fp=rows('63ED301E-0F74-4D3A-886D-F7F9631B3309');truth=set(labels[0]);check('BLAZE false target observations',len(fp)==15 and {r[0] for r in fp}==set(canon['BLAZE'])-truth);check('FP assignment counts',all(r[1]==canon['BLAZE'][r[0]]['all_incorrect'] for r in fp));check('no fabricated FP observations',all(r[2]==r[3]==''for r in fp))
for aid in log['invalidated_analyses']:
 check('analysis pending '+aid,getj('analyses/'+aid+'/sheet.json')['isCalculated']is False and getj('analyses/'+aid+'/results.json')=={'@class':'AnalysisResults'})
for gid,g in inventory['graphs'].items():
 p=f'graphs/{gid}/sheet.json';newg=getj(p);check('graph dataset references preserved '+gid,newg.get('inputDataSets')==g.get('inputDataSets'))
 for did in newg.get('inputDataSets',[]):check('graph dataset exists '+gid+' '+did,'data/sets/'+did+'.json'in new)
check('all three manual percent labels reviewed',len(log['replaced_literal_annotations'])==3)
for a in log['replaced_literal_annotations']:
 n=a['member'];o=a['offset'];before=a['old_exact_text'].encode();after=a['new_exact_text'].encode()
 check('literal percentage length preserved '+a['tool'],len(before)==len(after) and len(old[n])==len(new[n]))
 check('literal percentage region exact '+a['tool'],old[n][o:o+len(before)]==before and new[n][o:o+len(after)]==after)
 restored=new[n][:o]+before+new[n][o+len(after):]
 check('only exact percentage bytes changed '+a['tool'],restored==old[n])
report={'source':str(source),'output':str(out),'passed':True,'checks':checks,'check_count':len(checks),'important_limitations':['Prism was not launched, per user request to open later.','Correction-only pie exclusions and reference increment are verified in saved data; native rendered geometry, cached/static labels and significance markers are not visually verified.','Six stale statistical results are cleared; no replacement tests or p-values were produced.','Main layout is explicitly marked DATA UPDATED; VISUAL AND STATISTICAL REVIEW PENDING.']}
(prism/'Figure2_corrected_20261022_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(checks),'output':str(out)},indent=2))
