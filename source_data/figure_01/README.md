# Figure 1 source data

The [Figure 1 guide](../../docs/figure_01.md) gives the commands for RAD 1.0.2 (`4acbe00`), BLAZE 2.5.0 and Flexiplex 1.02.6, then follows the timing and spatial calculations.

## Timing: phase logs to plotted summaries

The benchmark used the complete LongBench SN-ONT and SC-PB inputs, with 4, 16 and 64 tool threads and three repetitions per condition on AMD EPYC 7543 hardware. SN-ONT denotes single-nucleus ONT; SC-PB denotes single-cell PacBio.

| File | Read it to see |
|---|---|
| [software_and_resources.tsv](software_and_resources.tsv) | Executable versions, input files, catalogs and references |
| [accepted_phase_records.tsv](accepted_phase_records.tsv) | 108 measurements: two inputs × three tools × three thread counts × three repetitions × two phases; input and processed-read counts are included |
| [timing_raw_source_registry.tsv](timing_raw_source_registry.tsv) | The log file and hash behind each measurement |
| [combined_replicates.tsv](combined_replicates.tsv) | The 54 paired discovery-plus-demultiplexing repetitions |
| [timing_summary.tsv](timing_summary.tsv) | Mean and sample standard deviation across the three repetitions per condition |

For each repetition, processing time is the sum of the two phase wall times. Memory is the larger process maximum RSS across the two phases, converted from KiB to decimal GB as `KiB × 1,024 / 1,000,000,000`. The [timing example](../../data/examples/figure_01/) starts with two GNU-time logs and shows the parsed and combined outputs.

The [algorithm crosswalk](algorithm_crosswalk.tsv) and [barcode-processing reference](pinned_algorithm_audit.md) explain RAD commit `cb699170`. The timing runs use the software identities listed above.

## Visium HD: barcode counts to spatial bins

| File | Read it to see |
|---|---|
| [hd_RAD_bins.tsv](hd_RAD_bins.tsv) | PBC44593 detection counts, bin coordinates, tissue and validity flags, and transformed plotting values |
| [hd_stage_counts.tsv](hd_stage_counts.tsv) | Four wide-table totals and their corresponding valid-pair totals |
| [hd_stage_differences.tsv](hd_stage_differences.tsv) | Detection and demultiplexing counts for the 165,898 bins with different values |
| [hd_grid_reference_sources.json](hd_grid_reference_sources.json) | Raw and filtered 16-µm barcode sets defining the grid and tissue mask |

PBC44593 uses a full-table denominator of 45,979,761. Each positive bin count is transformed as `log10(count × 1,000,000 / 45,979,761)`. Nonpositive counts have empty transformed values and are omitted from logarithmic plots. The four wide-table totals equal their valid-pair count totals.

The spatial workflow joins positions, barcode-to-bin mappings and Seurat counts by bin ID. The full-grid and tissue-mask columns match the raw and filtered 16-µm barcode sets. [Example bins](../../data/examples/figure_01/hd_grid_example.tsv) show the IDs, row, column and tissue fields. The [table schemas](schemas.json) define all fields and units.
