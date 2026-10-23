#!/usr/bin/env python3
"""Independent saved-archive audit; never opens Prism or changes the archive."""
import csv
import hashlib
import io
import json
import pathlib
import sys
import zipfile
from datetime import datetime, timezone

BASE = pathlib.Path('/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022')
P = BASE / 'prism'
SRC = BASE / 'evidence/092126_Figure_2_CMV_V18.prism'
OUT = P / 'Figure2_corrected_20261022.prism'
EXPECTED_SOURCE = 'd8cc036cdca79d607be863fd15a9bc4721c4e86d09721ea4b368401fa9b3a10c'
PIN = sys.argv[1]
checks = []
def check(name, passed, details=None):
    item = {'check': name, 'pass': bool(passed)}
    if details is not None:
        item['details'] = details
    checks.append(item)
def sha(b):
    return hashlib.sha256(b).hexdigest()
source_bytes, output_bytes = SRC.read_bytes(), OUT.read_bytes()
check('Pinned corrected archive', sha(output_bytes) == PIN, sha(output_bytes))
if sha(output_bytes) != PIN:
    raise SystemExit('Archive no longer matches closed checkpoint; stop before auditing')
check('Evidence source unchanged', sha(source_bytes) == EXPECTED_SOURCE, sha(source_bytes))
sp = json.loads((P / 'Figure2_corrected_20261022_source_preservation.json').read_text())
check('Original Dropbox source unchanged', sha(pathlib.Path(sp['dropbox_original']).read_bytes()) == EXPECTED_SOURCE)
zs = zipfile.ZipFile(io.BytesIO(source_bytes))
zo = zipfile.ZipFile(io.BytesIO(output_bytes))
check('ZIP CRC integrity', zo.testzip() is None)
check('No duplicate ZIP names', len(zo.namelist()) == len(set(zo.namelist())))
old = {n: zs.read(n) for n in zs.namelist()}
new = {n: zo.read(n) for n in zo.namelist()}
parsed = {n: json.loads(b) for n,b in new.items() if n.endswith('.json')}
check('All JSON documents parse', True, len(parsed))
log = json.loads((P/'Figure2_corrected_20261022_change_log.json').read_text())
actual_changed = {n for n in old.keys() & new.keys() if old[n] != new[n]}
actual_removed = old.keys() - new.keys()
actual_added = new.keys() - old.keys()
check('Changed member inventory exact', actual_changed == {e['member'] for e in log['changed_members']})
check('Removed member inventory exact', actual_removed == set(log['removed_stale_result_members']))
check('No undocumented new members', not actual_added, sorted(actual_added))
for e in log['changed_members']:
    check('Member hashes: '+e['member'], sha(old[e['member']]) == e['before_sha256'] and sha(new[e['member']]) == e['after_sha256'])

allowed_binary = {
 'graphs/83474767-C51C-4BC1-B6AB-E18E9B70436B/data.bin': ('93.3% Correct | 6.7% Incorrect','93.4% Correct | 6.6% Incorrect'),
 'graphs/B966F8E8-0320-49B2-ACD2-68E5E5FF8904/data.bin': ('91.02% Correct | 8.98% Incorrect','91.03% Correct | 8.97% Incorrect'),
}
binary_changed = {n for n in actual_changed if not n.endswith(('.json','.csv','.dt'))}
check('Only two approved binary annotations changed', binary_changed == set(allowed_binary))
for n, (before,after) in allowed_binary.items():
    b,a = before.encode(),after.encode()
    check('Exact equal-length percentage replacement: '+n, len(b)==len(a) and old[n].count(b)==1 and old[n].replace(b,a)==new[n])
flex_binary='graphs/98FF29A5-EA42-4F66-9919-ABA4DD8B11C4/data.bin'
check('Flex pie percentage annotation remains exactly unchanged and rounds correctly',old[flex_binary]==new[flex_binary] and b'83.24% Correct | 16.76 % Incorrect' in new[flex_binary])
check('All layout binaries and embedded media unchanged', all(old[n]==new[n] for n in old.keys() & new.keys() if (n.startswith(('layouts/','media/')) and not n.endswith('.json'))))

CAN = BASE/'evidence/figure2_canonical_rad_flex'
def dict_rows(path, delimiter=','):
    with path.open(newline='') as f:
        return list(csv.DictReader(f, delimiter=delimiter))
rf = {name:dict_rows(CAN/f'{name}_truth5000_aligned_per_barcode.csv') for name in ['RAD','Flexiplex']}
rf_selected = {name:dict_rows(CAN/f'{name}_selected_per_barcode.csv') for name in ['RAD','Flexiplex']}
rf_info=json.loads((CAN/'canonical_results.json').read_text())
bl = dict_rows(P/'blaze2023_assignment_replay/per_barcode.tsv', '\t')
blmap={r['barcode']:r for r in bl}
truth=[r['barcode'] for r in rf['RAD']]
truth_set=set(truth)
check('Canonical truth universe contains 5000 unique rows', len(truth)==len(truth_set)==5000)
check('Canonical RF barcode alignment identical', truth==[r['barcode'] for r in rf['Flexiplex']])
check('BLAZE selected targets 5015 unique, all 5000 truth plus 15 extras', len(bl)==len(blmap)==5015 and truth_set <= blmap.keys() and len(blmap.keys()-truth_set)==15)
check('Flex selected list 3004 unique truth targets', len(rf_selected['Flexiplex'])==len({r['barcode'] for r in rf_selected['Flexiplex']})==3004 and all(r['barcode'] in truth_set for r in rf_selected['Flexiplex']))
states=['native_correct','corrected_correct','all_incorrect','ambiguous','unassigned']
totals={name:{key:rf_info[name]['counts'][key] for key in states} for name in rf}
totals['BLAZE']={
 'native_correct':sum(int(r['native_correct']) for r in bl),
 'corrected_correct':sum(int(r['corrected_correct']) for r in bl),
 'all_incorrect':sum(int(r['native_incorrect'])+int(r['corrected_incorrect']) for r in bl),
 'ambiguous':0,
 'unassigned':4993805-sum(int(r['assigned']) for r in bl),
}
for name in rf:
    for key in ['native_correct','corrected_correct','all_incorrect']:
        check(f'{name} canonical array sums agree with raw audit tabulation: {key}', sum(int(r[key]) for r in rf_selected[name])==totals[name][key])
for name, counts in totals.items():
    check(name+' exhaustive denominator', sum(counts.values())==4993805, counts)
check('BLAZE row state partition', all(int(r['assigned'])==sum(int(r[k]) for k in ['native_correct','corrected_correct','native_incorrect','corrected_incorrect']) for r in bl))
extra=[r for r in bl if r['barcode'] not in truth_set]
extra_assigned=sum(int(r['assigned']) for r in extra)
truth_incorrect=sum(int(r['native_incorrect'])+int(r['corrected_incorrect']) for r in bl if r['barcode'] in truth_set)
check('BLAZE all-target versus truth-target partition', extra_assigned==1091 and truth_incorrect==132747 and totals['BLAZE']['all_incorrect']==133838)
check('BLAZE extra native/corrected incorrect', sum(int(r['native_incorrect']) for r in extra)==183 and sum(int(r['corrected_incorrect']) for r in extra)==908)

def sheet(sid):
    return parsed[f'data/sheets/{sid}/sheet.json']
def table(sid):
    uid=sheet(sid)['table']['uid']
    return list(csv.reader(io.StringIO(new[f'data/tables/{uid}/data.csv'].decode())))
def nint(s):
    return None if s=='' else int(s)
per_sheets={
 'native_correct':'63D81234-28AC-46E8-8332-CB1AE2FC1AFF',
 'corrected_correct':'66EF3D96-C86B-4FA9-ACE5-53621808DA50',
 'corrected_incorrect':'98505F94-3866-4F00-A8CD-E076CF542357',
}
per_summary={}
for metric,sid in per_sheets.items():
    rows=table(sid)
    check(metric+' exact 5000 row barcode order', len(rows)==5000 and [r[0] for r in rows]==truth)
    check(metric+' six CSV columns', all(len(r)==6 for r in rows))
    blexpected=[int(blmap[b]['native_incorrect'])+int(blmap[b]['corrected_incorrect']) if metric=='all_incorrect' else int(blmap[b][metric]) for b in truth]
    check(metric+' exact BLAZE cells', [nint(r[1]) for r in rows]==blexpected)
    check(metric+' exact RAD cells', [nint(r[2]) for r in rows]==[nint(r[metric]) for r in rf['RAD']])
    flex_expected=[nint(r[metric]) for r in rf['Flexiplex']]
    check(metric+' exact selected Flex cells', [nint(r[3]) for r in rows]==flex_expected)
    check(metric+' exactly 1996 missing Flex values', sum(r[3]=='' for r in rows)==1996)
    if metric != 'corrected_incorrect':
        check(metric+' mirrored graph-bound Flex D equals selected C including blanks', [r[4] for r in rows]==[r[3] for r in rows])
    per_summary[metric]={name:sum(nint(r[col]) or 0 for r in rows) for name,col in [('BLAZE',1),('RAD',2),('Flexiplex',3)]}

pie_sheets={
 'RAD':'B3E0F44C-855D-4363-A355-2267133BA781',
 'BLAZE':'6A891CCF-953F-4BA6-B06C-DA6B6693C7FE',
 'Flexiplex':'28DC41C5-EC81-4A2B-87F9-2D94E2314B62',
}
six_states=['native_correct','corrected_correct','corrected_incorrect','native_incorrect','ambiguous','unassigned']
pie_labels=['Native correct','Corrected correct','Corrected incorrect','Native incorrect','Multiple outputs excluded','Unassigned']
six_totals={name:dict(counts) for name,counts in totals.items()}
for name in six_totals:
    if name in rf:
        for key in ['native_incorrect','corrected_incorrect']:
            six_totals[name][key]=rf_info[name]['counts'][key]
    else:
        for key in ['native_incorrect','corrected_incorrect']:
            six_totals[name][key]=sum(int(r[key]) for r in bl)
    check(name+' all incorrect partition by correction state',six_totals[name]['all_incorrect']==six_totals[name]['native_incorrect']+six_totals[name]['corrected_incorrect'])
    check(name+' six states exhaustive',sum(six_totals[name][k] for k in six_states)==4993805)
correction_totals={name:c['corrected_correct']+c['corrected_incorrect'] for name,c in six_totals.items()}
check('Exact correction-only denominators',correction_totals=={'RAD':2135825,'Flexiplex':1680396,'BLAZE':2014432})
for name,sid in pie_sheets.items():
    rows=table(sid)
    check(name+' six exact pie states', rows==[[label,str(six_totals[name][key])] for label,key in zip(pie_labels,six_states)])
    tab=sheet(sid)['table']
    for uid in [tab['rowTitlesDataSet']]+tab['dataSets']:
        ds=parsed[f'data/sets/{uid}.json']
        excluded=[x for rep in ds['replicates'] for x in rep.get('cellAttributes',[]) if 'EXCLUDED' in x.get('attributes',[])]
        exrows=set()
        for attr in excluded:
            for token in attr['rows'].split(','):
                endpoints=[int(x) for x in token.split('~')]
                exrows.update(range(endpoints[0],endpoints[-1]+1))
        check(name+' pie includes only correction states, excludes native/multiple/unassigned: '+uid, exrows=={0,3,4,5}, excluded)
        check(name+' pie metadata spans all six rows: '+uid, all(rep.get('firstRow',0)==0 and rep.get('lastRow')==5 for rep in ds['replicates']))

check('Whitelist TP exact cells',table('9100E66C-33E7-4AEE-B921-BC107610957C')==[['5000','5000','',''],['5000','','5000',''],['3004','','','3004']])
check('Whitelist FP exact cells',table('048B406C-BE30-4A2E-97F9-A72753A121D3')==[['0','0','',''],['15','','15',''],['0','','','0']])
disc=table('9FA3BE17-60E1-4F42-8084-62CD9B3AE250')
check('Stacked discovery exact TP FP FN cells',disc[:3]==[['BLAZE','5000','15','0'],['Flexiplex','3004','0','1996'],['RAD','5000','0','0']] and all(not any(r) for r in disc[3:]))
perf=table('52A2C540-4929-4698-BB41-5176D0B18C1B')
expected_perf=[[1,10000/10015,6008/8004],[1,1,3004/5000],[1,5000/5015,1]]
check('Discovery F1 sensitivity precision full precision',all(abs(float(perf[i][j+1])-expected_perf[i][j])<1e-14 for i in range(3) for j in range(3)))

# All-target headline counts: array panel J intentionally uses truth-target subtotal.
raw=table('34E8AE1E-2DCD-4259-95B3-F86294E8E563')
for row,key in enumerate(['corrected_correct','native_correct','all_incorrect','ambiguous']):
    check('Raw count headline '+key, [int(x) for x in raw[row][1:4]]==[totals[t][key] for t in ['BLAZE','RAD','Flexiplex']])
for sid,key in [('4B8EFB7D-5961-4D1B-84F1-D6FA39AF32C7','corrected_correct'),('37772031-416B-47A5-AAEF-0FF64BCA23FC','corrected_incorrect'),('143E6D76-C580-4FB0-B793-B6F41DB235A9','ambiguous')]:
    check('Headline selected tools '+key,[int(x) for x in table(sid)[0][1:4]]==[six_totals[t][key] for t in ['BLAZE','RAD','Flexiplex']])
native_alt=table('448995F1-96AC-4614-A785-176A654CEC8E')
source_native_alt=list(csv.reader(io.StringIO(old['data/tables/8DCF6CC1-F58F-4F14-AFA9-249161E0D372/data.csv'].decode())))
check('Flex reference overlay unchanged from preserved source control',native_alt[1][2]==source_native_alt[1][2]=='222371')
for hist in sorted((P/'history_before_20261022').glob('*.csv')):
    sh=json.loads(old[f'data/sheets/{hist.stem}/sheet.json'])
    member='data/tables/'+sh['table']['uid']+'/data.csv'
    check('Historical original CSV preserved: '+hist.name,hist.read_bytes()==old[member])
check('Main native-count plot and fixed5K overlay',native_alt[:3]==[['BLAZE','640957','0','1091'],['Flexiplex','463613','222371','0'],['RAD','667965','0','0']])
native_main=table('F77BA3D7-5161-4287-947E-F87AF98DADAF')
check('Native scalar alternate table', [int(native_main[i][i+1]) for i in range(3)]==[totals[t]['native_correct'] for t in ['RAD','BLAZE','Flexiplex']])
fp=table('F6376CA6-885E-415C-9035-E11EB49F448B')
check('FP target scalar table', [int(fp[i][i+1]) for i in range(3)]==[0,1091,0])
fp_rows=table('63ED301E-0F74-4D3A-886D-F7F9631B3309')
check('15 exact BLAZE FP target count cells',len(fp_rows)==15 and {r[0]:int(r[1]) for r in fp_rows}=={r['barcode']:int(r['assigned']) for r in extra} and all(r[2:]==['',''] for r in fp_rows))
trans=table('DCE67226-5717-4515-B51D-5C0D69C5E5B5')
check('Transposed count cache current selected tools',all(trans[i][1:]==[str(totals[t][k]) for k in ['corrected_correct','native_correct','all_incorrect','ambiguous']] for i,t in enumerate(['BLAZE','RAD','Flexiplex'])))

# Validate the changed table metadata rather than just the plotted values.
changed_csv={n for n in actual_changed if n.endswith('/data.csv')}
changed_tables={n.split('/')[2] for n in changed_csv}
for n in sorted(changed_csv):
    rows=list(csv.reader(io.StringIO(new[n].decode())))
    meta=parsed[n.replace('data.csv','content.json')]
    widths={len(r) for r in rows}
    check('CSV rectangular and metadata dimensions: '+n, widths=={meta['numberOfColumns']} and len(rows)==meta['numberOfRows'], {'rows':len(rows),'widths':sorted(widths),'metadata':meta})
    check('Table SHA256 prefix .dt: '+n,new[n.replace('.csv','.dt')].decode()==sha(new[n])[:32])
for n,s in parsed.items():
    if not n.startswith('data/sheets/') or not n.endswith('sheet.json') or s['table']['uid'] not in changed_tables:
        continue
    meta=parsed['data/tables/'+s['table']['uid']+'/content.json']
    t=s['table']
    for uid in [t.get('rowTitlesDataSet'),t.get('xDataSet')]+t.get('dataSets',[]):
        if not uid:
            continue
        ds=parsed[f'data/sets/{uid}.json']
        check('Changed table dataset bounds: '+uid, all(0<=r.get('firstRow',0)<=r.get('lastRow',meta['numberOfRows']-1)<meta['numberOfRows'] for r in ds.get('replicates',[])), ds.get('replicates',[]))

expected_bindings={
 'C7434C91-4E18-4805-93E3-FCBE8777D387': ['55733904-0FA1-4462-9987-5CDECF83A340','7A817AB2-8B3F-4B5F-85FB-0984A7A35D99','B7A95E01-DCE4-4964-ADD1-71CF919FE6DE'],
 '618D16ED-954A-44DD-B5C8-FA74FF1CD274': ['FF40BBC9-474C-49EC-85C5-707493619F18','33CFF86A-A5F5-4454-B030-E0492F0A9B49','25C79583-B71F-4587-A42E-2C295A006D14'],
 '3568D2DE-F40D-46FE-B8F5-7C7BB63AA49F': ['BA645DAC-CA07-4E30-82F8-81C9505CB8BF','594B2375-BAC7-43FF-8B3D-89B48CF0526B','9EAF2EAD-1268-45DD-A97B-95FB03243A40'],
}
for uid,sets in expected_bindings.items():
    check('Main per-barcode graph selected-list bindings: '+uid,parsed[f'graphs/{uid}/sheet.json']['inputDataSets']==sets)
for n,d in parsed.items():
    if n.startswith('graphs/') and n.endswith('sheet.json'):
        check('Graph declared dataset links resolve: '+d['uid'],all(f'data/sets/{uid}.json' in new for uid in d.get('inputDataSets',[])))

expected_invalidated=['E2C721DC-CF0D-45D4-A198-0E9955653EDC','1692D0EE-34B0-47E1-AA9A-B1A96AD55A39','BB4EB3C9-1C4C-4843-B4D5-72F9942D120C','6868ACFE-05E0-455D-B273-BCB0856BE80B','5BD85BDF-0140-4146-8921-64C4ABC643C5','AA4C6237-DB10-425A-866F-F7E130BDA8F1']
for uid in expected_invalidated:
    a=parsed[f'analyses/{uid}/sheet.json']
    check('Analysis explicitly uncalculated: '+uid,a.get('isCalculated') is False)
    check('Analysis aggregate result cleared: '+uid,parsed[f'analyses/{uid}/results.json']=={'@class':'AnalysisResults'})
    for result in a.get('resultSheets',[]):
        v=parsed[f'analyses/{uid}/result_sheets/{result["uid"]}.json']
        check('Analysis result title flagged stale: '+result['uid'],'recalculation required' in v.get('name',''))
        check('Analysis text cache cleared: '+result['uid'],all(not b.get('block') for b in v.get('textBlocks',[])))
        ds=sheet(v['dataSheet'])
        f='data/tables/'+ds['table']['uid']+'/data.csv'
        check('Analysis numeric cache empty or removed: '+result['uid'],f not in new or not any(c for row in csv.reader(io.StringIO(new[f].decode())) for c in row))

report={
 'audited_utc':datetime.now(timezone.utc).isoformat(),
 'auditor':'evidence_inventory independent audit; no writer implementation or writer validation assertions reused',
 'source':str(SRC),'source_sha256':sha(source_bytes),'corrected':str(OUT),'corrected_sha256':sha(output_bytes),
 'status':'PASS_SAVED_DATA_AND_STRUCTURE_NATIVE_REVIEW_PENDING' if all(c['pass'] for c in checks) else 'FAIL',
 'checks_passed':sum(c['pass'] for c in checks),'checks_total':len(checks),
 'failures':[c for c in checks if not c['pass']],
 'canonical_totals':totals,'six_state_totals':six_totals,'correction_only_denominators':correction_totals,'per_barcode_truth_target_sums':per_summary,
 'BLAZE_extra_target_assignments':extra_assigned,'BLAZE_truth_target_all_incorrect':truth_incorrect,'BLAZE_truth_target_corrected_incorrect':sum(int(r['corrected_incorrect']) for r in bl if r['barcode'] in truth_set),
 'archive_changes':{'changed':len(actual_changed),'removed':len(actual_removed),'added':len(actual_added)},
 'graph_intent_reference':str(BASE/'extracted/figure_images/paragraph_2_image2.png'),
 'graph_intent':'Source Figure2 F is Correction totals within Error-corrected barcodes; D shows selected-list native correct counts plus the explicit Flex fixed5000 reference increment. Independently viewed image confirms this.',
 'limitations':[
  'Native Prism opening, recalculation, saving and visual rendering were not performed because the user is using Prism.',
  'Data and saved graph dataset bindings are verified. Pie dataset EXCLUDED metadata is checked to show only corrected correct/incorrect states. Binary plot caches, displayed labels, significance annotations, legends, and other native row selections still require visual review.',
  'Six existing analyses are marked uncalculated and old result caches cleared. No new statistical test was approved or computed.',
  'BLAZE assignment is a new deterministic cached-table replay performed on 2026-10-22, not a previously saved 2023 assignment run.',
  'RAD assignment uses the preserved exact5000-global/custom adapter-fix contract; global-chemistry-whitelist equivalence was not tested.',
 ],
 'input_artifact_hashes':{str(path):sha(path.read_bytes()) for path in [CAN/'RAD_truth5000_aligned_per_barcode.csv',CAN/'Flexiplex_truth5000_aligned_per_barcode.csv',CAN/'canonical_results.json',P/'blaze2023_assignment_replay/per_barcode.tsv',P/'blaze2023_assignment_replay/provenance.json']},
 'checks':checks,
}
(P/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['status','checks_passed','checks_total','failures','corrected_sha256','archive_changes']},indent=2))
