#!/usr/bin/env bash
set -euo pipefail

root=/scratch/f005f43/visium_lebrigand_combined_full_auto_wl_20260731
input_dir=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/visium_lebrigand_GSE153859_MOB
input_one="${input_dir}/SRR12157794_1.fastq.gz"
input_two="${input_dir}/SRR12157795_1.fastq.gz"
combined="${root}/MOB_SRR12157794_SRR12157795.fastq.gz"
design=/scratch/f005f43/visium_lebrigand_mob_redirect_audit_20260730/inputs/visium_v2_full_4992.txt
truth=/scratch/f005f43/visium_lebrigand_mob_redirect_audit_20260730/inputs/MOB_in_tissue_918.txt
positions="${input_dir}/mob164315-spatial-illumina/spatial/tissue_positions_list.csv"
rad=/scratch-nfs/f005f43/longbench_full_demux_20260730/tools/rad_920adda_edlibfix/build_release/rad
blaze=/scratch/f005f43/blaze2_260a0_native_20260727/venv/bin/blaze
flex_root=/tmp/flexiplex_release.GqgaKA/flexiplex
flex="${flex_root}/bin/flexiplex-linux"
analysis_script=/scratch/f005f43/visium_lebrigand_full_auto_wl_20260731/analyze_callsets.py
figure_script=/scratch/f005f43/visium_lebrigand_full_auto_wl_20260731/render_figures.py
threads=${LEBRIGAND_THREADS:-12}

mkdir -p "${root}/logs" "${root}/rad" "${root}/blaze_expect918" \
    "${root}/flex_f0" "${root}/flex_f8"
exec >>"${root}/logs/controller.log" 2>&1

echo "$(date -u +%FT%TZ) validating source FASTQs"
[[ "$(md5sum "${input_one}" | awk '{print $1}')" == ac05146de32ac04bc42e5b6ef36d1a5a ]]
[[ "$(md5sum "${input_two}" | awk '{print $1}')" == d1cd65d8f5a55fb1b189c0019204f872 ]]
pigz -t -p "${threads}" "${input_one}"
pigz -t -p "${threads}" "${input_two}"

if [[ ! -e "${root}/COMBINED_FASTQ_DONE" ]]; then
    temporary="${combined}.building.$$"
    cp --sparse=never "${input_one}" "${temporary}"
    dd if="${input_two}" of="${temporary}" bs=16M oflag=append conv=notrunc status=progress
    mv "${temporary}" "${combined}"
    pigz -t -p "${threads}" "${combined}"
    [[ "$(stat --printf='%s' "${combined}")" -eq 34253341514 ]]
    touch "${root}/COMBINED_FASTQ_DONE"
fi

run_rad() {
    if [[ -e "${root}/rad/DONE" ]]; then return; fi
    /usr/bin/time -v -o "${root}/rad/time.txt" \
        "${rad}" scan-wl \
        -i "${combined}" -o "${root}/rad/MOB_RAD" \
        -p CTACACGACGCTCTTCCGATCT -n 16 -e 0.3 \
        -w "${design}" -t "${threads}" -k 10000 -v \
        >"${root}/rad/stdout.log" 2>"${root}/rad/stderr.log"
    test -s "${root}/rad/MOB_RAD.txt"
    touch "${root}/rad/DONE"
}

run_blaze() {
    if [[ -e "${root}/blaze_expect918/DONE" ]]; then return; fi
    /usr/bin/time -v -o "${root}/blaze_expect918/time.txt" \
        "${blaze}" --expect-cells 918 --full-bc-whitelist "${design}" \
        --umi-len 12 --threads "${threads}" --batch-size 1000 \
        --no-emtpy-drops --no-demultiplexing \
        --output-prefix "${root}/blaze_expect918/" "${combined}" \
        >"${root}/blaze_expect918/stdout.log" \
        2>"${root}/blaze_expect918/stderr.log"
    test -s "${root}/blaze_expect918/whitelist.csv"
    touch "${root}/blaze_expect918/DONE"
}

run_flex() {
    local flank=$1
    local label="f${flank}"
    local out="${root}/flex_${label}"
    local prefix="MOB_${label}"
    if [[ -e "${out}/DONE" ]]; then return; fi
    (
        cd "${out}"
        export LD_LIBRARY_PATH=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/lib
        /usr/bin/time -v -o time.txt bash -c '
            set -o pipefail
            pigz -dc -p "$1" "$2" |
                "$3" -d 10x3v3 -f "$4" -e 2 -p "$1" -n "$5" > /dev/null
        ' _ "${threads}" "${combined}" "${flex}" "${flank}" "${prefix}" \
            >stdout.log 2>stderr.log
        test -s "${prefix}_barcodes_counts.txt"
        test -s "${prefix}_barcodes_final.txt"
        touch DONE
    )
}

echo "$(date -u +%FT%TZ) starting four complete-data selectors"
run_rad & pid_rad=$!
run_blaze & pid_blaze=$!
run_flex 0 & pid_f0=$!
run_flex 8 & pid_f8=$!

status=0
for item in "rad:${pid_rad}" "blaze:${pid_blaze}" "flex_f0:${pid_f0}" "flex_f8:${pid_f8}"; do
    label=${item%%:*}
    pid=${item##*:}
    if wait "${pid}"; then
        echo "$(date -u +%FT%TZ) PASS ${label}"
    else
        return_code=$?
        echo "$(date -u +%FT%TZ) FAIL ${label} status=${return_code}"
        status=1
    fi
done
[[ "${status}" -eq 0 ]]

if [[ -e "${root}/analysis_stage.tmp" ]]; then
    mv "${root}/analysis_stage.tmp" \
        "${root}/analysis_stage.tmp.stale.$(date -u +%Y%m%dT%H%M%SZ)"
fi
if [[ -e "${root}/analysis_stage" ]]; then
    echo "Refusing to overwrite existing analysis_stage" >&2
    exit 4
fi
python3 "${analysis_script}" --run-root "${root}" --truth "${truth}" \
    --design "${design}" --output "${root}/analysis_stage.tmp" \
    --expect-cells 918 \
    --input-label "complete SRR12157794 plus SRR12157795 concatenated input"
python3 "${figure_script}" --analysis "${root}/analysis_stage.tmp" \
    --positions "${positions}"
python3 "${root}/scripts/generate_report.py" \
    --analysis "${root}/analysis_stage.tmp"

mkdir -p "${root}/analysis_stage.tmp/scripts" \
    "${root}/analysis_stage.tmp/source_outputs" \
    "${root}/analysis_stage.tmp/provenance/logs"
cp "${analysis_script}" "${root}/analysis_stage.tmp/scripts/analyze_callsets.py"
cp "${figure_script}" "${root}/analysis_stage.tmp/scripts/render_figures.py"
cp "${root}/scripts/generate_report.py" \
    "${root}/analysis_stage.tmp/scripts/generate_report.py"
cp "${root}/scripts/run_combined_benchmark.sh" \
    "${root}/analysis_stage.tmp/scripts/run_combined_benchmark.sh"
cp "${root}/rad/MOB_RAD.csv" \
    "${root}/analysis_stage.tmp/source_outputs/RAD_barcode_counts.csv"
cp "${root}/blaze_expect918/hq_design_counts.tsv" \
    "${root}/analysis_stage.tmp/source_outputs/BLAZE_hq_design_counts.tsv"
cp "${root}/flex_f0/MOB_f0_barcodes_counts.txt" \
    "${root}/analysis_stage.tmp/source_outputs/Flexiplex_f0_barcode_counts.txt"
cp "${root}/flex_f8/MOB_f8_barcodes_counts.txt" \
    "${root}/analysis_stage.tmp/source_outputs/Flexiplex_f8_barcode_counts.txt"
cp "${root}/rad/stdout.log" \
    "${root}/analysis_stage.tmp/provenance/logs/RAD.stdout.log"
cp "${root}/rad/stderr.log" \
    "${root}/analysis_stage.tmp/provenance/logs/RAD.stderr.log"
cp "${root}/blaze_expect918/stdout.log" \
    "${root}/analysis_stage.tmp/provenance/logs/BLAZE.stdout.log"
cp "${root}/blaze_expect918/stderr.log" \
    "${root}/analysis_stage.tmp/provenance/logs/BLAZE.stderr.log"
cp "${root}/flex_f0/stdout.log" \
    "${root}/analysis_stage.tmp/provenance/logs/Flexiplex_f0.stdout.log"
cp "${root}/flex_f0/stderr.log" \
    "${root}/analysis_stage.tmp/provenance/logs/Flexiplex_f0.stderr.log"
cp "${root}/flex_f8/stdout.log" \
    "${root}/analysis_stage.tmp/provenance/logs/Flexiplex_f8.stdout.log"
cp "${root}/flex_f8/stderr.log" \
    "${root}/analysis_stage.tmp/provenance/logs/Flexiplex_f8.stderr.log"
(
    cd "${root}/analysis_stage.tmp"
    find . -type f ! -name SHA256SUMS.txt -print0 |
        sort -z | xargs -0 sha256sum > SHA256SUMS.txt
)
mv "${root}/analysis_stage.tmp" "${root}/analysis_stage"

destination=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/wl_scan/20260731_lebrigand_MOB_complete_two_accession_benchmark
if [[ -e "${destination}" ]]; then
    echo "Refusing to overwrite existing durable export: ${destination}" >&2
    exit 5
fi
staging="${destination}.staging.$$"
mkdir -p "$(dirname "${destination}")" "${staging}"
rsync -a --no-group "${root}/analysis_stage/" "${staging}/"
mv "${staging}" "${destination}"
touch "${root}/EXPORT_DONE"
touch "${root}/DONE"
echo "$(date -u +%FT%TZ) combined benchmark complete"
