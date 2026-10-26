#!/usr/bin/env bash
set -euo pipefail
umask 007

root=/scratch-nfs/f005f43/measles_p8_whole_three_tool_20260801
input=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/complex_outsourced_datasets/measles_wgs/mmr_p8_raw_data/SRR28349078.fastq.gz
design=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/cellranger_whitelists/3M-february-2018-3v3.txt
flex=/scratch/f005f43/measles_p7_p8_four_tool_20260730/tools/flexiplex-v1.02.6/flexiplex-linux
filter=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/bin/flexiplex-filter
conda_lib=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/lib
discovery="$root/runs/flexiplex/discovery"
demux="$root/runs/flexiplex/demux"
prefix="$discovery/p8_wt_SRR28349078"
status="$root/logs/flexiplex.status.log"
threads=24

test -s "$input"
test -s "$design"
test -x "$flex"
test -x "$filter"

printf '%s\tFlexiplex f8 discovery start\n' "$(date -Is)" >> "$status"
/usr/bin/time -v -o "$discovery/time.txt" \
  bash -o pipefail -c \
  'pigz -dc -p 4 "$1" | "$2" -d 10x3v3 -e 2 -f 8 -p "$3" -n "$4" > /dev/null' \
  bash "$input" "$flex" "$threads" "$prefix" \
  > "$discovery/stdout.log" \
  2> "$discovery/stderr.log"
test -s "${prefix}_barcodes_counts.txt"

LD_LIBRARY_PATH="$conda_lib" \
  /usr/bin/time -v -o "$discovery/filter.time.txt" \
  "$filter" \
    --whitelist "$design" \
    --outfile "$discovery/selected.tsv" \
    "${prefix}_barcodes_counts.txt" \
    > "$discovery/filter.stdout.log" \
    2> "$discovery/filter.stderr.log"
test -s "$discovery/selected.tsv"
touch "$discovery/DONE"
printf '%s\tFlexiplex discovery complete; demux start\n' "$(date -Is)" >> "$status"

/usr/bin/time -v -o "$demux/time.txt" \
  bash -o pipefail -c \
  'pigz -dc -p 4 "$1" | "$2" -d 10x3v3 -e 2 -f 8 -p "$3" -k "$4" -n "$5" | pigz -p 4 > "$6"' \
  bash \
  "$input" \
  "$flex" \
  "$threads" \
  "$discovery/selected.tsv" \
  "$demux/p8_wt_SRR28349078" \
  "$demux/matched_reads.fastq.gz" \
  > "$demux/stdout.log" \
  2> "$demux/stderr.log"
test -s "$demux/matched_reads.fastq.gz"
touch "$demux/DONE"
printf '%s\tFlexiplex demux complete\n' "$(date -Is)" >> "$status"
touch "$root/FLEXIPLEX_DONE"
