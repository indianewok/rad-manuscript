# Data — R workspaces for each figure

The four `.RData` workspace files referenced by the figure analyses are too large for GitHub (5.8 GB total). They are hosted on Zenodo with a citable DOI.

> **Zenodo record:** _(TODO: replace with DOI after upload)_
> `https://doi.org/10.5281/zenodo.XXXXXXX`

---

## What each workspace contains

| File | Size | Loaded by | Contents |
|------|------|-----------|----------|
| `figure_2_workspace.RData` | 484 MB | `figure_2/figure_2_analysis.Rmd` | RAD + BLAZE outputs on ScTagger synthetic data (S/M/L sims, downsampled subsets), precision/recall tables, edit-distance distributions, ROC/PR scores. |
| `figure_3_workspace.RData` | 2.0 GB | `figure_3/figure_3_analysis.Rmd` | RAGEseq RAD + BLAZE results, off-list false-positive runs, UMI tables, BCR/TCR mapping data, barcode entropy. |
| `figure_4_workspace.RData` | 444 MB | `figure_4/figure_4_analysis.Rmd` | scMixology2 timing, Split-seq tabulation, NBC BCR sans/with-WL, Visium 8-section data, read-length/count violins. |
| `figure_5_workspace.RData` | 2.9 GB | `figure_5/figure_5_analysis.Rmd` | NBC + Visium tonsil clonotype tables, IgBLAST output, IGH locus depth, per-clone spatial coordinates. |

Each workspace was saved with `save(list = ls(), file = ...)` from the R session that produced the published figure. Loading a workspace restores all named objects referenced in the corresponding `.Rmd`.

---

## Installation

After cloning this repo, download each `.RData` into its figure directory:

```bash
# from the repo root
ZENODO_BASE="https://zenodo.org/records/XXXXXXX/files"  # TODO: replace

curl -L -o figure_2/figure_2_workspace.RData "${ZENODO_BASE}/figure_2_workspace.RData"
curl -L -o figure_3/figure_3_workspace.RData "${ZENODO_BASE}/figure_3_workspace.RData"
curl -L -o figure_4/figure_4_workspace.RData "${ZENODO_BASE}/figure_4_workspace.RData"
curl -L -o figure_5/figure_5_workspace.RData "${ZENODO_BASE}/figure_5_workspace.RData"
```

---

## SHA-256 checksums

Verify each download:

```
3d6323869b80c12a13b78487f2e49792f7447e9ec1b7a6dcb79adab6b72dcd9d  figure_2/figure_2_workspace.RData
4c1fbcb6c086d1fa87325a8fc872b8ca2ba1bf9d65838a4caf952464b281d92c  figure_3/figure_3_workspace.RData
50e3c21008e420d79b57de59a7db49878cc0b79f95139da2d40d17a009e3d734  figure_4/figure_4_workspace.RData
07f3a581e63e16e80fae59c7371045a68725f5e90f33fd4bac881df208e1f1ae  figure_5/figure_5_workspace.RData
```

Quick check after download:

```bash
shasum -a 256 -c <<'EOF'
3d6323869b80c12a13b78487f2e49792f7447e9ec1b7a6dcb79adab6b72dcd9d  figure_2/figure_2_workspace.RData
4c1fbcb6c086d1fa87325a8fc872b8ca2ba1bf9d65838a4caf952464b281d92c  figure_3/figure_3_workspace.RData
50e3c21008e420d79b57de59a7db49878cc0b79f95139da2d40d17a009e3d734  figure_4/figure_4_workspace.RData
07f3a581e63e16e80fae59c7371045a68725f5e90f33fd4bac881df208e1f1ae  figure_5/figure_5_workspace.RData
EOF
```

---

## Raw FASTQs

This repo does **not** redistribute raw long-read FASTQs. Sources, accession numbers, and the exact `rad demux` invocation used for each dataset are catalogued in [`../rad_demux_commands.md`](../rad_demux_commands.md). For datasets generated in this manuscript, accessions will be added on acceptance.
