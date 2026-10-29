#!/usr/bin/env python3
"""Recover producing-run settings without borrowing versions from other runs."""
import argparse,json,shutil
from pathlib import Path
from source_paths import data_root, resolve_source
from figures_124 import REPO,sha,rows,write_rows,write_json,NATIVE,EXTENDED,SWEEP
from tool_parameter_schema import FIELDS, project_parameters, details_path_name, prepare_evidence_rows
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--project-root',type=Path,default=data_root())
p.add_argument('--output-root',type=Path,default=REPO)
a=p.parse_args();B=a.project_root/'reviewer_comment_data';O=a.output_root
fields=['figure','experiment','producing_run','tool','version','commit_or_build','binary_or_source_sha256','exact_command_or_recorded_settings','command_status','chemistry_layout','reference_whitelist','seed','threads','evidence','evidence_sha256','applies_to','limitation']
output=[];evidence=[]
def add(**kw):
 r={k:'unrecovered' for k in fields};r.update(kw);output.append(r)
def kv(path):
 with Path(path).open() as f:return dict(x.rstrip('\n').split('\t',1) for x in f if '\t' in x)
def keep(path,name):
 path=Path(path);dest=O/'source_data'/f'figure_{name[:2]}'/'producing_evidence'/name[3:]
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
 evidence.append(dict(path=str(dest.relative_to(O)),source_path=str(path),source_sha256=sha(path),source_bytes=path.stat().st_size,sha256=sha(dest),bytes=dest.stat().st_size))
 return str(dest.relative_to(O))
# Every accepted timing phase has its own exact saved command and resource record.
soft=kv(O/'source_data/figure_01/software_and_resources.tsv')
for r in rows(O/'source_data/figure_01/accepted_phase_records.tsv'):
 t=r['tool'];prefix=t.lower()
 add(figure='01',experiment='complete-input timing',producing_run='|'.join(r[k] for k in ('dataset','tool','threads','replicate','phase')),tool=t,
 version=soft[prefix+'_version'],commit_or_build=soft[prefix+'_commit'],binary_or_source_sha256=soft.get(prefix+'_sha256',soft.get(prefix+'_launcher_sha256')),
 exact_command_or_recorded_settings=r['command'],command_status='exact saved command, SHA256 '+r['command_sha256'],
 chemistry_layout='10x3v3; RAD layout SHA256 '+soft['layout_sha256'],reference_whitelist='global3v3 SHA256 '+soft['global_whitelist_sha256']+'; selected whitelist SHA256 '+r['whitelist_sha256'],
 seed='PYTHONHASHSEED=0; no other explicit seed' if t=='BLAZE' else 'no explicit seed in saved command',threads=r['threads'],evidence='source_data/figure_01/accepted_phase_records.tsv',evidence_sha256=sha(O/'source_data/figure_01/accepted_phase_records.tsv'),
 applies_to=r['dataset']+'; '+r['phase'],limitation='BLAZE identity includes launcher; Flex discovery includes filter phase; auxiliary compression threads recorded in exact command')
# The HD stage is distinct; no timing or later-demux pin is imputed to detection.
hd_table=O/'source_data/figure_01/hd_stage_counts.tsv'
if hd_table.is_file():
 for h in rows(hd_table):
  add(figure='01',experiment='HD whitelist-detection count source',producing_run=h['flowcell']+'|RAD_valid_pair_detection',tool='RAD',version='unrecovered',commit_or_build='unrecovered original detection build',binary_or_source_sha256='unrecovered',exact_command_or_recorded_settings='unrecovered original detection argv; complete valid-pair count table SHA256 '+h['source_sha256'],command_status='count-source identity and whole-table total verified; original execution not recovered',chemistry_layout='VisiumHD; paired barcode sequence; plotted16um bins',reference_whitelist='original design pair membership; exact generating resources unrecovered',seed='unrecovered',threads='unrecovered',evidence='source_data/figure_01/producing_evidence/HD_selected_count_definition.json; source_data/figure_01/hd_stage_counts.tsv',evidence_sha256=sha(O/'source_data/figure_01/producing_evidence/HD_selected_count_definition.json'),applies_to=h['flowcell']+' count column; representative plot isPBC44593',limitation='Whole-table total matches original valid-pair counts. Full per-bin creation provenance and selected spatial assets unavailable; no later-demux build substituted.')
# Preserve only code/provenance actually used to produce the selected discovery grids.
run_case=keep(B/SWEEP/'code/original_three_tool_sweep/run_case.sh','02_discovery_run_case.sh')
native_soft=keep(B/NATIVE/'provenance/software.tsv','02_discovery_software.tsv')
keep(B/NATIVE/'provenance/tool_equivalence.tsv','02_discovery_tool_equivalence.tsv')
blaze_replay=keep(B/EXTENDED/'blaze_replay/provenance/replay_blaze.executed.py','02_discovery_blaze_replay.py')
blaze_prov=keep(B/EXTENDED/'blaze_replay/provenance/provenance.json','02_discovery_blaze_replay_provenance.json')
blaze_cmd=keep(B/EXTENDED/'blaze_replay/provenance/commands.txt','02_discovery_blaze_replay_commands.txt')
software={r['component']:r for r in rows(B/NATIVE/'provenance/software.tsv')}
rad_receipt=B/'LongBench_comps/full_A_to_B_audit_20260731/provenance/producers/rad/SC_ONT/run_metadata.txt'
rad_identity=dict(line.split('=',1) for line in rad_receipt.read_text().splitlines() if '=' in line)
assert rad_identity['rad_binary_sha256']==software['RAD']['sha256']
rad_receipt_link=keep(rad_receipt,'02_discovery_RAD_same_binary_build_receipt.txt')
seen=set()
for r in rows(O/'source_data/figure_02/discovery_callset_manifest.tsv'):
 path=resolve_source(r['resolved_path'],base=B);tool=r['tool'];t=tool.split('_')[0]
 # Reused RAD/Flex quality-invariant callsets are one producing run, with multiple applications.
 if str(path) in seen:continue
 seen.add(str(path));s=software[t];metadata=path.parent/'run_metadata.tsv'
 if metadata.is_file():
  m=kv(metadata);command=m.get('command','unrecovered');status='exact saved run metadata';ev=keep(metadata,'02_discovery_runs/'+r['dataset']+'_'+r['condition']+'_'+tool+'.tsv')
 else:
  command='unrecovered expanded argv; see exact executed template '+run_case;status='executed shell template; expanded command not saved';ev=run_case
 if 'blaze_replay' in str(path):
  command='exact executed replay source '+blaze_replay+'; shell commands '+blaze_cmd;status='exact selector replay code/parameters; no FASTQ tool rerun';ev=blaze_prov
 elif r['model']!='nanopore2023' and not metadata.is_file():
  command+='; arguments: '+r['dataset']+' '+r['condition']+' INPUT; RAD scan-wl -p CTACACGACGCTCTTCCGATCT -n16 -e0.3 -w10x_3v3 -t8 -k10000 -v; BLAZE --expect-cells '+('50' if r['dataset']=='S' else '5000')+' --10x-kit-version3v3 --minQ15 --threads8 --no-emtpy-drops --no-demultiplexing; Flex -d10x3v3 -f'+('0' if tool=='Flexiplex_f0' else '8')+' -e2 -p8 plus filter'
 same=[x['condition'] for x in rows(O/'source_data/figure_02/discovery_callset_manifest.tsv') if x['resolved_path']==str(path)]
 add(figure='02',experiment='barcode discovery',producing_run=f"{r['dataset']}|{r['model']}|{r['condition']}|{tool}",tool=tool,version=s['version_or_identity'],commit_or_build=(rad_identity['rad_commit']+'; '+rad_identity['rad_patch_label']+'; same exact binary SHA256 as direct discovery receipt') if t=='RAD' else 'unrecovered commit; exact executable/package identity recorded',binary_or_source_sha256=s['sha256'],exact_command_or_recorded_settings=command,command_status=status,chemistry_layout='10x3v3; adapter CTACACGACGCTCTTCCGATCT; 16nt barcode',reference_whitelist='10x3v3 design; exact truth '+('50' if r['dataset']=='S' else '5000')+' barcodes for scoring',seed='generation S2018=20260727; L2018/L2023=20260731; selector no explicit RNG seed',threads='8 for native tools; replay threads see executed code',evidence=ev+'; '+native_soft+('; '+rad_receipt_link if t=='RAD' else ''),evidence_sha256=sha(O/ev),applies_to=r['dataset']+' conditions '+','.join(same),limitation='Discovery is separate from assignment; repeated quality-invariant source callset is not a fresh run; historical lexical model path is part of generation seed')
# Distinct read-assignment producers.
rad=B/'sctagger_L_rad_fixed5000_adapter_fix_20260817';rk=kv(rad/'provenance.tsv');ev=keep(rad/'provenance.tsv','02_assignment_RAD_provenance.tsv');cmd=keep(rad/'command.sh.txt','02_assignment_RAD_command.sh');keep(rad/'L_flatQ20_rad_adapter_fix_layout.csv','02_assignment_RAD_layout.csv')
add(figure='02',experiment='physical-read assignment',producing_run='L_flatQ20_RAD_adapter_fix',tool='RAD',version=rk['rad_version'],commit_or_build=rk['git_commit'],binary_or_source_sha256=rk['rad_binary_sha256'],exact_command_or_recorded_settings=(rad/'command.sh.txt').read_text().strip(),command_status='exact saved command',chemistry_layout='10x3v3 16nt barcode/12nt UMI; layout '+rk['layout_sha256'],reference_whitelist='same truth5000 global+custom SHA256 '+rk['global_whitelist_sha256'],seed='no explicit seed',threads=rk['threads'],evidence=ev+'; '+cmd,evidence_sha256=sha(O/ev),applies_to='assignment states/per-selected-target/correction proportions',limitation='Repeated physical read IDs excluded entirely')
flex=B/'sctagger_flexiplex_audit_20260812';ev=keep(flex/'L_audit.runner.log','02_assignment_Flexiplex_run.log');keep(flex/'run_audit_20260812.sh','02_assignment_Flexiplex_command.sh')
pin=B/'software_pins_20260810/flexiplex_raw_to_assigned_audit/validation/longbench_prefix/tool_provenance.tsv';keep(pin,'02_assignment_Flexiplex_software.tsv');fk=kv(pin)
command=next(x[len('command='):] for x in (flex/'L_audit.runner.log').read_text().splitlines() if x.startswith('command='))
add(figure='02',experiment='physical-read assignment',producing_run='L_flatQ20_Flexiplex_raw_to_assigned_audit',tool='Flexiplex',version=fk['upstream_version']+' diagnostic raw-to-assigned build',commit_or_build=fk['upstream_commit'],binary_or_source_sha256=fk['diagnostic_binary_sha256'],exact_command_or_recorded_settings=command,command_status='exact saved command; defaults retained from pinned source',chemistry_layout='10x3v3; default f8/e2; 16nt barcode/12nt UMI',reference_whitelist='own native selected3004; filename in exact command',seed='no explicit seed',threads='16; pigz4',evidence=ev,evidence_sha256=sha(O/ev),applies_to='assignment states/per-selected-target/correction proportions',limitation='Identical-target duplicate IDs collapsed; conflicting-target IDs excluded; diagnostic output adds RawCellBarcode')
bl=B/'paper_revision_20261022/prism/blaze2023_assignment_replay';bp=json.loads((bl/'provenance.json').read_text());ev=keep(bl/'provenance.json','02_assignment_BLAZE_provenance.json');keep(bl/'matcher_whitelist_iteration_order.txt','02_assignment_BLAZE_iteration_order.txt')
add(figure='02',experiment='physical-read assignment',producing_run='L_native2023_BLAZE_incremental_matcher_replay',tool='BLAZE',version='2.6.0a0 _match_bc_row',commit_or_build='exact stock matcher source; commit unrecovered',binary_or_source_sha256=bp['matcher_sha256'],exact_command_or_recorded_settings='max_edit_distance=2; minQ=0; retained seed0 candidate order; incremental exact replay method: '+bp['method'],command_status='matcher parameters/method recovered; entrypoint argv unrecovered',chemistry_layout='native2023 extraction 10x3v3; unchanged sequence/error collection',reference_whitelist='5015 selected targets=5000truth+15extra; iteration order deposited',seed='retained archived seed0 order; appended new candidates lexically',threads='unrecovered for matcher replay',evidence=ev,evidence_sha256=sha(O/ev),applies_to='assignment states/per-selected-target/correction proportions',limitation='Full source assignment records independently rescored; not new FASTQ extraction')
# Figure4 settings come only from the current per-input table and receipts.
current=rows(O/'source_data/figure_04/tool_parameters.tsv')
selected=rows(O/'source_data/figure_04/barcode_detection_metrics.tsv')
keys={(r['canonical_id'],r['tool']) for r in selected}
if len(current)!=111 or {(r['dataset'],r['tool']) for r in current}!=keys:
 raise ValueError('Current Figure4 tool parameters must cover all37 three-tool inputs')
producers=O/'source_data/figure_04/producing_run_evidence.tsv'
wide_current=O/'manifests'/details_path_name('124')
wide_current={(row['applies_to'],row['tool']):row for row in rows(wide_current) if row['figure']=='04'} if wide_current.exists() else {}
for r in current:
 dataset,tool=r['dataset'],r['tool']
 selected_row=next(x for x in selected if x['canonical_id']==dataset and x['tool']==tool)
 receipt_path=O/'source_data/figure_04/producing_evidence/current_RAD'/(dataset+'.json')
 if tool=='RAD':
  receipt=json.loads(receipt_path.read_text())
  if r['source_commit']!='4acbe004ba11b150d6832395452632f367a6e6c1' or receipt['max_error']!=0.3:
   raise ValueError('Current Figure4 RAD source/error pin differs: '+dataset)
  ev=str(receipt_path.relative_to(O));digest=receipt['binary_sha256']
 else:
  previous=wide_current.get((dataset,tool))
  if previous:
   payload={key:previous[key] for key in fields}
   payload.update(version=r['version'],exact_command_or_recorded_settings=r['command'],threads=r['threads'],chemistry_layout=r['chemistry'])
   if previous.get('evidence_original_sha256'):payload['evidence_original_sha256']=previous['evidence_original_sha256']
   add(**payload)
   continue
  ev=str(producers.relative_to(O));digest='not_recorded'
 add(figure='04',experiment='barcode discovery across37inputs',producing_run=dataset+'|'+tool,
     tool=tool,version=r['version'],commit_or_build=r['source_commit'],binary_or_source_sha256=digest,
     exact_command_or_recorded_settings=r['command'],command_status='current per-input command record',
     chemistry_layout=r['chemistry'],reference_whitelist=selected_row['reference_type']+'; n='+selected_row['reference_n'],
     seed='not_recorded',threads=r['threads'],evidence=ev,evidence_sha256=sha(O/ev),
     applies_to=dataset,limitation='Descriptive matched-reference barcode-set comparison')
output=prepare_evidence_rows(output,O)
write_rows(O/'manifests'/details_path_name('124'),output,fields+['evidence_original_sha256'])
write_rows(O/'manifests/figures_124_tool_parameters.tsv',project_parameters(output,'124',O),FIELDS)
write_rows(O/'manifests/figures_124_parameter_evidence.tsv',evidence)
write_json(O/'validation/figures_124_parameter_recovery.json',dict(status='recorded with explicit unresolved identities',producing_runs=len(output),figure_counts={f:sum(r['figure']==f for r in output) for f in ['01','02','04']},figure4_source_parameters=dict(path='source_data/figure_04/tool_parameters.tsv',sha256=sha(O/'source_data/figure_04/tool_parameters.tsv')),no_global_version_imputation=True))
print('Recorded',len(output),'producing-run rows; unknown means unrecovered, not default.')
