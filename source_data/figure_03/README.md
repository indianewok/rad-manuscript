# Figure 3 source data

Figure 3 measures assignments to excluded barcode lists and classifies barcode changes in LongBench. The [Figure 3 workflow](../../docs/figure_03.md) defines the input lists, counting units, correction classes, and percentage denominators.

## Off-list assignments in panels B and C

| File | Content |
|---|---|
| `plotted_checkpoint/plotted_offlist_totals.tsv` | Twenty-seven plotted totals: three datasets × three tools × three target-list draws |
| `plotted_checkpoint/plotted_offlist_per_target.tsv.gz` | The 44,148 target-count observations selected in panel C, identified by dataset, tool, draw, and Prism row |
| `plotted_checkpoint/plotted_offlist_provenance.json` | Source Prism hash, layout and graph bindings, native table hashes, count units, and total-to-target checks |

ScTagger-L and LongBench SC-ONT use strict single-output original-read counts. RAGE-seq uses historical tool-assignment tables. Panel B displays the total counts for all three list draws. Panel C displays per-target observations from the first draw. The totals and target distributions are preserved as separate plotted tables.

The deposited checkpoint can be used directly. To refresh it from a local author project:

```bash
python3 scripts/figure_03/extract_plotted_offlist.py \
  --prism "external_data/prism/Figure 3.prism" \
  --output-dir results/figure_03/plotted_checkpoint
```

The extractor follows the graph-to-dataset references in the saved manuscript layout. Each target observation retains its original Prism row order.

## LongBench correction in panels E–G

`correction_totals.tsv` contains category totals. `correction_per_target.tsv.gz` contains target-level category counts, assignment denominators, and percentages. `panel_data_manifest.tsv` binds the tables to the panels, and `schema.json` defines the fields and keys.

The chemistry catalog defines valid barcode sequences; the matched Cell Ranger filtered set defines the reference cell population. Corrected off-list assignments change a source outside the catalog to a selected target. Failure Mode 1 changes a catalog-valid source outside the filtered reference to a selected target. Failure Mode 2 changes a reference-supported source to a different reference-supported target selected by the tool.

Counts use unique original-read–target-barcode pairs. Each category percentage is its count divided by all unique assignments to the same target. The [worked examples](../../data/examples/figure_03/) connect source fields, category counts, and denominator calculations.
