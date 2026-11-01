# Figure 1 — RAD workflow and computational efficiency

Figure 1 introduces RAD's read-layout model, measures the time and memory required for barcode discovery and demultiplexing, and applies the workflow to Visium HD spatial reads. The runtime comparison uses the complete LongBench single-nucleus ONT and single-cell PacBio inputs.

![Figure 1](../figures/figure_01/prism/figure_01.png)

[Figure legend](current_figure_legends.md) · [Source tables](../source_data/figure_01/) · [Worked examples](../data/examples/figure_01/)

## Software and benchmark settings

| Tool | Version and source | Settings |
|---|---|---|
| RAD | 1.0.2; `4acbe004ba11b150d6832395452632f367a6e6c1` | Discovery: adapter `CTACACGACGCTCTTCCGATCT`, 16-base barcode, maximum error 0.1, 3v3 catalog, chunks of 10,000. Demultiplexing: 3v3 layout, global catalog and discovered shortlist, offensive correction, both mutation limits 2, minimum length 85, chunks of 5,000. |
| BLAZE | 2.5.0; `11994f9c12a6664dfe1679576aaca19b6bfd35c1` | Discovery: `--force-cells 10000` for SN-ONT and `--expect-cells 5000` for SC-PB; 3v3, minimum Q15, edit distance 2, batch size 1,000. Demultiplexing: `--no-whitelisting --known-bc-list` with the discovered shortlist. `PYTHONHASHSEED=0`; SC-PB uses the FIFO launcher in the run records. |
| Flexiplex | 1.02.6; `d84c8ae4f3865052f2b5ecec816949b94682f302` | Discovery: flank distance 0 followed by the global 3v3 filter. Demultiplexing: `-d 10x3v3 -e 2 -f 8 -k SELECTED`; one compression thread. |

The [software and resource table](../source_data/figure_01/software_and_resources.tsv) identifies the binaries, catalogs, references, and input files.

## Read processing workflow

RAD reads a layout CSV that specifies static sequences, barcodes, UMIs, and transcript segments in their 5′-to-3′ order. Static sequences anchor extraction in both read orientations. Dataset-specific alignment thresholds and relative element positions support reads with missing terminal adapters or poly-tails. Barcode discovery selects a cell-barcode shortlist from the count distribution. Demultiplexing then extracts the barcode and UMI, applies barcode correction, and writes the annotated transcript sequence.

The [algorithm crosswalk](../source_data/figure_01/algorithm_crosswalk.tsv) and [barcode-processing reference](../source_data/figure_01/pinned_algorithm_audit.md) explain these stages at RAD commit `cb6991705ac0e9c93a108fd439aa0357834cc701`. The table above identifies the timed executables.

## Runtime and memory calculation

The SN-ONT and SC-PB inputs contain 119,016,231 and 195,242,483 reads, respectively. Each tool ran with 4, 16, and 64 tool threads, with three repetitions per condition on AMD EPYC 7543 nodes. Discovery and demultiplexing were timed separately. Each demultiplexing run used the shortlist from its corresponding discovery run.

GNU time recorded elapsed time and maximum resident set size for each phase. Flexiplex discovery includes its extraction and filtering steps. Total processing time is the sum of discovery and demultiplexing time; peak process memory is the larger of the two phase maxima. Memory is converted from KiB to decimal GB:

```text
wall hours = (discovery seconds + demultiplexing seconds) / 3,600
peak GB = max(discovery maxRSS, demultiplexing maxRSS) × 1,024 / 1,000,000,000
```

The [phase table](../source_data/figure_01/accepted_phase_records.tsv) contains 108 measurements that form 54 paired repetitions. Means and sample standard deviations use the three repetitions in each dataset–tool–thread condition. The [combined repetitions](../source_data/figure_01/combined_replicates.tsv) and [summary table](../source_data/figure_01/timing_summary.tsv) supply panels B and C.

The [SN-ONT/RAD/four-thread example](../data/examples/figure_01/) includes the commands and GNU-time logs for one complete repetition. Parse its measurements and combine the complete phase table with:

```bash
mkdir -p results
python3 scripts/revision/figures_124_steps/read_gnu_time.py \
  data/examples/figure_01/raw_timing/whitelist_detection/metrics.tsv \
  data/examples/figure_01/raw_timing/demultiplexing/metrics.tsv \
  --output results/figure1_parsed_time.tsv

python3 scripts/revision/figures_124_steps/combine_timing.py \
  source_data/figure_01/accepted_phase_records.tsv results/figure1_all54_totals.tsv
```

The parsed example is provided in [parsed_gnu_time.tsv](../data/examples/figure_01/parsed_gnu_time.tsv). The [source registry](../source_data/figure_01/timing_raw_source_registry.tsv) links each measurement to its log. The [collector](../scripts/revision/figures_124_collect_timing.py) combines those phase records.

## Visium HD barcode counts

Panel D displays a common 16-µm spatial grid. RAD barcode pairs are mapped to their spatial coordinates, and eight adjacent 2-µm positions along each axis are combined into one 16-µm bin. The displayed tissue reference uses Space Ranger `in_tissue` annotations. The RAD matrix contains barcode-discovery counts, as specified by the [count definition](../source_data/figure_01/producing_evidence/HD_selected_count_definition.json) and [stage-count table](../source_data/figure_01/hd_stage_counts.tsv).

The complete grid contains 175,561 bins arranged as 419 × 419 positions. For PBC44593, the plotted value is `log10(RAD_count × 1,000,000 / 45,979,761)` for bins with positive counts. Its 123,658 in-tissue bin identifiers match the Space Ranger filtered barcode set. The count matrix is stored at `checkpoints/figure_01/sample_bin_matrix_16um.csv.gz`; [reference hashes](../source_data/figure_01/hd_grid_reference_sources.json) identify the raw and filtered coordinate sets.

Reconstruct the grid and tissue mask from the deposited identifiers:

```bash
python3 scripts/revision/figures_124_steps/recover_hd_grid.py \
  --input source_data/figure_01/hd_RAD_bins.tsv \
  --raw-barcodes source_data/figure_01/hd_16um_raw_barcodes.tsv.gz \
  --filtered-barcodes source_data/figure_01/hd_16um_filtered_barcodes.tsv.gz \
  --output results/tissue_positions_16um_reconstructed.csv \
  --report results/figure1_grid_receipt.json
```

[Example grid rows](../data/examples/figure_01/hd_grid_example.tsv) show the coordinates and tissue-mask fields; [stage-count examples](../data/examples/figure_01/hd_stage_example.tsv) show the count columns. The figure displays the tissue reference, Seurat counts and RAD counts on the same grid. The command above writes the RAD grid and tissue-mask table.

## Generate the source tables

With the project inputs mounted, build the timing and spatial tables:

```bash
python3 scripts/revision/figures_124.py build --project-root /path/to/rad_data --output-root .
python3 scripts/revision/figures_124_hd_lineage.py --project-root /path/to/rad_data --output-root .
python3 scripts/revision/figures_124.py validate --output-root .
```

The shared workflow also processes Figures 2 and 4. [Table schemas](../source_data/figure_01/schemas.json) define the fields, units, and join keys.
