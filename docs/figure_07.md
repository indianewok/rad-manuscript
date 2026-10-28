# Figure 7 — differential expression in LongBench single nuclei

Figure 7 compares differential expression between H146 and H526 nuclei with the matched Illumina reference. It follows each workflow from barcode and UMI assignments to molecule counts, gene-level tests and recovery of reference-supported expression differences. The analysis uses **8,135 genes** eligible in all four platforms and retains all emitted RAD concatemer segments.

![Figure 7](../figures/figure_07/prism/figure_07.png)

Panels A and C show the earlier analysis. The source tables and methods below use the updated 8,135-gene analysis.

## Software and parameters

| Stage | Software and settings | Source record |
|---|---|---|
| RAD assignments | RAD 1.0.2, commit `4acbe004ba11b150d6832395452632f367a6e6c1`; 10x 3v3.1, offensive correction, generated/whitelist edit distance 2, minimum read length 85, chunk size 5,000, 60 RAD and four pigz threads; all emitted records retained | [Run metadata](../source_data/figure_07/provenance/RAD_run_metadata.txt), [command](../source_data/figure_07/provenance/RAD_demux_command.txt) |
| BLAZE assignments | BLAZE 2.5.0; native output from `--force-cells 10000 --threads 48 --minimal_stdout`, 3v3 default; 10,001 selected barcodes; `PYTHONHASHSEED=UNSET` | [Producer](../source_data/figure_06/provenance/BLAZE_run_metadata.txt), [extraction command](../source_data/figure_07/provenance/extract_BLAZE_command.txt) |
| Flexiplex assignments | Flexiplex 1.02.6 audit build `d84c8ae4f3865052f2b5ecec816949b94682f302`; `-d 10x3v3 -f 8 -e 2 -k SELECTED -p 16`; 12,101 selected barcodes; diagnostic sidecar with `RawCellBarcode` | [Producer](../source_data/figure_07/provenance/Flexiplex_run_metadata.txt), [extraction command](../source_data/figure_07/provenance/extract_Flexiplex_command.txt) |
| Common raw-read alignment | minimap2 2.30-r1287, samtools 1.22.1; `-ax splice --secondary=no --MD -Y`; GENCODE v44 splice index; wrapper default 48 alignment threads, eight sort threads | [Alignment wrapper](../source_data/figure_07/provenance/align_common_raw.sh) |
| Differential expression | R 4.5.3, scran 1.34.0, scuttle 1.16.0; two-sided `pairwiseWilcox` with serial execution; native-script seed 20260825 | [Native producer](../source_data/figure_07/provenance/direct_native_DE_producer.R), [common-gene producer](../source_data/figure_07/provenance/common_gene_DE_producer.R), [session information](../source_data/figure_07/provenance/DE_sessionInfo.txt) |

The Flexiplex audit build adds raw-barcode reporting while preserving barcode-matching logic. Its diagnostic-sidecar execution supplies this expression analysis; the native FASTQ execution supplies the genotype alignment in [Figure 6](figure_06.md).

## Assign genes and count molecules

The [assignment extractor](../source_data/figure_07/provenance/extract_assignments.py) reads cell barcodes and UMIs from each tool's output. The common [gene-assignment script](../source_data/figure_07/provenance/assign_genes.py) uses primary alignments with MAPQ ≥1. It sums unstranded overlap with annotated exon records and selects the gene with the greatest overlap; tied best genes and reads without exon overlap are excluded.

Each RAD concatemer segment inherits the gene assigned to its original read. The [matrix builder](../source_data/figure_07/provenance/build_matrices.py) counts each exact cell–gene–UMI combination once and counts records without a UMI individually.

The retained RAD assignment ledger contains 57,885,606 emitted rows: 49,555,699 exact-barcode rows and 8,329,907 corrected-barcode rows. Each row contains original read ID, cell barcode, UMI, raw barcode and correction flag. The ledger covers all 12,423 selected barcodes and retains 12-base UMIs. Its SHA-256 is `a5dc369445826fdd36541a301b1b85448438fb52d351ce8883a12ef456457c48`.

[Ten example assignments](../data/examples/figure_07/RAD_emitted_assignment_rows.tsv), their [extraction receipt](../data/examples/figure_07/assignment_extraction.json), and [per-barcode row counts](../source_data/figure_07/RAD_assignment_rows_by_barcode.tsv) connect individual records to the complete stream.

## Molecule matrices and normalization

Matrix Market files store a one-based gene index, cell index and integer molecule count. Ordered feature and barcode files resolve each coordinate; absent sparse entries have count zero. The [matrix preview](../data/examples/figure_07/PREVIEW.md), [example entries](../data/examples/figure_07/RAD_matrix_entries.tsv) and [extraction record](../data/examples/figure_07/extraction.json) show the mapping.

| Workflow | Genes × selected nuclei | Nonzero coordinates | Molecules |
|---|---:|---:|---:|
| RAD, all emitted segments | 45,224 × 12,423 | 15,772,545 | 22,875,174 |
| BLAZE | 44,807 × 10,001 | 17,301,003 | 27,350,119 |
| Flexiplex | 45,939 × 12,101 | 21,582,352 | 35,106,495 |

The matrices and labels are stored under `checkpoints/figure_07/`. The [cohort table](../source_data/figure_07/native_positive_depth_cohorts.tsv) records cell IDs, named genotypes and complete-library depths for 9,404 RAD, 6,478 BLAZE and 7,125 Flexiplex nuclei.

Counts are normalized to 10,000 molecules per nucleus using each nucleus's complete library total before gene filtering, then transformed as `log2(1 + CP10K)`. For example, the retained RAD entry for PTPRJ (`ENSG00000149177.15`) in barcode `CATACCCAGCGTGAGT` contains two molecules in a 2,400-molecule library:

```text
CP10K = 10,000 × 2 / 2,400 = 8.333333333333334
log2(1 + CP10K) = 3.222392421336448
```

Extract the examples from the complete matrix with:

```bash
mkdir -p results
python3 scripts/figure_07/extract_examples.py \
  --matrix-dir checkpoints/figure_07/native/RAD/all \
  --de-table source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz
```

This produces eight matrix entries and nine differential-expression rows for DPM1, ASCL1 and POU2F3, retaining original indices and full-input hashes.

## Differential expression between cell lines

The contrast includes positive-depth nuclei assigned to H146 or H526: 709/419 for RAD, 234/185 for BLAZE, 290/219 for Flexiplex and 263/195 for Illumina. Within each platform, a gene requires at least ten molecules and detection in at least 1% of the two-line cohort. Intersecting the four eligible sets gives 8,135 common genes.

Two-sided Wilcoxon tests compare `log2(1 + CP10K)` values. The effect estimate is:

```text
log2 fold change = log2[(mean H146 CP10K + 0.1) / (mean H526 CP10K + 0.1)]
```

Positive values indicate higher expression in H146. Benjamini–Hochberg adjustment is applied separately to each workflow and the Illumina reference over the same common-gene family.

The [gene-level table](../source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz) contains 24,405 rows, one per gene and long-read workflow:

| Columns | Meaning |
|---|---|
| `gene_id`, `gene_symbol`, `tool` | Versioned gene ID, symbol and workflow |
| `tool_log2FC`, `Illumina_log2FC` | Mean-expression effect estimates |
| `tool_p_value`, `Illumina_p_value` | Direct Wilcoxon P values |
| `tool_BH_FDR_common`, `Illumina_BH_FDR_common` | Adjusted P values over 8,135 genes |
| `tool_confidence`, `Illumina_confidence` | Uncapped −log10 adjusted P values |
| `*_confidence_cap50` | Display values capped at 50 |

Recalculate the adjusted P values and directional scores from the retained direct tests:

```bash
python3 scripts/figure_07/adjust_common_gene_pvalues.py \
  --input source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz \
  --output results/figure07_adjusted.tsv
python3 scripts/figure_07/score_directional_calls.py \
  --input results/figure07_adjusted.tsv --output results/figure07_thresholds.tsv
```

The output contains 24,405 adjusted rows and 594 directional threshold rows. Counts match the [deposited threshold grid](../source_data/figure_07/threshold_grid.tsv) exactly, and metrics match within 1e-12. The [direct-test comparison script](../scripts/figure_07/check_direct_test_provenance.py) checks every retained P value and effect against the native test output.

## Connect the tests to panels A–D

**Panel A** shows recovery of same-direction Illumina calls. Both reference and long-read calls require adjusted P <0.05 and absolute log2 fold change >1. The reference contains 412 H146-high and 769 H526-high genes. The updated analysis recovers 654 with RAD, 522 with BLAZE and 556 with Flexiplex. [Gene membership](../source_data/figure_07/directional_membership.tsv) and the seven [intersection regions](../source_data/figure_07/venn_regions.tsv) define the comparison.

**Panel B** plots log2 fold change against −log10 adjusted P for each long-read workflow. The common gene-level table supplies the coordinates, symbols and reference calls.

**Panel C** compares uncapped confidence among directional Illumina-reference genes. The [source points](../source_data/figure_07/confidence_fit_points.tsv) support a retained OLS fit with an estimated intercept; its [coefficients](../source_data/figure_07/confidence_fit_candidates.tsv) are recorded separately from the saved artwork's fit.

**Panel D** evaluates adjusted-P cutoffs of 10⁻⁸, 10⁻⁶, 10⁻⁵, 10⁻⁴, 0.001, 0.005, 0.01, 0.05 and 0.1, and absolute log2-fold-change cutoffs of 0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5 and 3. Adjusted P must fall below its cutoff and absolute fold change must exceed its cutoff. Both directions are evaluated for each workflow while the Illumina thresholds remain fixed. Precision is TP/(TP + FP), recall is TP/(TP + FN), and F1 is `2TP/(2TP + FP + FN)`, with F1 = 0 for a zero denominator. The [grid](../source_data/figure_07/threshold_grid.tsv) includes counts, metrics and the 594 display labels, rounded half-up to one significant digit.

Source-table plots can be regenerated with matplotlib and numpy:

```bash
python3 scripts/figure_07/render_source_proofs.py
```

## Additional source records

Reconstruction from emitted sequences requires the emitted FASTQ and frozen original-read-to-gene table listed in the [source manifest](../source_data/figure_07/RAD_emitted_segment_source_manifest.tsv). The available assignment ledger normalizes orientation and concatemer suffixes and stores barcode/UMI assignments keyed to original reads. Reproducing the saved Panel C regression annotations requires its executed fit specification.
