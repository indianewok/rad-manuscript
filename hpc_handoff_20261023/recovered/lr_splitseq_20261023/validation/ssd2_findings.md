> Inventory note: file-count and size estimates below describe the initial SSD candidate list. The completed package also contains the validated RAD published-cell subset and additional source evidence. Consult source_manifest.json and SHA256SUMS for the packaged files.

# LR-Split-seq recovery from CMV_SSD_2

Recovered on 23 October 2026. Originals were inspected read-only.

## Exact figure source recovered

`/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/plotting_exports/20260801_reads_per_published_cell/splitseq_published_barcode_read_counts.csv` contains the original 568-row export with published cell identity, physical-well-normalized barcode, biological sample class, and five comparison arms. The separate Prism recovery agent confirmed that all 3,408 numerical cells of the retained six-column Prism table match this CSV in the same row order. The sixth Prism column repeats RAD for the identity line. No sorting or count-based inference was used to assign row identities.

`build_export.mjs` retains the source joins and explicit total assertions. The selected pair is `rad_ed2_assigned_reads` and `flex_component_polyt_assigned_reads`, summing to 2,078,171 and 1,156,252 read–cell pairs. The other columns are a no-poly-T ablation, MATCHED_SPLIT, and historical two-pass controls; they must not be relabeled as the selected comparator.

The underlying published-cell identity table is `/Volumes/CMV_SSD_2/results/misc/splitseq_shortread_umis_20260728/published_568_barcode_map.csv`.

## Selected RAD run

Directory: `/Volumes/CMV_SSD_2/results/rad/demultiplexed/splitseq/20260801_reverse_complement_whitelist_clean_main_ed2`.

The retained run manifest pins RAD 1.0.2 commit `b6853a3d3d1818130ac364f7937bd0690ae9e385`, a clean Release binary SHA256, source FASTQ SHA256, and layout SHA256. It specifies four threads, strict joint-barcode mode, defensive correction, chunk size 5,000, minimum read length zero, and generated/whitelist mutation settings of two. The accompanying RESULTS.md notes that text whitelists disable mismatch pregeneration, so the effective correction change is the generated-mutation radius.

`analysis/ed1_ed2_per_published_cell.tsv` contains current and earlier control rows. Select `tool == "ED2 current main"` for the final 568-cell read and UMI counts. `analysis/assignments_normalized.tsv.gz` is the retained read-level checkpoint. `analysis/ed1_ed2_metrics.tsv` reports 2,498,488 assigned source reads, 2,063,573 distinct source reads across published cells, and 1,891,704 published cell–UMIs. These counting units differ from the sum of per-cell read counts.

The native FASTQ is 1,063,230,648 bytes and the normalized ledger is 56,523,149 bytes. These are included in the preservation manifest, but excluded from its conservative GitHub candidate set.

## Selected FLAMESv2/Flexiplex component run

Directory: `/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_polyt_paired_t4`.

The manifest pins FLAMES `bf2211a8da1e1c7327370ab12479ae70e1d37cd8`; the output log identifies Flexiplex 1.02.6. Each component whitelist contains 96 entries. The run uses per-component edit distance one, maximum flank edit distance three, four threads, and an explicit terminal eight-thymidine segment. The recorded command calls `/Users/cmv/Desktop/rad/benchmarks/lr_splitseq_no_polyt/run_component_no_polyt.R` with the final argument `include`.

The native statistics file, normalized assignment ledger, count files, logs, manifest and timings survive. The ledger contains 1,345,255 assignment records covering 1,338,285 unique source-read IDs. A complete independent replay verified that every native statistics row maps to the normalized row by retaining the read ID, reversing component order to BC3_BC2_BC1, reverse-complementing the UMI, and retaining the flank edit distance. The portable `verify_component_normalization.py` and `ssd2_component_normalization_validation.json` document this check, including hashes of both compressed inputs.

`component_no_polyt_t4/analysis_concordance.sql` contains the shared downstream normalization and counting code for both component arms. It maps paired R/T primer sequences to the T-primer sequence of the same physical well, counts distinct read IDs and distinct UMI sequences within each published cell, and fills missing cells with zero. Select `tool == "Flexiplex polyT"` in `per_published_cell_counts.tsv`. The SQL references the actual primer-well map at `/Users/cmv/Desktop/tools/LR-splitpipe-master/barcodes/bc_data_v2.csv`, which must accompany the bare sequence whitelists for reproduction.

The selected native FASTQ is 522,815,268 bytes. Native statistics and normalized assignments are 19,436,939 and 17,448,867 bytes and fit the GitHub candidate set.

## Remaining distinctions

- The primary read-table identity gap is resolved, including all 568 rows. The separate Prism recovery also located the executed paired t-test and its exact saved P value.
- The selected RAD source-read fraction is based on 2,498,488 of 5,764,421 input reads. Flexiplex has 1,338,285 distinct source reads and 1,345,255 raw assignment records. These must remain distinct when reconciling rounded assignment percentages in artwork or text.
- Current RAD and component-poly-T per-cell UMI counts are recovered, but the master Prism file lacks a UMI table that confirms their Figure 5H binding. `/Volumes/CMV_SSD_2/results/misc/splitseq_rad_flex_shortread_umi_20260728` contains useful UMI intersection tables, but their RAD counts are from an earlier ED1 run (1,605,269 total cell–UMIs), not the final ED2 run. Do not call these the current Figure 5H source without a figure-specific match.

## Transfer list

`ssd2_selected_file_manifest.json` lists 55 recovered files, original paths, roles, byte counts and GitHub candidate flags. The candidate set is approximately 38 MB; all listed native and supporting outputs total approximately 1.68 GB. The separately discovered `normalize_joint_assignments.py` (1,790 bytes) is also worth preserving; despite its historical MATCHED_SPLIT docstring, its transformation matches every selected component-poly-T record as independently verified.
