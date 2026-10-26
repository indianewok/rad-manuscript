# Data packages

The analysis package contains the code, examples, source tables, figures and
file manifests. Larger intermediate files are distributed as separate
checkpoint archives. Each archive includes an `ARCHIVE_CONTENTS.tsv` with file
sizes and SHA-256 hashes; `release_manifest.json` and `SHA256SUMS` record the
archive checksums.

## Package contents

| Archive | Contents |
|---|---|
| `rad-manuscript-current.tar.gz` | Analysis code, examples, source tables, figures, software records, licenses and validation reports |
| `flexiplex-1.02.6-rad-audit.1.tar.gz` | Diagnostic Flexiplex source, patch, dependency, executable, licenses and build check |
| `rad-manuscript-checkpoints-03.tar.gz` | RAGE-seq parsed assignments, physical-read outcomes, counts and run records |
| `rad-manuscript-checkpoints-05.tar.gz` | RAD and component Flexiplex LR-Split-seq assignments for cell-level read and UMI counts |
| `rad-manuscript-checkpoints-06-07.tar.gz` | Genotype, donor-reference and expression checkpoints |
| `rad-manuscript-hd-lineage-under-review.tar.gz` | Visium HD detection and demultiplexing count sources for Figure 1D |
| `rad-manuscript-rage-software.tar.gz` | Software source archives for the RAGE-seq experiment |
| `rad-manuscript-rage-input-order.tar.gz` | Physical-read order and input-identity records for reconstructing the RAGE-seq benchmark FASTQ |

[SETUP.md](../SETUP.md) gives checkpoint-restoration commands. The
[RAGE-seq input guide](rage_public_input_order.md) describes reconstruction from
the public FASTQ. The [reproducibility table](validation.md) lists the inputs
needed to repeat each analysis.

## Build the packages

Run these commands from the repository root:

```bash
python3 scripts/check_data_inventory.py
python3 scripts/check_manuscript_claims.py
python3 scripts/collect_handoff_status.py
python3 scripts/prepare_review_release.py \
  --include-checkpoints --include-software --include-rage-order
```

The builder writes the archives to the ignored `release_staging/` directory,
then reads each member back and checks its bytes against the manifest.

## Archival metadata

[Record 20189813](https://zenodo.org/records/20189813) identifies the manuscript
preprint with DOI **10.64898/2026.05.29.728810**. The
[data-package metadata](../manifests/zenodo_metadata.draft.json) records that DOI
as a related publication. A separate archival identifier for these analysis
packages has not yet been assigned.

The repository contains aggregate metrics for the eight EGA-controlled Visium
inputs. Their raw reads are obtained through the access route in the
[data guide](../data/README.md). Third-party datasets retain their original
access and license terms. Flexiplex and Edlib licenses are included with their
source packages.

The diagnostic Flexiplex archive has its own version identifier,
`flexiplex-1.02.6-rad-audit.1`, together with source, patch and binary hashes. Its
[build instructions](../vendor/flexiplex-audit/README.md) describe the packaged
implementation.
