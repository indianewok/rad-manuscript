# Figure 7 Differential expression in LongBench single nuclei

Figure 7 compares differential-expression signals between H146 and H526 nuclei with the matched Illumina reference. Panels A–C use the deposited native call, volcano and confidence tables. Panel D evaluates directional call recovery over a common family of 8,135 eligible genes. The molecule-counting workflow below defines that common-gene analysis and retains all emitted RAD concatemer segments.

![Figure 7](../figures/figure_07/prism/figure_07.png)

## Figure legend

Figure 7. Faithful and confident identification of differentially-expressed genes. A. Venn diagram depicting the overlap between Illumina-reference-supported differentially expressed genes recovered by each tool. B. Volcano plot depicting the fold change and confidence (FDR, False Discovery Rate) of differences in gene expression between H526 and H146 cell lines. Genes identified with greatest confidence (FDR < 10⁻²⁰) in Flexiplex or BLAZE are identified by name. Genes identified as key markers of small cell lung cancer (SCLC) types -A and SCLC-P, are distinguished by transcriptional regulators, ASCL1 and POU2F3 (red). C. Scatterplot of confidence in expression differences between BLAZE (x-axis) other tools (y-axis) for genes that are overexpressed in H146 (top) and H526 (bottom) nuclei, respectively. Red line indicates unity and slopes of best fit lines for RAD and Flexiplex are listed in inset. D. Accuracy of differentially expressed gene identification for each tool (F1 scores) as compared to ground truth, as defined by short read data across a sweep of fold-change (x-axis) and FDR (y-axis) cutoff thresholds.

## Inputs and software

The common-gene analysis uses the LongBench single-nucleus ONT reads, each tool’s selected barcodes and assignments, and the paired Illumina gene-count matrix. The cell-line labels come from the genotype analysis in [Figure 6](figure_06.md). Native plotting tables for the other panels are supplied separately below.

| Stage | Software and parameters | Command or source |
|---|---|---|
| RAD assignments | RAD 1.0.2, commit `4acbe004ba11b150d6832395452632f367a6e6c1`; 10x 3v3.1 layout, offensive correction, generated and whitelist edit distances two, minimum read length 85, chunk size 5,000, 60 RAD and four pigz threads; all emitted records retained | [Metadata](../source_data/figure_07/provenance/RAD_run_metadata.txt), [command](../source_data/figure_07/provenance/RAD_demux_command.txt) |
| BLAZE assignments | BLAZE 2.5.0; `--force-cells 10000 --threads 48 --minimal_stdout`, 3v3 default | [Producing run](../source_data/figure_06/provenance/BLAZE_run_metadata.txt), [extraction command](../source_data/figure_07/provenance/extract_BLAZE_command.txt) |
| Flexiplex assignments | Flexiplex 1.02.6; `-d 10x3v3 -f 8 -e 2 -k SELECTED -p 16`; assignments read from the diagnostic sidecar containing `RawCellBarcode` | [Producing run](../source_data/figure_07/provenance/Flexiplex_run_metadata.txt), [extraction command](../source_data/figure_07/provenance/extract_Flexiplex_command.txt) |
| Common raw-read alignment | minimap2 2.30-r1287, samtools 1.22.1; `-ax splice --secondary=no --MD -Y`; GENCODE v44 splice index; wrapper defaults of 48 alignment threads and eight sort threads | [Alignment wrapper](../source_data/figure_07/provenance/align_common_raw.sh) |
| Differential expression | R 4.5.3, [scran](https://doi.org/10.12688/f1000research.9501.2) 1.34.0, scuttle 1.16.0; two-sided `pairwiseWilcox`, serial execution; native-script seed 20260825 | [Direct-test producer](../source_data/figure_07/provenance/direct_native_DE_producer.R), [common-gene producer](../source_data/figure_07/provenance/common_gene_DE_producer.R), [session information](../source_data/figure_07/provenance/DE_sessionInfo.txt) |

## Assign reads to genes

The [assignment extractor](../source_data/figure_07/provenance/extract_assignments.py) reads each tool’s cell-barcode and UMI assignments and links them to original read IDs. A common raw-read alignment supplies gene assignments for all tools. The aligner searches both transcript-strand orientations. The [gene-assignment script](../source_data/figure_07/provenance/assign_genes.py) selects primary alignments with MAPQ at least one, sums unstranded overlap with annotated exon records, and assigns the gene with the greatest overlap. Reads without exon overlap or with tied best genes are excluded.

Each emitted RAD concatemer segment inherits its original read’s gene assignment. The [matrix builder](../source_data/figure_07/provenance/build_matrices.py) counts each exact cell–gene–UMI combination once. Records without a UMI are counted individually.

The RAD assignment stream contains original read ID, cell barcode, UMI, raw barcode and correction flag. It retains 12-base UMIs and covers the 12,423 selected barcodes. Its SHA-256 is `a5dc369445826fdd36541a301b1b85448438fb52d351ce8883a12ef456457c48`. The [source manifest](../source_data/figure_07/RAD_emitted_segment_source_manifest.tsv) identifies the emitted-sequence and read-to-gene inputs. [Example assignment rows](../data/examples/figure_07/RAD_emitted_assignment_rows.tsv), their [extraction record](../data/examples/figure_07/assignment_extraction.json) and [per-barcode row counts](../source_data/figure_07/RAD_assignment_rows_by_barcode.tsv) connect the records to molecule counting.

## Molecule matrices for the common-gene analysis

Matrix Market files store one-based gene and cell indices with integer molecule counts. Ordered feature and barcode files identify each matrix coordinate. An absent sparse entry has count zero.

| Workflow | Genes × selected nuclei | Nonzero coordinates | Counted molecules |
|---|---:|---:|---:|
| RAD | 45,224 × 12,423 | 15,772,545 | 22,875,174 |
| BLAZE | 44,807 × 10,001 | 17,301,003 | 27,350,119 |
| Flexiplex | 45,939 × 12,101 | 21,582,352 | 35,106,495 |

The matrices and ordered labels are stored under `checkpoints/figure_07/`. The [cohort table](../source_data/figure_07/native_positive_depth_cohorts.tsv) supplies cell IDs, cell-line labels and complete-library depths. The contrast includes positive-depth nuclei assigned by Vireo to H146 or H526; doublets and unassigned nuclei are excluded.

| Workflow | H146 nuclei | H526 nuclei |
|---|---:|---:|
| RAD | 709 | 419 |
| BLAZE | 234 | 185 |
| Flexiplex | 290 | 219 |
| Illumina | 263 | 195 |

## Normalize counts and test differential expression

Within each platform, a gene requires at least ten counted molecules and detection in at least 1% of the H146-plus-H526 cohort. Intersecting the four eligibility sets gives the common gene family used for cross-platform comparison.

Each nucleus is normalized to 10,000 molecules using its complete-library total before gene filtering. Counts are transformed as `log2(1 + CP10K)`. Two-sided Wilcoxon rank-sum tests implemented by scran `pairwiseWilcox` compare the transformed values. The effect estimate is:

```text
log2 fold change = log2[(mean H146 CP10K + 0.1) / (mean H526 CP10K + 0.1)]
```

Positive effects indicate higher expression in H146. [Benjamini–Hochberg adjustment](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x) is performed separately for each long-read workflow and the Illumina reference over the same common gene family.

The [matrix examples](../data/examples/figure_07/PREVIEW.md) show the normalization calculation. For PTPRJ (`ENSG00000149177.15`) in barcode `CATACCCAGCGTGAGT`, two molecules in a 2,400-molecule library give CP10K = 8.333333333333334 and `log2(1 + CP10K)` = 3.222392421336448. Extract these examples from the complete matrix with:

```bash
mkdir -p results
python3 scripts/figure_07/extract_examples.py \
  --matrix-dir checkpoints/figure_07/native/RAD/all \
  --de-table source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz
```

## Construct the figure panels

The panel-specific plotting records preserve the gene family, coordinates and fitted values used in each display. The [native table manifest](../source_data/figure_07/plotted/prism_table_manifest.json) maps every plotted graph to its Prism data sheet, dataset definitions, row bounds and source CSV.

**Panel A** is defined by the seven [Venn region counts](../source_data/figure_07/plotted/panel_A_venn_regions.tsv) in the layout artwork: 126 RAD-only, 26 BLAZE-only, 24 Flexiplex-only, 32 RAD–BLAZE-only, 67 RAD–Flexiplex-only, 20 BLAZE–Flexiplex-only and 443 shared by all three. These sum to 668 RAD, 521 BLAZE and 554 Flexiplex reference-supported calls. The [artwork provenance](../source_data/figure_07/plotted/panel_A_artwork_provenance.json) records the exported image and source-project hashes.

**Panel B** plots each native workflow’s signed log2 fold change against `−log10(FDR)`. The exact [RAD](../source_data/figure_07/plotted/panel_B_RAD.csv.gz), [Flexiplex](../source_data/figure_07/plotted/panel_B_Flexiplex.csv.gz) and [BLAZE](../source_data/figure_07/plotted/panel_B_BLAZE.csv.gz) tables preserve the plotted values and displayed gene labels. Each CSV retains the source table’s native column order, as recorded in the manifest.

**Panel C** compares confidence with BLAZE on the X axis and RAD or Flexiplex on the Y axis. The plotted subsets contain 412 H146-high and 767 H526-high reference-gene coordinates. The exact [H146-high](../source_data/figure_07/plotted/panel_C_H146_high.csv.gz) and [H526-high](../source_data/figure_07/plotted/panel_C_H526_high.csv.gz) tables, [plotted XY points](../source_data/figure_07/plotted/panel_B_C_points.tsv.gz) and saved regression parameters/results identify the fitted data. The four fits use ordinary least squares with a free intercept. [Recalculated coefficients](../source_data/figure_07/plotted/panel_C_regressions.tsv) reproduce the saved results; dataset row bounds exclude unused cells in the native table.

**Panel D** measures directional precision, recall and F1 across long-read calling thresholds. The adjusted-P cutoffs are 10⁻⁸, 10⁻⁶, 10⁻⁵, 10⁻⁴, 0.001, 0.005, 0.01, 0.05 and 0.1. Absolute log2-fold-change cutoffs are 0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5 and 3. Adjusted P must be below its cutoff and absolute fold change must exceed its cutoff. The Illumina reference thresholds remain fixed at adjusted P <0.05 and absolute log2 fold change >1.

For each expression direction, TP denotes a same-direction reference call recovered by the long-read workflow, FP denotes a long-read call without same-direction reference support, and FN denotes a reference call not recovered in that direction. Precision is `TP/(TP + FP)`, recall is `TP/(TP + FN)`, and F1 is `2TP/(2TP + FP + FN)`. A zero F1 denominator gives zero. The [gene-level table](../source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz) contains the signed effects and direct and adjusted P values for all 8,135 common genes. The [threshold grid](../source_data/figure_07/threshold_grid.tsv) records call counts, metrics and the 594 display labels, rounded half-up to one significant digit.

## Reproduce the common-gene threshold analysis

Recalculate common-family adjustment and directional scores from the direct tests:

```bash
python3 scripts/figure_07/adjust_common_gene_pvalues.py \
  --input source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz \
  --output results/figure07_adjusted.tsv
python3 scripts/figure_07/score_directional_calls.py \
  --input results/figure07_adjusted.tsv \
  --output results/figure07_thresholds.tsv
python3 scripts/figure_07/render_source_proofs.py
```

The adjustment produces 24,405 gene–workflow rows. Directional scoring produces 594 threshold rows. The [direct-test provenance check](../scripts/figure_07/check_direct_test_provenance.py) accepts the complete native test table through `--native-tests` and compares its direct P values and effects with the common-gene table. The plotting script reads the portable source tables with matplotlib and numpy. The assembled manuscript figure is provided in the image above.

## Reproduce the native plotting tables and confidence fits

Recalculate the four confidence fits from the deposited plotting tables:

```bash
python3 scripts/figure_07/replay_prism_scatter_fits.py \
  --source-dir source_data/figure_07/plotted
```

To refresh the native plotting checkpoint from a local author project:

```bash
python3 scripts/figure_07/extract_prism_panel_tables.py \
  --prism "external_data/prism/Figure 7.prism" \
  --output-dir results/figure07_native_tables \
  --threshold-grid source_data/figure_07/threshold_grid.tsv
```

The extractor preserves the CSV values, dataset row bounds and exclusions, graph bindings, and native regression settings and results. With `--threshold-grid`, it also checks all 594 plotted heatmap values against the common-gene F1 table. The fit replay checks the point counts, slopes, intercepts and R² against the saved Prism regressions. The [validation record](../source_data/figure_07/plotted/panel_C_regression_validation.json) records the numerical agreement.
