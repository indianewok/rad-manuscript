# Figure 7 — from read assignments to expression matrices

The LongBench SN-ONT matrix uses RAD 1.0.2 at commit `4acbe004ba11b150d6832395452632f367a6e6c1`. The [demultiplexing command](provenance/RAD_demux_command.txt), [common alignment command](provenance/align_common_raw.sh) and [matrix builder](provenance/build_matrices.py) define the processing steps.

1. Extract original read ID, cell barcode, UMI, raw barcode and correction flag. The complete RAD assignment table contains **57,885,606 records** across **12,423 selected barcodes**. Orientation and concatemer suffixes are normalized to the original read ID.
2. Join each original read to its gene assignment from the common raw-read alignment. Every emitted RAD segment, including `-CT` concatemer segments, inherits that gene assignment.
3. Count each exact cell–gene–UMI combination once. Count records without a UMI individually.

The resulting RAD matrix has **45,224 genes × 12,423 nuclei**, **15,772,545 nonzero coordinates** and **22,875,174 molecules**. The [production summary](RAD_emitted_segment_build_summary.json) identifies the inputs and counting fields; [example records](../../data/examples/figure_07/PREVIEW.md) follow assignments through molecule counting and normalization.

For H146-versus-H526 testing, select positive-depth Vireo singlets and retain the **8,135 genes eligible in RAD, BLAZE, Flexiplex and Illumina**. The [gene-level table](direct_H146_vs_H526_plot_data.tsv.gz) gives each gene's raw P value, signed fold change, common-family BH adjustment and reference membership. The [Figure 7 guide](../../docs/figure_07.md) gives the cohorts, normalization, tests and threshold sweep.
