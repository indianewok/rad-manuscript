# RAD Manuscript — Figure Generation Repository

## Current revision: HPC handoff

The 23 October 2026 revision audit and 36-task regeneration plan are in **[hpc_handoff_20261023](hpc_handoff_20261023/README.md)**. The HPC agent should begin with **[AGENT_START_HERE.md](hpc_handoff_20261023/AGENT_START_HERE.md)**. This includes source and code snapshots, checkpoint requirements, validation criteria, author decisions and recovery requests for current Figures 1–7.

The missing LR-Split-seq read comparison is now recovered: **[source tables, 568-cell mapping, run settings and validation](hpc_handoff_20261023/recovered/lr_splitseq_20261023/README.md)**.

The figure layout and run instructions below describe the older manuscript baseline. Consult the handoff before running them; the current revision has additional workflows and unresolved provenance/statistical items.

Code and analysis to regenerate every figure in the RAD manuscript:

> **RAD: A Read-structure Agnostic Demultiplexer Long-Read Sequencing.**

The RAD tool itself lives at **[github.com/indianewok/rad](https://github.com/indianewok/rad)**. This repo is the analysis layer: shell harnesses that drive `rad demux` over the manuscript datasets, R Markdown notebooks that consume the demultiplexed output, and the helper scripts used to produce each panel.

---

## Repository layout

```
.
├── README.md             ← this file (setup + usage)
├── LICENSE
├── CITATION.cff
│
├── scripts/              ← shell drivers — run_all_figures.sh + run_figure_{2..5}.sh
├── figures/              ← per-figure analysis (Rmd + helpers + reference PDF/PNG)
│   ├── figure_2/         ← Figure 2: ScTagger synthetic benchmark
│   ├── figure_3/         ← Figure 3: RAGEseq real-data benchmark
│   ├── figure_4/         ← Figure 4: multi-platform efficiency
│   └── figure_5/         ← Figure 5: isotype-resolved B-cell clonotypes
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

The figure scripts read every path from the environment — no config file to edit. See **[SETUP.md](SETUP.md)** for the full block to paste into your shell; at minimum set the four required paths (`RAD_BIN`, `RAW_FQ`, `RESULTS_BASE`, `WL_DIR`). Scripts fail fast and tell you exactly which variable is missing.

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
./scripts/run_figure_5.sh igblast        # rerun IgBLAST clonotyping then render
```

See [`scripts/README.md`](scripts/README.md) for the full per-script flag reference.

---

## Datasets used per figure

| Figure | Datasets | Reference |
|--------|----------|-----------|
| **2** | ScTagger long-read simulations (S, M, L; 100K/250K/500K downsampled) | Ebrahimi *et al.* (ScTagger) |
| **3** | RAGEseq (real BCR/TCR mix) + off-list false-positive controls | Singh *et al.* |
| **4** | scMixology2, Split-seq (C2C12, LR-Splitpipe), NBC BCR, 10X Visium HD mouse brain (panels 4I-4K, overview triptych) | Tian *et al.*; Rebboah *et al.*; 10X public dataset |
| **5** | NBC BCR + Engblom *et al.* Visium tonsil spatial (panels 5C + 5E) | Engblom *et al.* |

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
