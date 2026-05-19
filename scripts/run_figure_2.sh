#!/usr/bin/env bash
# =============================================================================
# Figure 2: Benchmarking RAD on Synthetic (ScTagger) Data
# =============================================================================
# Panels: 2B-2J + Supplemental (downsampling, edit distances, ROC/PR)
#
# Datasets:
#   - ScTagger L simulation (shuffled synthetic long reads)
#   - ScTagger S, M simulations
#   - ScTagger downsampled subsets (100K, 250K, 500K)
#
# Pipeline per simulation:
#   1. generate_whitelist → produces .txt (final barcodes) + .csv (all candidates)
#   2. rad demux with .txt as custom whitelist → produces demuxed .fq.gz
#   3. extract_rad_headers_new.sh → parses FASTQ headers into extracted_headers.csv
#   4. Renders figure_2_analysis.Rmd
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

DEMUX_MODE="${1:-full}"   # "full" = rerun WL gen + demux + analysis; "analysis" = Rmd only

if [ "$DEMUX_MODE" = "full" ]; then
  require_env RAD_BIN GEN_WL_BIN EXTRACT_HEADERS RAW_FQ RESULTS_BASE SCTAGGER_SIM
  require_file_executable "$RAD_BIN" "rad binary"
  require_file_executable "$GEN_WL_BIN" "generate_whitelist binary"
fi

STAMP=$(timestamp)

# --- ScTagger layout parameters (from sctagger_sim_read_layout.csv) ---
SCTAGGER_PRIMER="CTACACGACGCTCTTCCGATCT"   # 22bp forward primer
SCTAGGER_BC_LEN=16

FIG2_DEMUX_BASE="${RESULTS_BASE:-/PLACEHOLDER}/synthetic_data"

# =============================================================================
# STEP 1: GENERATE WHITELISTS + RAD DEMUX + EXTRACT HEADERS per simulation
# =============================================================================
if [ "$DEMUX_MODE" = "full" ]; then
  log_start "Figure 2 — Whitelist generation + RAD demux on ScTagger data"

  if [ ! -f "$EXTRACT_HEADERS" ]; then
    echo "ERROR: extract_rad_headers_new.sh not found at $EXTRACT_HEADERS"
    echo "Set EXTRACT_HEADERS (or PROJECT_SCRIPTS) — see README.md → Setup."
    exit 1
  fi

  # Map sim tags to FASTQ paths (bash 3.2 compatible)
  get_sctagger_fq() {
    case "$1" in
      S)    echo "${SCTAGGER_SIM}/shuffled_S_lr_synth.fq.gz" ;;
      M)    echo "${SCTAGGER_SIM}/shuffled_M_lr_synth.fq.gz" ;;
      L)    echo "${SCTAGGER_SIM}/shuffled_L_lr_synth.fq.gz" ;;
      100K) echo "${SCTAGGER_SIM}/100K_downsampled_L_lr_synth.fq.gz" ;;
      250K) echo "${SCTAGGER_SIM}/250K_downsampled_L_lr_synth.fq.gz" ;;
      500K) echo "${SCTAGGER_SIM}/500K_downsampled_L_lr_synth.fq.gz" ;;
    esac
  }

  for sim_tag in S M L 100K 250K 500K; do
    sim_fq="$(get_sctagger_fq "$sim_tag")"
    sim_out="${FIG2_DEMUX_BASE}/${STAMP}_sctagger_${sim_tag}"
    ensure_dir "$sim_out"

    # --- Step 1a: Generate whitelist ---
    wl_prefix="${sim_out}/sctagger_${sim_tag}_generated_wl"
    echo ">> [${sim_tag}] Generating whitelist from ${sim_fq}..."
    "$GEN_WL_BIN" \
      -i "$sim_fq" \
      -o "$wl_prefix" \
      -p "$SCTAGGER_PRIMER" \
      -n "$SCTAGGER_BC_LEN" \
      -w 10x_3v3 \
      -e 0.3 \
      -t "$RAD_THREADS" \
      -v

    generated_wl="${wl_prefix}.txt"
    if [ ! -f "$generated_wl" ]; then
      echo "WARNING: No whitelist .txt generated for ${sim_tag}, skipping demux"
      continue
    fi

    wl_count=$(wc -l < "$generated_wl" | tr -d ' ')
    echo ">> [${sim_tag}] Generated whitelist: ${generated_wl} (${wl_count} barcodes)"

    # --- Step 1b: Demux with generated whitelist ---
    echo ">> [${sim_tag}] Running rad demux with generated whitelist..."
    "$RAD_BIN" demux \
      -l sctagger \
      -k 10x_3v3 \
      -c "$generated_wl" \
      -q "$sim_fq" \
      -t "$RAD_THREADS" \
      -d "$sim_out" \
      -o "sctagger_${sim_tag}" \
      -v \
      -F "${sim_out}/sctagger_${sim_tag}_rad.log"

    # --- Step 1c: Extract headers from demuxed FASTQ ---
    demuxed_fq="${sim_out}/sctagger_${sim_tag}.fq.gz"
    headers_csv="${sim_out}/extracted_headers.csv"
    if [ -f "$demuxed_fq" ]; then
      echo ">> [${sim_tag}] Extracting headers from ${demuxed_fq}..."
      bash "$EXTRACT_HEADERS" "$demuxed_fq" "$headers_csv"
    else
      echo "WARNING: Demuxed FASTQ not found at ${demuxed_fq}"
    fi

    echo ">> [${sim_tag}] Done."
    echo ""
  done

  log_done "Figure 2 — Whitelist generation + RAD demux + header extraction"

  # Write manifest so the Rmd knows where to find results
  cat > "${REPO_ROOT}/figures/figure_2/.last_demux_paths.txt" <<MANIFEST
timestamp=${STAMP}
sctagger_S=${FIG2_DEMUX_BASE}/${STAMP}_sctagger_S
sctagger_M=${FIG2_DEMUX_BASE}/${STAMP}_sctagger_M
sctagger_L=${FIG2_DEMUX_BASE}/${STAMP}_sctagger_L
ds_100K=${FIG2_DEMUX_BASE}/${STAMP}_sctagger_100K
ds_250K=${FIG2_DEMUX_BASE}/${STAMP}_sctagger_250K
ds_500K=${FIG2_DEMUX_BASE}/${STAMP}_sctagger_500K
MANIFEST
fi

# =============================================================================
# STEP 2: R ANALYSIS — Render Figure 2
# =============================================================================
log_start "Figure 2 — R analysis"

cd "${REPO_ROOT}/figures/figure_2"
Rscript -e "rmarkdown::render('figure_2_analysis.Rmd', output_dir = '.')"

log_done "Figure 2 — Complete"
echo "Output: ${REPO_ROOT}/figures/figure_2/figure_2_analysis.html"
