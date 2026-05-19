# RAD Manuscript — Figure Generation Repository

Code and analysis to regenerate every figure in the RAD manuscript:

> **RAD: A Read-structure Agnostic Demultiplexer for Single-Cell Long-Read Sequencing and Analysis.**
> Chinmay M. Vaidya *et al.*, 2026. *(manuscript in preparation)*

The RAD tool itself lives at **[github.com/indianewok/rad](https://github.com/indianewok/rad)**. This repo is the analysis layer: shell harnesses that drive `rad demux` over the manuscript datasets, R Markdown notebooks that consume the demultiplexed output, and the helper scripts used to produce each panel.

---

## Repository layout

```
.
├── README.md             ← this file (setup + usage)
├── LICENSE
├── CITATION.cff
├── TODO.md               ← open items (manuscript polish, repo plumbing)
│
├── scripts/              ← shell drivers — run_all_figures.sh + run_figure_{2..5}.sh
├── figures/              ← per-figure analysis (Rmd + helpers + reference PDF/PNG)
│   ├── figure_2/         ← Figure 2: ScTagger synthetic benchmark
│   ├── figure_3/         ← Figure 3: RAGEseq real-data benchmark
│   ├── figure_4/         ← Figure 4: multi-platform efficiency
│   ├── figure_5/         ← Figure 5: isotype-resolved B-cell clonotypes
│   └── supp_figure_1/    ← Supp. Fig. 1: RAD on 10X Visium HD mouse brain
├── data/                 ← Zenodo DOI + SHA-256 checksums for the .RData workspaces
└── misc/                 ← manuscript color palette + every rad demux command
```

Each `figures/figure_N/` directory has its own `README.md` with the panel breakdown, an inline PNG render of the published figure, and a high-res PDF.

---

## Setup

### 1. External tools (pin these versions)

| Tool | Version | Source |
|------|---------|--------|
| **RAD** | commit `2a37ac9` (2026-03-13) for the published benchmark; current head `a8cea3a` for new runs | [github.com/indianewok/rad](https://github.com/indianewok/rad) — `git clone`, `cd build && cmake .. && cmake --build .` |
| **BLAZE** | `v0.10.1` (used for the published benchmark) | [pypi.org/project/blaze](https://pypi.org/project/blaze/0.10.1/) — `pip install blaze==0.10.1` |
| **Flexiplex** | `v1.02.5` | [github.com/DavidsonGroup/flexiplex](https://github.com/DavidsonGroup/flexiplex) |
| **seqkit** | `v2.8.2` | [bioinf.shenwei.me/seqkit](https://bioinf.shenwei.me/seqkit/download/) — `brew install seqkit` |
| **csvtk** | `v0.31.0` | [bioinf.shenwei.me/csvtk](https://bioinf.shenwei.me/csvtk/download/) — `brew install csvtk` |
| **pigz** | `2.8` | [zlib.net/pigz](https://zlib.net/pigz/) — `brew install pigz` |
| **minimap2** | `2.30-r1287` (Figure 5 chr14 depth only) | [github.com/lh3/minimap2](https://github.com/lh3/minimap2) — `brew install minimap2` |
| **IgBLAST** | NCBI 1.22+ (Figure 5 clonotyping only) | [ncbi.nlm.nih.gov/igblast](https://ncbi.nlm.nih.gov/igblast/) |
| **R** | `4.5.2` | [cran.r-project.org](https://cran.r-project.org/) |

### 2. R packages

Versions used for the published renders:

```r
install.packages(c(
  "data.table",  # 1.18.2.1
  "dplyr",       # 1.2.0
  "ggplot2",     # 4.0.2
  "ggpubr",      # 0.6.2
  "magrittr",    # 2.0.4
  "magick",      # 2.9.0
  "jsonlite",    # 2.0.0
  "readr",       # 2.1.6
  "pheatmap",    # 1.0.13
  "rmarkdown",   # 2.30
  "knitr",       # 1.51
  "Seurat"       # 5.4.0
))
# rad R package (Rcpp wrapper around the RAD binary):
remotes::install_github("indianewok/rad_dev")
```

### 3. Configure paths via environment variables

The figure scripts read every path from the environment — no config file to edit. Paste this block into your shell, **edit the four required paths**, then run the scripts:

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
export SWEDISH_TONSIL_DIR=/path/to/swedish_tonsil_spatial  # Engblom et al. Visium data
# Optional fallback if not set: derived from WL_DETECTION_RESULTS
# export VISIUM_WL_DIR="${WL_DETECTION_RESULTS}/120525_visium_data_results"
# export LEENA_WL_DIR="${WL_DETECTION_RESULTS}/leena_data"

# === required for Figure 5 ===
export NBC_DEPTH_DIR=/path/to/nbc_chr14_depth_csvs         # IGH locus depth CSVs

# === required for Supplementary Figure 1 (10X Visium HD mouse brain) ===
export HD_MAPPING_DIR=/path/to/visium_hd_mapping           # Seurat RDS + tissue_positions_16um.csv

# === optional ===
export BLAZE_BIN=/path/to/blaze                            # if regenerating BLAZE benchmarks
export BLAZE_RESULTS=/path/to/results/blaze                # if regenerating BLAZE comparisons
export RAD_THREADS=4                                       # default if unset
```

Scripts fail fast and tell you exactly which variable is missing — no silent guesses.

### 4. Data

The `.RData` workspaces (5.8 GB total) are on Zenodo, reserved DOI **[10.5281/zenodo.20189813](https://doi.org/10.5281/zenodo.20189813)** (private draft until manuscript acceptance). Download paths + SHA-256 checksums are in [`data/README.md`](data/README.md). Place each `figure_N_workspace.RData` inside its matching `figures/figure_N/` directory.

Raw FASTQs are not redistributed here; their accessions are documented in [`misc/rad_demux_commands.md`](misc/rad_demux_commands.md).

---

## Usage

Two modes, both invoked from the repo root after exporting the env vars above.

### Re-render only (uses cached workspaces)

```bash
./scripts/run_all_figures.sh analysis
```

Renders `figures/figure_N/figure_N_analysis.html` for every figure using the cached `.RData` workspaces. Doesn't require the raw FASTQs or `RAD_BIN`.

### Full re-run (raw FASTQs → demux → render)

```bash
./scripts/run_all_figures.sh
```

Or per-figure:

```bash
./scripts/run_figure_2.sh                # full
./scripts/run_figure_3.sh analysis       # render only
./scripts/run_figure_4.sh full true      # full, skip scmix timing runs
./scripts/run_figure_4.sh full true true # full, also skip LA benchmark runs
./scripts/run_figure_5.sh igblast        # rerun IgBLAST clonotyping then render
```

See [`scripts/README.md`](scripts/README.md) for the full per-script flag reference.

---

## Datasets used per figure

| Figure | Datasets | Reference |
|--------|----------|-----------|
| **2** | ScTagger long-read simulations (S, M, L; 100K/250K/500K downsampled) | Ebrahimi *et al.* (ScTagger) |
| **3** | RAGEseq (real BCR/TCR mix) + off-list false-positive controls | Singh *et al.* |
| **4** | scMixology2, Split-seq (LR-Splitpipe), NBC BCR, Visium spatial tonsil, LA1–LA3 | Tian *et al.*; Rosenberg *et al.*; Engblom *et al.* |
| **5** | NBC BCR + Visium spatial tonsil (downstream of Figure 4 demux) | Engblom *et al.* |

Full provenance — every `rad demux` invocation, every whitelist used — is in [`misc/rad_demux_commands.md`](misc/rad_demux_commands.md).

---

## Versioning

- **Manuscript:** v9 (pre-submission)
- **RAD binary:** see release notes at [github.com/indianewok/rad/releases](https://github.com/indianewok/rad/releases)
- **Figures:** v7

## License

MIT. See [LICENSE](LICENSE).

## Contact

Chinmay M. Vaidya — `chinmay.m.vaidya.gr@dartmouth.edu`
Geisel School of Medicine at Dartmouth
