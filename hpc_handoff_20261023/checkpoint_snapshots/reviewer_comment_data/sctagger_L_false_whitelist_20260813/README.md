# ScTagger-L random false-whitelist experiment (2026-08-13)

All nine arms use the same 4,993,805-read flat-Q20 ScTagger-L FASTQ. For each of three fixed RNG seeds, 5,000 unique 10x 3' v3 catalogue barcodes were sampled after excluding all 5,000 synthetic truth barcodes. RAD, BLAZE and the pinned Flexiplex audit build were each forced to use that exact replicate list.

Counts use strict physical-read semantics: one emitted assignment gives one count; if a physical read ID has more than one emitted record, the entire ID is classified as ambiguous and excluded from all per-cell counts. Zero-count targets are retained. A 'false' barcode here means absent from the known synthetic truth list, not a general claim about every possible biological library.

The requested presentation file is `results/false_target_assigned_reads_wide.csv`. Use the identity-bearing companion for audits. Commands, versions, logs, wall time, maximum RSS, supplied lists and exit markers remain under `runs/`.

The wide CSV header is exactly `RAD_rep1..3`, `BLAZE_rep1..3`, and
`Flexiplex_rep1..3`; it has no barcode column. Rows pair by lexical sampled-
whitelist rank within each replicate. The identity-retaining tables preserve
the barcode, replicate, rank, tool, and count mapping.

Whitelist-manifest terminology: `rejected_truth_or_duplicate` counts only
catalog candidates actually processed before a target list was filled, while
`unused_cushion_draws` are sampled but unconsumed candidates. Thus the prior
reported `rejected_truth_or_duplicate=66` was the cushion/unconsumed-candidate
count for rep1; the correct rep1 manifest values are rejected=0 and
unused_cushion_draws=66. The rep2/rep3 manifest values are interpreted the same
way.
