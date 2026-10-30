#!/usr/bin/env bash
set -euo pipefail

run_root=/scratch-nfs/f005f43/longbench_snont_postdemux_vireo_20260803
source_fastq=/scratch-nfs/f005f43/longbench_full_demux_20260730/runs/blaze2_2.5.0_longbench_published/SN_ONT/matched_reads.fastq
source_whitelist=/scratch-nfs/f005f43/longbench_full_demux_20260730/runs/blaze2_2.5.0_longbench_published/SN_ONT/whitelist.csv
source_bam=/scratch-nfs/f005f43/longbench_full_demux_20260730/runs/flames2.0.1_longbench_published/SN_ONT/align2genome.bam
source_bai="${source_bam}.bai"
source_log=/scratch-nfs/f005f43/longbench_full_demux_20260730/runs/flames2.0.1_longbench_published/SN_ONT/genome_map.log
outdir="$run_root/align/BLAZE"
provenance="$run_root/provenance/BLAZE"

mkdir -p "$outdir" "$provenance"
for input in "$source_fastq" "$source_whitelist" "$source_bam" "$source_bai" "$source_log"; do
  [[ -r "$input" && -s "$input" ]] || { echo "Missing input: $input" >&2; exit 2; }
done

samtools quickcheck -v "$source_bam"
samtools view -H "$source_bam" > "$provenance/alignment_header.sam"

# Both the FLAMES log and BAM @PG must independently identify BLAZE's own
# post-demultiplexed FASTQ and the paper-pinned alignment flags.
grep -F $'fastq\t'"$source_fastq" "$source_log" >/dev/null
grep -F -- "-ax splice -y -t 32 -k14 --secondary=no --seed 2023" "$source_log" >/dev/null
grep -F "$source_fastq" "$provenance/alignment_header.sam" >/dev/null
grep -F -- "-ax splice -y -t 32 -k14 --secondary=no --seed 2023" "$provenance/alignment_header.sam" >/dev/null

set +o pipefail
samtools view "$source_bam" | awk '
  BEGIN { seen=0; cb=0; ub=0 }
  {
    seen++
    for (i=12; i<=NF; i++) {
      if ($i ~ /^CB:Z:/) cb++
      if ($i ~ /^UB:Z:/) ub++
    }
    if (seen >= 100000) exit
  }
  END {
    printf "records_checked\t%d\nrecords_with_CB\t%d\nrecords_with_UB\t%d\n", seen, cb, ub
    if (seen == 0 || cb != seen || ub != seen) exit 3
  }
' > "$provenance/first_100k_tag_validation.tsv"
tag_status=${PIPESTATUS[1]}
set -o pipefail
[[ "$tag_status" -eq 0 ]] || exit "$tag_status"

{
  printf 'validated_utc\t%s\n' "$(date -u +%FT%TZ)"
  printf 'derivation\tpost-demultiplexed BLAZE FASTQ, independently aligned\n'
  printf 'source_fastq\t%s\n' "$source_fastq"
  printf 'source_whitelist\t%s\n' "$source_whitelist"
  printf 'source_bam\t%s\n' "$source_bam"
  printf 'source_bai\t%s\n' "$source_bai"
  printf 'source_alignment_log\t%s\n' "$source_log"
  stat -c 'fastq_bytes\t%s' "$source_fastq"
  stat -c 'whitelist_bytes\t%s' "$source_whitelist"
  stat -c 'bam_bytes\t%s' "$source_bam"
  stat -c 'bai_bytes\t%s' "$source_bai"
  sha256sum "$source_whitelist" "$source_log"
} > "$provenance/input_manifest.tsv"

printf '%s\n' "$source_bam" > "$outdir/align2genome.bam.path"
printf '%s\n' "$source_bai" > "$outdir/align2genome.bam.bai.path"
touch "$outdir/ALIGNMENT.VALIDATED"
