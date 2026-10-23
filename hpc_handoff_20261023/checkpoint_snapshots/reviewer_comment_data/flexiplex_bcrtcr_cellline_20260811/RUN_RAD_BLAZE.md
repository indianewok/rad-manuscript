# RAD and BLAZE read-level BCR/TCR analysis - cluster instructions

Goal: make the same per-barcode BCR/TCR counts for RAD and BLAZE that the
Flexiplex run already made. Then all 3 tools sit in one frame, and the
Figure 3G-H panels stop mixing the manuscript-era run with the new run.

## What to run

```bash
cd /dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811
bash run_rad_blaze_bcrtcr.sh both
```

Run `rad` or `blaze` instead of `both` to do one tool at a time.
Suggested resources: 32 cores, 64 GB, 6 hours.

Outputs land in
`reviewer_comment_data/rad_blaze_bcrtcr_cellline/`.

## Important: do not align the reads again

The BCR/TCR class of a read does not depend on the demultiplexing tool. All
tools read the same raw reads. The Flexiplex run already aligned every read
to the TRUST4 hg38 reference and wrote `rage_bcrtcr_hits.tsv` (739 MB) in
this folder. The script reuses that file. Aligning again wastes hours and
gives the same answer.

## What the script does

1. Runs `rad demux` with the benchmark parameters, and `-w` so RAD writes
   the debug FASTQ.
2. Runs `blaze` with `--expect-cells 4505` and `--output-fastq`.
3. Extracts per-read barcode assignments:
   - RAD: the FASTQ header holds `CB:Z` (final barcode) and `CR:Z` (raw
     barcode). RAD leaves `CR:Z` empty when the barcode needed no
     correction, so an empty `CR:Z` marks a native read. The `-F`/`-R`
     suffix comes off the read identifier.
   - BLAZE: the matched FASTQ header holds `CB:Z` (final barcode) and the
     read identifier between `#` and the last underscore.
     `putative_bc.csv` holds the raw barcode. A read is native when the raw
     barcode equals the final barcode.
4. Joins each read to its BCR/TCR class and its cell type, then writes the
   per-barcode and summary tables.

## Expected outputs per tool

- `RAD_bcrtcr_summary.tsv`, `BLAZE_bcrtcr_summary.tsv`
- `RAD_bcrtcr_data11.tsv`, `BLAZE_bcrtcr_data11.tsv`
- `RAD_per_barcode_bcrtcr.tsv`, `BLAZE_per_barcode_bcrtcr.tsv`
- `rad_per_read.tsv`, `blaze_per_read.tsv` (the intermediate join keys)

Corrected counts are rescued reads only, so native + corrected = total.
This matches the current Figure 3 sheets. The Flexiplex cluster run wrote
cumulative corrected counts instead, and that difference caused an error
once; this script writes the panel definition directly.

## Concordance checks

Compare the script's printed totals with the benchmark package
`wl_scan/20260730_rageseq_ERR3268991_cellline_control/analysis/demux_assignment_metrics.tsv`:

| Tool | Assigned unique reads | Ambiguous dropped |
|---|---:|---:|
| RAD | about 7,653,089 | about 63,560 |
| BLAZE | about 5,588,729 | 0 |

Report any difference greater than 1 percent. A small difference is normal
when the tool version differs. A large difference means a wrong parameter.

## Verified before delegation

The RAD extractor ran on a 200,000-read subset on a laptop. It read 70,419
records and split them into 25,862 native and 44,557 corrected, which
matches a direct count of the FASTQ headers. The BLAZE header format was
confirmed against a BLAZE 2.6.0 output already on the share.
