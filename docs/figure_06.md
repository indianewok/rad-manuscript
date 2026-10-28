# Figure 6 — genotype recovery in LongBench single nuclei

Figure 6 measures recovery of cell-line identity from the LongBench single-nucleus ONT library. The mixture contains eight cell lines: H146, H1975, H211, H2228, H526, H69, HCC827 and SHP77. Each workflow's native demultiplexed reads are aligned and genotyped against a common bulk-Illumina panel. The resulting calls are compared with the matched single-nucleus Illumina reference and displayed on its fixed UMAP coordinates.

![Figure 6](../figures/figure_06/prism/figure_06.png)

## Software and parameters

| Stage | Software and settings | Code and run record |
|---|---|---|
| RAD demultiplexing | RAD 1.0.2, commit `920addacdbf40b815e13a146226e8f4b14a58aaf`; 10x 3v3.1, offensive correction, generated/whitelist edit distance 2, chunk size 5,000, 32 threads; 12,423 selected barcodes | [Metadata](../source_data/figure_06/provenance/RAD_run_metadata.txt), [command](../source_data/figure_06/provenance/RAD_demux_command.txt) |
| BLAZE demultiplexing | BLAZE 2.5.0; `--force-cells 10000 --threads 48 --minimal_stdout`, 3v3 default; 10,001 selected barcodes; `PYTHONHASHSEED=UNSET` | [Metadata](../source_data/figure_06/provenance/BLAZE_run_metadata.txt), [command](../source_data/figure_06/provenance/BLAZE_demux_command.txt) |
| Flexiplex demultiplexing | Flexiplex 1.02.6 audit build `d84c8ae4f3865052f2b5ecec816949b94682f302`; `-d 10x3v3 -f 8 -e 2 -k SELECTED -p 16`; 12,101 selected barcodes | [Execution metadata](../source_data/figure_06/provenance/Flexiplex_run_metadata.txt) |
| Native alignment | FLAMES 2.0.1, minimap2 2.28-r1209, samtools 1.21; GENCODE v44; `-ax splice -y -t 32 -k14 --secondary=no --seed 2023 --junc-bed … --junc-bonus 1` | [FLAMES pipeline call](https://github.com/mritchielab/FLAMES/blob/4b6058f58c5b19365919990b3f2c1053f2035b01/R/sc_long_pipeline.R#L237-L245), [alignment implementation](https://github.com/mritchielab/FLAMES/blob/4b6058f58c5b19365919990b3f2c1053f2035b01/R/minimap2_align.R#L42-L104); BAM headers: [RAD](../source_data/figure_06/RAD_alignment_header.sam), [BLAZE](../source_data/figure_06/BLAZE_alignment_header.sam), [Flexiplex](../source_data/figure_06/Flexiplex_alignment_header.sam) |
| Allele counting | CellSNP-lite 1.2.3; `--cellTAG CB --UMItag UB --minMAF 0.1 --minCOUNT 10 --gzip --genotype`; 32 threads for RAD/Flexiplex and 16 for BLAZE | [LongBench counting rule](https://github.com/youyupei/LongBench_workflow/blob/37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/rules/sc_cell_line_anno.smk#L38-L62), [executed commands](../source_data/figure_06/executed_cellsnp_commands.tsv) |
| Genotype assignment | Vireo 0.5.8; `-t GT --callAmbientRNAs -p 16` | [LongBench Vireo rule](https://github.com/youyupei/LongBench_workflow/blob/37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/rules/sc_cell_line_anno.smk#L65-L88), [executed commands](../source_data/figure_06/executed_vireo_commands.tsv) |
| Illumina embedding | Seurat 5.4.0; SCTransform v2 with glmGamPoi; 50 PCs; neighbors on PCs 1–30; Louvain algorithm 1, resolution 0.5; UMAP on PCs 1–30, 30 neighbors, minimum distance 0.3, cosine distance, seed 20260805, one thread | [Stored object commands](../source_data/figure_06/umap_object_commands.txt) |

These are the native-alignment runs used for genotype analysis. The expression analysis in [Figure 7](figure_07.md) uses RAD `4acbe00` and a common raw-read gene-assignment workflow.

The bulk reference follows the LongBench [genome-index construction](https://github.com/youyupei/LongBench_workflow/blob/37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/sub_workflows/sr_bulk/scripts/build_index.R#L8-L14), [bulk alignment](https://github.com/youyupei/LongBench_workflow/blob/37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/sub_workflows/sr_bulk/scripts/align_reads.R#L17-L30) and [donor-genotyping protocol](https://github.com/youyupei/LongBench_workflow/blob/37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/rules/sc_cell_line_anno.smk#L8-L35).

## From alignments to genotype calls

Native FASTQ records carry cell-barcode (`CB`) and UMI (`UB`) tags. CellSNP produces variant-by-cell matrices for alternate-allele molecules (`AD`) and total-depth molecules (`DP`), together with ordered variant and barcode lists. A missing sparse matrix entry represents zero counted molecules.

The fixed donor VCF contains 360,814 records and 360,809 unique chromosome/position/reference/alternate keys. Its five identical duplicate records are retained in the executed reference, preserving matrix row identity. The VCF SHA-256 is `586b1dd8d8c9fb5df5f12ccf111a5c9fa1c9cdd0019ef3fa70bf97a79f342940`. [Duplicate identities](../source_data/figure_06/donor_panel_duplicate_records.tsv) and [panel validation](../source_data/figure_06/donor_panel_validation.tsv) document the reference. Reconstructed Illumina genotypes match all 12,012 released hard calls.

| Tool | Variant rows | Selected barcodes |
|---|---:|---:|
| RAD | 115,810 | 12,423 |
| BLAZE | 118,378 | 10,001 |
| Flexiplex | 129,712 | 12,101 |

The [matrix summary](../source_data/figure_06/cellsnp_matrix_summary.tsv) gives the matrix dimensions and counts. The donor VCF, index and matrices are stored under `checkpoints/figure_06/`.

The [data preview](../data/examples/figure_06/PREVIEW.md) follows individual allele counts through genotype assignment and UMAP placement. For example, chr1:14464 A/T has one alternate-allele molecule in barcode `AAAGTGACAAACGGCA`. Both query and reference assign that nucleus to H69, at fixed coordinates `(3.4304353354217, 5.11612037766271)`. The [joined records](../data/examples/figure_06/allele_to_genotype.tsv), [extraction receipt](../data/examples/figure_06/allele_extraction.json) and [extraction script](../scripts/figure_06/extract_allele_examples.py) retain each matrix row and cell column.

## Classify cell-line recovery

All joins use the exact `cell_barcode`. For each reference nucleus, the comparison records reference membership, reference genotype, tool selection and query genotype. Named singlets are classified as the same or a different cell line; doublets, unassigned genotypes, absent genotype rows and unselected barcodes have separate states.

| Field group | Meaning |
|---|---|
| `illumina_reference_present/state/label` | Reference membership, genotype state and cell-line label |
| `rad`, `blaze_panel_matched`, `flexiplex` + `_query_selected` | Whether the workflow selected the barcode |
| Same prefixes + `_vireo_state/_vireo_label` | Query genotype state and cell-line label |
| `strict_identity_eligible`, `outcome` | Reference named-singlet membership and classified outcome |

Run the classifier on the [five-cell example](../data/examples/figure_06/genotype_input.csv):

```bash
mkdir -p results
python3 scripts/figure_06/classify_genotypes.py \
  --input data/examples/figure_06/genotype_input.csv \
  --output results/figure06_outcomes.tsv
python3 scripts/figure_06/summarize_identity.py \
  --input results/figure06_outcomes.tsv \
  --output results/figure06_summary.tsv --expected-reference-singlets 5
```

The result contains 15 rows, matching the [expected outcomes](../data/examples/figure_06/genotype_outcomes.tsv). This example includes one RAD cell for each outcome. For the complete source CSV, use the same classifier with `--expected-reference-singlets 5782`.

The reference contains 12,012 nuclei: 5,782 named singlets, 59 doublets and 6,171 unassigned nuclei. **Strict identity recall** is the number of correctly recovered named singlets divided by all 5,782 reference named singlets. **Conditional concordance** is the number of matching named calls divided by matching plus different named calls.

| Tool | Same | Different | Doublet | Unassigned | Not selected | Strict recall |
|---|---:|---:|---:|---:|---:|---:|
| RAD | 5,324 | 32 | 246 | 165 | 15 | 5,324 / 5,782 |
| BLAZE | 4,450 | 12 | 766 | 308 | 246 | 4,450 / 5,782 |
| Flexiplex | 4,674 | 17 | 725 | 340 | 26 | 4,674 / 5,782 |

The [per-cell outcomes](../source_data/figure_06/per_cell_genotype.tsv) retain every reference nucleus. The [union table](../source_data/figure_06/union_per_cell_genotype.tsv) additionally includes tool-selected nuclei outside the reference. Panel C uses all selected named genotypes: 9,404 for RAD, 6,478 for BLAZE and 7,125 for Flexiplex, separated by cell line in the [donor-count table](../source_data/figure_06/selected_nuclei_by_donor.tsv).

## Display on the Illumina reference embedding

Join the genotype outcomes to the [fixed coordinates](../source_data/figure_06/fixed_coordinates.tsv) by barcode to obtain the [overlay table](../source_data/figure_06/genotype_overlay.tsv). The exported coordinates and all 12,012 barcodes match the saved SCTransform Seurat object within 1e-12. Every tool is displayed on this common embedding.

The source-table plotting command is:

```bash
python3 scripts/figure_06/render_source_proofs.py
```

It uses matplotlib and numpy and reads the portable Figure 6 tables.

## Statistical records

The figure specifies ANOVA with Dunnett comparisons. Reproducing those annotations requires the executed analysis settings linked to the current Panel C counts. The retained candidate Prism analysis uses a different count table. Cell-line strata come from a single mixed library.
