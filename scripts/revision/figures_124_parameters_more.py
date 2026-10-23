"""Additional Figure4 producer recovery from exact saved commands/receipts."""
import json,re
from pathlib import Path
from figures_124 import sha,rows

def recover(base,output,keep):
 result={}
 def metadata(path,sep='='):
  return dict(x.split(sep,1) for x in path.read_text().splitlines() if sep in x)
 def command(path):
  lines=[x.strip().split('Command being timed:',1)[1].strip().strip('"') for x in path.read_text().splitlines() if 'Command being timed:' in x]
  return lines[0] if lines else path.read_text().strip()
 def evidence(path,name):return keep(path,'04_'+name)
 def record(sample,tool,files,**kw):
  links=[evidence(p,sample+'_'+tool+'_'+p.name) for p in files]
  result[(sample,tool)]=dict(evidence='; '.join(links),evidence_sha256=sha(files[0]),**kw)
 # LongBench RAD discovery is identified by the scan-specific GNU-time command.
 pkg=base/'LongBench_comps/full_A_to_B_audit_20260731/provenance/producers'
 for short in ('SC_ONT','SN_ONT','SC_PB','SN_PB'):
  sample='LongBench-'+short.replace('_','-')
  path=pkg/'rad'/short;meta=metadata(path/'run_metadata.txt')
  record(sample,'RAD',[path/'run_metadata.txt',path/'scan_wl_time.txt'],version=meta['rad_version'],commit_or_build=meta['rad_commit']+'; '+meta['rad_patch_label'],binary_or_source_sha256=meta['rad_binary_sha256'],exact_command_or_recorded_settings=command(path/'scan_wl_time.txt'),command_status='exact scan-wl producing command; excludes later demux settings',chemistry_layout='10x3v3.1;adapter CTACACGACGCTCTTCCGATCT;barcode16',threads=meta['threads'],seed='no explicit seed in saved scan argv')
  path=pkg/'blaze'/short;meta=metadata(path/'run_metadata.txt')
  record(sample,'BLAZE',[path/'run_metadata.txt',path/'time.txt'],version=meta['blaze2_version'],commit_or_build='full commit unrecovered in producing receipt',binary_or_source_sha256='unrecovered in producing receipt',exact_command_or_recorded_settings=command(path/'time.txt'),command_status='exact producing command saved by GNU time',chemistry_layout='3v3 default; full_bc_whitelist=none (bundled design)',threads=meta['threads'],seed='PYTHONHASHSEED='+meta['PYTHONHASHSEED'])
 # PromethION exact selected tracks: RAD907, BLAZE804 (expect500), Flex801.
 pkg=base/'wl_scan/20260730_promethion_four_tool_benchmark'
 meta=metadata(pkg/'provenance/MANIFEST.tsv','\t')
 for tool,track,version in [('RAD','rad_scan_e01','unversioned CLI; exact binary preserved'),('BLAZE','blaze_expect500','2.6.0a0'),('Flexiplex','flexiplex_f8','1.02.6')]:
  time=pkg/'results'/track/'time.txt'
  if not time.exists():
   candidates=list((pkg/'results'/track).glob('*time*.txt'));time=candidates[0] if len(candidates)==1 else pkg/'provenance/run_selection_tools.sh'
  record('PromethION_iPSC',tool,[pkg/'provenance/MANIFEST.tsv',pkg/'provenance/run_selection_tools.sh',time],version=version,commit_or_build=(meta['rad_source_git_head']+'; modified source; patch SHA256 '+meta['rad_source_patch_sha256']) if tool=='RAD' else 'unrecovered commit in producer receipt',binary_or_source_sha256=meta['rad_binary_sha256'] if tool=='RAD' else 'unrecovered in producer receipt',exact_command_or_recorded_settings=command(time),command_status='exact selected producing track; BLAZEexpect500 is primary',threads='32',seed='no explicit seed in saved producer command',chemistry_layout='10x3v3;barcode16/UMI12;RADscan e0.1;Flexf8')
 # LeBrigand: combined two-accession run, not the separate single-accession experiment.
 pkg=base/'wl_scan/20260731_lebrigand_MOB_complete_two_accession_benchmark'
 cmd=pkg/'scripts/run_combined_benchmark.sh'
 for tool,version in [('RAD','1.0.2 build920adda_edlibfix'),('BLAZE','2.6.0a0 native executable'),('Flexiplex','1.02.6 release executable')]:
  record('LeBrigand-MOB',tool,[cmd,pkg/'provenance/input_manifest.tsv'],version=version,commit_or_build='build label/path recorded; run-specific binary digest/full commit unrecovered',binary_or_source_sha256='unrecovered in combined-run receipt',exact_command_or_recorded_settings='Exact executed shell source '+str(cmd)+'; selected track '+tool+' (Flexiplex_f8); RAD e0.3; BLAZEexpect918/full4992/UMI12; Flextolerancef8/e2',command_status='executed combined-run template; expanded argv unrecovered',threads='12',seed='no explicit seed in producing template',chemistry_layout='Visium combined SRR12157794+SRR12157795; full4992 design; selected calls RAD915/BLAZE844/Flex196')
 # Measles P7/P8VDJ: discovery RAD callsets were reused; never borrow demux build.
 pkg=base/'wl_scan/20260801_measles_p7_four_tool'
 for sample,short in [('Measles-P7','p7'),('Measles-P8-VDJ-enriched','p8')]:
  scan=base/'wl_scan/scanwl_statistical_experiments_20260728_30/adaptive_floor_20260728'/('measles_'+short+'_final')
  record(sample,'RAD',[scan/'time.verbose.txt'],version='unrecovered; native adaptive-floor discovery callset',commit_or_build='unrecovered original scan build; later demux build deliberately not used',binary_or_source_sha256='unrecovered',exact_command_or_recorded_settings=command(scan/'time.verbose.txt'),command_status='exact original scan command, selected940/9490callset retained',threads='see exact argv',seed='no explicit seed in saved scan command',chemistry_layout='10x3v3;barcode16;adapter CTACACGACGCTCTTCCGATCT')
  for tool,version in [('BLAZE','2.6.0a0'),('Flexiplex','1.02.6 release')]:
   record(sample,tool,[pkg/'scripts/run_sample.sh',pkg/'provenance/tool_checksums.tsv'],version=version,commit_or_build='unrecovered full commit in producer receipt',binary_or_source_sha256='6eee3a7113044d45e106dc74a541b9a53475311449bf49bd91cc912ba911c40e' if tool=='Flexiplex' else 'unrecovered in producer receipt',exact_command_or_recorded_settings='Exact executed run_sample.sh '+short+'; BLAZEexpect'+('964' if short=='p7' else '10299')+' kit3v3 ED2; Flex release discovery f8 (diagnostic assignment binary not used)',command_status='exact executed parameterized shell template',threads='16' if tool=='Flexiplex' else '24',seed='no explicit seed in template',chemistry_layout='10x3v3;16nt barcode;10nt UMI as source manifest')
 # Measles whole transcriptome is a distinct complete input and RAD build.
 pkg=base/'scratch_preservation_20260921/files/measles_p8_whole_three_tool_20260801'
 meta=metadata(pkg/'provenance/run_manifest.tsv','\t')
 for tool in ['RAD','BLAZE','Flexiplex']:
  script=pkg/'scripts'/('run_'+tool.lower()+'.sh')
  record('Measles-P8-WTA',tool,[pkg/'provenance/run_manifest.tsv',script],version='1.0.2' if tool=='RAD' else meta[tool.lower()+'_version'],commit_or_build=meta['rad_commit'] if tool=='RAD' else 'unrecovered full commit in producer receipt',binary_or_source_sha256=(pkg/'provenance/rad_binary.sha256').read_text().split()[0] if tool=='RAD' else 'unrecovered in producer receipt',exact_command_or_recorded_settings=script.read_text().strip(),command_status='exact executed whole-transcriptome producer script',threads='24',seed='no explicit random seed in producer template',chemistry_layout=meta['chemistry']+';16nt barcode/12nt UMI')
 # Isosceles commands are explicitly verbatim reconstructions; label them as such.
 pkg=base/'scratch_preservation_20260921/files/rad_biological_benchmark_20260731/runs/GSE248115'
 for tool,sub,version in [('RAD','RAD','build path rad_920adda; full commit/version unrecovered'),('BLAZE','BLAZE_expect2462','2.6.0a0 native executable'),('Flexiplex','Flexiplex/discovery','1.02.6 release executable')]:
  cmd=pkg/sub/'command.sh'
  record('Isosceles-ovarian-GSE248115',tool,[cmd],version=version,commit_or_build='unrecovered producing checkout commit/binary digest',binary_or_source_sha256='unrecovered',exact_command_or_recorded_settings=cmd.read_text().strip(),command_status='source labels command a verbatim reconstruction; original invocation log not separately recovered',threads='20',seed='no explicit seed in reconstructed argv',chemistry_layout='10x3v3; RAD auto-wl; BLAZEexpect2462/ED2; Flexf8/e2')
 # The three retained m1 producers have direct software/argv receipts.
 pkg=base/'tilgner_native_three_tool_whitelist_20260810/provenance'
 for run in (1,2,3):
  sample=f'Hipp_SN_m1_ONT_Run{run}'
  for tool in ('RAD','BLAZE'):
   source=pkg/tool/(sample+'.'+tool+'.tsv');meta=metadata(source,'\t')
   record(sample,tool,[source],version=meta['rad_version'] if tool=='RAD' else meta['blaze_version'],commit_or_build=meta['rad_commit'] if tool=='RAD' else '2.5.0 pinned wheel; full source commit not in receipt',binary_or_source_sha256=meta['rad_sha256'] if tool=='RAD' else meta['blaze_wheel_sha256'],exact_command_or_recorded_settings=meta['command'],command_status='exact producing argv and binary/wheel identity',threads=meta['reserved_cpus'],seed='no explicit seed in producing argv',chemistry_layout=('three_prime layout SHA256 '+meta['layout_sha256']) if tool=='RAD' else '10x3v3 native default;expect10205')
  path=pkg/'Flexiplex_f0'/sample;meta=metadata(path/'run.tsv','\t')
  record(sample,'Flexiplex',[path/'run.tsv',path/'command.sh'],version=meta['version'],commit_or_build='exact executable hash; full commit not in run receipt',binary_or_source_sha256=meta['flexiplex_sha256'],exact_command_or_recorded_settings=(path/'command.sh').read_text().strip(),command_status='exact native f0 discovery and filtering command',threads=meta['threads'],seed='no explicit seed in producing command',chemistry_layout='10x3v3;catalog SHA256 '+meta['catalog_sha256'])
 return result
