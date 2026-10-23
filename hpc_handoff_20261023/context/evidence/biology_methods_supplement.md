# Biology Methods evidence supplement, 22 October 2026

Read-only audit after permission to inspect referenced folders on `/Volumes/rad_data`. No sequence-data pipeline was rerun. The table comparisons below use retained result tables. This supplements `biology_methods.md`.

## Figure 7D is the updated analysis; Figure 7A is the older analysis

All **594 displayed numerical heatmap labels** in Figure 7D match the current direct H146-versus-H526 F1 grid, to the displayed precision of one significant digit. Decimal half-up rounding is needed at seven exact rounding ties (0.25 and 0.075). Panel order is H146-high RAD, Flexiplex, BLAZE, then H526-high RAD, Flexiplex, BLAZE. The check is retained in `figure7D_current_heatmap_match.tsv` alongside this report. This is an exact match to the numerical labels, not proof that the same graphic export was inserted.

Authoritative source:

`/Volumes/rad_data/reviewer_comment_data/082426_volcano_plots/SN_ONT_H146_H526_vs_all_combined_F1_sweeps_20260831/inputs/direct_H146_H526_F1_threshold_sweep_grid.tsv`

Its README lines 35–48 specifies 8,135 common genes, a fixed Illumina reference of 412 H146-high genes and 769 H526-high genes, and current RAD commit `4acbe00`. The source input is `inputs/direct_H146_vs_H526_plot_data.tsv.gz`. The original table is the current plot-23 table in `Illumina_tool_confidence_19plots_20260825`.

The expanded grid uses FDR cutoffs 1e-8, 1e-6, 1e-5, 1e-4, 1e-3, 0.005, 0.01, 0.05, and 0.1, and absolute log2 fold-change cutoffs 0.10, 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00, 2.50, and 3.00. Both are strict inequalities. The reference remains fixed at Illumina BH FDR < 0.05 and absolute log2 fold change > 1 in the corresponding direction. Precision = TP/(TP+FP), recall = TP/(TP+FN), and F1 = 2TP/(2TP+FP+FN); a zero denominator gives zero. See `Illumina_tool_confidence_19plots_20260825/generate_plot24_expanded_threshold_sweep.R:25–30,71–94`, and the combined package's `scripts/generate_combined_figures.R` for the two-direction implementation.

In contrast, Figure 7A's seven Venn-region numbers exactly match the **older** 8,126-common-gene, 1,179-Illumina-reference-gene result in `direct_H146_vs_H526_Illumina_threshold_FDR005_absFCgt1_20260825/direct_H146_vs_H526_FDR005_absFCgt1_Illumina_set_comparison.tsv`: RAD-only 126, BLAZE-only 26, Flexiplex-only 24, RAD/BLAZE 32, RAD/Flexiplex 67, BLAZE/Flexiplex 20, all 443. These are same-direction Illumina-supported recoveries, not all tool DEGs. RAD total 668, BLAZE 521, Flexiplex 554. The updated equivalent has RAD 654, BLAZE 522, Flexiplex 556, with regions 117,29,26,29,66,22,442 respectively.

### Reason for the changed analysis

`/Volumes/rad_data/reviewer_comment_data/LongBench_comps/SN_ONT_H146_H526_fullcohort_DEG_20260822/provenance/RAD_4acbe00_full_rebuild_20260828/README.md:3–18` records a full RAD count-matrix rebuild from all serialized records of commit `4acbe004ba11b150d6832395452632f367a6e6c1`, including `-CT` records. The frozen parent-read gene assignment table and exact (cell barcode, gene, UMI) collapse were reused. Total UMIs rose from 21,013,660 to 22,875,174 (+1,861,514). The `-CT` segments inherit the original physical read's one gene assignment. They were retained for parity with Flexiplex, which already included deconcatenated/multi-target rows. Lines20–21 warn that existing DEG tables and figures were stale at matrix promotion. Later direct/plot-23/F1 packages were refreshed.

The gene-list changes therefore arise from changed RAD counts, gene eligibility and statistics, and BH adjustment over a changed common-gene universe. They do not represent a new biological gene annotation. The exact old whole 8,126-gene ID list has not been located. The old script derives it from the old native direct table plus Illumina eligibility, but the canonical native table has since been overwritten by the updated file. Old DEG/reference subsets remain available in the old threshold and ranking tables.

## Figure 7C: strong older-analysis match, one residual slope discrepancy

The older table

`/Volumes/rad_data/reviewer_comment_data/082426_volcano_plots/direct_H146_vs_H526_Illumina_truth_rank_vs_all_tools_confidence_bars_20260825/direct_H146_vs_H526_Illumina_truth_rank_vs_all_tools_confidence_bars.tsv`

contains all three tools' statistics for 412 H146-high and 767 H526-high Illumina reference DEGs. Ordinary least-squares fits of tool -log10(BH FDR) on BLAZE -log10(BH FDR), with an estimated intercept and no clipping, give:

| Direction | Tool | Slope | Figure 7C slope |
|---|---|---:|---:|
| H146-high | RAD |2.2449310096|2.25|
| H146-high | Flexiplex |1.2168096459|1.22|
| H526-high | RAD |2.4927907973|2.49|
| H526-high | Flexiplex |1.1835179016|1.18|

The older source reproduces three labels at two decimals and nearly reproduces the fourth. The updated source gives RAD slopes 2.2589 (H146-high) and 2.4543 (H526-high), which do not match the figure's 2.25/2.49. Thus C appears to retain old RAD statistics, but the exact source/filter/fit for the 2.25 label needs the author or plotting workbook. No decision about statistical testing or regression inference has been made. These calculated slopes are provenance diagnostics, not a replacement analysis.

The source SVGs 08/09/12/13 in `Illumina_tool_confidence_19plots_20260825` report Spearman correlations and do not establish the regression used for Figure 7C. The display range 0–20 should not be assumed to be a fitting filter.

## Figure 6 UMAP: external script recovered, final normalization remains uncertain

The referenced external script exists:

`/Volumes/rad_data/LongBench_Illumina_SC_SN_Seurat_UMAP_20260805/scripts/build_longbench_illumina_seurat_umap.R`

It specifies the public LongBench Cell Ranger 8.0.1 filtered Illumina matrices, 62,700 features and 12,012 SN barcodes, with all barcodes retained (`ReadMtx`, feature column2; `CreateSeuratObject(min.cells=0,min.features=0)`; lines117–142). It then uses:

- LogNormalize, scale factor 10,000; VST selection of 3,000 variable features (lines163–167).
- Scaling of variable features and 50 PCA components (lines170–172).
- Neighbor graph from PCs 1–30; Louvain clustering, resolution 0.5, algorithm 1 (lines176–178).
- UMAP on PCs 1–30, 30 neighbors, minimum distance 0.3, cosine distance, one thread (lines179–189).
- Seed 20260805 (line 26).

The script attaches Vireo and merged annotation metadata; these labels are not inputs to the embedding. Its text describes a locally computed embedding, not a published UMAP.

However, the current `objects` directory contains only `LongBench_Illumina_SC_SCT_Seurat_UMAP.rds` and `LongBench_Illumina_SN_SCT_Seurat_UMAP.rds`. Their names conflict with this LogNormalize builder, which writes `_Seurat_UMAP.rds` without `_SCT_`. The expression-rescue workflow references the SCT-named SN object. No SCT builder/log was found in the scoped stored manifests. The 2.06 GB SN object was not loaded. **Do not state LogNormalize as the final Figure 6 method until the figure's source object is identified or its stored command history is inspected.** The source script supports a candidate workflow, not a confirmed final embedding.

### Conditional UMAP prose, only after confirming that this script produced Figure 6

The published LongBench Illumina count matrix was imported into Seurat. All 12,012 barcodes in the filtered single-nucleus matrix were retained. Counts were normalized to 10,000 per cell and log-transformed. The 3,000 most variable genes were selected with the variance-stabilizing transformation method. These genes were scaled and used to calculate 50 principal components. A neighbor graph was constructed from the first 30 components. Louvain clustering used resolution 0.5. UMAP used the same30components, 30 neighbors, minimum distance 0.3 and cosine distance. The random seed was 20260805. Cell-line labels from Vireo were joined by barcode and displayed on the fixed embedding.

## Figure 5G–H: comparator configuration gap remains

The retained historical FLAMES paper workflow is:

`/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_full_demux_20260730/tools/FLAMES_figures_paperstate/targets/LR-split-seq.R`

It uses PacBio SRR13948564, FLAMES/Flexiplex, and a 10 nt UMI plus one contiguous barcode pattern containing three 8 nt barcodes and both linkers, followed by 8 T. Its first pass identifies barcodes; only exact flank matches with at least 100 distinct UMIs are retained (lines85–141). The second pass uses the selected whitelist and maximum barcode edit distance 6 (lines144–177). This is the **historical two-pass configuration**. The rebuttal explicitly states that its final LR-Split-seq comparison uses component-based FLAMESV2/Flexiplex with poly-T and excludes this historical method and MATCHED_SPLIT. Therefore these settings must not be substituted into the final Methods.

The external `/Volumes/rad_data/20250514_splitseq_out` holds output CSV/FASTQ, layout, whitelist, signature and position-map files, but no final comparator script. The old `/Volumes/rad_data/old/run_progress_nohups/splitseq_nohup.out` is an earlier December 2024 RAD run and is not provenance for the new comparison. The final component-based command/version, per-component correction limits, whitelist origin and successful run log remain unfound.

The preserved Prism input `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/prism_inventory_source.Pn5f14/SPLIT-seq benchmarking.csv` has 568 rows and six unlabeled numeric columns. Columns 1 and 3 sum exactly to the rebuttal's **2,078,171 RAD and 1,156,252 FLAMESV2 reads** in 568 published cells. This establishes the source of the rebuttal read-count summary, but not the final component settings. Column medians should be calculated by averaging the two middle values (not choosing only the upper middle value). No header identifying all six columns was retained.

These read counts are distinct from Figure 5H's UMI counts. The final Figure 5G 43.34%/23.35% assigned fractions have not been matched to exact total-assignment output. With total 5,764,421 reads, percentages alone only bound their numerators and cannot identify unique integer counts. The general dataset and matched short-read reconstruction Methods in the first report remain supported; the final comparator and final H UMI-collapse/source-table link need author confirmation.

## Ready-to-integrate updated Figure 7D Methods prose

For the H146-versus-H526 comparison, the evaluation was restricted to 8,135 genes that met the expression criteria in the Illumina data and in all three long-read analyses. Benjamini–Hochberg correction was applied separately to each analysis over this common gene set. The fixed Illumina reference comprised genes with FDR < 0.05 and absolute log2 fold change > 1. H146-high and H526-high genes were evaluated separately. A long-read result was counted as a true positive only when it met the selected FDR and fold-change thresholds in the same direction as the Illumina reference. Precision, recall and F1 were calculated at each combination of nine FDR thresholds (10⁻⁸, 10⁻⁶, 10⁻⁵, 10⁻⁴, 10⁻³, 0.005, 0.01, 0.05 and 0.1) and 11 absolute log2 fold-change thresholds (0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5 and 3). The inequalities were strict. F1 was calculated as 2TP/(2TP+FP+FN). The Illumina reference was held fixed across the threshold grid.

Before final manuscript delivery, Figure 7A/C must be reconciled with updated Figure 7D. A Methods paragraph must not silently combine the old and updated statistical universes as if all panels used one analysis.
