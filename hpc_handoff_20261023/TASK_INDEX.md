# Task index

36 tasks: 19 P0 (inventory/provenance/recovery), 14 P1 (regeneration/integration/validation), 2 P2 (pending panel/release), and 1 deferred code follow-up. See the full JSON for inputs, scripts and acceptance criteria. Deferred F2-05 does not gate the current release.

| ID | Priority | Task | Dependencies |
|---|---|---|---|
| G-01 | P0 | Freeze the current analysis and resolve assets on HPC before regenerating. |  |
| G-02 | P0 | Index and reconcile the legacy public Zenodo workspaces. | G-01 |
| G-03 | P0 | Recover executable provenance and lock the environments for each selected workflow. | G-01 |
| G-04 | P1 | Build the current Figures 1-7 stage graph with resumable, validated checkpoints. | G-01, G-03 |
| G-05 | P1 | Freeze statistical designs and export auditable test inputs/results. | G-01 |
| G-06 | P1 | Integrate final figures and reconcile Methods, Results, legends and rebuttal with evidence. | G-04, G-05, F1-01, F1-02, F1-03, F2-01, F2-02, F2-03, F2-04, F4-01, F4-02, F4-03, F3-01, F3-02, F3-03, F3-04, F3-05, F3-06, F3-07, F3-08, F3-09, F5-01, F5-02, F6-01, F6-02, F6-03, F7-01, F7-02, F7-03 |
| G-07 | P1 | Demonstrate reproducibility in a clean HPC environment and report each level separately. | G-04, G-06 |
| G-08 | P2 | Prepare the revised GitHub and Zenodo release, metadata and publication handoff. | G-02, G-07 |
| F1-01 | P1 | Reconcile workflow schematic with the pinned code and Methods without substituting current code for historical benchmarks. | G-01 |
| F1-02 | P0 | Rebuild computational-efficiency tables from accepted September runs; rerun sequence processing only for missing/failed checkpoints. | G-01 |
| F1-03 | P1 | Recover and render the Visium HD spatial triptych from the archived plotting recipe and validate the upstream RAD bin-count mapping. | G-01 |
| F2-01 | P0 | Freeze original sequences, truth and historical quality-generator contracts before any regeneration. | G-01 |
| F2-02 | P1 | Reuse or rebuild the complete archived 2018 S/L and 2023 L quality-discovery sweeps without conflating replay with demultiplexing. | G-01, F2-01 |
| F2-03 | P0 | Retain the completed native-2023 assignment replay and exact RAD/Flexiplex audit categories; rebuild only from preserved checkpoints if required. | G-01, F2-01 |
| F2-04 | P1 | Finish native Prism review, approved statistics and publication exports of the already corrected Figure 2 copy. | G-01, F2-03 |
| F2-05 | DEFERRED | Record the path-dependent random-number issue and define the boundary for a possible future portable generator. | G-01 |
| F4-01 | P0 | Rebuild the complete 37-input barcode-detection comparison with the corrected immune reference and explicit reconstruction status. | G-01 |
| F4-02 | P1 | Preserve current all-input SeqKit summaries and recover the execution provenance; regenerate only if the missing provenance cannot be recovered. | G-01, F4-01 |
| F4-03 | P1 | Build the selected all-37-input plots and resolve final inferential tests without reusing native-only statistics. | G-01, F4-01, F4-02 |
| F3-01 | P0 | Freeze the intended historical/replacement scope before any regeneration. | G-01 |
| F3-02 | P0 | Recover or explicitly bound the historical RAGE-seq replay. | G-01, F3-01 |
| F3-03 | P0 | Restore portable, pinned ScTagger/LongBench off-list execution and aggregation. | G-01, F3-01 |
| F3-04 | P0 | Build an auditable strict physical-read ledger and off-list checkpoint tables. | G-01, F3-03 |
| F3-05 | P1 | Conditional new RAGE-seq matched off-list experiment, explicitly separate from historical replay. | G-01, F3-01, F3-02, F3-03, F3-04 |
| F3-06 | P0 | Restore all 12 LongBench assignment/source-evidence contracts with version and CT scope pinned. | G-01, F3-01 |
| F3-07 | P0 | Regenerate measured barcode-category checkpoints with exact pair-level grouping. | G-01, F3-06 |
| F3-08 | P0 | Produce explicit graph bindings and defensible statistics from identity-bearing source data. | G-01, F3-02, F3-04, F3-07 |
| F3-09 | P1 | Package a releasable raw-to-figure workflow with a small independent smoke test. | G-01, F3-01, F3-02, F3-03, F3-04, F3-06, F3-07, F3-08 |
| F5-01 | P0 | Identify the exact RAGE receptor/cell-label source for each current panel before regenerating. | G-01 |
| F5-02 | P0 | Recover final component-based LR-Split-seq comparison and its paired read/UMI tables. | G-01 |
| F6-01 | P0 | Validate and preserve the independent bulk genotype panel and short-read reference. | G-01 |
| F6-02 | P0 | Resume per-tool genotype analysis from retained alignments and CellSNP checkpoints. | G-01, F6-01 |
| F6-03 | P1 | Validate fixed UMAP provenance and regenerate genotype overlays/statistical inputs. | G-01, F6-02 |
| F7-01 | P0 | Preserve and validate updated native expression matrices and their raw-read/segment lineage. | G-01 |
| F7-02 | P1 | Regenerate common-universe expression results, Venn/confidence panels and directional threshold grids. | G-01, F7-01 |
| F7-03 | P2 | Keep pending collaborator panel explicit until its definition and sources arrive. | G-01 |
