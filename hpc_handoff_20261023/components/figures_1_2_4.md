# Current Figures 1, 2 and 4: HPC regeneration handoff

Prepared 23 October 2026 from metadata, saved tables and source code. No heavy sequence reads, analysis jobs or source-data edits were performed. This file uses the **current revision's** figure numbering. The cloned manuscript repository uses an older panel organization: its Figure 4 includes earlier timing and Split-seq work plus Visium HD panels 4I–K, which map to current Figure 1D. Its old Figure 2 does not supersede the corrected 22 October native-2023 Figure 2 copy.

## Operating contract

1. Prefer checkpoint reuse and independent read-back validation. Run a missing stage only after input and output paths are resolved on HPC. Local existence below is a filesystem metadata check, not a fresh integrity scan.
2. Keep originals immutable. Copy scripts and write new outputs to a new run root. Many archived scripts hardcode `/scratch`, `/scratch-nfs` and `/dartfs` paths and can overwrite completed reports. Do not run cleanup/deletion scripts. The local path prefix `/Volumes/rad_data` usually maps to historical `/dartfs/rc/lab/A/AckermanLab/CMV/rad_data`; scratch-preserved files have separate original locations recorded in manifests. Verify every mapping rather than blindly replacing roots.
3. Figure 2 historical quality RNG additionally depends on the **literal model path string**. Ordinary path relocation is not safe for that argument. The possible portable-generator fix is a deferred decision, not an instruction to change code.
4. Statistical choices and native Prism review remain explicit gates. No new P values or final Prism-render claims are supplied here. Figure 4's descriptive scope is already all 37 inputs; the final inferential configuration remains pending.
5. Retain raw source accessions and exact checksums separately from newly derived outputs. Root owns repository/release integration. Its new public API audit confirms that Zenodo record 20189813 is open and contains four legacy RData workspaces; those are not proof that the current expanded result set is deposited. Do not repeat the earlier private-draft claim or invent a final DOI.

## Execution order

- F1-01 is an artwork/code consistency check. F1-02 can rebuild accepted timing tables immediately from retained records. F1-03 needs the Seurat/grid inputs and wide-table lineage resolved before rendering.
- F2-01 freezes the generation contract; F2-02 reuses/rebuilds the full historical discovery sweeps. F2-03 preserves the completed native-2023 assignment correction, then F2-04 performs final native Prism/statistical review. F2-05 is note-only and deferred.
- F4-01 builds the final 37-input manifest/metrics. F4-02 resolves all-read input summary provenance. F4-03 prepares final paired plots/statistics after the explicit analysis choice.

## New evidence versus older audit notes

- Native-2023 BLAZE assignments were completed on 22 October. The old inventory's “not found” finding is superseded by `prism/blaze2023_assignment_replay/` and its validation.
- The copied repo's `figures/figure_4/overview_panels_bare.R` supplies the previously missing spatial normalization recipe: `nCount_Spatial`, pre-merge library-total CPM, no pseudocount, full combined color range. Exact current-panel identity and upstream RAD/Seurat provenance still require validation.
- Complete native-2023 FASTQ and both original S/L flat-Q20 fixtures exist locally. Full LongBench SN-ONT and SC-PB FASTQs are absent at the inspected preserved paths; check their explicitly recorded HPC locations before scheduling download.

## F1-01 — Reconcile workflow schematic with the pinned code and Methods without substituting current code for historical benchmarks.

Priority: **P1**. Panels: 1A. Dependencies: none.

### Inputs

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/extracted/RAD R1 figures and legends.txt`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/extracted/figure_images/paragraph_0_image1.text.txt`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/github_main_methods_audit.md`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/github_audit/main_cb699170`

### Existing checkpoints and unresolved local paths

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/github_main_methods_audit.md`: **present** (16,617 bytes)

### Ordered actions

1. Use current-paper panel numbering: current 1A is schematic; current 1B-C use September scaling, not repository legacy Figure 4A-C.
2. Keep schematic/editable artwork as a source asset; cross-check exact-catalog handling, selected-list correction and output filtering against pinned main cb699170.
3. Use root code audit for algorithm prose; do not retrofit a main-branch binary into archived RAD 4acbe00 timing results.

### Acceptance checks

- Schematic labels and Methods describe the same two-list roles and supported architectures.
- No guarantee of preventing biological ambient contamination or universal exact-barcode preservation is introduced.

### Artifacts to retain and publish

- Editable schematic; vector PDF; pinned code/figure crosswalk

### Availability notes

- No numerical regeneration needed for 1A. Artwork source remains to be identified by the figure owner if embedded PDF is the only available version.
## F1-02 — Rebuild computational-efficiency tables from accepted September runs; rerun sequence processing only for missing/failed checkpoints.

Priority: **P0**. Panels: 1B, 1C. Dependencies: none.

### Inputs

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/provenance/all_runs_long.tsv`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/provenance/input_manifest.tsv`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/provenance/software_and_resources.tsv`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/raw`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/PARALLEL_DESIGN.md`

### Scripts

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/scripts/collect_results.py`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/scripts/aggregate_metrics.py`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/scripts/config.sh`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/scripts/run_block.sh`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/scripts/stage_and_run.sh`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/scripts/submit_all.sh`

### Existing checkpoints and unresolved local paths

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/provenance/all_runs_long.tsv`: **present** (731,625 bytes)
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/results/SN-ONT/whitelist_detection_wall_seconds.csv`: **present** (347 bytes)
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/results/SC-PB/demultiplexing_wall_seconds.csv`: **present** (355 bytes)
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/data/sc_sn/raw_fastq/SN_ONT.fastq.gz`: **not_at_inspected_local_path**. Absent at preserved local path; historical HPC path is recorded in input_manifest.tsv.
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/data/sc_sn/raw_fastq/SC_PB.fastq.gz`: **not_at_inspected_local_path**. Absent at preserved local path; absence here does not prove deletion on HPC.

### Ordered actions

1. Clone run metadata/outputs into a new task work directory before running collectors; archived scripts and outputs are immutable. Review accepted flags and latest successful attempt selection before rebuilding.
2. Invoke copied collect_results.py with --run-root pointing to the clone, then aggregate_metrics.py after checking its output-path assumptions. Read collectors before execution: no recovery/cleanup/deletion scripts are required.
3. Retain 108 accepted phase records: 2 inputs x3 tools x3 worker counts x3 repetitions x2 phases. Sum matching detection+demux times; memory is the larger GNU-time process maxRSS across phases, not sum of process-tree RSS.
4. If reruns are necessary, first resolve historical /scratch-nfs/f005f43/rad_longbench_20260726/data/sc_sn/raw_fastq/{SN_ONT,SC_PB}.fastq.gz or reacquire only those files from LongBench; verify recorded size/hash before staging. Pin RAD 1.0.2 / 4acbe004, BLAZE 2.5.0 / 11994f9c, pristine Flexiplex 1.02.6 / d84c8ae4 and filter 1.1.
5. Use actual accepted AMD EPYC 7543 host stratum, requested threads 4/16/64, independent repeat IDs. Preserve serialization-to-sink and decompression contract; do not substitute persistent-output timing or different CPU family and pool it into old bars.

### Acceptance checks

- SN-ONT 119,016,231 reads; SC-PB 195,242,483 reads. RAD historical parser reports one fewer SC-PB record; preserve disclosed discrepancy.
- 16-thread total mean hours round to SN-ONT RAD 1.75 / BLAZE 7.24 / Flex 9.08 and SC-PB RAD 1.49 / BLAZE 3.04 / Flex 2.01.
- GNU maxRSS KiB x 1024 / 1e9 gives maximum accepted GB RAD 2.282, Flex 1.947, BLAZE 1.722; optional sampled BLAZE summed tree RSS reaches 6.721 and must be separate.
- Every used attempt has success/exit/resource provenance; source label is single-nucleus ONT, not single-cell ONT.

### Author decisions / gates

- Confirm final plotted summary mean and error bars (three repetitions; preserve exact plotted convention). Any new hardware stratum must be labeled separately.

### Artifacts to retain and publish

- Accepted run table with commands/host/version/resource metadata; per-phase and combined replicate CSVs; process-RSS definition; SVG/PDF/PNG plots; hashes

### Availability notes

- Raw input hashes in config.sh: SN_ONT62e75b222c7046cfa0297ca59f56a26fdb923e3307edda0bb69701713719801a; SC_PB68e818fdd9d329e56fd159ac90befba8350d30a4eaa959610fe03fd4484d07d4.
- Public inputs: GSE303762/PRJNA1171488 and s3://longbench-data. Some historical outputs were counted streams and intentionally not retained. Old repo Figure 4 timing is not this dataset/run design.
## F1-03 — Recover and render the Visium HD spatial triptych from the archived plotting recipe and validate the upstream RAD bin-count mapping.

Priority: **P1**. Panels: 1D. Dependencies: none.

### Inputs

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/hpc_handoff_20261023/rad-manuscript/figures/figure_4/sample_bin_matrix_16um.csv.gz`
- `/Volumes/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts/uncorrected_counts_by_sr16.csv`
- `/Volumes/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts/canonical_per_spot.csv.gz`
- `/Volumes/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts/per_bin_compare_PBC44593.csv.gz`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/figure1D_figure4B-E_supplement.md`

### Scripts

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/hpc_handoff_20261023/rad-manuscript/figures/figure_4/overview_panels_bare.R`
- `/Volumes/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts/aggregate_to_sr16.py`
- `/Volumes/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts/bin_overlap_rad_vs_seurat.py`
- `/Volumes/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts/exact_match_counts.py`

### Existing checkpoints and unresolved local paths

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/hpc_handoff_20261023/rad-manuscript/figures/figure_4/sample_bin_matrix_16um.csv.gz`: **present** (2,743,379 bytes)
- `/Volumes/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts/uncorrected_counts_by_sr16.csv`: **present** (6,474,762 bytes)
- `/Volumes/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts/canonical_per_spot.csv.gz`: **present** (67,091,099 bytes)

### Ordered actions

1. Locate only the referenced HPC HD_MAPPING_DIR and its tissue_positions_16um.csv plus visium_hd_mouse_brain_016um_seurat.rds; record hashes and creation provenance. These two files are not included in the cloned repo and their current HPC location is unresolved.
2. Old repo panels 4I-K correspond to current 1D. Use overview_panels_bare.R in an output copy, with HD_MAPPING_DIR and a working directory containing the copied sample_bin_matrix_16um.csv.gz. Record R/sessionInfo and six package versions.
3. Before rendering, trace the repo wide-table columns/counts to preserved RAD spot counts and map. aggregate_to_sr16.py bins each 2 µm coordinate by integer division by 8; sum 8x8 positions into 16 µm bins. Do not substitute legacy Hamming-inclusive counts.
4. Plot recipe: representative PBC44593; Seurat obj$nCount_Spatial; Seurat denominator is sum over the entire object; RAD denominator is sum of PBC44593_count in the entire wide table; log10(count*1e6/total), no pseudocount. These sums precede grid merge/display subset.
5. Shared color limits use Seurat-present and RAD-valid bins, full combined range; common bounding box from complete tissue-position grid; Space Ranger in_tissue==1 is displayed in gray. Validate finite values and positive counts in plotted subsets instead of silently adding pseudocounts.
6. Render the three plots, both colorbar options, and triptych; compare orientation, extent, count meanings, scale and silhouette with current panel before final assembly.

### Acceptance checks

- Exactly four named flowcells PBC44593 / PBC44760 / PBC49262 / PBC52788; display is PBC44593 only.
- 16 µm unit is retained (old legend incorrectly says 16 mm). Shared coordinates/limits and mask agree across three panels.
- RAD-valid mapping is documented and no unmatched observed pairs are silently imputed. exact_match_counts.py infers canonical pairs from aggregate support; verify whether this inferred mapping is actually the final source.
- No unmatched/missing bins silently become zero observations; no -Inf scale endpoints or unrecorded clipping.

### Author decisions / gates

- Identify HD_MAPPING_DIR and the creation/source metadata for the Seurat object and RAD wide table. Confirm archived plotting recipe is intended current 1D; retain current panel until visual/data match is established.

### Artifacts to retain and publish

- Per-bin plotted counts, validity and in_tissue columns; coordinate/mapping table; denominator and color-limit CSV; source hashes; script/sessionInfo; individual panels and triptych as PDF/PNG

### Availability notes

- Source release https://epi2me.nanoporetech.com/visium_hd_2025.06/ and s3://ont-open-data/visium_hd_2025.06. Its Space Ranger output derives from converted Nanopore reads; do not label it independently matched Illumina.
- The previously unresolved normalization now has an explicit archived recipe at overview_panels_bare.R:26-68. Count-table lineage and final-panel matching still require validation.
## F2-01 — Freeze original sequences, truth and historical quality-generator contracts before any regeneration.

Priority: **P0**. Panels: 2A, 2B, 2C, quality-sweep supplement. Dependencies: none.

### Inputs

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/data/shuffled_S_lr_synth.fq.gz`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/data/shuffled_L_lr_synth.fq.gz`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/code/models/nanopore2018.gz`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/code/models/nanopore2023.gz`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/metadata/L_truth_barcodes.txt`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/code/SOURCE_MANIFEST.tsv`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/provenance/generation_environment.tsv`

### Scripts

- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/code/original_quality_generation/generate_truth_conditioned_qscores.py`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/code/original_quality_generation/run_S_truth_conditioned.sh`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/code/original_three_tool_sweep/generate_l_quality_variants.sh`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/scripts/generate_truth_conditioned_qscores.py`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/scripts/run_generation.sh`

### Existing checkpoints and unresolved local paths

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/data/shuffled_S_lr_synth.fq.gz`: **present** (106,477,677 bytes)
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/data/shuffled_L_lr_synth.fq.gz`: **present** (3,074,597,647 bytes)
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/inputs/L_variants/shuffled_L_lr_synth.nanopore2023_truthbc.native_unadjusted.fq.gz`: **present** (10,032,810,794 bytes)
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/validation/full_fastq_validation.json`: **present** (1,871 bytes)
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/code/SOURCE_MANIFEST.tsv`: **present** (3,755 bytes)

### Ordered actions

1. Reuse validated input files first. Source ScTagger simulated long reads are public FASTA; local flatQ20 FASTQ is a derived conversion. S: 98,873 reads/50 truth barcodes; L: 4,993,805 reads/5,000. Preserve order, full headers, nucleotide sequences and lengths.
2. Snapshot model bytes, generator, environment and invocation. Historical 2018 S seed 20260727 and L seed 20260731; native 2023 L seed 20260731. This is truth-conditioned barcode quality sampling on fixed errors, not new BadRead error simulation.
3. Historical background-tape seed includes the literal model pathname. Preserve lexical --model string for replay; no Path.resolve or new pathname substitution even with identical model bytes. If the old path cannot be recreated, stop exact replay and report the path contract; a future decoupled RNG is task F2-05.
4. Historical 2018 --model path is /scratch/f005f43/rad_sctagger_badread_quality_20260727/models/nanopore2018.gz. Historical 2023 path is /dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_nanopore2023_Q15_Q20_20260819/models/nanopore2023.gz.
5. Do not use older marginal S-pilot scripts or Desktop methods note as the current truth-conditioned experiment; those sample without the same error-context conditioning.

### Acceptance checks

- Native 2023 compressed 10,032,810,794 bytes; SHA256 69b3da301d03d57f3932cfe2d227cc4c0a63ad45191d48eead36d00171471f67; ordered header/sequence SHA256 ca3073f0a44d03b40a5919e01e59a8df89ceceafa086ee7580fae2daa3bf2f61; ordered quality SHA256 1356a4993a6cc31ca80857f99d105da376534d594112588af4e32b3cdf138841.
- Native 2023 Q1–90, whole mean 31.6695023; 8,394,808,882 bases; barcode located 4,976,160, unlocated 17,645. Background-only quality retained when barcode unlocated.
- Generation environment Python 3.9.16, BadRead 0.4.1, edlib 1.3.9, NumPy 1.23.5; tape 16,777,216; adapter ED 7; boundary slop 8. Validate sequence/header and decompressed quality hashes, not only gzip file hash across compressors.

### Artifacts to retain and publish

- Input/model hashes and public source DOI10.6084/m9.figshare.19740475.v1; exact generator/environment/invocations; validation summaries; truth barcodes; quality-derived file manifest

### Availability notes

- Both source S/L flatQ20 and full native 2023 FASTQ are present on mounted drive; only metadata was inspected in this task. Historical Linux environments/binaries require HPC verification.
- A future corrected generator is NOT authorized by this handoff; only the issue/note is authorized.
## F2-02 — Reuse or rebuild the complete archived 2018 S/L and 2023 L quality-discovery sweeps without conflating replay with demultiplexing.

Priority: **P1**. Panels: 2B, 2C, quality-sweep supplement. Dependencies: F2-01.

### Inputs

- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/callset_metrics.tsv`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/quality_conditions.tsv`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/ALL_TOOLS_SWEEP_WITH_QUALITY.tsv`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913/results/all_tools_both_models.tsv`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913/quality/paired_50000_barcode_mean_Q.csv`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/runs/L/nanopore2023_native_unadjusted/blaze/putative_bc.csv`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/results/quality_distribution.tsv`

### Scripts

- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/code/original_three_tool_sweep/run_case.sh`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/code/original_three_tool_sweep/run_s_sweep.sh`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/code/original_three_tool_sweep/run_l_sweep.sh`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/summary_code/build_summary.py`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/summary_code/plot_sweep.py`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913/scripts/reconstruct_quality_sweep.py`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913/blaze_replay/scripts/replay_blaze.py`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913/scripts/tabulate_extended_sweep.py`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913/scripts/finalize_report.py`

### Existing checkpoints and unresolved local paths

- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/callset_metrics.tsv`: **present** (17,085 bytes)
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/summary_validation_20260912.json`: **present** (1,210 bytes)
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913/COMPLETE`: **present** (33 bytes)
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913/blaze_replay/DONE`: **present** (33 bytes)
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913/blaze_replay/native_validation.json`: **present** (679 bytes)
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913/results/all_tools_both_models.tsv`: **present** (38,186 bytes)
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913/quality/paired_50000_barcode_mean_Q.csv`: **present** (10,332,546 bytes)
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/runs/L/nanopore2023_native_unadjusted/blaze/putative_bc.csv`: **present** (330,768,009 bytes)

### Ordered actions

1. Reuse complete archived tables/whitelists and record actual-run versus reused-callset origins. For 2018: eleven shifts +1,+2,+3,+4,+5,+6,+8,+10,+11,+12,+13 and flatQ20, S/L, four configurations RAD/BLAZE/Flex f0/Flex f8 = 96 rows.
2. For 2023 L: shifts -17,-16,-15,-14,-12,-11,-9,-7,-6,-5,-4 plus native ; 48 rows. The combined 2018/2023 L table has 96 rows; do not confuse it with the distinct 96-row 2018 S/L table. 2023 S was not established in the saved extended sweep.
3. Reuse paired 50,000 located-read distributions spanning 5,000 truth barcodes. Shift individual bases then clip to 1–50 before averaging 16 barcode bases; native 2023 preserves 1–90. Match model conditions by full-dataset whole-base mean, not barcode-region mean.
4. If table replay is needed, copy scripts into a new run root and explicitly remap ordinary paths. Rebuild quality summaries, then BLAZE selector replay, then tabulation/plots. The source reconstruct_quality_sweep.py also needs historical sample_replay_evidence.jsonl.gz at /dartfs/rc/lab/A/AckermanLab/CMV/rad_data/081226_Figure_2_CMV_V14_Q20p18_sweep_20260913_provenance/quality/; its mounted counterpart was not located. Do not derive exact per-base transforms from already averaged Q values.
5. BLAZE replay imports pinned 2.6.0a0 selector; minQ gate 15-shift; expect 5000/3v3/default sensitivity; no empty-drop analysis/demultiplexing. Freeze full candidate table including low-Q candidates. RAD/Flex callsets reuse is valid only with fixed sequences and same settings.
6. If full 2018 FASTQs are missing on HPC, regenerate with historical generator after F2-01. The 2023 shifted FASTQs were never all written; no need to materialize them merely to reproduce the exact whitelist replay. New full per-condition assignment experiments or 2023 S are separate scientific expansions.

### Acceptance checks

- Native 2023 replay matches 5,015 whitelist entries byte for byte:5,000 TP, 15 FP, 0 FN. RAD5,000 / 0 / 0; Flex f8=3,004 / 0 / 1,996; Flex f0=5,000 / 7,744 / 0.
- Full-base histograms sum 8,394,808,882; located barcode-base count 16 x 4,976,160. Paired sample 50,000unique IDs/all 5,000 truth. Maximum matched-mean difference 0.373602 Q.
- Independently rescore each output list against exact truth; whitelist counts=TP+FP and 5,000 = TP + FN. Do not label shifted discovery curves as sequencing-accuracy changes or read-assignment results.

### Author decisions / gates

- Confirm presentation placement of full sweep (main versus supplement) and whether any new 2023 S/full-assignment sweep is wanted; current saved scope is 2018 S/L and 2023 L discovery.

### Artifacts to retain and publish

- All per-condition whitelists and TP/FP/FN barcode identities; long-format metrics with origin flags; paired-read Q distributions; full histograms and match table; raw inputs or reproducible generator+hash manifest; code/env/logs; PDF/SVG figures

### Availability notes

- Saved 2023 native/extended packages and checkpoint tables are present. Exact sample_replay_evidence location and 2018 working FASTQs require narrowly scoped HPC inventory.
- Do not run an archived script in place: several hardcode output roots and overwrite report files; completed replay has DONE guard.
## F2-03 — Retain the completed native-2023 assignment replay and exact RAD/Flexiplex audit categories; rebuild only from preserved checkpoints if required.

Priority: **P0**. Panels: 2D, 2E, 2F, 2G, 2H. Dependencies: F2-01.

### Inputs

- `/Volumes/rad_data/reviewer_comment_data/sctagger_L_rad_fixed5000_adapter_fix_20260817/independent_validation/record_audit.tsv.gz`
- `/Volumes/rad_data/reviewer_comment_data/sctagger_flexiplex_audit_20260812/L_flatQ20_audit_reads_barcodes.txt`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/figure2_canonical_rad_flex/canonical_results.json`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/blaze2023_assignment_replay/provenance.json`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/blaze2023_assignment_replay/prism_manifest.json`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_q20p18_prism_update_20260912/blaze_native_replay_seed0/shift_p06_Q20p1811/assignment_records.tsv.gz`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/runs/L/nanopore2023_native_unadjusted/blaze/putative_bc.csv`

### Scripts

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/tabulate_figure2_rad_flex.py`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/scripts/replay_blaze_2023.py`
- `/Volumes/rad_data/reviewer_comment_data/sctagger_flexiplex_audit_20260812/join_audit_native.py`
- `/Volumes/rad_data/reviewer_comment_data/software_pins_20260810/blaze_fast_selector/upstream_v2.6.0a0/source/read_assignment.py`

### Existing checkpoints and unresolved local paths

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/figure2_canonical_rad_flex/RAD_selected_per_barcode.csv`: **present** (229,648 bytes)
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/figure2_canonical_rad_flex/Flexiplex_selected_per_barcode.csv`: **present** (139,833 bytes)
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/figure2_canonical_rad_flex/array_validation.json`: **present** (933 bytes)
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/blaze2023_assignment_replay/DONE`: **present** (5 bytes)
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/blaze2023_assignment_replay/assignment_records.tsv.gz`: **present** (102,379,073 bytes)
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/blaze2023_assignment_replay/BLAZE_selected_per_barcode.csv`: **present** (169,728 bytes)
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/blaze2023_assignment_replay/metrics.json`: **present** (356 bytes)

### Ordered actions

1. The 22 October native-2023 BLAZE assignment replay is COMPLETE. Earlier inventory notes saying it is missing are superseded. Reuse its per-read records, per-target arrays, metrics, whitelist iteration order and hashes.
2. RAD uses repaired commit 24d5ce47 with the exact 5,000 truth barcodes supplied as both global and custom lists. This target set equals RAD discovery but is not the same contract as full-chemistry-global demultiplexing. Flexiplex uses its selected 3,004 targets and diagnostic RawCellBarcode field.
3. Retabulate only if necessary using tabulate_figure2_rad_flex.py in a copy with output remapped. RAD excludes every normalized ID with more than one output; Flex collapses same-target duplicates and excludes different-target IDs. Keep these actual contracts explicit.
4. For BLAZE replay, preserve the archived candidate order. New order retains common candidates from the old seed-zero order and appends new candidates lexically. Stock 2.6.0a0 row matcher uses edit distance 2 and demultiplexing minQ 0. Incremental reuse is permitted only outside changed-candidate edit neighborhoods; all non-quality extraction fields and order were checked.
5. The replay script hardcodes paths and has a DONE guard; any rebuild must use a new output root and pinned fast_edit_distance 1.2.2. Validate its archived baseline, changed neighborhoods and deterministic full-matcher control before accepting output.
6. For correction panels use corrected-correct versus corrected-incorrect. Preserve native-incorrect separately. For BLAZE total corrected-incorrect include extra targets; per-truth-target distribution excludes those extras.

### Acceptance checks

- Each tool exhaustive state sum is 4,993,805. RAD [native correct, corrected correct, corrected incorrect, native incorrect, excluded multiple outputs, unassigned] = [667965,1944306,191519,571,9048,2180396].
- Flexiplex same order = [463613,1398700,281696,381,364,2849051]; BLAZE = [640957,1881358,133074,764,0,2337652]. BLAZE matcher ambiguity remains unassigned, not absent biological ambiguity.
- BLAZE truth-target corrected-incorrect subtotal is 132,166; extra-target corrected-incorrect 908; extra-target native-incorrect 183; total extra-target assignments 1,091 across 15 targets.
- RAD arrays have 5,000 targets; Flex observed arrays 3,004; aligned truth arrays have 1,996 missing entries, not artificial zeros. Preserve selected targets with genuine zero counts.
- Saved BLAZE baseline old-2018 replay reproduces all seven scalar categories; 4,993,805 non-quality extraction rows match and 999 deterministic full old/new comparisons passed.

### Artifacts to retain and publish

- Per-read scoring records; six-state and correction-only totals; barcode-keyed arrays with explicit missingness and target classes; matcher order, scripts, source/environment hashes and validations

### Availability notes

- RAD/Flex arrays and BLAZE assignment replay were completed without new sequence alignment or FASTQ processing.
- Old raw scorer and current code are different provenance layers. Do not use current-main output tag assumptions to reinterpret historical runs.
## F2-04 — Finish native Prism review, approved statistics and publication exports of the already corrected Figure 2 copy.

Priority: **P1**. Panels: 2B, 2C, 2D, 2E, 2F, 2G, 2H. Dependencies: F2-03.

### Inputs

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/Figure2_corrected_20261022.prism`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/Figure2_corrected_20261022_README.md`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/Figure2_corrected_20261022_change_log.json`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/independent_audit.json`

### Scripts

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/scripts/build_figure2_corrected_prism.py`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/scripts/validate_figure2_corrected_prism.py`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/independent_audit_figure2.py`

### Existing checkpoints and unresolved local paths

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/Figure2_corrected_20261022.prism`: **present** (4,502,468 bytes)
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/Figure2_corrected_20261022_validation.json`: **present** (56,585 bytes)
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/independent_audit.json`: **present** (101,432 bytes)

### Ordered actions

1. Use the corrected copy with SHA256 dded389f9d8214278f93d2669c64e704bbf2208c47db96bf57a4ce4c77d6d016. Do not use superseded_five_outcome_draft or the original V18 numeric data.
2. Open a fresh review copy in licensed Prism, verify all graphs and native-save before final export. HPC can prepare tables but must not claim native UI verification without actually performing it.
3. The two-outcome correction doughnuts intentionally exclude source rows 0 and 3–5 of their six-state tables. Do not remove these exclusions. Correction denominators are RAD 2,135,825; Flex 1,680,396; BLAZE 2,014,432.
4. Retain the native Flex full-truth reference increment of 222,371 reads and label it as a reference increment, not as observed native count under the selected 3,004-target condition.
5. Inspect manual false-positive labels, bar labels, center labels and significance brackets/stars. Six numeric statistical caches were invalidated; no replacement P values have been calculated. Apply the author-approved analysis only, and update legend/test parameters together.

### Acceptance checks

- Saved archive validation: 388 builder checks and 499 independent checks pass on the closed hash; repeat read-back after any save.
- Displayed correction ratios: RAD 91.03%/8.97%; Flex 83.24%/16.76%; BLAZE 93.4%/6.6%.
- Native and corrected Flex per-target graphs bind to the selected-list arrays, not older fixed-5,000 arrays.
- Final PDF/PNG is visually checked for stale numbers, stars, category denominators and readable panel labels.

### Author decisions / gates

- Select statistical design, analysis population and multiple-comparison method; original one-way ANOVA annotation is not current evidence. Native Prism review/export is still pending.

### Artifacts to retain and publish

- Native saved reviewed Prism; all source CSVs; approved statistical results and analysis configuration; PDF/PNG/vector export; read-back and visual QA records

### Availability notes

- Corrected data copy is present and structurally audited. Native rendering/annotation review has not yet occurred. Original V18 SHA256 d8cc036cdca79d607be863fd15a9bc4721c4e86d09721ea4b368401fa9b3a10c remains preserved.
## F2-05 — Record the path-dependent random-number issue and define the boundary for a possible future portable generator.

Priority: **DEFERRED**. Panels: quality-sweep supplement. Dependencies: none.

### Inputs

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/scripts/generate_truth_conditioned_qscores.py`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/scripts/run_generation.sh`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/ScTagger_quality_sweep_20260731/code/original_quality_generation/generate_truth_conditioned_qscores.py`

### Existing checkpoints and unresolved local paths

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913/scripts/generate_truth_conditioned_qscores.py`: **present** (23,565 bytes)

### Ordered actions

1. NOTE ONLY: user has authorized documenting the issue, not changing the generator or rerunning an alternative experiment.
2. Historical generator line 379 seeds the background tape with stable_seed(str(args.model), args.seed, "quality-tape"). Identical model bytes at a new path can change generated scores. Preserve existing records and archived paths for historical replay.
3. If a future change is expressly approved, create a separately versioned generator using a documented stable model identity or content hash in the RNG key. Specify migration behavior, tests and output naming before running it. Never call its new outputs byte-identical historical results.
4. A future implementation should separate filesystem location from RNG identity, preserve per-read paired draws across shifts, and test path-invariance with identical bytes at two paths. Numerical comparison to historical results and separate publication labels would then be required.

### Acceptance checks

- No source generator or quality data is changed by this handoff.
- Any future portability test must use a tiny declared fixture before full-scale regeneration; historical exact-replay hash checks remain separate.

### Author decisions / gates

- Deferred: explicit author approval is needed to choose and implement a new RNG identity convention and decide whether newly generated results replace or supplement historical results.

### Artifacts to retain and publish

- Current RNG-path note and preserved generator/source hashes; future outputs only after the separate decision

### Availability notes

- This is a known reproducibility constraint, not evidence that archived results are numerically invalid. Model path and model bytes are both part of the existing historical contract.
## F4-01 — Rebuild the complete 37-input barcode-detection comparison with the corrected immune reference and explicit reconstruction status.

Priority: **P0**. Panels: 4A, 4B, 4F, 4G, 4H. Dependencies: none.

### Inputs

- `/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/complete_three_tool_metrics.tsv`
- `/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/sample_inventory.tsv`
- `/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/SOURCE_MANIFEST.tsv`
- `/Volumes/rad_data/reviewer_comment_data/master_native_comparison_20260811/tables/master_native_comparison_long.csv`
- `/Volumes/rad_data/reviewer_comment_data/master_native_comparison_20260811/provenance/source_manifest.tsv`
- `/Volumes/rad_data/reviewer_comment_data/master_native_comparison_20260811/provenance/dataset_manifest.tsv`
- `/Volumes/rad_data/reviewer_comment_data/wl_scan/20260730_rageseq_ERR3268990_tnbc_lymphnode_four_tool/analysis/barcode_level_annotations.tsv`

### Scripts

- `/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/scripts/build_complete_whitelist_project_rageseq_immune.py`
- `/Volumes/rad_data/reviewer_comment_data/master_native_comparison_20260811/scripts/build_master.py`
- `/Volumes/rad_data/reviewer_comment_data/master_native_comparison_20260811/scripts/independent_validate.py`

### Existing checkpoints and unresolved local paths

- `/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/complete_three_tool_metrics.tsv`: **present** (73,490 bytes)
- `/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/sample_inventory.tsv`: **present** (13,270 bytes)
- `/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/VALIDATION_SUMMARY.json`: **present** (1,614 bytes)
- `/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/PZFX_VALIDATION.tsv`: **present** (3,481 bytes)
- `/Volumes/rad_data/reviewer_comment_data/master_native_comparison_20260811/validation/independent_validation_summary.json`: **present** (569 bytes)

### Ordered actions

1. Use the September immune-corrected package as current authority. The August master is a source checkpoint, not the final reference: its RAGE lymph-node denominator is superseded.
2. Preserve 37 scored inputs and 111 tool rows: 35 unchanged native inputs, one immune-rescored native input, one labeled ScMixology2 reconstruction. Keep Visium HD inventory-only; exclude NBC and extra ScTagger quality variants from this table.
3. Reconstruct in a new output root after resolving source manifests. The builder hardcodes historical /dartfs and /scratch paths; remap ordinary filesystem roots in a copied script and retain an explicit path map. Do not run cleanup/deletion scripts from master package.
4. Rescore RAGE lymph-node against 5,978 named T/B-containing barcodes: 4,255 T + 1,637 B + 86 doublets. Do not restore all 10,433 deposited barcodes as positive truth.
5. Keep ScMixology2 explicitly reconstructed: RAD native scan, BLAZE expected-500 selector replay on published cache, Flex 1.02.6 filter replay on common RAD counts. Its 248-barcode reference is a positive proxy.
6. Join tables by canonical input identity and tool, not row position or biological donor name. Retain technical runs separately as inputs; reference classes distinguish exact truth, matched short-read proxies and on-tissue operational sets.

### Acceptance checks

- 37 unique scored inputs x 3 tools = 111 unique rows; no duplicate/missing tool row. Each row satisfies calls=TP+FP and reference_n=TP+FN; recomputed precision/recall/F1 matches table.
- Input inventory has 38 entries including Visium HD inventory-only. Current category counts: 2 synthetic, 11 single-cell, 12 single-nucleus, 9 Visium and 3 targeted inputs.
- RAGE reference_n=5,978; ScMixology2=248; LongBench SC=5,211 and SN=12,012; ScTagger S=50/L=5,000.
- Original native master reported 687 independent checks; final package cell-level PZFX validation and immune rescore must also pass. Legacy native-only statistics are not evidence for all 37.

### Artifacts to retain and publish

- 37-input dataset/callset/reference manifest with public accession links, version/settings, TP/FP/FN and metrics; exact whitelist sets where redistributable; PZFX/CSV; validation and hashes

### Availability notes

- Master provenance points to named upstream packages: whitelist_native_three_tool_graph_ready_20260810, tilgner_all10_native_three_tool_whitelist_20260810, visium_three_tool_splitaware_scatter_20260802 and mpnst_native_three_tool_whitelist_20260811. Resolve only referenced paths, no blanket rerun.
- Operational false positives against retained-cell/on-tissue references are not proven biological negatives. All 37 inputs are already the author-selected scope.
## F4-02 — Preserve current all-input SeqKit summaries and recover the execution provenance; regenerate only if the missing provenance cannot be recovered.

Priority: **P1**. Panels: 4B, 4C, 4D, 4E. Dependencies: F4-01.

### Inputs

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/092126_Figure_4_CMV_V1.prism`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/Figure4_SeqKit_stats_saved.csv`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/Figure4_SeqKit_saved_provenance.json`
- `/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/sample_inventory.tsv`

### Existing checkpoints and unresolved local paths

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/Figure4_SeqKit_stats_saved.csv`: **present** (4,136 bytes)
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/Figure4_SeqKit_saved_provenance.json`: **present** (2,491 bytes)
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/092126_Figure_4_CMV_V1.prism`: **present** (243,402 bytes)

### Ordered actions

1. Reuse the exact saved 37-row SeqKit stats (all reads) table and its native Prism source hash. Link all rows to canonical inventory IDs. These summaries describe long-read inputs; correct the inherited short-read wording in the figure legend.
2. Recover the original SeqKit invocation/version from explicitly referenced project logs/manifests if available. No such exact all-37 record has yet been verified; do not invent the version or assert AvgQual is arithmetic mean Phred.
3. If the record cannot be recovered, plan a new all-input summary pass on HPC with a pinned SeqKit version and explicit all-read input manifest. Record bytes, input hash, number of records and emitted fields. Label new summaries as regenerated and compare every row against the saved table before adopting them.
4. Keep uniform-Q20 ScTagger S/L in Figure 4 despite native-2023 Figure 2. Do not silently replace these two rows with quality-sweep conditions. Reference barcode counts are drawn from exact/matched/on-tissue reference sets, not from SeqKit.

### Acceptance checks

- Saved table has 37 rows and num_seqs, AvgQual and GC(%) fields. ScTagger L=4,993,805/Q20.00/GC49.14; LongBench SC-ONT=117,002,380/Q16.02/GC45.61; SN-ONT=119,016,231/Q16.22/GC44.79; SC-PB=195,242,483/Q25.90/GC45.14.
- No characteristics are computed from a 10-million-read subsample or read-length plot sample unless independently identified and labeled as a different analysis.
- Rebuilt row counts and file-level input identity agree with the 37-input manifest; retain an explicit mismatch report instead of overwriting values silently.

### Author decisions / gates

- Original SeqKit command/version is unresolved. If provenance recovery fails, agree on adopting a newly pinned summary pass and report its implementation rather than pretending to reproduce undocumented settings.

### Artifacts to retain and publish

- Saved and, if generated, revised SeqKit table; input file/hash manifest; exact command/version; field definitions; source-table hash and comparison report

### Availability notes

- Native Prism source sheet UID 25C36598-E266-51BB-B350-2807CF182B3F; table UID 3503036B-4EA6-5554-B401-9CEECB8B40A7. A copied project and extracted CSV already exist; no large reads were opened for this handoff.
## F4-03 — Build the selected all-37-input plots and resolve final inferential tests without reusing native-only statistics.

Priority: **P1**. Panels: 4F, 4G, 4H, 4I, 4J, 4K. Dependencies: F4-01, F4-02.

### Inputs

- `/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/complete_three_tool_metrics.tsv`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/092126_Figure_4_CMV_V1.prism`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/extracted/RAD R1 figures and legends.txt`

### Existing checkpoints and unresolved local paths

- `/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/complete_three_tool_metrics.tsv`: **present** (73,490 bytes)
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/092126_Figure_4_CMV_V1.prism`: **present** (243,402 bytes)

### Ordered actions

1. Import all 37 input-wise matched tool triples for F1, precision and recall; keep ScMixology2 provenance visible in source data. Plot individual inputs and distribution summaries from the same row set.
2. The current legend requests Friedman testing, but the exact final analysis configuration/post hoc correction is unverified. Prepare complete paired data and propose the test configuration for approval; do not reuse old 36-native-input or one-way ANOVA outputs.
3. Preserve the stated median/min-to-max box-plot description only if the actual final Prism configuration matches. Export native analysis tables, test parameters, exclusions/missingness and comparison families with the revised figure.
4. Review the role of repeated technical inputs: 37 input entries do not imply 37 independent biological samples. If sensitivity analyses by biological grouping are requested, create separate labeled results without replacing the approved all-input descriptive comparison.

### Acceptance checks

- Every metric table contains the same 37 input identities in the same matched order, all three tools, no silently omitted reconstruction.
- Reported N, test design, pairwise adjustment, P values and annotations derive from the final approved row set.
- Final figure uses barcode-discovery performance terminology rather than implying these F1 metrics are read-assignment accuracy.

### Author decisions / gates

- Resolve Friedman/post hoc versus the proposed paired Wilcoxon approach, including multiplicity and correlated technical inputs; all 37 inputs remain the settled descriptive scope.

### Artifacts to retain and publish

- All-input paired metric tables; approved statistical configuration/results; native Prism/project source; final PDF/PNG/SVG and visual QA

### Availability notes

- No statistical tests or final graphics were executed in this handoff. Repository legacy Figure 4A-H is a different panel set and cannot serve as the current 37-input analysis script.
