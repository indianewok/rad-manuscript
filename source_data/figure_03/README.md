# Figure 3 source data

The [Figure 3 guide](../../docs/figure_03.md) follows the off-list challenges and
LongBench barcode-correction analysis from read assignments to these tables.
RAGE-seq was rerun in all nine tool–replicate combinations. Retained ScTagger and
LongBench assignments were recounted across their 18 combinations.

| File | Row key and measurement |
|---|---|
| [offlist_totals.tsv](offlist_totals.tsv) | Dataset, tool and replicate: strict physical-read total, input denominator, assignment fraction, target count and mean assignments per target. Panel B uses `100 × assignment_fraction`. |
| [offlist_per_target.tsv.gz](offlist_per_target.tsv.gz) | Dataset, tool, replicate and supplied barcode: 132,444 rows, including zero-count targets. Panel C uses replicate 1. |
| [offlist_read_fates.tsv](offlist_read_fates.tsv) | Dataset, tool and replicate: assigned, ambiguous-excluded and unassigned read counts, which sum to the input total. |
| [replicate_whitelists.tsv](replicate_whitelists.tsv) | Dataset, replicate, rank, barcode and list hash. Each replicate supplies the same list to all three tools. |
| [measured_category_definitions.tsv](measured_category_definitions.tsv) | Panel D source-to-target barcode categories. |
| [correction_totals.tsv](correction_totals.tsv) | Dataset, tool and category: unique original-read–target pairs for panel E. `O` denotes all assigned pairs. |
| [correction_per_target.tsv.gz](correction_per_target.tsv.gz) | Dataset, tool, target and category: 340,317 rows for panels F/G. Unselected targets are marked; percentages are null when `O = 0`. |
| [panel_data_manifest.tsv](panel_data_manifest.tsv) | Panel-to-table mapping, row keys, units, metrics and table hashes. |

TSV files use UTF-8, one header row and empty fields for null numeric values.
The [schema](schema.json) defines the columns; [checksums](checksums.json) identify
the files. The [descriptive summaries](../../validation/figure_3_offlist_metric_summary.tsv)
give the values for all three target-list draws, their arithmetic means and ranges.

Off-list counting retains a physical read only when it has exactly one
assignment row. The correction analysis deduplicates `(original_id, target)`
pairs within each category and allows category overlap. Complete retained C5
tables supply the marginal counts for panels D–G; reconstructing intersections
between categories requires the source-bearing assignment streams.

Validate the tables from the repository root:

```bash
python3 scripts/revision/figure_3.py validate
```
