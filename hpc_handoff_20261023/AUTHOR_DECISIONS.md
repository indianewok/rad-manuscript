# Author decisions and unresolved choices

This file carries decisions made in the paper-revision conversation through 23 October 2026. It takes precedence over older notes copied into `context/`. The component audits contain the source evidence and exact paths. This is a handoff of settled scope and pending choices, not approval to publish or to substitute a new experiment silently.

## Settled scope

- Use the **Nat Comm** manuscript sources. The three original documents were copied into `/Users/cmv/Desktop/RAD_paper_revision_2026-10-22/sources/`. Work from those copies and the working revisions, not the Dropbox originals.
- Save new analysis/material under `/Volumes/rad_data/reviewer_comment_data` on the local system; use a mapped project root on HPC. Inspection of referenced directories elsewhere on `rad_data` is authorized.
- The current paper has Figures **1–7**. **Figure 8 is removed**, including its dedicated clonotype/isotype/membrane-versus-secreted methods and exclusive references. The eight Engblom benchmark libraries remain in Figure 4.
- Include **all 37 inputs** in Figure 4, including reconstructed ScMixology2. Preserve native/reconstructed and technical-library relationships in the source registry.
- Use the **updated Figure 7 analysis**: 8,135 common eligible genes and the RAD matrix that retains emitted concatemer segments. Old 8,126-gene Figure 7A/C material must be replaced. Panel D and the rebuttal were already based on the updated analysis.
- Figure 7E (“Olivia…”) is pending. Do not invent its analysis or treat it as completed. Other panels can proceed.
- Figure 3 must use the observed correction/failure categories, explicitly named **Failure Mode 1** and **Failure Mode 2**, rather than assigning a biological origin to a read from barcode-set membership alone.
- The Measles P7, P8 VDJ-enriched and P8 WTA datasets are from **Beaulaurier et al.**, not newly generated data awaiting deposition by this group. The source-data audit resolves their accessions.
- Methods should be full methods in clear, direct language, defaulting to ASD-STE100 style and avoiding “we.” Remove outcome/cohort totals from narrative Methods where they belong in Results, while preserving the parameters needed to reproduce an analysis.

## Canonical Figure 3 definitions

All three classes require that the observed raw barcode changes to a tool-selected target.

| Class | Observed source | Selected target |
|---|---|---|
| Corrected off-list | Outside the full chemistry barcode catalog | A barcode selected by that tool |
| **Failure Mode 1** | In the chemistry catalog, outside the matched Cell Ranger filtered set | A barcode selected by that tool |
| **Failure Mode 2** | In the matched Cell Ranger filtered set | A different barcode that belongs to both that filtered set and the tool-selected set |

The biological rationale is to examine reassignment of valid barcode sequences from outside the reference-supported population, and reassignment between reference-supported cells/nuclei. Use the actual source/target definitions in the schematic, Methods and table schema. The counting unit is a unique original-read–target-barcode pair; duplicate pairs collapse, different targets remain. Per-target percentages divide by all unique assignments to that target for the corresponding tool. Save observed raw sequence, catalog/reference membership and target selection so classifications remain auditable. Group pairs within each class: different source-bearing records for the same read–target pair can produce more than one class flag. Preserve the observed source set and class overlaps; the classes are not an exhaustive or mutually exclusive partition. Do not use the sum of their counts as the Figure 3G denominator. A zero total-assignment denominator gives a null percentage; a missing raw source is not evidence of a noncatalog barcode.

## ScTagger choices and provenance

- The “Large” source has 4,993,805 reads from 5,000 known source barcodes. Keep read sequences and sequence-error patterns fixed while changing quality scores.
- Final documented quality models are Badread **Nanopore2018** and **Nanopore2023**. Background bases sample the model-wide quality distribution. Barcode bases sample a distribution conditioned on the alignment of the observed barcode to its known source. Reads with no located barcode retain background qualities.
- Selected base seed for the final **ScTagger-L** conditions: **20260731**. The archived Nanopore2018 **ScTagger-S** generation uses **20260727**; do not describe the two sizes as having the same seed. Historical background quality-tape seeds also depend on the model file pathname and a purpose label. The same selected seed therefore does not by itself guarantee identical draws after moving a model file.
- Document all eleven shifts for each model. Nanopore2018: **+1, +2, +3, +4, +5, +6, +8, +10, +11, +12, +13**. Nanopore2023: **−17, −16, −15, −14, −12, −11, −9, −7, −6, −5, −4**. The unshifted native Nanopore2023 condition is separately retained. Apply the historical shift/clipping and pairing rules exactly as recorded in the executed generator and component audit; do not substitute the older Desktop “ScTagger sweep” document's eight-shift/seed recipe.
- The author requested a **note** to remove pathname dependence from the maintained generator. This was explicitly deferred: `context/CODE_FOLLOWUPS.md`. Exact historical replay and a future path-independent generator are separate tasks. Record a new run/version and compare affected results if the latter is authorized and used.
- The author requested a corrected **copy** of the Figure 2 Prism file and will open it later. `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/Figure2_corrected_20261022.prism` has file-level/data-array checks, but has not passed a native Prism reopen/recalculate/export check. Do not edit the unrelated open Prism project.
- Flexiplex output has a corrected CB tag. The diagnostic build was needed to retain **raw extracted barcodes**, not because final CB was absent. Preserve the diagnostic source/patch and prove that source truth is not injected into extraction. BLAZE's matched output is `matched_reads.fastq.gz`; raw extractions are in `putative_bc.csv`.

## Updated LongBench expression definitions

Use the native positive-depth, genotype-assigned cohorts, excluding doublets and unassigned nuclei. The final code/evidence, rather than a fixed cohort count in Methods, defines membership. Eligibility is at least ten counted molecules across the compared groups and detection in at least 1% of included positive-depth nuclei. Normalize with each nucleus's total counts **before gene filtering**, to 10,000; use `log2(1 + normalized count)`. Use two-sided Wilcoxon rank-sum tests and BH adjustment as recorded in the executed workflow. Effect sizes use `log2((mean target normalized count + 0.1)/(mean comparison normalized count + 0.1))`.

For the direct H146/H526 comparison, use the common 8,135-gene set and recalculate BH adjustment within that set for every platform. The Illumina reference uses adjusted P < 0.05 and absolute log2 fold change > 1; evaluate directions separately. The long-read threshold sweep uses adjusted-P cutoffs `1e-8, 1e-6, 1e-5, 1e-4, 0.001, 0.005, 0.01, 0.05, 0.1` and absolute log2-fold-change cutoffs `0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3`, with strict < and > comparisons. Keep the Illumina thresholds fixed. F1 is `2TP/(2TP + FP + FN)`, or zero when its denominator is zero. Preserve separate eligibility/threshold definitions for the broader cell-line-versus-rest analyses; do not transfer this direct-comparison threshold to all contrasts.

## Decisions still needed

These are targeted scientific or release choices. Independent inventory, parsing, descriptive summaries and checkpoint validation can proceed now.

| ID | Choice | Preparation the HPC agent should deliver before asking |
|---|---|---|
| D01 | Historical RAGE off-list: retain a clearly qualified historical result, recover exact original evidence, or replace it with a fully documented matched experiment? | Show missing lists/seeds/logs, count-unit differences and ambiguous inferred barcode identities. Supply the proposed replacement's catalog, exclusion set, sample size, seeds, tool versions and counting rule. Do not present new samples as recovered history. |
| D02 | If archived synthetic inputs cannot be restored, which ScTagger rerun becomes the release analysis? | First try exact historical replay with effective seeds/path metadata. Report the effect of a path-independent generator only in a separately versioned comparison if authorized. The existing deferred note is not approval to change canonical outputs. |
| D03 | Figure 4 final repeated/paired statistical procedure | All 37 inputs are confirmed. Show the analysis unit and pairing, Li Song's paired-Wilcoxon comment and existing Friedman/Dunn description; propose a coherent test and correction for approval. |
| D04 | Figure 6 one-way versus two-way ANOVA and comparisons | Show the actual response table, factors and replication. Margaret's comment was dated 24 September 2026, 09:13 UTC; current legend mentions one-way ANOVA/Dunnett. Do not infer independent replication from cell-line categories. |
| D05 | LR-Split-seq final paired test | Resolve the text's Wilcoxon signed-rank label versus legend's paired t-test label. Locate executed statistics or recompute both from the same explicitly paired observations and show their implications. |
| D06 | Figure 2/3 inferential unit, pairing and multiplicity | Distinguish input/list replicates from nested barcode observations. Present final observation table and proposed tests before updating annotations. |
| D07 | Figure 7E inclusion and analysis | Obtain the collaborator's completed analysis definition/code/output or an author decision to remove the panel. Do not block completion of 7A–D. |
| D08 | Final artifact selection and release publication | Present completed panel-to-source mapping, Prism exports, discrepancy report and upload-ready release. Author selects remaining artwork/analysis alternatives and approves publishing/visibility changes. |

## Source findings that must be reflected in captions and Methods

- The accepted September Figure 1B–C timing package uses **LongBench single-nucleus ONT (SN-ONT)** and **single-cell PacBio (SC-PB)**, not single-cell ONT. Preserve its AMD EPYC 7543 hardware stratum, 4/16/64 requested threads, three repetitions and phase timing/resource definitions. Correct any conflicting panel/source label after checking the selected artwork.
- The expanded ScTagger archive establishes Nanopore2018 S/L and Nanopore2023 L discovery sweeps. It does not establish a Nanopore2023 S or full assignment-at-every-shift sweep. Such extensions would be new scope.

## Superseded notes to interpret carefully

- `context/revision_status.json` is a historical snapshot, not the latest authority on unresolved items.
- Older “Measles needs accession” notes are resolved by Beaulaurier provenance and the saved accession inventory.
- Earlier missing-UMAP/missing-genotype notes are partly resolved by retained durable bundles and the referenced external UMAP project. The fixed-coordinate versus RDS normalization provenance still needs validation as described in the Figure 6 component.
- The old RAD matrix README's “DEGs stale” warning is superseded by the documented 28 August 2026 DEG regeneration; use the exact updated artifacts specified for Figure 7.
- The old 8,126-gene analysis remains historical, not canonical.
- GitHub/older local notes call Zenodo a private draft. The 23 October public API snapshot in `audit/` shows a published/open record. Its DOI inconsistency must be reconciled.
- Whole-session legacy RData files and old figure numbers must not override the current panel definitions.

The working manuscript v3 predates some accepted paragraph edits in the conversation. Reconcile final Methods, Results, legends and rebuttal with the selected validated workflows; do not assume every later refinement is already in the DOCX.
