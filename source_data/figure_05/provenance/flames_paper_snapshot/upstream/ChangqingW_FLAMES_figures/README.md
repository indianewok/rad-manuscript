# FLAMES manuscript figure repository

This repository contains the analysis pipelines and generated artifacts used for manuscript figures, built with the R `targets` workflow.

## Overview
1. Benchmarking against other single-cell workflows are under the "benchmarking" folder
2. Figures / results of running FLAMES are produced using the [targets](https://docs.ropensci.org/targets) package. Targets are defined under the targets folder.

## Targets structure
- `targets/`: target modules by dataset/domain (e.g. `visium.R`, `Curio.R`).
- `R/`: reusable helper functions.
- `output/`: generated figure and artifacts.
- `files/`: analysis config JSON files.

## Running Targets

In `R`, set the working folder to be the repo folder and:

- `tar_make([target_name])` to build specific target by name, or `tar_make()` to build everything.
- `tar_load([target_name])` to load a built target.
 
## Target figures
Table of figures produced with targets:

| Manuscript figure/panel | Module | Target(s) | Output artifact(s) | 
|---|---|---|---|
| Supplementary S10 | `targets/visualisations.R` | `sc_mean_coverage_pdf`; `sc_removed_trs_coverage_pdf`; `demultiplex_read_counts_pdf`; `demultiplex_cutadapt_pdf` | `output/sc_mean_coverage.pdf`; `output/sc_removed_trs_coverage.pdf`; `output/demultiplex_read_counts.pdf`; `output/demultiplex_cutadapt.pdf` | 
| Visium expression/spatial plots (Fig2 H,J,K) | `targets/visium.R` | `visium_cluster_pdf`; `visium_expr_pdf`; `visium_expr_Gad1_pdf`; `visium_heatmap_Plp1_pdf`; `visium_heatmap_Gad1_pdf`; `nnSVG_visium` | `output/visium_cluster.pdf`; `output/visium_expr.pdf`; `output/visium_expr_Gad1.pdf`; `output/visium_heatmap_Plp1.pdf`; `output/visium_heatmap_Gad1.pdf`; `output/visium_gene_correlation.pdf` | 
| LR-Split-seq re-run UMAP and QC (Fig2 G,I S6, S7) | `targets/LR-split-seq.R` | `LR_split_seq_barcode_knee_plot_pdf`; `LR_split_seq_clusters_umap_pdf`; `LR_split_seq_previous_clusters_umap_pdf`; `LR_split_seq_n_clusters_umap_pdf` | `output/LR-Split-seq-barcode_knee_plot.pdf`; `output/LR_split_seq_clusters_umap.pdf`; `output/LR_split_seq_previous_clusters_umap.pdf`; `output/LR_split_seq_n_clusters_umap.pdf` | 
| Bulk vs pseudobulk benchmarking with FLAMES (S10) | `targets/bench_quantification.R` | `bulk_vs_sc_r2_boxplot_pdf`; `bulk_vs_sc_r2_boxplot_longbench_pdf` | `output/FLAMES_bulk_vs_pseudobulk_r2_boxplot.pdf`; `output/LongBench_bulk_vs_pseudobulk_r2_boxplot.pdf` | 
| Curio re-run (Fig2L, S9) | `targets/Curio.R` | `curio_gene_correlation`; `curio_bin_libsize_plot` | `output/curio_gene_corr_plot.pdf`; `output/curio_bin_libsize_plot.pdf` |
