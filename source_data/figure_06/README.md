# Figure 6 source data

The Figure 6 guide describes how demultiplexed reads were aligned, genotyped and compared with Illumina. [Methods](../../docs/figure_06.md), [software and commands](../../docs/figure_06.md#software-and-commands), [worked examples](../../data/examples/figure_06/PREVIEW.md).

## Find the plotted data

| Table | Contents |
|---|---|
| [Genotypes by barcode](per_cell_genotype.tsv) | Illumina genotype and long-read selection, genotype and recovery outcome for each tool |
| [Genotype summary](genotype_summary.tsv) | Outcome counts, strict identity recall and conditional concordance by tool |
| [Illumina UMAP coordinates](fixed_coordinates.tsv), [genotype overlays](genotype_overlay.tsv) | Shared coordinates for all 12,012 filtered Illumina barcodes and the outcomes joined to them |
| [Panel C counts](plotted_panel_c_counts.tsv), [genotype calls](plotted_genotype_calls.tsv.gz) | Counts of selected named singlets among Illumina-reference barcodes and the underlying calls |
| [Panel C statistics](plotted_panel_c_statistics.json) | One-way repeated-measures ANOVA, Geisser–Greenhouse correction and Dunnett comparisons against RAD |

The complete genotype table includes selected barcodes outside the Illumina reference. Figure 7 selects H146 and H526 singlets with positive expression depth from this broader population. [Complete genotype table](union_per_cell_genotype.tsv), [all-selected counts](selected_nuclei_by_donor.tsv).

## Follow the processing inputs

| Files | Purpose |
|---|---|
| [Demultiplexing commands](provenance/), [pinned FLAMES configurations](../../docs/pinned_flames_configs.md) | Barcode assignment and genome alignment |
| [CellSNP-lite commands](executed_cellsnp_commands.tsv), [Vireo commands](executed_vireo_commands.tsv) | Allele counting and genotype assignment |
| [Bulk-panel settings](bulk_panel_runtime_manifest.tsv), [Illumina comparison](donor_panel_validation.tsv) | Reference genotypes for all eight cell lines |
| [Matrix summary](cellsnp_matrix_summary.tsv) | Variant and barcode dimensions of the AD and DP matrices |

Restore the VCF and allele matrices under `checkpoints/figure_06/`. To reproduce the counts in panel C:

```bash
python3 scripts/figure_06/reproduce_panel_c_counts.py
```
