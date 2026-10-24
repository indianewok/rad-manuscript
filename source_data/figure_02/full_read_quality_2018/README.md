# Nanopore2018 barcode quality across the complete dataset

The [full-data table](full_quality_with_blaze_f1.tsv) gives the correct and
incorrect read-barcode counts, their mean quality scores, and existing BLAZE
discovery F1 for every selected condition. The counts refer to observed barcode
windows in individual reads, not unique barcodes called by BLAZE.

All **4,993,805 reads** were scanned. The **17,645 reads with no located barcode**
are excluded from both quality groups. Counts below are individual read-barcode windows.

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

The group counts stay fixed because the sequence and its errors stay unchanged.
Differences are calculated before rounding. An em dash means no recorded BLAZE result.

## Software and input

The original quality scores used **Badread 0.4.1**, its pinned
[**Nanopore2018 model**](../models/nanopore2018.gz), and seed **20260731**.
The model's scores range from **Q1 to Q28**.
The retained full FASTQ is the **+1 condition**, containing scores Q2–Q29.
Subtracting 1 therefore recovers the original scores exactly: no clipping
occurred and no scores need to be sampled again.

The scan uses **edlib 1.3.9** and the original barcode-location function.
The adapter is `CTACACGACGCTCTTCCGATCT`, adapter maximum edit distance is **7**,
boundary slop is **8**, and each window contains **16 bases**. Both orientations
are checked. The known barcode in the read header resolves the barcode location.
The copied locator functions are identical to those in the original 2018
generator; the [independent review](../../../validation/figure_02_scanner_2018_independent_review.json)
records this check and the model's score support.

**BLAZE 2.6.0a0** discovery uses `--expect-cells 5000`,
`--10x-kit-version 3v3`, and `--minQ 15`, with empty-droplet output and
demultiplexing disabled. Its F1 values come from the original full-data results.
The [Figure 2 tool registry](../../../docs/figure_02.md#versions-and-parameters-that-produced-these-data)
gives exact build hashes and producing commands. An unshifted 2018 BLAZE result
is not recorded; its metric fields are blank, not zero.

## Follow the calculation

1. Inspect [the first 20 actual read windows](first20_barcode_windows.tsv).
   The true and observed sequences, edit distance, barcode location, and all
   16 recovered native quality scores are shown. Adding 1 to each listed score
   gives the corresponding stored input score.
2. Inspect [read counts by edit distance](barcode_edit_distance_counts.tsv)
   and [native quality counts by edit distance](barcode_quality_by_ed.tsv).
   Correct means edit distance zero; incorrect means one or more sequence edits.
   Unlocated reads are counted separately and excluded from both groups.
3. For each condition, add its shift to every native score. Every selected
   result remains within Q1–Q50, so clipping has no effect. Within each group,
   sum `score * base_count` and divide by the total number of barcode bases.
   All windows contain 16 bases, so this equals the average of the per-read
   barcode means. The [summary](full_quality_summary.tsv) exposes both integer
   quality sums and their denominators.
4. Join the existing BLAZE discovery counts and recompute
   `F1 = 2*TP / (2*TP + FP + FN)`. The read-level groups used for quality means
   are distinct from BLAZE's true-positive and false-positive barcode calls.

The mean difference is a comparison between two groups of reads. It is not a
fixed quality penalty assigned to each error. Because each group receives the
same unclipped shift, the difference between its means stays constant.

## Reproduce

Run from the repository root with edlib 1.3.9:

```bash
python scripts/figure_02/summarize_full_barcode_quality_2018.py \
  --fastq /path/to/shuffled_L_lr_synth.badread2018_truthbc.shift_p01.fq.gz \
  --input-shift 1 \
  --output-dir /tmp/full_barcode_quality_2018 \
  --workers 7 \
  --sample-csv source_data/figure_02/paired_50000_barcode_mean_Q.csv.gz
```

The [scanner](../../../scripts/figure_02/summarize_full_barcode_quality_2018.py)
reads the complete retained FASTQ once with bounded parallel workers. It checks
the score range of every input base and records separate hashes for the actual
stored qualities and their exact unshifted values. The [run receipt](run.json)
records counts, software versions, source identities, and sample checks.
The [staging receipt](../../../validation/figure_02_full_quality_2018_staging.json)
identifies the retained input and its compressed SHA256. The
[Dartmouth submission script](../../../scripts/figure_02/summarize_full_barcode_quality_2018.sbatch)
uses eight CPUs on a verified CPU-only partition, with no GPUs.

The [independent validator](../../../scripts/figure_02/validate_full_barcode_quality_2018.py)
checks the original [generation counts](source_generation_summary.tsv),
[full-stream identities](source_variant_invariants.tsv),
[native minimum-score histogram](source_native_barcode_min_q.tsv), all recorded
shifted minimum-Q15 pass counts and pooled means, and all 600,000 quality values
in the retained paired sample. The original pooled means were saved to six
decimal places; their comparison allows only that rounding difference.
The original generator did not save a base-score histogram, so the new
base-score histogram is checked for internal conservation and against those
independent records. The [validation report](../../../validation/figure_02_full_barcode_quality_2018.json)
states exactly which comparisons were possible.

```bash
python scripts/figure_02/validate_full_barcode_quality_2018.py \
  --scan-dir /tmp/full_barcode_quality_2018 \
  --generation-summary source_data/figure_02/full_read_quality_2018/source_generation_summary.tsv \
  --source-invariants source_data/figure_02/full_read_quality_2018/source_variant_invariants.tsv \
  --native-minimum-histogram source_data/figure_02/full_read_quality_2018/source_native_barcode_min_q.tsv \
  --output /tmp/full_barcode_quality_2018/full_quality_with_blaze_f1.tsv \
  --report /tmp/full_barcode_quality_2018/validation.json
```
