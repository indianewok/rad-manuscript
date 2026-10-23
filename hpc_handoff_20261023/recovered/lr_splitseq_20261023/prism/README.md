# LR-Split-seq Prism recovery, 23 October 2026

The original table's **568 cell identities are recovered** in [prism_row_to_cell.csv](prism_row_to_cell.csv). All 3,408 numeric entries in the six-column saved Prism table match the original keyed export in the same row order. No sorting or count-based identity inference was used. `published_rank` is exactly the original one-based Prism row number. The source export contains 568 unique `published_cell_barcode` values.

The keyed source is `/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/plotting_exports/20260801_reads_per_published_cell/splitseq_published_barcode_read_counts.csv` (SHA-256 `8a26f5537b50c2f3199f03b5613622d02cf4d0c9dadf5a0091c2fb2a3841a2ff`). Its export builder and upstream component analysis are preserved separately in the recovered source package. The native Prism file contains no cell IDs on these two tables; its numeric values and labels were checked independently against that keyed source.

| Primary Prism column | Saved column title | Source export field | Sum |
|---|---|---|---:|
| 1 / X | rad_ed2_assigned_reads | rad_ed2_assigned_reads | 2,078,171 |
| 2 / A | component-based Flexiplex, no poly-T | flex_component_no_polyt_assigned_reads | 2,062,349 |
| 3 / B | component-based Flexiplex, poly-T | flex_component_polyt_assigned_reads | 1,156,252 |
| 4 / C | GitHub FLAMESV2 (Newest) | flames_matched_split_polyt_assigned_reads | 2,331,521 |
| 5 / D | Preprint FLAMESV2 (Canonical) | flames_historical_two_pass_assigned_reads | 2,209,802 |
| 6 / E | Identity Line | duplicate of rad_ed2_assigned_reads | 2,078,171 |

The final comparison is primary columns **1 and 3**. The two historical FLAMES columns remain here as original source context. The identity-line column duplicates RAD; all its cells are marked excluded in the original dataset metadata.

The second table, `SPLIT-seq benchmarking, continued`, contains exactly primary columns 2 through 6 in the same order. Its older titles are `Custom Flexiplex Layout`, `Default Flexiplex Layout (2/26)`, `GitHub FLAMESV2 (Newer)`, `Preprint FLAMESV2 (Canonical)`, and `RAD`. The final comparison is therefore continued columns **5 and 2**.

## Executed statistical test recovered

The saved analysis `F616A250-536B-42B0-B4E6-23C2BF786E46` explicitly specifies `PAIRED_T_TEST` and `P_VALUE_TWO_TAILED`. It compares RAD against the poly-T component column, under the older continued-table label `Default Flexiplex Layout (2/26)`. Its saved result is **t = 14.959474687143327, df = 567, P = 6.890554214980993e-43**. This is the exact P value rounded in the rebuttal. The paired t statistic was independently recalculated from the recovered numeric rows (14.959474687143306). The medians are 1,979.5 RAD and 1,102.5 component-based Flexiplex with poly-T.

This establishes which historical test generated the reported number. Selection of the final statistical method remains an author decision. The saved result supports correcting the historical test's name to paired t test; describing that same saved P value as Wilcoxon signed-rank is inconsistent with the archived execution record.

## Contents and verification

- [cell_mapping_validation.json](cell_mapping_validation.json): all-row/all-column comparison, source hashes and output mapping hash.
- [validation.json](validation.json): native archive hash, exact table/analysis identifiers, totals, medians, test validation, graph-sheet metadata and hashes of every retained native component.
- [native_components](native_components): verbatim saved table CSVs, data/column definitions, relevant analysis parameters/results and graph-sheet metadata. These components are evidence extracts, not a standalone editable Prism project.
- [rad_vs_component_polyT_by_prism_row.csv](rad_vs_component_polyT_by_prism_row.csv): final read-count comparison before adding external row identities.
- [splitseq_all_methods_by_prism_row.csv](splitseq_all_methods_by_prism_row.csv): all six source columns with original labels and row numbers.
- [extract_and_validate.py](extract_and_validate.py): repeat native extraction and numeric checks using `--source MASTER.prism --out OUTPUT_DIRECTORY`.
- [validate_cell_mapping.py](validate_cell_mapping.py): repeat exact mapping checks using `--prism-csv native_components/data/tables/954A959E-2630-403B-89C7-8EEBAF7A986A/data.csv --labeled-source ORIGINAL_KEYED_EXPORT.csv --out OUTPUT_DIRECTORY`.

Source native archive: `/Volumes/rad_data/reviewer_comment_data/081926_rebuttal_RAD4acbe_rawLongBench_updated_20260827.prism`, SHA-256 `2987ae97728ff61488a861b305aa2b9fb356f51ba860c084e9c06c823765572b`. Its stored modification date is `2026-09-01T17:14:15Z`. No Prism application interaction or rendering was performed. Graph JSON establishes the stored dataset references only; it does not establish which historical graph was ultimately exported into the manuscript artwork.

## Figure 5H boundary

This recovery establishes the read-count comparison and cell identities. The keyed export also carries published short- and long-read UMI annotations; those annotations are not the current RAD-versus-Flexiplex UMI comparison. The master Prism file contains only the two Split-seq read-count sheets, with no UMI sheet for Figure 5H. The candidate `results/misc/splitseq_rad_flex_shortread_umi_20260728/per_cell_umi_intersection.csv` on CMV_SSD_2 uses earlier RAD counts (first published cell: 52,491 reads, versus 60,941 in the final ED2 read table). Its source and its `per_cell_umi_lv1_intersection.csv` companion require version reconciliation before assigning them to Figure 5H.
