#!/bin/bash
# Figure 3G-H read-level analysis for RAD and BLAZE, RAGE-seq cell line.
#
# Purpose: make the same per-barcode BCR/TCR counts that the Flexiplex run
# already made, so all 3 tools sit in one frame.
#
# The BCR/TCR alignment is NOT repeated. All tools read the same raw reads,
# so this script reuses rage_bcrtcr_hits.tsv from the Flexiplex run.
# That file is the expensive part. Do not make it again.
#
# Usage:  bash run_rad_blaze_bcrtcr.sh [rad|blaze|both]
# Suggested resources: 32 cores, 64 GB, 6 hours.

set -euo pipefail

WORK=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811
PKG=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/wl_scan/20260730_rageseq_ERR3268991_cellline_control
FASTQ=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/rageseq.fq.gz
HITS="$WORK/rage_bcrtcr_hits.tsv"
CELLTYPES="$WORK/rageseq_barcode_celltype_map.csv"
THREADS=32
WHICH="${1:-both}"
# The benchmark package records this native BLAZE 2.6.0a0 executable.  The
# generic PATH entry on this node is an unrelated BLAZE 2.1.3 install whose
# pandas ABI cannot load; use the documented benchmark executable explicitly.
BLAZE=/scratch/f005f43/blaze2_260a0_native_20260727/venv/bin/blaze
BLAZE_LIB=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/pkgs/libstdcxx-ng-13.2.0-hc0a3c3a_7/lib

OUT=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/rad_blaze_bcrtcr_cellline
mkdir -p "$OUT"
cd "$OUT"

# The requested `both` workflow runs its two independent arms concurrently.
# Keep each child on a disjoint 46-CPU affinity set (92 logical CPUs total);
# the RAD/BLAZE tool arguments below remain unchanged at 32 threads each.
# Child invocations use this same wrapper so the exact per-arm workflow and
# settings are preserved.  The parent waits for both arms before succeeding.
if [ "$WHICH" = "both" ]; then
  echo "[$(date -u +%FT%TZ)] launching RAD on CPUs 0-45 and BLAZE on CPUs 46-91 (32 tool threads each)"
  rad_rc=0
  blaze_rc=0
  taskset -c 0-45 bash "$WORK/run_rad_blaze_bcrtcr.sh" rad &
  rad_pid=$!
  taskset -c 46-91 bash "$WORK/run_rad_blaze_bcrtcr.sh" blaze &
  blaze_pid=$!
  wait "$rad_pid" || rad_rc=$?
  wait "$blaze_pid" || blaze_rc=$?
  if [ "$rad_rc" -ne 0 ] || [ "$blaze_rc" -ne 0 ]; then
    echo "RAD exit=$rad_rc; BLAZE exit=$blaze_rc" >&2
    exit 1
  fi
  exit 0
fi

for f in "$HITS" "$CELLTYPES" "$FASTQ"; do
  [ -s "$f" ] || { echo "MISSING INPUT: $f" >&2; exit 1; }
done

# ---------------------------------------------------------------- RAD ----
# The parameters copy the benchmark run exactly. See the package file
# analysis/timing_by_phase.tsv, row RAD_demux.
# -w writes the debug FASTQ. Its headers carry CB:Z (final barcode) and
# CR:Z (raw barcode). An empty CR:Z means the barcode needed no correction.
# The output prefix must differ from the input file name.
if [ "$WHICH" = "rad" ] || [ "$WHICH" = "both" ]; then
  echo "[$(date -u +%FT%TZ)] RAD demux start"
  mkdir -p rad
  /usr/bin/time -v rad demux \
    -l three_prime \
    -q "$FASTQ" \
    -g "$PKG/input/10x_3v2_full_whitelist.txt" \
    -c "$PKG/runs/rad/scan/rageseq.txt" \
    -R offensive -M 2 -m 2 -z 10000 \
    -o radout -d rad -t "$THREADS" -w \
    > rad/demux.stdout.log 2> rad/demux.time.txt

  python3 "$WORK/extract_per_read.py" --tool rad \
    --fastq rad/radout_dbg.fq.gz --out rad_per_read.tsv

  python3 "$WORK/join_tool_bcrtcr.py" \
    --per-read rad_per_read.tsv --hits "$HITS" \
    --celltypes "$CELLTYPES" --prefix RAD
  echo "[$(date -u +%FT%TZ)] RAD done"
fi

# -------------------------------------------------------------- BLAZE ----
# --expect-cells 4505 matches the benchmark. --output-fastq is required:
# the matched FASTQ carries the corrected barcode in a CB:Z tag.
# putative_bc.csv carries the raw barcode per read, and the script marks a
# read native when the raw barcode equals the final barcode.
if [ "$WHICH" = "blaze" ] || [ "$WHICH" = "both" ]; then
  echo "[$(date -u +%FT%TZ)] BLAZE start"
  mkdir -p blaze
  ( cd blaze && LD_LIBRARY_PATH="$BLAZE_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" /usr/bin/time -v "$BLAZE" \
      --expect-cells 4505 \
      --10x-kit-version 3v2 \
      --threads "$THREADS" \
      --max-edit-distance 2 \
      --output-prefix ./ \
      --output-fastq matched_reads.fastq.gz \
      --overwrite \
      "$FASTQ" > blaze.stdout.log 2> blaze.time.txt )

  python3 "$WORK/extract_per_read.py" --tool blaze \
    --fastq blaze/matched_reads.fastq.gz \
    --putative blaze/putative_bc.csv --out blaze_per_read.tsv

  python3 "$WORK/join_tool_bcrtcr.py" \
    --per-read blaze_per_read.tsv --hits "$HITS" \
    --celltypes "$CELLTYPES" --prefix BLAZE
  echo "[$(date -u +%FT%TZ)] BLAZE done"
fi

echo
echo "Outputs in $OUT:"
ls -la *_bcrtcr_summary.tsv *_bcrtcr_data11.tsv *_per_barcode_bcrtcr.tsv 2>/dev/null

cat <<'NOTE'

CHECK THESE NUMBERS against the 2026-07-30 benchmark package
(analysis/demux_assignment_metrics.tsv):
  RAD    assigned unique reads   expect about 7,653,089
         ambiguous dropped       expect about 63,560
  BLAZE  assigned unique reads   expect about 5,588,729
         ambiguous dropped       expect 0
Report any difference greater than 1 percent. A small difference is normal
when the tool version differs; a large one means the parameters are wrong.
NOTE
