# Selected Figure 5 recovery and verification

The user upload at Git commit `07b39852cf436ad729cd7e4271c786a8c956fa1f` restores the selected RAD ED2 and component-polyT LR-Split-seq comparison. Original upload bytes remain outside the current repository. Only the selected current arms, necessary producing evidence and explicit physical-cell identities are promoted. No raw demultiplexing was rerun.

## Exact source chain

The [incoming acquisition and review receipt](figure_05_incoming_review.json) records the original archive and all incoming metadata deltas. All 180 listed package files passed their original hashes; the complete package has 181 files including its checksum manifest. The [selected source manifest](../manifests/figure_05_splitseq_sources.tsv) records original paths, hashes, sizes and any field selection. The independent native Prism check rehashed the actual master archive (`2987ae97728ff61488a861b305aa2b9fb356f51ba860c084e9c06c823765572b`), compared saved analysis components and verified the selected dataset and graph links.

All 568 original row identities and all 3,408 original numeric entries matched the keyed upload before selecting only RAD ED2 and component polyT. The current table contains 568 physical-cell keys and 2,272 read/UMI integer values, not the superseded comparison columns. Physical identifiers also match the independent 568-cell short-read reference. [Promotion receipt](figure_05_splitseq_recovery.json), [native review](figure_05_native_stat_review.json).

## Executed portable checks

From the repository root with the three current checkpoints staged according to [their SHA-256 manifest](../manifests/figure_05_staged_checkpoints.tsv):

```bash
/scratch/f005f43/rad-manuscript-render-env-20261023/bin/python scripts/figure_05/replay_splitseq.py --root .
python3 scripts/figure_05/extract_splitseq_examples.py
python3 scripts/figure_05/normalize_component_stats.py --input data/examples/figure_05/splitseq/component_native_stats.tsv --output /tmp/f5_component_example.tsv
cmp /tmp/f5_component_example.tsv data/examples/figure_05/splitseq/component_assignments.tsv
python3 scripts/revision/figures_567.py validate
```

The replay verifies all 1,345,255 native component records against normalized assignments, including exact row count and each field; it aggregates both complete current ledgers, requires all 568 exact cell identities and matches every one of the 2,272 retained count values. The verifier binds each aggregation report to its exact count-table hash, recomputes medians and checks conservation. [Native normalization](figure_05_component_normalization.json), [count verification](figure_05_splitseq_counts.json).

The original full RAD ledger also regenerated the uploaded selected-cell RAD checkpoint byte-for-byte: SHA-256 `fe39fc76b67eb374c270ad684d5e96179933d1ce98a9e747b7744083788ff406`. This selected subset is not duplicated in the current package; the complete ledger is retained instead. The source producer's original tally script remains unrecovered, but the explicit replacement aggregation reproduces all selected counts.

The bounded normalization and physical-cell aggregation examples run with the Python standard library. The source renderer reads only its three explicit portable inputs:

```bash
python3 scripts/figure_05/render_candidate_counts.py \
  --input source_data/figure_05/candidate_receptor_totals.tsv \
  --splitseq-input source_data/figure_05/splitseq_reads_umis_568.tsv \
  --splitseq-summary source_data/figure_05/splitseq_summary.tsv \
  --output-dir /tmp/figure05_proofs
```

The count verification used one CPU on the verified shared CPU host Andes8. Initial full RAD/component aggregations took 11.24/4.83 seconds with maximum resident memory 575,712/366,864 KiB. No cluster job or previously stopped work was restarted. The Python 3.11 rendering environment also passed the complete current checkpoint replay. Final isolated render receipts are managed by the repository-wide renderer.

## Counts, units and preserved native analysis

The [summary table](../source_data/figure_05/splitseq_summary.tsv) distinguishes full-input assignment rows, globally unique original reads, published-cell read–cell pairs and exact cell–UMI pairs. Both tools use the same 568 physical cells. Nonempty UMIs of any length are included, matching the executed selected source; imposing a ten-base length filter changes the comparison and is not done here.

The saved selected native test is **two-sided paired t**, t=14.959474687143327, df=567, P=6.890554214980993e-43. Independent calculation from the recovered pairs agrees within floating-point rounding. This confirms the existing executed test and resolves the conflicting signed-rank label for the LR-Split read comparison. No new statistical choice or inferential annotation is introduced. Selected dataset links and graph links are verified; exact final panel/export appearance remains native artwork QA. The receptor-panel test statement is not certified by this separate analysis.

The displayed component value 23.35% remains unverified. Full-input unique-read recovery is 1,338,285/5,764,421 =23.22%; assignment-row recovery is 1,345,255/5,764,421 =23.34%. These are separate numerators. Neither may be silently substituted into the existing annotation.

## Remaining source gates

- **Figure 5A–F:** candidate receptor count semantics are checked; final artwork binding and the successful RAD receptor producing command remain unresolved.
- **Figure 5H:** current RAD ED2/component-polyT per-cell UMI counts are recovered. The exact depth-matched short-read checkpoint or sampling rule/seed and intended panel binding are not. The retained older intersection used RAD ED1. Full short-read FASTQ/BAM summaries are different processing stages and do not establish the missing sampling rule.
- **Native artwork:** final panel lettering, export and significance-annotation appearance still need review. Source-proof plots do not certify those steps.

Checked Figure 5H leads include the durable recovery metadata indexes and the preserved `splitseq_shortread_20260727` package. Its full FASTQ summary has 41,274,093 reads/17,648,026 uncorrected UMIs among 568 cells, and its BAM summary has 21,338,304 reads/9,193,269 corrected UMIs; neither is the intended depth-matched checkpoint. The source SSD path for the separate UMI-intersection work is not mounted. No new depth sampling or intersection was chosen.

The [guide](../docs/figure_05.md) leads from real native records to normalization, physical-cell mapping, complete counts and visible proofs. Exact producing versions/argv/layout/catalog hashes are in the [parameter registry](../manifests/figures_567_tool_parameters.tsv), with unknown R/compiler-runtime details explicit. FLAMES and embedded Flexiplex license notices remain alongside their distinct selected source snapshots.
