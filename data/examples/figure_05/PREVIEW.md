# Figure 5 source-data examples

The tables below show selected RAGE-seq receptor assignments and the paired LR-Split-seq short-read reference. [Extraction details](extraction.json) record source paths, hashes and selected rows. The [Figure 5 guide](../../../docs/figure_05.md) gives the complete analysis.

## Read-assignment input (first six rows)

| read_id | barcode | native |
|---|---|---|
| 51593f7b-d384-41a3-877c-4d27bfc0c279 | CGTAGGCGTGGCGAAT | 0 |
| 111ba9ec-6366-46fa-9dca-d97af1a6d3c6 | CATGGCGTCTGTCCGT | 0 |
| 1e789233-789f-47ff-b983-72a5135e6e84 | GACGCGTCATCCTTGC | 1 |
| 32ed8d5d-9dd7-49e7-bcf8-7dcd4181786d | GCATGCGCATATGAGA | 0 |
| 45d42e26-7d8e-46e6-b287-9e78f044e876 | GAAGCAGCAGCTGTGC | 1 |
| c22d530b-f000-466b-bb44-a924a4e53e4b | CAACCAAAGTTGTCGT | 1 |

## Receptor input (first three selected barcode rows)

| barcode | celltype | native_bcr | corrected_bcr | native_tcr | corrected_tcr |
|---|---|---|---|---|---|
| AAACCTGAGAATCTCC | Ramos | 713 | 1413 | 10 | 45 |
| AAACCTGAGCGTCTAT | Ramos | 535 | 1040 | 22 | 54 |
| AAACCTGAGTCCATAC | Ramos | 497 | 930 | 17 | 35 |

The corrected columns above include native assignments. Subtract the native count to obtain corrected-only reads.

## Exclusive output

| barcode | receptor | native | corrected_only | assigned |
|---|---|---|---|---|
| AAACCTGAGAATCTCC | bcr | 713 | 700 | 1413 |
| AAACCTGAGAATCTCC | tcr | 10 | 35 | 45 |
| AAACCTGAGAATCTCC | unmapped | 340 | 358 | 698 |
| AAACCTGAGCGTCTAT | bcr | 535 | 505 | 1040 |
| AAACCTGAGCGTCTAT | tcr | 22 | 32 | 54 |
| AAACCTGAGCGTCTAT | unmapped | 329 | 325 | 654 |
| AAACCTGAGTCCATAC | bcr | 497 | 433 | 930 |
| AAACCTGAGTCCATAC | tcr | 17 | 18 | 35 |
| AAACCTGAGTCCATAC | unmapped | 216 | 227 | 443 |

## LR-Split-seq short-read reference (first three cells)

| cell_bc | sample | fastq_reads | fastq_umis_uncorrected | bam_reads | bam_umis_corrected |
|---|---|---|---|---|---|
| CAAGGAGCATAGCGAC_22 | MB_nuclei | 1688527 | 495255 | 825860 | 326783 |
| AAGAGATCTCTTCACA_39 | MT_nuclei | 1043341 | 393166 | 563991 | 241593 |
| GATGAATCCACCTTAC_33 | MT_nuclei | 915931 | 328622 | 244439 | 99233 |
