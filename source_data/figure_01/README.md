# Figure 1 source data

[Methods and commands](../../docs/figure_01.md) · [Table schemas](schemas.json)

## Timing: phase logs to plotted summaries

| File | Contents |
|---|---|
| [software_and_resources.tsv](software_and_resources.tsv) | Executable versions, input files, catalogs and references |
| [accepted_phase_records.tsv](accepted_phase_records.tsv) | 108 measurements: two inputs × three tools × three thread counts × three repetitions × two phases; input and processed-read counts are included |
| [timing_raw_source_registry.tsv](timing_raw_source_registry.tsv) | The log file and hash behind each measurement |
| [combined_replicates.tsv](combined_replicates.tsv) | The 54 paired discovery-plus-demultiplexing repetitions |
| [timing_summary.tsv](timing_summary.tsv) | Mean and sample standard deviation across the three repetitions per condition |

[Timing example](../../data/examples/figure_01/) · [Algorithm crosswalk](algorithm_crosswalk.tsv) · [Pinned barcode-processing reference](pinned_algorithm_audit.md)

## Visium HD: barcode counts to spatial bins

| File | Contents |
|---|---|
| [hd_RAD_bins.tsv](hd_RAD_bins.tsv) | PBC44593 detection counts, bin coordinates, tissue and validity flags, and transformed plotting values |
| [hd_stage_counts.tsv](hd_stage_counts.tsv) | Four wide-table totals and their corresponding valid-pair totals |
| [hd_stage_differences.tsv](hd_stage_differences.tsv) | Detection and demultiplexing counts for the 165,898 bins with different values |
| [hd_grid_reference_sources.json](hd_grid_reference_sources.json) | Raw and filtered 16-µm barcode sets defining the grid and tissue mask |

Join positions, barcode-to-bin mappings and Seurat counts by bin ID. Empty transformed values mark nonpositive counts and are excluded from logarithmic plots. The four wide-table totals equal the corresponding valid-pair totals. [Example bins](../../data/examples/figure_01/hd_grid_example.tsv)
