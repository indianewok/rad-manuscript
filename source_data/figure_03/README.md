# Figure 3 source data

[Methods and commands](../../docs/figure_03.md) · [Worked examples](../../data/examples/figure_03/)

## Off-list assignments: panels B and C

| File | Contents |
|---|---|
| [replicate_whitelists.tsv](replicate_whitelists.tsv) | Supplied barcode sequences and list hashes for each dataset and replicate |
| [offlist_totals.tsv](offlist_totals.tsv) | Twenty-seven observations: three datasets × three tools × three target lists; assigned-read counts, input-read denominators and assignment fractions |
| [offlist_per_target.tsv.gz](offlist_per_target.tsv.gz) | Counts for every supplied target in every run, including zero-count targets |
| [offlist_read_fates.tsv](offlist_read_fates.tsv) | Assigned, multiple-output-excluded and unassigned counts, which sum to the input-read total |

The total-count comparison uses all three target lists. The per-target distribution uses replicate 1.

## Barcode correction: panels D–G

| File | Contents |
|---|---|
| [measured_category_definitions.tsv](measured_category_definitions.tsv) | Observed source and selected-target membership defining each correction category |
| [correction_totals.tsv](correction_totals.tsv) | Category totals for each dataset and tool |
| [correction_per_target.tsv.gz](correction_per_target.tsv.gz) | Per-target category counts, total-assignment denominators and percentages |
| [panel_data_manifest.tsv](panel_data_manifest.tsv) | Table-to-panel bindings |
| [schema.json](schema.json) | Field names, keys and units |
| [checksums.json](checksums.json) | File identities |

Counts use unique original-read–target-barcode pairs within each category. Each category percentage uses all unique assignments to the same target as its denominator. [Category definitions](../../docs/figure_03.md#longbench-correction-categories)

From the repository root, check the deposited tables with:

```bash
python3 scripts/revision/figure_3.py validate
```
