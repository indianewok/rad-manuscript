# Figure 4 — Computational Efficiency and Generalizability

Headline claim: RAD is faster and lighter than BLAZE / Flexiplex on a standard scRNA-seq dataset, scales to 117M reads on HPC, supports non-10x chemistries (Split-seq, Visium), and detects high-confidence spatial barcodes without paired short-read data.

## Panels

| Panel | What it shows |
|-------|---------------|
| 4A | Single-threaded runtime — RAD / Flexiplex / BLAZE on scMixology2 (25M reads, triplicate) |
| 4B | Single-threaded peak memory — same comparison |
| 4C | 24-core HPC runtime on 117M reads (RAD vs BLAZE) |
| 4D | Split-seq — RAD correctly recovers all three barcodes per read |
| 4E | UMI counts per cell, long-read vs short-read (MB cells, MB nuclei, MT nuclei) |
| 4F | Read counts with/without short-read whitelist (correlation) |
| 4G | Read-length distributions across modalities |
| 4H | Counts per barcode across modalities |
| 4I | Visium SpaceRanger ground-truth `in_tissue` spots |
| 4J | RAD high-confidence barcodes overlaid on Visium coordinates |
| 4K | TP / FP / TN / FN classification overlay vs SpaceRanger ground truth |

## Inputs

- **Workspace:** `figure_4_workspace.RData` — see [`../data/README.md`](../data/README.md)
- **Demultiplexed FASTQs (full pipeline)** — paths relative to `${RESULTS_BASE}` (see `config.local.sh`):
  - `scmixology2/*_scmix_timing_run_r{1,2,3}/`
  - `splitseq/*_splitseq/`
  - `sans_wl/*_nbc_{sans,wl}/`
  - `visium_data/*_pt0{72,86}_bc*/` (8 sections)
  - `sans_wl/*_la{1,2,3,1mem,3mem}_{sans,wl}/`
- **Visium H&E:** `tissue_hires_image.png` (Engblom *et al.*, section 12)

## Scripts in this directory

| File | Purpose |
|------|---------|
| `figure_4_analysis.Rmd` | Master notebook |
| `comparing_visium_data.R` | Merge RAD vs SpaceRanger spot tables, classify TP/FP/TN/FN |
| `readcountlengthviolinprep.R` | Build per-modality read-length / count tables (downsampled to 100K, seed 123) |
| `verify_fig4.R` | Sanity check: workspace + Rmd objects match expected schema |

## How to regenerate

```bash
./run_figure_4.sh analysis                # workspace-only
./run_figure_4.sh                         # everything
./run_figure_4.sh full true               # skip scmix timing runs (expensive)
./run_figure_4.sh full true true          # also skip LA benchmark runs (very expensive)
```

Output: `figure_4_analysis.html`.

## Key workspace objects

`splitseq_headers`, `splitseq_read_cts`, `splitseq_umi_cts`, `tabulated_splitseq_data`, `final_splitseq_cts`, `scmixology_all_read_lengths`, `sct12` (RAD + SpaceRanger merged Visium section 12), `spaceranger_section_12`, `rad_section_12`.
