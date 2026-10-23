#!/usr/bin/env bash
set -euo pipefail

run_root=/scratch-nfs/f005f43/sctagger_nanopore2023_unadjusted_20260913
input=/scratch-nfs/f005f43/rad_longbench_20260726/data/shuffled_L_lr_synth.fq.gz
# Keep this exact historical path: its string is part of the deterministic
# background-tape seed, in addition to identifying the pinned model bytes.
model=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_nanopore2023_Q15_Q20_20260819/models/nanopore2023.gz
python=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/bin/python
generator=${run_root}/scripts/generate_truth_conditioned_qscores.py
output_dir=${run_root}/inputs/L_variants
log_dir=${run_root}/logs/generation

mkdir -p "${output_dir}" "${log_dir}" "${run_root}/provenance"
test -s "${input}"
test -s "${model}"

{
    printf 'start_utc\t%s\n' "$(date -u +%FT%TZ)"
    printf 'host\t%s\n' "$(hostname -f)"
    printf 'slurm_job_id\t%s\n' "${SLURM_JOB_ID:-none}"
    printf 'slurm_cpus_per_task\t%s\n' "${SLURM_CPUS_PER_TASK:-unset}"
    printf 'input\t%s\n' "${input}"
    printf 'model_seed_path\t%s\n' "${model}"
    printf 'command\t%s %s --input %s --output-dir %s --model %s --model-label nanopore2023 --native-unadjusted --seed 20260731 --adapter-max-ed 7 --boundary-slop 8 --tape-size 16777216 --pigz-threads 4 --progress-every 100000\n' "${python}" "${generator}" "${input}" "${output_dir}" "${model}"
    "${python}" - <<'PY'
import platform
import badread
import edlib
import numpy
print("python\t" + platform.python_version())
print("badread\t" + getattr(badread, "__version__", "0.4.1"))
print("edlib_module\t" + str(edlib.__file__))
print("numpy\t" + numpy.__version__)
PY
} > "${run_root}/provenance/generation_environment.tsv"

/usr/bin/time -v -o "${log_dir}/generation.time.txt" \
    "${python}" "${generator}" \
    --input "${input}" \
    --output-dir "${output_dir}" \
    --model "${model}" \
    --model-label nanopore2023 \
    --native-unadjusted \
    --seed 20260731 \
    --adapter-max-ed 7 \
    --boundary-slop 8 \
    --tape-size 16777216 \
    --pigz-threads 4 \
    --progress-every 100000 \
    > "${log_dir}/generation.stdout.log" \
    2> "${log_dir}/generation.stderr.log"

output=${output_dir}/shuffled_L_lr_synth.nanopore2023_truthbc.native_unadjusted.fq.gz
test -s "${output}"
pigz -t "${output}"
printf 'finish_utc\t%s\n' "$(date -u +%FT%TZ)" >> "${run_root}/provenance/generation_environment.tsv"
touch "${run_root}/GENERATION_DONE"
