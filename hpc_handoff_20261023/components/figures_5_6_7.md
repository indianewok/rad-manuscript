# Figures 5–7: HPC regeneration handoff

Prepared 23 October 2026 from retained execution evidence, small result/provenance tables, current file-availability checks and the revision decisions. Large sequencing, BAM and RDS content was not read or rerun for this handoff. This report uses current-paper numbering.

## Recovery assessment

- **Figure 5:** the RAGE receptor scripts and candidate outputs survive, but the exact current artwork-to-run mapping and cell-label provenance require resolution. The LR-Split-seq short-read reconstruction and a 568-row Prism read-count table survive; final component-based comparator settings and the UMI-panel source remain unresolved. Do not substitute historical two-pass code.
- **Figure 6:** retained post-demultiplexing BAMs (approximately 28/49/36 GB for RAD/Flexiplex/BLAZE), CellSNP matrices, a validated bulk donor panel and graph-ready outputs permit checkpoint restoration. Exact content/hash verification belongs on HPC. The fixed UMAP coordinates are retained, but a LogNormalize builder and SCT-named RDS need a command-history/coordinate provenance check.
- **Figure 7:** the native matrix and completed updated DE packages provide a useful restart point. The latest RAD FASTQ and frozen read-to-gene table were absent at inspected preservation mirrors; check original HPC locations if upstream replay is needed. The updated 8,135-gene analysis is selected. Replace stale A/C, retain the matching D lineage, and keep E pending.

## Evidence authority

Read `../AUTHOR_DECISIONS.md` before historical notes. Detailed source citations and numerical comparisons are in `../context/evidence/biology_methods.md`, `biology_methods_supplement.md`, and `longbench_genotype_methods_verification_20261022.md`. The supplement's unresolved normalization finding qualifies the earlier candidate UMAP description. The full-cohort package's later DEG regeneration supersedes its initial stale-output warning.

The retained full-cohort package was previously reported as passing 26/26 packaged checks; this is historical validation evidence to independently verify, not a new full rerun in this audit. Figure 6 reference-restricted counts and Figure 7 native positive-depth cohorts are intentionally different populations.

## Tasks and acceptance criteria

### F5-01 — Identify the exact RAGE receptor/cell-label source for each current panel before regenerating.

Priority: **P0**. Panels: 5A, 5B, 5C, 5D, 5E, 5F. Dependencies: none.

**Existing inputs / evidence**

- `/Volumes/rad_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811/RUN_ON_CLUSTER.md`
- `/Volumes/rad_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811/RUN_STATUS.md`
- `/Volumes/rad_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811/RUN_RAD_BLAZE.md`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/biology_methods.md`

**Existing scripts**

- `/Volumes/rad_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811/run_flexiplex_bcrtcr.sh`
- `/Volumes/rad_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811/run_rad_blaze_bcrtcr.sh`
- `/Volumes/rad_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811/join_flexiplex_bcrtcr.py`
- `/Volumes/rad_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811/join_tool_bcrtcr.py`

**Checkpoints to retain**

- panel-to-run map
- cell identity reference with provenance
- per-read assignment/receptor ledger
- per-cell exclusive native/corrected receptor table

**Actions**

- Use ERR3268991 cell-line mixture, not the TNBC lymph-node sample. Distinguish the 4505 discovery reference from the 3585-barcode cell identity map.
- Resolve artwork labels versus candidate rerun outputs. The schematic and printed category totals do not match that identity map; recover the actual workbook/run used.
- Verify successful RAD producer command; an archived stderr contains offensive: command not found. Preserve actual Flexiplex 1.02.5 receptor alignment versus 1.02.6 discovery provenance.
- Retain maximum-PAF-match receptor classification, tie rule, read ambiguity policy, barcode orientation and absent-label status. Convert the Flex cumulative corrected column to exclusive corrected-only when comparing exclusive classes.

**Acceptance checks**

- Each final panel resolves to a selected run and source table.
- Native plus corrected-only equals assigned within the declared accounting; cumulative Flex columns are not double counted.
- Receptor reference/hash, mapper settings and cell labels are captured; no successful execution inferred solely from intended wrapper.

**Release outputs**

- annotated receptor ledger/schema
- per-cell plot tables
- renderer and caption provenance

**Decision gate:** Select canonical panel source if candidate reruns do not reproduce artwork; statistical design requires review.

### F5-02 — Recover final component-based LR-Split-seq comparison and its paired read/UMI tables.

Priority: **P0**. Panels: 5G, 5H. Dependencies: none.

**Existing inputs / evidence**

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/splitseq_shortread_20260727/README.md`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/prism_inventory_source.Pn5f14/SPLIT-seq benchmarking.csv`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/biology_methods_supplement.md`

**Existing scripts**

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/splitseq_shortread_20260727/parse_bc_umi.py`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/splitseq_shortread_20260727/lr_vs_sr_umi.py`

**Checkpoints to retain**

- 568-cell reference table
- three-component barcode/UMI extraction ledger
- selected component layout and tool run manifest
- paired read/UMI table
- executed paired statistics

**Actions**

- Use long SRR13948564 and matched short SRR13948565. Restore depth-matched short-read reconstruction and exact cell-UMI counting.
- Recover final component-based FLAMESV2/Flexiplex plus poly-T command/layout/correction limits/output and corresponding RAD run. Do not substitute historical two-pass or MATCHED_SPLIT comparator.
- The retained six-column Prism table has 568 rows; columns 1/3 sum 2,078,171 / 1,156,252 reads. Identify all columns and barcode order from original source, not totals alone.
- Distinguish full-input assigned fractions from read counts limited to 568 cells and from UMI counts. Recover final UMI-collapse rules/source link.
- Reconcile paired t-test versus signed-rank text, using the same explicit pairs and multiple-comparison policy.

**Acceptance checks**

- Barcode/UMI orientation and inclusion criteria are explicit and paired cells align by ID.
- Published/read/UMI denominators are distinct and exact.
- The executed final component comparator is identified; old RAD-only/reference scripts are not misrepresented as its producer.
- Test names and values agree across code, legend and rebuttal.

**Release outputs**

- cell reference
- paired read/UMI source data
- final component configurations
- statistics and figure exports

**Decision gate:** Final comparator provenance and paired test D05 remain unresolved; prepare reviewable evidence before choosing a replacement.

### F6-01 — Validate and preserve the independent bulk genotype panel and short-read reference.

Priority: **P0**. Panels: 6A, 6B, 6C. Dependencies: none.

**Existing inputs / evidence**

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_snont_postdemux_vireo_20260803/bulk_donor_panel/provenance/README.md`
- `/Volumes/rad_data/reviewer_comment_data/reviewer_response_20260804/manuscript_tables/SN_ONT_CROSS_TOOL_VIREO_VALIDATED_20260804.md`
- `/Volumes/rad_data/reviewer_comment_data/reviewer_response_20260804/objects/longbench/durable_sources/BLAZE_panel_matched_20260804`

**Existing scripts**

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_snont_postdemux_vireo_20260803/scripts/bulk_donor_panel/run_fastp_one.sh`
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_snont_postdemux_vireo_20260803/scripts/bulk_donor_panel/run_bulk_panel.sh`

**Checkpoints to retain**

- bulk sample/accession manifest
- reference FASTA/GTF/sites hashes
- 360814-site donor VCF and index
- released Illumina labels and panel-validation table

**Actions**

- Recover the retained validated donor panel before rerunning bulk mapping. Preserve eight independent bulk cell-line libraries and exact named order.
- If needed reproduce fastp 0.23.4, Rsubread subjunc unique annotation-assisted mapping, GENCODE v44 and 1000 Genomes phase 3 hg38 AF > 5% sites.
- Keep bulk CellSNP cellTAG/UMItag None separate from single-nucleus CB/UB settings. Validate panel GT-based Vireo against released Illumina calls.

**Acceptance checks**

- Reference/cell-line/variant order and allele compatibility are explicit.
- Historical360814-site panel and all 12,012 released hard calls match under documented comparison.
- An independent bulk panel is not described as the authors unreleased private VCF.

**Release outputs**

- bulk panel provenance and permitted VCF
- reference validation
- donor/sample key

**Decision gate:** None for recovery and validation.

### F6-02 — Resume per-tool genotype analysis from retained alignments and CellSNP checkpoints.

Priority: **P0**. Panels: 6A, 6B, 6C. Dependencies: F6-01.

**Existing inputs / evidence**

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_snont_postdemux_vireo_20260803`
- `/Volumes/rad_data/reviewer_comment_data/reviewer_response_20260804/objects/longbench/durable_sources/BLAZE_panel_matched_20260804`
- `/Volumes/rad_data/reviewer_comment_data/reviewer_response_20260804/manuscript_tables/SN_ONT_cross_tool_vireo_per_cell_graph_ready.csv`

**Existing scripts**

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_snont_postdemux_vireo_20260803/scripts/run_snont_tool_cellsnp_vireo_when_ready.sh`
- `/Volumes/rad_data/reviewer_comment_data/reviewer_response_20260804/objects/longbench/durable_sources/BLAZE_panel_matched_20260804/scripts/compare_snont_tools.py`

**Checkpoints to retain**

- per-tool BAM/BAI and alignment manifest
- CellSNP AD/DP/sites/barcodes
- Vireo donor probabilities and hard assignments
- per-cell status and selected-list table

**Actions**

- Validate retained RAD/Flexiplex/BLAZE BAMs and CellSNP matrices. Do not repeat upstream alignments merely to rebuild graphs.
- For missing producer stages, use independently aligned demultiplexed FASTQs and FLAMES 2.0.1 with tag retention; this is distinct from Figure 7 common raw alignment.
- Use CellSNP 1.2.3 cellTAG CB UMItag UB minMAF 0.1 minCOUNT 10 and genotype, then Vireo 0.5.8 bulk GT panel with ambient estimation. Executed logs override README UMItag None typo.
- Use panel-matched BLAZE and explicit same/different/doublet/unassigned/not-selected/missing-row categories. Strip terminal-1 consistently.

**Acceptance checks**

- Matrix dimensions/sites/barcodes and tag definitions match.
- All 12,012 reference barcodes participate in figure summaries; strict named-singlet recall uses 5,782.
- Recall=same/5782 and conditional concordance=same/(same+different). Absent selected-list membership is not lack of a genotype result.

**Release outputs**

- per-cell genotype table
- state/count/denominator tables
- Vireo/CellSNP provenance and suitable checkpoints

**Decision gate:** None for recovery and validation.

### F6-03 — Validate fixed UMAP provenance and regenerate genotype overlays/statistical inputs.

Priority: **P1**. Panels: 6A, 6B, 6C. Dependencies: F6-02.

**Existing inputs / evidence**

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/biology_methods_supplement.md`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/longbench_genotype_methods_verification_20261022.md`
- `/Volumes/rad_data/reviewer_comment_data/reviewer_response_20260804/manuscript_tables/SN_ONT_cross_tool_vireo_per_cell_graph_ready.csv`

**Existing scripts**

- `/Volumes/rad_data/LongBench_Illumina_SC_SN_Seurat_UMAP_20260805/scripts/build_longbench_illumina_seurat_umap.R`

**Checkpoints to retain**

- fixed barcode-indexed coordinates
- Seurat object command history export
- per-cell overlay table
- statistical observation table

**Actions**

- Inspect referenced /Volumes/rad_data/LongBench_Illumina_SC_SN_Seurat_UMAP_20260805 or its mapped HPC root. Builder uses LogNormalize 10,000,3,000 VST genes,50 PCs,first 30 PCs,30 neighbors,min.dist 0.3,cosine,seed 20260805.
- Only SCT-named RDS objects were found; inspect stored command history/coordinates before assigning the LogNormalize recipe to the final figure. Preserve fixed coordinates rather than generating a new embedding without review.
- Summarize all 12,012 reference nuclei; annotated display combines 5,782 named singlets and 59 doublets. Do not substitute native DE cohorts or expression-rescue classifier as genotype truth.
- Prepare factor/replication table to resolve one-way versus two-way ANOVA and comparisons.

**Acceptance checks**

- Overlay joins preserve coordinates and barcode identity.
- Final normalization provenance follows actual source object, not filename alone.
- No label-driven re-embedding or unsupported biological replication assumptions.

**Release outputs**

- fixed coordinates and recipe
- overlay/source tables
- plots and statistical results

**Decision gate:** UMAP source evidence required; D04 governs final statistical design.

### F7-01 — Preserve and validate updated native expression matrices and their raw-read/segment lineage.

Priority: **P0**. Panels: 7A, 7B, 7C, 7D. Dependencies: none.

**Existing inputs / evidence**

- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/SN_ONT_H146_H526_fullcohort_DEG_20260822/METHODS.md`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/SN_ONT_H146_H526_fullcohort_DEG_20260822/provenance/RAD_4acbe00_full_rebuild_20260828/README.md`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/SN_ONT_H146_H526_fullcohort_DEG_20260822`

**Existing scripts**

- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/SN_ONT_H146_H526_fullcohort_DEG_20260822/provenance/source_snapshots/scripts/align_arm.sh`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/SN_ONT_H146_H526_fullcohort_DEG_20260822/provenance/source_snapshots/scripts/assign_genes.py`
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/SN_ONT_H146_H526_fullcohort_DEG_20260822/provenance/source_snapshots/scripts/build_matrices.py`

**Checkpoints to retain**

- native MEX features/barcodes/matrix
- Vireo labels and positive-depth cohort lists
- read-to-gene table
- original-read/emitted-segment ledger
- matrix validation

**Actions**

- Use latest RAD 4acbe00 native matrix retaining all emitted records including CT segments; preserve complete existing matrices before seeking upstream files.
- Common raw-read alignment uses minimap2 2.30 splice/no secondary/MD/-Y and GENCODE v44. Gene call uses primary MAPQ >= 1, summed overlap with unmerged exon records, no strand restriction, no ties.
- Emitted RAD segments inherit the original physical read gene call; do not replace with per-segment alignment. Exact cell-gene-UMI deduplication applies; missing UMI records count individually.
- If raw replay needed, restore original RAD FASTQ and frozen read-gene table at recorded paths or regenerate from validated source identities; they were absent at inspected local mirrors.

**Acceptance checks**

- Matrix dimensions/keys/count sums and positive-depth cohorts match updated checkpoints.
- RAD count promotion and subsequent DEG refresh are distinguished from the stale README warning.
- No universal physical-read deduplicator changes emitted-segment accounting.

**Release outputs**

- native matrix bundles
- cohort eligibility tables
- gene assignment/segment manifest and schemas

**Decision gate:** None for recovery and validation.

### F7-02 — Regenerate common-universe expression results, Venn/confidence panels and directional threshold grids.

Priority: **P1**. Panels: 7A, 7B, 7C, 7D. Dependencies: F7-01.

**Existing inputs / evidence**

- `/Volumes/rad_data/reviewer_comment_data/082426_volcano_plots/three_tool_overlay_and_H146_vs_H526_20260825/METHODS.md`
- `/Volumes/rad_data/reviewer_comment_data/082426_volcano_plots/Illumina_tool_confidence_19plots_20260825`
- `/Volumes/rad_data/reviewer_comment_data/082426_volcano_plots/SN_ONT_H146_H526_vs_all_combined_F1_sweeps_20260831/README.md`
- `/Volumes/rad_data/reviewer_comment_data/082426_volcano_plots/SN_ONT_H146_H526_vs_all_combined_F1_sweeps_20260831/inputs/direct_H146_H526_F1_threshold_sweep_grid.tsv`

**Existing scripts**

- `/Volumes/rad_data/reviewer_comment_data/082426_volcano_plots/three_tool_overlay_and_H146_vs_H526_20260825/scripts/build_overlay_and_direct.R`
- `/Volumes/rad_data/reviewer_comment_data/082426_volcano_plots/Illumina_tool_confidence_19plots_20260825/generate_plot23_spearman_and_log2fc.R`
- `/Volumes/rad_data/reviewer_comment_data/082426_volcano_plots/Illumina_tool_confidence_19plots_20260825/generate_plot24_expanded_threshold_sweep.R`
- `/Volumes/rad_data/reviewer_comment_data/082426_volcano_plots/SN_ONT_H146_H526_vs_all_combined_F1_sweeps_20260831/scripts/generate_combined_figures.R`

**Checkpoints to retain**

- eligibility and normalization totals
- full direct-DE table
- 8135 common gene IDs and recomputed BH statistics
- directional truth/call membership
- Venn regions
- confidence fit inputs/specification
- F1 grid and plot tables

**Actions**

- Use all positive-depth named native cohorts; gene eligibility >= 10 molecules and >= 1% detection; CP10K from full prefilter library then log2(1 + x), two-sided scran pairwiseWilcox and BH.
- Keep one-versus-rest analyses distinct from direct H146/H526. For direct comparison recompute BH over common 8,135 genes and use fixed Illumina FDR < 0.05 absolute FC > 1 truth, direction-specific.
- Regenerate old A/C from current data. Expected supported recoveries RAD 654, BLAZE 522, Flexiplex 556 and Venn 117/29/26/29/66/22/442; old 8,126 outputs are historical.
- For confidence slopes recover actual fit/intercept/selection/capping rule; do not assume visual 0–20 limits define fitting data or substitute Spearman plots.
- Rebuild 9 × 11 grids with strict inequalities and fixed Illumina truth: 412 H146-high / 769 H526-high. Match 594 displayed D labels with documented rounding; do not tune data to labels.

**Acceptance checks**

- All platforms share 8,135 identical gene IDs and BH family.
- Direction, effect pseudocount 0.1, thresholds, denominators and zero-denominator F1 = 0 agree.
- Native matrices and reference-restricted Figure 6 cohorts remain distinct.
- New A/C source and figures agree with D and rebuttal; plot-only labels do not define statistics.

**Release outputs**

- complete tested statistics and eligibility
- Venn membership
- confidence source/fit table
- threshold grids
- new A–D exports

**Decision gate:** Confirm exact intended confidence-fit/annotation presentation if original workbook remains missing; updated 8,135 analysis is already selected.

### F7-03 — Keep pending collaborator panel explicit until its definition and sources arrive.

Priority: **P2**. Panels: 7E. Dependencies: none.

**Existing inputs / evidence**

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/extracted/RAD R1 figures and legends.txt`

**Checkpoints to retain**

- panel status/decision record
- analysis/input/code specification if retained

**Actions**

- Record author confirmation that Olivia panel is pending. Obtain definition, inputs, code and validation if retained, or record removal. Continue 7A–D independently.

**Acceptance checks**

- No placeholder is presented as a complete analysis or filled with inferred methods.

**Release outputs**

- final panel specification or explicit removal record

**Decision gate:** D07: collaborator analysis or author removal decision required.

## Handback boundary

Use the root checkpoint specification and machine-readable task queue. Restore missing assets before new expensive producers, keep genotyping and gene-count alignment workflows distinct, and verify per-cell/per-gene identity as well as totals. Export portable tables/matrices plus provenance, statistics, plots and validation reports. Native Prism QA may require a desktop handback. A replacement run, new embedding or altered counting rule must be clearly versioned and reviewed before it changes the manuscript.

## Additional retained checkpoint paths verified by metadata

These files were checked for presence/size, not integrity or scientific content. Exact hashes and sibling matrix/site/barcode/index validation remain HPC tasks.

- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_snont_postdemux_vireo_20260803/align/RAD/align2genome.bam` — 28219388685 bytes; present.
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_snont_postdemux_vireo_20260803/align/Flexiplex/align2genome.bam` — 49036591237 bytes; present.
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_full_demux_20260730/runs/flames2.0.1_longbench_published/SN_ONT/align2genome.bam` — 36413849035 bytes; present.
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/SN_ONT_RAD_bulk_cellline_bundle_20260803/RAD/cellsnp/cellSNP.tag.AD.mtx` — 53882353 bytes; present.
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_snont_postdemux_vireo_20260803/cellsnp/Flexiplex/cellSNP.tag.AD.mtx` — 89752186 bytes; present.
- `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_snont_postdemux_vireo_20260803/rebuilds/BLAZE_rebuilt_bulk_panel_tool_postdemux_20260804T135956Z/cellsnp/cellSNP.tag.AD.mtx` — 69111693 bytes; present.
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/SN_ONT_RAD_bulk_cellline_bundle_20260803/bulk_donor_panel/final/fixed_8line_bulk_illumina_donor_panel.vcf.gz` — 18128667 bytes; present.
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/SN_ONT_H146_H526_fullcohort_DEG_20260822/RERUN.sh` — 876 bytes; present.
- `/Volumes/rad_data/reviewer_comment_data/LongBench_comps/SN_ONT_H146_H526_fullcohort_DEG_20260822/results/VALIDATION.tsv` — 2519 bytes; present.
