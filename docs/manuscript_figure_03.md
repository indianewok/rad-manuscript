# Current manuscript integration draft — Figure 3

The selected RAGE-seq comparison is a completed matched experiment. Its current
results replace the preceding RAGE analysis. Existing statistical procedures
are preserved; prior significance annotations have not been certified for these
new observations.

## Methods replacement prose

The RAGE-seq cell-line mixture ERR3268991 contained 20,346,396 unique physical
reads. Three lists of 4,505 barcodes were sampled without replacement from the
737,280-entry 10x 3′ v2 chemistry catalog after excluding the matched
4,505-barcode filtered reference. Python 3.9.16 `random.Random` used list seeds
2026102301, 2026102302 and 2026102303. All three tools received the complete input and the same list within
each replicate, using 16 tool threads. The lists, reference and catalog are
deposited with their hashes.

RAD used commit `cd0582b2440cde0f35725dc557fa47307d74d374`, the 3′ v2 layout with
a ten-base UMI, offensive correction, both mutation limits set to two and chunks
of 5,000 reads. BLAZE 2.6.0a0 used commit
`af8d2cc9f6374caf4d1006d5f8a0e99097211646`, the supplied list with discovery
disabled, the 3v2 kit and barcode edit distance two. Flexiplex used the pinned
1.02.6 diagnostic build, the 10x3v2 layout, barcode edit distance two and flank
edit distance eight; its optional source-set filter was unset. Exact commands,
build identities and dependency versions are recorded in the
[Figure 3 producer table](figure_03.md).

Tool output identifiers were resolved to original physical reads and checked
against the complete input universe. Any identifier with multiple assignment
records was excluded entirely, including repeated records for the same target.
Every remaining identifier contributed one count to its target, and all
zero-count supplied targets were retained. The diagnostic Flexiplex sidecar was
the assignment source; the separate FASTQ comparison records assignments that
did not produce an emitted FASTQ record. Strict assignments, excluded ambiguous
identifiers and unassigned identifiers summed to the complete input in every
arm. Full source, producer and output hashes were checked.

For comparison across datasets, strict assigned physical reads were divided by
all input physical reads: 4,993,805 for ScTagger-L, 10,000,000 for LongBench
SC-ONT and 20,346,396 for RAGE-seq. The three supplied-list draws were technical
randomizations. Raw totals and counts per supplied target remain available.
The supplied targets are absent from an operational reference; this does not
establish biological absence for experimental datasets.

## Results replacement prose

RAD assigned fewer input reads to the reference-excluded lists in each of the
three datasets. In the new RAGE-seq experiment, the mean assigned fraction was
0.248% for RAD, 6.889% for BLAZE and 8.035% for Flexiplex. The three RAD totals
were 50,349, 50,901 and 50,280 physical reads; the corresponding BLAZE totals
were 1,369,920, 1,419,257 and 1,415,786, and Flexiplex totals were 1,594,697,
1,652,917 and 1,656,957. All nine arms passed complete input-identity and
read-conservation checks.

Values below are the mean percentage of input physical reads, with the minimum
and maximum across the three list draws. These ranges are descriptive.

| Dataset | RAD | BLAZE | Flexiplex |
|---|---:|---:|---:|
| ScTagger-L | 0.983 (0.981–0.987) | 5.995 (5.891–6.102) | 9.257 (9.187–9.319) |
| LongBench SC-ONT | 0.467 (0.465–0.470) | 10.425 (10.054–10.976) | 13.858 (13.644–14.226) |
| RAGE-seq | 0.248 (0.247–0.250) | 6.889 (6.733–6.975) | 8.035 (7.838–8.144) |

The [27 current observations](../source_data/figure_03/offlist_totals.tsv) and
[numerical claim registry](../manifests/results_claims.tsv) expose the counts,
denominators and arithmetic. The selected one-way ANOVA procedure is unchanged;
native recalculation and final significance/artwork review remain required.
No new test or biological-replication claim is introduced here.
