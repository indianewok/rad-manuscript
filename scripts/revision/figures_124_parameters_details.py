"""Bind selected Figure4 rows to recovered producer records, not global versions."""
import csv,json,re
from pathlib import Path
from figures_124 import sha,rows,write_json

def recover(base,output,keep):
 result={}
 # The F4 flat-Q20 grid is a DIFFERENT RAD build from F2's paired-quality grid.
 pkg=base/'wl_scan/20260731_sctagger_badread_quality_full'
 metrics={(r['dataset'],r['tool']):r for r in rows(pkg/'analysis/combined_metrics.tsv') if r['case']=='flatQ20'}
 current={(r['canonical_id'],r['tool']):r for r in rows(output/'source_data/figure_04/barcode_detection_metrics.tsv')}
 rp=dict(line.rstrip().split('\t',1) for line in (pkg/'provenance/rad/provenance.tsv').open())
 software=keep(pkg/'provenance/tool_and_whitelist_sha256.txt','04_ScTagger_software_hashes.txt')
 keep(pkg/'provenance/rad/provenance.tsv','04_ScTagger_RAD_build.tsv')
 for size in ('S','L'):
  sample=f'ScTagger-{size}_flatQ20'
  for tool,folder in [('RAD','rad'),('BLAZE','blaze'),('Flexiplex','flexiplex')]:
   for key in ('calls','tp','fp','fn'):
    assert current[(sample,tool)][key]==metrics[(size,tool)][key],(sample,tool,key)
   run=pkg/'runs'/folder/size/'flatQ20'
   command_files=[run/'command.txt'] if tool!='Flexiplex' else [run/'discovery.command.txt',run/'filter.command.txt']
   command_text='\n'.join(x.read_text().strip() for x in command_files)
   ev='; '.join(keep(x,f'04_ScTagger_{size}_{tool}_{x.name}') for x in command_files)
   keep(run/'provenance.tsv',f'04_ScTagger_{size}_{tool}_run.tsv')
   identity={'RAD':(rp['rad_version'],rp['git_commit'],rp['binary_sha256']),'BLAZE':('2.6.0a0','exact native launcher/parser/pipeline hashes; commit unrecovered','46d36e12fb0dfd4ce3c403169bdb9a6574eddc8e5b26363afe40867471f994dc'),'Flexiplex':('1.02.6','exact pristine executable hash; commit unrecovered in producing records','62a41db2407e2675b8d1bc4201839c9d47b8d102116a0f1d504346ecfc753e10')}[tool]
   result[(sample,tool)]=dict(version=identity[0],commit_or_build=identity[1],binary_or_source_sha256=identity[2],exact_command_or_recorded_settings=command_text,command_status='exact saved command; producing metrics match selected counts',chemistry_layout='10x3v3; RAD resource10x_3v3.1; barcode16; adapter CTACACGACGCTCTTCCGATCT',seed='flatQ20 fixed synthetic sequences; no explicit tool seed',threads='16' if tool=='Flexiplex' else '8',evidence=ev+'; '+software,evidence_sha256=sha(command_files[0]))
 # RAGE cell-line and immune-reference LN retain direct binary provenance.
 for sample,name in [('RAGEseq-cell-line','20260730_rageseq_ERR3268991_cellline_control'),('RAGEseq-TNBC-LN','20260730_rageseq_ERR3268990_tnbc_lymphnode_four_tool')]:
  pkg=base/'wl_scan'/name;prov=pkg/'analysis/tool_provenance.tsv'
  ev=keep(prov,f'04_{sample}_tool_provenance.tsv')
  producer=rows(prov)
  commands=pkg/'run_after_download.sh'
  if not commands.exists():
   candidates=list(pkg.glob('run*.sh'));commands=candidates[0] if len(candidates)==1 else pkg/'COMMANDS.md'
  cmd=keep(commands,f'04_{sample}_producer.sh') if commands and commands.exists() else ''
  for tool in ('RAD','BLAZE','Flexiplex'):
   r=next(x for x in producer if x['method']==tool and x['component'] in ('RAD binary','BLAZE2','Flexiplex binary'))
   digest=r['sha256_or_note'];match=re.search('[0-9a-f]{64}',digest)
   result[(sample,tool)]=dict(version=r['version_or_revision'],commit_or_build=r['version_or_revision'],binary_or_source_sha256=match.group() if match else 'unrecovered in this producer record',exact_command_or_recorded_settings='Exact executed producer shell template '+cmd if cmd else 'unrecovered expanded argv; tool provenance table available',command_status='executed shell template' if cmd else 'version evidence only',chemistry_layout='10x3v2;16nt barcode/10ntUMI; adapter CTACACACGACGCTCTTCCGATCT (see executed source for exact adapter)',evidence=ev+('; '+cmd if cmd else ''),evidence_sha256=sha(output/ev))
   result[(sample,tool)]['chemistry_layout']='10x3v2;16nt barcode/10nt UMI; adapter CTACACGACGCTCTTCCGATCT'
  for tool in ('RAD','BLAZE','Flexiplex'):
   result[(sample,tool)]['threads']='32' if sample=='RAGEseq-cell-line' else ('10' if tool=='Flexiplex' else '16')
  if sample=='RAGEseq-TNBC-LN':
   launch=next(x for x in producer if x['component']=='entry-point script');result[(sample,'BLAZE')]['binary_or_source_sha256']=re.search('[0-9a-f]{64}',launch['sha256_or_note']).group()
 # Native RAD ScMix source remains native; other two selected ScMix rows are reconstructions.
 pkg=base/'scratch_preservation_20260921/files/rad_scmix2_20260726/results/fixed_scmix2_scanwl_e03_t24_full_20260726'
 cmd=keep(pkg/'cases/01_full/command.sh','04_ScMixology2_RAD_command.sh')
 keep(pkg/'run_config.tsv','04_ScMixology2_RAD_run.tsv')
 keep(pkg/'provenance/git_head.txt','04_ScMixology2_RAD_git_head.txt')
 keep(pkg/'provenance/git_status.txt','04_ScMixology2_RAD_git_status.txt')
 keep(pkg/'provenance/checksums.sha256','04_ScMixology2_RAD_checksums.sha256')
 result[('ScMixology2','RAD')]=dict(version='version text retained in source help; binary hash identifies exact build',commit_or_build=(pkg/'provenance/git_head.txt').read_text().strip()+'; source branch fix/longbench-memory; build_fixed untracked',binary_or_source_sha256=(pkg/'provenance/checksums.sha256').read_text().split()[0],exact_command_or_recorded_settings=(pkg/'cases/01_full/command.sh').read_text().strip(),command_status='exact executed command; callset verified against retained RDS',chemistry_layout='10x3v3;16nt barcode;adapter CTACACGACGCTCTTCCGATCT',seed='no explicit tool seed',threads='24',evidence=cmd,evidence_sha256=sha(output/cmd))
 # ScMix BLAZE selector reconstruction has a published-analysis identity, not a native run pin.
 pkg=base/'blaze_single_cell_expect_sweep_20260810/exploratory/scmixology2'
 ev=keep(pkg/'provenance.json','04_ScMixology2_BLAZE_provenance.json')
 source=keep(pkg/'scripts/reconstruct_expect_sweep.py','04_ScMixology2_BLAZE_selector.py')
 command=keep(pkg/'scripts/run.sh','04_ScMixology2_BLAZE_command.sh')
 bp=json.loads((pkg/'provenance.json').read_text())
 result[('ScMixology2','BLAZE')]=dict(version='published selector reconstruction; BLAZE2.5.0 cross-check library',commit_or_build='published analysis '+bp['published_analysis_commit'],binary_or_source_sha256=sha(pkg/'scripts/reconstruct_expect_sweep.py'),exact_command_or_recorded_settings=(pkg/'scripts/run.sh').read_text().strip()+'; selected expect500; '+bp['published_selector_semantics'],command_status='exact reconstruction script and launch command; no authentic native selected callset',chemistry_layout='10x3v3 design; Q>=15 native raw-barcode cache',seed='no random seed in reconstructed deterministic selector',threads='see executed launch; selector worker count not specified',evidence=ev+'; '+source+'; '+command,evidence_sha256=sha(pkg/'provenance.json'))
 full=base/'wl_scan/20260804_common_count_selector_ablation/provenance/Flex_full37_run_manifest.json'
 manifest=json.loads(full.read_text());entry=next(x for x in manifest['datasets'] if x['dataset']=='scMixology2')
 ev='source_data/figure_04/producing_evidence/ScMixology2_Flexiplex_selected_run.json'
 write_json(output/ev,dict(full_source_path=str(full),full_source_sha256=sha(full),selection='datasets row with dataset=scMixology2',selected_run=entry,source_analysis=manifest['analysis'],chemistry_whitelist_handling=manifest['chemistry_whitelist_handling']))
 result[('ScMixology2','Flexiplex')]=dict(version='1.02.6 filter reconstruction on RAD counts',commit_or_build='exact filter identity in selected-run provenance; native extraction not used',binary_or_source_sha256='unrecovered filter binary digest in current manifest',exact_command_or_recorded_settings=json.dumps(entry['command']),command_status='exact selector argv; common-count reconstruction',chemistry_layout=manifest['chemistry_whitelist_handling'],seed='deterministic selector; no explicit seed',threads='no worker count in saved argv',evidence=ev,evidence_sha256=sha(output/ev))
 from figures_124_parameters_more import recover as recover_more
 result.update(recover_more(base,output,keep))
 # Allow root's independent producer recovery to augment other Figure4 runs.
 additions=output/'manifests/figures_124_parameter_additions.tsv'
 if additions.exists():
  for row in rows(additions):
   key=(row.pop('canonical_id'),row.pop('tool'));result.setdefault(key,{}).update({k:v for k,v in row.items() if v})
 return result
