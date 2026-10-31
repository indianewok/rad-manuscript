# Setup and analysis

The analysis starts from source tables, intermediate checkpoints or raw reads.
Choose the starting point for the figure of interest, then follow its
[figure guide](README.md). Software versions and parameters are recorded with
each experiment.

## Analysis environment

Use Python 3.11 for the source-table calculations and plotting programs:

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r environments/render-python311.lock.txt
```

Run commands from the repository root. Substitute `.venv/bin/python` for
`python3` to use this environment. Limit numerical-library threads for the
small examples and source-table calculations:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
```

The figure guides identify programs that use only the Python standard library.
RDS, Seurat and differential-expression workflows use the R packages and
versions recorded with their producing scripts.

## Source tables

`source_data/figure_XX/` contains the tables used to calculate plotted metrics.
`data/examples/figure_XX/` provides smaller records with the same field
definitions, extraction rules and expected outputs. Start with an example to
follow a calculation, then apply the same program to the complete source table.

The [dataset registry](manifests/datasets.tsv) links inputs to their accessions.
Check the source-data inventory with:

```bash
python3 scripts/check_data_inventory.py
```

This writes a file inventory and checks the 37-input, three-tool Figure 4
table. Figure-specific commands check the calculations and table relationships.

## Export the Prism figures

The repository includes editable Prism projects for Figures 1–7 and the two
supplementary figures. The [figure gallery](figures/README.md) links each
project. The [export record](source_data/prism_exports.json) specifies its
SHA-256 identity and the layout used for the figure.

Prepare an export from the included projects:

```bash
python3 scripts/export_prism_figures.py prepare --work results/prism_export
```

Use a new work directory for each export. Preparation checks the source
identities and creates working copies, an export plan and
`results/prism_export/export.pzc`. Open that script through Prism's
**File → Run Script** command and run it to export the saved layouts.

Check the completed export:

```bash
python3 scripts/export_prism_figures.py verify --work results/prism_export
```

The check compares source and working-copy hashes, validates the exported
images and records their identities. To use a separately saved source directory,
pass `--source-dir "/path/to/CURRENT FIGURES"` to the preparation command.

## Intermediate checkpoints

Restore large FASTQ, BAM, assignment-ledger and sparse-matrix files under
`checkpoints/`, which is excluded from Git. Each workflow specifies its required
filenames, field definitions and SHA-256 identities. Run its counting or metric
programs after restoring those files. The `scripts/revision/` programs build
the complete source tables from these checkpoints.

For RAGE-seq, the [input-order workflow](docs/rage_public_input_order.md)
restores the benchmark read order from the public ENA submission.

## Raw-read workflows

Acquire the sequencing input and references identified in the figure guide,
install its specified software versions, and run the recorded discovery,
demultiplexing and downstream commands. Preserve input headers, sequences,
quality strings and read order when preparing the FASTQ.

Adapt Slurm templates to the cluster's account and CPU partition. Use the
producing run's CPU, memory and time settings, and record the hardware used for
computational benchmarks.

## External input paths

Repository files use paths relative to the repository root. `external_data/`
identifies inputs acquired separately by accession, filename and checksum.
Scripts accept explicit input paths or the following location variables:

| Variable | Default relative to the repository |
|---|---|
| `RAD_DATA_ROOT` | `external_data` |
| `RAD_REVIEWER_ROOT` | `external_data/reviewer_comment_data` |
| `RAD_SCRATCH_ROOT` | `external_data/reviewer_comment_data/scratch_preservation_20260921/files` |
| `RAD_SCRATCH_NFS_ROOT` | Same as `RAD_SCRATCH_ROOT` |

Deposited source tables and small examples use repository-relative paths.

## Preserved software and configurations

The [FLAMES configuration archive](docs/pinned_flames_configs.md) contains the
LR-Split-seq configurations and the exact Figure 6 genome-alignment
configuration, with source versions and hashes. Check those files with:

```bash
python3 scripts/verify_pinned_flames_configs.py
```

ScTagger's [quality-generation record](source_data/figure_02/quality_generation_contract.json)
contains the effective quality-sampling seeds. The
[recorded-seed adapter](scripts/figure_02/generate_with_recorded_seed.py) preserves
those seeds when quality-model files are stored at a different path.

Build the [diagnostic Flexiplex source](vendor/flexiplex-audit/README.md) with a
C++11 compiler. Its helper checks the patch and pre-correction barcode output.
Leave `FLEXIPLEX_AUDIT_SOURCE_FILE` unset for manuscript assignment runs.
