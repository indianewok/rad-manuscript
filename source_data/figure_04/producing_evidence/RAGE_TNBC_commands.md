# RAGE-seq lymph-node commands (ERR3268990)

Figure 4 uses BLAZE **2.6.0a0** with **10,433 expected cells** and Flexiplex **1.02.6** with **`-f 8`**. The [software record](RAGEseq-TNBC-LN_tool_provenance.tsv) identifies their executables and filter. Both use the 10x 3′ v2 structure: adapter `CTACACGACGCTCTTCCGATCT`, a 16-nt barcode, a 10-nt UMI and maximum barcode-correction distance two.

The complete FASTQ contains 23,044,761 records and 24,041,380,990 sequence bases. Its compressed size is 24,090,380,952 bytes and its ENA MD5 is `23177cd143a521db1d7e41fd3e7d1981`.

## BLAZE

The 10,433 expected cells come from the deposited short-read capture list.

```bash
blaze --expect-cells 10433 --10x-kit-version 3v2 \
  --threads 16 --max-edit-distance 2 \
  --output-prefix ./ --output-fastq matched_reads.fastq.gz \
  --overwrite input/ERR3268990.fastq.gz
```

The 6,027-cell condition uses `--expect-cells 6027`, the downstream-QC cell count, in its own output directory. Its `putative_bc.csv` links to the 10,433-cell extraction table. Omitting `--overwrite` reuses that table for whitelisting and demultiplexing; the recorded runtime for this condition covers those two stages.

## Flexiplex

Each flank-distance setting performs discovery, filtering against the full 737,280-barcode 10x 3v2 catalog, and selected-list demultiplexing. The commands below show the f0 condition:

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

For the f8 condition, use `-f 8` and the corresponding `f8_*` directories. Figure 4 uses f8, selected by its higher recorded F1 score.

## FLAMESv2 workflow

FLAMES 2.6.0 uses the Bioconductor 3.23 container and `scripts/run_flamesv2_blaze_10x.R`. Its embedded BLAZE 2.5.1 receives `expect_cells=10433`, kit `3v2`, correction distance two and 24 threads.
