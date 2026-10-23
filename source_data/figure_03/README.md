# Figure 3 source data

The [walkthrough](../../docs/figure_03.md) follows actual raw reads and assignment records through the small counting scripts to these selected current tables. All nine full matched RAGE producer/count validations passed. The retained ScTagger and LongBench assignments were independently recounted across all 18 arms.

| File | Row key and measurement |
|---|---|
| [offlist_totals.tsv](offlist_totals.tsv) | Dataset, tool, replicate. Strict physical-read total, complete input denominator, assignment fraction, target count and mean assignments per target. B displays `100 * assignment_fraction`; raw totals are a companion. |
| [offlist_per_target.tsv.gz](offlist_per_target.tsv.gz) | Dataset, tool, replicate, actual supplied barcode. 132,444 rows, including every zero-count supplied target. C uses replicate 1. |
| [offlist_read_fates.tsv](offlist_read_fates.tsv) | Dataset, tool, replicate. Complete physical-read conservation: strict assigned + ambiguous excluded + unassigned = input. |
| [replicate_whitelists.tsv](replicate_whitelists.tsv) | Dataset, replicate, rank, barcode and complete list hash. The same list is supplied to all three tools. |
| [measured_category_definitions.tsv](measured_category_definitions.tsv) | D definitions based on observed source and selected target membership. |
| [correction_totals.tsv](correction_totals.tsv) | Dataset, tool, category. Unique original-read–target pairs for E; `O` includes all assigned pairs. |
| [correction_per_target.tsv.gz](correction_per_target.tsv.gz) | Dataset, tool, actual target, category. 340,317 rows for F/G; outer joins mark unselected targets explicitly. Percentages are null when `O=0`. |
| [panel_data_manifest.tsv](panel_data_manifest.tsv) | Panel-to-table bindings, row keys, units, metric and table hashes. |

TSV files use UTF-8, one header row and an empty field for null numeric values. [schema.json](schema.json) lists every column; [checksums.json](checksums.json) fixes every deposited table. [Exact descriptive summaries](../../validation/figure_3_offlist_metric_summary.tsv) report all three list draws, arithmetic means and ranges. These are not confidence intervals or new hypothesis tests.

Off-list counting excludes every row for a physical read with more than one assignment row, even repeated identical targets. Correction categories instead deduplicate `(original_id,target)` pairs within each category and may overlap. Their marginal totals do not identify full pair intersections. Full source-bearing D–G assignment streams remain missing; complete retained C5 tables are the current reproducible starting point for those panels.

From the repository root, `python3 scripts/revision/figure_3.py validate` checks these files and `python3 scripts/revision/figure_3.py render` redraws their data proofs without original storage. Native Prism recalculation/export and annotated artwork QA remain pending, preserving the existing statistical choices.
