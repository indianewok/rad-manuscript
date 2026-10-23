# RAGE-seq false-whitelist (off-list) experiment - manuscript-era tabulation

Assembled 2026-08-17 from the manuscript-era runs. This dataset was NOT
re-run for the revision; unlike the ScTagger-L and LongBench packages
(20260813), the runs below predate the 2026-08-17 RAD adapter fix.

## Runs

- RAD: three demux runs dated 2025-08-28 (082825_rad_fp1/2/3), archived in
  Dropbox rad_paper_data_backup/121325_results/rad/demultiplexed/
  false_positive_wl/. Manuscript-era build. Per-barcode counts recomputed
  from each run's extracted_headers.csv.
- Flexiplex: three demux runs dated 2025-10-22 (offlist_v1/2/3), Flexiplex
  1.02.5, 10x3v2 preset, -e 2 (barcode) / flank 8, archived in Dropbox
  rad_paper_data_backup/103025_results/flexiplex/offlist/. The v3 FASTQ sits
  inside the offlist_v2 folder (original run redirect). Per-barcode counts
  computed from output FASTQ CB tags.
- BLAZE: raw runs are not archived anywhere we could find. Per-barcode counts
  were recovered from the manuscript file 041026_Figure_3_CMV.prism, sheet
  "Figure 3E, Off-list total barcode counts across three replicates".

## Design

Each replicate uses its OWN 4,505-barcode false whitelist ("dummy" list;
union across replicates: 13,426 barcodes). The original dummy_bcs_v1/2/3.txt
files were not archived; the lists in whitelists/ are reconstructed from the
union of assigned barcodes (complete: RAD and BLAZE assign reads to every
list member in every replicate).

## Row-identity proof

The manuscript 3E sheet has no barcode labels. Labels were recovered by
proving the row order: each replicate's RAD column, read in sheet order,
exactly equals the recomputed per-barcode counts sorted by barcode
(lexical). Rows therefore pair by lexical rank within each replicate,
the same convention as the 20260813 packages.

## Semantics

Counts in the wide and long tables are RECORD-LEVEL (one emitted assignment
record = one count), matching the manuscript's own RAD and BLAZE columns:

- RAD: 128/143/147 read IDs per replicate emit two records; retained.
- BLAZE: emits at most one record per read; the 3E sheet sums exceed the
  Figure 3D totals by 881/870/715 (3D counted reads, the sheet counts
  records including reads BLAZE reported without emitting).
- Flexiplex: 6,127/6,796/6,617 read IDs per replicate emit multiple records
  (multi-barcode splits). The main tables count records; the companion
  results/flexiplex_strict_per_barcode.tsv excludes those ambiguous read IDs
  (strict physical-read semantics, as in the 20260813 packages). The Figure
  3D Flexiplex totals are the tool's own log line "Number of reads where a
  barcode was found" (read-level).

## Files

- results/false_target_assigned_reads_wide.csv - RAD_rep1..3, BLAZE_rep1..3,
  Flexiplex_rep1..3; 4,505 rows; rows pair by lexical rank per replicate;
  no barcode column (mirrors the 20260813 wide CSV).
- results/false_target_assigned_reads_long.tsv - identity-bearing:
  barcode, replicate, rank, tool, count.
- results/flexiplex_strict_per_barcode.tsv - strict vs record counts.
- results/read_level_totals.csv - per-tool per-rep sums vs Figure 3D totals
  with accounting notes.
- whitelists/dummy_bcs_v1/2/3_reconstructed.txt - 4,505 barcodes each.
- scripts/ - the exact tabulation and assembly scripts.
- VALIDATION.tsv, SHA256SUMS.
