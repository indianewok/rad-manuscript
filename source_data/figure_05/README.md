# Figure 5 source data

The [Figure 5 guide](../../docs/figure_05.md) gives the software versions, command flags and runnable examples for RAGE-seq receptor recovery and LR-Split-seq demultiplexing.

## RAGE-seq receptor reads

| Table | Row and measurement |
|---|---|
| [receptor_counts.tsv](receptor_counts.tsv) | Tool, barcode, cell type and receptor class: native, corrected-only and total assigned reads. |
| [receptor_totals.tsv](receptor_totals.tsv) | Native, corrected-only and total assigned reads summed by tool. |
| [receptor_identity_summary.tsv](receptor_identity_summary.tsv), [receptor_cell_identity_map.csv](receptor_cell_identity_map.csv) | Cell-type annotation counts and barcode-to-cell-type mapping. |

Native and corrected-only reads are mutually exclusive; `assigned = native + corrected_only`. The Flexiplex source receptor table stores cumulative counts, so its native counts are subtracted once before reporting corrected-only counts. Follow the [record-to-count example](../../data/examples/figure_05/PREVIEW.md) and [execution settings](provenance/Flexiplex_receptor_execution.md).

## LR-Split-seq panels G and H

| File | Measurement |
|---|---|
| [component_ED2_native_read_counts.tsv](provenance/splitseq/component_ED2_native_read_counts.tsv) | Full-input read counts for the FLAMESv2 ED2 component workflow used in panel G. The input contains 5,764,421 original reads. |
| [splitseq_umi_panel_ED2_568.tsv](splitseq_umi_panel_ED2_568.tsv) | Published ID, physical-cell barcode, sample, short-read UMIs, RAD reads/UMIs and FLAMESv2 ED2 component reads/UMIs for all 568 cells. |
| [MB cells](splitseq_umi_panel_ED2_MB_cells.tsv), [MB nuclei](splitseq_umi_panel_ED2_MB_nuclei.tsv), [MT nuclei](splitseq_umi_panel_ED2_MT_nuclei.tsv) | The three sample-specific panel H tables. |
| [splitseq_umi_panel_ED2_regressions.tsv](splitseq_umi_panel_ED2_regressions.tsv) | Ordinary least-squares slope, free intercept and R² on untransformed UMI counts. The display axes are logarithmic. |
| [published_568_barcode_map.csv](provenance/splitseq/published_568_barcode_map.csv) | Published cell IDs, component barcodes, RT wells, sample classes and short-read UMI counts. |

Panel G counts distinct original read IDs across the full input. Per-cell reads count distinct original IDs within each cell; per-cell UMIs count distinct exact UMI strings. A record contributes when barcode and UMI are nonempty. The two RT primers from each well map to one physical well before counting.

The [component-record examples](../../data/examples/figure_05/splitseq/PREVIEW.md) show the normalization and cell matching. The [ED2 replay](../../scripts/figure_05/replay_splitseq_umi_panel.py) reproduces the full per-cell table from the [specified assignment files](splitseq_umi_panel_ED2_files.tsv). The [pinned FLAMES configuration release](../../docs/pinned_flames_configs.md) provides the exact component layout and executed ED2 wrapper.
