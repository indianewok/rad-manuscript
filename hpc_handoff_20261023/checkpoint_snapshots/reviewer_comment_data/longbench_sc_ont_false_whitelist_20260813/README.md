# LongBench SC-ONT false-whitelist experiment

The experiment uses the exact 10,000,000-read SeqKit subsample recorded in
`provenance/sample_validation.tsv` and three deterministic 5,211-row false
whitelists. False means excluded from the matched short-read list; it does
not mean an absolute biological false barcode.

`results/false_target_assigned_reads_wide.csv` has exactly 5,211 data rows and
exactly nine non-negative integer tool-by-replicate columns, with no cell
identity column. Row i is lexical whitelist rank i within each replicate.
The identity-retaining companion is
`results/false_target_assigned_reads_long.tsv`.

Counts use strict physical-read semantics. Tool suffixes are normalized to
the source read ID. If an ID is assigned more than once, all of its assignments
are excluded as ambiguous, including duplicate assignments with the same final
barcode. Zero-count supplied cells are retained; sums and dimensions are
validated in `VALIDATION.tsv`.

For Flexiplex, the audit sidecar is the authoritative assignment table. The
trimmed FASTQ is independently parsed and must be an exact subset of those
assignments. A few sidecar-only rows can occur when Flexiplex assigns a barcode
but has no nonempty trimmed sequence to emit. These rows remain valid barcode
assignments and their exact counts are reported in
`summaries/per_run_summary.tsv`; FASTQ-only rows or changed shared-ID barcode
groups are hard validation failures.

All three whitelist text files are preserved under `whitelists/`. Native
commands, versions, hashes, exact commands, stdout/stderr, `/usr/bin/time -v`
RSS logs, and exit markers remain under `runs/`. Older non-SeqKit partials are
excluded from the result and were removed at the user's request. The exact
cleanup inventory is `provenance/CLEANUP_20260813.tsv`. The runner preserves a
stale arm under `interrupted_*` during recovery so it cannot be mistaken for a
completed arm; no such directory is retained in the cleaned package.
