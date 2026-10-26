# Existing statistical analyses and native review

The author instructed that existing statistics and annotations stay unchanged. No hypothesis tests were added, replaced, or rerun in this reconstruction. Earlier requests to choose a new D03/D06 test design are superseded by that instruction. Scripted PNG/PDF/SVG proofs are descriptive reconstructions; they do not reproduce or replace the native Prism significance annotations.

## Figure 4: preserve the analysis, expose the observations

The current observation table contains all 37 input identities × 3 tools. The three paired tables preserve exactly the same input IDs. ScMixology2 remains included and explicitly reconstructed. The RAGE lymph-node reference is the 5,978-barcode T/B-containing positive proxy. These are barcode-discovery metrics, not physical-read assignment metrics. Technical runs from the same material remain separate input observations; 37 observations must not be described as 37 independent biological replicates.

The supplied analysis labels do not provide enough evidence here to independently recover the exact statistical procedure, tie handling, multiplicity family, or original software invocation. This is a provenance limitation. No alternative Friedman/Wilcoxon/Dunn procedure or correction was substituted. Descriptive review plots show every input, median, and minimum-to-maximum whiskers.

## Figure 2: preserve the analysis and its denominator contract

Each physical-read partition totals 4,993,805. RAD has 5,000 supplied truth targets, Flexiplex has 3,004 native selected targets, and BLAZE has 5,015 native selected targets (5,000 truth plus 15 extras). Unselected Flexiplex truth targets remain missing rather than zero. Native errors and excluded/unassigned reads do not enter correction-only proportions. The quality sweep reuses one sequence/error collection per size; quality conditions are paired transformations, not biological replicates or new sequence-error simulations.

The immutable external corrected Prism source was verified (SHA256 `dded389f9d8214278f93d2669c64e704bbf2208c47db96bf57a4ce4c77d6d016`). The whole file contains unrelated/superseded sheets and is therefore excluded from this selected-only repository. Its existing analyses, annotations, and caches have not been modified during this work. A clean current native project needs native authoring/inspection. Their interpretation after source-array corrections needs native inspection; no claim is made that this reconstruction has recalculated them.

## Native Prism review that remains unavailable on HPC

1. Open external `rad_data/reviewer_comment_data/paper_revision_20261022/prism/Figure2_corrected_20261022.prism` in licensed Prism as a new review copy. Inspect loading, sheet links, labels, and annotations. Retain the native version and save under a new reviewed name.
2. Compare plotted numbers to `assignment_six_states.tsv`, `assignment_per_target.tsv`, and `correction_only.tsv`. Keep blank unselected truth targets; keep genuine selected-target zero values.
3. Preserve correction-doughnut exclusion of rows 0 and 3–5. Corrected denominators: RAD 2,135,825; Flexiplex 1,680,396; BLAZE 2,014,432. Existing display values are RAD 91.03/8.97%, Flexiplex 83.24/16.76%, and BLAZE 93.4/6.6% (one decimal).
4. The Flexiplex full-truth native increment 222,371 is a separately labeled reference increment, not an observed native count under the selected 3,004-target contract.
5. Preserve existing statistical tests and annotations. Export the existing native analysis tables/settings to document their provenance; record any inconsistency for the author rather than silently replacing tests or significance labels.
6. Export PDF/SVG and PNG from the inspected native file and hash the results. Automated ZIP/JSON/table validation does not establish native load/save/render behavior.

The general Prism structural verifier reports repeated layout-object fenIDs 134 and 135 in both the unchanged V18 source and selected corrected copy. ZIP integrity, JSON, sheet identities, and inspected layout links pass. This predates our copy. Native inspection must determine whether the repeated IDs are tolerated or cause a load problem; this report does not label the file corrupt or native-validated. All 45,000 inspected selected-truth CSV values and blank policies match the independently reconstructed arrays.

## Figure 1

Timing proofs use means ± sample SD over three repetitions. Memory is the maximum GNU-time process maxRSS across detection and demultiplexing, converted from KiB to decimal GB; it is not summed sampled process-tree memory. The HD panel remains unresolved because full bin-mapping creation provenance and the named Seurat/tissue-coordinate assets were not recovered. The wide detection-count totals exactly match original pair-count tables; differences from retained rad_demux quantify separate stages. No pseudocount, zero filling, or imputation was introduced.
