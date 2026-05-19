# RAD Manuscript — Figure Generation Repository

Code and analysis to regenerate every figure in the RAD manuscript:

> **RAD: A Read-structure Agnostic Demultiplexer for Single-Cell Long-Read Sequencing and Analysis.**
> Chinmay M. Vaidya *et al.*, 2026. *(manuscript in preparation)*

The RAD tool itself lives at **[github.com/indianewok/rad](https://github.com/indianewok/rad)**. This repo is the analysis layer: shell harnesses that drive `rad demux` over the manuscript datasets, R Markdown notebooks that consume the demultiplexed output, and the helper scripts used to produce each panel.

---

## Repository layout

```
.
├── README.md                  ← this file
├── INSTALL.md                 ← dependency setup (R packages, RAD binary, seqkit)
├── LICENSE                    ← MIT
├── CITATION.cff               ← how to cite this repo
├── config.sh                  ← single source of truth for paths (edit for your machine)
├── manuscript_colors.txt      ← official manuscript color palette
├── rad_demux_commands.md      ← every rad demux command used, organized by figure
│
├── run_all_figures.sh         ← top-level driver (full pipeline or analysis only)
├── run_figure_2.sh            ← Figure 2: ScTagger synthetic benchmark
├── run_figure_3.sh            ← Figure 3: RAGEseq real-data benchmark
├── run_figure_4.sh            ← Figure 4: multi-platform efficiency + generalizability
├── run_figure_5.sh            ← Figure 5: isotype-resolved B-cell clonotypes
│
├── figure_2/                  ← analysis Rmd + helper R scripts + figure outputs
├── figure_3/
├── figure_4/
├── figure_5/
│
└── data/
    └── README.md              ← Zenodo links + checksums for the .RData workspaces
```

Each `figure_N/` directory has its own `README.md` explaining which panels it produces and which inputs it consumes.

---

## Two ways to use this repo

### 1. Re-render only (fast — uses cached workspaces)

If you just want to reproduce the plots from the cached analysis objects:

```bash
# 1. clone
git clone https://github.com/indianewok/rad-manuscript.git
cd rad-manuscript

# 2. download the .RData workspaces from Zenodo into figure_2/ ... figure_5/
#    (see data/README.md for DOIs + sha256 checksums)

# 3. render analysis-only mode (no rad demux required)
./run_all_figures.sh analysis
```

This produces `figure_N/figure_N_analysis.html` for each figure. No external SSD required.

### 2. Full re-run from raw FASTQs (full pipeline)

If you have the raw long-read FASTQs (see [`rad_demux_commands.md`](rad_demux_commands.md) for sources) and want to regenerate every intermediate:

```bash
# 1. build the RAD binary (see github.com/indianewok/rad)
# 2. edit config.sh — update RAD_BIN, RAW_FQ, WL_DIR, RESULTS_BASE
# 3. run end-to-end
./run_all_figures.sh
```

Use `./run_all_figures.sh 2 3` to run only specific figures. Use `./run_all_figures.sh analysis 4 5` to skip demux and only re-render figures 4 and 5.

---

## Datasets used per figure

| Figure | Datasets | Reference |
|--------|----------|-----------|
| **2** | ScTagger long-read simulations (S, M, L; 100K/250K/500K downsampled) | Ebrahimi *et al.* (ScTagger) |
| **3** | RAGEseq (real BCR/TCR mix) + off-list false-positive controls | this manuscript |
| **4** | scMixology2, Split-seq (LR-Splitpipe), NBC BCR, Visium spatial tonsil, LA1–LA3 | Tian *et al.*; Rosenberg *et al.*; Engblom *et al.* |
| **5** | NBC BCR + Visium spatial tonsil (downstream of Figure 4 demux) | Engblom *et al.* |

Full provenance — including every `rad demux` invocation and every whitelist used — is in [`rad_demux_commands.md`](rad_demux_commands.md).

---

## Versioning

- **Manuscript:** v9 (pre-submission)
- **RAD binary:** see release notes at [github.com/indianewok/rad/releases](https://github.com/indianewok/rad/releases)
- **Figures:** v7

---

## License

MIT. See [LICENSE](LICENSE).

## Contact

Chinmay M. Vaidya — `chinmay.m.vaidya.gr@dartmouth.edu`
Geisel School of Medicine at Dartmouth
