# Figure 7 source-data examples

The tables below show selected RAD assignments, molecule counts and differential-expression results from LongBench single nuclei. [Extraction details](extraction.json) record source paths, hashes and selected rows. The [Figure 7 guide](../../../docs/figure_07.md) gives the complete analysis.

## Emitted RAD assignments

These are the first ten rows of the RAD assignment checkpoint. The complete ledger contains 57,885,606 assignments across all 12,423 selected cells. The extractor normalizes orientation and `-CT` suffixes to retain original read IDs alongside barcodes, UMIs and correction flags. [Extraction details](assignment_extraction.json) record source hashes and row selection.

| source_data_row | original_read_id | cell_barcode | UMI | raw_barcode | corrected_flag |
|---|---|---|---|---|---|
| 1 | 5bab4385-5eb7-4f92-870f-a95e9b102bb7 | TGAACGTAGTTGAAGT | CAGTGTAACACA | TGAACGTAGTTGAAGT | 0 |
| 2 | b7a395eb-e573-4cc9-b9fe-ee8adc75a117 | TCGAACAAGATAACAC | ATCTTTTAACCC | TCGAACAAGATAACAC | 0 |
| 3 | c2cb618c-84f2-4aba-bf9d-25a1c827cb13 | AAGTCGTCAATGGCCC | GCAAACGGTTTG | AAGTCGTCAATGGCCC | 0 |
| 4 | a82c080c-2d42-4a63-89d9-0247b4ba5618 | CATACCCAGCGTGAGT | ACGACTCAGTTC | CATACCCAGCGTGAGT | 0 |
| 5 | 068ae4b4-4c0a-4571-83d2-d9d971af1799 | AATCGTGAGCAGTACG | TGTGACGGAGCA | AATCGTGAGCAGTACG | 0 |
| 6 | 50c761ad-cc6c-45d3-b4b3-aedb4bea265b | CATAAGCCAAGAATAC | TATACATAGCCT | CATAAGCCAAGAATAC | 0 |
| 7 | 5f700d64-ad11-4099-bd2c-e39af41341b5 | TGATGGTCATCCTTGC | TCGGTCCAGGGC | GATGGTCAGTCCTTGT | 1 |
| 8 | 20838f03-aaea-4e99-a243-19c43db379da | ACCCTCATCATGCGGC | CCTGTGGCGGGG | ACCCTCATCATGCGGC | 0 |
| 9 | 19f0d679-bd5d-43c7-bd09-744626f8f415 | TGACTCCCAGCGTATT | CCATGCCCAGAG | TGACTCCCAGCGTATT | 0 |
| 10 | 2e57d915-82ad-465d-bf57-a6fb172b144e | GCTGCAGCAATCTGCA | GAGTGTTTACGC | GCTGCAGCAATCTGCA | 0 |

## Molecule counts and normalization

Matrix indices are one-based. Normalization uses each nucleus's complete molecule count from the source matrix.

| source_entry | gene_symbol | cell_barcode | molecule_count | full_cell_library_molecules | CP10K | log2_1_plus_CP10K |
|---|---|---|---|---|---|---|
| 1 | PTPRJ | CATACCCAGCGTGAGT | 2 | 2400 | 8.333333333333334 | 3.222392421336448 |
| 2 | RPS18 | AATCGTGAGCAGTACG | 3 | 1536 | 19.53125 | 4.35974956032233 |
| 3 | NOPCHAP1 | CATAAGCCAAGAATAC | 3 | 1727 | 17.371163867979156 | 4.19937112326218 |
| 4 | TTF2 | TGATGGTCATCCTTGC | 1 | 4715 | 2.1208907741251326 | 1.6419578662652983 |
| 5 | ENSG00000289017 | ACCCTCATCATGCGGC | 2 | 2657 | 7.527286413248024 | 3.0920867144640782 |
| 6 | HAUS8 | AGGTGTTTCAAGAGGC | 1 | 1725 | 5.797101449275362 | 2.7649196557372075 |
| 7 | TTLL5 | CAACCAAGTGTTAAAG | 1 | 1465 | 6.825938566552901 | 2.9682637851585456 |
| 8 | RPL7P9 | ATACCTTGTACTAACC | 2 | 1238 | 16.15508885298869 | 4.100564693090373 |

## Differential-expression results

Benjamini–Hochberg adjusted P values use all 8,135 genes in each workflow and the reference. Positive fold change indicates higher expression in H146.

| gene_symbol | tool | tool_log2FC | tool_p_value | tool_BH_FDR_common | Illumina_log2FC | Illumina_BH_FDR_common |
|---|---|---|---|---|---|---|
| DPM1 | RAD | -0.0234930202181864 | 0.425673842280219 | 0.602445495293942 | 0.285089458337929 | 0.929165434623057 |
| POU2F3 | RAD | -4.79925153249573 | 1.38961571508478e-76 | 1.88408730703578e-73 | -5.3542992786053 | 2.05646963102755e-38 |
| ASCL1 | RAD | 1.14360118517971 | 1.19928300204628e-05 | 0.0001273651073322 | 1.09161128158037 | 0.213204908508441 |
| DPM1 | BLAZE | -0.105842452922816 | 0.1207039548107 | 0.296207140990964 | 0.285089458337929 | 0.929165434623057 |
| POU2F3 | BLAZE | -4.56637292474957 | 1.14919291902758e-33 | 1.55811406604823e-30 | -5.3542992786053 | 2.05646963102755e-38 |
| ASCL1 | BLAZE | 0.578030353497497 | 0.187596667799346 | 0.390107078872106 | 1.09161128158037 | 0.213204908508441 |
| DPM1 | Flexiplex | -0.219405700579521 | 0.137144903199346 | 0.323947092777782 | 0.285089458337929 | 0.929165434623057 |
| POU2F3 | Flexiplex | -4.89306842992386 | 2.43027761367136e-42 | 3.29505139786942e-39 | -5.3542992786053 | 2.05646963102755e-38 |
| ASCL1 | Flexiplex | 0.745588972847403 | 0.0525969040519832 | 0.174391216610382 | 1.09161128158037 | 0.213204908508441 |
