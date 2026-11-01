# Figure 2 — synthetic barcode discovery and read assignment

Figure 2 compares barcode discovery and read assignment using ScTagger-L reads with known source barcodes. The source simulation contains 4,993,805 reads from 5,000 barcodes. Read headers identify the barcode of origin, allowing each final assignment to be scored directly against its source.

![Figure 2](../figures/figure_02/prism/figure_02.png)

[Figure legend](current_figure_legends.md) · [Source tables](../source_data/figure_02/) · [Worked examples](../data/examples/figure_02/) · [Nanopore2023 quality sweep](../source_data/figure_02/full_read_quality/) · [Nanopore2018 quality sweep](../source_data/figure_02/full_read_quality_2018/)

## Discovery software and parameters

| Tool | Version and source | Discovery settings |
|---|---|---|
| RAD | 1.0.2; `920addacdbf40b815e13a146226e8f4b14a58aaf` | `scan-wl -p CTACACGACGCTCTTCCGATCT -n 16 -e 0.3 -w 10x_3v3 -t 8 -k 10000 -v` |
| BLAZE | 2.6.0a0 | Expected cells 5,000; 3v3, minimum Q15, eight threads, `--no-emtpy-drops --no-demultiplexing`; native extraction cache passed to the pinned selector. |
| Flexiplex | 1.02.6 | `-d 10x3v3 -e 2 -p 8`; separate flank-distance-0 and flank-distance-8 tracks, followed by the global 3v3 filter. |

## Synthetic sequences and base qualities

The discovery input uses ScTagger nucleotide sequences and simulated errors with base qualities assigned from the Badread Nanopore2023 model. Quality generation uses Badread 0.4.1, Python 3.9.16, NumPy 1.23.5, and edlib 1.3.9. The ScTagger-L input contains 8,394,808,882 bases. Its uniform-Q20 and Nanopore2023 files have the same ordered headers and sequences, with sequence-identity SHA-256 `ca3073f0a44d03b40a5919e01e59a8df89ceceafa086ee7580fae2daa3bf2f61`.

All read positions first receive scores sampled from the model's overall distribution. The observed barcode is aligned to its known source sequence. Scores within a located 16-base barcode are then replaced with samples conditioned on the local alignment's matching bases and sequence errors. Reads without a located barcode retain the initial background scores.

The Nanopore2023 generator uses nominal seed `20260731`, adapter edit distance 7, boundary slop 8, a 16,777,216-score sampling tape, and four compression threads. The [environment and commands](../source_data/figure_02/generation_environment.tsv) and [generation contract](../source_data/figure_02/quality_generation_contract.json) define the random streams. Use the [recorded-seed adapter](../scripts/figure_02/generate_with_recorded_seed.py) when relocating model files so that the sampling tape retains its original seed.

The native Nanopore2023 input uses the generated quality scores. Its whole-dataset mean base quality is Q31.67 and its mean located-barcode quality is Q22.23. Assignment inputs are specified separately below.

The [paired FASTQ example](../data/examples/figure_02/) shows the same two read sequences with uniform-Q20 and sampled qualities:

```bash
mkdir -p results
python3 scripts/revision/figures_124_steps/compare_fastq_sequences.py \
  data/examples/figure_02/L_flatQ20_first2.fastq \
  data/examples/figure_02/L_native2023_first2.fastq results/figure2_two_reads.tsv
```

## Barcode discovery in panels B and C

Discovery uses the full chemistry catalog and each tool's barcode-selection procedure. The displayed condition is native Nanopore2023. Selected barcode sequences are compared exactly with the 5,000 source barcodes. True positives are selected source barcodes, false positives are selected barcodes outside the source set, and false negatives are source barcodes absent from the selected set.

```text
precision = TP / (TP + FP)
recall    = TP / (TP + FN)
F1        = 2TP / (2TP + FP + FN)
```

The [discovery source tables](../source_data/figure_02/discovery_metrics.tsv), [callset hashes](../source_data/figure_02/discovery_callset_manifest.tsv), and [barcode identities](../source_data/figure_02/discovery_barcode_identities.tsv.gz) connect the selected lists to the plotted metrics. Quality changes affect BLAZE's Q15 minimum-barcode-score filter. The selected RAD and Flexiplex settings depend on sequence, so their callsets are reused across quality offsets.

## Assignment runs and plotted barcode sets

These inputs and settings identify the assignment data shown in panels D–H.

| Plotted data | Tool and version | Input and assignment settings |
|---|---|---|
| RAD assignment panels | RAD 1.0.2; `24d5ce47e172222c96cd7dd19e94758d32aa5009` | Uniform Q20; 3v3 layout with a 12-base UMI; the same 5,000 truth barcodes supplied as both the global and custom lists; offensive correction, mutation limits 2/2, chunks of 5,000, 64 threads. |
| BLAZE assignment panels | BLAZE 2.6.0a0 matching-function replay | Native Nanopore2023 extractions; barcode distance 2, minimum Q0, 5,015 selected targets; seed-0 candidate order with new candidates appended lexically. |
| Flexiplex detected-list totals, correction pie, and panel H distribution | Flexiplex 1.02.6 with raw-barcode diagnostic output | Uniform Q20; 3v3, flank distance 8, barcode distance 2, 16 tool threads; 3,004 discovered targets and four compression threads. |
| Flexiplex per-barcode distributions in panels E and G | Flexiplex 1.02.6 with raw-barcode diagnostic output | Uniform Q20; `-d 10x3v3 -f 8 -e 2 -k TRUTH5000 -p 28`; all 5,000 source barcodes supplied, with four decompression and four compression threads. |

The [RAD native command](../source_data/figure_02/plotted_assignment/producing_evidence/RAD_command.sh), [input layout](../source_data/figure_02/plotted_assignment/producing_evidence/RAD_input_layout.csv) and [run identities](../source_data/figure_02/plotted_assignment/producing_evidence/) specify its input, binary and supplied barcode lists. The [Flexiplex source and diagnostic-output patch](../vendor/flexiplex-audit/) define the barcode fields used for classification. [Producer records](../source_data/figure_02/producing_evidence/) identify BLAZE's extraction cache and matching replay.

Panel D reports native-correct reads from the detected-list runs; its red Flexiplex increment is the additional native-correct recovery when the complete truth list is supplied. Panels E and G display per-barcode counts for the 5,000 truth targets. Their Flexiplex distributions use the supplied-truth-list run. Panel H uses the discovered Flexiplex list and the truth-supported BLAZE targets. The [per-panel tables](../source_data/figure_02/plotted_assignment/) identify each graph's assignment condition and barcode identities.

## Read classification

Original read identifiers link emitted assignments to the ScTagger source barcode. RAD provides the final barcode in `CB` and the extracted sequence in `CR`; an empty CR identifies native assignments. BLAZE raw extractions come from `putative_bc.csv`. Flexiplex's diagnostic table provides the raw and final barcodes, flank and barcode edit distances, and UMI.

A read contributes to assignment counts when it has exactly one emitted record. All records for an original read with multiple outputs are excluded, including repeated records assigned to the same target. Native and corrected assignments are separated using the raw and final barcode fields. An assignment is correct when its final barcode matches the read's known source barcode. The table below distinguishes reads without an emitted output from reads excluded for multiple outputs.

| Assignment state | RAD | BLAZE | Flexiplex detected list |
|---|---:|---:|---:|
| Native correct | 667,965 | 640,957 | 463,613 |
| Corrected correct | 1,944,306 | 1,881,358 | 1,398,700 |
| Corrected incorrect | 191,519 | 133,074 | 281,696 |
| Native incorrect | 571 | 764 | 381 |
| Multiple outputs excluded | 9,048 | 0 | 364 |
| Unassigned | 2,180,396 | 2,337,652 | 2,849,051 |

Each column partitions all 4,993,805 input reads. Panel F's correction-only pies use corrected-correct plus corrected-incorrect assignments as their denominator. The total bars in panels G and H use the corresponding corrected category. Per-barcode distributions retain zero counts for selected targets and blank entries for targets absent from a detected list. BLAZE's panel H distribution covers its 5,000 truth targets; assignments to its fifteen additional selected targets contribute to the total bar separately.

## Reproduce the RAD assignment table

The fixed-5,000 RAD run supplies a `record_audit.tsv.gz` table with the original read ID, known source barcode, observed barcode and assigned barcode. Recalculate the strict assignment states and all 5,000 target rows with:

```bash
python3 scripts/figure_02/summarize_plotted_rad_audit.py \
  --audit external_data/figure_02/RAD_record_audit.tsv.gz \
  --truth source_data/figure_02/plotted_assignment/L_truth_5000_barcodes.txt \
  --output-dir results/figure_02/RAD_assignment
```

The [RAD summary](../source_data/figure_02/plotted_assignment/RAD_assignment_summary.json), [state counts](../source_data/figure_02/plotted_assignment/RAD_assignment_states.tsv), and [per-target table](../source_data/figure_02/plotted_assignment/RAD_assignment_per_target.tsv) supply the corresponding calculation outputs. The per-panel Prism tables connect these outputs to the figure's distributions and totals. Extract those tables from a Prism project with:

```bash
python3 scripts/figure_02/extract_plotted_prism.py \
  --prism "external_data/prism/Figure 2.prism" \
  --output-dir results/figure_02/plotted_assignment
```

Rebuild and check the deposited source tables with:

```bash
python3 scripts/revision/figures_124.py build --project-root /path/to/rad_data --output-root .
python3 scripts/revision/figures_124.py validate --output-root .
```

[Table schemas](../source_data/figure_02/schemas.json) define the metrics and counting units. The image above shows the manuscript layout.
