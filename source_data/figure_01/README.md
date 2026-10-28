# Figure 1 source data

The [Figure 1 guide](../../docs/figure_01.md) describes the RAD workflow, timing
benchmark and Visium HD analysis.

## Computational efficiency

`accepted_phase_records.tsv` contains 108 successful timing phases: two inputs,
three tools, three thread counts, three repetitions and two phases. GNU-time
records are joined to status and completion markers through the file hashes in
`timing_raw_source_registry.tsv`.

`combined_replicates.tsv` sums the detection and demultiplexing wall times for
each repetition. Its memory measurement is the larger process maximum RSS
across the two phases, converted from KiB to decimal GB as `KiB × 1024 / 1e9`.
`timing_summary.tsv` reports the mean and sample standard deviation across the
three repetitions. Runs used AMD EPYC 7543 hardware with 4, 16 or 64 requested
threads. SN-ONT denotes single-nucleus ONT; SC-PB denotes single-cell PacBio.
The RAD parser recorded one fewer SC-PB read than the input reference count.

`algorithm_crosswalk.tsv` and `pinned_algorithm_audit.md` describe RAD commit
`cb699170`. The timing experiments retain their own software versions, including
RAD `4acbe00`.

## Visium HD

`hd_RAD_bins.tsv` contains PBC44593 16-µm barcode-detection counts, validity flags
and the full-table denominator of 45,979,761. The four wide-table totals match
the original valid-pair count tables. `hd_stage_counts.tsv` records those totals;
`hd_stage_differences.tsv` contains 165,898 bins whose detection count differs
from the separately retained demultiplexing count.

Full-grid and tissue-mask columns are reconstructed from the selected data and
match the saved raw and filtered 16-µm barcode sets. Their sources are recorded
in `hd_grid_reference_sources.json`. Nonpositive counts have empty transformed
values and are omitted from logarithmic plots.

A complete spatial-count reconstruction also requires the original positions
file, count-to-bin generation code and selected Seurat count values. The [Figure 1 guide](../../docs/figure_01.md) describes those input requirements.
