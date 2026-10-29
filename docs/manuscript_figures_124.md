# Computational efficiency, synthetic benchmarks, and barcode discovery

These passages describe the analyses for Figures 1, 2, and 4.

## Computational efficiency

Computational efficiency was assessed using complete LongBench single-nucleus ONT and single-cell PacBio inputs with 119,016,231 and 195,242,483 reads, respectively. RAD 1.0.2 (`4acbe00`), BLAZE 2.5.0 (`11994f9`), and Flexiplex 1.02.6 (`d84c8ae`) were run with 4, 16, and 64 tool threads, with three repetitions per condition on AMD EPYC 7543 nodes. Each demultiplexing run used the whitelist selected in its corresponding discovery phase. Total wall time was the sum of the two phases within each repetition. Peak process memory was the larger GNU-time maximum resident set size, converted from KiB to decimal GB. Means and sample standard deviations were calculated across repetitions.

At 16 threads, mean total wall times were 1.75, 7.24, and 9.08 hours for RAD, BLAZE, and Flexiplex on SN-ONT, and 1.49, 3.04, and 2.01 hours on SC-PB. The [Figure 1 guide](figure_01.md) provides the phase-specific commands and software identities.

The Visium HD analysis used 16 µm bins. Whitelist-detection totals matched the original valid-pair tables across all four flow cells. The 419 × 419 grid and its 123,658-bin tissue mask matched the saved Space Ranger barcode sets. Space Ranger processed converted Nanopore reads. Reconstruction of the shared-scale spatial comparison requires the original Seurat `nCount_Spatial` values and barcode-to-bin creation workflow, as listed in the Figure 1 guide.

## Synthetic barcode discovery and assignment

ScTagger-L contained 4,993,805 reads from 5,000 known source barcodes; ScTagger-S contained 98,873 reads from 50 source barcodes. Quality experiments retained read identifiers, nucleotide sequences, and error patterns across conditions. Badread Nanopore2018 and Nanopore2023 models supplied background quality scores across each read. Scores in a located barcode were sampled conditional on local matches and errors against its known source sequence. Each sweep condition added a fixed Phred-score offset to every base and clipped the result to Q1–Q50. The native Nanopore2023 condition retained the original generated scores. The recorded seed and model pathname jointly determine the effective sampling seed; the [Figure 2 guide](figure_02.md) links the exact generation contract.

Barcode discovery was scored by comparison of the selected barcode set with the known source set. Precision was the fraction of selected barcodes present in the source set, recall was the fraction of source barcodes selected, and F1 was the harmonic mean of precision and recall.

Read assignment used RAD `24d5ce4` with all 5,000 source barcodes supplied as both global and custom lists; diagnostic Flexiplex 1.02.6 with its 3,004 selected targets; and the BLAZE 2.6.0a0 matching-function replay on native Nanopore2023 extractions with 5,015 selected targets. RAD and Flexiplex used the sequence-identical uniform-Q20 input. Flexiplex’s diagnostic field recorded the raw barcode before correction.

Each original read was classified as native-correct, corrected-correct, native-incorrect, corrected-incorrect, or unassigned. Each tool’s state counts summed to the complete input. Per-target tables represented unselected source barcodes as blank and selected targets with no reads in a category as zero. Correction-only fractions used the sum of correct and incorrect corrected assignments as their denominator. Source tables, counting rules, and numerical checks are provided in the Figure 2 guide.

## Barcode discovery across modalities

The comparison included 37 complete sequencing inputs and three tools, yielding 111 observations. Every RAD whitelist-discovery result used RAD 1.0.2, commit `4acbe004ba11b150d6832395452632f367a6e6c1`, with `scan-wl --max-error 0.3` and no read cap. The [per-input tool table](../source_data/figure_04/tool_parameters.tsv) reports the versions and analysis flags for RAD, BLAZE and Flexiplex. Input identifiers retain the relationships among donors, libraries and technical sequencing runs.

Known source barcodes defined the synthetic references; matched filtered short-read barcodes and published spatial masks defined the biological reference sets. ScMixology2 used native RAD, BLAZE 2.5.1 and Flexiplex 1.02.7 (release v1.02.7.1) on the same complete 25,164,948-read FASTQ, with the matched 248-barcode Cell Ranger list used for scoring. The RAGE-seq lymph-node reference comprised 5,978 barcodes annotated as containing adaptive immune cells: 4,255 T-cell barcodes, 1,637 B-cell barcodes and 86 T/B-doublet barcodes. Reference selection required membership in the deposited short-read list and the corresponding annotation label. Barcode calls outside this set contributed to the false-positive count under that reference definition. The [Figure 4 guide](figure_04.md) describes the references, including the unresolved sample/reference pairing for ERR15095097.

RAD, BLAZE and Flexiplex achieved F1 scores above 0.90 on 26, 19 and 17 of the 37 inputs, respectively. The statistical analysis retained the Friedman test across the three tools, followed by Dunn comparisons of RAD with each comparator, adjusted within the two comparisons for each metric. The [Friedman](../source_data/figure_04/friedman.tsv) and [Dunn](../source_data/figure_04/dunn.tsv) tables report the results. Read count, GC percentage and average-quality summaries describe the corresponding long-read inputs using retained SeqKit results. The guide links the current source tables, per-dataset run records and commands for reproducing the comparison.
