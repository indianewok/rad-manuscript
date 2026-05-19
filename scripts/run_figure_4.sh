#!/usr/bin/env bash
# =============================================================================
# Figure 4: Computational Efficiency and Generalizability
# =============================================================================
# Panels: 4A-4K
#
# Datasets:
#   - scMixology2 (3 timing replicates)          — Panels 4A-4B
#   - Split-seq                                    — Panel 4D
#   - NBC BCR (sans WL + with WL)                  — Panel 4F, 4G-4H
#   - Visium spatial (8 barcodes × 2 patients)     — Panels 4I-4K
#   - LA1/LA2/LA3 sans/with WL                     — Panel 4F (supplemental)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

DEMUX_MODE="${1:-full}"      # "full" or "analysis"
SKIP_TIMING="${2:-false}"    # "true" to skip scmix timing runs (expensive)
SKIP_LA="${3:-false}"        # "true" to skip LA benchmark runs (very expensive)

if [ "$DEMUX_MODE" = "full" ]; then
  require_env RAD_BIN RAW_FQ WL_DIR RESULTS_BASE
  require_file_executable "$RAD_BIN" "rad binary"
fi

STAMP=$(timestamp)

# =============================================================================
# STEP 1: RAD DEMUX
# =============================================================================
if [ "$DEMUX_MODE" = "full" ]; then
  log_start "Figure 4 — RAD demux (multi-platform)"

  # -------------------------------------------------------------------------
  # 4A-4B: scMixology2 timing runs (3 replicates, single-threaded)
  # -------------------------------------------------------------------------
  if [ "$SKIP_TIMING" != "true" ]; then
    for rep in 1 2 3; do
      scmix_out="${RESULTS_BASE}/scmixology2/${STAMP}_scmix_timing_run_r${rep}"
      ensure_dir "$scmix_out"
      echo ">> scMixology2 timing replicate ${rep} (single-threaded)..."
      "$RAD_BIN" demux \
        -l three_prime \
        -k 10x_3v3 \
        -c "$SCMIX2_WL" \
        -q "$SCMIX2_FQ" \
        -t 1 \
        -d "$scmix_out" \
        -o "scmix2_r${rep}" \
        -v \
        -F "${scmix_out}/scmix2_r${rep}_rad.log"
    done
  else
    echo ">> Skipping scMixology2 timing runs (SKIP_TIMING=true)"
  fi

  # -------------------------------------------------------------------------
  # 4D: Split-seq (3-barcode detection)
  # -------------------------------------------------------------------------
  SPLITSEQ_OUT="${RESULTS_BASE}/splitseq/${STAMP}_splitseq"
  ensure_dir "$SPLITSEQ_OUT"
  echo ">> Split-seq..."
  "$RAD_BIN" demux \
    -l splitseq \
    -q "$SPLITSEQ_FQ" \
    -t "$RAD_THREADS" \
    -d "$SPLITSEQ_OUT" \
    -o splitseq \
    -v \
    -F "${SPLITSEQ_OUT}/splitseq_rad.log"

  # -------------------------------------------------------------------------
  # 4F + 4G-4H: NBC BCR data (sans whitelist and with whitelist)
  # -------------------------------------------------------------------------
  NBC_SANS_OUT="${RESULTS_BASE}/sans_wl/${STAMP}_nbc_sans"
  NBC_WL_OUT="${RESULTS_BASE}/sans_wl/${STAMP}_nbc_wl"

  ensure_dir "$NBC_SANS_OUT"
  echo ">> NBC BCR sans whitelist..."
  "$RAD_BIN" demux \
    -l five_prime \
    -q "$NBC_BCR_FQ" \
    -t "$RAD_THREADS" \
    -d "$NBC_SANS_OUT" \
    -o nbc_sans \
    -v \
    -F "${NBC_SANS_OUT}/nbc_sans_rad.log"

  ensure_dir "$NBC_WL_OUT"
  echo ">> NBC BCR with whitelist..."
  "$RAD_BIN" demux \
    -l five_prime \
    -k 10x_5v1 \
    -c "$NBC_WL" \
    -q "$NBC_BCR_FQ" \
    -t "$RAD_THREADS" \
    -d "$NBC_WL_OUT" \
    -o nbc_wl \
    -v \
    -F "${NBC_WL_OUT}/nbc_wl_rad.log"

  # -------------------------------------------------------------------------
  # 4I-4K: Visium spatial (8 sections)
  # -------------------------------------------------------------------------
  require_env VISIUM_WL_DIR
  VISIUM_SAMPLES=(
    "pt072_bc1009" "pt072_bc1010" "pt072_bc1018" "pt072_bc1020"
    "pt086_bc1011" "pt086_bc1016" "pt086_bc1018" "pt086_bc1020"
  )

  for sample in "${VISIUM_SAMPLES[@]}"; do
    vis_out="${RESULTS_BASE}/visium_data/${STAMP}_${sample}"
    patient="${sample%%_*}"
    barcode="${sample##*_}"
    vis_wl="${VISIUM_WL_DIR}/${patient}_demultiplex_${barcode}.txt"

    ensure_dir "$vis_out"
    echo ">> Visium ${sample}..."
    "$RAD_BIN" demux \
      -l visium \
      -k 10x_Vis_V1 \
      -c "$vis_wl" \
      -q "$SPATIAL_FQ" \
      -t "$RAD_THREADS" \
      -d "$vis_out" \
      -o "$sample" \
      -v \
      -F "${vis_out}/${sample}_rad.log"
  done

  # -------------------------------------------------------------------------
  # Sans-WL / With-WL benchmarks on LA datasets (optional, very large)
  # -------------------------------------------------------------------------
  if [ "$SKIP_LA" != "true" ]; then
    require_env LEENA_WL_DIR

    get_la_fq() {
      case "$1" in
        la1)    echo "$LA1_FQ" ;;
        la2)    echo "$LA2_FQ" ;;
        la3)    echo "$LA3_FQ" ;;
        la1mem) echo "$LA1MEM_FQ" ;;
        la3mem) echo "$LA3MEM_FQ" ;;
      esac
    }
    get_la_wl() {
      case "$1" in
        la1)    echo "" ;;
        la2)    echo "${LEENA_WL_DIR}/la2.txt" ;;
        la3)    echo "${LEENA_WL_DIR}/la3.txt" ;;
        la1mem) echo "${LEENA_WL_DIR}/la1_mem.txt" ;;
        la3mem) echo "${LEENA_WL_DIR}/la3_mem.txt" ;;
      esac
    }

    for ds in la1 la2 la3 la1mem la3mem; do
      fq="$(get_la_fq "$ds")"

      sans_out="${RESULTS_BASE}/sans_wl/${STAMP}_${ds}_sans"
      ensure_dir "$sans_out"
      echo ">> ${ds} sans whitelist..."
      "$RAD_BIN" demux \
        -l three_prime \
        -q "$fq" \
        -t "$RAD_THREADS" \
        -d "$sans_out" \
        -o "${ds}_sans" \
        -v \
        -F "${sans_out}/${ds}_sans_rad.log"

      wl="$(get_la_wl "$ds")"
      if [ -n "$wl" ] && [ -f "$wl" ]; then
        wl_out="${RESULTS_BASE}/sans_wl/${STAMP}_${ds}_wl"
        ensure_dir "$wl_out"
        echo ">> ${ds} with whitelist..."
        "$RAD_BIN" demux \
          -l three_prime \
          -k 10x_3v3 \
          -c "$wl" \
          -q "$fq" \
          -t "$RAD_THREADS" \
          -d "$wl_out" \
          -o "${ds}_wl" \
          -v \
          -F "${wl_out}/${ds}_wl_rad.log"
      fi
    done
  else
    echo ">> Skipping LA benchmark runs (SKIP_LA=true)"
  fi

  log_done "Figure 4 — RAD demux"

  cat > "${REPO_ROOT}/figures/figure_4/.last_demux_paths.txt" <<MANIFEST
splitseq=${SPLITSEQ_OUT}
nbc_sans=${NBC_SANS_OUT}
nbc_wl=${NBC_WL_OUT}
timestamp=${STAMP}
MANIFEST
fi

# =============================================================================
# STEP 2: R ANALYSIS — Render Figure 4
# =============================================================================
log_start "Figure 4 — R analysis"

cd "${REPO_ROOT}/figures/figure_4"

echo ">> Preparing read length/count data..."
Rscript readcountlengthviolinprep.R

Rscript -e "rmarkdown::render('figure_4_analysis.Rmd', output_dir = '.')"

log_done "Figure 4 — Complete"
echo "Output: ${REPO_ROOT}/figures/figure_4/figure_4_analysis.html"
