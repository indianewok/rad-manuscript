# RAD manuscript: concrete HPC regeneration handoff

Prepared **23 October 2026** from the Nat Comm manuscript/figure/rebuttal copies, the revision notes and retained `rad_data` analyses, the downloaded manuscript repository, and the live Zenodo record metadata.

## What this audit establishes

**Historical RAGE-seq and the ScTagger quality sweep remain the main experimental-provenance questions. There is also a substantial repository integration job.** The GitHub repository represents the old Figures 2–5, and its raw-run drivers do not rebuild the saved workspaces subsequently used for plotting. Current Figures 4, 6 and 7 are largely outside that repository. This handoff identifies what can be recovered, what must be rebuilt, what needs a decision, and what evidence is required before calling a figure reproducible.

The latest LongBench genotype and expression analyses have useful downstream checkpoints. Start there rather than scheduling an indiscriminate full rerun. Missing paths in the local preservation mirror are restore requests for the HPC agent, not proof that the original HPC data no longer exist.

## Deliverables in this package

| File | Purpose |
|---|---|
| [AGENT_START_HERE.md](AGENT_START_HERE.md) | Standalone instructions to give the HPC agent |
| [TASK_INDEX.md](TASK_INDEX.md) | Readable overview of all 36 tasks |
| [REGENERATION_MATRIX.tsv](REGENERATION_MATRIX.tsv) | Short, filterable task list, priority, dependencies and decisions |
| [regeneration_tasks.json](regeneration_tasks.json) | Exact inputs, existing scripts, requested checkpoints, actions and acceptance tests |
| [AUTHOR_DECISIONS.md](AUTHOR_DECISIONS.md) | Settled scope, pending choices and corrections to older notes |
| [REPOSITORY_AUDIT.md](REPOSITORY_AUDIT.md) | Concrete repository defects, old/current figure mapping and Zenodo findings |
| [CHECKPOINT_AND_RELEASE_SPEC.md](CHECKPOINT_AND_RELEASE_SPEC.md) | Stage schemas, counting rules, validation and proposed release layout |
| [components/figures_1_2_4.md](components/figures_1_2_4.md) | Workflow/runtime/HD, synthetic sweep and 37-input analysis |
| [components/figure_3.md](components/figure_3.md) | Off-list controls and LongBench correction/failure audit |
| [components/figures_5_6_7.md](components/figures_5_6_7.md) | Receptor/LR-Split-seq, genotype and expression analyses |
| `templates/` | Empty dataset, asset, panel, statistical, claim and validation tables plus an example run manifest |
| `audit/` | Repository/file hashes, metadata snapshots, availability and preparation checks |
| `context/` | Frozen revision notes and source/working document copies; superseded notes are retained as evidence |
| [TRANSFER_AND_AVAILABILITY.tsv](TRANSFER_AND_AVAILABILITY.tsv) | Named assets, local availability and transfer/restore actions |
| `checkpoint_snapshots/` | Selected compact checkpoint/provenance files, with hashes and original paths |
| `code_snapshots/` | Selected existing analysis scripts collected for transport, with original-path/hash mapping; these are not yet a portable integrated workflow |
| Parent repository | Manuscript code; audited baseline `3465937aa6a8e51b9f6989e750d45990a2a3d7d6` is retained in Git history |

## GitHub edition

This directory contains the handoff that the author requested be pushed to GitHub. Start at `AGENT_START_HERE.md`. The original ZIP and a duplicate nested checkout are omitted; the parent repository contains the code and its history. Original local paths remain in the evidence and asset registry and must be mapped on HPC. The local audit’s “no GitHub push” statement below describes work completed before this later authorized upload.

## Source roots and authority

- Local retained project material: `/Volumes/rad_data/reviewer_comment_data`.
- Revision notes and products: `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022`.
- This handoff: `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/hpc_handoff_20261023`.
- Source/working manuscript copies: `/Users/cmv/Desktop/RAD_paper_revision_2026-10-22`; byte copies are included under `context/manuscript_documents/`.
- Other referenced `rad_data` folders may be inspected. Original `/scratch/f005f43/...` and Dartmouth paths in retained manifests must be mapped or restored on HPC.
- GitHub: https://github.com/indianewok/rad-manuscript, audited commit **`3465937aa6a8e51b9f6989e750d45990a2a3d7d6`**. This repository's RAD/software pins are not the pins for all revised experiments.
- Public archive: https://zenodo.org/records/20189813. Four legacy RData files total **6,194,634,418 bytes**. Their contents were not downloaded for this audit. The API describes a published/open record and lists the preprint DOI; the README's private-draft/Zenodo-DOI description conflicts with that metadata.

Current author decisions take precedence over older note snapshots. Retained executed commands and hashed artifacts establish what actually ran; proposed Methods language does not override conflicting execution evidence. When they disagree, report the difference and reconcile it before publication.

## First work to assign, in order

1. **Inventory and freeze the selected analysis (G-01).** Map paths on HPC; verify source/reference identity and checkpoint availability. Build one registry for the 37 benchmark inputs plus the additional analyses and matched references. Record native versus reconstructed input, public/controlled access, parent dataset/library relationships, and all run-specific tool pins. Capture the accepted current figure list and unresolved decisions.
2. **Recover the archival and execution context (G-02, G-03).** Download/verify/index the four public workspaces; preserve them as legacy evidence. Collect the exact executed scripts, diagnostic Flexiplex patch/source, historical RAD sources/binaries, reference files, catalog/model hashes and environment records. A version string alone is insufficient.
3. **Resolve the two major provenance branches without stalling other work.** For ScTagger, restore the selected generator/model/path/effective-seed/input lineage and reproduce retained checkpoints before proposing a new generator. For historical RAGE, recover original lists/output/logs if possible and present a concrete retain/qualify/replace choice; do not use ambiguous inferred barcode identities in paired analyses.
4. **Restore completed figure checkpoints and regenerate source tables.** The component task lists name the earliest useful retained checkpoint for each panel. In parallel, complete runtime/HD provenance, assemble the 37-input table, settle the Figure 5 source-to-artwork mapping, validate the Figure 6 donor/reference/UMAP chain, and rebuild Figure 7A–D from the updated 8,135-gene analysis.
5. **Connect the current repository and finalize statistics (G-04, G-05).** Implement separate render/resume/raw stages with manifests and strict validators. Freeze observation units, pairing, test families and correction before adding final statistical annotations. Record genuine pending choices; most inventory and table reconstruction can proceed immediately.
6. **Validate the whole chain (G-06, G-07).** Produce final source data and editable figures, compare every claim with the selected result, and test clean-environment rendering and checkpoint resumption. Clearly label full raw reruns, pilots and unexecuted branches.
7. **Prepare the revised release (G-08).** Stage code and permitted data/checkpoints, checksums, source-data legends, Methods provenance, validation reports, citation metadata and the corrected archive/repository description for author review. Preserve the old published record and distinguish retired Figure 8 material from the current build.

## Per-figure regeneration summary

| Current figure | What is on hand | Concrete remaining job | Completion gate |
|---|---|---|---|
| **1 — RAD workflow, runtime/memory, Visium HD** | Workflow code/audit, timing packages, HD bin table and renderer; referenced mapping objects | Tie schematic to the selected algorithm/code pin and record historical timing version separately; rebuild timing from logs with hardware/thread settings; restore HD mapping input and verify PBC44593, 16-µm bins and color normalization against artwork | Panel inputs, units and code match the selected artwork; runtime comes from logs |
| **2 — ScTagger** | Two-model sweep scripts and retained results, canonical assignment summaries, native-2023 BLAZE replay and corrected Prism copy | Recover exact generator seeds/model path context, enumerate eleven shifts per model, verify the exact discovery/assignment inputs, whitelist roles and diagnostic extraction, rebuild all plot tables and reopen/recalculate/export Prism | Complete truth/read accounting, exact condition/whitelist lineage and approved final comparison |
| **3 — off-list and correction audit** | Complete newer ScTagger/LongBench challenge results; partial historical RAGE evidence; complete per-target LongBench audit tables | Separate record versus strict-read counting; recover RAGE originals or explicitly replace; export pair-level correction lineage and denominator; refresh correct all-record RAD Prism tables | Explicit Failure Mode 1/2 definitions; correct units; no unsupported barcode pairing; tests based on approved design |
| **4 — 37-input comparison** | Sample inventory, three-tool metrics, reference and input provenance, SeqKit summaries | Integrate all 37 inputs, qualify reconstructed ScMixology2 and controlled spatial libraries, verify exact detection/assignment definitions, rebuild source tables and final paired/repeated statistics | Registry covers all inputs, each tool result has provenance, captions use correct metric/source |
| **5 — RAGE receptors and LR-Split-seq** | Candidate receptor outputs/annotations; recovered LR-Split-seq ED2/poly-T ledgers, labeled 568-cell table and saved paired-t analysis | Validate recovered checkpoints; bind receptor/UMI panels to their selected runs and reconcile full-input counting units | One selected source-to-artwork chain per panel, with executed statistics and paired IDs |
| **6 — LongBench genotype** | Three large per-tool alignment files, CellSNP matrices, validated donor VCF and fixed coordinates | Validate donor/reference identities and label joins; export per-cell status and denominator tables; verify the fixed UMAP's normalization provenance; finalize statistical design | Resume from validated heavy checkpoints; no mixing missing, unassigned and absent-whitelist states |
| **7 — LongBench expression** | Native count matrices and updated DE/threshold-sweep packages; current A/C replacements can be regenerated | Preserve RAD emitted segments and inherited gene assignments; restore absent upstream FASTQ/read→gene artifacts only if raw replay needed; regenerate A–D using common 8,135 genes | Common tested universe and direction/threshold metrics agree across panels; 7E remains explicitly pending |

HPC owns recovery, computation, validation, portable tables and scripted renders. A Prism-capable desktop agent or the author must complete native Prism reopen/recalculation/export; this should be an explicit handback item if Prism is unavailable on HPC.

The detailed components distinguish verified small-table contents from metadata-only large-file availability. Historical values are regression references, not targets to force a changed analysis to reproduce.

## Decisions that require the author

Full descriptions are in `AUTHOR_DECISIONS.md`. Prepare the underlying tables/design before requesting a decision:

- historical RAGE: recovery/qualified retention versus a new matched replacement;
- ScTagger: selection of a separately versioned replacement only if historical input restoration is insufficient; pathname-independent seed change remains deferred;
- Figure 4 paired/repeated tests; Figure 6 factor structure and comparisons; LR-Split-seq paired test; Figure 2/3 observation unit and multiplicity;
- Figure 7E completion or removal;
- final artwork selection and publication/repository visibility.

No reconfirmation is needed for all 37 inputs, updated 8,135-gene Figure 7, measured failure-mode definitions, removed Figure 8 or inspection of referenced project folders.

## What a completed HPC handback must contain

For each task: status, exact run/configuration, code/binary/input hashes, retained or regenerated checkpoint, validator results, discrepancies and next dependencies. For each panel: raw acquisition path, minimum resume checkpoint, compact source-data table, renderer/editable figure, final export, caption/test and a claim-to-source mapping.

The final release must demonstrate lightweight rendering and checkpoint resumption separately from raw reruns. Supply a clear exception list for any raw step that could not be repeated. The deliverable is an upload-ready, versioned code/data package and a validated manuscript/rebuttal evidence trail. Neither a successful old shell script nor a matching screenshot alone meets this standard.

## Scope of work completed in this local audit

The manuscript repository was downloaded and examined; historical and current figure scopes were mapped; retained code, manifests and selected checkpoint tables were inspected; public archive metadata was captured; small-source snapshots and machine-readable task/availability manifests were prepared. The original documents and downloaded repository were preserved. No full HPC analyses, native Prism recalculation, GitHub push, Zenodo upload or publication were performed during this handoff preparation.
