# Nanopore2018 barcode quality

The [complete-dataset table](full_quality_with_blaze_f1.tsv) combines correct
and incorrect barcode-window counts, mean quality scores and BLAZE discovery
F1 for each selected condition. The scan covers all 4,993,805 reads. The
17,645 reads without a located barcode are excluded from both quality groups.

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

Sequences and error patterns are retained across all shifts, so the group
counts remain fixed. Quality differences are calculated before rounding. The
unshifted BLAZE result is unrecorded and its metric fields are blank.

## Input and software

The quality scores were generated with Badread 0.4.1, its pinned
[Nanopore2018 model](../models/nanopore2018.gz) and seed `20260731`. The model
produces scores from Q1 to Q28. The retained complete FASTQ is the +1 condition,
with scores from Q2 to Q29. Subtracting one recovers the native scores exactly.

The scan uses edlib 1.3.9 and the original barcode locator. It searches both
orientations for adapter `CTACACGACGCTCTTCCGATCT`, with a maximum adapter edit
distance of 7 and boundary slop of 8. Each window contains 16 bases. The known
source barcode in the read header resolves its location. The
[locator check](../../../validation/figure_02_scanner_2018_independent_review.json)
verifies the copied functions against the original generator.

BLAZE 2.6.0a0 discovery used `--expect-cells 5000`, `--10x-kit-version 3v3` and
`--minQ 15`, with empty-droplet output and demultiplexing disabled. F1 values
come from the retained complete-dataset discovery results. The
[Figure 2 guide](../../../docs/figure_02.md) gives the build hashes and commands.

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

The [scanner](../../../scripts/figure_02/summarize_full_barcode_quality_2018.py)
reads the FASTQ once, checks every input score and records separate hashes for
the stored and recovered native qualities. The [run record](run.json) contains
counts, versions, source identities and sample checks. The
[input record](../../../validation/figure_02_full_quality_2018_staging.json)
identifies the compressed FASTQ and its SHA-256 hash. The
[Dartmouth submission script](../../../scripts/figure_02/summarize_full_barcode_quality_2018.sbatch)
requests eight CPUs.

The [validator](../../../scripts/figure_02/validate_full_barcode_quality_2018.py)
checks the [generation counts](source_generation_summary.tsv),
[complete-stream identities](source_variant_invariants.tsv),
[native minimum-score histogram](source_native_barcode_min_q.tsv), shifted
minimum-Q15 pass counts, pooled means and all 600,000 quality values in the
retained paired sample. Comparisons with original pooled means allow their
recorded six-decimal rounding. Base-score counts are checked for conservation
and agreement with these independent summaries.

```bash
python scripts/figure_02/validate_full_barcode_quality_2018.py \
  --scan-dir results/full_barcode_quality_2018 \
  --generation-summary source_data/figure_02/full_read_quality_2018/source_generation_summary.tsv \
  --source-invariants source_data/figure_02/full_read_quality_2018/source_variant_invariants.tsv \
  --native-minimum-histogram source_data/figure_02/full_read_quality_2018/source_native_barcode_min_q.tsv \
  --output results/full_barcode_quality_2018/full_quality_with_blaze_f1.tsv \
  --report results/full_barcode_quality_2018/validation.json
```

The [validation report](../../../validation/figure_02_full_barcode_quality_2018.json)
records the comparisons and their results.
