# Figure 7 matrix and differential-expression workflow

The LongBench SN-ONT RAD matrix uses RAD commit
`4acbe004ba11b150d6832395452632f367a6e6c1`. All emitted records contribute,
including concatemer-derived `-CT` segments. Gene annotations are assigned to
the original read, and each emitted segment inherits that assignment. Exact
cell–gene–UMI keys are collapsed; records without a UMI count individually.

The selected matrix contains 45,224 genes and 12,423 cells, with 15,772,545
nonzero coordinates and 22,875,174 molecules. Matrix production uses the
emitted FASTQ and original-read-to-gene assignments; the
[production summary](RAD_emitted_segment_build_summary.json) records the
input identities and counting fields.

The direct H146-versus-H526 comparison uses 8,135 common eligible genes. The
[plotting table](direct_H146_vs_H526_plot_data.tsv.gz) contains one row per gene
and long-read workflow, with raw P values, fold changes, common-family
Benjamini–Hochberg adjustment and reference membership. The
[Figure 7 guide](../../docs/figure_07.md) specifies the cell groups, gene filters,
normalization, tests and threshold calculations.

The emitted-assignment checkpoint contains 57,885,606 five-field records for
all 12,423 selected barcodes. Its fields are original read ID, cell barcode,
UMI, raw barcode and correction flag. The extractor normalizes orientation and
concatemer suffixes. Matrix production additionally uses the gene assignment
for each original read.
