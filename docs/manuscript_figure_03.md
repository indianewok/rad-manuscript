# Off-list assignments and barcode correction

## Supplied-list challenge methods

The RAGE-seq cell-line mixture ERR3268991 contained 20,346,396 unique physical reads. Three lists of 4,505 barcodes were sampled without replacement from the 737,280-entry 10x 3′ v2 chemistry catalog after excluding the matched filtered reference. Python 3.9.16 `random.Random` used seeds 2026102301, 2026102302, and 2026102303. All three tools received the complete input and the same target list within each replicate, with 16 tool threads. The lists, reference, and catalog are deposited with their hashes.

RAD used commit `cd0582b2440cde0f35725dc557fa47307d74d374`, the 3′ v2 layout with a ten-base UMI, offensive correction, both mutation limits set to two, and chunks of 5,000 reads. BLAZE 2.6.0a0 used commit `af8d2cc9f6374caf4d1006d5f8a0e99097211646`, the supplied list with discovery disabled, the 3v2 kit, minimum barcode quality Q15, and barcode edit distance two. Flexiplex used the pinned 1.02.6 diagnostic build, the 10x3v2 layout, barcode edit distance two, and flank edit distance eight. Its optional source-set filter was unset. Exact commands, build identities, and dependencies are recorded in the [Figure 3 guide](figure_03.md).

Output identifiers were resolved to original physical reads and checked against the complete input. Identifiers with multiple assignment records were excluded entirely, including repeated records for the same target. Each remaining identifier contributed one count to its target. All supplied targets were retained, including zero-count targets. The Flexiplex diagnostic table supplied its assignment records; comparison with the emitted FASTQ identified diagnostic assignments without a corresponding FASTQ record. Assigned, excluded ambiguous, and unassigned identifiers summed to the complete input in every run.

For comparison across datasets, assigned physical reads were divided by all input physical reads: 4,993,805 for ScTagger-L, 10,000,000 for LongBench SC-ONT, and 20,346,396 for RAGE-seq. Each dataset had three independently sampled target lists. Mean assignment percentages and ranges were calculated across these technical list draws. Raw totals and per-target counts are also retained.

## LongBench barcode-correction methods

Correction outcomes were examined in LongBench single-cell and single-nucleus ONT and PacBio inputs. Extracted source barcodes were linked to the final assigned barcodes. The chemistry catalog defined valid barcode sequences, and the matched Cell Ranger filtered set identified short-read-supported cells or nuclei.

Corrected off-list assignments changed a source outside the chemistry catalog to a tool-selected target. Failure Mode 1 changed a catalog-valid source outside the matched filtered set to a tool-selected target, measuring reassignment from a valid barcode outside the short-read reference into the selected population. Failure Mode 2 changed a source in the matched filtered set to a different selected target in that set, measuring reassignment between reference-supported cells or nuclei. Each category required an observed source-to-target change.

Counts used unique original-read–target-barcode pairs within each category. Repeated records for the same pair were collapsed, including records from RAD concatemer segments. A read assigned to two different targets could contribute to both. A pair with different observed sources could contribute to more than one category. Counts were summarized by target barcode and joined across tools by barcode sequence. Each category percentage used all unique read–target assignments to that tool’s target as its denominator. Unselected targets and selected targets with no assignments had null percentages.

## Supplied-list challenge results

RAD assigned fewer input reads to the reference-excluded lists in each of the three datasets. In RAGE-seq, the mean assigned fraction was 0.248% for RAD, 6.889% for BLAZE, and 8.035% for Flexiplex. The three RAD totals were 50,349, 50,901, and 50,280 reads. BLAZE totals were 1,369,920, 1,419,257, and 1,415,786; Flexiplex totals were 1,594,697, 1,652,917, and 1,656,957.

The table shows mean percentages and the minimum–maximum range across the three target-list draws.

| Dataset | RAD | BLAZE | Flexiplex |
|---|---:|---:|---:|
| ScTagger-L | 0.983 (0.981–0.987) | 5.995 (5.891–6.102) | 9.257 (9.187–9.319) |
| LongBench SC-ONT | 0.467 (0.465–0.470) | 10.425 (10.054–10.976) | 13.858 (13.644–14.226) |
| RAGE-seq | 0.248 (0.247–0.250) | 6.889 (6.733–6.975) | 8.035 (7.838–8.144) |

The [27 observations](../source_data/figure_03/offlist_totals.tsv) and [results registry](../manifests/results_claims.tsv) contain the counts, denominators, and arithmetic. The [Figure 3 guide](figure_03.md) links the complete run and counting checks.
