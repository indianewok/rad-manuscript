# Figure 3: off-list assignments and barcode correction

![Figure 3](./prism/figure_03.png)

This image reproduces the saved Prism layout. Panel B shows total read counts;
the source tables below contain the updated assignment fractions and RAGE-seq
rerun counts.

The [Figure 3 guide](../../docs/figure_03.md) describes the datasets, software,
counting rules and calculations. The [source tables](../../source_data/figure_03/)
contain the assignment fractions, per-target counts and correction categories.

The off-list challenge counts physical reads with exactly one assignment row.
Assignment fractions use all physical input reads as the denominator. The
LongBench correction analysis counts unique original-read–target-barcode pairs
and summarizes them by target barcode.

Validate the source tables from the repository root:

```bash
python3 scripts/revision/figure_3.py validate
```

Rebuild them from the retained project checkpoints:

```bash
python3 scripts/revision/figure_3.py build --project-root /path/to/reviewer_comment_data
```
