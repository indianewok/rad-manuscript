# LR-Split-seq assignment examples

These examples follow the first two published physical cells through RAD and component Flexiplex/poly-T assignments. Each tool contributes eight records. [Extraction details](extraction.json) give the source hashes and original row numbers.

## Native component records

| Read | BC1 | BC2 | BC3 | UB |
|---|---|---|---|---|
| SRR13948564.332868 | CAAGGAGC | ATAGCGAC | TACGGTTA | CGCGTGCTTA |
| SRR13948564.1893980 | AAGAGATC | TCTTCACA | GGTGGAGC | GGTCATAGTA |
| SRR13948564.2011980 | AAGAGATC | TCTTCACA | GGTGGAGC | TGGTACCTCG |

The normalization script writes `BC3_BC2_BC1` and reverse-complements `UB`. RT primer variants then map to the T primer of the same physical well; exact read IDs and UMI strings are counted within that cell. The [full selected table](../../../../source_data/figure_05/splitseq_reads_umis_568.tsv) contains the complete 568-cell counts.

## Physical-cell identities

| Original Prism row | Published ID | Canonical RT_BC2_BC3 | Sample |
|---|---|---|---|
| 1 | CAAGGAGCATAGCGAC_22 | TACGGTTA_ATAGCGAC_CAAGGAGC | MB_nuclei |
| 2 | AAGAGATCTCTTCACA_39 | GGTGGAGC_TCTTCACA_AAGAGATC | MT_nuclei |

## UMI inclusion

| Original RAD read | Saved normalized barcode | Canonical physical cell | Exact UMI | Bases |
|---|---|---|---|---|
| SRR13948564.2239534 | TACGGTTA_ATAGCGAC_CAAGGAGC | TACGGTTA_ATAGCGAC_CAAGGAGC | GGATTAGAA | 9 |

This nine-base UMI passes the nonempty-UMI inclusion rule and contributes to both the read and exact-UMI counts.

The eight RAD example rows give five read–cell pairs for the first cell and three for the second; see [example counts](rad_bounded_counts.tsv).

Follow [Figure 5](../../../../docs/figure_05.md) for exact normalization and aggregation commands.
