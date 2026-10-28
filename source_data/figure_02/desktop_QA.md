# Figure 2 Prism data checks

The numerical comparison in this record used the corrected project `Figure2_corrected_20261022.prism`, SHA-256 `dded389f9d8214278f93d2669c64e704bbf2208c47db96bf57a4ce4c77d6d016`.

## Assignment tables

Each physical-read partition sums to 4,993,805. The target sets contain 5,000 supplied truth barcodes for RAD, 3,004 native selected barcodes for Flexiplex, and 5,015 selected barcodes for BLAZE, including 15 outside the truth set. Unselected Flexiplex truth targets are blank; a selected target with no reads in a category has zero.

Correction-only plots use the corrected states and exclude native, ambiguous, and unassigned states. Their denominators are 2,135,825 for RAD, 1,680,396 for Flexiplex, and 2,014,432 for BLAZE. The checked display proportions were RAD 91.03/8.97%, Flexiplex 83.24/16.76%, and BLAZE 93.4/6.6%. The separately labeled Flexiplex full-truth increment of 222,371 comes from the full-truth reference comparison.

The [value comparison](../../validation/figures_124_prism_values.json) matched all 45,000 inspected selected-truth values and blanks to the reconstructed arrays. Relevant tables are [assignment states](assignment_six_states.tsv), [per-target assignments](assignment_per_target.tsv), and [correction proportions](correction_only.tsv).

## Statistics

The quality conditions share the same sequences and error patterns. Assignment proportions use the denominators above. The retained Prism analyses and annotations were preserved during table reconstruction; the original native analysis settings are the source for reproducing their statistical calculations.

The [Figure 2 guide](../../docs/figure_02.md) describes the complete analysis, software versions, and reproduction commands. [Statistical data definitions](../../validation/figures_124_decisions.md) summarize the related Figure 1 and Figure 4 quantities.
