#!/usr/bin/env bash
# =============================================================================
# RAD Manuscript — Run All Figure Harnesses
# =============================================================================
# Usage:
#   ./run_all_figures.sh                  # Full pipeline (demux + analysis)
#   ./run_all_figures.sh analysis         # R analysis only (skip demux)
#   ./run_all_figures.sh 2 3              # Only figures 2 and 3
#   ./run_all_figures.sh analysis 4 5     # Analysis-only for figures 4 and 5
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

check_ssd
check_rad

# Parse arguments
MODE="full"
FIGURES=()
for arg in "$@"; do
  case "$arg" in
    full|analysis) MODE="$arg" ;;
    [2-5])         FIGURES+=("$arg") ;;
    *)             echo "Unknown argument: $arg"; exit 1 ;;
  esac
done

# Default to all figures if none specified
if [ ${#FIGURES[@]} -eq 0 ]; then
  FIGURES=(2 3 4 5)
fi

echo "============================================"
echo " RAD Manuscript Figure Generation"
echo " Mode: ${MODE}"
echo " Figures: ${FIGURES[*]}"
echo " Started: $(date)"
echo "============================================"
echo ""

FAILED=()
for fig in "${FIGURES[@]}"; do
  echo "--------------------------------------------"
  echo " Running Figure ${fig}..."
  echo "--------------------------------------------"
  if bash "${SCRIPT_DIR}/run_figure_${fig}.sh" "$MODE"; then
    echo ">> Figure ${fig}: SUCCESS"
  else
    echo ">> Figure ${fig}: FAILED"
    FAILED+=("$fig")
  fi
  echo ""
done

echo "============================================"
echo " Summary"
echo " Finished: $(date)"
echo "============================================"
if [ ${#FAILED[@]} -eq 0 ]; then
  echo " All figures completed successfully."
else
  echo " FAILED figures: ${FAILED[*]}"
  exit 1
fi
