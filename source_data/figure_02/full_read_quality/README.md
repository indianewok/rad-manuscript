# Nanopore2023 barcode quality across the complete dataset

The [full-data table with BLAZE F1](full_quality_with_blaze_f1.tsv) uses every
located barcode in the retained native Nanopore2023 FASTQ. The table describes
stored quality scores; no sequences, scores, or BLAZE calls were regenerated.

All **4,993,805 reads** were scanned. The means include **879,860 correct** and
**4,096,300 incorrect** barcode windows. The **17,645 reads with no located barcode**
are excluded from both means.

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

## Software and definitions

The original scores were generated with **Badread 0.4.1**, its pinned
**Nanopore2023 model**, and seed **20260731**. The full scan uses **edlib 1.3.9**
and the original barcode-location function, copied without changes. The
adapter maximum edit distance is **7** and the boundary-slop parameter is **8**.
The adapter sequence is `CTACACGACGCTCTTCCGATCT`; each barcode window is **16 bases**.
The function checks both orientations and uses the known barcode in the read
header to resolve its location.

**BLAZE 2.6.0a0** discovery uses `--expect-cells 5000`, `--10x-kit-version 3v3`,
and `--minQ 15`, with empty-droplet output and demultiplexing disabled. Its F1
values come from the existing full-data discovery results. See the
[Figure 2 tool registry](../../../docs/figure_02.md#versions-and-parameters-that-produced-these-data)
for exact build hashes and producing commands.

- **Correct:** the observed 16-base barcode exactly matches its known true
  barcode (`barcode_ED = 0`).
- **Incorrect:** the observed barcode has at least one sequence edit relative
  to its known true barcode (`barcode_ED > 0`). These are observed read windows,
  not BLAZE's final true-positive or false-positive barcode calls.
- **Unlocated:** the original locator returns no barcode window. These reads
  are counted separately and excluded from both quality means.

Each barcode mean includes all 16 bases, including correct bases within an
incorrect barcode. Each read has equal weight. The means are arithmetic means
of Phred scores, not averages of error probabilities. BLAZE instead filters on
the lowest score within its extracted barcode.

## Follow the calculation

1. Inspect the [first 20 actual read windows](first20_barcode_windows.tsv).
   Each row contains the true and observed barcode, edit distance, location,
   and all 16 native quality scores in the same orientation as the barcode.
2. Inspect [read counts by edit distance](barcode_edit_distance_counts.tsv)
   and the [native base-score counts by edit distance](barcode_quality_by_ed.tsv).
   These counts summarize every located barcode base and support exact group
   means without a sample or a new random draw.
3. For each negative shift, replace each score `q` with
   `max(1, min(50, q + shift))`. Native scores are used without any clipping.
   Sum `transformed_score * base_count` separately for edit distance zero and
   greater than zero. Divide each sum by that group's total number of bases.
   Because every window has 16 bases, this is also the mean of the per-read
   barcode means.
4. The [full quality summary](full_quality_summary.tsv) exposes both integer
   quality sums and their denominators. The
   [joined table](full_quality_with_blaze_f1.tsv) adds existing BLAZE TP, FP,
   FN, precision, recall, and `F1 = 2*TP / (2*TP + FP + FN)`.

The original 50,000-read sample remains the input to the paired distribution
panel. It is also a check on this full scan: all 12 means and the edit distance
for each sampled read must agree with the retained sample records.

## Reproduce from the retained native FASTQ

Run from the repository root in an environment with edlib 1.3.9:

```bash
python scripts/figure_02/summarize_full_barcode_quality.py \
  --fastq /path/to/shuffled_L_lr_synth.nanopore2023_truthbc.native_unadjusted.fq.gz \
  --output-dir /tmp/full_barcode_quality \
  --workers 7 \
  --sample-csv source_data/figure_02/paired_50000_barcode_mean_Q.csv.gz
```

The [scanner](../../../scripts/figure_02/summarize_full_barcode_quality.py)
streams the FASTQ once with bounded parallel workers. The separate
[locator](../../../scripts/figure_02/barcode_locator.py) records the exact
original source and function hashes. The [run receipt](run.json) records
input identities, software versions, counts, sample checks, and script hashes.
The Dartmouth [submission script](../../../scripts/figure_02/summarize_full_barcode_quality.sbatch)
uses eight CPUs on a verified CPU-only partition, with no GPUs.

The [independent validator](../../../scripts/figure_02/validate_full_barcode_quality.py)
recalculates the group means from integer histograms, compares the complete
quality histograms and read counts with the original records, and joins BLAZE's
discovery results. Its checks use the deposited
[original generation summary](source_generation_summary.tsv), not estimates
from the 50,000-read sample.

```bash
python scripts/figure_02/validate_full_barcode_quality.py \
  --scan-dir /tmp/full_barcode_quality \
  --generation-summary source_data/figure_02/full_read_quality/source_generation_summary.tsv \
  --output /tmp/full_barcode_quality/full_quality_with_blaze_f1.tsv \
  --report /tmp/full_barcode_quality/validation.json
```

The deposited [validation report](../../../validation/figure_02_full_barcode_quality.json)
records the checks on the published table and binds all inputs and outputs to
their SHA256 hashes.
