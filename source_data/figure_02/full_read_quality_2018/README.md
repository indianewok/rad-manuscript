# Nanopore2018 barcode quality

The scan covers all 4,993,805 Nanopore2018 reads. Quality means use reads
with a located barcode and exclude 17,645 reads. [Complete dataset](full_quality_with_blaze_f1.tsv)

## Software and input settings

The quality scores were generated with Badread 0.4.1, its pinned
[Nanopore2018 model](../models/nanopore2018.gz) and seed `20260731`. The model
produces scores from Q1 to Q28. The input FASTQ is the +1 condition,
with scores from Q2 to Q29. Subtracting one recovers the native scores exactly.

The scan uses edlib 1.3.9 and the [barcode locator](../../../scripts/figure_02/barcode_locator.py). It searches both
orientations for adapter `CTACACGACGCTCTTCCGATCT`, with a maximum adapter edit
distance of 7 and boundary slop of 8. Each window contains 16 bases. The known
source barcode in the read header resolves its location.

BLAZE 2.6.0a0 discovery used `--expect-cells 5000`, `--10x-kit-version 3v3` and
`--minQ 15`, with empty-droplet output and demultiplexing disabled. [Figure 2 discovery commands](../../../docs/figure_02.md#discovery-software-and-parameters)

## Quality means and BLAZE F1

| Quality shift | Correct reads | Incorrect reads | Correct mean Q | Incorrect mean Q | Q difference | BLAZE F1 |
|---|---:|---:|---:|---:|---:|---:|
| +1 | 879,860 | 4,096,300 | 16.465 | 13.635 | 2.830 | 0.0854 |
| +2 | 879,860 | 4,096,300 | 17.465 | 14.635 | 2.830 | 0.3346 |
| +3 | 879,860 | 4,096,300 | 18.465 | 15.635 | 2.830 | 0.7439 |
| +4 | 879,860 | 4,096,300 | 19.465 | 16.635 | 2.830 | 0.9585 |
| +5 | 879,860 | 4,096,300 | 20.465 | 17.635 | 2.830 | 0.9538 |
| +6 | 879,860 | 4,096,300 | 21.465 | 18.635 | 2.830 | 0.9914 |
| +8 | 879,860 | 4,096,300 | 23.465 | 20.635 | 2.830 | 0.9874 |
| +10 | 879,860 | 4,096,300 | 25.465 | 22.635 | 2.830 | 0.9730 |
| +11 | 879,860 | 4,096,300 | 26.465 | 23.635 | 2.830 | 0.9538 |
| +12 | 879,860 | 4,096,300 | 27.465 | 24.635 | 2.830 | 0.9476 |
| +13 | 879,860 | 4,096,300 | 28.465 | 25.635 | 2.830 | 0.9428 |
| Unshifted | 879,860 | 4,096,300 | 15.465 | 12.635 | 2.830 | — |

Sequences and error patterns are identical across shifts, so the group counts remain fixed. Quality differences are calculated before rounding. The unshifted row reports quality statistics with blank BLAZE metric fields.

## Calculation

A correct barcode window has edit distance zero from its known source barcode;
an incorrect window has one or more sequence edits. The
[first 20 windows](first20_barcode_windows.tsv) show both sequences, edit distance,
location and all 16 recovered native scores. Adding one to those scores gives
the corresponding stored input qualities.

The [read counts](barcode_edit_distance_counts.tsv) and
[native base-score histogram](barcode_quality_by_ed.tsv) summarize the complete
dataset by edit distance. Add each selected shift to every native score. All
results remain within Q1–Q50. Within each barcode group, sum
`shifted_score × base_count` and divide by the total number of barcode bases.
All windows contain 16 bases, so each read has equal weight. The
[quality summary](full_quality_summary.tsv) records the integer sums and
denominators.

Join the BLAZE discovery counts and calculate
`F1 = 2 × TP / (2 × TP + FP + FN)`. The quality groups describe individual read
windows; TP, FP and FN describe the discovered barcode set. Applying the same
shift to both quality groups preserves the difference between their means.

## Reproduce the analysis

Run from the repository root with edlib 1.3.9:

```bash
mkdir -p results
python scripts/figure_02/summarize_full_barcode_quality_2018.py \
  --fastq /path/to/shuffled_L_lr_synth.badread2018_truthbc.shift_p01.fq.gz \
  --input-shift 1 \
  --output-dir results/full_barcode_quality_2018 \
  --workers 7 \
  --sample-csv source_data/figure_02/paired_50000_barcode_mean_Q.csv.gz
```

The scan reads the FASTQ once, checks every score and records separate hashes for
the stored and recovered native qualities. [Run record](run.json) · [Eight-CPU submission script](../../../scripts/figure_02/summarize_full_barcode_quality_2018.sbatch)

Verify the stream fingerprints, base-score totals, shifted Q15 pass counts and
all 600,000 quality values in the paired sample. Pooled means are checked to six
decimal places. [Generation counts](source_generation_summary.tsv) · [Stream fingerprints](source_variant_invariants.tsv) · [Native minimum-score histogram](source_native_barcode_min_q.tsv)

```bash
python scripts/figure_02/validate_full_barcode_quality_2018.py \
  --scan-dir results/full_barcode_quality_2018 \
  --generation-summary source_data/figure_02/full_read_quality_2018/source_generation_summary.tsv \
  --source-invariants source_data/figure_02/full_read_quality_2018/source_variant_invariants.tsv \
  --native-minimum-histogram source_data/figure_02/full_read_quality_2018/source_native_barcode_min_q.tsv \
  --output results/full_barcode_quality_2018/full_quality_with_blaze_f1.tsv \
  --report results/full_barcode_quality_2018/validation.json
```
