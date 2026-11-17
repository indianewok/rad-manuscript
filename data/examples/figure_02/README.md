# Figure 2 examples

## Compare read sequences and quality scores

[L_flatQ20_first2.fastq](L_flatQ20_first2.fastq) and [L_native2023_first2.fastq](L_native2023_first2.fastq) contain the same two ScTagger-L read sequences with uniform and model-generated qualities. Compare them with:

```bash
mkdir -p results
python3 scripts/revision/figures_124_steps/compare_fastq_sequences.py \
  data/examples/figure_02/L_flatQ20_first2.fastq \
  data/examples/figure_02/L_native2023_first2.fastq results/figure2_two_reads.tsv
```

The paired quality table follows the same physical reads across conditions. `barcode_ED` gives the edit distance from the known source barcode. Each quality column gives the mean across the 16-base barcode window. [Expected comparison](two_read_quality_comparison.tsv) · [Paired quality table](paired_quality_example.tsv)

## Score a barcode list

Score the `S_shift_p01_*.txt` tool lists against the 50 ScTagger-S source barcodes by exact sequence. The output gives TP, FP, FN, precision, recall and F1. [Source list](S_truth_barcodes.txt) · [Scoring script](../../../scripts/revision/figures_124_steps/score_whitelists.py) · [Expected metrics](S_shift_p01_metrics.tsv)

## Follow an assignment

| Tool | Extracted and assigned fields | Classification |
|---|---|---|
| RAD | [Assignment records](RAD_assignment_records_example.tsv) | [Classified records](RAD_assignment_classified_example.tsv) |
| BLAZE | [Assignment records](BLAZE_assignment_records_example.tsv) | [Classified records](BLAZE_assignment_classified_example.tsv) |
| Flexiplex | [Assignment records](Flexiplex_assignment_records_example.tsv) | [Classified records](Flexiplex_assignment_classified_example.tsv) |

Follow the original read ID, known source barcode, observed barcode and final target across a row. The [classification script](../../../scripts/revision/figures_124_steps/classify_assignment_preview.py) applies the tool's field definitions. The [Figure 2 guide](../../../docs/figure_02.md#read-classification) explains how original-read outputs are grouped and counted.

[Figure 2 guide](../../../docs/figure_02.md) · [Complete tables](../../../source_data/figure_02/) · [Fields and units](schema.json) · [Source files and records](provenance.json)
