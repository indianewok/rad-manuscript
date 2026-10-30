# Figure 4 — barcode discovery across 37 inputs

**RAD 1.0.2, commit [`4acbe004ba11b150d6832395452632f367a6e6c1`](https://github.com/indianewok/rad/commit/4acbe004ba11b150d6832395452632f367a6e6c1), `scan-wl --max-error 0.3`, complete inputs.**

The [per-input tool table](../source_data/figure_04/tool_parameters.tsv) records the RAD, BLAZE and Flexiplex versions and analysis flags; unavailable versions are marked `NA`. BLAZE and Flexiplex settings vary by input. The [RAD run records](../source_data/figure_04/run_records/) specify each input, catalogue and matched reference; [execution records](../source_data/figure_04/producing_evidence/current_RAD/) report the selected build and output counts.

P8 denotes the whole-transcriptome library; P8-enriched denotes its VDJ-enriched library.

Flexiplex barcode discovery used these flank-distance conditions. The [per-input tool table](../source_data/figure_04/tool_parameters.tsv) explicitly lists `-f` for every Flexiplex result.

| Flexiplex condition | Inputs | Number of inputs |
|---|---|---:|
| `-f 0` | P7, P8-enriched and P8; all four LongBench inputs; Isosceles ovarian; all ten Tilgner hippocampus inputs; all four MPNST inputs; ScMixology2 | 23 |
| `-f 8` | ScTagger-S and ScTagger-L (flat Q20); PromethION iPSC; both RAGE-seq inputs; LeBrigand-MOB; all eight Engblom tonsil inputs | 14 |

![Paired barcode discovery metrics](../figures/figure_04/barcode_discovery_paired.png)

Each point is one sequencing input. Lines join the three tools on that input; black bars show medians. Labels show Dunn-adjusted P-values for the two RAD comparisons within each metric. Individual libraries and technical runs retain their own input identifiers.

## Read the results

The [metrics table](../source_data/figure_04/barcode_detection_metrics.tsv) contains 111 observations: 37 inputs × three tools. For each observation it reports called barcodes, reference barcodes, TP, FP, FN, precision, recall and F1. The [sample inventory](../source_data/figure_04/sample_inventory.tsv) identifies the input, donor, library and sequencing-run relationships.

![Metrics for every input](../figures/figure_04/barcode_discovery_by_input.png)

The [paired precision](../source_data/figure_04/paired_precision.tsv), [recall](../source_data/figure_04/paired_recall.tsv) and [F1](../source_data/figure_04/paired_f1.tsv) tables use the same 37 input rows. The [input-characteristics table](../source_data/figure_04/input_characteristics.tsv) contains the saved full-input SeqKit summaries, including read counts, lengths, GC and quality statistics. Its `AvgQual` field follows SeqKit's definition; the original SeqKit version and invocation are unavailable.

The statistical analysis uses the existing Friedman test across the three tools, followed by two Dunn comparisons per metric: RAD versus BLAZE and RAD versus Flexiplex. Adjustment is within each metric's two-comparison family. The [Friedman results](../source_data/figure_04/friedman.tsv) and [Dunn results](../source_data/figure_04/dunn.tsv) give the statistics and P-values. The [calculation script](../scripts/figure_04/statistics.py) implements [GraphPad's documented Dunn calculation](https://www.graphpad.com/guides/prism/latest/statistics/stat_how_the_dunn_method_for_nonpar.htm).

## What the reference means

Synthetic inputs use their known source barcode sets. Biological inputs use matched filtered short-read barcodes or published spatial masks. TP is the intersection between a tool's selected set and its reference; FP is selected barcodes outside that reference; FN is reference barcodes not selected. These metrics measure agreement with the stated reference.

```text
precision = TP / (TP + FP)
recall    = TP / (TP + FN)
F1        = 2TP / (2TP + FP + FN)
```

The RAGE-seq TNBC lymph-node reference includes deposited short-read barcodes annotated as `T_cell*`, `B_cell*` or `T_B_doublet`, with `in_deposited_shortread_list=True`: 5,978 barcodes comprising 4,255 T-cell, 1,637 B-cell and 86 T/B-doublet barcodes. The cell-line input has a separate 4,505-barcode reference.

ScMixology2 uses the same complete 25,164,948-read FASTQ for native RAD, BLAZE 2.5.1 and Flexiplex 1.02.7 (release v1.02.7.1) runs. BLAZE uses `--expect-cells 500 --minQ 15 --max-edit-distance 2`; Flexiplex uses `-d 10x3v3 -f 0 -e 2` followed by `flexiplex-filter` against the complete chemistry catalogue. Both comparators use 16 threads. The matched 248-barcode Cell Ranger reference is used for scoring. [Commands and outputs](../scripts/figure_04/scmixology2/README.md) provide the per-tool steps and pinned software identities.

P7, P8-enriched, P8 and Isosceles ovarian use Flexiplex 1.02.6 with `-d 10x3v3 -f 0 -e 2`, followed by filter 1.02 against the complete chemistry catalogue. Each run uses the complete input and 16 tool threads. [Per-input commands](../scripts/figure_04/flexiplex_f0/README.md) and [execution records](../source_data/figure_04/producing_evidence/current_Flexiplex_f0/) give the input identities and selected-barcode results.

ERR15095097 uses the 4,602-barcode MPNST1 (2020_23) short-read reference, matching its raw-read barcode identities. The accession retains its deposited [MPNST2 sample label](https://www.ebi.ac.uk/biostudies/files/E-MTAB-15190/E-MTAB-15190.sdrf.txt). ERR15095096 uses the MPNST2 reference. The [scoring record](../source_data/figure_04/reference_scoring/ERR15095097.json) binds the native selected lists to the MPNST1 reference.

To reproduce ERR15095097's scoring, use the selected barcode list from each native tool run and the MPNST1 short-read reference identified in its [dataset record](../source_data/figure_04/run_records/ERR15095097.json). The [scoring script](../scripts/figure_04/rescore_reference.py) checks the reference barcode identity before calculating TP, FP, FN, precision, recall and F1:

```bash
REFERENCE=external_data/figure_04/references/ERR15095094_MPNST1_scNaUMIseq_MinION.reference.txt.gz
RECORD=source_data/figure_04/run_records/ERR15095097.json

python3 scripts/figure_04/rescore_reference.py --dataset-record "$RECORD" \
  --tool RAD --selected "$RAD_SELECTED" --reference "$REFERENCE" \
  --output results/figure_04/ERR15095097/RAD_metrics.tsv
python3 scripts/figure_04/rescore_reference.py --dataset-record "$RECORD" \
  --tool BLAZE --selected "$BLAZE_SELECTED" --reference "$REFERENCE" \
  --output results/figure_04/ERR15095097/BLAZE_metrics.tsv
python3 scripts/figure_04/rescore_reference.py --dataset-record "$RECORD" \
  --tool Flexiplex --selected "$FLEXIPLEX_SELECTED" --reference "$REFERENCE" \
  --output results/figure_04/ERR15095097/Flexiplex_metrics.tsv
```

Set `RAD_SELECTED`, `BLAZE_SELECTED` and `FLEXIPLEX_SELECTED` to their emitted selected-list files. The script accepts plain or gzipped lists, with optional counts after each barcode. It removes a terminal `-1` suffix when reading the matched short-read reference.

## Walk through one dataset

Start with [ScTagger-S's run record](../source_data/figure_04/run_records/ScTagger-S_flatQ20.json) and its row in the tool table. Its complete input has 98,873 reads from 50 true barcodes, with uniform Q20 scores. RAD selects 53 barcodes: 50 TP, three FP and zero FN, giving precision 50/53, recall 50/50 and F1 100/103. The [two ScTagger-L FASTQ records](../data/examples/figure_02/L_flatQ20_first2.fastq) show the read format used by the uniform-Q20 simulation: identifier, nucleotide sequence, `+`, and one quality character per base.

Build the pinned source using the [single-dataset instructions](../scripts/figure_04/README.md). The native command for ScTagger-S is:

```bash
mkdir -p results/figure_04/ScTagger-S_flatQ20
external_data/software/rad_build_4acbe00/rad scan-wl \
  --input external_data/figure_04/inputs/ScTagger-S_flatQ20.fastq.gz \
  --output-prefix results/figure_04/ScTagger-S_flatQ20/rad \
  --adapter_seq CTACACGACGCTCTTCCGATCT \
  --barcode-length 16 --left-margin 0 --right-margin 0 \
  --max-error 0.3 \
  --whitelist external_data/figure_04/catalogues/3M-february-2018-3v3.txt_bitlist.csv.gz \
  --threads 16 --chunk-size 10000
```

The chemistry catalogue is the full set of allowed barcode sequences. It is separate from the matched reference used for scoring. All RAD scans use the complete selected input and high-specificity selection, without a read cap. ScTagger's uniform-Q20 input is specified explicitly; biological inputs retain their native qualities.

The [single-dataset runner](../scripts/figure_04/run_scan.py) verifies the build and inputs, saves the native command and output, and writes a metrics CSV plus a barcode-membership CSV. The latter shows which selected barcodes match the reference. Complete barcode lists and external input files are kept outside Git. Controlled-access spatial data require their registered access process.

## Recalculate the deposited tables

The [small example](../data/examples/figure_04/three_input_metrics_example.tsv) contains all three tools for ScTagger-S, ScTagger-L and the RAGE-seq lymph node. Recalculate its metrics from TP, FP and FN:

```bash
mkdir -p results
python3 scripts/revision/figures_124_steps/recompute_detection_metrics.py \
  data/examples/figure_04/three_input_metrics_example.tsv \
  results/figure4_example.tsv --expected-inputs 3
```

Compare this with the [expected output](../data/examples/figure_04/three_input_metrics_recomputed.tsv). Use `source_data/figure_04/barcode_detection_metrics.tsv` and `--expected-inputs 37` to check the complete comparison. The [immune-reference example](../data/examples/figure_04/immune_reference_annotation_example.tsv) shows how annotation labels select the lymph-node reference:

```bash
python3 scripts/revision/figures_124_steps/rescore_immune_reference.py \
  data/examples/figure_04/immune_reference_annotation_example.tsv \
  results/figure4_immune_example.tsv
python3 scripts/figure_04/statistics.py \
  --output-dir results/figure_04/statistics
python3 scripts/figure_04/plot_discovery.py \
  --statistics-dir results/figure_04/statistics \
  --output-dir results/figure_04/plots
```

The plotted points and labelled matrices above are generated directly from the current source table. [Schemas](../source_data/figure_04/schemas.json) define its fields.
