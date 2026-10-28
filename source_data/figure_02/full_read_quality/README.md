# Nanopore2023 barcode quality

The [complete-dataset table](full_quality_with_blaze_f1.tsv) combines mean
barcode quality with BLAZE discovery F1 for each selected shift. The scan covers
all 4,993,805 reads in the retained Nanopore2023 FASTQ: 879,860 contain a correct
barcode window, 4,096,300 contain an incorrect window, and 17,645 have no located
barcode. Unlocated reads are excluded from both quality means.

| Quality shift | Correct barcode mean Q | Incorrect barcode mean Q | Q difference | BLAZE F1 |
|---|---:|---:|---:|---:|
| −17 | 16.69 | 7.49 | 9.21 | 0.0669 |
| −16 | 17.56 | 7.93 | 9.63 | 0.1668 |
| −15 | 18.44 | 8.39 | 10.05 | 0.3517 |
| −14 | 19.33 | 8.87 | 10.45 | 0.5813 |
| −12 | 21.13 | 9.90 | 11.22 | 0.9007 |
| −11 | 22.04 | 10.45 | 11.58 | 0.9607 |
| −9 | 23.89 | 11.66 | 12.23 | 0.9935 |
| −7 | 25.77 | 13.03 | 12.74 | 0.9954 |
| −6 | 26.73 | 13.80 | 12.93 | 0.9943 |
| −5 | 27.69 | 14.63 | 13.06 | 0.9984 |
| −4 | 28.65 | 15.51 | 13.14 | 0.9980 |
| Unshifted | 33.61 | 19.78 | 13.83 | 0.9985 |

## Input and software

The quality scores were generated with Badread 0.4.1, the pinned Nanopore2023
model and seed `20260731`. The scan uses edlib 1.3.9 and the original barcode
locator. It searches both orientations for adapter `CTACACGACGCTCTTCCGATCT`,
using a maximum adapter edit distance of 7 and boundary slop of 8. Each barcode
window contains 16 bases. The known source barcode in the read header resolves
its location.

BLAZE 2.6.0a0 discovery used `--expect-cells 5000`, `--10x-kit-version 3v3` and
`--minQ 15`, with empty-droplet output and demultiplexing disabled. F1 values are
calculated from the retained complete-dataset discovery results. The
[Figure 2 guide](../../../docs/figure_02.md) gives the build hashes and commands.

## Calculation

A correct barcode window has edit distance zero from its known source barcode;
an incorrect window has one or more sequence edits. Quality means include all
16 bases of each window, with equal weight per read. These are arithmetic means
of Phred scores. BLAZE applies its quality filter to the minimum score within
its extracted barcode.

The [first 20 windows](first20_barcode_windows.tsv) show the source and observed
sequences, edit distance, location and all 16 native quality scores. The
[read counts](barcode_edit_distance_counts.tsv) and
[base-score histogram](barcode_quality_by_ed.tsv) summarize the complete dataset
by edit distance.

For each shift, transform every native score `q` as
`max(1, min(50, q + shift))`. The unshifted condition uses the native scores.
Within each barcode group, sum `transformed_score × base_count` and divide by
the total number of bases. The [quality summary](full_quality_summary.tsv)
records the integer sums and denominators. The
[joined results](full_quality_with_blaze_f1.tsv) add BLAZE TP, FP, FN, precision,
recall and `F1 = 2 × TP / (2 × TP + FP + FN)`.

The paired distribution panel uses the retained 50,000-read sample. Its edit
distances and all 12 quality conditions are checked against the complete scan.

## Reproduce the analysis

Run from the repository root with edlib 1.3.9:

```bash
mkdir -p results
python scripts/figure_02/summarize_full_barcode_quality.py \
  --fastq /path/to/shuffled_L_lr_synth.nanopore2023_truthbc.native_unadjusted.fq.gz \
  --output-dir results/full_barcode_quality \
  --workers 7 \
  --sample-csv source_data/figure_02/paired_50000_barcode_mean_Q.csv.gz
```

The [scanner](../../../scripts/figure_02/summarize_full_barcode_quality.py)
streams the FASTQ once. The [locator](../../../scripts/figure_02/barcode_locator.py)
records its original source and function hashes. The [run record](run.json)
contains input identities, versions, counts and sample checks. The
[Dartmouth submission script](../../../scripts/figure_02/summarize_full_barcode_quality.sbatch)
requests eight CPUs.

The [validator](../../../scripts/figure_02/validate_full_barcode_quality.py)
recalculates group means from integer histograms, compares complete quality
histograms and read counts with the
[original generation summary](source_generation_summary.tsv), and joins the
BLAZE discovery results:

```bash
python scripts/figure_02/validate_full_barcode_quality.py \
  --scan-dir results/full_barcode_quality \
  --generation-summary source_data/figure_02/full_read_quality/source_generation_summary.tsv \
  --output results/full_barcode_quality/full_quality_with_blaze_f1.tsv \
  --report results/full_barcode_quality/validation.json
```

The [validation report](../../../validation/figure_02_full_barcode_quality.json)
records the comparisons and SHA-256 hashes of the inputs and outputs.
