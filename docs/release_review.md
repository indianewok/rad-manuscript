# Current release review

The staged package is a review artifact. The repository has one current analysis
tree, actual input excerpts, current source tables, scripts and verification
receipts. Older workspaces, mixed Prism projects, obsolete figures, manuscript
source documents and recovery copies are outside the package. Git history is not
rewritten.

## Build the review artifacts

After the source data and validation reports are stable:

```bash
python3 scripts/check_data_inventory.py
python3 scripts/check_manuscript_claims.py
python3 scripts/collect_handoff_status.py
python3 scripts/prepare_review_release.py \
  --include-checkpoints --include-software --include-rage-order
```

The ignored `release_staging/` directory receives:

- `rad-manuscript-current.tar.gz`: current code, readable examples, source tables,
  proofs, version registries, licenses and checks.
- `flexiplex-1.02.6-rad-audit.1.tar.gz`: a standalone copy of the custom build's
  source, patch, dependency, executable, licenses and rebuild check, ready to
  attach to a distinct GitHub Release when approved.
- `rad-manuscript-checkpoints-06-07.tar.gz`: the separately indexed validated
  donor/reference and expression checkpoint files.
- `rad-manuscript-checkpoints-05.tar.gz`: the selected RAD and component Flexiplex
  LR-Split-seq assignment checkpoints for replaying cell-level counts.
- `rad-manuscript-checkpoints-03.tar.gz`: the matched RAGE experiment's parsed
  assignments, physical-read outcomes, counts and producer/validation receipts.
  Large regenerable tool FASTQs are excluded.
- `rad-manuscript-hd-lineage-under-review.tar.gz`: the two current count sources
  for Figure 1D. Detection and demultiplexing are distinct processing stages;
  the grid, tissue mask and detection totals are verified. The selected Seurat
  counts and barcode-to-bin producer remain unrecovered.
- `rad-manuscript-rage-software.tar.gz`: source archives for the selected RAGE
  execution; the custom Flexiplex source/binary is already in the current archive.
- `rad-manuscript-rage-input-order.tar.gz`: the selected physical-read order and
  complete input-identity receipts, needed for [public FASTQ reconstruction](rage_public_input_order.md).
- `release_manifest.json` and `SHA256SUMS`: archive hashes and read-back results.

Every archive member is listed with its size and SHA-256 in
`ARCHIVE_CONTENTS.tsv`, and the builder reads every member back to verify bytes.
This packaging check does not replace the scientific validation or remaining
source gates listed in [validation.md](validation.md).

## Identifiers and metadata

On 23 October 2026, the live API for
[record 20189813](https://zenodo.org/records/20189813) reported a published record
whose DOI field is **10.64898/2026.05.29.728810**, the manuscript preprint DOI.
It did not establish a separate reserved Zenodo DOI for this new package. The
earlier reserved-DOI statement has therefore been removed from repository
documentation. No new archival DOI is fabricated or promised.

[The metadata draft](../manifests/zenodo_metadata.draft.json) treats the preprint
DOI as a related publication and deliberately omits a new record DOI. At release,
the author must select the correct new-record/version workflow and verify the
identifier actually assigned by the archive before updating citation links.
The existing public record has not been modified.

## Items to settle before public release

The package still has the scientific and native-artwork gates listed in
[validation.md](validation.md). The repository's current privacy setting must be
reviewed before it can serve as a public reproduction URL. Eight benchmark inputs
derive from EGA-controlled tonsil libraries. The repository includes aggregate
benchmark metrics and acquisition instructions, with no controlled raw reads or
raw controlled examples. The author should confirm that derived-result
redistribution matches the applicable data-access agreement before publication.
The repository's MIT license does not relicense third-party datasets; the
Flexiplex and Edlib licenses are supplied with their source.

The custom Flexiplex package can be attached to a distinct release tag such as
`flexiplex-1.02.6-rad-audit.1`. Pin the full repository commit and the package's
source/patch/binary hashes. A separate fork is optional. See the exact
[build-and-host instructions](../vendor/flexiplex-audit/README.md).
