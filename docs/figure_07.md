# Figure 7 — H146-versus-H526 differential expression

Figure 7 compares long-read differential-expression signals with paired Illumina data in the LongBench single-nucleus ONT library. Cell-line labels come from the Vireo analysis in [Figure 6](figure_06.md).

[Source tables](../source_data/figure_07/) · [Read-to-molecule examples](../data/examples/figure_07/PREVIEW.md) · [Figure legend](current_figure_legends.md#figure-7)

![Figure 7](../figures/figure_07/prism/figure_07.png)

| Panels | Genes and measurements |
|---|---|
| A–C | Panel-specific gene sets: Venn overlaps, volcano coordinates and confidence fits from the [plotted tables](../source_data/figure_07/plotted/) |
| D | Directional precision, recall and F1 across **8,135 genes eligible in RAD, BLAZE, Flexiplex and Illumina**, with BH adjustment over that common family |

## Software and commands

| Stage | Software and parameters | Command or source |
|---|---|---|
| RAD assignments | RAD 1.0.2, commit `4acbe004ba11b150d6832395452632f367a6e6c1`; 10x 3v3.1 layout, offensive correction, generated and whitelist edit distances two, minimum read length 85, chunk size 5,000, 60 RAD and four pigz threads; all emitted records retained | [Metadata](../source_data/figure_07/provenance/RAD_run_metadata.txt), [command](../source_data/figure_07/provenance/RAD_demux_command.txt) |
| BLAZE assignments | BLAZE 2.5.0; `--force-cells 10000 --threads 48 --minimal_stdout`, 3v3 default | [Producing run](../source_data/figure_06/provenance/BLAZE_run_metadata.txt), [extraction command](../source_data/figure_07/provenance/extract_BLAZE_command.txt) |
| Flexiplex assignments | Flexiplex 1.02.6; `-d 10x3v3 -f 8 -e 2 -k SELECTED -p 16`; assignments read from the diagnostic sidecar containing `RawCellBarcode` | [Producing run](../source_data/figure_07/provenance/Flexiplex_run_metadata.txt), [extraction command](../source_data/figure_07/provenance/extract_Flexiplex_command.txt) |
| Common raw-read alignment | minimap2 2.30-r1287, samtools 1.22.1; `-ax splice --secondary=no --MD -Y`; GENCODE v44 splice index; wrapper defaults of 48 alignment threads and eight sort threads | [Alignment wrapper](../source_data/figure_07/provenance/align_common_raw.sh) |
| Differential expression | R 4.5.3, [scran](https://doi.org/10.12688/f1000research.9501.2) 1.34.0, scuttle 1.16.0; two-sided `pairwiseWilcox`, serial execution; native-script seed 20260825 | [Direct-test producer](../source_data/figure_07/provenance/direct_native_DE_producer.R), [common-gene producer](../source_data/figure_07/provenance/common_gene_DE_producer.R), [session information](../source_data/figure_07/provenance/DE_sessionInfo.txt) |


## 1. Join barcode assignments to genes

The [assignment extractor](../source_data/figure_07/provenance/extract_assignments.py) links each tool's cell-barcode and UMI assignments to original read IDs. A common raw-read alignment supplies the gene assignment for all three tools. The aligner searches both transcript-strand orientations. The [gene-assignment script](../source_data/figure_07/provenance/assign_genes.py) uses primary alignments with MAPQ at least one, sums unstranded overlap with annotated exons, and chooses the gene with the largest overlap. Reads without exon overlap or with tied best genes are excluded.

Each emitted RAD concatemer segment inherits its original read's gene assignment. The [matrix builder](../source_data/figure_07/provenance/build_matrices.py) counts each exact cell–gene–UMI combination once; records without a UMI count individually. The [assignment examples](../data/examples/figure_07/RAD_emitted_assignment_rows.tsv) show original read ID, cell barcode, 12-base UMI, raw barcode and correction flag. The [input manifest](../source_data/figure_07/RAD_emitted_segment_source_manifest.tsv) and [matrix production record](../source_data/figure_07/matrix_production_record.md) identify the complete inputs.

## 2. Build molecule matrices and select H146/H526 nuclei

Matrix Market files store one-based gene and cell indices with integer molecule counts. Ordered feature and barcode files label the coordinates; absent sparse entries count as zero.

| Workflow | Genes × selected nuclei | Nonzero coordinates | Counted molecules |
|---|---:|---:|---:|
| RAD | 45,224 × 12,423 | 15,772,545 | 22,875,174 |
| BLAZE | 44,807 × 10,001 | 17,301,003 | 27,350,119 |
| Flexiplex | 45,939 × 12,101 | 21,582,352 | 35,106,495 |


The matrices and labels are under `checkpoints/figure_07/`. The [cohort table](../source_data/figure_07/native_positive_depth_cohorts.tsv) lists cell IDs, Vireo labels and complete-library molecule totals. Include positive-depth H146 or H526 singlets:

| Workflow | H146 nuclei | H526 nuclei |
|---|---:|---:|
| RAD | 709 | 419 |
| BLAZE | 234 | 185 |
| Flexiplex | 290 | 219 |
| Illumina | 263 | 195 |


Each workflow contributes its recovered nuclei and their sequencing depths. Gene eligibility is evaluated within these cohorts.

## 3. Normalize counts and test genes

In each of the four workflows, require at least ten molecules per gene and detection in at least 1% of the combined H146-plus-H526 cohort. Intersecting these four sets gives the [8,135 common genes](../source_data/figure_07/common_genes.tsv) used in panel D.

Normalize each nucleus to 10,000 molecules using its complete-library total before gene filtering, then transform counts as `log2(1 + CP10K)`. Raw P values come from two-sided Wilcoxon rank-sum tests implemented by scran `pairwiseWilcox` on these transformed counts. The effect estimate is:

```text
log2 fold change = log2[(mean H146 CP10K + 0.1) / (mean H526 CP10K + 0.1)]
```

Positive effects indicate higher expression in H146; negative effects indicate higher expression in H526. [Benjamini–Hochberg adjustment](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x) is applied separately to each workflow and the Illumina reference over the same 8,135-gene family. The [gene-level table](../source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz) supplies raw P values, adjusted P values and signed effects.

The [matrix examples](../data/examples/figure_07/PREVIEW.md) follow PTPRJ in barcode `CATACCCAGCGTGAGT`: two molecules in a 2,400-molecule library give CP10K = 8.333333333333334 and `log2(1 + CP10K)` = 3.222392421336448.

```bash
mkdir -p results
python3 scripts/figure_07/extract_examples.py \
  --matrix-dir checkpoints/figure_07/native/RAD/all \
  --de-table source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz
```

## 4. Plot gene calls, fold changes and confidence: panels A–C

**Panel A** uses seven [Venn-region counts](../source_data/figure_07/plotted/panel_A_venn_regions.tsv): 126 RAD-only, 26 BLAZE-only, 24 Flexiplex-only, 32 RAD–BLAZE-only, 67 RAD–Flexiplex-only, 20 BLAZE–Flexiplex-only and 443 shared by all three. These total 668 RAD, 521 BLAZE and 554 Flexiplex reference-supported calls.

**Panel B** plots signed log2 fold change against `−log10(FDR)`. The [RAD](../source_data/figure_07/plotted/panel_B_RAD.csv.gz), [Flexiplex](../source_data/figure_07/plotted/panel_B_Flexiplex.csv.gz) and [BLAZE](../source_data/figure_07/plotted/panel_B_BLAZE.csv.gz) tables give the coordinates and gene labels.

**Panel C** plots BLAZE confidence on the X axis and RAD or Flexiplex confidence on the Y axis for [412 H146-high](../source_data/figure_07/plotted/panel_C_H146_high.csv.gz) and [767 H526-high](../source_data/figure_07/plotted/panel_C_H526_high.csv.gz) reference-gene coordinates. The four fits use ordinary least squares with a free intercept. [Regression coefficients](../source_data/figure_07/plotted/panel_C_regressions.tsv) give the slopes, intercepts and R². The [plot manifest](../source_data/figure_07/plotted/prism_table_manifest.json) maps each graph to its gene coordinates and table row bounds.

## 5. Sweep calling thresholds: panel D

Hold the Illumina reference at adjusted P <0.05 and absolute log2 fold change >1. Sweep the long-read adjusted-P cutoff over 10⁻⁸, 10⁻⁶, 10⁻⁵, 10⁻⁴, 0.001, 0.005, 0.01, 0.05 and 0.1, and the absolute log2-fold-change cutoff over 0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5 and 3. A call must fall below the adjusted-P cutoff and exceed the effect-size cutoff.

For each direction, TP is a same-direction Illumina call recovered by the tool, FP is a tool call without same-direction reference support, and FN is a reference call not recovered in that direction:

```text
precision = TP / (TP + FP)
recall = TP / (TP + FN)
F1 = 2TP / (2TP + FP + FN)
```

A zero F1 denominator gives zero. The [threshold grid](../source_data/figure_07/threshold_grid.tsv) contains 594 rows: three tools × two directions × 99 threshold combinations. Display labels are rounded half-up to one significant digit.

Reproduce the common-family adjustment and directional scores:

```bash
python3 scripts/figure_07/adjust_common_gene_pvalues.py \
  --input source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz \
  --output results/figure07_adjusted.tsv
python3 scripts/figure_07/score_directional_calls.py \
  --input results/figure07_adjusted.tsv \
  --output results/figure07_thresholds.tsv
```

The adjustment produces 24,405 gene–tool rows. The [direct-test checker](../scripts/figure_07/check_direct_test_provenance.py) accepts the complete test table through `--native-tests` and compares its raw P values and effects with the common-gene table.

## Reproduce the confidence fits and plotting tables

```bash
python3 scripts/figure_07/replay_prism_scatter_fits.py \
  --source-dir source_data/figure_07/plotted
```

The [fit validation](../source_data/figure_07/plotted/panel_C_regression_validation.json) compares point counts, slopes, intercepts and R² with the Prism results. To extract panel tables and check the 594 heatmap values from the Prism project:

```bash
python3 scripts/figure_07/extract_prism_panel_tables.py \
  --prism "external_data/prism/Figure 7.prism" \
  --output-dir results/figure07_native_tables \
  --threshold-grid source_data/figure_07/threshold_grid.tsv
```
