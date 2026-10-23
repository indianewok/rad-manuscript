# RAGE reference and chemistry catalog

These are the complete fixed identifier sets used to draw the three supplied
challenge lists. The [Figure 3 walkthrough](../../docs/figure_03.md) begins with
the exact tool versions and then follows real reads into counts.

| File | Meaning | Rows |
|---|---|---:|
| [Matched reference](rage_matched_reference_4505.txt) | Filtered short-read cell barcodes, with the terminal `-1` removed, deduplicated and sorted | 4,505 |
| [Chemistry catalog](chemistry_3v2_catalog.txt.gz) | All possible 10x 3v2 barcode sequences in the selected catalog | 737,280 |
| [Source manifest](source_manifest.tsv) | Compressed/plain hashes, normalization and original source identities | 2 files |

Each random challenge list contains 4,505 catalog barcodes outside the matched
reference. Every tool receives the same list within a replicate. The full catalog
is a design list; membership does not indicate that a cell was observed.

The first five actual lines of each file are:

| Matched reference | Chemistry catalog |
|---|---|
| `AAACCTGAGAATCTCC` | `AAACCTGAGAAACCAT` |
| `AAACCTGAGCGTCTAT` | `AAACCTGAGAAACCGC` |
| `AAACCTGAGTCCATAC` | `AAACCTGAGAAACCTA` |
| `AAACCTGAGTGGGCTA` | `AAACCTGAGAAACGAG` |
| `AAACCTGCAAACGTGG` | `AAACCTGAGAAACGCC` |

The complete raw FASTQ is acquired separately. Its original read identifiers,
sequence, quality and **order** are verified before an exact replay. See the
[public input-order guide](../../docs/rage_public_input_order.md).
