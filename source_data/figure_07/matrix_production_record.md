# Figure 7 matrix and differential-expression analysis

The native SN-ONT RAD matrix was produced with RAD commit
`4acbe004ba11b150d6832395452632f367a6e6c1`, retaining all emitted records,
including concatemer-derived `-CT` segments. The selected matrix has **45,224
genes × 12,423 cells**, **15,772,545 nonzero coordinates** and **22,875,174
molecules**. Each emitted segment inherits the frozen original-read gene
assignment. Exact cell–gene–UMI keys are collapsed; records without a UMI count
individually. Gene annotations are assigned at the original-read level.

The selected direct H146-versus-H526 comparison uses **8,135 common eligible
genes** and **24,405 tool/gene rows**. Its raw P values and effects exactly match
the selected native direct-test output; common-family BH adjustment, supported
membership and all 594 threshold combinations have been independently checked.
Repeating matrix production requires the original emitted FASTQ and frozen
read-to-gene file, which remain to be recovered.

The selected emitted-assignment checkpoint was recovered and fully verified:
57,885,606 five-field rows cover all 12,423 selected barcodes. It retains read
IDs, cell barcodes, UMIs, raw barcodes and correction flags. The extractor
removed orientation/concatemer suffixes; gene IDs and segment coordinates are
absent. The checkpoint supports assignment-level summaries.

- [Current direct comparison source](direct_H146_vs_H526_plot_data.tsv.gz)
- [Selected matrix production fields](RAD_emitted_segment_build_summary.json)
- [Current walkthrough and exact producer parameters](../../docs/figure_07.md)
