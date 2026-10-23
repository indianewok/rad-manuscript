# Actual Split-seq root-data preview

These are bounded records from the selected current runs. Full-source hashes and exact data-row ordinals are in [extraction.json](extraction.json). The first two original physical-cell IDs are retained; eight matching assignment rows are shown per tool.

## Native component records

| Read | BC1 | BC2 | BC3 | UB |
|---|---|---|---|---|
| SRR13948564.332868 | CAAGGAGC | ATAGCGAC | TACGGTTA | CGCGTGCTTA |
| SRR13948564.1893980 | AAGAGATC | TCTTCACA | GGTGGAGC | GGTCATAGTA |
| SRR13948564.2011980 | AAGAGATC | TCTTCACA | GGTGGAGC | TGGTACCTCG |

The small normalization script writes `BC3_BC2_BC1` and reverse-complements `UB`. RT primer variants then map to the T primer of the same physical well; exact read IDs and UMI strings are counted within that cell. The [full selected table](../../../../source_data/figure_05/splitseq_reads_umis_568.tsv) contains the complete 568-cell counts.

## Physical-cell identities

| Original Prism row | Published ID | Canonical RT_BC2_BC3 | Sample |
|---|---|---|---|
| 1 | CAAGGAGCATAGCGAC_22 | TACGGTTA_ATAGCGAC_CAAGGAGC | MB_nuclei |
| 2 | AAGAGATCTCTTCACA_39 | GGTGGAGC_TCTTCACA_AAGAGATC | MT_nuclei |

## A real non-ten-base UMI is included

| Original RAD read | Saved normalized barcode | Canonical physical cell | Exact UMI | Bases |
|---|---|---|---|---|
| SRR13948564.2239534 | TACGGTTA_ATAGCGAC_CAAGGAGC | TACGGTTA_ATAGCGAC_CAAGGAGC | GGATTAGAA | 9 |

This actual nine-base UMI is nonempty and contributes to the bounded read and exact-UMI counts. Requiring exactly ten bases would discard it and change the selected counting rule.

The eight RAD excerpt rows yield five read–cell pairs for the first selected cell and three for the second; see [bounded counts](rad_bounded_counts.tsv). These are excerpt counts, not full-cell depths.

Follow [Figure 5](../../../../docs/figure_05.md) for exact normalization and aggregation commands.
