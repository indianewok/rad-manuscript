# Figure 2 examples

These files show how synthetic read headers, barcode lists and emitted assignment fields produce the metrics in the [Figure 2 guide](../../../docs/figure_02.md).

## Compare read sequences and quality scores

[L_flatQ20_first2.fastq](L_flatQ20_first2.fastq) and [L_native2023_first2.fastq](L_native2023_first2.fastq) contain the same two ScTagger-L read sequences with uniform and model-generated qualities. Compare them with:

```bash
mkdir -p results
python3 scripts/revision/figures_124_steps/compare_fastq_sequences.py \
  data/examples/figure_02/L_flatQ20_first2.fastq \
  data/examples/figure_02/L_native2023_first2.fastq results/figure2_two_reads.tsv
```

[two_read_quality_comparison.tsv](two_read_quality_comparison.tsv) shows the expected comparison. [paired_quality_example.tsv](paired_quality_example.tsv) follows the same physical reads across quality conditions; `barcode_ED` is the edit distance from the known source barcode, and each quality column is the mean across the 16-base barcode window.

## Score a barcode list

The [50-source-barcode list](S_truth_barcodes.txt) and `S_shift_p01_*.txt` tool lists form a complete small barcode-discovery example. [S_shift_p01_metrics.tsv](S_shift_p01_metrics.tsv) gives TP, FP, FN, precision, recall and F1. The [scoring script](../../../scripts/revision/figures_124_steps/score_whitelists.py) compares barcode sequences exactly.

## Follow an assignment

| Tool | Extracted and assigned fields | Classification |
|---|---|---|
| RAD | [Assignment records](RAD_assignment_records_example.tsv) | [Classified records](RAD_assignment_classified_example.tsv) |
| BLAZE | [Assignment records](BLAZE_assignment_records_example.tsv) | [Classified records](BLAZE_assignment_classified_example.tsv) |
| Flexiplex | [Assignment records](Flexiplex_assignment_records_example.tsv) | [Classified records](Flexiplex_assignment_classified_example.tsv) |

Follow the original read ID, known source barcode, observed barcode and final target across a row. The [classification script](../../../scripts/revision/figures_124_steps/classify_assignment_preview.py) applies the tool's field definitions. The [Figure 2 guide](../../../docs/figure_02.md#read-classification) explains how original-read outputs are grouped and counted.

The [schema](schema.json) defines fields and units. [Source identities](provenance.json) give file hashes and selected record numbers. [Complete source tables](../../../source_data/figure_02/) contain the full assignment and discovery results.
