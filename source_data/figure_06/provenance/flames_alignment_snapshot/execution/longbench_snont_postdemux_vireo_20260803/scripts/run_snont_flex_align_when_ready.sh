#!/usr/bin/env bash
set -euo pipefail

run_root=/scratch-nfs/f005f43/longbench_snont_postdemux_vireo_20260803
prepdir="$run_root/demux/Flexiplex"
source_fastq="$prepdir/SN_ONT_flexiplex_v1026_alignment.raw.fastq.gz"
source_sidecar="$prepdir/SN_ONT_flexiplex_v1026_alignment_reads_barcodes.txt.gz"
demux_metadata="$prepdir/run_metadata.txt"
source_whitelist=/scratch-nfs/f005f43/longbench_snont_postdemux_vireo_20260803/inputs/SN_flexiplex_whitelist.txt
flames_runner=/scratch-nfs/f005f43/longbench_full_demux_20260730/scripts/run_longbench_flames_stage.sh
flames_config=/scratch-nfs/f005f43/longbench_full_demux_20260730/provenance/LongBench_workflow_37a9506/lr_sc_sn/config/flames_genome_map.json
outdir="$run_root/align/Flexiplex"
logdir="$run_root/logs"
provenance="$run_root/provenance/Flexiplex"

mkdir -p "$outdir" "$logdir" "$provenance"

if [[ -e "$outdir/align2genome.bam" || -e "$outdir/ALIGNMENT.DONE" ]]; then
  echo "Refusing to overwrite an existing Flexiplex alignment in $outdir" >&2
  exit 2
fi

for input in \
  "$source_fastq" "$source_sidecar" "$demux_metadata" \
  "$source_whitelist" "$flames_runner" "$flames_config"; do
  [[ -r "$input" && -s "$input" ]] || { echo "Missing input: $input" >&2; exit 4; }
done
grep -qx 'demux_exit_status=0' "$demux_metadata" || {
  echo "Flexiplex metadata does not record a successful demultiplexing run" >&2
  exit 4
}
pigz -t -p 16 "$source_fastq"
pigz -t -p 16 "$source_sidecar"

{
  printf 'started_utc\t%s\n' "$(date -u +%FT%TZ)"
  printf 'hostname\t%s\n' "$(hostname -f)"
  printf 'source_fastq\t%s\n' "$source_fastq"
  printf 'source_fastq_mode\tdirect Flexiplex output with native CB/UB tags\n'
  printf 'source_sidecar\t%s\n' "$source_sidecar"
  printf 'sidecar_use\tprovenance only; not a lockstep FASTQ index\n'
  printf 'source_whitelist\t%s\n' "$source_whitelist"
  printf 'flames_runner\t%s\n' "$flames_runner"
  printf 'flames_config\t%s\n' "$flames_config"
  stat -c 'input_fastq_bytes\t%s' "$source_fastq"
  stat -c 'input_whitelist_bytes\t%s' "$source_whitelist"
  sha256sum "$demux_metadata" "$source_whitelist" "$flames_runner" "$flames_config"
} > "$provenance/input_manifest.tsv"

/usr/bin/time -v -o "$logdir/Flexiplex_alignment.time.txt" \
  "$flames_runner" "$source_fastq" "$outdir" "$flames_config" \
  > "$logdir/Flexiplex_alignment.log" 2>&1

samtools quickcheck -v "$outdir/align2genome.bam"
samtools index -@ 8 "$outdir/align2genome.bam"
samtools view -H "$outdir/align2genome.bam" > "$provenance/alignment_header.sam"
set +o pipefail
samtools view "$outdir/align2genome.bam" | awk -v whitelist="$source_whitelist" '
  BEGIN {
    while ((getline barcode < whitelist) > 0) allowed[barcode]=1
    close(whitelist)
    seen=0; cb=0; ub=0; bad_cb_count=0; bad_ub_count=0
    invalid_cb=0; invalid_ub=0; outside_whitelist=0
  }
  {
    seen++; record_cb=0; record_ub=0; cb_value=""; ub_value=""
    for (i=12; i<=NF; i++) {
      if ($i ~ /^CB:Z:/) { record_cb++; cb_value=substr($i,6) }
      if ($i ~ /^UB:Z:/) { record_ub++; ub_value=substr($i,6) }
    }
    if (record_cb == 1) cb++; else bad_cb_count++
    if (record_ub == 1) ub++; else bad_ub_count++
    if (record_cb == 1 && (length(cb_value) != 16 || cb_value !~ /^[ACGT]+$/)) invalid_cb++
    if (record_ub == 1 && (length(ub_value) != 12 || ub_value !~ /^[ACGTN]+$/)) invalid_ub++
    if (record_cb == 1 && !(cb_value in allowed)) outside_whitelist++
    if (seen >= 100000) exit
  }
  END {
    printf "records_checked\t%d\nrecords_with_single_CB\t%d\nrecords_with_single_UB\t%d\n", seen, cb, ub
    printf "records_with_bad_CB_count\t%d\nrecords_with_bad_UB_count\t%d\n", bad_cb_count, bad_ub_count
    printf "invalid_CB_value\t%d\ninvalid_UB_value\t%d\nCB_outside_whitelist\t%d\n", invalid_cb, invalid_ub, outside_whitelist
    if (seen == 0 || cb != seen || ub != seen || invalid_cb || invalid_ub || outside_whitelist) exit 4
  }
' > "$provenance/first_100k_tag_validation.tsv"
tag_status=${PIPESTATUS[1]}
set -o pipefail
if [[ "$tag_status" -ne 0 ]]; then
  echo "CB/UB validation failed" >&2
  exit "$tag_status"
fi

{
  printf 'completed_utc\t%s\n' "$(date -u +%FT%TZ)"
  stat -c 'bam_bytes\t%s' "$outdir/align2genome.bam"
  stat -c 'bai_bytes\t%s' "$outdir/align2genome.bam.bai"
} > "$outdir/ALIGNMENT.DONE"
