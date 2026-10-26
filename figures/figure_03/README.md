# Figure 3 selected current analysis

Start with the [data-first walkthrough](../../docs/figure_03.md): exact versions and parameters, actual raw/assignment excerpts, small counting scripts, observed outputs and links to every plotted source table.

The three off-list datasets use strict physical-read counts. All nine current RAGE matched raw producer/count validations passed, and ScTagger and LongBench retained assignments have been fully recounted. B displays strict assigned reads divided by every physical input read; a raw-total companion is retained. Correction panels use unique original-read–target pairs and the selected all-record RAD4acbe00 plus native competitor checkpoints.

These PDF/SVG/PNG files are scripted data proofs. Existing statistical test and annotation choices remain unchanged. Native Prism recalculation/export and inspection of final annotated artwork remain pending; [current cell-update instructions](../../validation/figure_3_native_table_updates.tsv) contain only table identities and selected current values.

From the repository root:

```bash
python3 scripts/revision/figure_3.py build --project-root /path/to/reviewer_comment_data
python3 scripts/revision/figure_3.py validate
python3 scripts/revision/figure_3.py render
```

The renderer uses only [deposited source data](../../source_data/figure_03/). Full input and assignment ledgers are large current checkpoints, excluded from Git. Complete D–G source-bearing assignment streams are still required to reconstruct full pair-overlap ledgers; marginal tables cannot supply these intersections.
