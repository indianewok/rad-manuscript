# Figure 5 source data

The Figure 5 guide covers receptor recovery in RAGE-seq and the three-component barcode comparison in LR-Split-seq. [Methods, commands and examples](../../docs/figure_05.md).

## RAGE-seq receptor reads

| Table | Contents |
|---|---|
| [Per-cell receptor counts](receptor_counts.tsv) | Native, corrected-only and total assigned reads by tool, barcode, cell type and receptor class |
| [Receptor totals](receptor_totals.tsv) | The same counts summed by tool |
| [Cell-type totals](receptor_identity_summary.tsv), [cell-type labels](receptor_cell_identity_map.csv) | Counts and barcode identities for each cell type |

Total assigned reads equal native plus corrected-only reads. [Worked example](../../data/examples/figure_05/PREVIEW.md), [Flexiplex execution](provenance/Flexiplex_receptor_execution.md).

## LR-Split-seq panels G and H

| Table | Contents |
|---|---|
| [FLAMESv2 ED2 read counts](provenance/splitseq/component_ED2_native_read_counts.tsv) | Distinct original reads for panel G |
| [All 568 cells](splitseq_umi_panel_ED2_568.tsv) | Cell and sample identities, short-read UMIs, and long-read reads and UMIs from RAD and the FLAMESv2 component workflow |
| [Myoblast cells](splitseq_umi_panel_ED2_MB_cells.tsv), [myoblast nuclei](splitseq_umi_panel_ED2_MB_nuclei.tsv), [myotube nuclei](splitseq_umi_panel_ED2_MT_nuclei.tsv) | UMI counts in panel H by sample |
| [Regression coefficients](splitseq_umi_panel_ED2_regressions.tsv) | Count of cells, slope, intercept and R² for each fit in panel H |
| [Published cell map](provenance/splitseq/published_568_barcode_map.csv) | Published cell IDs, component barcodes, reverse-transcription wells, sample and short-read UMI counts |

Join the assignment files to the published cell map to reproduce the per-cell counts. [Worked examples](../../data/examples/figure_05/splitseq/PREVIEW.md), [assignment files](splitseq_umi_panel_ED2_files.tsv), [counting script](../../scripts/figure_05/replay_splitseq_umi_panel.py), [pinned FLAMES configurations](../../docs/pinned_flames_configs.md).
