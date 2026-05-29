# Environment setup

The figure scripts read **every path from the environment** — there is no config
file to edit. Paste the block below into your shell, **edit the four required
paths**, then run the scripts (see [`README.md`](README.md) → Usage).

```bash
# === required for any figure ===
export RAD_BIN=/path/to/rad                                # built rad binary
export RAW_FQ=/path/to/raw_fastqs                          # root of raw input FASTQs
export RESULTS_BASE=/path/to/results/rad/demultiplexed     # demux output root
export WL_DIR=/path/to/barcode_whitelists                  # barcode whitelist root

# === required for figures 2, 3, 4, 5 ===
export GEN_WL_BIN=/path/to/rad/build/generate_whitelist    # Figure 2 whitelist gen
export PROJECT_SCRIPTS=/path/to/project_specific_scripts   # header parsers + IgBLAST glue
export EXTRACT_HEADERS="${PROJECT_SCRIPTS}/extract_rad_headers_new.sh"

# === required for Figure 3 ===
# verify_fig3.R and graphing_bcr_rad_blaze_counts.R read these:
export FLEXIPLEX_RESULTS=/path/to/results/flexiplex
export RAD_PAPER_DIR=/path/to/rad_paper                    # parent of per-run benchmark dirs

# === required for Figure 4 ===
export WL_DETECTION_RESULTS=/path/to/results/whitelist_detection

# === required for Figure 4 (panels 4I-4K) ===
# Uses the 10X Visium HD mouse brain dataset.
export HD_MAPPING_DIR=/path/to/visium_hd_mapping           # Seurat RDS + tissue_positions_16um.csv

# === required for Figure 5 ===
export NBC_DEPTH_DIR=/path/to/nbc_chr14_depth_csvs         # IGH locus depth CSVs (panel 5A)
# Figure 5's spatial clone maps (5E + 5G) also use the Engblom Visium tonsil demux:
# export VISIUM_WL_DIR="${WL_DETECTION_RESULTS}/120525_visium_data_results"  # auto-derived

# === optional ===
export BLAZE_BIN=/path/to/blaze                            # if regenerating BLAZE benchmarks
export BLAZE_RESULTS=/path/to/results/blaze                # if regenerating BLAZE comparisons
export RAD_THREADS=4                                       # default if unset
```

Scripts fail fast and tell you exactly which variable is missing — no silent guesses.
