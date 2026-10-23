# What has been reproduced

The repository separates **rendering**, **resuming retained analytical data**,
and **running tools again on raw reads**. These are different claims. Existing
statistical choices and annotations remain unchanged; a source-verification PNG
does not establish native Prism recalculation or final artwork approval.

| Figure | Executed verification | Remaining dependency |
|---|---|---|
| 1 | Reparsed 108 accepted timing phases and reconstructed 54 paired repetitions; distinguished HD detection/demultiplexing count stages; recovered the exact 419×419 grid and 123,658-bin tissue mask | Selected Seurat `nCount_Spatial` values and full barcode-to-bin creation provenance remain unrecovered. Unequal counts from different processing stages are not a failed equivalence check. |
| 2 | Rescored 144 discovery lists; full FASTQ sequence/ID/quality checks; full assignment recount and all 52,076 per-target values | Native Prism desktop review remains. Raw synthetic generation and all three tool runs were not repeated. |
| 3 | Full retained ScTagger/LongBench strict-read recount; completed nine-arm raw RAGE experiment on all 20,346,396 reads with identity/conservation checks; sidecar/FASTQ comparisons; LongBench correction aggregates and edge-case fixtures | Current source data and normalized fractions passed 414 build checks. Native statistical recalculation/artwork and full correction pair-overlap recovery remain separate. |
| 4 | Retained all 37 inputs/111 observations; all 87 tool/reference comparisons for 29 public inputs reproduce exactly from deposited lists; verified saved input-characteristic joins | The 24 controlled-input rows retain aggregate metrics. Some producing-run identities and the original all-input SeqKit execution remain unrecovered. Four Visium splitRAD temporary callsets were absent at checked paths. |
| 5 | Receptor candidate count semantics checked; selected LR-Split producers, all 568 explicit physical-cell identities and all 2,272 read/UMI counts reproduced from complete current ledgers; saved native paired t test independently verified | Receptor final-artwork/producer binding, exact final native export and Figure 5H depth-matched short-read checkpoint/selection remain unresolved. Current long-read per-cell UMIs are recovered. |
| 6 | Full donor/CellSNP content, all 12,012 reference identities, BAM/BAI bytes and index/header checks; exact fixed-coordinate comparison | No raw alignment, CellSNP or Vireo execution was repeated. BAM byte/index verification is not a full decoded-record audit. |
| 7 | Verified all 57,885,606 retained RAD assignment rows and the matrices; all 24,405 selected effects/P values match native output; recalculated common-family BH values and all 594 threshold cells | The assignment checkpoint has lost segment/orientation suffixes and has no gene IDs. The emitted FASTQ/read-to-gene files and selected panel C fit remain unrecovered. Panel E is removed. |

The [task registry](../manifests/task_status.tsv) records completion and dependencies
at task level. Each figure guide links its detailed checks, source hashes,
commands and limitations. A missing producer is never filled with a version from
another run.

## Portable rendering

The [clean-render report](../validation/clean_render.json) uses a separate output
directory, a minimal environment and a fresh Python 3.11 environment pinned by
[the dependency lock](../environments/render-python311.lock.txt). File-access
tracing checks that rendering does not read the author's sequencing project,
scratch directories or old workstation paths. The report lists the exact groups
and outputs checked; groups absent from the report are not implied to pass.

```bash
python3 scripts/check_render_isolation.py \
  --python /path/to/render-environment/bin/python --groups 124 3 5 567 --promote
```

This check redraws source-verification figures. It does not rerun sequencing
tools or recover missing artwork. `--promote` copies the verified exports into
the current figure directories only after all requested renderers pass. The
release builder requires those exact export hashes, as well as unchanged source
tables, renderers and isolation checker.

## Small examples and numerical claims

The examples are actual bounded source records with extraction rules and hashes.
Use each figure's small commands before attempting a full checkpoint resume.
The [numerical claim registry](../manifests/results_claims.tsv) records values,
units, denominators, selection rules and source hashes. Regenerate it with:

```bash
python3 scripts/check_manuscript_claims.py
python3 scripts/check_data_inventory.py
```

The [custom Flexiplex check](../validation/software/flexiplex_audit_build.json)
rebuilds upstream and modified source and compares both with the pinned binary
on a four-read fixture. Its scope is explicit; it is not full-data equivalence.

## Release status

This is a current analysis review package. Missing scientific sources and native
artwork checks remain visible. No archive record or repository visibility has
been changed. Large retained checkpoints are staged separately from Git; public
release of derived controlled-access results still requires the author's access
agreement review. No controlled raw reads are included in the repository.
