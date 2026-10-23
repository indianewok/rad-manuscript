# Figures 5–7 checkpoint handback

These outputs resume retained analytical checkpoints. No FASTQ demultiplexing,
alignment, CellSNP, Vireo, or differential-expression test was rerun. The current
BH families, directional calls, threshold metrics, genotype summaries and source
table renders are recomputed. Full upstream execution and native Prism QA remain
separate validation levels.

## Commands

From the repository root:

```bash
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 Rscript scripts/revision/figures_567_inspect_umap.R /dartfs/rc/lab/A/AckermanLab/CMV/rad_data/LongBench_Illumina_SC_SN_Seurat_UMAP_20260805/objects/LongBench_Illumina_SN_SCT_Seurat_UMAP.rds source_data/figure_06
/usr/bin/python3 scripts/revision/figures_567.py build
/usr/bin/python3 scripts/revision/figures_567.py validate
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 MPLCONFIGDIR=/tmp/rad_manuscript_fig567_mpl /usr/bin/python3 scripts/revision/figures_567.py render
sbatch --parsable scripts/revision/figures_567_checkpoints.sbatch
sbatch --parsable scripts/revision/figures_567_bam_checks.sbatch
```

`build --project-root PATH --output-root PATH` resolves retained checkpoints under
the chosen reviewer project and writes a separate output tree. `render` uses only
that tree's portable `source_data` files. `validate` checks source-data hashes
against the successful build receipt; a changed source file fails validation.

The full matrix/donor/CellSNP validation uses one CPU and 8 GB RAM. The BAM byte
hash and index/header audit uses one CPU and 2 GB RAM. The submitted partition
`standard` was checked live and contains no GPU GRES. The account's permitted
`lsonglab_gpu` QoS does not change that CPU-only placement. The job scripts request
`--gres=gpu:0`. Initial jobs 9976792 and 9976798 stopped at newly discovered
duplicate-variant assertions; the unchanged source files were subsequently
examined and explicit historical row identity was implemented. No failed run is
represented as passed.

## Figure 5: receptor candidates and verified selected LR-Split sources

The receptor candidates retain mutually exclusive native/corrected-only counts. Flexiplex cumulative counts subtract native once; assigned totals remain RAD 7,808,411, BLAZE 5,588,936 and Flexiplex 6,595,231. Final receptor-artwork binding and the successful RAD producer remain unresolved.

The user-uploaded selected LR-Split recovery at commit 07b39852 restores exact RAD ED2 and component-polyT producing runs, all 568 physical-cell IDs and their original Prism rows. The complete saved assignment ledgers reproduce all 2,272 read/UMI counts. Selected read–cell pairs total 2,078,171/1,156,252, median 1,979.5/1,102.5; cell–UMI pairs total 1,891,704/1,050,292, median 1,866/1,042 (RAD/component). Globally distinct full-input reads are a separate count: 2,498,488/1,338,285 of 5,764,421 input reads, or 43.34%/23.22%. The displayed component 23.35% is not reproduced by either distinct-read or assignment-row fractions.

The saved native analysis is the existing two-sided paired t test, t=14.959474687143327, df=567, P=6.890554214980993e-43. Independent native archive validation verifies dataset and graph links and all 568 row identities. No statistical choice or star was changed. Final exported panel/annotation appearance remains native QA. The precise Figure 5H short-read depth-matched checkpoint or selection/seed remains unrecovered; prior RAD ED1 intersections are not substituted for current ED2. See the [selected-source handback](figure_05_handback.md) and [walkthrough](../docs/figure_05.md).

## Figure 6: reference identities and fixed embedding

The recovered reference contains all 12,012 barcodes: 5,782 named singlets, 59
doublets and 6,171 unassigned nuclei. Per-cell output distinguishes selection,
Vireo state and reference outcome. The primary BLAZE source is panel matched;
the published/private-panel sensitivity result is not substituted.

Strict named-singlet outcomes `(same, different, doublet, unassigned, not selected)`:

| Tool | Same | Different | Doublet | Unassigned | Not selected |
|---|---:|---:|---:|---:|---:|
| RAD | 5,324 | 32 | 246 | 165 | 15 |
| BLAZE | 4,450 | 12 | 766 | 308 | 246 |
| Flexiplex | 4,674 | 17 | 725 | 340 | 26 |

Strict recall divides by 5,782. Conditional concordance divides by same plus
different. Every reference barcode remains present in the long source table.

The retained SN Seurat RDS was loaded and its stored commands inspected. Its
coordinates match the fixed 12,012-barcode table within an absolute 1e-12 export
tolerance. This identifies **SCTransform v2 with glmGamPoi**, followed by SCT PCA
with 50 components, neighbor construction from PCs 1–30, Louvain resolution 0.5,
and UMAP with PCs 1–30, 30 neighbors, minimum distance 0.3, cosine distance and seed
20260805. The stored call specifies one UMAP thread. The LogNormalize script is a
different candidate recipe and must not describe this selected embedding.
`umap_object_commands.txt`, `umap_object_summary.txt` and the inspection session
are preserved. No re-embedding was performed.

The BAM program headers retain the actual genotype alignment producer:
minimap2 2.28-r1209 via FLAMES 2.0.1, samtools 1.21, `-ax splice -y -k14
--secondary=no --seed 2023`, an annotation junction BED and `--junc-bonus 1`.
The RAD source path is `rad_920adda_current`; the BLAZE source is
`blaze2_2.5.0_longbench_published`. These pins are specific to Figure 6 and must
not be replaced with Figure 7's RAD 4acbe00 and common-raw alignment recipe.
The original BAM headers and index statistics are exported without changing
reference names or coordinates. All BAM and BAI compressed bytes were hashed
in job 9976799 (13 minutes 13 seconds); boundary and index/header checks passed.

The union per-cell table also retains selected barcodes outside the Illumina
reference. Figure 6C source counts use all selected named genotypes; the
reference-restricted recall table uses its separate, fixed denominator. The
Figure 6A scripted rendering includes all 12,012 fixed reference coordinates.

The donor VCF contains **360,814 records and 360,809 unique variant keys**. Five
record pairs are byte-identical duplicates. The duplicate ledger retains the
original and repeated record ordinal. RAD and Flexiplex CellSNP each retain two
rows for chr4:74446969 A/G; BLAZE does not. The row order, matrix dimensions and
alleles are preserved. This is a provenance caveat in the historical panel;
deduplicating it would be a separately reviewed new analysis. The previous
wording “360,814 sites” should be clarified to “360,814 VCF records.”

**D04 author instruction (2026-10-23):** preserve existing selected statistics and annotations. No replacement test was selected and no stars were removed. The one-way/two-way ANOVA wording discrepancy remains documented. Source observations have three tools × eight donor strata within one mixed library; donor categories do not create independent library replicates. The new PNGs verify source values and fixed coordinates; they do not replace the selected inferential annotations.

## Figure 7: updated common universe

The 24,405-row C5 table contains 8,135 unique genes for each of three tools. The
Illumina reference values are identical across tool rows. BH adjustment is
independently recomputed from the stored raw P values for each tool and the
Illumina reference; the maximum allowed numerical discrepancy is 1e-12, selected
for decimal export precision. The Wilcoxon P values themselves are retained, not
recomputed in this lightweight resume mode.

Same-direction Illumina-supported recovery is RAD 654, BLAZE 522 and Flexiplex
556. The exclusive regions are RAD-only 117, BLAZE-only 29, Flexiplex-only 26,
RAD/BLAZE 29, RAD/Flexiplex 66, BLAZE/Flexiplex 22 and all three 442. The source
table includes every gene's membership. The Venn export uses schematic circle
areas; counts are authoritative.

All 594 directional threshold combinations are recomputed with strict
inequalities, fixed Illumina truth (412 H146-high and 769 H526-high), and explicit
TP/FP/FN/TN. F1 is zero at a zero denominator. All displayed one-significant-digit
artwork labels are compared using decimal half-up rounding, including tie cases.

The updated volcano uses the common BH family. ASCL1 and POU2F3 are labeled only
when present; any additional final annotation list requires artwork review.
The candidate confidence fit is uncapped OLS with an estimated intercept over
all directional Illumina-truth genes. Its slopes are:

| Direction | RAD | Flexiplex | Genes |
|---|---:|---:|---:|
| H146-high | 2.258913 | 1.216813 | 412 |
| H526-high | 2.454322 | 1.183511 | 769 |

**Fit-provenance gate:** recover the executed workbook/filter/fit specification
and bind it to the selected artwork. The computed candidate is not a recovered
execution definition; no coefficient is selected by similarity to a label. The
source point and candidate coefficient tables are included for inspection.

The selected native RAD matrix retains all emitted concatemer segments and sums
to 22,875,174 molecules. The complete native MEX matrices and named positive-depth
cohorts are validated separately. Frozen original-read gene inheritance and exact
cell–gene–UMI counting remain the selected production contract. The original RAD emitted
FASTQ and frozen read-to-gene table are missing at the checked scratch and
preservation paths, so complete upstream segment-ledger reconstruction/raw replay
remains an explicit recovery exception. Existing matrix/C5 resumption proceeds.

**D07 resolved by author (2026-10-23):** remove Figure 7E. Current Figure 7 comprises A–D. No collaborator analysis or placeholder is substituted. F7-03 is passed by explicit scope removal.

## Machine-readable evidence

- `figures_567_checks.tsv/json`: rebuilt source-table scientific checks.
- `figures_567_checkpoint_checks.tsv`: complete native matrix, donor and CellSNP
  content checks, including historical duplicate-record qualifications.
- `figures_567_bam_checks.tsv`: complete compressed-byte hashes plus quickcheck
  and index/header identity; this is not a full decoded-record/tag audit.
- `../manifests/figures_567_assets.tsv` and
  `figures_567_checkpoint_assets.tsv`: exact retained input hashes and roles.
- `../manifests/figures_567_run.json`: code hash, command and built output hashes.
- `../manifests/figures_567_tasks.json`: task-specific status and remaining gate.
- `figures_567_clean_render_location.json`: minimal-environment rendering from
  copied source tables, without raw reads, matrices or RDS objects.
- `figures_567_mutation_guard.json`: a deliberate source-table change is rejected
  and the restored baseline passes. This is the local hash guard; global stage
  graph invalidation is tested separately.

The final source tables, figures and captions still require author selection and
Prism-capable desktop QA where applicable. Nothing in this handback authorizes
publishing or changing repository/archive visibility.

## Data-first walkthroughs and exact producer pins

Start with [Figure 5](../docs/figure_05.md), [Figure 6](../docs/figure_06.md), or [Figure 7](../docs/figure_07.md). Each begins with versions/parameters and exposes real bounded input excerpts, schemas, a small transformation and visible PNG proofs. The [parameter registry](../manifests/figures_567_tool_parameters.tsv) records exact flags/build hashes and explicit unknowns. The native Figure 6 RAD executable is the patched920adda build b2feda73…; Figure 7 is4acbe00 build01ae4700…. Flexiplex native FASTQ and diagnostic-sidecar executions use the same pinned38dccd37… build but are separate source runs.

For Figure 7 direct H146/H526 tests, eligibility is >=10 molecules and >=1% detected cells within each pair-only cohort. Other six lines do not influence eligibility. Full-library CP10K precedes filtering. The current common universe is8135 genes. Direct scran tests use SerialParam; native producer seed20260825, while the common-Illumina producer has no explicit seed. The executed selected scripts are retained in source_data/figure_07/provenance.

The source checkpoints staged under ignored checkpoints/figure_06 and figure_07 are byte-verified copies, indexed by manifests/figures_567_staged_checkpoints.tsv. No giant matrices were added to Git. The walkthrough checks compare the separate human-readable scripts against complete retained output tables; source excerpts remain explicitly bounded and are not claimed as full upstream reproduction.

## Recovered selected C2 assignment checkpoint

The full RAD emitted-assignment checkpoint was recovered at the preserved path in [the access manifest](../manifests/figures_567_assignment_access.tsv). Job 9977822 verified its recorded compressed-byte SHA, complete gzip stream, all 57,885,606 five-field rows, exact/corrected flag totals, and membership in all 12,423 selected matrix barcodes. [Full receipt](figures_567_assignment_recovery.json). Its first 10 actual rows and full per-barcode row counts are exposed in the Figure 7 walkthrough. These are assignment rows, not unique physical reads or molecules. The extractor had stripped orientation/CT suffixes, and the table lacks gene IDs and segment coordinates, so this recovers C2 but does not complete the gene/segment-boundary ledger. No raw demultiplexing or alignment was restarted. The 2.36 GB source is not copied into Git or the default archive.

The [bounded Figure 7C fit-definition search](figures_567_fit_definition_search.json) found no native Figure 7 project or executed directional BLAZE-axis regression definition in the checked primary folders. Regressions in the available scripts use different reference axes or contrasts. The existing fit gate therefore remains; no fit was selected by closeness to an annotation.
