#!/usr/bin/env bash
# =============================================================================
# Figure 5: Isotype-Resolved B-cell Clonotype Analysis
# =============================================================================
# Panels: 5A-5G
#
# Figure 5 uses NBC BCR + Engblom Visium tonsil spatial demultiplexed data.
# Downstream clonotyping is done via IgBLAST and custom R pipelines.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

DEMUX_MODE="${1:-analysis}"   # "full" / "igblast" / "analysis"

if [ "$DEMUX_MODE" = "full" ]; then
  require_env RAD_BIN RAW_FQ WL_DIR RESULTS_BASE PROJECT_SCRIPTS
  require_file_executable "$RAD_BIN" "rad binary"
fi

STAMP=$(timestamp)

NBC_DEMUX_DIR="${NBC_DEMUX_DIR:-${RESULTS_BASE:-/PLACEHOLDER}/sans_wl/nbc_wl}"
VISIUM_DEMUX_BASE="${VISIUM_DEMUX_BASE:-${RESULTS_BASE:-/PLACEHOLDER}/visium_data}"

IGBLAST_SCRIPT="${PROJECT_SCRIPTS:-/PLACEHOLDER}/rnabloom_to_igblast.sh"
IG_MAPPING_SCRIPT="${PROJECT_SCRIPTS:-/PLACEHOLDER}/generate_ig_mappings.sh"

# =============================================================================
# STEP 1: (Optional) RAD DEMUX — NBC BCR + Engblom Visium tonsil
# =============================================================================
# The Visium tonsil 8-section demux used to live in run_figure_4.sh when 4I-K
# were tonsil panels. After the Visium HD reshuffle, the only consumer of the
# tonsil demux output is Figure 5's spatial clone maps (panels 5E + 5G), so
# the loop now lives here.
if [ "$DEMUX_MODE" = "full" ]; then
  log_start "Figure 5 — RAD demux (NBC BCR + Engblom Visium tonsil)"

  NBC_OUT="${RESULTS_BASE}/sans_wl/${STAMP}_nbc_wl_fig5"
  ensure_dir "$NBC_OUT"
  echo ">> NBC BCR with whitelist (for Figure 5)..."
  "$RAD_BIN" demux \
    -l five_prime \
    -k 10x_5v1 \
    -c "$NBC_WL" \
    -q "$NBC_BCR_FQ" \
    -t "$RAD_THREADS" \
    -d "$NBC_OUT" \
    -o nbc_wl \
    -v \
    -F "${NBC_OUT}/nbc_wl_rad.log"

  NBC_DEMUX_DIR="$NBC_OUT"

  # ---------------------------------------------------------------------------
  # Engblom et al. tonsil Visium spatial — 8 sections × 2 patients (pt072, pt086)
  # Used by Figure 5 for the spatial clone maps; required for panels 5E + 5G.
  # ---------------------------------------------------------------------------
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

  log_done "Figure 5 — RAD demux"
fi

# =============================================================================
# STEP 2: (Optional) IgBLAST clonotyping pipeline
# =============================================================================
if [ "$DEMUX_MODE" = "full" ] || [ "$DEMUX_MODE" = "igblast" ]; then
  require_env PROJECT_SCRIPTS
  log_start "Figure 5 — IgBLAST clonotyping"

  if [ -x "$IGBLAST_SCRIPT" ]; then
    echo ">> Running IgBLAST pipeline on NBC demuxed reads..."
    bash "$IGBLAST_SCRIPT" "$NBC_DEMUX_DIR"
  else
    echo "WARNING: IgBLAST script not found or not executable: $IGBLAST_SCRIPT"
    echo "Skipping clonotyping. Ensure figure_5_workspace.RData is up to date."
  fi

  if [ -x "$IG_MAPPING_SCRIPT" ]; then
    echo ">> Generating IG mappings..."
    bash "$IG_MAPPING_SCRIPT"
  fi

  log_done "Figure 5 — IgBLAST"
fi

# =============================================================================
# STEP 3: R ANALYSIS — Render Figure 5
# =============================================================================
log_start "Figure 5 — R analysis"

cd "${REPO_ROOT}/figures/figure_5"
Rscript -e "rmarkdown::render('figure_5_analysis.Rmd', output_dir = '.')"

log_done "Figure 5 — Complete"
echo "Output: ${REPO_ROOT}/figures/figure_5/figure_5_analysis.html"

# =============================================================================
# STEP 4: Export raw data for Prism / PowerPoint
# =============================================================================
echo ""
echo "Exported data locations:"
echo "  Heatmap raw data:     ${REPO_ROOT}/figures/figure_5/heatmap_raw_data/"
echo "  Histogram raw data:   ${REPO_ROOT}/figures/figure_5/histogram_raw_data/"
echo "  Scatterplot raw data: ${REPO_ROOT}/figures/figure_5/scatterplot_raw_data/"
