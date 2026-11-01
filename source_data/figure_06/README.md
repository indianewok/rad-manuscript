# Figure 6 — cell-line assignments

Follow **demultiplexed reads → genome alignments → allele counts → Vireo calls → Illumina comparison** in the [Figure 6 guide](../../docs/figure_06.md). Its [software table](../../docs/figure_06.md#software-and-commands) gives the versions and flags. The [worked examples](../../data/examples/figure_06/PREVIEW.md) show individual allele counts, genotype calls and UMAP coordinates.

## Find the plotted data

| File | Rows and measurements |
|---|---|
| [per_cell_genotype.tsv](per_cell_genotype.tsv) | Barcode × tool: Illumina state, long-read selection and genotype, and recovery outcome |
| [genotype_summary.tsv](genotype_summary.tsv) | Outcome counts, strict identity recall and conditional concordance for each tool |
| [fixed_coordinates.tsv](fixed_coordinates.tsv) | Shared Illumina UMAP coordinates for 12,012 filtered barcodes |
| [genotype_overlay.tsv](genotype_overlay.tsv) | Genotype outcomes joined to those coordinates by barcode |
| [plotted_panel_c_counts.tsv](plotted_panel_c_counts.tsv) | Panel C's 24 counts: eight cell lines × three tools |
| [plotted_genotype_calls.tsv.gz](plotted_genotype_calls.tsv.gz) | Barcode-level genotype calls used to calculate panel C |
| [plotted_panel_c_statistics.json](plotted_panel_c_statistics.json) | Repeated-measures ANOVA, Geisser–Greenhouse correction and Dunnett comparisons against RAD |

**Strict identity recall** is matching named-singlet calls divided by all **5,782 Illumina-reference named singlets**. **Conditional concordance** is matching named calls divided by matching plus different named calls. A barcode absent from a tool's selected list contributes to `not_selected`.

Panel C counts selected named singlets among Illumina-reference barcodes. RAD and Flexiplex use the bulk-panel genotypes; BLAZE uses the published ONT-SN genotypes. The panel B comparison uses the BLAZE calls in `per_cell_genotype.tsv`. The [panel input record](plotted_panel_c_provenance.json) identifies the annotation sources.

The [union table](union_per_cell_genotype.tsv) includes selected barcodes outside the Illumina reference. The [all-selected cell-line counts](selected_nuclei_by_donor.tsv) describe that broader population; Figure 7 selects positive-expression-depth H146/H526 singlets from it.

## Follow the processing inputs

| Files | Purpose |
|---|---|
| [Demultiplexing metadata](provenance/) | RAD, BLAZE and Flexiplex commands and software identities |
| [FLAMES alignment configuration](provenance/flames_alignment_snapshot/) | Configuration, source implementation and execution records |
| [CellSNP commands](executed_cellsnp_commands.tsv) and [Vireo commands](executed_vireo_commands.tsv) | Allele counting and genotype assignment |
| [Bulk-panel manifest](bulk_panel_runtime_manifest.tsv) and [panel validation](donor_panel_validation.tsv) | Eight-cell-line genotype reference and its Illumina comparison |
| [Matrix summary](cellsnp_matrix_summary.tsv) | Variant and selected-barcode dimensions of the AD and DP matrices |

The complete VCF and allele matrices are under `checkpoints/figure_06/`. To recount panel C:

```bash
python3 scripts/figure_06/reproduce_panel_c_counts.py
```
