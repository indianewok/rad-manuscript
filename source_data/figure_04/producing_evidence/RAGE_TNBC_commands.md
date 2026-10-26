# ERR3268990 four-tool benchmark commands

The executable orchestration is in `run_after_download.sh`. All methods use
10x 3' v2 structure (adapter `CTACACGACGCTCTTCCGATCT`, 16-nt cell barcode,
10-nt UMI) and maximum correction edit distance 2 where applicable.

Runs used local NVMe storage and two scheduling waves. The first wave ran
RAD, BLAZE and Flexiplex discovery; the second ran the BLAZE 6,027-cell
sensitivity analysis and FLAMES. Per-tool thread counts appear in the commands
below, and the original resource allocation is recorded in
`analysis/resource_budget.tsv` within the producing project.

## Input validation

The runner waits for exactly 24,090,380,952 bytes, checks the official ENA MD5
`23177cd143a521db1d7e41fd3e7d1981`, copies the validated FASTQ to local NVMe,
and requires 23,044,761 records and 24,041,380,990 bases from `seqkit stats`.

## RAD

```bash
rad scan-wl \
  -i input/ERR3268990.fastq.gz \
  -o runs/rad/scan/ERR3268990 \
  -p CTACACGACGCTCTTCCGATCT -n 16 -e 0.3 \
  -w input/10x_3v2_full_whitelist.txt -t 16 -k 10000

rad demux \
  -l three_prime -q input/ERR3268990.fastq.gz \
  -g input/10x_3v2_full_whitelist.txt \
  -c runs/rad/scan/ERR3268990.txt \
  -R offensive -M 2 -m 2 -z 10000 \
  -o ERR3268990 -d runs/rad/demux \
  -F runs/rad/demux/run.log -t 16
```

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

## Analysis

```bash
python3 scripts/analyze_callsets.py
python3 scripts/analyze_blaze_highq_mechanism.py
python3 scripts/analyze_demux_assignments.py
python3 scripts/analyze_blaze_assignment_nondeterminism.py
python3 scripts/analyze_blaze_strict_redirect_seed_robustness.py \
  --workers 16 --seed-count 32
python3 scripts/audit_blaze_raw_to_corrected.py \
  --matched-fastq runs/blaze/matched_reads.fastq.gz \
  --putative-csv runs/blaze/putative_bc.csv \
  --truth input/official_shortread_barcodes_10433.txt \
  --design-whitelist input/10x_3v2_full_whitelist.txt \
  --selected-whitelist runs/blaze/whitelist.csv \
  --truth-labels input/Lymph_node_official_barcodes_labels.tsv.gz \
  --output analysis/blaze_raw_to_corrected_metrics.tsv \
  --examples analysis/blaze_raw_valid_to_valid_examples.tsv \
  --label-transitions \
    analysis/blaze_raw_valid_to_valid_label_transitions.tsv \
  --barcode-transitions \
    analysis/blaze_raw_valid_to_valid_barcode_transitions.tsv
python3 scripts/audit_rad_raw_to_corrected.py \
  --fastq runs/rad/demux/ERR3268990.fq.gz \
  --truth input/official_shortread_barcodes_10433.txt \
  --design-whitelist input/10x_3v2_full_whitelist.txt \
  --selected-whitelist runs/rad/scan/ERR3268990.txt \
  --truth-labels input/Lymph_node_official_barcodes_labels.tsv.gz \
  --output analysis/rad_raw_to_corrected_metrics.tsv \
  --examples analysis/rad_raw_valid_to_valid_examples.tsv \
  --label-transitions \
    analysis/rad_raw_valid_to_valid_label_transitions.tsv
python3 scripts/audit_rad_output_integrity.py
python3 scripts/analyze_endpoint_redirects.py
python3 scripts/analyze_clone5_cross_method.py
python3 scripts/summarize_flexiplex_edit_distances.py
python3 scripts/make_timing_summary.py
python3 scripts/plot_benchmark_summary.py
python3 scripts/validate_benchmark.py
scripts/package_compact_results.sh
```

Runs within each wave shared a compute node. Timing records include this
concurrent workload. The 6,027-cell BLAZE timing measures whitelist selection
and demultiplexing after reuse of the primary run's putative-barcode extraction.
