# Figure 3 Off-list assignments and barcode correction

![Figure 3](prism/figure_03.png)

The [legend](../../docs/current_figure_legends.md) describes the panels. The
[analysis guide](../../docs/figure_03.md) follows the sequencing inputs through
barcode assignment, correction classification and calculation of the plotted
metrics. The [source tables](../../source_data/figure_03/) contain off-list
assignment totals, per-target counts and LongBench correction categories.

The off-list challenge counts original physical reads with exactly one
assignment record. The LongBench correction analysis counts unique
original-read–target-barcode pairs and summarizes them by target barcode.

Check the source tables:

```bash
python3 scripts/revision/figure_3.py validate
```

Build them from the project checkpoints:

```bash
python3 scripts/revision/figure_3.py build --project-root /path/to/reviewer_comment_data
```
