# Figure 7 — from read assignments to expression matrices

The RAD 1.0.2 run at commit `4acbe004ba11b150d6832395452632f367a6e6c1` produced 57,885,606 assignment records across 12,423 selected barcodes. The assignment extractor removes orientation and concatemer suffixes to recover the original read ID and records the cell barcode, UMI, raw barcode and correction flag. [RAD command](provenance/RAD_demux_command.txt), [assignment extractor](provenance/extract_assignments.py).

Join each record to the gene assigned to the original read by the shared raw-read alignment. Each RAD concatemer segment, including `-CT` records, inherits that gene assignment. Count each exact cell–gene–UMI combination once and count each record without a UMI separately. [Alignment command](provenance/align_common_raw.sh), [matrix builder](provenance/build_matrices.py).

The resulting matrix contains 45,224 genes × 12,423 nuclei with 15,772,545 nonzero entries and 22,875,174 molecules. [Matrix summary](RAD_emitted_segment_build_summary.json), [input identities](RAD_emitted_segment_source_manifest.tsv), [worked examples](../../data/examples/figure_07/PREVIEW.md).

H146 and H526 testing uses Vireo singlets with positive expression depth. Panel D uses the intersection of the eligible gene sets across all four workflows. [Cohort selection, gene tests and threshold sweep](../../docs/figure_07.md), [gene-level results](direct_H146_vs_H526_plot_data.tsv.gz).
