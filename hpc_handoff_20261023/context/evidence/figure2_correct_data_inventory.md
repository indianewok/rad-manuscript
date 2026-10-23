# Figure 2 corrected-data inventory

Audit date: 2026-10-22. Inventory only; no demultiplexer, sequence analysis, or assignment replay was run. New files remain under `reviewer_comment_data`. Paths below are local mounted-drive paths unless explicitly described as historical.

## Finding

The saved data are sufficient to correct the quality-distribution and whitelist-discovery panels for the nanopore2023 model now. Full nanopore2023 read-assignment results were **not found**. The native2023 and extended-sweep packages explicitly stop after whitelist discovery, and their saved outputs agree with that scope. The extended package's “BLAZE replay” recomputes whitelist selection, not read assignments.

A complete native2023 BLAZE extraction cache and selected list are preserved. Consequently a new BLAZE read-assignment replay can be performed without reading or realigning a FASTQ. Existing RAD and Flexiplex read-assignment outputs can be reused for fixed nucleotide sequences and unchanged settings, with their original whitelist contracts made explicit. Some per-barcode arrays and native-versus-corrected incorrect splits need a fresh tabulation of preserved audit tables, not a new sequence-processing run.

## 1. Canonical nanopore2023 quality and whitelist evidence

Root:

`/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913`

Key files:

- `README.md`, `RESULTS.md`: completed full-data benchmark scope and definitions.
- `results/native_whitelist_metrics.tsv`: native unadjusted discovery results.
- `runs/L/nanopore2023_native_unadjusted/{rad,blaze,flex_f0,flex_f8}/`: retained callsets and execution evidence.
- `validation/root_final_callset_audit.json`, `validation/final_audit.json`: independent rescore and validation.
- `provenance/software.tsv`, `provenance/run_resources.tsv`: historical versions, binaries, commands, resources.

Native unadjusted results against 5,000 true barcodes:

| Tool/setting | Selected | TP | FP | FN |
|---|---:|---:|---:|---:|
| RAD | 5,000 | 5,000 | 0 | 0 |
| BLAZE | 5,015 | 5,000 | 15 | 0 |
| Flexiplex f8 | 3,004 | 3,004 | 0 | 1,996 |
| Flexiplex f0 | 12,744 | 5,000 | 7,744 | 0 |

Native2023 is unshifted and uncapped: Q1–Q90; whole-file mean Q31.6695023; barcode-base mean Q22.2270824. Headers and nucleotide sequences are unchanged from the 4,993,805-read ScTagger-L fixture. It must not be called a new nanopore2023 nucleotide-error simulation.

Extended quality sweep root:

`/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913`

Ready-to-use files:

- `results/all_tools_2023_sweep.tsv`
- `results/BLAZE_2023_sweep.tsv`
- `results/BLAZE_2018_vs2023.tsv`
- `quality/paired_50000_barcode_mean_Q.csv`
- `quality/quality_summary.tsv`
- `quality/matched_quality_levels.tsv`
- `blaze_replay/conditions/<condition>/whitelist.csv`

There are eleven shifted2023 controls plus native2023. Shifted controls clip individual-base qualities to Q1–Q50; native retains Q1–Q90. Quality levels were matched to the prior2018 sweep using full-dataset mean base Q, not barcode-region means. RAD/Flexiplex callsets are explicitly reused because quality-independent for the fixed sequences/settings. BLAZE's native extraction cache includes low-quality candidates, and the exact native selector is rerun after applying the shifted minimum-quality test.

The often-referenced2023 “near Q20” control is **shift−11**, whole-file mean Q20.4134566 and barcode mean Q12.502898. Its BLAZE selected list contains 4,649 barcodes:4,635TP,14FP,365FN. This is a different condition from native2023 (5,015 selected), and neither equals the earlier2018+6 condition (5,087 selected).

## 2. Saved Prism2023 update is quality-only

Root:

`/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_prism_nanopore2023_20260913`

- `README.md`
- `input_provenance.json`
- `table_spec.json`
- `csv/column_label_mapping.json`
- `csv/` input tables
- `added_tables.prism`

This package added the2023 50K barcode-quality and summary tables and changed quality labels. It explicitly preserved existing benchmark numeric data. Its existence does not establish that assignment or discovery charts in the output Prism were converted to2023. The label convention is rounded **barcode-region mean across the50K sample**, with duplicateQ10 labels disambiguated by their two-decimal means. Native2023 is labeled Q22(unadjusted), not Q32, because this label uses barcode-region quality rather than whole-file mean quality.

The recorded output project was `081226_Figure_2_CMV_V14_np2023_Qlabels_20260913.prism`. Its historical path is a provenance reference; this audit did not edit or open that Prism project.

## 3. Complete BLAZE inputs for a new2023 read-assignment replay

Native2023 extraction cache (exists,330,768,009bytes):

`/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/runs/L/nanopore2023_native_unadjusted/blaze/putative_bc.csv`

Native2023 selected list (5,015barcodes):

`/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/runs/L/nanopore2023_native_unadjusted/blaze/whitelist.csv`

CSV fields are `read_id,putative_bc,putative_bc_min_q,putative_umi,polyT_end,pre_bc_flanking,post_umi_flanking`. This contains every field used by the native row matcher. The run metadata/validation describes one row for each of4,993,805input reads. This audit inspected the header and prefix only; it did not rescan all5million rows.

Prior assignment-replay implementation:

`/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_q20p18_prism_update_20260912/scripts/replay_blaze_assignments.py`

Prior launch settings:

`/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_q20p18_prism_update_20260912/scripts/replay_blaze.sbatch`

The script imports the unmodified BLAZE `_match_bc_row`, uses maximum barcode edit distance2 and demultiplexing minimumQ0, checks all non-quality extraction fields against a flatQ20 cache, and writes per-read and per-barcode four-way truth scores. It needs adaptation: it currently hardcodes lists of5,607 and5,087barcodes, two labels, and the2018+6 paired control. Changing those assertions/labels and supplying the2023 selected list is required; it cannot be run unchanged as a2023 analysis.

Pinned BLAZE2.6.0a0 source (upstream commit `af8d2cc9f6374caf4d1006d5f8a0e99097211646`):

`/Volumes/rad_data/reviewer_comment_data/software_pins_20260810/blaze_fast_selector/upstream_v2.6.0a0/source/read_assignment.py`

The complete package snapshot is the sibling `source/` directory, with `pyproject.toml` one level above. The2023 package's historical Linux virtual environment is not present in its local `tools/` folder. A local environment can expose the pinned source; the package declares `fast-edit-distance==1.2.2`, matplotlib, tqdm, numpy, and pandas. The matcher imports fast_edit_distance, pandas, numpy, tqdm, and BLAZE helper/config. Native2023's selector environment freeze records Python3.9, fast_edit_distance1.2.2, NumPy2.0.2, pandas2.3.3, matplotlib3.9.4, and tqdm4.70.0. A saved Linux extension cannot simply be executed on macOS; the local equivalent must be installed/validated if absent.

The prior read-assignment replay used Python3.9 and `PYTHONHASHSEED=0`; it saved whitelist iteration order because ties are order-sensitive. The32-worker paired replay processed4.9million rows in594.3seconds, then completed. This is historical cluster timing, not a local runtime guarantee.

Exact saved deterministic control outputs:

`/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_q20p18_prism_update_20260912/blaze_native_replay_seed0/flatQ20_control/{assignment_records.tsv.gz,matcher_whitelist_iteration_order.txt,metrics.json,per_barcode.tsv}`

The flat-control result has2,612,247assigned reads,640,957native-correct,1,810,128corrected-correct,7,526native-incorrect,153,636corrected-incorrect. This differs slightly from the historical nondeterministic native CLI result (2,612,031assigned). Use the saved seed-zero control to verify a local replay; do not claim exact agreement with the old CLI's tie outcomes without testing it.

Corresponding inputs are preserved under:

`/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_q20p18_prism_update_20260912/replay_inputs/flatQ20/putative_bc.csv.gz`

and sibling `whitelist.csv`, plus `../L_truth_barcodes.txt`. The earlier `shift_p06_Q20p1811` assignment result is2018+6 and must not be relabeled2023.

## 4. RAD assignment evidence and arrays

Canonical repaired-calibration run:

`/Volumes/rad_data/reviewer_comment_data/sctagger_L_rad_fixed5000_adapter_fix_20260817`

- `README.md`, `RESULTS.tsv`, `provenance.tsv`, `command.sh.txt`
- `independent_validation/record_audit.tsv.gz` (46,703,941bytes)
- `independent_validation/strict_assignment_counts.tsv`
- `independent_validation/METHODS.md`

This run uses commit24d5ce47 and supplies the exact5,000truth barcodes as **both global and custom lists**. It does not execute whitelist discovery. Since the native2023 RAD discovered set is also exactly5,000truth barcodes, the target identities coincide, but that alone does not prove equivalence of a full-chemistry-global-list demultiplexing contract. Report the actual fixed-list configuration if these outputs are used.

Strict counts:667,965native-correct;1,944,306corrected-correct;192,090pooled incorrect;9,048ambiguous original IDs;2,180,396unassigned. Strict scoring drops every ID with more than one emitted record. The audit contains normalized original ID, truth barcode, final `rad_cb`, raw/correction tag `rad_cr`, strand, and pooled category. It is sufficient to tabulate all5,000target-barcode arrays and split incorrect records by the presence/absence of the correction tag after the same strict grouping. The existing scalar table does not supply that split; a fresh audit-table tabulation is needed. Reverse-strand `CR` values are not necessarily in the final-barcode orientation, so do not naïvely compare `CR==CB`; retain the documented correction-tag convention or normalize orientation explicitly.

The older folder `sctagger_L_fixed5000_three_tool_20260812/rad` is superseded for RAD by this adapter-calibration repair.

## 5. Flexiplex own-selected3004 evidence and arrays

Canonical own-selected-list assignment audit:

`/Volumes/rad_data/reviewer_comment_data/sctagger_flexiplex_audit_20260812`

Ready arrays:

- `L_per_barcode.tsv`: barcode,native,corrected,incorrect_in. Native/corrected columns are **correct assignments only**.
- `L_read_summary.tsv`:463,613native-correct;1,398,700corrected-correct;282,077pooled incorrect;364ambiguous IDs.
- `L_flatQ20_audit_reads_barcodes.txt`: raw/final record-level evidence; fields `Read,CellBarcode,RawCellBarcode,FlankEditDist,BarcodeEditDist,UMI`.
- `join_audit_native.py`: exact existing grouping/scoring.
- `VALIDATION_STATUS_20260812.md`, `run_audit_20260812.sh`: provenance and run completion.

The selected list is:

`/Volumes/rad_data/reviewer_comment_data/wl_scan/20260731_sctagger_badread_quality_full/runs/flexiplex/L/flatQ20/output/L_flatQ20_barcodes_final.txt`

It contains the3,004selected barcode identities. The2023 native callset audit establishes invariance of Flexiplex callsets across these quality-only controls. The audit build adds `RawCellBarcode` without changing assignment behavior.

The existing scorer removes IDs assigned to different final barcodes, collapses duplicate assignments to the same final barcode, and keeps the first raw barcode for that target. Its `total` includes the ambiguous count; assigned unambiguous total is the sum of the three assignment categories, not that displayed total. The existing per-barcode file pools all incorrect assignments. To obtain native-incorrect and corrected-incorrect arrays, retabulate the preserved sidecar with the same ID treatment and split by `RawCellBarcode == CellBarcode`. No Flexiplex rerun is needed. Retain the3,004target population across all own-selected-list panels; the older fixed5,000arrays answer a different question.

## 6. Alternative common perfect-whitelist design

A complete fixed5,000 comparison is also saved:

`/Volumes/rad_data/reviewer_comment_data/sctagger_L_fixed5000_three_tool_20260812`

- `common/L_truth_5000_barcodes.txt`
- `blaze/putative_bc.csv`, `blaze/assignment_record_metrics.tsv`, `blaze/matched_reads.fastq.gz`
- `flexiplex/flexiplex_L_flatQ20_fixed5000_audit_reads_barcodes.txt`, `flexiplex/assignment_classification.tsv`, `flexiplex/commands_and_provenance.tsv`
- RAD: substitute the repaired-calibration run in section4, not this folder's old RAD arm.

With quality-independent RAD/Flexiplex and BLAZE demultiplexing minQ0, these fixed-sequence assignment inputs are useful controls. This design is explicitly supplied-ground-truth assignment, separate from own-discovered-whitelist performance. It must not be combined with a headline3,004Flexiplex target set while presenting its read depths as if they used those3,004targets.

## 7. What can be corrected without new sequence processing

| Figure content | Saved evidence status | Work still needed |
|---|---|---|
|2023 barcode-quality distributions | Complete50K paired arrays and summaries | Select intended condition/label and update Prism copy |
|2023 whitelist TP/FP/FN and metrics | Complete native and11shift controls | Select consistent condition; keep Flex f0/f8 separate |
|RAD assignment totals and arrays | Repaired5,000target audit retained | Tabulate four-way categories/per-target arrays; disclose fixed global/custom configuration |
|Flexiplex own-selected3,004 assignment | Complete sidecar and pooled per-target arrays | Split incorrect into native/corrected consistently; use same3,004targets throughout |
|BLAZE2023 own-selected assignment | Complete extraction cache and callsets; no completed assignment result found | New native-matcher assignment replay, with deterministic control and provenance |
|Common supplied5,000target comparison | All three tools' saved evidence retained | Re-tabulate consistently; keep separate from own-discovered-list analysis |

## Inventory scope and limits

Inspected named2023 packages, the2023 Prism update, both saved2018 assignment replays, old2023 adjusted-control metadata, fixed5,000result packages, Flexiplex raw-barcode audits, and relevant preservation file manifests. The final/initial compact manifests list2023 selector replay files but no2023 read-assignment output package. The broad historical SQLite inventory query was stopped when slow; no claim is made that every byte on the drive was searched. No new FASTQ generation, sequence alignment, demultiplexing, or full5million-row scoring was performed in this audit.

## Completed addendum: canonical RAD/Flexiplex table tabulation

After the inventory, the parent agent authorized re-tabulation of the preserved RAD/Flexiplex audit tables for the corrected Prism copy. This completed without processing FASTQ sequences or rerunning either tool. The reproducible script is `paper_revision_20261022/evidence/tabulate_figure2_rad_flex.py`; outputs are in `paper_revision_20261022/evidence/figure2_canonical_rad_flex/`.

- `RAD_selected_per_barcode.csv`:5,000selected targets, including zeros.
- `Flexiplex_selected_per_barcode.csv`:3,004selected targets, including zeros.
- `*_truth5000_aligned_per_barcode.csv`:aligned5,000truth targets; the1,996unselected Flexiplex targets are blank rather than zero.
- `five_state_pie_counts.csv`:exhaustive original-input-ID partition.
- `canonical_results.json`, `array_validation.json`, `SHA256SUMS.txt`:counts, actual source contracts, validation, checksums.

| State | RAD | Flexiplex |
|---|---:|---:|
|Native correct |667,965|463,613|
|Corrected correct |1,944,306|1,398,700|
|ALL incorrect |192,090|282,077|
|Ambiguous |9,048|364|
|Unassigned |2,180,396|2,849,051|
|Total |4,993,805|4,993,805|

All original scalar categories matched exactly. Every native/corrected/pooled-incorrect value in the pre-existing Flexiplex per-barcode file also matched exactly. Per-barcode `all_incorrect` includes every strict incorrect assignment and requires no subtraction. Its selected-target mean is38.418 for RAD and93.9004660 for Flexiplex. The optional finer split is571native-incorrect+191,519corrected-incorrect for RAD and381+281,696 for Flexiplex. No statistical tests were performed. BLAZE2023 assignment replay remains separate work by the parent agent.
