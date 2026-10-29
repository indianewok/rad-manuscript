# ERR3268990 comparator commands

All methods use
10x 3' v2 structure (adapter `CTACACGACGCTCTTCCGATCT`, 16-nt cell barcode,
10-nt UMI) and maximum correction edit distance 2 where applicable.

## Input validation

The runner waits for exactly 24,090,380,952 bytes, checks the official ENA MD5
`23177cd143a521db1d7e41fd3e7d1981`, copies the validated FASTQ to local NVMe,
and requires 23,044,761 records and 24,041,380,990 bases from `seqkit stats`.

## BLAZE 2.6.0a0

The primary run uses the 10,433 exact deposited short-read capture list size.
A second run uses the paper's 6,027 downstream-QC count as an explicitly
labeled sensitivity analysis.

```bash
blaze --expect-cells 10433 --10x-kit-version 3v2 \
  --threads 16 --max-edit-distance 2 \
  --output-prefix ./ --output-fastq matched_reads.fastq.gz \
  --overwrite input/ERR3268990.fastq.gz
```

The sensitivity run uses `--expect-cells 6027` in a separate output directory.
Its `putative_bc.csv` is a symlink to the primary BLAZE run, and the command
omits `--overwrite`; BLAZE therefore skips duplicate putative-barcode
extraction and performs only sensitivity-specific whitelisting and
demultiplexing. Its standalone timing is incremental and excludes the shared
extraction cost.

## Flexiplex

The chemistry-default error-tolerant search (`-f 8`) is the primary Flexiplex
comparator. Strict discovery (`-f 0`) is retained as a sensitivity diagnostic.
Each setting performs discovery, whitelist filtering against the full 737,280
10x-v2 design, and demultiplexing:

```bash
gzip -cd input/ERR3268990.fastq.gz |
  flexiplex-linux -d 10x3v2 -f 0 -p 10 \
  -n runs/flexiplex/f0_detection/ERR3268990

flexiplex-filter \
  --whitelist input/10x_3v2_full_whitelist.txt \
  --outfile runs/flexiplex/f0_detection/selected.tsv \
  runs/flexiplex/f0_detection/ERR3268990_barcodes_counts.txt

gzip -cd input/ERR3268990.fastq.gz |
  flexiplex-linux -d 10x3v2 -f 0 -p 10 \
  -k runs/flexiplex/f0_detection/selected.tsv \
  -n runs/flexiplex/f0_demux/ERR3268990 |
  pigz -p 2 > runs/flexiplex/f0_demux/matched_reads.fastq.gz
```

The `-f 8` track uses the corresponding `f8_*` directories.

## FLAMESv2

FLAMES 2.6.0 is run in the Bioconductor 3.23 container through
`scripts/run_flamesv2_blaze_10x.R`. Its embedded BLAZE 2.5.1 receives
`expect_cells=10433`, kit `3v2`, correction distance 2, and 24 threads.
