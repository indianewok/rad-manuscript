# Installation

Setup needed to re-render the figures or to re-run the full pipeline from raw FASTQs.

---

## 1. RAD binary

Build from source — see [github.com/indianewok/rad](https://github.com/indianewok/rad) for the canonical instructions. Summary:

```bash
git clone https://github.com/indianewok/rad.git
cd rad
mkdir -p build && cd build
cmake ..
cmake --build . -j$(sysctl -n hw.ncpu 2>/dev/null || nproc)
```

This produces `build/rad` and `build/generate_whitelist`. Point the harness at them by setting `RAD_BIN` and `GEN_WL_BIN` in [`config.local.sh`](config.local.sh.example) (see step 5 below).

The pipeline was last validated against RAD release `v1.x` (see `CITATION.cff` for the exact commit).

---

## 2. R environment

R ≥ 4.3. Install CRAN dependencies:

```r
install.packages(c(
  "data.table",
  "dplyr",
  "ggplot2",
  "ggpubr",
  "magrittr",
  "magick",
  "jsonlite",
  "readr",
  "pheatmap",
  "rmarkdown",
  "knitr"
))
```

Bioconductor / GitHub:

```r
# Seurat (Figure 5 spatial)
install.packages("Seurat")

# rad R package (Rcpp wrapper for the RAD binary)
# install.packages("remotes")
remotes::install_github("indianewok/rad_dev")
```

---

## 3. Command-line tools

Used by the shell harnesses for FASTQ inspection and header extraction:

```bash
# macOS via Homebrew
brew install seqkit csvtk pigz

# Linux
conda install -c bioconda seqkit csvtk pigz
```

---

## 4. Project-specific scripts (header extraction, IG mapping)

The harnesses source helper scripts from `${PROJECT_SCRIPTS}`. If you cloned only this repo, fetch them from:

> *(TODO: link the project_specific_scripts/ repo or vendor them in here)*

In the meantime, point `PROJECT_SCRIPTS` at your local copy (step 5).

---

## 5. Configure paths for your machine

All paths the harness needs (RAD binary, raw FASTQs, results dirs, whitelists, helper scripts) live in [`config.sh`](config.sh). The shipped defaults are `/path/to/...` placeholders. Set your machine's real paths via a gitignored override file:

```bash
cp config.local.sh.example config.local.sh
$EDITOR config.local.sh           # set RAD_BIN, RAW_FQ, RESULTS_BASE, WL_DIR, …
```

`config.local.sh` is sourced before the defaults inside `config.sh`, so anything you put there wins. It's listed in `.gitignore`, so it never leaves your machine.

Smoke test:
```bash
bash -c 'source ./config.sh && check_paths && check_rad'
```

If both checks pass, you're configured. (You can also just run `./run_figure_2.sh analysis` and it'll error loudly on the first missing path.)

---

## 6. Data

The `.RData` workspaces (5.8 GB total) are hosted on Zenodo — see [`data/README.md`](data/README.md) for DOIs and SHA-256 checksums.

Raw FASTQs are not redistributed here; sources for each dataset are documented in [`rad_demux_commands.md`](rad_demux_commands.md).

---

## 7. Verifying your install

Render a single figure end-to-end (analysis only, no demux required):

```bash
./run_figure_2.sh analysis
open figure_2/figure_2_analysis.html
```

If that succeeds you have everything you need to reproduce the manuscript figures.
