# Replay the recovered checkpoints

Run from this directory with Python 3. Outputs go to a new directory. These commands replay stored evidence; they do not run raw demultiplexing.

```sh
python3 prism/validate_cell_mapping.py --prism-csv prism/native_components/data/tables/954A959E-2630-403B-89C7-8EEBAF7A986A/data.csv --labeled-source tables/splitseq_published_barcode_read_counts.csv --out replay/prism
python3 scripts/validate_rad_ed2_checkpoint.py --checkpoint checkpoints/rad_ed2/assignments_selected_ed2_published_cells.tsv.gz --master reference/published_568_barcode_map.csv --expected checkpoints/rad_ed2/ed1_ed2_per_published_cell.tsv --report replay/rad_ed2.json
python3 validation/verify_component_normalization.py --stats ssd2/benchmarks/flamesv2_splitseq_20260728/component_polyt_paired_t4/stats.tsv.gz --assignments ssd2/benchmarks/flamesv2_splitseq_20260728/component_polyt_paired_t4/assignments.tsv.gz --report replay/component_normalization.json
```

The original source-to-checkpoint and standalone replay reports accompany the checkpoint. The commands above are portable equivalents; create `replay/` if your Python/runtime does not create report parents. For a native Prism reread, pass the full master project explicitly to `prism/extract_and_validate.py`. That original project is external; the extracted components are included and independently hashed.

For cell-count aggregation, preserve the exact SQL in `source/component_runner/` and `ssd2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/`. Map its original paths to copied assets and filter the selected arm. The complete RAD producer was not recovered; the new portable RAD validator recreates per-cell read and UMI counts from the stored assignment checkpoint and fails if any cell differs. Rebuild Figure 5H's selected-arm UMI intersections separately.
