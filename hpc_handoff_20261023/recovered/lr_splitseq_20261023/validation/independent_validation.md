# Independent validation of recovered LR-Split-seq export

**PASS:** all 568 labeled rows match the master barcode map and all five named source count tables, with zero join or count discrepancies. All master metadata fields match exactly. Published ranks are 1–568, and canonical keys are unique.

The export's cell set, sample labels, short-read UMI counts and three round/well assignments were independently checked against the separately preserved GSM5169184 short-read metadata and barcode-to-well maps. All checks passed.

| Export arm | Read–cell pairs | Cells with positive counts |
|---|---:|---:|
| RAD ED2 | 2,078,171 | 568 |
| Flexiplex component, poly-T | 1,156,252 | 568 |
| Flexiplex component, no poly-T | 2,062,349 | 568 |
| FLAMES MATCHED_SPLIT | 2,331,521 | 568 |
| Historical two-pass FLAMES | 2,209,802 | 546 |

The final component comparator is the **Flexiplex polyT** row group within `component_no_polyt_t4/per_published_cell_counts.tsv`. The enclosing directory also contains the no-poly-T comparison; its name must not determine which row group is used. The separate RAD source must be filtered to **ED2 current main**.

## Counting and barcode conventions

`analyze_no_polyt.sql` explicitly counts distinct source-read IDs within each canonical cell. The sum across cells therefore counts unique read–cell pairs. One read assigned to two cells contributes to both cells. The saved component summary confirms 1,156,252 read–cell pairs versus 1,152,260 globally distinct source reads for the poly-T arm, and 2,062,349 versus 2,047,298 for the no-poly-T arm. Calls with an empty barcode or UMI are excluded. RT primer variants are joined by well and normalized to the same well's T-primer sequence.

The canonical key is **RT/v2 sequence _ round-2 ligation sequence _ round-3 ligation sequence**. BAM CB uses the reversed component order. Published cell IDs concatenate the round-3 and round-2 sequences, followed by an underscore and the RT well. All 568 mappings match the independent plate maps. The builder calls canonical components BC3/v2_BC2/v1_BC1/v1 using FLAMES names; those numbers differ from physical-round names.

The final paired component run records FLAMES commit `bf2211a8da1e1c7327370ab12479ae70e1d37cd8`, per-component edit distance 1, flank edit distance 3, four threads and terminal poly-T included. The runner defines that segment as eight T bases. The upstream paper-state configuration previously recovered uses a different flank setting (8); the local executed manifest controls this comparison.

This validation checks retained checkpoints and producer code. It does not rerun demultiplexing. The additional RAD assignment-level replay is documented below. Prism row order and copied manuscript values are being verified separately.

## RAD ED2 assignment-level checkpoint replay

The retained normalized RAD ED2 ledger contains 2,536,299 assignment rows. Restricting its canonical cells to the published set retains 2,079,870 rows and excludes 456,429 rows outside that set. Independent aggregation reproduces **every one of the 568 per-cell read counts and UMI counts** in the saved ED2 table: 2,078,171 read–cell pairs, 2,063,573 globally distinct source reads and 1,891,704 cell–UMI pairs. Repeated rows remain in the checkpoint and are collapsed by the validator's distinct-count operation.

A portable Python exporter/validator and deterministic gzip checkpoint are saved under `package/scripts/validate_rad_ed2_checkpoint.py` and `package/checkpoints/rad_ed2/assignments_selected_ed2_published_cells.tsv.gz`. The checkpoint contains only original read ID, canonical cell barcode and UMI for the published cell set. The full normalized ledger remains on the SSD, with its hash recorded in `rad_ed2_checkpoint_validation.json`. The original tally-producing script was not located; this independently validated implementation supplies the missing checkpoint-to-table step.
