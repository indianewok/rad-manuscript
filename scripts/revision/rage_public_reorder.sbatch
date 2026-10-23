#!/usr/bin/env bash
#SBATCH --job-name=rad_rage_public_order
#SBATCH --account=lsonglab
#SBATCH --qos=lsonglab_gpu
#SBATCH --partition=standard
#SBATCH --cpus-per-task=6
#SBATCH --mem=24G
#SBATCH --time=01:00:00
#SBATCH --gres=gpu:0
#SBATCH --output=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/rad-manuscript/validation/rage_public_reorder_job_%j.log
set -euo pipefail
# Allocation basis: the real 100k-prefix verify-only benchmark took 3.472 s
# with one sort/pigz worker; scaling by bases gives about 13 min before large
# input/shared-I/O overhead. One hour provides approximately 4x headroom.
cd /dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/rad-manuscript
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python3 - <<'PY'
import json,os,re,subprocess
from pathlib import Path
identity=json.loads(Path('checkpoints/figure_03/rage_matched/counts/input_id_validation.json').read_text())
assert identity['canonical_record_sha256']=='a5f866d6180b46e0acbd3aa2526364060c152380714b00ec0ed74b8c1e8c24af'
assert identity['input_ids_sha256']=='e4831a95828b65f21253c9f1058f1af9ef2fa7abe286321d88aaffba12ab2952'
assert identity['records']==20346396 and identity['sequence_bases']==16466857803
acquisition=json.loads(Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/rage_public_replication_20261023/ramos_nanopore.fastq.acquisition.json').read_text())
assert acquisition['status']=='passed' and acquisition['md5']=='93bdd7b64877d96f38720aea13c92bdc'
assert acquisition['bytes']==16675472857
node=os.environ['SLURMD_NODENAME']
hardware=subprocess.check_output(['scontrol','show','node',node,'-o']).decode()
gres=re.search(r'\bGres=(\S+)',hardware).group(1)
assert 'gpu' not in gres.lower(), 'CPU-only work cannot run on a GPU-equipped node'
partition=os.environ['SLURM_JOB_PARTITION']
assert partition=='standard' or (partition=='preempt_lsong' and node=='t02'), 'Only verified CPU-only standard or explicitly pinned CPU-only t02 is permitted'
Path('validation/rage_public_reorder_placement.json').write_text(json.dumps(dict(status='passed',job_id=os.environ['SLURM_JOB_ID'],node=node,gres=gres,partition=os.environ['SLURM_JOB_PARTITION'],cpus_per_task=os.environ['SLURM_CPUS_PER_TASK'],requested_memory='24G',requested_time='01:00:00',requested_gpu_gres=0,allocation_basis='100000 actual-prefix records verified in3.472 seconds; approximately13minutes scaled by bases, plus large-input/shared-I/O overhead; one-hour request gives approximately4x headroom',scontrol_node=hardware),indent=2)+'\n')
PY
exec /usr/bin/python3 scripts/figure_03/reorder_public_fastq.py \
  --public /dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/rage_public_replication_20261023/ramos_nanopore.fastq.gz \
  --acquisition-report /dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/rage_public_replication_20261023/ramos_nanopore.fastq.acquisition.json \
  --order checkpoints/figure_03/rage_matched/counts/input_original_ids.txt.gz \
  --identity checkpoints/figure_03/rage_matched/counts/input_id_validation.json \
  --verify-only \
  --report validation/rage_public_payload_comparison.json \
  --scratch "/scratch/f005f43/rage_public_reorder_${SLURM_JOB_ID}" \
  --sort-threads 3 --sort-memory 6G --pigz-threads 2
