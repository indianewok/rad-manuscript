# Figure 3 source data

The [Figure 3 workflow](../../docs/figure_03.md) explains the experiment and follows individual read records through counting and plotting.

## Off-list assignments: panels B and C

RAGE-seq, ScTagger-L and LongBench SC-ONT used the same off-list procedure: three independently sampled, size-matched lists outside the reference; the same input and list for all three tools within each replicate; and the same single-output physical-read counting rule. Chemistry catalogs, references, input sizes and seeds are specified in the workflow.

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

The chemistry catalog defines valid barcode sequences, and the matched Cell Ranger filtered set defines the reference population. **FM1** changes a reference-supported source to a different reference-supported target selected by the tool. **FM2** changes a catalog-valid source outside that reference to a selected target. Corrected off-list assignments change a source outside the catalog to a selected target.

Counts use unique original-read–target-barcode pairs within each category. Each category percentage is its count divided by all unique assignments to the same target. The [worked examples](../../data/examples/figure_03/) connect source fields, category counts and denominators.

From the repository root, check the deposited tables with:

```bash
python3 scripts/revision/figure_3.py validate
```
