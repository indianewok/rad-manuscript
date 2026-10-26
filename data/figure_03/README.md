# RAGE-seq reference barcodes

The off-list challenge uses the matched short-read reference and the complete
10x 3′ v2 chemistry catalog to sample three target lists. Each list contains
4,505 catalog barcodes after exclusion of the reference set. All three tools
receive the same list within each replicate. The [Figure 3 guide](../../docs/figure_03.md)
describes the sampling and assignment analysis.

| File | Contents | Rows |
|---|---|---:|
| [Matched reference](rage_matched_reference_4505.txt) | Filtered short-read cell barcodes, with terminal `-1` suffixes removed, deduplicated and sorted | 4,505 |
| [Chemistry catalog](chemistry_3v2_catalog.txt.gz) | Valid 10x 3′ v2 barcode sequences | 737,280 |
| [Source manifest](source_manifest.tsv) | Source identities, normalization rules and compressed/plain file hashes | 2 files |

The first five barcodes in each file are:

| Matched reference | Chemistry catalog |
|---|---|
| `AAACCTGAGAATCTCC` | `AAACCTGAGAAACCAT` |
| `AAACCTGAGCGTCTAT` | `AAACCTGAGAAACCGC` |
| `AAACCTGAGTCCATAC` | `AAACCTGAGAAACCTA` |
| `AAACCTGAGTGGGCTA` | `AAACCTGAGAAACGAG` |
| `AAACCTGCAAACGTGG` | `AAACCTGAGAAACGCC` |

Obtain the raw FASTQ and restore the benchmark read order using the
[public-input guide](../../docs/rage_public_input_order.md). That procedure
verifies read identifiers, sequences, qualities and order.
