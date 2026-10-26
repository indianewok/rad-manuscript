# Reproducibility checks for Figures 5–7

These checks connect retained assignments, matrices and test results to the deposited source tables. They recalculate cell counts, genotype outcomes, Benjamini–Hochberg adjustments, directional expression calls and threshold metrics. The [Figure 5](../docs/figure_05.md), [Figure 6](../docs/figure_06.md) and [Figure 7](../docs/figure_07.md) guides give the analysis methods and reproduction commands.

## Figure 5: LR-Split-seq

The complete assignment ledgers reproduce all 2,272 read/UMI counts for 568 physical cells. RAD/component-polyT read–cell totals are 2,078,171/1,156,252, with medians of 1,979.5/1,102.5. Exact cell–UMI totals are 1,891,704/1,050,292, with medians of 1,866/1,042. The [Figure 5 validation](figure_05_handback.md) records source hashes, pairing, normalization and the saved two-sided paired t-test.

## Figure 6: genotype assignments and fixed embedding

The Illumina reference contains 12,012 nuclei: 5,782 named singlets, 59 doublets and 6,171 unassigned nuclei. Every reference barcode is retained in the outcome table. The selected BLAZE source uses the same genotype panel as the other workflows.

| Tool | Same cell line | Different cell line | Doublet | Unassigned | Not selected |
|---|---:|---:|---:|---:|---:|
| RAD | 5,324 | 32 | 246 | 165 | 15 |
| BLAZE | 4,450 | 12 | 766 | 308 | 246 |
| Flexiplex | 4,674 | 17 | 725 | 340 | 26 |

Strict recall divides matching calls by all 5,782 reference named singlets. Conditional concordance divides them by matching plus different named calls. Panel C uses all selected named genotypes, including barcodes outside the reference.

The fixed coordinates match the saved 12,012-barcode Seurat object within 1e-12. Stored commands specify SCTransform v2 with glmGamPoi, 50 principal components, neighbors on PCs 1–30, Louvain resolution 0.5 and UMAP on PCs 1–30 with 30 neighbors, minimum distance 0.3, cosine distance, seed 20260805 and one thread. The [object commands](../source_data/figure_06/umap_object_commands.txt) retain the recipe.

BAM program headers identify minimap2 2.28-r1209 through FLAMES 2.0.1 and samtools 1.21, using splice alignment, secondary alignments disabled, seed 2023, an annotation junction BED and junction bonus 1. Figure 6 uses RAD `920adda`; Figure 7 uses RAD `4acbe00` with common raw-read gene assignments. [BAM checks](figures_567_bam_checks.tsv) cover compressed-byte hashes, file boundaries, indexes and headers.

The donor VCF contains 360,814 records and 360,809 unique variant keys. Five record pairs are identical duplicates. RAD and Flexiplex CellSNP matrices each retain two chr4:74446969 A/G rows. The [duplicate ledger](../source_data/figure_06/donor_panel_duplicate_records.tsv) preserves original record ordinals, and the [checkpoint checks](figures_567_checkpoint_checks.tsv) verify matrix row order, alleles and dimensions.

## Figure 7: common genes and expression recovery

The gene-level table contains 24,405 rows: 8,135 genes for each of three long-read workflows. Illumina values match across the three copies. Benjamini–Hochberg adjustment is independently recomputed from the retained direct Wilcoxon P values for each workflow and the reference, with a numerical tolerance of 1e-12.

Same-direction reference-supported recoveries total 654 for RAD, 522 for BLAZE and 556 for Flexiplex. The seven exclusive intersection counts are:

| Region | Genes |
|---|---:|
| RAD only | 117 |
| BLAZE only | 29 |
| Flexiplex only | 26 |
| RAD and BLAZE | 29 |
| RAD and Flexiplex | 66 |
| BLAZE and Flexiplex | 22 |
| All three | 442 |

All 594 directional threshold combinations use strict inequalities and fixed Illumina reference calls: 412 H146-high and 769 H526-high genes. TP, FP, FN and TN are recalculated for every combination, and F1 is zero for a zero denominator. Display labels match decimal half-up rounding to one significant digit.

The retained confidence-fit calculation uses uncapped confidence and OLS with an estimated intercept over directional Illumina-reference genes:

| Direction | RAD slope | Flexiplex slope | Genes |
|---|---:|---:|---:|
| H146-high | 2.258913 | 1.216813 | 412 |
| H526-high | 2.454322 | 1.183511 | 769 |

The selected RAD matrix includes emitted concatemer segments and contains 22,875,174 molecules. Native matrices, feature and barcode identities, integer counts and positive-depth genotype cohorts pass the [checkpoint checks](figures_567_checkpoint_checks.tsv). Gene eligibility uses at least ten molecules and detection in at least 1% of each two-line cohort; normalization uses complete-library totals before filtering.

The full RAD assignment checkpoint contains 57,885,606 five-field rows and all 12,423 selected barcodes. Its [validation report](figures_567_assignment_recovery.json) verifies the recorded compressed-file hash, gzip integrity, schema, exact/corrected flags and barcode membership. The [access manifest](../manifests/figures_567_assignment_access.tsv) locates the 2.36 GB file. Assignment records contain original-read ID, cell barcode, UMI, raw barcode and correction flag, with orientation and concatemer suffixes normalized by the extractor.

## Validation records

| Record | Contents |
|---|---|
| [Source-table checks](figures_567_checks.tsv) | Numerical consistency checks for the rebuilt tables |
| [Checkpoint checks](figures_567_checkpoint_checks.tsv) | Native matrices, donor panel and CellSNP content |
| [BAM checks](figures_567_bam_checks.tsv) | Compressed-byte hashes, file boundaries, indexes and headers |
| [Input manifest](../manifests/figures_567_assets.tsv) | Retained input hashes and analysis roles |
| [Build record](../manifests/figures_567_run.json) | Code hash, command and output hashes |
| [Render record](figures_567_clean_render_location.json) | Source-table rendering in a minimal environment |
| [Hash guard](figures_567_mutation_guard.json) | Rejection of a changed source table and acceptance after restoration |

The figure guides identify additional records needed for reconstruction: the Figure 5 receptor source mapping and short-read depth-matching rule, Figure 6's executed ANOVA settings, and Figure 7's emitted FASTQ, frozen read-to-gene table and saved regression specification.
