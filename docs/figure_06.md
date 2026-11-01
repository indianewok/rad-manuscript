# Figure 6 Cell-line identity in LongBench single nuclei

Figure 6 measures recovery of cell-line identities after demultiplexing the LongBench single-nucleus ONT library. The mixture contains H146, H1975, H211, H2228, H526, H69, HCC827 and SHP77. Genotype assignments are compared with the matched single-nucleus Illumina reference and displayed on the same Illumina UMAP. The source tables identify the genotype stream and barcode population used for each panel.

![Figure 6](../figures/figure_06/prism/figure_06.png)

## Figure legend

Figure 6. Improved single nuclei data depth and cell line annotation. A. Uniform Manifold Approximation and Projection (UMAP) plot of LongBench single nuclei dataset depicting short-read unassigned (orange), and short read annotated (other colors) nuclei per cell line. B. Performance of each tool in identifying short read-annotated (left) and short read-un-annotated (center) nuclei, with quantification of each cell line or failure mode (right). C. Total number of nuclei identified by each tool per cell line. Statistical significance was assessed by one-way repeated-measures ANOVA, matched by cell line, with Geisser–Greenhouse correction and Dunnett comparisons against RAD.

## Demultiplexing and genome alignment

| Stage | Software and parameters | Command or source |
|---|---|---|
| RAD demultiplexing | RAD 1.0.2, commit `920addacdbf40b815e13a146226e8f4b14a58aaf`; 10x 3v3.1 layout, offensive correction, generated and whitelist edit distances two, chunk size 5,000, 32 threads | [Metadata](../source_data/figure_06/provenance/RAD_run_metadata.txt), [command](../source_data/figure_06/provenance/RAD_demux_command.txt) |
| BLAZE demultiplexing | BLAZE 2.5.0; `--force-cells 10000 --threads 48 --minimal_stdout`, 3v3 default | [Metadata](../source_data/figure_06/provenance/BLAZE_run_metadata.txt), [command](../source_data/figure_06/provenance/BLAZE_demux_command.txt) |
| Flexiplex demultiplexing | Flexiplex 1.02.6; `-d 10x3v3 -f 8 -e 2 -k SELECTED -p 16` | [Execution metadata](../source_data/figure_06/provenance/Flexiplex_run_metadata.txt) |
| Genome alignment | FLAMES 2.0.1, minimap2 2.28-r1209, samtools 1.21; GENCODE v44; `-ax splice -y -t 32 -k14 --secondary=no --seed 2023 --junc-bed … --junc-bonus 1` | [Executed configuration](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_06/provenance/flames_alignment_snapshot/upstream/LongBench_workflow_37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/sub_workflows/lr_sc_sn/config/flames_genome_map.json), [alignment implementation](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_06/provenance/flames_alignment_snapshot/upstream/FLAMES_4b6058f58c5b19365919990b3f2c1053f2035b01/R/minimap2_align.R#L42-L104) |
| Allele counting | [CellSNP-lite](https://doi.org/10.1093/bioinformatics/btab358) 1.2.3; `--cellTAG CB --UMItag UB --minMAF 0.1 --minCOUNT 10 --gzip --genotype`; 32 threads for RAD/Flexiplex and 16 for BLAZE | [Executed commands](../source_data/figure_06/executed_cellsnp_commands.tsv) |
| Genotype assignment | [Vireo](https://doi.org/10.1186/s13059-019-1865-2) 0.5.8; `-t GT --callAmbientRNAs -p 16` | [Executed commands](../source_data/figure_06/executed_vireo_commands.tsv) |

The exact FLAMES configuration and the source that interprets it are preserved in the [versioned configuration archive](pinned_flames_configs.md). The supplied `flames_genome_map.json` enables genome alignment, uses seed 2023 and 32 threads, and disables FLAMES demultiplexing and downstream quantification. Corrected cell barcodes and UMIs are carried into the alignments as `CB` and `UB` tags. The [RAD](../source_data/figure_06/RAD_alignment_header.sam), [BLAZE](../source_data/figure_06/BLAZE_alignment_header.sam) and [Flexiplex](../source_data/figure_06/Flexiplex_alignment_header.sam) BAM headers record the alignment programs and flags.

## Reference genotype panel and allele counts

Separate bulk-Illumina libraries from the eight cell lines supply the reference genotypes. Reads are processed with [fastp](https://doi.org/10.1093/bioinformatics/bty560) 0.23.4 using 16 threads and aligned uniquely to the GENCODE v44 primary assembly with [Rsubread](https://doi.org/10.1093/nar/gkz114) 2.20.0 [subjunc](https://doi.org/10.1093/nar/gkt214). Alignment uses the GTF annotation, `reportAllJunctions=TRUE`, `useAnnotation=TRUE`, `unique=TRUE` and 16 threads. Processing follows the LongBench [genome-index construction](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_06/provenance/flames_alignment_snapshot/upstream/LongBench_workflow_37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/sub_workflows/sr_bulk/scripts/build_index.R#L8-L14), [bulk alignment](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_06/provenance/flames_alignment_snapshot/upstream/LongBench_workflow_37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/sub_workflows/sr_bulk/scripts/align_reads.R#L17-L30) and [donor-genotyping rules](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_06/provenance/flames_alignment_snapshot/upstream/LongBench_workflow_37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/rules/sc_cell_line_anno.smk#L8-L35).

Candidate SNPs come from the [1000 Genomes phase-3](https://doi.org/10.1038/nature15393) hg38 panel with population allele frequency greater than 5%. CellSNP-lite calls bulk genotypes with `--cellTAG None --UMItag None --gzip --genotype`. The fixed panel is validated by applying it to the released Illumina single-nucleus allele matrices and comparing the resulting Vireo calls with the published assignments. The [bulk-panel runtime manifest](../source_data/figure_06/bulk_panel_runtime_manifest.tsv) records the versions, commands, references and input checksums.

The fixed donor VCF contains 360,814 records and 360,809 unique chromosome/position/reference/alternate keys. Five identical duplicate records are retained to preserve the executed panel and matrix row identities. Its SHA-256 is `586b1dd8d8c9fb5df5f12ccf111a5c9fa1c9cdd0019ef3fa70bf97a79f342940`. The [duplicate-record table](../source_data/figure_06/donor_panel_duplicate_records.tsv) and [panel validation](../source_data/figure_06/donor_panel_validation.tsv) identify those records and the comparison with released Illumina classifications.

CellSNP-lite counts alternate-allele molecules (`AD`) and total-depth molecules (`DP`) for each variant and selected barcode. Ordered variant and barcode files define matrix rows and columns; absent sparse entries have count zero. Vireo uses the common reference genotype calls and ambient-RNA estimation to classify each nucleus as a named cell-line singlet, doublet or unassigned nucleus.

| Workflow | Variant rows | Selected barcodes |
|---|---:|---:|
| RAD | 115,810 | 12,423 |
| BLAZE | 118,378 | 10,001 |
| Flexiplex | 129,712 | 12,101 |

The donor VCF, index and allele matrices are stored under `checkpoints/figure_06/`. The [matrix summary](../source_data/figure_06/cellsnp_matrix_summary.tsv) records their dimensions. The [allele-to-genotype example](../data/examples/figure_06/allele_to_genotype.tsv) follows individual matrix entries through Vireo assignment and UMAP placement; its [extraction record](../data/examples/figure_06/allele_extraction.json) and [script](../scripts/figure_06/extract_allele_examples.py) identify the source rows and columns.

## Classify recovery against the Illumina reference

Genotype calls are joined by exact `cell_barcode`. Each reference barcode records its Illumina state, tool selection status and long-read genotype. Reference singlets are classified as assigned to the same cell line, assigned to a different cell line, doublet, unassigned or not selected. A reference barcode absent from a tool’s selected whitelist is counted as not selected. Selected barcodes without a genotype row are recorded separately.

**Strict identity recall** divides matching named-singlet assignments by all reference named singlets. Different-line calls, doublets, unassigned calls and unselected barcodes remain in that denominator. **Conditional concordance** divides matching named calls by matching plus different named calls. The [per-cell outcomes](../source_data/figure_06/per_cell_genotype.tsv) retain the reference population; the [union table](../source_data/figure_06/union_per_cell_genotype.tsv) also retains tool-selected barcodes outside that population.

Run the classifier on the five-cell example:

```bash
mkdir -p results
python3 scripts/figure_06/classify_genotypes.py \
  --input data/examples/figure_06/genotype_input.csv \
  --output results/figure06_outcomes.tsv
python3 scripts/figure_06/summarize_identity.py \
  --input results/figure06_outcomes.tsv \
  --output results/figure06_summary.tsv --expected-reference-singlets 5
```

The [expected example outcomes](../data/examples/figure_06/genotype_outcomes.tsv) cover the comparison states. For the complete input, use `--expected-reference-singlets 5782`. The [summary](../source_data/figure_06/genotype_summary.tsv) reports recovery across the complete reference.

Panel C counts selected named singlets among barcodes present in the Illumina reference. Its [plotted count table](../source_data/figure_06/plotted_panel_c_counts.tsv) is regenerated from the [per-barcode genotype checkpoint](../source_data/figure_06/plotted_genotype_calls.tsv.gz). RAD and Flexiplex calls in this checkpoint use the reconstructed bulk panel; BLAZE uses the published ONT-SN genotype calls. Panel B uses the panel-matched BLAZE annotations recorded in the per-cell outcome table. The [panel C provenance record](../source_data/figure_06/plotted_panel_c_provenance.json) identifies these inputs.

Recount the plotted cell-line groups with:

```bash
python3 scripts/figure_06/reproduce_panel_c_counts.py
```

The [validation record](../source_data/figure_06/plotted_panel_c_validation.json) checks all 24 counts against the saved Prism graph and records the comparison with the panel-matched annotation stream. The separate [all-selected count table](../source_data/figure_06/selected_nuclei_by_donor.tsv) includes named genotypes outside the Illumina reference and supplies the broader cell cohort used in the [Figure 7](figure_07.md) expression workflow.

## Shared Illumina embedding

The UMAP coordinates come from the released Illumina single-nucleus matrix processed with [Seurat v5](https://doi.org/10.1038/s41587-023-01767-y) 5.4.0, SCTransform v2 and glmGamPoi. PCA uses 50 components. Neighbors use PCs 1–30, and Louvain clustering uses algorithm one with resolution 0.5. [UMAP](https://doi.org/10.48550/arXiv.1802.03426) uses PCs 1–30, 30 neighbors, minimum distance 0.3, cosine distance, seed 20260805 and one thread. The [stored object commands](../source_data/figure_06/umap_object_commands.txt) record these settings.

All 12,012 filtered Illumina barcodes retain their common coordinates. Joining [genotype outcomes](../source_data/figure_06/per_cell_genotype.tsv) to the [fixed coordinates](../source_data/figure_06/fixed_coordinates.tsv) gives the [overlay table](../source_data/figure_06/genotype_overlay.tsv). This shared embedding displays the effects of tool-specific genotype assignment on the same nuclei.

Regenerate source-table plots with:

```bash
python3 scripts/figure_06/render_source_proofs.py
```

The plotting script uses matplotlib and numpy and reads the portable Figure 6 tables.

## Statistical comparison

The plotted named-singlet counts are compared across tools with a one-way repeated-measures ANOVA. The eight cell lines form matched rows, and RAD, BLAZE and Flexiplex form the three columns; doublet, unassigned and not-detected rows are excluded. The analysis does not assume sphericity and applies the Geisser–Greenhouse correction. Dunnett’s multiple-comparison procedure compares BLAZE and Flexiplex with RAD. The [analysis specification](../source_data/figure_06/analysis_specification.json) records the matching structure and comparisons, and the [saved Prism results](../source_data/figure_06/plotted_panel_c_statistics.json) retain the numerical output. These comparisons describe recovery across the eight cell-line groups in the LongBench mixture.
