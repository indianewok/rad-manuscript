#!/usr/bin/env bash
# =============================================================================
# Figure 5: Isotype-Resolved B-cell Clonotype Analysis
# =============================================================================
# Panels: 5A-5G
#
# Figure 5 uses NBC BCR + Visium spatial demultiplexed data from Figure 4.
# Downstream clonotyping is done via IgBLAST and custom R pipelines.
#
# What this does:
#   1. (Optional) Re-runs NBC demux if not already done in Figure 4
#   2. Runs IgBLAST clonotyping pipeline on demuxed NBC BCR reads
#   3. Generates chr14 depth data for IGH locus histograms
#   4. Renders figure_5_analysis.Rmd (heatmaps, spatial plots, depth histograms)
#   5. Exports raw data CSVs for Prism/PowerPoint figure assembly
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${REPO_ROOT}/config.sh"

check_ssd
check_rad

# --- Configuration ---
STAMP=$(timestamp)
DEMUX_MODE="${1:-analysis}"  # "full" (re-run demux + igblast), "igblast" (just clonotyping), "analysis" (Rmd only)

# --- Paths to existing demuxed data (from Figure 4 runs or prior) ---
# These can be overridden by setting env vars before running
NBC_DEMUX_DIR="${NBC_DEMUX_DIR:-${RESULTS_BASE}/sans_wl/nbc_wl}"
VISIUM_DEMUX_BASE="${VISIUM_DEMUX_BASE:-${RESULTS_BASE}/visium_data}"

# --- IgBLAST / clonotyping paths ---
IGBLAST_SCRIPT="${PROJECT_SCRIPTS}/rnabloom_to_igblast.sh"
IG_MAPPING_SCRIPT="${PROJECT_SCRIPTS}/generate_ig_mappings.sh"

# =============================================================================
# STEP 1: (Optional) RAD DEMUX — NBC BCR data
# =============================================================================
if [ "$DEMUX_MODE" = "full" ]; then
  log_start "Figure 5 — RAD demux (NBC BCR)"

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
  log_done "Figure 5 — RAD demux"
fi

# =============================================================================
# STEP 2: (Optional) IgBLAST clonotyping pipeline
# =============================================================================
if [ "$DEMUX_MODE" = "full" ] || [ "$DEMUX_MODE" = "igblast" ]; then
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

cd "${REPO_ROOT}/figure_5"
Rscript -e "rmarkdown::render('figure_5_analysis.Rmd', output_dir = '.')"

log_done "Figure 5 — Complete"
echo "Output: ${REPO_ROOT}/figure_5/figure_5_analysis.html"

# =============================================================================
# STEP 4: Export raw data for Prism / PowerPoint
# =============================================================================
echo ""
echo "Exported data locations:"
echo "  Heatmap raw data:     ${REPO_ROOT}/figure_5/heatmap_raw_data/"
echo "  Histogram raw data:   ${REPO_ROOT}/figure_5/histogram_raw_data/"
echo "  Scatterplot raw data: ${REPO_ROOT}/figure_5/scatterplot_raw_data/"
echo ""
echo "To assemble final figure, open in Prism or PowerPoint from:"
echo "  ${FIGURES_DIR}/figure_5/"
