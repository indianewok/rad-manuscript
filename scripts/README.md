# scripts/

Shell drivers that wire `rad demux` + `Rscript ::: rmarkdown::render` together for each figure. Every path is resolved from environment variables — see [`../README.md`](../README.md) → Setup for the full list of vars to export before running anything. `_lib.sh` (sourced by every driver) collects shared helpers and the env-var validation that fails fast on missing config.

| Script | Purpose |
|--------|---------|
| `run_all_figures.sh` | Top-level driver — runs any subset of figures 2-5 in either full or analysis-only mode |
| `run_figure_2.sh` | Figure 2: ScTagger synthetic benchmark (whitelist gen + demux + R render) |
| `run_figure_3.sh` | Figure 3: RAGEseq real-data benchmark (RAD demux + off-list FP tests + R render) |
| `run_figure_4.sh` | Figure 4: multi-platform efficiency (scMixology2, Split-seq, NBC, Visium, LA) |
| `run_figure_5.sh` | Figure 5: isotype-resolved B-cell clonotypes (NBC + Visium + IgBLAST + R render) |

## Usage (from the repo root)

```bash
# Full pipeline, all figures (raw FASTQs → demux → render)
./scripts/run_all_figures.sh

# R analysis only (uses cached workspaces from data/ on Zenodo)
./scripts/run_all_figures.sh analysis

# Subset of figures
./scripts/run_all_figures.sh 2 3
./scripts/run_all_figures.sh analysis 4 5

# A single figure directly
./scripts/run_figure_3.sh           # full
./scripts/run_figure_3.sh analysis  # render only
```

`run_figure_4.sh` accepts two extra flags to skip the expensive scMix triplicate timing runs and the large LA benchmark runs:

```bash
./scripts/run_figure_4.sh full true       # skip scmix timing
./scripts/run_figure_4.sh full true true  # also skip LA benchmarks
```

`run_figure_5.sh` defaults to analysis-only because the IgBLAST clonotyping is the expensive part:

```bash
./scripts/run_figure_5.sh           # analysis only (default)
./scripts/run_figure_5.sh igblast   # re-run IgBLAST + render
./scripts/run_figure_5.sh full      # also re-run NBC demux
```

## What each script writes

| Side effect | Where |
|-------------|-------|
| Demux output | `${RESULTS_BASE}/...` (env var) |
| Latest demux paths manifest | `figures/figure_N/.last_demux_paths.txt` (gitignored) |
| Rendered figure HTML | `figures/figure_N/figure_N_analysis.html` (gitignored) |
| Figure-5 raw data CSVs | `figures/figure_5/{heatmap,histogram,scatterplot}_raw_data/` |
