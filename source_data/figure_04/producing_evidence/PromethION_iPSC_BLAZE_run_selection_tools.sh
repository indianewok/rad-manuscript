#!/usr/bin/env bash
set -euo pipefail

root=/scratch/f005f43/promethion_four_tool_20260729
input="$root/input/promethion.fq.gz"
stage_status="$root/logs/input_stage.status.log"
rad=/tmp/rad-current-f005f43.8ChwC9/build-system/rad
blaze=/scratch/f005f43/blaze2_260a0_native_20260727/venv/bin/blaze
flex=/tmp/flexiplex_release.GqgaKA/flexiplex/bin/flexiplex-linux
flex_filter=/tmp/flexiplex_release.GqgaKA/flexiplex/scripts/flexiplex_filter/main.py
python=/scratch/f005f43/rad_scmix2_20260726/tools/flexiplex-v1.02.6/.venv/bin/python
full_3v3=/scratch/f005f43/blaze_analysis_data_20335203/data/3M-february-2018.txt
status="$root/logs/selection_queue.status.log"

"$python" -c 'import pandas, numpy'

while true; do
    if [[ -s "$input" ]] && [[ -s "$stage_status" ]] &&
       grep -q $'\tcomplete\t' "$stage_status"; then
        break
    fi
    printf '%s\twaiting-for-staged-input\n' "$(date -Is)" >> "$status"
    sleep 30
done

mkdir -p \
    "$root/results/rad_scan_e01" \
    "$root/results/rad_scan_e03" \
    "$root/results/blaze_expect500" \
    "$root/results/flexiplex_f0" \
    "$root/results/flexiplex_f8"

printf '%s\tstart\trad-scan-e01\n' "$(date -Is)" >> "$status"
/usr/bin/time -v -o "$root/results/rad_scan_e01/time.txt" \
    "$rad" scan-wl \
    -i "$input" \
    -p CTACACGACGCTCTTCCGATCT \
    -n 16 \
    -w 10x_3v3 \
    -o "$root/results/rad_scan_e01/promethion" \
    -e 0.1 \
    -t 32 \
    -k 10000 \
    > "$root/results/rad_scan_e01/stdout.log" \
    2> "$root/results/rad_scan_e01/stderr.log"
printf '%s\tcomplete\trad-scan-e01\n' "$(date -Is)" >> "$status"

printf '%s\tstart\trad-scan-e03\n' "$(date -Is)" >> "$status"
/usr/bin/time -v -o "$root/results/rad_scan_e03/time.txt" \
    "$rad" scan-wl \
    -i "$input" \
    -p CTACACGACGCTCTTCCGATCT \
    -n 16 \
    -w 10x_3v3 \
    -o "$root/results/rad_scan_e03/promethion" \
    -e 0.3 \
    -t 32 \
    -k 10000 \
    > "$root/results/rad_scan_e03/stdout.log" \
    2> "$root/results/rad_scan_e03/stderr.log"
test -s "$root/results/rad_scan_e03/promethion.txt"
test -s "$root/results/rad_scan_e03/promethion.csv"
printf '%s\tcomplete\trad-scan-e03\n' "$(date -Is)" >> "$status"

printf '%s\tstart\tblaze-expect500-selection\n' "$(date -Is)" >> "$status"
/usr/bin/time -v -o "$root/results/blaze_expect500/time.txt" \
    "$blaze" \
    --expect-cells 500 \
    --10x-kit-version 3v3 \
    --threads 32 \
    --batch-size 1000 \
    --no-demultiplexing \
    --no-emtpy-drops \
    --overwrite \
    --output-prefix "$root/results/blaze_expect500/" \
    "$input" \
    > "$root/results/blaze_expect500/stdout.log" \
    2> "$root/results/blaze_expect500/stderr.log"
test -s "$root/results/blaze_expect500/putative_bc.csv"
test -s "$root/results/blaze_expect500/whitelist.csv"
printf '%s\tcomplete\tblaze-expect500-selection\n' "$(date -Is)" >> "$status"

printf '%s\tstart\tflexiplex-f0-discovery\n' "$(date -Is)" >> "$status"
(
    cd "$root/results/flexiplex_f0"
    /usr/bin/time -v -o discovery.time.txt \
        bash -o pipefail -c \
        'pigz -p 32 -dc "$1" | "$2" -d 10x3v3 -f 0 -p 32 -n flexiplex' \
        bash "$input" "$flex" \
        > discovery.stdout.log \
        2> discovery.stderr.log
    /usr/bin/time -v -o filter.time.txt \
        "$python" "$flex_filter" \
        -v \
        -w "$full_3v3" \
        -o flexiplex_barcodes_final.txt \
        flexiplex_barcodes_counts.txt \
        > filter.stdout.log \
        2> filter.stderr.log
    test -s flexiplex_barcodes_counts.txt
    test -s flexiplex_barcodes_final.txt
)
printf '%s\tcomplete\tflexiplex-f0-discovery\n' "$(date -Is)" >> "$status"

printf '%s\tstart\tflexiplex-f8-discovery\n' "$(date -Is)" >> "$status"
(
    cd "$root/results/flexiplex_f8"
    /usr/bin/time -v -o discovery.time.txt \
        bash -o pipefail -c \
        'pigz -p 32 -dc "$1" | "$2" -d 10x3v3 -f 8 -p 32 -n flexiplex' \
        bash "$input" "$flex" \
        > discovery.stdout.log \
        2> discovery.stderr.log
    /usr/bin/time -v -o filter.time.txt \
        "$python" "$flex_filter" \
        -v \
        -w "$full_3v3" \
        -o flexiplex_barcodes_final.txt \
        flexiplex_barcodes_counts.txt \
        > filter.stdout.log \
        2> filter.stderr.log
    test -s flexiplex_barcodes_counts.txt
    test -s flexiplex_barcodes_final.txt
)
printf '%s\tcomplete\tflexiplex-f8-discovery\n' "$(date -Is)" >> "$status"

printf '%s\tcomplete\tall-selection-tools\n' "$(date -Is)" >> "$status"
