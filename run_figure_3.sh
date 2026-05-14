#!/usr/bin/env bash
# =============================================================================
# Figure 3: Benchmarking RAD on Real Immune Receptor Data (RAGEseq)
# =============================================================================
# Panels: 3A-3K + entropy analysis + RAD vs BLAZE count comparison
#
# Datasets:
#   - RAGEseq (rageseq.fq.gz) — demux with whitelist and global WL modes
#   - False positive whitelist tests (3 replicates)
#
# What this does:
#   1. Runs rad demux on RAGEseq data (total+analysis mode)
#   2. Runs rad demux with global whitelist
#   3. Runs false positive whitelist tests (3 reps)
#   4. Renders figure_3_analysis.Rmd
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

check_ssd
check_rad

# --- Configuration ---
STAMP=$(timestamp)
DEMUX_MODE="${1:-full}"   # "full" or "analysis"

# --- Input ---
RSQ_FQ="${RAW_FQ}/rageseq.fq.gz"

# --- Output directories ---
FIG3_DEMUX_BASE="${RESULTS_BASE}/rageseq"
RSQ_TOT_OUT="${FIG3_DEMUX_BASE}/${STAMP}_rsq_tot_and_analysis"
RSQ_GLOBAL_WL_OUT="${FIG3_DEMUX_BASE}/${STAMP}_rsq_global_wl"
FP_BASE="${RESULTS_BASE}/false_positive_wl"

# =============================================================================
# STEP 1: RAD DEMUX — RAGEseq
# =============================================================================
if [ "$DEMUX_MODE" = "full" ]; then
  log_start "Figure 3 — RAD demux on RAGEseq data"

  # --- RAGEseq total + analysis (with custom whitelist) ---
  ensure_dir "$RSQ_TOT_OUT"
  echo ">> RAGEseq total+analysis (custom WL, 10x_3v1)..."
  "$RAD_BIN" demux \
    -l three_prime \
    -k 10x_3v1 \
    -c "$RAGESEQ_WL" \
    -q "$RSQ_FQ" \
    -t "$RAD_THREADS" \
    -d "$RSQ_TOT_OUT" \
    -o rsq_tot \
    -v \
    -F "${RSQ_TOT_OUT}/rsq_tot_rad.log"

  # --- RAGEseq global whitelist ---
  ensure_dir "$RSQ_GLOBAL_WL_OUT"
  echo ">> RAGEseq global whitelist..."
  "$RAD_BIN" demux \
    -l three_prime \
    -k 10x_3v1 \
    -q "$RSQ_FQ" \
    -t "$RAD_THREADS" \
    -d "$RSQ_GLOBAL_WL_OUT" \
    -o rsq_global_wl \
    -v \
    -F "${RSQ_GLOBAL_WL_OUT}/rsq_global_wl_rad.log"

  # --- False positive whitelist tests (3 replicates) ---
  for rep in 1 2 3; do
    fp_out="${FP_BASE}/${STAMP}_rad_fp${rep}"
    ensure_dir "$fp_out"
    echo ">> False positive test replicate ${rep}..."
    "$RAD_BIN" demux \
      -l three_prime \
      -k 10x_3v1 \
      -c "$RAGESEQ_DUMMY_WL" \
      -q "$RSQ_FQ" \
      -t "$RAD_THREADS" \
      -d "$fp_out" \
      -o "fp_rep${rep}" \
      -v \
      -F "${fp_out}/fp_rep${rep}_rad.log"
  done

  log_done "Figure 3 — RAD demux"

  # Write manifest
  cat > "${SCRIPT_DIR}/figure_3/.last_demux_paths.txt" <<MANIFEST
rsq_tot=${RSQ_TOT_OUT}
rsq_global_wl=${RSQ_GLOBAL_WL_OUT}
fp_rep1=${FP_BASE}/${STAMP}_rad_fp1
fp_rep2=${FP_BASE}/${STAMP}_rad_fp2
fp_rep3=${FP_BASE}/${STAMP}_rad_fp3
MANIFEST
fi

# =============================================================================
# STEP 2: R ANALYSIS — Render Figure 3
# =============================================================================
log_start "Figure 3 — R analysis"

cd "${SCRIPT_DIR}/figure_3"
Rscript -e "rmarkdown::render('figure_3_analysis.Rmd', output_dir = '.')"

log_done "Figure 3 — Complete"
echo "Output: ${SCRIPT_DIR}/figure_3/figure_3_analysis.html"
