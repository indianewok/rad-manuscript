# Figure 4 — Computational Efficiency and Generalizability

> _Reference render (`figure_4.png` / `figure_4.pdf`) pending re-export — the prior render still showed the dropped LA panel._

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
| 4I | 10X Visium HD mouse brain — SpaceRanger `in_tissue` bin mask (PBC44593, 16 µm) |
| 4J | 10X Visium HD mouse brain — Percula/Seurat `log1p(ncpm)` (PBC44593, plasma scale) |
| 4K | 10X Visium HD mouse brain — RAD `log1p(ncpm)` (PBC44593, shared plasma scale) |

Panels 4I-4K share a single grid bounding box and color scale; they're an *overview* triptych on one representative section.

## Inputs

- **Workspace:** `figure_4_workspace.RData` (panels A–H) — see [`../../data/README.md`](../../data/README.md)
- **Demultiplexed FASTQs (full pipeline)** — paths relative to `${RESULTS_BASE}` (env var, see [`../../README.md`](../../README.md) → Setup):
  - `scmixology2/*_scmix_timing_run_r{1,2,3}/` — panels 4A/4B
  - `splitseq/*_splitseq/` — panel 4D
  - `sans_wl/*_nbc_{sans,wl}/` — panel 4F + part of 4G/4H
- **Visium HD inputs (panels 4I-4K)**:
  - `${HD_MAPPING_DIR}/tissue_positions_16um.csv` — full bin grid
  - `${HD_MAPPING_DIR}/visium_hd_mouse_brain_016um_seurat.rds` — Percula/Seurat counts (384 MB; not in repo)
  - `sample_bin_matrix_16um.csv.gz` — RAD per-sample bin counts

## Scripts in this directory

| File | Purpose |
|------|---------|
| `figure_4_analysis.Rmd` | Master notebook for panels A–H (loads `figure_4_workspace.RData`) |
| `readcountlengthviolinprep.R` | Build per-modality read-length / count tables (downsampled to 100K, seed 123) for 4G/4H |
| `overview_panels_bare.R` | Render the Visium HD triptych (panels 4I-4K + colorbars) |
| `verify_fig4.R` | Sanity check: workspace + Rmd objects match expected schema |

## How to regenerate

```bash
# Workspace-only (panels A–H render from figure_4_workspace.RData):
./scripts/run_figure_4.sh analysis

# Full pipeline (re-runs rad demux on every dataset, then renders):
./scripts/run_figure_4.sh                         # everything
./scripts/run_figure_4.sh full true               # skip scmix timing runs (expensive)
```

The Visium HD triptych (4I-4K) is generated separately — outputs are *not* committed:

```bash
export HD_MAPPING_DIR=/path/to/visium_hd_mapping
cd figures/figure_4
Rscript overview_panels_bare.R
# writes: overview_panel{1,2,3}_*_bare.png, overview_triptych_bare.png,
#         overview_colorbar_plasma{,_ncpm}.png, overview_panels_bare_color_limits.csv
```

The bare PNGs are then composited into the final figure outside the harness (PowerPoint / Illustrator / Prism). Output of the main Rmd render: `figure_4_analysis.html`.

## Key workspace objects

`splitseq_headers`, `splitseq_read_cts`, `splitseq_umi_cts`, `tabulated_splitseq_data`, `final_splitseq_cts`, `scmixology_all_read_lengths`.
