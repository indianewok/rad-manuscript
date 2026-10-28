#!/usr/bin/env bash
set -euo pipefail
umask 007

root=external_data/reviewer_comment_data/scratch_preservation_20260921/files/measles_p8_whole_three_tool_20260801
input=external_data/raw_fastq_datasets/complex_outsourced_datasets/measles_wgs/mmr_p8_raw_data/SRR28349078.fastq.gz
design=external_data/cellranger_whitelists/3M-february-2018-3v3.txt
layout="$root/resources/10x_3v3_1_12nt_umi_layout.csv"
rad="$root/tools/rad_b02ff24_build/rad"
rad_resources="$root/tools/rad_b02ff24_src"
scan="$root/runs/rad/scanwl"
demux="$root/runs/rad/demux"
status="$root/logs/rad.status.log"
threads=24

test -s "$input"
test -s "$design"
test -s "$layout"
test -x "$rad"

printf '%s\tRAD scan-wl start\n' "$(date -Is)" >> "$status"
RAD_RESOURCES="$rad_resources" \
  /usr/bin/time -v -o "$scan/time.txt" \
  "$rad" scan-wl \
    -i "$input" \
    -p CTACACGACGCTCTTCCGATCT \
    -n 16 \
    -e 0.3 \
    -w "$design" \
    -o "$scan/scanwl" \
    -t "$threads" \
    -k 5000 \
    -v \
    > "$scan/stdout.log" \
    2> "$scan/stderr.log"
test -s "$scan/scanwl.txt"
touch "$scan/DONE"
printf '%s\tRAD scan-wl complete; RAD demux start\n' "$(date -Is)" >> "$status"

RAD_RESOURCES="$rad_resources" \
  /usr/bin/time -v -o "$demux/time.txt" \
  "$rad" demux \
    -l "$layout" \
    -q "$input" \
    -g "$design" \
    -c "$scan/scanwl.txt" \
    -R offensive \
    -M 2 \
    -m 2 \
    -z 5000 \
    -o p8_wt_SRR28349078 \
    -d "$demux" \
    -F "$demux/run.log" \
    -t "$threads" \
    -v \
    > "$demux/stdout.log" \
    2> "$demux/stderr.log"
test -s "$demux/p8_wt_SRR28349078.fq.gz"
touch "$demux/DONE"
printf '%s\tRAD demux complete\n' "$(date -Is)" >> "$status"
touch "$root/RAD_DONE"
