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

This produces `build/rad` and `build/generate_whitelist`. Either symlink them onto your `PATH` or set `RAD_BIN=/path/to/rad` in [`config.sh`](config.sh).

The pipeline was last validated against RAD release `v1.x` (see CITATION.cff for the exact commit).

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

The harnesses source helper scripts from `project_specific_scripts/`. If you cloned only this repo, fetch them from:

> *(TODO: link the project_specific_scripts/ repo or vendor them in here)*

In the meantime, edit `config.sh` and set `PROJECT_SCRIPTS=/path/to/your/copy`.

---

## 5. Data

The `.RData` workspaces (5.8 GB total) are hosted on Zenodo — see [`data/README.md`](data/README.md) for DOIs and SHA-256 checksums.

Raw FASTQs are not redistributed here; sources for each dataset are documented in [`rad_demux_commands.md`](rad_demux_commands.md).

---

## 6. Verifying your install

Render a single figure end-to-end (analysis only, no demux required):

```bash
./run_figure_2.sh analysis
open figure_2/figure_2_analysis.html
```

If that succeeds you have everything you need to reproduce the manuscript figures.
