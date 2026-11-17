# Figure 3 methods

## Off-list barcode assignments

For each of the three datasets, the matched reference barcodes were removed from the chemistry catalog. Three target lists equal in size to the reference were sampled independently as technical replicates. RAD, BLAZE and Flexiplex received the same input reads and target list within each replicate.

ScTagger-L contained 4,993,805 reads from 5,000 known source barcodes. LongBench SC-ONT used a 10,000,000-read subsample and a 5,211-barcode filtered Cell Ranger reference. Both used the 10x 3′ v3 catalog. RAGE-seq used all 20,346,396 reads from ERR3268991, its 4,505-barcode filtered Cell Ranger reference and the 737,280-entry 10x 3′ v2 catalog. The [Figure 3 guide](figure_03.md) lists the exact target-list seeds, software versions and commands for all three datasets.

All three off-list experiments used RAD 1.0.2 at commit `cd0582b2440cde0f35725dc557fa47307d74d374`, BLAZE 2.6.0a0 at commit `af8d2cc9f6374caf4d1006d5f8a0e99097211646`, and the Flexiplex 1.02.6 build with pre-correction barcode output. RAD used offensive correction and mutation limits of two. BLAZE used supplied-list demultiplexing, minimum quality Q15 and barcode edit distance two, with EmptyDrops disabled. Flexiplex used barcode edit distance two and flank edit distance eight. Each dataset used its appropriate chemistry layout.

Output records were matched to the original reads. Each read with exactly one assignment record was counted once. Reads with multiple records were excluded, including repeated assignments to the same target. The per-target table includes all supplied barcodes, including those with zero reads. Flexiplex assignments came from its diagnostic table. Assignment percentages used all input reads as the denominator. Assigned reads, reads with multiple records and unassigned reads summed to the full input.

## LongBench barcode-correction outcomes

Extracted source barcodes were matched to final assignments in the four LongBench single-cell and single-nucleus ONT and PacBio datasets. The chemistry catalog defined valid barcode sequences. The matched Cell Ranger filtered set defined the reference cells or nuclei.

Corrected off-list assignments changed a source outside the chemistry catalog to a selected target. Failure Mode 1 changed a source in the filtered reference to a different reference-supported target selected by the tool. Failure Mode 2 changed a catalog-valid source outside the filtered reference to a selected target. Each category required an observed source-to-target change.

Counts used unique original-read–target-barcode pairs within each category. Repeated records for the same pair were collapsed, including records from RAD concatemer segments. A read assigned to two targets could contribute to both. A pair with different observed sources could contribute to more than one category. Each per-target percentage used all unique read–target assignments to that tool's target as its denominator. Unselected targets and selected targets without assignments had null percentages.

[Commands and worked examples](figure_03.md) · [Source tables](../source_data/figure_03/) · [Figure legend](current_figure_legends.md#figure-3)
