# Data guide

The [figure guides](../README.md) follow each analysis from its input records to
its plotted values. The files below provide the source data, examples and
identifiers used in those steps.

| Location | Contents |
|---|---|
| [`examples/`](examples/) | Selected source records, extraction rules, hashes and expected outputs |
| [`../source_data/`](../source_data/) | Complete plotting and metric tables with schemas |
| [`../manifests/datasets.tsv`](../manifests/datasets.tsv) | Dataset IDs, families and accessions |
| `../manifests/data_files.tsv` (generated locally) | Columns, row counts, file sizes and SHA-256 hashes |
| `../checkpoints/` | Large read ledgers, sparse matrices and reference files restored from the checkpoint archives |

## File formats and identifiers

**FASTQ.** Each record contains an identifier, nucleotide sequence, separator and
quality string. A physical read can yield several emitted segments. The example
schemas identify the counting unit and the relationship between original-read
and segment identifiers.

**Assignment tables.** These tables link the original read ID to the selected
barcode and, when available, the extracted barcode sequence. Diagnostic
Flexiplex output stores `CellBarcode` and `RawCellBarcode` in separate columns.
Figure 3's off-list challenge counts physical reads with exactly one assignment
row. Its correction analysis counts unique original-read–target-barcode pairs;
category flags can overlap for a pair. The [Figure 3 guide](../docs/figure_03.md)
defines both counting procedures and their denominators.

**Matrix Market / MEX.** A sparse matrix is accompanied by feature and barcode
files. Its one-based row and column indexes refer to these files. Figure 7 uses
each nucleus's complete library total for normalization before filtering genes.

**VCF and CellSNP.** Variant and cell order link the genotype inputs and outputs.
The selected Figure 6 VCF retains identical duplicate records; its schema
reports both record counts and unique variant keys.

**Plot tables.** Input, barcode and gene keys identify observations. Local
schemas define numerators, denominators, transformations and missing values.
Zero represents an observed zero; empty or null fields represent missing or
undefined values. The file inventory's `header_present` field identifies tables
without headers, including barcode lists and `samtools idxstats` output. The
inventory supplies descriptive column names for those files.

## Dataset sources

The [dataset registry](../manifests/datasets.tsv) identifies the 37 Figure 4
inputs, Visium HD and LR-Split-seq. Each entry gives the dataset family and
acquisition accessions. Figure-specific manifests record references, file hashes and processing
commands. ScMixology2 uses the reconstructed input described in the Figure 4
guide.

The eight Engblom/Swedish Visium libraries are available through controlled EGA
access: dataset `EGAD00001011062`, study `EGAS00001007337`, and data-access
committee `EGAC00001003294`. Their aggregate benchmark metrics and acquisition
identifiers are included here; raw reads are obtained through EGA.

The [data-package guide](../docs/release_review.md) describes the checkpoint
archives used to resume analyses from saved intermediate data.
