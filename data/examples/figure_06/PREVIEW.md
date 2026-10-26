# Figure 6 — source-data examples

The tables below show selected allele counts, cell-line genotypes and fixed UMAP coordinates from LongBench single nuclei. [Extraction details](extraction.json) record source paths, hashes and selected rows. The [Figure 6 guide](../../../docs/figure_06.md) gives the complete analysis.

## Allele counts, genotype calls and UMAP coordinates

The first eight alternate-allele molecule counts (AD) are resolved by one-based matrix row and column, then joined to genotype calls and UMAP coordinates by barcode. [Extraction details](allele_extraction.json) retain the hashes and selection rules.

| source_AD_entry | CHROM | POS | REF | ALT | cell_barcode | alternate_allele_molecules | query_label | reference_label | UMAP_1 | UMAP_2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 14464 | A | T | AAAGTGACAAACGGCA | 1 | H69 | H69 | 3.4304353354217 | 5.11612037766271 |
| 2 | 1 | 14464 | A | T | AACCACATCAGGACGA | 1 | H2228 | H2228 | -10.8863836171387 | 1.58853928196721 |
| 3 | 1 | 14464 | A | T | AATCGACCATCGAAGG | 1 | H1975 | unassigned | -2.67525347492681 | -3.01360507857509 |
| 4 | 1 | 14464 | A | T | ACAGAAAAGCTCGAAG | 1 | H1975 | H1975 | -2.86928924343572 | -4.06138201605983 |
| 5 | 1 | 14464 | A | T | ACAGGGACAGACCAAG | 1 | H1975 | H1975 | 0.246125986957687 | -0.953269084808303 |
| 6 | 1 | 14464 | A | T | ACATCGAAGCGGGTAT | 1 | HCC827 | HCC827 | -1.58097120544897 | 6.51777080643468 |
| 7 | 1 | 14464 | A | T | ACGGAAGTCTGGGCGT | 1 | HCC827 | HCC827 | -1.85452970287786 | 6.16738371002965 |
| 8 | 1 | 14464 | A | T | AGAGAGCTCGGCGATC | 1 | H2228 | unassigned | -9.68027170917974 | 3.53467945206456 |

## Five genotype outcomes

| cell_barcode | illumina_reference_label | rad_query_selected | rad_vireo_state | rad_vireo_label |
|---|---|---|---|---|
| AAACCCACATCCGAGC | H2228 | TRUE | named_singlet | H2228 |
| AAAGGGCTCGAACGCC | H2228 | TRUE | unassigned | unassigned |
| AAAGGTAAGAGGCGGA | SHP77 | TRUE | doublet | doublet |
| AAAGGTAAGTGTGTTC | SHP77 | TRUE | named_singlet | H69 |
| AATTCCTGTAACGGTG | H1975 | FALSE | NA | NA |

## Classifier output (all three tools, five cells)

| cell_barcode | tool | selected | reference_label | query_label | outcome |
|---|---|---|---|---|---|
| AAACCCACATCCGAGC | RAD | 1 | H2228 | H2228 | same |
| AAACCCACATCCGAGC | BLAZE | 1 | H2228 | H2228 | same |
| AAACCCACATCCGAGC | Flexiplex | 1 | H2228 | H2228 | same |
| AAAGGGCTCGAACGCC | RAD | 1 | H2228 | unassigned | unassigned |
| AAAGGGCTCGAACGCC | BLAZE | 0 | H2228 | NA | not_selected |
| AAAGGGCTCGAACGCC | Flexiplex | 1 | H2228 | unassigned | unassigned |
| AAAGGTAAGAGGCGGA | RAD | 1 | SHP77 | doublet | doublet |
| AAAGGTAAGAGGCGGA | BLAZE | 1 | SHP77 | doublet | doublet |
| AAAGGTAAGAGGCGGA | Flexiplex | 1 | SHP77 | unassigned | unassigned |
| AAAGGTAAGTGTGTTC | RAD | 1 | SHP77 | H69 | different |
| AAAGGTAAGTGTGTTC | BLAZE | 1 | SHP77 | H69 | different |
| AAAGGTAAGTGTGTTC | Flexiplex | 1 | SHP77 | H69 | different |
| AATTCCTGTAACGGTG | RAD | 0 | H1975 | NA | not_selected |
| AATTCCTGTAACGGTG | BLAZE | 0 | H1975 | NA | not_selected |
| AATTCCTGTAACGGTG | Flexiplex | 0 | H1975 | NA | not_selected |

## Summary of the five-cell example

| tool | reference_denominator | same | different | doublet | unassigned | not_selected | strict_recall |
|---|---|---|---|---|---|---|---|
| BLAZE | 5 | 1 | 1 | 1 | 0 | 2 | 0.2 |
| Flexiplex | 5 | 1 | 1 | 0 | 2 | 1 | 0.2 |
| RAD | 5 | 1 | 1 | 1 | 1 | 1 | 0.2 |
