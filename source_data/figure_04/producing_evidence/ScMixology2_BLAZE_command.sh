#!/usr/bin/env bash
set -euo pipefail

root=external_data/reviewer_comment_data/scratch_preservation_20260921/files/blaze_single_cell_expect_sweep_20260810/scmixology2_exploratory
python=external_data/reviewer_comment_data/scratch_preservation_20260921/files/blaze2_250_probe_20260727/venv/bin/python
script="${root}/scripts/reconstruct_expect_sweep.py"
raw=external_data/reviewer_comment_data/scratch_preservation_20260921/files/blaze_analysis_data_20335203/data/scmixology/blaze/raw_bc.csv.gz
reference=external_data/reviewer_comment_data/scratch_preservation_20260921/files/blaze_analysis_data_20335203/data/scmixology/cellranger/whitelist.tsv
design=external_data/reviewer_comment_data/scratch_preservation_20260921/files/blaze_analysis_data_20335203/data/3M-february-2018.txt.gz

mkdir -p "${root}/logs" "${root}/tables" "${root}/callsets" "${root}/evidence"
exec 9>"${root}/run.lock"
flock -n 9 || exit 3
[[ ! -e "${root}/DONE" ]] || exit 0

args=(
    --raw-bc "${raw}"
    --cellranger-reference "${reference}"
    --preserved-design-whitelist "${design}"
    --output-root "${root}"
    --expected-data-rows 25164948
    --expected-reference-count 248
    --min-q 15
    --chunksize 1000000
)

{
    echo "started_utc=$(date -u +%FT%TZ)"
    echo "status=EXPLORATORY_RECONSTRUCTION_NO_AUTHENTIC_NATIVE_CALLSET"
    echo "fastq_extraction_or_demultiplexing=not_run"
    echo "native_selected_callset_available=false"
    echo "expectation_grid=250,500,1000"
    printf 'command='
    printf '%q ' "${python}" "${script}" "${args[@]}"
    printf '\n'
} > "${root}/run_metadata.txt"

export MPLCONFIGDIR="${root}/mpl"
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
mkdir -p "${MPLCONFIGDIR}"

set +e
/usr/bin/time -v -o "${root}/time.verbose.txt" \
    "${python}" "${script}" "${args[@]}" \
    > "${root}/logs/stdout.log" \
    2> "${root}/logs/stderr.log"
status=$?
set -e
printf '%s\n' "${status}" > "${root}/exit_status.txt"
[[ "${status}" -eq 0 ]] || exit "${status}"

test -s "${root}/tables/expect_sensitivity_metrics.tsv"
test -s "${root}/tables/baseline_status.tsv"
grep -Fq 'EXPLORATORY_RECONSTRUCTION_NO_AUTHENTIC_NATIVE_CALLSET' \
    "${root}/tables/baseline_status.tsv"

{
    sha256sum "${raw}"
    sha256sum "${reference}"
    sha256sum "${design}"
    sha256sum "${script}"
    sha256sum "$0"
} > "${root}/source_artifact_sha256.txt"

{
    echo "finished_utc=$(date -u +%FT%TZ)"
    echo "primary_validated_package_eligible=false"
} >> "${root}/run_metadata.txt"
touch "${root}/DONE"
