# Setup and analysis

The [figure guides](README.md) list the inputs, commands and software versions
for each experiment. Most small counting scripts use the Python standard
library. Plotting and matrix analysis require the scientific Python environment
below; the named RDS and Seurat steps also require R.

## Install the analysis environment

The source-table checks use Python 3.11 with pinned dependencies:

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r environments/render-python311.lock.txt
```

Use `.venv/bin/python` in place of `python3` to select this environment. For small
checks, limit numerical-library threads with:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
```

Tool versions for RAD, BLAZE, Flexiplex and other analysis tools are recorded
in each figure guide.

## Choose the starting data

**Source tables and examples.** The `source_data/figure_XX/` directories contain
the complete plotting and metric tables. The `data/examples/figure_XX/`
directories contain selected records, extraction rules, source hashes and
expected outputs. Run the numbered steps in a figure guide to follow the
calculation from these inputs.

**Saved checkpoints.** Restore the files listed in the figure's checkpoint
manifest, verify their SHA-256 hashes, and run the linked counting or metric
scripts. The `scripts/revision/` commands rebuild the full checkpoint tables.

**Raw reads.** Follow the producing-run commands in the figure guide. Each run
requires its specified raw input, reference, barcode list and software version.

## Restore checkpoint files

Large FASTQ, BAM, assignment-ledger and sparse-matrix files are stored in
`checkpoints/`, which is excluded from Git. The [data-package guide](docs/release_review.md)
lists the archives and their contents. After obtaining an archive and its
SHA-256 manifest, verify the archive and restore its checkpoint payload from the
repository root. For example:

```bash
shasum -a 256 /path/to/rad-manuscript-checkpoints-05.tar.gz
tar -tzf /path/to/rad-manuscript-checkpoints-05.tar.gz
tar -xzf /path/to/rad-manuscript-checkpoints-05.tar.gz \
  --strip-components=1 --wildcards 'rad-manuscript/checkpoints/*'
```

Use the corresponding archive for Figures 3, 6/7, Visium HD or RAGE-seq. Figure
manifests give the restored relative paths and file hashes. RAGE-seq raw-read
runs require the [input-order reconstruction](docs/rage_public_input_order.md),
which restores the read order used in the benchmark from the public ENA file.

## Portable input locations

Files included in Git use paths relative to the repository root. External
records use `external_data/` as a location label; those files are obtained
separately using the dataset accession, filename and SHA-256 in the manifests.
Configure archive locations with these variables, or a script's input options:

| Variable | Default relative to the repository |
|---|---|
| `RAD_DATA_ROOT` | `external_data` |
| `RAD_REVIEWER_ROOT` | `external_data/reviewer_comment_data` |
| `RAD_SCRATCH_ROOT` | `external_data/reviewer_comment_data/scratch_preservation_20260921/files` |
| `RAD_SCRATCH_NFS_ROOT` | Same as `RAD_SCRATCH_ROOT` |

Source tables and small examples work without external files.

ScTagger's [generation contract](source_data/figure_02/quality_generation_contract.json)
retains the exact effective quality-tape seeds. Use the
[recorded-seed adapter](scripts/figure_02/generate_with_recorded_seed.py) to
preserve them when model files are relocated.

## Build diagnostic Flexiplex

The [pinned diagnostic source](vendor/flexiplex-audit/README.md) builds offline
with a C++11 compiler. `build_and_check.py` verifies the patch and tests the
pre-correction barcode output. Leave `FLEXIPLEX_AUDIT_SOURCE_FILE` unset for
manuscript assignment runs.

## Scheduled CPU jobs

Adapt the Slurm templates to your cluster's account and CPU-only partition.
Set explicit CPU, memory and time requests, and verify the selected nodes'
hardware. The figure registries record the producing runs' thread settings.
