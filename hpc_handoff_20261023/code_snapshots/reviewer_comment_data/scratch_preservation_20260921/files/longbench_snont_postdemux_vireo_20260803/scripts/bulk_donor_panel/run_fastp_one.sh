#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 CELL_LINE" >&2
  exit 2
fi

sample=$1
run_root=/scratch-nfs/f005f43/longbench_snont_postdemux_vireo_20260803
panel_root="$run_root/bulk_donor_panel"
raw="$panel_root/raw_fastq"
out="$panel_root/trimmed/$sample"
log="$panel_root/logs/fastp/$sample.log"
time_log="$panel_root/logs/fastp/$sample.time.txt"
fastp="$run_root/env_fastp_0.23.4/bin/fastp"
threads=${FASTP_THREADS:-16}

case "$sample" in
  H146) stem=H146_S1 ;;
  H69) stem=H69_S2 ;;
  H526) stem=H526_S3 ;;
  H211) stem=H211_S4 ;;
  SHP77) stem=SHP77_S5 ;;
  H1975) stem=H1975_S6 ;;
  H2228) stem=H2228_S7 ;;
  HCC827) stem=HCC827_S8 ;;
  *) echo "unsupported cell line: $sample" >&2; exit 2 ;;
esac

r1="$raw/${stem}_R1_001.fastq.gz"
r2="$raw/${stem}_R2_001.fastq.gz"
o1="$out/${sample}_R1.fastq.gz"
o2="$out/${sample}_R2.fastq.gz"
done_file="$out/FASTP.DONE.tsv"
mkdir -p "$out" "$(dirname "$log")"

if [[ -s "$done_file" ]]; then
  gzip -t "$o1" "$o2"
  exit 0
fi
if [[ -e "$o1" || -e "$o2" ]]; then
  echo "partial fastp outputs exist without completion marker for $sample" >&2
  exit 3
fi
for input in "$r1" "$r2" "$fastp"; do
  [[ -r "$input" && -s "$input" ]] || { echo "missing input: $input" >&2; exit 4; }
done

/usr/bin/time -v -o "$time_log" \
  "$fastp" \
    -i "$r1" -I "$r2" \
    -o "$o1" -O "$o2" \
    --thread "$threads" \
    -j "$out/${sample}.json" \
    -h "$out/${sample}.html" \
    > "$log" 2>&1

gzip -t "$o1" "$o2"
{
  printf 'completed_utc\t%s\n' "$(date -u +%FT%TZ)"
  printf 'cell_line\t%s\n' "$sample"
  printf 'threads\t%s\n' "$threads"
  stat -c 'trimmed_r1_bytes\t%s' "$o1"
  stat -c 'trimmed_r2_bytes\t%s' "$o2"
} > "$done_file"

