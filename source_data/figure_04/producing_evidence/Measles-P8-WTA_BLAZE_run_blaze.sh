#!/usr/bin/env bash
set -euo pipefail
umask 007

root=external_data/reviewer_comment_data/scratch_preservation_20260921/files/measles_p8_whole_three_tool_20260801
input=external_data/raw_fastq_datasets/complex_outsourced_datasets/measles_wgs/mmr_p8_raw_data/SRR28349078.fastq.gz
blaze=external_data/reviewer_comment_data/scratch_preservation_20260921/files/blaze2_260a0_native_20260727/venv/bin/blaze
out="$root/runs/blaze"
status="$root/logs/blaze.status.log"
threads=24

test -s "$input"
test -x "$blaze"
mkdir -p "$out/mpl"
printf '%s\tBLAZE selection and demux start\n' "$(date -Is)" >> "$status"
PYTHONHASHSEED=0 MPLCONFIGDIR="$out/mpl" \
  /usr/bin/time -v -o "$out/time.txt" \
  "$blaze" \
    --expect-cells 10299 \
    --10x-kit-version 3v3 \
    --minQ 15 \
    --max-edit-distance 2 \
    --threads "$threads" \
    --output-prefix "$out/" \
    --output-fastq matched_reads.fastq.gz \
    --minimal_stdout \
    --overwrite \
    "$input" \
    > "$out/stdout.log" \
    2> "$out/stderr.log"
test -s "$out/whitelist.csv"
test -s "$out/matched_reads.fastq.gz"
printf '%s\tBLAZE selection and demux complete\n' "$(date -Is)" >> "$status"
touch "$out/DONE" "$root/BLAZE_DONE"
