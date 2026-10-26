# Run the readable analysis steps

Begin with the [figure walkthrough](README.md) for the panel of interest. The
small scripts show their expected columns and write inspectable TSV/CSV outputs.
Most counting examples use only the Python standard library. Plotting and the
full matrix checks require a scientific Python environment.

## Portable render environment

The independent render check uses Python 3.11 and this exact dependency lock:

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r environments/render-python311.lock.txt
```

Use `.venv/bin/python` in the walkthrough commands if your default `python3`
selects a different environment. Limit numerical-library threads for small
checks with `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`.
The initial HPC verification used the system Python3.6.8 environment; it is
recorded in the run receipts and is not silently substituted for tool-producer
versions. R/Seurat are needed only for the explicitly named RDS inspection or
producer steps, not for reading TSVs or rendering their Python proofs.

## Three starting points

1. **Read or run an example.** `data/examples/figure_XX/` includes actual bounded
   source records, source hashes, selection rules and expected outputs. These
   examples explain an operation; they are not full reproduction evidence.
2. **Resume a checkpoint.** Restore the current checkpoints listed by the
   figure's manifest, verify their hashes, then run the linked count/metric
   scripts. The full source tables are in `source_data/figure_XX/`.
3. **Run from raw reads.** Follow the exact producing-run parameters in the
   figure guide. The raw input, reference, supplied list and software pins are
   all dependencies. A path existing is not proof of identity; check its hash.

The supplementary `scripts/revision/` commands reconstruct and validate full
checkpoint tables. They are implementation aids; the numbered figure-specific
steps and column examples are the main explanation.

## Current checkpoints and local paths

Large FASTQs, BAMs, read ledgers and MEX files are not committed to Git.
`checkpoints/` is ignored. Exact retained locations/hashes and acquisition
identifiers appear in the figure manifests. On this HPC installation,
`/Volumes/rad_data` maps to
`/dartfs/rc/lab/A/AckermanLab/CMV/rad_data`; this mapping does not alter source
identity. For ScTagger quality generation, the original literal model pathname
is part of the effective RNG seed and must be preserved as data, not rewritten.

Do not put home-directory paths into a reproducibility command without declaring
what asset they identify. The compact deposited source tables and examples can
be read independently of HPC paths.

## Restore a supplied checkpoint archive

The [release guide](docs/release_review.md) names the separate checkpoint,
software and RAGE read-order archives. They are prepared for review; an archive
being staged locally does not mean it has been published. The source tables and
small examples in Git remain usable without them.

After obtaining the archive and its SHA-256 manifest, verify the checksum before
extracting it. From the repository root, restore only its checkpoint payload:

```bash
tar -tzf /path/to/rad-manuscript-checkpoints-05.tar.gz
tar -xzf /path/to/rad-manuscript-checkpoints-05.tar.gz \
  --strip-components=1 --wildcards 'rad-manuscript/checkpoints/*'
```

Use the corresponding archive name for Figures 3, 6/7, HD, RAGE software or RAGE
read order. Each figure's checkpoint manifest records the resulting relative
paths and exact hashes. For a raw RAGE replay, follow the
[public-input reconstruction](docs/rage_public_input_order.md) before running
the tools; the ENA file has a different read order.

## CPU jobs on Dartmouth Discovery

Inspect the live partition hardware before submission. Current validation used
`standard`, whose nodes reported no GPU GRES, with account `lsonglab`, explicit
CPU/memory/time requests and `--gres=gpu:0`. The account permits/defaults to
`lsonglab_gpu`; the CPU-only partition is the placement safeguard. Do not route
CPU-only jobs to a02 or unrestricted `preempt_lsong`. Example scripts record
resources per job; old dependency IDs are never reused.

## Custom Flexiplex

[The pinned diagnostic source](vendor/flexiplex-audit/README.md) builds offline
with a C++11 compiler. `build_and_check.py` verifies the exact patch and tests
pre-correction barcode output. `FLEXIPLEX_AUDIT_SOURCE_FILE` must be unset for
manuscript assignment runs.
