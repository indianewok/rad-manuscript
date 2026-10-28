# Flexiplex BCR/TCR cell-line analysis

This analysis was completed on 11 August 2026.

## Inputs and integrity

- WORK: `external_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811`
- FASTQ: `external_data/raw_fastq_datasets/rageseq.fq.gz`
  - 16,922,373,879 bytes; `gzip -t` exit 0 (10m26.619s)
  - SHA-256: `cfdba50a497dd4f6b24c2a4e730e297a09498ad5fe006f65eee01fa202bcdcec`
- selected.tsv: `external_data/reviewer_comment_data/wl_scan/20260730_rageseq_ERR3268991_cellline_control/runs/flexiplex/f8_detection/selected.tsv`
  - 3,259 lines / unique barcodes; 2,762,471 count sum; 69,318 bytes
  - SHA-256: `6efd9352872b06db447e540457757c3a5e50b00d654bfcd7c6e658e8786a41b9`
- `hg38_bcrtcr.fa` SHA-256: `615152a7481d0a68557ab0a84b735d8f25fc1ee9d5076af3b8d31aa7792dc3df`
- `rageseq_barcode_celltype_map.csv` SHA-256: `5d398b62c37b10e0a080f7e84321c11edb7fb0a1e2badef27209186e57e80f95`
- `join_flexiplex_bcrtcr.py` SHA-256: `5486f574028de3cfd62b505c41d8de2a99ae2c509f93c73ecc314e122bef0b99`

## Tools and execution

The run used Flexiplex 1.02.5 with the cached libstdc++ 13.2 runtime.

- Flexiplex 1.02.5: `external_data/software/miniconda3/pkgs/flexiplex-1.02.5-py39h2de1943_0/bin/flexiplex`
- minimap2 2.26-r1175: `external_data/software/miniconda3/pkgs/minimap2-2.26-he4a0461_1/bin/minimap2`
- Python 3.9.16: `external_data/software/miniconda3/bin/python3`
- gzip 1.9 (`/usr/bin/gzip`), GNU bash 4.4.20, GNU Awk 4.2.1
- 128 online CPUs; worker allocation: Flexiplex `-p 56`, minimap2 `-t 20` (76 workers)

The reproducible wrapper is `run_flexiplex_bcrtcr.sh`. Its pipeline is the
gzip → tee(process-substitution Flexiplex) → minimap2 → awk stream,
with explicit capture of both pipefail status and the asynchronous Flexiplex
status, followed by `python3 join_flexiplex_bcrtcr.py` inside WORK.

Pipeline start: `2026-08-11T18:39:24-04:00`.

Streaming completion: `2026-08-11T18:49:12-04:00` (wall 588 s).

Join completion: `2026-08-11T18:49:48-04:00`.

Minimap2 reported real time 587.054 s, CPU 875.318 s, peak RSS 1.337 GB.

Exit status: pipeline 0; Flexiplex 0; join 0.

## Counts and concordance

- Flexiplex raw reads processed: 20,346,396
- Flexiplex reads with a barcode: 6,665,219
- Flexiplex reads with more than one barcode (tool log): 45,612
- Sidecar assignment records: 6,755,575
- Sidecar unique read IDs: 6,665,219
- Ambiguous read IDs dropped by join: **69,988**
- Assigned unique read IDs after ambiguity removal: **6,595,231**
- Reduced minimap2 hits: 16,233,872 rows / 11,467,989 unique read IDs
  - BCR target rows: 10,459,673; TCR target rows: 5,774,199; other: 0
- Corrected summary total: 6,595,231 (BCR 2,985,039; TCR 1,126,957; unmapped 2,483,235)
- Native summary total: 3,052,826 (BCR 1,418,603; TCR 536,531; unmapped 1,097,692)
- Unique alignment rate: 56.3637% of raw reads
- Barcode-found rate: 32.7587% of raw reads (assigned-unique rate 32.4147%)

Validation found zero malformed sidecar/hit rows, zero nonnumeric edit or
match fields, summary 25 lines (header + 24 cells), Data-11 shape 5 lines,
and per-barcode table 3,260 lines (header + 3,259 selected barcodes).

## Output hashes

See `SHA256SUMS.txt` for the input, staged-reference, script, log, marker, and
result hashes; `sha256sum -c SHA256SUMS.txt` passed for every listed file. Main
result files:

- `rage_flex_f8_full_reads_barcodes.txt`
- `rage_bcrtcr_hits.tsv`
- `flexiplex_bcrtcr_summary.tsv`
- `flexiplex_bcrtcr_data11_shape.tsv`
- `flexiplex_per_barcode_bcrtcr.tsv`
- `flex_full.log`, `mm2_full.log`, `join_flexiplex_bcrtcr.stdout`
