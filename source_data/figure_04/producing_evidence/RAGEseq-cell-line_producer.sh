# RAGE-seq four-tool benchmark commands

Working directory:

`external_data/reviewer_comment_data/scratch_preservation_20260921/files/rageseq_four_tool_20260729`

All primary runs used 32 requested threads and 10x 3' v2 structure:
adapter `CTACACGACGCTCTTCCGATCT`, 16-nt barcode, and 10-nt UMI.

## RAD

```bash
/usr/bin/time -v -o runs/rad/scan/time.txt \
  external_data/temporary/rad-current-f005f43.8ChwC9/build-system/rad scan-wl \
  -i input/rageseq.fq.gz \
  -o runs/rad/scan/rageseq \
  -p CTACACGACGCTCTTCCGATCT -n 16 -e 0.3 \
  -w input/10x_3v2_full_whitelist.txt -t 32 -k 10000

/usr/bin/time -v -o runs/rad/demux/time.txt \
  external_data/temporary/rad-current-f005f43.8ChwC9/build-system/rad demux \
  -l three_prime -q input/rageseq.fq.gz \
  -g input/10x_3v2_full_whitelist.txt \
  -c runs/rad/scan/rageseq.txt \
  -R offensive -M 2 -m 2 -z 10000 \
  -o rageseq -d runs/rad/demux \
  -F runs/rad/demux/run.log -t 32
```

## BLAZE

```bash
cd runs/blaze
/usr/bin/time -v -o time.txt \
  external_data/reviewer_comment_data/scratch_preservation_20260921/files/blaze2_260a0_native_20260727/venv/bin/blaze \
  --expect-cells 4505 --10x-kit-version 3v2 \
  --threads 32 --max-edit-distance 2 \
  --output-prefix ./ --output-fastq matched_reads.fastq.gz \
  --overwrite ../../input/rageseq.fq.gz
```

## Flexiplex

Flexiplex 1.02.6's predefined `10x3v2` scheme uses the chemistry-native
flank tolerance `-f 8`; that run is the primary Flexiplex comparison.
The otherwise identical `-f 0` run is an explicit strict-flank sensitivity.
The commands below retain their original execution order and paths.

```bash
gzip -cd input/rageseq.fq.gz |
  external_data/temporary/flexiplex_release.GqgaKA/flexiplex/bin/flexiplex-linux \
  -d 10x3v2 -f 0 -p 32 \
  -n runs/flexiplex/f0_detection/rageseq

LD_LIBRARY_PATH=external_data/software/miniconda3/lib \
  external_data/software/miniconda3/bin/flexiplex-filter \
  --whitelist input/10x_3v2_full_whitelist.txt \
  --outfile runs/flexiplex/f0_detection/selected.tsv \
  runs/flexiplex/f0_detection/rageseq_barcodes_counts.txt

gzip -cd input/rageseq.fq.gz |
  external_data/temporary/flexiplex_release.GqgaKA/flexiplex/bin/flexiplex-linux \
  -d 10x3v2 -f 0 -p 32 \
  -k runs/flexiplex/f0_detection/selected.tsv \
  -n runs/flexiplex/f0_demux/rageseq |
  pigz -p 4 > runs/flexiplex/f0_demux/matched_reads.fastq.gz
```

The `-f 8` discovery, filtering, and demultiplexing commands were identical
except that `f0_*` paths and `-f 0` were replaced with `f8_*` and `-f 8`.

## FLAMESv2

FLAMES 2.6.0 was run through the Bioconductor container and its basilisk
environment with:

```bash
Rscript external_data/reviewer_comment_data/scratch_preservation_20260921/files/four_tool_benchmark_20260729/run_flamesv2_blaze_10x.R \
  input/rageseq.fq.gz runs/flamesv2 32 4505 3v2
```

The driver calls `FLAMES::blaze()` with `expect_cells=4505`,
`max-edit-distance=2`, `threads=32`, and the 10x 3v2 kit.

## Analysis

```bash
python3 scripts/analyze_callsets.py
python3 scripts/analyze_demux_assignments.py
python3 scripts/make_timing_summary.py
python3 scripts/plot_selection_umap.py
```

Wall times are descriptive shared-node timings. The four tools were run with
overlap to finish the biological benchmark promptly, so the measurements are
not an isolated performance ranking.
