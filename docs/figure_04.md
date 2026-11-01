# Figure 4 — barcode discovery across 37 sequencing inputs

Figure 4 compares barcode discovery across 37 inputs spanning synthetic reads, single-cell and single-nucleus libraries, targeted receptor sequencing, and spatial transcriptomics. Each tool's selected barcode list is compared with the reference assigned to that input. The same reference is used for all three tools.

[Tool versions and command flags](../source_data/figure_04/tool_parameters.tsv) · [Input inventory](../source_data/figure_04/sample_inventory.tsv)

![Figure 4](../figures/figure_04/prism/figure_04.png)

## Inputs and barcode references

The [sample inventory](../source_data/figure_04/sample_inventory.tsv) identifies each input, donor, library, and sequencing run. P8 denotes the whole-transcriptome library; P8-enriched denotes the corresponding VDJ-enriched library. Individual libraries and flow-cell runs retain separate input identifiers throughout scoring.

Synthetic inputs use their known source barcodes as the reference. Biological inputs use matched filtered short-read barcodes or published spatial masks. The chemistry catalog supplies all allowed barcode sequences during discovery; the matched reference defines the comparison set for scoring.

The RAGE-seq cell-line mixture uses a 4,505-barcode reference. The TNBC lymph-node reference uses deposited short-read barcodes annotated as `T_cell*`, `B_cell*`, or `T_B_doublet`, with `in_deposited_shortread_list=True`. This produces 5,978 reference barcodes: 4,255 T-cell, 1,637 B-cell, and 86 T/B-doublet barcodes.

The [input-characteristics table](../source_data/figure_04/input_characteristics.tsv) supplies the read counts, read lengths, GC content, and quality statistics displayed in panels B–E. `AvgQual` follows the SeqKit definition used by the source summaries.

## Discovery software and settings

All RAD inputs were processed with RAD 1.0.2 at commit [`4acbe004ba11b150d6832395452632f367a6e6c1`](https://github.com/indianewok/rad/commit/4acbe004ba11b150d6832395452632f367a6e6c1), using `scan-wl --max-error 0.3`, high-specificity selection, and the complete input. Synthetic ScTagger inputs use uniform Q20 scores; biological inputs retain their native qualities.

The [tool-parameter table](../source_data/figure_04/tool_parameters.tsv) records each tool's version and command flags for every tool–input combination. [RAD run records](../source_data/figure_04/run_records/) identify each input, chemistry catalog, and matched reference. The [execution records](../source_data/figure_04/producing_evidence/current_RAD/) link the build, input and emitted barcode list.

Flexiplex was evaluated at flank distances `-f 0` and `-f 8`, followed by filtering against the complete chemistry catalog. For inputs with both settings, the figure uses the condition with the higher F1 score. The same selected condition supplies precision and recall. The [selected-condition table](../source_data/figure_04/plotted_checkpoint/flexiplex_selected_conditions.tsv) records both F1 values and the selected setting for every input.

| Displayed flank distance | Inputs | Count |
|---|---|---:|
| `-f 0` | P8 WTA; PromethION iPSC; LongBench SN-ONT, SC-PB, and SN-PB; Isosceles ovarian; nine hippocampal inputs; four MPNST inputs; section17 1T/1B and 4T/1B; ScMixology2 | 22 |
| `-f 8` | ScTagger-S/L; P7 and P8 VDJ-enriched; both RAGE-seq inputs; LongBench SC-ONT; LeBrigand-MOB; Tilgner m1 ONT Run3; the six other tonsil inputs | 15 |

ScMixology2 uses the complete 25,164,948-read FASTQ for native RAD, BLAZE 2.5.1, and Flexiplex 1.02.7 (release v1.02.7.1) runs. BLAZE uses `--expect-cells 500 --minQ 15 --max-edit-distance 2`. Flexiplex uses `-d 10x3v3 -f 0 -e 2`, followed by `flexiplex-filter` against the complete chemistry catalog. Both comparators use 16 threads. Scoring uses the matched 248-barcode Cell Ranger reference. The [ScMixology2 workflow](../scripts/figure_04/scmixology2/README.md) gives its commands, software identities, and outputs.

## Barcode scoring and panel tables

Selected barcodes are compared with the reference by exact sequence. True positives are selected reference barcodes; false positives are selected barcodes outside the reference; false negatives are reference barcodes absent from the selected set.

```text
precision = TP / (TP + FP)
recall    = TP / (TP + FN)
F1        = 2TP / (2TP + FP + FN)
```

The [plotted metrics](../source_data/figure_04/plotted_checkpoint/plotted_metrics.tsv) contain the 111 input–tool observations used in the figure. The paired [F1](../source_data/figure_04/plotted_checkpoint/paired_f1.tsv), [precision](../source_data/figure_04/plotted_checkpoint/paired_precision.tsv), and [recall](../source_data/figure_04/plotted_checkpoint/paired_recall.tsv) tables use the same 37 input IDs and displayed names. The modality panels use transposed copies of the same 333 metric values. The [panel bindings](../source_data/figure_04/plotted_checkpoint/panel_bindings.json) connect the plots to their source tables.

The [barcode-count table](../source_data/figure_04/barcode_detection_metrics.tsv) reports calls, reference sizes, TP, FP and FN for each native discovery run. The [condition comparison](../source_data/figure_04/plotted_checkpoint/producer_comparison.tsv) connects these runs to the Flexiplex condition selected for plotting.

ERR15095097 is scored against the 4,602-barcode MPNST1 (2020_23) short-read reference, which matches its raw-read barcode identities. The accession retains its deposited [MPNST2 sample label](https://www.ebi.ac.uk/biostudies/files/E-MTAB-15190/E-MTAB-15190.sdrf.txt). ERR15095096 uses the MPNST2 reference. The [scoring record](../source_data/figure_04/reference_scoring/ERR15095097.json) binds the native selected lists to the MPNST1 reference.

Recalculate ERR15095097's metrics with the selected list from each native run:

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

Set `RAD_SELECTED`, `BLAZE_SELECTED`, and `FLEXIPLEX_SELECTED` to the emitted selected-list files. The script accepts plain or gzipped lists, checks reference identity, and removes a terminal `-1` suffix from short-read reference barcodes.

## Matched statistical comparison

Within each metric, the sequencing input is the matched unit: its RAD, BLAZE, and Flexiplex values are calculated against the same reference. The three tools are compared with a Friedman test across all 37 inputs. Two Dunn comparisons follow within each metric: RAD versus BLAZE and RAD versus Flexiplex. Multiplicity adjustment is applied to that metric's two-comparison family.

The [Friedman table](../source_data/figure_04/plotted_checkpoint/friedman.tsv) and [Dunn table](../source_data/figure_04/plotted_checkpoint/dunn.tsv) give the statistics and adjusted P values. The [statistical implementation](../scripts/figure_04/statistics.py) follows [GraphPad's documented Dunn calculation](https://www.graphpad.com/guides/prism/latest/statistics/stat_how_the_dunn_method_for_nonpar.htm). The figure displays distributions and medians across the 37 input values; box-plot whiskers extend to the minimum and maximum. The folder also contains the Prism statistical-result tables.

## Run one input from reads to metrics

The [single-input workflow](../scripts/figure_04/README.md) builds the pinned RAD source and runs discovery from a dataset record. For ScTagger-S, the input contains 98,873 reads from 50 source barcodes. Its [run record](../source_data/figure_04/run_records/ScTagger-S_flatQ20.json) identifies the input, chemistry catalog, and truth set.

```bash
mkdir -p results/figure_04/ScTagger-S_flatQ20
external_data/software/rad_build_4acbe00/rad scan-wl \
  --input external_data/figure_04/inputs/ScTagger-S_flatQ20.fastq.gz \
  --output-prefix results/figure_04/ScTagger-S_flatQ20/rad \
  --adapter_seq CTACACGACGCTCTTCCGATCT \
  --barcode-length 16 \
  --max-error 0.3 \
  --whitelist external_data/figure_04/catalogues/3M-february-2018-3v3.txt_bitlist.csv.gz \
  --threads 16 --chunk-size 10000
```

The [runner](../scripts/figure_04/run_scan.py) checks the build and inputs, records the executed command, and writes a metrics table plus the selected-barcode membership table. These outputs connect the native selected list to the Figure 4 scores.

## Recalculate barcode-set scores and the plotted comparison

The [three-input example](../data/examples/figure_04/three_input_metrics_example.tsv) follows the count-to-score calculation for ScTagger-S, ScTagger-L and the RAGE-seq lymph node:

```bash
mkdir -p results
python3 scripts/revision/figures_124_steps/recompute_detection_metrics.py \
  data/examples/figure_04/three_input_metrics_example.tsv \
  results/figure4_example.tsv --expected-inputs 3
```

The [example output](../data/examples/figure_04/three_input_metrics_recomputed.tsv) gives the corresponding recalculated scores. Apply the same command to `source_data/figure_04/barcode_detection_metrics.tsv` with `--expected-inputs 37` to check the producing-run barcode counts. The [immune-reference example](../data/examples/figure_04/immune_reference_annotation_example.tsv) shows how the lymph-node annotations define its reference:

```bash
python3 scripts/revision/figures_124_steps/rescore_immune_reference.py \
  data/examples/figure_04/immune_reference_annotation_example.tsv \
  results/figure4_immune_example.tsv
python3 scripts/figure_04/extract_plotted_prism.py \
  --prism "external_data/prism/Figure 4.prism" \
  --producer-metrics source_data/figure_04/barcode_detection_metrics.tsv \
  --output-dir results/figure_04/plotted_checkpoint
python3 scripts/figure_04/extract_plotted_prism.py --validate-only \
  --output-dir results/figure_04/plotted_checkpoint
```

The extractor reads the selected layout, checks all 333 metric values and their F1 arithmetic, verifies the Flexiplex f0/f8 selection and calculates the matched Friedman/Dunn comparisons. Use `--validate-only` with `source_data/figure_04/plotted_checkpoint` to check the tables already in this repository. [Schemas](../source_data/figure_04/schemas.json) define their fields.
