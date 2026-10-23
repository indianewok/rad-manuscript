#!/usr/bin/env python3
"""Run one tool on one matched RAGE target list; every argv is saved before execution."""
import argparse,json,os,subprocess,time
from pathlib import Path
from figure_3 import ROOT,sha,js
from figure_3_rage_verify_tools import verify_frozen_files

def pipeline_exit_status(codes):
    """A negative signal status must fail even when another process exits0."""
    return next((code for code in codes if code!=0),0)

def main():
    p=argparse.ArgumentParser();p.add_argument('tool',choices=['RAD','BLAZE','Flexiplex']);p.add_argument('replicate',type=int,choices=[1,2,3]);p.add_argument('--pilot',action='store_true');a=p.parse_args()
    base=ROOT/'checkpoints/figure_03/rage_matched';m=json.loads((base/'experiment.json').read_text())
    if 'software_verification' not in m:raise ValueError('Prepare and verify the supplied software paths before execution')
    verify_frozen_files(m['software_verification'])
    report=json.loads((base/'input_validation.json').read_text())
    if report['status']!='passed':raise ValueError('Full input has not passed preflight')
    original=Path(m['input'])
    if report['source']!=str(original) or original.stat().st_size!=report['bytes'] or original.stat().st_mtime_ns!=report.get('mtime_ns'):raise ValueError('Input path or file metadata changed; rerun preflight')
    raw=base/'inputs/pilot_10000.fastq.gz' if a.pilot else Path(m['input'])
    targets=base/'inputs'/f'false_rep{a.replicate}.txt'
    if sha(targets)!=m['whitelists'][a.replicate-1]['sha256']:raise ValueError('Supplied target list changed after preparation')
    out=base/('pilot' if a.pilot else 'runs')/a.tool.lower()/f'rep{a.replicate}';out.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env.pop('FLEXIPLEX_AUDIT_SOURCE_FILE',None);env.update(PYTHONHASHSEED='20261023',OMP_NUM_THREADS='16',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',RAD_PIGZ_THREADS='2',MPLCONFIGDIR=str(base/'matplotlib_cache'))
    prefix=f'rage_rep{a.replicate}_{a.tool.lower()}'
    if a.tool=='RAD':
        command=[m['rad_binary'],'demux','-l',m['layout'],'-q',str(raw),'-g',m['bitlist'],'-c',str(targets),'-R','offensive','-M','2','-m','2','-z','5000','-o',prefix,'-d',str(out),'-F',str(out/(prefix+'.log')),'-t','16','-v']
        expected=[out/(prefix+'.fq.gz')]
    elif a.tool=='BLAZE':
        command=[m['blaze_python'],m['blaze_entrypoint'],'--no-whitelisting','--known-bc-list',str(targets),'--10x-kit-version','3v2','--minQ','15','--max-edit-distance','2','--no-emtpy-drops','--threads','16','--output-prefix',str(out)+'/', '--output-fastq','matched_reads.fastq.gz','--overwrite',str(raw)]
        expected=[out/'matched_reads.fastq.gz',out/'putative_bc.csv']
    else:
        command=[m['flex_binary'],'-d','10x3v2','-k',str(targets),'-f','8','-e','2','-p','16','-n',str(out/prefix)]
        expected=[out/(prefix+'.fastq.gz'),out/(prefix+'_reads_barcodes.txt')]
    run=dict(experiment_id=m['experiment_id'],tool=a.tool,replicate=a.replicate,scope='10000-read pilot' if a.pilot else 'full input',argv=command,cwd=str(out),input=str(raw),input_sha256=report['pilot_sha256'] if a.pilot else report['compressed_sha256'],input_reads=10000 if a.pilot else report['physical_reads'],target_sha256=sha(targets),catalog_sha256=m['catalog_sha256'],reference_sha256=m['reference_sha256'],layout_sha256=m['layout_sha256'],code_sha256=sha(__file__),executable_sha256=sha(command[0]),binary_versions={k:m[k] for k in ['rad_commit','blaze_version','blaze_commit','flex_commit','flex_patch_sha256']},threads=16,compression_threads=2,PYTHONHASHSEED=env['PYTHONHASHSEED'],FLEXIPLEX_AUDIT_SOURCE_FILE='UNSET',scheduler_job=os.environ.get('SLURM_JOB_ID',''),scheduler_array_task=os.environ.get('SLURM_ARRAY_TASK_ID',''),start_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),status='running')
    if a.tool=='Flexiplex':run['pipeline']=[['pigz','-dc','-p','2',str(raw)],command,['pigz','-p','2']]
    js(out/'run_manifest.json',run);(out/'supplied_whitelist_used.txt').write_bytes(targets.read_bytes())
    print(json.dumps(run),flush=True)
    try:
        with (out/'stdout.log').open('w') as stdout,(out/'stderr.log').open('w') as stderr:
            if a.tool!='Flexiplex':
                code=subprocess.run(['/usr/bin/time','-v','-o',str(out/'time.txt')]+command,cwd=out,env=env,stdout=stdout,stderr=stderr).returncode
            else:
                with expected[0].open('wb') as compressed:
                    decompressor=subprocess.Popen(run['pipeline'][0],stdout=subprocess.PIPE,stderr=stderr,env=env)
                    producer=subprocess.Popen(['/usr/bin/time','-v','-o',str(out/'time.txt')]+command,stdin=decompressor.stdout,stdout=subprocess.PIPE,stderr=stderr,cwd=out,env=env)
                    decompressor.stdout.close()
                    compressor=subprocess.Popen(run['pipeline'][2],stdin=producer.stdout,stdout=compressed,stderr=stderr,env=env)
                    producer.stdout.close();codes=[compressor.wait(),producer.wait(),decompressor.wait()];code=pipeline_exit_status(codes)
                    run['pipeline_exit_statuses_compressor_producer_decompressor']=codes
        if code:raise RuntimeError(f'Producer failed with exit status {code}')
        if any(not x.is_file() or x.stat().st_size==0 for x in expected):raise ValueError('Producer exit0 but expected output absent')
        run.update(status='passed',exit_status=0,outputs=[dict(path=str(x),sha256=sha(x),bytes=x.stat().st_size) for x in expected])
    except Exception as e:
        run.update(status='failed',error=str(e));raise
    finally:
        run['end_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());js(out/'run_manifest.json',run)
    print(json.dumps({'status':'passed','tool':a.tool,'replicate':a.replicate,'out':str(out)}),flush=True)
if __name__=='__main__':main()
