# Figure 7 source data

The Figure 7 guide follows read assignments through molecule counting and differential expression in H146 and H526 nuclei. [Methods](../../docs/figure_07.md), [software and commands](../../docs/figure_07.md#software-and-commands), [worked examples](../../data/examples/figure_07/PREVIEW.md).

## Choose the panel's tables

| Panels | Tables |
|---|---|
| A–C | [Venn counts, volcano coordinates and confidence fits](plotted/), [Prism table and graph mapping](plotted/prism_table_manifest.json) |
| D | [Threshold grid](threshold_grid.tsv), [gene-level effects and P values](direct_H146_vs_H526_plot_data.tsv.gz) |

## Follow the common-gene analysis

| Inputs | Contents |
|---|---|
| [Cell cohorts](native_positive_depth_cohorts.tsv) | Tool, barcode, Vireo label and complete-library molecule count for each H146 or H526 nucleus with positive expression depth |
| [Common genes](common_genes.tsv) | The 8,135 genes that met the eligibility rules in RAD, BLAZE, Flexiplex and Illumina |
| [Gene-level tests](direct_H146_vs_H526_plot_data.tsv.gz) | Signed effect, raw P value and common-family BH adjustment for each tool and the Illumina reference |
| [Threshold grid](threshold_grid.tsv) | Per-direction call counts, precision, recall and F1 across 99 cutoff pairs for each long-read workflow |
| [Matrix construction](matrix_production_record.md), [input identities](RAD_emitted_segment_source_manifest.tsv) | Barcode and gene assignments used for molecule counting |

Panel D holds the Illumina calls fixed while changing the long-read significance and effect-size thresholds. [Scoring rules and commands](../../docs/figure_07.md#5-sweep-calling-thresholds-panel-d).
