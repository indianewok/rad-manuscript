# Figure 1 — RAD workflow and computational efficiency

Figure 1 introduces RAD’s barcode detection and demultiplexing workflow, compares runtime and memory use on complete LongBench inputs, and examines barcode counts in Visium HD spatial bins.

![Figure 1 exported from Prism](../figures/figure_01/prism/figure_01.png)

[Prism source and export details](../manifests/prism_exports.json).

## Workflow and software

The [algorithm crosswalk](../source_data/figure_01/algorithm_crosswalk.tsv) links each workflow stage to RAD source commit `cb6991705ac0e9c93a108fd439aa0357834cc701`. The timing experiment used the following builds and settings.

| Tool | Version and source | Main settings |
|---|---|---|
| RAD | 1.0.2; `4acbe004ba11b150d6832395452632f367a6e6c1` | Detection: adapter `CTACACGACGCTCTTCCGATCT`, 16-base barcode, maximum error 0.1, 3v3 catalog, chunks of 10,000. Demultiplexing: 3v3 layout, global catalog and detected whitelist, offensive correction, both mutation limits 2, minimum length 85, chunks of 5,000. |
| BLAZE | 2.5.0; `11994f9c12a6664dfe1679576aaca19b6bfd35c1` | Detection: `--force-cells 10000` for SN-ONT and `--expect-cells 5000` for SC-PB; 3v3, minimum Q15, edit distance 2, batch size 1,000. Demultiplexing: `--no-whitelisting --known-bc-list` with the detected whitelist. `PYTHONHASHSEED=0`; SC-PB uses the saved FIFO launcher. |
| Flexiplex | 1.02.6; `d84c8ae4f3865052f2b5ecec816949b94682f302` | Discovery: flank distance 0 and the pinned global 3v3 filter. Demultiplexing: `-d 10x3v3 -e 2 -f 8 -k SELECTED`; one compression thread. |

The [run registry](../manifests/figures_124_tool_parameters.tsv) contains all 108 accepted phase commands, executable and whitelist hashes, layouts, and thread settings. [Software and resources](../source_data/figure_01/software_and_resources.tsv) identifies the binaries and reference files.

## Runtime and memory

The complete SN-ONT and SC-PB inputs contain 119,016,231 and 195,242,483 reads, respectively. Each tool ran with 4, 16, and 64 tool threads, with three repetitions per condition on AMD EPYC 7543 nodes. Each demultiplexing run used the whitelist from its corresponding detection run.

For each dataset, tool, thread count, and repetition, total wall time is the sum of detection and demultiplexing time. Peak process memory is the larger of the two GNU-time maximum resident set sizes, converted from KiB to decimal GB:

```text
wall hours = (detection seconds + demultiplexing seconds) / 3,600
peak GB = max(detection maxRSS, demultiplexing maxRSS) × 1,024 / 1,000,000,000
```

The 108 accepted phase records form 54 paired repetitions. Means and sample standard deviations use the three repetitions in each condition. At 16 threads, mean total times are 1.75, 7.24, and 9.08 hours for RAD, BLAZE, and Flexiplex on SN-ONT, and 1.49, 3.04, and 2.01 hours on SC-PB.

The [example records](../data/examples/figure_01/) contain the GNU-time logs, commands, completion markers, and statuses for SN-ONT/RAD/4 threads/repetition 1. Parse those logs and combine the complete phase table with:

```bash
python3 scripts/revision/figures_124_steps/read_gnu_time.py \
  data/examples/figure_01/raw_timing/whitelist_detection/metrics.tsv \
  data/examples/figure_01/raw_timing/demultiplexing/metrics.tsv \
  --output /tmp/figure1_parsed_time.tsv

python3 scripts/revision/figures_124_steps/combine_timing.py \
  source_data/figure_01/accepted_phase_records.tsv /tmp/figure1_all54_totals.tsv
```

Expected outputs are [parsed measurements](../data/examples/figure_01/parsed_gnu_time.tsv), [combined repetitions](../source_data/figure_01/combined_replicates.tsv), and [timing summaries](../source_data/figure_01/timing_summary.tsv). The [raw-source registry](../source_data/figure_01/timing_raw_source_registry.tsv) records every contributing file. Reconstruction joins the preserved timing directory with the original scratch completion records through a temporary symlink directory, verifies duplicate files, and runs the original [collector](../scripts/revision/figures_124_collect_timing.py).

## Visium HD counts and spatial bins

The spatial analysis uses 16 µm bins. The selected wide matrix contains whitelist-detection counts. Its four flow-cell totals match the original valid-pair tables: PBC44593, 45,979,761; PBC44760, 39,268,207; PBC49262, 41,679,323; and PBC52788, 47,990,983. Demultiplexing counts describe a later processing stage; for PBC44593 they total 67,872,744. The [count definition](../source_data/figure_01/producing_evidence/HD_selected_count_definition.json), [stage counts](../source_data/figure_01/hd_stage_counts.tsv), and [stage differences](../source_data/figure_01/hd_stage_differences.tsv) identify these quantities.

The matrix contains 175,561 bins in a complete 419 × 419 grid. Its 123,658 in-tissue bin identifiers match the saved Space Ranger filtered barcode set; the complete grid also matches the raw barcode set. Space Ranger used converted Nanopore data. The large matrix is stored as `checkpoints/figure_01/sample_bin_matrix_16um.csv.gz`; its source hash is recorded in the [build report](../validation/figures_124_build.json).

Reconstruct the grid and verify its tissue mask from the deposited identifiers:

```bash
python3 scripts/revision/figures_124_steps/recover_hd_grid.py \
  --input source_data/figure_01/hd_RAD_bins.tsv \
  --raw-barcodes source_data/figure_01/hd_16um_raw_barcodes.tsv.gz \
  --filtered-barcodes source_data/figure_01/hd_16um_filtered_barcodes.tsv.gz \
  --output /tmp/tissue_positions_16um_reconstructed.csv \
  --report /tmp/figure1_grid_receipt.json
```

[Eight example bins](../data/examples/figure_01/hd_grid_example.tsv) show the grid and tissue-mask fields. [Grid validation](../validation/figures_124_hd_grid_reconstruction.json) and [reference hashes](../source_data/figure_01/hd_grid_reference_sources.json) record the complete comparisons. To reconstruct the shared-scale spatial triptych, the remaining required inputs are the Seurat `nCount_Spatial` values and the code and RAD invocation that created the barcode-to-bin matrix.

## Reproduction commands

With the project data mounted, rebuild the tables and verify the HD totals:

```bash
python3 scripts/revision/figures_124.py build --project-root /path/to/rad_data --output-root .
python3 scripts/revision/figures_124_hd_lineage.py --project-root /path/to/rad_data --output-root .
```

For local numerical checks and plots from the deposited tables:

```bash
python3 scripts/revision/figures_124.py validate --output-root .
python3 scripts/revision/figures_124.py render --output-root .
```

The shared commands also process Figures 2 and 4. [Table schemas](../source_data/figure_01/schemas.json) define units and keys; [portable validation](../validation/figures_124_portable.json) records the numerical comparisons.
