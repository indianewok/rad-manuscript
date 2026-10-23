# RAD ED2 published-cell assignment checkpoint

`assignments_selected_ed2_published_cells.tsv.gz` contains original read ID, canonical cell barcode and UMI for the 568 published cells. It was extracted from the retained ED2 `assignments_normalized.tsv.gz` on 23 October 2026. The original demultiplexing was not rerun. Both RT primer variants were mapped by well to the corresponding T-primer barcode.

The file retains 2,079,870 assignment rows. Distinct counts reproduce all 568 saved per-cell read and UMI values: 2,078,171 read–cell pairs, 2,063,573 globally distinct reads and 1,891,704 cell–UMI pairs. One source read can contribute to more than one cell. Empty barcode/UMI exclusion is implemented; the source contained no such rows. UMI strings are not restricted to ten bases.

The full source ledger contains 2,536,299 rows. The 456,429 rows outside the published cell set are excluded from this checkpoint. This smaller file is sufficient for the plotted per-cell comparison; it is not a full demultiplexing archive. The full source file path, hash and size are recorded in `rad_ed2_checkpoint_validation.json`.

Use `scripts/validate_rad_ed2_checkpoint.py --checkpoint <this gzip file> --master <published_568_barcode_map.csv> --expected <ed1_ed2_per_published_cell.tsv> --report <output.json>` to replay it. The expected table is filtered to `ED2 current main`. Replay uses only Python's standard library. The original tally producer was not located; this portable script was checked against every retained per-cell read and UMI count.

The gzip timestamp is zero and its embedded filename is empty. Source row order is retained. The file SHA256 is `fe39fc76b67eb374c270ad684d5e96179933d1ce98a9e747b7744083788ff406` (26,638,130 bytes).
