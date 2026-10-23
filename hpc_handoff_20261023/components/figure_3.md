# Figure 3: HPC regeneration handoff

Prepared 23 October 2026. This is an inventory and execution plan, not a rerun. Inspection was limited to named provenance files, code and small checkpoint tables. Sequencing files were checked by filesystem metadata only. No source document, raw sequence, original Prism file or external repository was changed.

## Decision boundary

**Do not silently replace historical RAGE-seq with a new matched experiment.** Some original inputs and settings are missing, its counting unit differs from the two newer challenges, and reconstructed BLAZE barcode identities are not uniquely established. Task F3-01 records the author's scope decision; F3-02 covers limited historical recovery and replay; F3-05 is a separate, conditional replacement experiment. A new tool build cannot be described as a replay of the original experiment.

The user has already approved the measured source-barcode classes for D–G. These do not identify biological origins. The corrected schematic is `W/github_audit/figure3_measured_categories/Figure3_measured_failure_modes_20261022.pdf` and its sibling PNG. The matching working figures document is `/Users/cmv/Desktop/RAD_paper_revision_2026-10-22/working/RAD_R1_figures_and_legends_failure_modes_2026-10-22.docx`.

## Canonical source map

Path abbreviations:

- `B=/Volumes/rad_data/reviewer_comment_data`
- `W=/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022`

| Scope | Available source package | Present evidence | Important gap |
|---|---|---|---|
| Historical RAGE, A–C | `B/rageseq_false_whitelist_manuscript_era_20260817` | Three reconstructed lists of 4,505 targets; record-count tables; Flex strict-count companion; reconciliation; scripts; validation and checksums | Original dummy lists, seeds, input identity, RAD build and BLAZE execution/output are unavailable in the package. RAD/Flex originals are referenced at old Dropbox locations. The assembler requires absent temporary JSON files. |
| ScTagger-L, A–C | `B/sctagger_L_false_whitelist_20260813` | Lists, catalog, truth reference, runner/parser/generator/auditor code; all nine sets of logs, exit metadata and FASTQs; full BLAZE extraction tables; Flex diagnostic sidecars; strict summaries | Runtime paths are hardcoded. Historical RAD binary/source must be pinned for replay. Using current code would constitute a new experiment. |
| LongBench SC-ONT, A–C | `B/longbench_sc_ont_false_whitelist_20260813` | Lists, seed manifest, input hashes, all nine sets of run logs and outputs, full BLAZE extraction tables, Flex sidecars and strict summaries | Only the list generator is shipped in `scripts`. The package builder and sample/run wrappers need recovery or reconstruction. The raw-input symlink is dangling locally. The exact 10-million-read input is recorded at an HPC scratch path but was not located here. |
| Latest RAD, D–G | `B/scratch_preservation_20260921/files/longbench_rad_4acbe00_raw_prism_20260827` | Pinned Linux RAD 4acbe00 binary, C++/Python audit code, selected lists, layouts, catalog, producer logs, exact all-record audit checkpoints, Prism archive and closure reports | Emitted RAD FASTQs are absent from the inspected preserved demultiplexing folders. Full raw input paths are absent locally. Build-source recovery must match 4acbe00. |
| BLAZE/Flex, D–G | `B/LongBench_comps/full_A_to_B_audit_20260731` | All eight complete-input summary and per-target result sets; producer metadata, executed analysis code, Flex diagnostic validation, reference lists and manifests | Full BLAZE extraction/FASTQ and Flex raw-source sidecars are referenced at scratch locations; current availability is unverified. Historical BLAZE hash seed was unset. |

Earlier sources must remain clearly labeled. August 25 allocation tables use earlier RAD values that excluded CT-derived records. The August 27 raw 4acbe00 all-record tables supersede those RAD columns. The `audit_raw_all` folders are incomplete for SC_ONT and SC_PB. Use `runs/{arm}/audit_raw_all_fast_exact` for all four complete current RAD checkpoint sets. Each contains `summary.tsv`, `per_target.tsv` and `invariants.tsv`. Saved validation reports establish agreement between fast and exact all-record audits, plus Python parity for the CT-excluded scope. These full-data checks were not rerun for this handoff.

## A–C: experiment contracts and historical conflicts

### ScTagger and LongBench

ScTagger uses 4,993,805 flat-Q20 reads and three lists of 5,000 targets drawn from the full 6,794,880-entry 10x 3′ v3 catalog, excluding all 5,000 truth barcodes. The generator records Python 3.9.16 `random.Random`/MT19937 seeds 20260813, 20260814 and 20260815. The input is present at `B/wl_scan/20260731_sctagger_badread_quality_full/inputs/L/flatQ20.fq.gz` (3.07 GB by filesystem metadata). Its recorded SHA-256 is `6f7385468b607cf86c91449b095c2968ee2a5d25ab473901102b87d141543090`.

LongBench uses the exact 10,000,000-read SeqKit 2.8.2 sample generated with `sample -2 -n10000000 -s2026081326`. Its recorded compressed SHA-256 is `ecb19387e6cad1f7095ea95b183b5c30d3ac83c9ced67df53fddde885398689a`. The three lists each contain 5,211 targets and exclude the matched 5,211-cell Illumina reference. List seeds are 2026081301, 2026081302 and 2026081303. The sample is recorded at `/scratch/f005f43/longbench_sc_ont_false_whitelist_20260813/fastq/SC_ONT_10M_seqkit_seed2026081326.fastq.gz`.

The local `inputs/SC_ONT.fastq.gz` symlink is dangling, and the expected `/Volumes/rad_data/raw_fastq_datasets/longbench/raw_fastq/` input files were absent. The independent F1 inventory also did not locate the exact 10-million-read sample. This requires restoration or HPC preflight; it does not establish that the HPC data are lost. Full-input metadata also survives at `B/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/provenance/input_manifest.tsv`, with original paths under `/scratch-nfs/f005f43/rad_longbench_20260726/data/sc_sn/raw_fastq/`.

Both newer packages use **strict physical-read counts**. After original-ID normalization, more than one assignment row excludes every assignment for that ID, even if both rows have the same target. Supplied targets with zero counts remain in the table. Flex sidecars include valid assignments with empty trimmed sequences that emit no FASTQ record. LongBench has 4, 1 and 0 such rows across its replicates, zero FASTQ-only rows and zero mismatches among shared ID groups. Record counts, ambiguous IDs and strict assigned counts must remain separate. ScTagger's existing `unassigned_by_unique_id` field means no observed assignment; it excludes ambiguous IDs from that count.

| Dataset/tool | Strict assigned counts, replicates 1 / 2 / 3 |
|---|---|
| ScTagger RAD | 48,997 / 49,004 / 49,292 |
| ScTagger BLAZE | 294,175 / 304,701 / 299,332 |
| ScTagger Flex | 462,690 / 465,375 / 458,773 |
| LongBench RAD | 46,487 / 46,961 / 46,568 |
| LongBench BLAZE | 1,005,393 / 1,024,563 / 1,097,594 |
| LongBench Flex | 1,364,364 / 1,370,330 / 1,422,565 |

RAD metadata pins commit `cd0582b2440cde0f35725dc557fa47307d74d374`, version 1.0.2 and binary SHA-256 `80a573fe05fa1a236751240fad7da17ca00e2d55a95259ca997584a8a5e0e67c`. Both challenges predate the 17 August adapter repair. BLAZE 2.6.0a0 uses supplied lists without discovery, chemistry 3′ v3, Q15 and edit distance 2. The Flex 1.02.6 diagnostic build uses the 10x 3′ v3 layout, flank threshold 8 and barcode edit distance 2. Preserve actual commands and binary hashes for each run; version strings alone are insufficient.

Existing ScTagger entrypoints are under `B/sctagger_L_false_whitelist_20260813/scripts`: `generate_sctagger_false_whitelists.py`, three `run_sctagger_false_*.sh` runners, `aggregate_sctagger_false_results.py`, `independent_audit_sctagger_false.py` and list validators. LongBench ships `scripts/generate_false_whitelists.py`. Its recorded package builder, `/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/rad/scripts/build_longbench_sc_ont_false_package.py`, is missing from the package and the two inspected source snapshots. An old builder failure predates the final sidecar-subset policy; do not treat that historical failure as failure of the final preserved package.

### Historical RAGE-seq

The package records RAD runs from 28 August 2025, Flex 1.02.5 runs from 22 October 2025, and BLAZE counts recovered from `041026_Figure_3_CMV.prism`. Three lists of 4,505 targets were reconstructed from assignments; their union contains 13,426 targets. The original sampling seed and list-generation record are unavailable. The historical per-barcode values are **record counts**, not strict counts of uniquely assigned physical reads.

| Tool | Per-barcode sums, replicates 1 / 2 / 3 | Historical headlines, replicates 1 / 2 / 3 | Distinction |
|---|---|---|---|
| RAD | 49,816 / 49,942 / 49,232 | 49,816 / 49,942 / 49,232 | Counts retain 128 / 143 / 147 duplicate physical IDs. |
| BLAZE | 1,355,389 / 1,403,176 / 1,357,996 | 1,354,508 / 1,402,306 / 1,357,281 | Differences are 881 / 870 / 715; original read-level evidence is absent. |
| Flex | 1,597,157 / 1,679,710 / 1,647,416 | 1,591,111 / 1,672,992 / 1,640,883 | Headline comes from the tool's reads-with-barcode log; emitted record count differs. |
| Flex strict companion | 1,584,869 / 1,666,073 / 1,634,153 | Not the current headline | Excludes 6,127 / 6,796 / 6,617 multiply assigned IDs. |

The old README attributes BLAZE differences to reported but non-emitted reads. Without original outputs, that is an unverified explanation. The inspected native evidence copy retains historical headline numbers and per-barcode record counts. These cannot be presented as a uniform counting unit without correction or disclosure.

**Inferred barcode identities block paired analysis.** Historical Prism 3E lacks barcode labels. Its RAD count column agrees with lexical barcode order, but ties make this test nonunique: 4,498, 4,496 and 4,492 of 4,505 rows belong to equal-count groups. The largest tied groups contain 3,205, 3,168 and 3,202 rows. A BLAZE row therefore has an inferred barcode identity unless an original labeled table or exporter proves its ordering. Preserve its count distribution, total and original row index. Do not use these inferred labels for barcode-paired cross-tool tests. In the newer experiments, lexical rank pairs tools within a replicate; equal rank across independently sampled replicate lists does not identify the same barcode.

The existing native-source audit is `W/evidence/figure2_prism_audit.md`. The off-list headline data sheet is `969A7A49-AD72-4F65-A725-A8B9E0A0CEC8`; the per-barcode sheet is `F0694302-5FC9-439B-9C62-B69220EEE154`. CSV copies are under `W/evidence/figure2_native_tables/`. The saved per-barcode graph binds replicate 1 only. Changing that presentation requires an explicit analysis decision; the presence of 27 data columns does not mean all replicates are plotted.

Historical scripts are under `B/rageseq_false_whitelist_manuscript_era_20260817/scripts`: `assemble_rage_pkg.py`, `flex_offlist_tab.py`, `flex_strict.py` and `flex_rules.py`. The assembler requires absent temporary JSON intermediates. Upstream RAD/BLAZE extraction code is not shipped. Original RAD/Flex files are referenced at specific old Dropbox paths, but no drive mirror was established in this scoped audit. A historical replay must report aggregate reproducibility separately from identity-level and read-level reproducibility.

## D–G: approved measured classes and checkpoints

Let `a` be the exact observed source barcode, `b` the assigned target, `C` the full chemistry catalog, `R` the matched Cell Ranger filtered set and `S` the tool-selected set. Only observed changes (`a != b`) qualify.

| Public label | Operational condition | Existing source field |
|---|---|---|
| Corrected off-list | `a` outside `C`; `b` in `S` | `noncatalog_to_selected` |
| Failure Mode 1 | `a` in `C` but not `R`; `b` in `S` | `catalog_noncell_to_selected_A` |
| Failure Mode 2 | `a` in `R`; `b` in both `R` and `S`; `a != b` | `cellranger_to_different_cellranger_K` |

These categories do not identify ambient RNA or missed cells, or establish a correct biological origin. A missing source barcode is not evidence of a noncatalog source. RAD uses `CR` with orientation normalization and treats empty `CR` as native. BLAZE joins the extraction table to emitted assignments. Flex uses `RawCellBarcode`, rather than substituting an edit-distance-zero test for source identity.

The unit is a unique `(physical_read_id, target_barcode)` pair within each category. Repeated records for the same pair collapse. A physical read assigned to multiple targets can contribute multiple pairs. Records for one pair can have different source barcodes and thus multiple class flags; measure the overlap instead of forcing an exhaustive, additive partition. `O` is the count of all unique pairs assigned by that tool to that target. Figure G uses `100 × n/O`, with an undefined value when `O=0`. It is not a percentage among the three error classes. Join per-target tables by barcode identity, retain `selected_by` flags, and use null percentages for zero denominators.

| Dataset | Tool | Corrected off-list | Failure Mode 1 | Failure Mode 2 | All read–target pairs, O |
|---|---|---:|---:|---:|---:|
| SC_ONT | RAD | 9,690,454 | 0 | 0 | 96,569,433 |
| SC_ONT | BLAZE | 8,672,726 | 1,101,618 | 61,301 | 93,175,479 |
| SC_ONT | Flexiplex | 10,386,527 | 1,429,752 | 31 | 103,475,960 |
| SN_ONT | RAD | 8,311,132 | 0 | 0 | 57,487,924 |
| SN_ONT | BLAZE | 5,800,878 | 10,562,779 | 738,294 | 59,984,175 |
| SN_ONT | Flexiplex | 8,221,126 | 14,331,912 | 108,704 | 73,883,233 |
| SC_PB | RAD | 4,816,829 | 0 | 0 | 178,846,937 |
| SC_PB | BLAZE | 3,932,949 | 1,511,949 | 122,127 | 178,095,634 |
| SC_PB | Flexiplex | 4,331,943 | 1,876,614 | 11 | 185,509,618 |
| SN_PB | RAD | 3,945,475 | 0 | 0 | 86,368,809 |
| SN_PB | BLAZE | 2,304,139 | 17,061,625 | 1,267,182 | 93,568,220 |
| SN_PB | Flexiplex | 3,292,660 | 21,703,944 | 202,701 | 107,301,108 |

These values were read from small saved tables, not generated by new sequence analyses. Current RAD 4acbe00 results include CT-derived records. The all-record Prism closure reports changes to 13 raw CSV tables and their 13 binary counterparts, with unrelated archive members preserved. Historical BLAZE 2.5.0 producer metadata records `PYTHONHASHSEED=UNSET`. If its outputs are lost, new tie assignments cannot be claimed as a bitwise historical replay without restored iteration evidence. One BLAZE `input_size_bytes=21` entry reflects a symlink-size artifact and does not validate the raw input content.

D–G RAD scripts reside under `B/scratch_preservation_20260921/files/longbench_rad_4acbe00_raw_prism_20260827/scripts`: `analyze_correction_events.py`, `fast_rad_raw_audit.cpp`, `validate_fast_rad_raw_audit.py`, `run_one_arm.sh` and `run_one_audit_all.sh`. Competitor executed analyzers and runners are under `B/LongBench_comps/full_A_to_B_audit_20260731/provenance/scripts`.

`update_raw_longbench_prism.py` updates selected RAD tables; it is not a complete raw-to-figure pipeline. Its default `audit_raw_noct` conflicts with the current all-record scope. Its hardcoded external `prism_tool.py` dependency and source-archive hash must be restored or pinned explicitly. Old submitters include hardcoded job IDs and paths and must not be run unchanged.

## Checkpoints, acceptance checks and release

The companion JSON contains nine dependency-linked tasks, F3-01 through F3-09. It lists existing scripts and inputs, decisions, new artifacts and acceptance checks. Existing code needs configurable paths before it can run portably.

Required checkpoint schemas:

1. `input_manifest.tsv`: experiment, dataset, accession, source URL, staged path, byte count, compressed SHA-256, decoded ID/sequence hash, record count, quality condition and scope.
2. `tool_run_manifest.json`: tool version, source commit, binary/container hash, dependencies, command, threads, iteration/hash seeds, input/list/layout hashes, logs, exit status and run times.
3. `replicate_whitelist.tsv`: experiment, dataset, replicate, seed, RNG, catalog/exclusion hashes, rank and target barcode. The same list must be used by all tools within a replicate.
4. `assignment_rows.parquet`: experiment, dataset, replicate, tool, original ID, record ID, observed source, target, orientation, CT/child flag, source evidence, emitted-FASTQ status and parser version. Ambiguity must remain visible.
5. Strict off-list read-fate and per-target tables: `input_reads = strict_assigned + ambiguous_ids + unassigned`. Historical record counts retain a separate label and contract.
6. LongBench pair ledger, per-target table and class-overlap table, preserving pair-level flags and exact proof that read groups do not re-enter. Summed per-target counts must reproduce run summaries.
7. `figure3_panel_data_manifest.tsv`: panel, experiment, metric, unit, denominator, table/key, Prism table/column, series/replicate filter, sample size and source hash. Statistics bind to this frozen manifest.
8. Figure exports, validation JSON, checksums, schemas and small edge-case fixtures. Release identity-bearing source-data tables instead of only unlabeled Prism numerics.

A clean smoke test must cover reverse orientation, CT records, read-group re-entry, same-target duplicates, multiple targets per read, missing sources, empty Flex transcripts, zero-count targets and zero denominators. Full runs must pass completeness, grouping and marginal checks before statistical analysis. Affected cached Prism statistics must be recalculated or invalidated, and plotted series must match the caption. Three false-list draws are technical randomization replicates, not biological replicates. Per-barcode observations do not by themselves justify independent ANOVA. The statistical plan must state the unit and pairing before tests are run.

Root owns repository and Zenodo integration, including correction of the existing public-record metadata. This component does not authorize job submission, publication, raw-data alteration or silent replacement of historical results. Every unrecovered historical artifact remains explicit in the availability manifest.
