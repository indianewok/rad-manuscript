#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 RAD|BLAZE|Flexiplex" >&2
  exit 2
fi

tool=$1
run_root=/scratch-nfs/f005f43/longbench_snont_postdemux_vireo_20260803
cellsnp_bin=/scratch-nfs/f005f43/rad_biological_benchmark_20260731/env_snp/bin/cellsnp-lite
tabix_bin=${TABIX_BIN:-/scratch-nfs/f005f43/rad_biological_benchmark_20260731/env_snp/bin/tabix}
vireo_bin="$run_root/env_vireo_0.5.8/bin/vireo"
panel_root="$run_root/bulk_donor_panel"
donor_panel="$panel_root/final/fixed_8line_bulk_illumina_donor_panel.vcf.gz"
donor_panel_index="${donor_panel}.tbi"
donor_ready="$panel_root/validation/BULK_PANEL.VALIDATED.ok"
expected_donors=$'H146\nH1975\nH211\nH2228\nH526\nH69\nHCC827\nSHP77'
cellsnp_threads=${CELLSNP_THREADS:-32}
vireo_threads=${VIREO_THREADS:-16}

case "$tool" in
  RAD)
    bam="$run_root/align/RAD/align2genome.bam"
    alignment_ready="$run_root/align/RAD/ALIGNMENT.DONE"
    whitelist_source=/scratch-nfs/f005f43/longbench_full_demux_20260730/runs/rad_920adda_current/SN_ONT/scan_wl/SN_ONT_RAD.txt
    expected_barcodes=12423
    ;;
  BLAZE)
    bam=/scratch-nfs/f005f43/longbench_full_demux_20260730/runs/flames2.0.1_longbench_published/SN_ONT/align2genome.bam
    alignment_ready="$run_root/align/BLAZE/ALIGNMENT.VALIDATED"
    whitelist_source=/scratch-nfs/f005f43/longbench_full_demux_20260730/runs/blaze2_2.5.0_longbench_published/SN_ONT/whitelist.csv
    expected_barcodes=10001
    ;;
  Flexiplex)
    bam="$run_root/align/Flexiplex/align2genome.bam"
    alignment_ready="$run_root/align/Flexiplex/ALIGNMENT.DONE"
    whitelist_source=/scratch-nfs/f005f43/longbench_snont_postdemux_vireo_20260803/inputs/SN_flexiplex_whitelist.txt
    expected_barcodes=12101
    ;;
  *)
    echo "unknown tool: $tool" >&2
    exit 2
    ;;
esac

for value in "$cellsnp_threads" "$vireo_threads"; do
  [[ "$value" =~ ^[1-9][0-9]*$ ]] || { echo "thread counts must be positive integers" >&2; exit 2; }
done

out_cellsnp="$run_root/cellsnp/$tool"
out_vireo="$run_root/vireo/$tool"
logdir="$run_root/logs"
provenance="$run_root/provenance/$tool"
barcodes="$provenance/cellsnp_barcodes.txt"
mkdir -p "$out_cellsnp" "$out_vireo" "$logdir" "$provenance"

if [[ -e "$out_vireo/VIREO.DONE" || -e "$out_cellsnp/CELLSNP.DONE" ]]; then
  echo "Refusing to mix with an existing $tool CellSNP/Vireo result" >&2
  exit 3
fi

wait_log="$logdir/${tool}_cellsnp_vireo.wait.log"
printf 'waiting_started_utc\t%s\n' "$(date -u +%FT%TZ)" > "$wait_log"
while [[ ! -e "$alignment_ready" || ! -e "$donor_ready" ]]; do
  sleep 30
done
printf 'prerequisites_ready_utc\t%s\n' "$(date -u +%FT%TZ)" >> "$wait_log"

for input in \
  "$bam" "${bam}.bai" "$whitelist_source" \
  "$donor_panel" "$donor_panel_index" "$donor_ready" \
  "$cellsnp_bin" "$tabix_bin" "$vireo_bin"; do
  [[ -r "$input" && -s "$input" ]] || { echo "Missing input: $input" >&2; exit 4; }
done
samtools quickcheck -v "$bam"
observed_contigs=$("$tabix_bin" -l "$donor_panel")
if [[ -z "$observed_contigs" ]]; then
  echo "Bulk donor panel tabix index has no contigs" >&2
  exit 4
fi
observed_donors=$("$tabix_bin" -H "$donor_panel" | awk -F '\t' '
  $1 == "#CHROM" { for (i=10; i<=NF; i++) print $i; found=1 }
  END { if (!found) exit 1 }
')
if [[ "$observed_donors" != "$expected_donors" ]]; then
  echo "Bulk donor panel does not have the required eight named samples in order" >&2
  printf 'expected:\n%s\nobserved:\n%s\n' "$expected_donors" "$observed_donors" >&2
  exit 4
fi

observed_vireo_version=$("$(dirname "$vireo_bin")/python" -c \
  'import vireoSNP; print(vireoSNP.__version__)')
if [[ "$observed_vireo_version" != "0.5.8" ]]; then
  echo "Expected vireoSNP 0.5.8, observed $observed_vireo_version" >&2
  exit 4
fi

awk '{print $1}' "$whitelist_source" > "$barcodes.partial"
awk 'length($0) != 16 || $0 !~ /^[ACGT]+$/ {bad=1} END {exit bad}' "$barcodes.partial"
if [[ "$(wc -l < "$barcodes.partial")" -ne "$expected_barcodes" ]]; then
  echo "$tool barcode-count mismatch" >&2
  exit 5
fi
if [[ "$(sort -u "$barcodes.partial" | wc -l)" -ne "$expected_barcodes" ]]; then
  echo "$tool barcode list contains duplicates" >&2
  exit 5
fi
mv "$barcodes.partial" "$barcodes"

{
  printf 'started_utc\t%s\n' "$(date -u +%FT%TZ)"
  printf 'tool\t%s\n' "$tool"
  printf 'alignment_derivation\ttool-specific post-demultiplexed FASTQ\n'
  printf 'bam\t%s\n' "$bam"
  printf 'barcode_source\t%s\n' "$whitelist_source"
  printf 'barcodes\t%s\n' "$expected_barcodes"
  printf 'donor_panel\t%s\n' "$donor_panel"
  printf 'donor_panel_ready_sentinel\t%s\n' "$donor_ready"
  printf 'donor_samples_order\t%s\n' "$(tr '\n' ',' <<<"$observed_donors" | sed 's/,$//')"
  printf 'cellsnp_threads\t%s\n' "$cellsnp_threads"
  printf 'vireo_threads\t%s\n' "$vireo_threads"
  printf 'cellsnp_cell_tag\tCB\n'
  printf 'cellsnp_umi_tag\tUB\n'
  printf 'cellsnp_min_maf\t0.1\n'
  printf 'cellsnp_min_count\t10\n'
  printf 'vireo_version\t%s\n' "$observed_vireo_version"
  "$cellsnp_bin" --version 2>&1
  sha256sum "$barcodes" "$donor_panel" "$donor_panel_index" "$donor_ready"
} > "$provenance/cellsnp_vireo_manifest.tsv"

/usr/bin/time -v -o "$logdir/${tool}_cellsnp.time.txt" \
  "$cellsnp_bin" \
    -s "$bam" \
    -b "$barcodes" \
    -O "$out_cellsnp" \
    -R "$donor_panel" \
    -p "$cellsnp_threads" \
    --cellTAG CB \
    --UMItag UB \
    --minMAF 0.1 \
    --minCOUNT 10 \
    --gzip \
    --genotype \
    > "$logdir/${tool}_cellsnp.log" 2>&1

for output in cellSNP.base.vcf.gz cellSNP.samples.tsv cellSNP.tag.AD.mtx cellSNP.tag.DP.mtx; do
  [[ -s "$out_cellsnp/$output" ]] || { echo "Missing CellSNP output: $output" >&2; exit 6; }
done
gzip -t "$out_cellsnp/cellSNP.base.vcf.gz"
if [[ "$(wc -l < "$out_cellsnp/cellSNP.samples.tsv")" -gt "$expected_barcodes" ]]; then
  echo "CellSNP emitted more samples than the supplied whitelist" >&2
  exit 6
fi
touch "$out_cellsnp/CELLSNP.DONE"

/usr/bin/time -v -o "$logdir/${tool}_vireo.time.txt" \
  "$vireo_bin" \
    -c "$out_cellsnp" \
    -d "$donor_panel" \
    -o "$out_vireo" \
    -t GT \
    --callAmbientRNAs \
    -p "$vireo_threads" \
    > "$logdir/${tool}_vireo.log" 2>&1

for output in donor_ids.tsv prob_singlet.tsv.gz prob_doublet.tsv.gz prop_ambient.tsv; do
  [[ -s "$out_vireo/$output" ]] || { echo "Missing Vireo output: $output" >&2; exit 7; }
done
gzip -t "$out_vireo/prob_singlet.tsv.gz"
gzip -t "$out_vireo/prob_doublet.tsv.gz"
printf 'completed_utc\t%s\n' "$(date -u +%FT%TZ)" > "$out_vireo/VIREO.DONE"
