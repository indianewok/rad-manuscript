#!/usr/bin/env python3
"""Recover producing-run settings without borrowing versions from other runs."""
import argparse,csv,json,re,shutil
from pathlib import Path
from figures_124 import REPO,sha,rows,write_rows,write_json,TIMING,NATIVE,EXTENDED,SWEEP
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--project-root',type=Path,default=Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data'))
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
 evidence.append(dict(path=str(dest.relative_to(O)),source_path=str(path),sha256=sha(path),bytes=path.stat().st_size))
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
 path=Path(r['resolved_path']);tool=r['tool'];t=tool.split('_')[0]
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
add(figure='02',experiment='physical-read assignment',producing_run='L_flatQ20_RAD_adapter_fix',tool='RAD',version=rk['rad_version'],commit_or_build=rk['git_commit'],binary_or_source_sha256=rk['rad_binary_sha256'],exact_command_or_recorded_settings=(rad/'command.sh.txt').read_text().strip(),command_status='exact saved command',chemistry_layout='10x3v3 16nt barcode/12nt UMI; layout '+rk['layout_sha256'],reference_whitelist='same truth5000 global+custom SHA256 '+rk['global_whitelist_sha256'],seed='no explicit seed',threads=rk['threads'],evidence=ev+'; '+cmd,evidence_sha256=sha(O/ev),applies_to='six states/per-selected-target/correction proportions',limitation='Repeated physical read IDs excluded entirely')
flex=B/'sctagger_flexiplex_audit_20260812';ev=keep(flex/'L_audit.runner.log','02_assignment_Flexiplex_run.log');keep(flex/'run_audit_20260812.sh','02_assignment_Flexiplex_command.sh')
pin=B/'software_pins_20260810/flexiplex_raw_to_assigned_audit/validation/longbench_prefix/tool_provenance.tsv';keep(pin,'02_assignment_Flexiplex_software.tsv');fk=kv(pin)
command=next(x[len('command='):] for x in (flex/'L_audit.runner.log').read_text().splitlines() if x.startswith('command='))
add(figure='02',experiment='physical-read assignment',producing_run='L_flatQ20_Flexiplex_raw_to_assigned_audit',tool='Flexiplex',version=fk['upstream_version']+' diagnostic raw-to-assigned build',commit_or_build=fk['upstream_commit'],binary_or_source_sha256=fk['diagnostic_binary_sha256'],exact_command_or_recorded_settings=command,command_status='exact saved command; defaults retained from pinned source',chemistry_layout='10x3v3; default f8/e2; 16nt barcode/12nt UMI',reference_whitelist='own native selected3004; filename in exact command',seed='no explicit seed',threads='16; pigz4',evidence=ev,evidence_sha256=sha(O/ev),applies_to='six states/per-selected-target/correction proportions',limitation='Identical-target duplicate IDs collapsed; conflicting-target IDs excluded; diagnostic output adds RawCellBarcode')
bl=B/'paper_revision_20261022/prism/blaze2023_assignment_replay';bp=json.loads((bl/'provenance.json').read_text());ev=keep(bl/'provenance.json','02_assignment_BLAZE_provenance.json');keep(bl/'matcher_whitelist_iteration_order.txt','02_assignment_BLAZE_iteration_order.txt')
add(figure='02',experiment='physical-read assignment',producing_run='L_native2023_BLAZE_incremental_matcher_replay',tool='BLAZE',version='2.6.0a0 _match_bc_row',commit_or_build='exact stock matcher source; commit unrecovered',binary_or_source_sha256=bp['matcher_sha256'],exact_command_or_recorded_settings='max_edit_distance=2; minQ=0; retained seed0 candidate order; incremental exact replay method: '+bp['method'],command_status='matcher parameters/method recovered; entrypoint argv unrecovered',chemistry_layout='native2023 extraction 10x3v3; unchanged sequence/error collection',reference_whitelist='5015 selected targets=5000truth+15extra; iteration order deposited',seed='retained archived seed0 order; appended new candidates lexically',threads='unrecovered for matcher replay',evidence=ev,evidence_sha256=sha(O/ev),applies_to='six states/per-selected-target/correction proportions',limitation='Full source assignment records independently rescored; not new FASTQ extraction')
# Figure4: attach settings to each selected input/tool observation, not one global pin.
master_path=B/'master_native_comparison_20260811/tables/master_native_comparison_long.tsv';master={(r['physical_input_run'],r['tool']):r for r in rows(master_path)}
selected=rows(O/'source_data/figure_04/barcode_detection_metrics.tsv')
current_evidence=[]
for r in selected:
 m=master.get((r['canonical_id'],r['tool']),{});settings=m.get('tool_settings') or 'unrecovered';version=m.get('tool_version') or 'unrecovered'
 current_evidence.append(dict(canonical_id=r['canonical_id'],tool=r['tool'],tool_version=version,tool_settings=settings,source_table_path=m.get('source_table_path',r['source_path']),source_callset_path=m.get('source_callset_path',''),reference_type=r['reference_type'],reference_n=r['reference_n'],source_method=r['source_method']))
 ev='source_data/figure_04/producing_run_evidence.tsv'
 add(figure='04',experiment='barcode discovery across37inputs',producing_run=r['canonical_id']+'|'+r['tool'],tool=r['tool'],version=version,commit_or_build='unrecovered unless explicit in version/settings',binary_or_source_sha256='unrecovered',exact_command_or_recorded_settings=settings,command_status='recorded source-table settings only; exact expanded argv unrecovered',chemistry_layout='unrecovered unless stated in settings',reference_whitelist=r['reference_type']+'; n='+r['reference_n']+'; '+r['reference_description'],seed='unrecovered',threads=(re.search(r'threads[=:]([0-9]+)',settings).group(1) if re.search(r'threads[=:]([0-9]+)',settings) else 'unrecovered'),evidence=ev,evidence_sha256='filled after writing evidence',applies_to=r['canonical_id'],limitation=r['source_method']+'; '+r['input_status']+'; no versions inferred from README or other experiments')
write_rows(O/'source_data/figure_04/producing_run_evidence.tsv',current_evidence)
for r in output:
 if r['figure']=='04':r['evidence_sha256']=sha(O/r['evidence'])
# Preserve exact primary LN commands as additional current provenance without borrowing binary identities.
keep(B/'wl_scan/20260730_rageseq_ERR3268990_tnbc_lymphnode_four_tool/COMMANDS.md','04_RAGE_TNBC_commands.md')
keep(B/'wl_scan/20260730_rageseq_ERR3268990_tnbc_lymphnode_four_tool/run_after_download.sh','04_RAGE_TNBC_executed.sh')
for r in output:
 if r['figure']=='04' and r['applies_to']=='RAGEseq-TNBC-LN':
  r['evidence']+='; source_data/figure_04/producing_evidence/RAGE_TNBC_commands.md; source_data/figure_04/producing_evidence/RAGE_TNBC_executed.sh'
  r['chemistry_layout']='10x3v2; 16nt barcode/10nt UMI; adapter CTACACGACGCTCTTCCGATCT'
  r['exact_command_or_recorded_settings']='exact executed shell template: source_data/figure_04/producing_evidence/RAGE_TNBC_executed.sh; primary RADscan e0.3/t16; BLAZEexpect10433/kit3v2/t16/ED2; Flexf8/t10/defaultED2 plus native filter'
  r['command_status']='exact shell template; binary versions/hashes unrecovered except BLAZE2.6.0a0 label'
  r['threads']='10' if r['tool']=='Flexiplex' else '16'
  if r['tool']=='BLAZE':r['version']='2.6.0a0'
from figures_124_parameters_details import recover
details=recover(B,O,keep)
for r in output:
 if r['figure']=='04':r.update(details.get((r['applies_to'],r['tool']),{}))
write_rows(O/'manifests/figures_124_tool_parameters.tsv',output,fields)
write_rows(O/'manifests/figures_124_parameter_evidence.tsv',evidence)
write_json(O/'validation/figures_124_parameter_recovery.json',dict(status='recorded with explicit unresolved identities',producing_runs=len(output),figure_counts={f:sum(r['figure']==f for r in output) for f in ['01','02','04']},source_master=dict(path=str(master_path),sha256=sha(master_path)),no_global_version_imputation=True))
print('Recorded',len(output),'producing-run rows; unknown means unrecovered, not default.')
