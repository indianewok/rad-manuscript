# Statistical data definitions for Figures 1, 2, and 4

| Figure | Observation and summary |
|---|---|
| 1 | Each timing condition has three computational repetitions. Total time combines detection and demultiplexing; peak process memory is the larger GNU-time maxRSS, converted from KiB to decimal GB. Summaries use the mean and sample standard deviation. |
| 2 | Each assignment partition covers 4,993,805 original reads. Correction proportions use corrected assignments as the denominator. Quality conditions are paired transformations of the same read sequences and errors. |
| 4 | Each metric table contains the same 37 inputs and three tools. Input identifiers retain donor, library, and technical-run relationships. ScMixology2 includes native RAD calls and BLAZE/Flexiplex selector replays. |

The Figure 4 RAGE lymph-node reference contains 5,978 T-cell, B-cell, and T/B-doublet barcodes. Exact reference selection and precision, recall, and F1 definitions are in the [Figure 4 guide](../docs/figure_04.md). Figure 2’s target sets, blank-versus-zero policy, and correction denominators are in the [Prism data record](../source_data/figure_02/desktop_QA.md).

The table reconstruction retained existing statistical procedures and annotations. Reproduction of the original inferential calculations requires their native Prism settings, including tie handling and the multiple-comparison family. Saved figure images and source identities are recorded in the [Prism export manifest](../manifests/prism_exports.json).
