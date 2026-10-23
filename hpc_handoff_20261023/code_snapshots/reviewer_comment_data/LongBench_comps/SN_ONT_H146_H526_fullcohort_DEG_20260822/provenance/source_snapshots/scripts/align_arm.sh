#!/usr/bin/env bash
# Controlled-arm alignment: align an arm's RAW fastq ONCE.
#
# Rationale: every demultiplexer consumes the SAME reads, so a read's genomic alignment is
# tool-independent. Aligning once and joining each tool's (read_id -> barcode,UMI) onto a single
# shared (read_id -> gene) table makes "identical reference, aligner, parameters and feature rules"
# exact by construction rather than merely intended. It also removes any possibility that aligner
# nondeterminism masquerades as a difference between demultiplexers.
#
# Usage: align_arm.sh <arm_name> <raw_fastq.gz> [threads]
set -uo pipefail

WD=/scratch-nfs/f005f43/rad_biological_benchmark_20260731
source "$WD/scripts/lib_run.sh"

ARM="$1"
FQ="$2"
THREADS="${3:-48}"

BIN=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/envs/ab_assembly/bin
MINIMAP2="$BIN/minimap2"
SAMTOOLS="$BIN/samtools"
REF=/scratch-nfs/f005f43/longbench_full_demux_20260730/references/gencode_v44/GRCh38.primary_assembly.genome.fa
MMI="$WD/refs/GRCh38.primary_assembly.splice.mmi"

OUT="$WD/align/$ARM"
mkdir -p "$OUT" "$WD/refs"

export DATASET="LongBench" SAMPLE="$ARM"

# ---- 1. splice index (built once, shared by every arm) ----
if [[ ! -f "$WD/refs/.mmi.done" ]]; then
  echo "[$(date -Is)] building minimap2 splice index"
  "$MINIMAP2" -x splice -d "$MMI" -t "$THREADS" "$REF" \
      > "$WD/logs/mmi_build.stdout" 2> "$WD/logs/mmi_build.stderr"
  rc=$?
  if [[ $rc -ne 0 || ! -s "$MMI" ]]; then echo "[FAIL] index build rc=$rc"; exit 1; fi
  sha256sum "$MMI" > "$WD/refs/GRCh38.primary_assembly.splice.mmi.sha256"
  date -Is > "$WD/refs/.mmi.done"
fi

# ---- 2. alignment ----
# -ax splice          : spliced alignment for cDNA
# (no -u)             : do NOT assume the read is the sense strand. Raw 10x ONT cDNA reads occur in
#                       BOTH orientations; -uf would mis-call splice sites on antisense reads.
#                       Gene assignment downstream is therefore strand-agnostic, identically for all tools.
# --secondary=no      : one alignment per read, so read_id -> gene is well defined
# --MD -Y             : MD tag for downstream QC; soft-clip supplementary alignments
if [[ ! -f "$OUT/.align.done" ]]; then
  run_tool "align_${ARM}" "$OUT/minimap2" "minimap2" "2.30-r1287" "ax_splice_secondary_no_t${THREADS}" -- \
    bash -c "'$MINIMAP2' -ax splice --secondary=no --MD -Y -t $THREADS '$MMI' '$FQ' \
             | '$SAMTOOLS' sort -@ 8 -m 3G -o '$OUT/${ARM}.bam' - && '$SAMTOOLS' index -@ 8 '$OUT/${ARM}.bam'"
  rc=$?
  if [[ $rc -ne 0 ]]; then echo "[FAIL] alignment rc=$rc"; exit 1; fi

  # ---- validation before the marker ----
  if ! "$SAMTOOLS" quickcheck -v "$OUT/${ARM}.bam"; then echo "[FAIL] bam quickcheck"; exit 1; fi
  "$SAMTOOLS" flagstat -@ 8 "$OUT/${ARM}.bam" > "$OUT/${ARM}.flagstat.txt"
  "$SAMTOOLS" idxstats "$OUT/${ARM}.bam" > "$OUT/${ARM}.idxstats.txt"
  n_primary=$(awk '/primary mapped/{print $1; exit}' "$OUT/${ARM}.flagstat.txt")
  if [[ -z "$n_primary" || "$n_primary" == "0" ]]; then echo "[FAIL] zero primary mapped"; exit 1; fi
  sha256sum "$OUT/${ARM}.bam" > "$OUT/${ARM}.bam.sha256"
  mark_validated "$OUT/minimap2" "align_${ARM}" "bam quickcheck ok, primary_mapped=${n_primary}"
  date -Is > "$OUT/.align.done"
  echo "[$(date -Is)] alignment complete: $n_primary primary mapped"
fi
echo "[DONE] $ARM"
