# Figure 3 — off-list assignments and barcode correction

[Methods and commands](../../docs/figure_03.md) · [Figure legend](../../docs/current_figure_legends.md#figure-3) · [Source data](../../source_data/figure_03/README.md)

## Off-list experiments

ScTagger-L, LongBench SC-ONT and RAGE-seq use three reference-excluded target lists, identical inputs and target lists across tools within each replicate, and strict original-read counting. [Totals](../../source_data/figure_03/offlist_totals.tsv) give assigned-read counts and input fractions across all three lists. [Per-target counts](../../source_data/figure_03/offlist_per_target.tsv.gz) include every supplied barcode; the per-target distribution uses replicate 1.

## LongBench correction outcomes

Failure Mode 1 is reassignment between reference-supported cell or nucleus barcodes. Failure Mode 2 is reassignment from a catalog-valid barcode outside that reference into a selected barcode. The [category definitions](../../docs/figure_03.md#longbench-correction-categories), [totals](../../source_data/figure_03/correction_totals.tsv) and [per-target counts and percentages](../../source_data/figure_03/correction_per_target.tsv.gz) describe the measured outcomes.
