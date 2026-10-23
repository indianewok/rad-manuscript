# Combined H146/H526 F1 threshold sweeps

This package contains two one-versus-all low/high figures and one direct H146-versus-H526 high-direction figure. Rows are RAD, BLAZE, and Flexiplex; columns are the two directions shown in each figure.

## Figures

1. `01_H146_low_high_combined_3tools_F1_threshold_sweep.*`
   - H146 versus the pooled other seven cell lines.
   - Left: H146-low; right: H146-high.
   - Reversed viridis C (plasma) palette.
2. `02_H526_low_high_combined_3tools_F1_threshold_sweep.*`
   - H526 versus the pooled other seven cell lines.
   - Left: H526-low; right: H526-high.
   - Reversed viridis D palette.
3. `03_H526_high_H146_high_direct_side_by_side_3tools_F1_threshold_sweep.*`
   - Direct H146-versus-H526 differential-expression test, not one-versus-all.
   - Left: H526-high (negative direct log2FC); right: H146-high (positive direct log2FC).
   - H526 uses reversed viridis D; H146 uses reversed viridis C.

Every low or H526-high left panel displays signed negative cutoffs from `-3.00` to `-0.10`, so the horizontal layout reads like the negative half of a volcano plot. Every high right panel displays positive cutoffs from `0.10` to `3.00`. This is an axis/label transformation only for figures 1 and 2: their 1,188 one-versus-all F1 values are byte-identical to the validated source grid.

All color scales span F1 from 0 to 1. The solid black outline marks the reference threshold (BH FDR `0.05`, absolute log2FC `1.00`); the dashed teal outline marks the best cell in the grid when it differs from the reference.

## Truth definitions

The one-versus-all fixed Illumina truth sets are:

| Contrast | Direction | Truth genes |
|---|---|---:|
| H146 vs all | Low | 535 |
| H146 vs all | High | 205 |
| H526 vs all | Low | 353 |
| H526 vs all | High | 186 |

The direct H146-versus-H526 fixed Illumina truth sets are:

| Direct direction | Predicate | Truth genes |
|---|---|---:|
| H526-high | BH FDR `< 0.05` and direct log2FC `< -1` | 769 |
| H146-high | BH FDR `< 0.05` and direct log2FC `> 1` | 412 |

The one-versus-all universe has 12,206 common genes per contrast. The direct comparison has 8,135 genes shared across Illumina and all three tools. All panels use nine tool-FDR cutoffs (`1e-8` through `0.10`) and eleven absolute tool-log2FC cutoffs (`0.10` through `3.00`).

## Reproducibility

- `inputs/directional_F1_threshold_sweep_grid.tsv` is the unchanged validated one-versus-all grid.
- `inputs/direct_H146_vs_H526_plot_data.tsv.gz` is the current RAD `4acbe00` direct plot-23 gene table.
- `inputs/direct_H146_H526_F1_threshold_sweep_grid.tsv` contains all 594 recomputed direct grid cells; companion reference, best-threshold, and parameter tables are included.
- `SOURCE_INPUT_SHA256.tsv` links all 13 packaged source inputs to canonical origins.
- `PANEL_LAYOUT.tsv` records every figure, row, column, contrast, direction, palette, and axis orientation.
- `scripts/generate_combined_figures.R` regenerates all figures and direct tables.
- `scripts/validate_combined_figures.py` independently validates the statistics, layout, annotations, provenance, and image structure.
