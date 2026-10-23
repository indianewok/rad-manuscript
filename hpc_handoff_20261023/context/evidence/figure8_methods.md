# Figure 8 methods provenance audit

Audit date: 2026-10-22. Read-only audit of mounted project material. Original source documents were not changed. This report distinguishes source-manuscript statements, preserved execution evidence, and unverified details. No later BCR-CSR analysis has been substituted for the displayed Figure 8 results.

## Figure identity and main finding

The supplied Figure 8 is the original IgH/isotype/spatial clonotype analysis, formerly Figure 5 in the source manuscript. It is not the later direct-MiXCR BCR-CSR workflow and is not the separate murine Visium HD benchmark. Figure 8A compares Ramos cells, Nojima in vitro B-cell culture, and tonsil in situ. Figure 8B reports 10,744 total clones and 620 class-switching clones. Figures 8D–E display clones 2277, 7445, and 5725. The spatial plots are conventional Visium spots.

Exact artifacts inspected:

- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/extracted/figure_images/paragraph_17_image8.png`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/extracted/RAD R1 figures and legends.txt`
- `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/extracted/Manuscript.txt`, paragraphs 52–56, 102, 105, and 108.

**No preserved script, parameter record, or result table was found that reproduces the exact 10,744/620 clone counts or the three displayed clone IDs.** In particular, no run-bound SHazaM/SCOPeR invocation, membrane/secreted classification rule, or final plot-building R script was found in the inspected project directories. The original Methods supply the conceptual procedure but do not resolve these parameters.

## What the manuscript itself establishes

Paragraph 102 states RNA-Bloom2 processing, IG/TR classification by minimap2 against a combined hg38 receptor reference, IgBLAST with human IMGT V/D/J/C databases, an E-value of 1e-4, AIRR output, clonotype detection, gene-level collapse of multi-allelic V calls, and separate IG/TR runs for mixed datasets.

Paragraph 105 states that SHazaM estimated a threshold from nearest-neighbor junction distances; SCOPeR hierarchically grouped sequences with common IGHV and IGHJ assignments; isotypes were tabulated from constant-gene calls; and clones with more than one constant gene were labeled class-switching. It states pheatmap hierarchical clustering of per-clone isotype read counts. It does not provide the numerical threshold, distance model, normalization, linkage, junction length grouping, productive/full-length filters, or minimum support per isotype.

Paragraph 108 states Seurat 5.3.0, imported microenvironment annotations, spatial coordinate projection, T2T-CHM13 IGH mapping, and splice-aware depth with `-ax splice -C0 --splice-flank=no`. It does not define secreted/membrane/unannotated classification. These source-manuscript claims can be preserved as author-provided methods, but the precise flags and software versions are not independently tied to Figure 8 by available execution records.

## Spatial tonsil provenance: preserved metadata

Strong provenance records:

- `/Volumes/rad_data/bcr_csr_project/datasets/tonsil/provenance/engblom_source.md`
- `/Volumes/rad_data/bcr_csr_project/datasets/tonsil/README.md`
- `/Volumes/rad_data/bcr_csr_project/datasets/tonsil/analysis/switch_t2t_v1/README.md`

These identify the original data as Engblom et al., Science 382, eadf8486 (2023), EGA EGAS00001007337 / EGAD00001011062, with associated public material at Zenodo 7961605. Eight PacBio CCS/HiFi libraries cover six tonsil sections from one donor; sections 17 and 32 have two capture libraries each. Therefore eight libraries must not be described as eight independent biological replicates. The library chemistry is conventional Visium, with a 16-base spatial barcode and a 12-base UMI; it is not the paired-barcode Visium HD chemistry.

The original upstream project is explicitly referenced at:

`/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/swedish_tonsil_spatial/`

The source record identifies the author archive `scripts/functions/long-read-processing-STAR-paper-main.zip`, commit `6eeace22f4005042c918bc190a8a50b5209ba6d5`; `run86.py` extracts 16-base barcodes and 12-base UMIs. The source record also describes `data/tonsil/1_LR-SpatialVDJ/read_lists/Tonsil-descrsR1-ST-Barcode.tsv` (666,700 author rows, all with 12-base UMIs). These are referenced upstream paths, not recovered files in the inspected mounted tree.

Original accessions and sections in that record:

| Accession | Section/library label |
|---|---|
| EGAF00008107340 | 17_1T_1B |
| EGAF00008107341 | 32_1T_1B |
| EGAF00008107344 | 17_4T_1B |
| EGAF00008107345 | 32_4T_1B |
| EGAF00008107350 | 21 in EGA; author barcode metadata says 22 (unresolved conflict) |
| EGAF00008107351 | 31 |
| EGAF00008107352 | 12 |
| EGAF00008107353 | 16 |

The displayed Figure 8 section(s) remain unspecified. The existence of six source sections does not establish that all six were used for the 10,744-clone denominator or each spatial panel.

## Retention and obsolescence warning

The current tonsil README states that the old MiXCR/clone branch and superseded 10-base-UMI RAD results/analysis products were permanently deleted without an archive. The `switch_t2t_v1/README.md` similarly states that superseded receptor annotations, candidate lists, switch calls, audits, and result counts are no longer a validation baseline. This does not prove that the original SCOPeR Figure 8 files were the deleted files, but it means the current result tree cannot be assumed to preserve the old analysis.

The current September replacement workflow annotated all 2,725,476 unchanged original CCS reads directly with MiXCR and joined RAD tags externally; RAD-emitted insert sequences were excluded as annotation inputs after source checks detected internal base deletion. That is a later, separate workflow. It must not be described as the method behind the displayed Figure 8 unless the figure is regenerated and its provenance established. The current 12-base-UMI correction does not retroactively prove that the original Figure 8 used 12-base UMIs.

## Preserved RNA-Bloom / IgBLAST code: relevant, not run-bound

Scripts:

- `/Volumes/rad_data/project_specific_scripts/lr_igblast.sh`
- `/Volumes/rad_data/project_specific_scripts/rnabloom_to_igblast.sh`
- `/Volumes/rad_data/project_specific_scripts/align_rnabloom_igblast.sh`
- `/Volumes/rad_data/project_specific_scripts/assemble_lr_abs.sh`

`lr_igblast.sh` invokes RNA-Bloom with `-k 20 -e 3 -extend -sensitive -stage 2 -long`, then uses `rnabloom.longreads.corrected.long.fa.gz`. `assemble_lr_abs.sh` uses `-k 20 -e 7 -extend -sensitive -stage 2 -long` after porechop. The preserved NBC record `/Volumes/rad_data/bcr_csr_project/datasets/bc1/rnabloom/output/STARTED` records the latter settings (`-e 7`, 64 threads), with input `reformat_clean.fq.gz`. Corrected long-read output is present. These records support read correction, not the source manuscript's stronger assertion that Figure 8 used assembled consensus transcripts. No per-cell, per-UMI, or per-clone assembly grouping was established.

The scripts run IgBLAST with `-organism human`, IG V/D/J/C databases, `human_gl.aux`, AIRR format 19, and (in `lr_igblast.sh` and `rnabloom_to_igblast.sh`) `-clonotype_out`. TCR processing uses TR V/D/J databases in a separate invocation. Complete V(D)J records are selected with `complete_vdj == "T"`; barcode/UMI fields are parsed from RAD headers. None of the inspected generic IgBLAST invocations explicitly sets `-evalue 1e-4`. Consequently the manuscript's E-value is not corroborated by these scripts. The scripts' existence alone does not prove that all those filters were used for Figure 8.

RNA-Bloom v2.0.1 is explicitly logged for barcode3/4 runs in `/Volumes/rad_data/20250918_barcode_3_results/rnabloom.log` and `/Volumes/rad_data/20250921_barcode_4_results/rnabloom.log`. These are adjacent dataset records, not evidence of the exact version used for Figure 8. IgBLAST, SHazaM, SCOPeR, pheatmap, and Figure-8-specific RNA-Bloom versions remain unresolved.

## Preserved IgH coverage results: candidate Figure 8A provenance

Preserved completed coverage analyses exist for NBC and RAGE-Seq:

- `/Volumes/rad_data/igh_pileups/nbc_twopass/pass1.log`
- `/Volumes/rad_data/igh_pileups/nbc_twopass/pass2.log`
- `/Volumes/rad_data/igh_pileups/logs/nbc_twopass.log`
- `/Volumes/rad_data/igh_pileups/nbc_twopass/nbc_igh_pileup.twopass.csv.gz`
- `/Volumes/rad_data/igh_pileups/rage_twopass/pass1.log`
- `/Volumes/rad_data/igh_pileups/logs/rage_twopass.log`
- `/Volumes/rad_data/igh_pileups/rage_twopass/rage_igh_pileup.twopass.csv.gz`
- `/Volumes/rad_data/igh_pileups/annotate_depth.py`

NBC pass 1 used minimap2 2.30-r1287 with `-x map-ont --secondary=no` against T2T chromosome 14 (101,161,492 bases), from the RNA-Bloom corrected long-read FASTA. It selected 3,036,293 IGH read names from approximately 5.95 million reads. Pass 2 used the 1,315,668-base IGH locus and `-ax splice -g 5k -G 200k -O 4,8 -E 2,1 --splice-flank=no -C 5 --secondary=no`; the BAM contained 3,130,753 mapped records, including 111,773 supplementary records. These are alignment-record counts, not unique molecules.

RAGE-Seq pass 1 used minimap2 2.30-r1287 with `-x map-ont --secondary=no`, the same chromosome 14 reference, and `/Volumes/rad_data/20250514_RAGE_out/RAGE.fq.gz` (4,654,964 input reads). The log reports 446,623 IGH read names and a 450,958-read subset, followed by eight splice-alignment shards. The final BAM had 445,914 records including 8,809 supplementary records.

`annotate_depth.py` reads `samtools depth -a` output and a `seg_to_locus.tsv` annotation. It emits locus position, depth, and annotation; the default locus length is 1,315,668. It retains V, C, CMem, I, S, and pseudogene features; the remainder is intergenic. Overlap priority from low to high is V < pseudogene < CMem < S < I < C. Feature starts are converted from zero-based to one-based coordinates. The annotation input was not recovered in this folder. The reference symlink `/Volumes/rad_data/igh_pileups/ref/igh_locus_t2t.fasta` is broken and points to the external PostRot genomes directory.

These results are plausible Figure 8A candidates but there is no identified plot script tying them to the supplied image. The completed NBC command uses `-C 5`, whereas the manuscript states `-C0`; a source/run match is needed before changing that flag. Neither the RAGE count nor the filename establishes that Ramos-specific barcodes were selected for the displayed Ramos panel.

The tonsil log `/Volumes/rad_data/igh_pileups/logs/tonsil.mm2.log` records a killed splice-alignment command, and `tonsil_verify.log` contains only a small verification run without a completed command record. The tiny BAM files in `igh_pileups/bams/` are not completed Figure 8 evidence. No complete tonsil pileup matched to Figure 8A was found.

## Questions required to make this section reproducible

1. Where is the original R script or saved analysis object that generated 10,744 clones, 620 multi-isotype clones, and clones 2277/7445/5725? The strongest upstream lead is the `swedish_tonsil_spatial` project path above. Please identify the actual final source and the exact section(s) used.
2. What SHazaM distance model, sequence field (nucleotide junction/CDR3 versus amino acid), normalization, numerical threshold, threshold-selection method, and SCOPeR linkage/grouping settings were used? Were junction lengths grouped? How were ambiguous V/J calls treated?
3. What were the eligibility and support filters (productive, complete VDJ, locus IGH, minimum length/quality, minimum read/UMI count, minimum support per isotype)? Were counts reads, RNA-Bloom-corrected reads, consensus transcripts, or unique barcode–UMI molecules? Were duplicate libraries combined before or after molecule counting?
4. What exact alignment or annotation rule classified a read/clone/spot as membrane anchored, secreted, or unannotated? What constitutes sufficient membrane exon evidence, what supports a secreted terminal exon, and how are truncated reads or contradictory assignments handled? No rule can safely be inferred from absence of a membrane exon alone.
5. Which input FASTA/FASTQ, RNA-Bloom output, IgBLAST result, reference release, and software versions fed the clone analysis? Was RNA-Bloom used only for read correction or for assembly, and was correction global or grouped? Is the stated IgBLAST E-value 1e-4 correct for the final run?
6. Which reference sequence, `seg_to_locus.tsv`, alignments, and depth table generated each Figure 8A track? Was the completed `-C 5` two-pass output used, or a separate `-C0` run? How were secondary/supplementary records and overlap/deduplication handled in depth? Were Ramos barcodes selected from RAGE-Seq?
7. Do the 620 clones include IGHM/IGHD-only clones? The source operational rule is >1 constant gene. That label alone does not establish DNA class-switch recombination; IgM/IgD alternative processing and mixture/support rules need explicit handling. Did each class-switching clone require a switched isotype (IGHG/IGHA/IGHE), and how were order/arrows inferred for panels D/E?
8. Does the final count bin mean 11 or more, or greater than 11? Figure 8B labels `1`, `2–5`, `6–10`, `>11`, leaving 11 unassigned if read literally.

## Conservative prose skeleton for integration after answers

RAD-demultiplexed reads from the published RAGE-Seq cell-line dataset, the Nojima B-cell culture, and the Engblom tonsil spatial receptor dataset were used to examine IGH constant-region usage. The tonsil data were generated with conventional Visium and PacBio CCS sequencing. [Specify the libraries and sections included in each analysis.] Reads were processed with RNA-Bloom [version and correction/assembly settings] and annotated with IgBLAST [version and IMGT release]. [Specify eligibility filters and the unit of counting.]

Clonal groups were defined from IGH junction sequences with SHazaM and SCOPeR. [Specify the distance model, normalization, threshold, V/J and junction-length grouping, and clustering settings.] Constant-gene assignments were tabulated within each clonal group. Multi-isotype clones were defined as [exact support rule and treatment of IgM/IgD]. Clone abundance was summarized as [reads/molecules/spots], and isotype composition was displayed for the selected clones.

For spatial analysis, receptor annotations were joined to Visium spots by barcode and plotted at the tissue coordinates. Previously assigned microenvironment labels were used for the tissue map. [Specify the source label file, section, transformation, and filtering.] Membrane-associated, secreted, and unannotated transcripts were classified by [explicit evidence rule], then summarized within each spot and clone. [State how contradictory or insufficient evidence was retained.] Coverage across the IGH locus was computed from [exact alignment source and depth parameters] and annotated with the reference feature intervals.

The bracketed items are unresolved evidence gaps, not proposed defaults.
