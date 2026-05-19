# Supplementary Figure 4 — caption and paragraph numbers

## Figure caption (draft)

**Supplementary Figure 4. RAD recovers nearly all Percula-called in-tissue bins and shows tight cross-sample reproducibility on a public 10X Visium HD murine brain dataset.**
(**A**) Spatial maps of log1p(ncpm) per 16 μm bin for bins called valid by RAD (double-positive plus single-positive RAD) across the four replicate sections. Shared plasma color scale; bins not called by RAD are not drawn.
(**B**) Per-sample distributions of log1p(ncpm) for each bin class: Both (double-positive, called by RAD and Percula), RAD only (single-positive RAD), Seurat only (called by Percula but missed by RAD), and Neither. Dots are a 1,500-bin quasi-random subsample per class; black bars show median and IQR; counts above each violin give the bin total per class.
(**C**) Spatial maps of the single-positive RAD bins per sample, on a plasma color scale shared across panels; grey background bins show all bins on the array for context. Counts in each title give the per-sample n.
(**D**) Cross-sample Pearson correlation of RAD log1p(ncpm) computed across in-tissue bins. All twelve off-diagonal pairs fall in the 0.988–0.990 range.
(**E**) Pooled three-group comparison of log1p(ncpm) for double-positive bins valued by Percula (TP Seurat), the same double-positive bins valued by RAD (TP RAD), and single-positive RAD bins. Dots are a 1,500-bin quasi-random subsample per group; black bars show median and IQR.

---

## Paragraph with numbers from the data (suggested edits in **bold**)

To establish RAD's performance on a state-of-the-art short-read spatial transcriptomic platform, we applied RAD to a publicly available 10X Visium HD dataset of murine brain parenchyma²². Using SpaceRanger's `in_tissue` annotation as a reference (Figure 4I), we compared per-bin log-normalized counts produced by a standard mapping workflow (Figure 4J) to those recovered by RAD during whitelist detection (Figure 4K). RAD called **120,791–121,968** valid 16 μm bins per sample (**mean 121,464**), of which **101,981–102,092** (**~102,000**, double-positive bins) were also called by Percula²³, the standard workflow for long-read Visium HD sequencing processing. This corresponds to recovery of **99.88–99.99 % (mean 99.94 %)** of Percula-called bins per sample, with **no more than 124 bins** missed by RAD in any sample. The remaining **18,810–19,876** bins called only by RAD (single-positive RAD bins) had log-normalized counts within the distribution of double-positive bins, with **99.2–99.5 % (pooled 99.55 %)** of single-positive RAD values falling inside the data range of double-positive values. Across the four replicates, RAD log-normalized counts showed a Pearson correlation of **0.988–0.990 (mean 0.989)** (Supplementary Figure 4D), supporting that single-positive RAD bins are reproducible over multiple samples.

> **Note**: the original paragraph references "Supplementary Figure 2" for the cross-sample Pearson correlation. The actual heatmap lives in **Supplementary Figure 4, Panel D** of this package — update if Supp Fig 2 was a placeholder.

---

## Key numbers (also in `raw_data/supp_fig4_paragraph_stats.csv`)

| Metric | Value |
| ------ | ----- |
| n samples | 4 |
| Total valid RAD bins per sample (Both + RAD only) | **120,791–121,968** (mean 121,464) |
| Double-positive bins (Both) per sample | **101,981–102,092** (mean 102,047) |
| Single-positive RAD bins per sample | **18,810–19,876** (mean 19,417) |
| Missed by RAD (Seurat only) per sample | **13–124** (mean 58, max 124) |
| Recovery % of Percula bins (Both / total Percula) | **99.88 %–99.99 %** (mean 99.94 %) |
| Single-positive RAD inside double-positive range, per sample | **99.21 %–99.54 %** (mean 99.36 %) |
| Single-positive RAD inside double-positive range, pooled (n=77,669) | **99.55 %** |
| Off-diagonal cross-sample Pearson r (n=12 pairs) | **0.9882–0.9896** (mean 0.9888, median 0.9888) |

Total `in_tissue` bins per Percula = **102,105** (constant across samples, single Percula reference). Per-sample Both + Seurat-only = 102,105 in all four samples.
