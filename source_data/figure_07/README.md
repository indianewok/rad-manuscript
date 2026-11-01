# Figure 7 — H146-versus-H526 expression

Follow **read assignments → genes → molecule matrices → H146/H526 nuclei → differential expression** in the [Figure 7 guide](../../docs/figure_07.md). Its [software table](../../docs/figure_07.md#software-and-commands) gives the versions and flags. [Worked examples](../../data/examples/figure_07/PREVIEW.md) show assignments, molecule counts, normalization and P values.

## Choose the panel's tables

| Analysis | Tables |
|---|---|
| Panels A–C: gene-call overlaps, volcano coordinates and confidence fits | [plotted/](plotted/), including its [graph-to-table manifest](plotted/prism_table_manifest.json) |
| Panel D: directional calling thresholds across 8,135 common genes | [threshold_grid.tsv](threshold_grid.tsv), calculated from [gene-level effects and P values](direct_H146_vs_H526_plot_data.tsv.gz) |

The **8,135-gene family** is the intersection of genes eligible in RAD, BLAZE, Flexiplex and Illumina. A gene must have at least ten molecules and be detected in at least 1% of the combined H146/H526 nuclei within each workflow. BH adjustment for panel D uses that same family in each workflow. Panels A–C use the gene coordinates and reference subsets in `plotted/`.

## Follow the common-gene analysis

| File | Rows and measurements |
|---|---|
| [native_positive_depth_cohorts.tsv](native_positive_depth_cohorts.tsv) | Tool, barcode, Vireo cell-line label and complete-library molecule total |
| [common_genes.tsv](common_genes.tsv) | The 8,135 eligible gene identifiers |
| [direct_H146_vs_H526_plot_data.tsv.gz](direct_H146_vs_H526_plot_data.tsv.gz) | Gene × long-read tool: signed effect, raw P value, common-family BH adjustment and Illumina-reference results |
| [threshold_grid.tsv](threshold_grid.tsv) | Three tools × two directions × 99 cutoffs: TP, FP, FN, precision, recall and F1 |
| [directional_membership.tsv](directional_membership.tsv) | Reference and tool call membership for each gene and expression direction |
| [venn_regions.tsv](venn_regions.tsv) | Common-family overlap counts |
| [Matrix production record](matrix_production_record.md) | Barcode assignments, gene joins and molecule counting |
| [Input manifest](RAD_emitted_segment_source_manifest.tsv) | RAD emitted-segment and read-to-gene inputs |

The H146/H526 cohorts contain **709/419 RAD**, **234/185 BLAZE**, **290/219 Flexiplex** and **263/195 Illumina** nuclei. Each nucleus is normalized to 10,000 molecules using its complete-library depth. Raw P values come from two-sided Wilcoxon rank-sum tests on `log2(1 + CP10K)`.

Hold the Illumina calls fixed at BH-adjusted P <0.05 and |log2 fold change| >1. For each long-read cutoff and direction:

- **TP:** a same-direction reference call recovered by the tool.
- **FP:** a tool call without same-direction reference support.
- **FN:** a reference call not recovered in that direction.

Precision is `TP/(TP+FP)`, recall is `TP/(TP+FN)` and F1 is `2TP/(TP+FP+FN)`. Positive fold change means higher expression in H146; negative fold change means higher expression in H526.

Reproduce the adjustment and threshold scores with the [commands in the guide](../../docs/figure_07.md#5-sweep-calling-thresholds-panel-d).
