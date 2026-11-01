# Setup and analysis

Choose a figure in the [repository guide](README.md). Its methods list the datasets, software versions, command-line flags and calculations.

## Install the table-analysis environment

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r environments/render-python311.lock.txt
source .venv/bin/activate
```

Run commands from the repository root. The figure guides specify the separate R, demultiplexing and alignment environments used to process raw data.

## Start with a small example

Each `data/examples/figure_XX/` directory shows input records and expected results. For example, calculate LongBench correction percentages with:

```bash
mkdir -p results
python3 scripts/revision/figure_3_example_percent.py   data/examples/figure_03/correction_C5_input.tsv   results/correction_percent.tsv
```

Compare the result with [correction_C6_output.tsv](data/examples/figure_03/correction_C6_output.tsv). FM1 counts reassignment between cell-associated reference barcodes; FM2 counts reassignment from catalog-valid barcodes outside the cell reference.

## Work with the complete tables

Open `source_data/figure_XX/README.md` for the file map, field definitions and metric denominators. Follow the corresponding figure guide to count reads, score barcode lists or calculate cell-level results. Figure images are displayed in the [gallery](figures/README.md).

## Process raw reads

1. Download the input and references listed in the [dataset registry](manifests/datasets.tsv) and figure guide.
2. Install the specified tool builds and dependencies.
3. Run the recorded discovery, demultiplexing and downstream commands.
4. Apply the counting script to the output and compare its result with the source table.

Keep original FASTQ identifiers, sequences, qualities and read order. The [RAGE-seq input guide](docs/rage_public_input_order.md) reconstructs the benchmark order from the public ENA reads.

Large inputs use `external_data/`; intermediate assignment tables, alignments and matrices use `checkpoints/`. The figure guides give their filenames and input identities. Slurm templates take the account, CPU partition, memory and time appropriate to the cluster. Computational benchmarks also record the hardware and thread count.

<details>
<summary>Configure external input locations</summary>

Scripts accept explicit input paths or these environment variables:

| Variable | Default relative to this repository |
|---|---|
| `RAD_DATA_ROOT` | `external_data` |
| `RAD_REVIEWER_ROOT` | `external_data/reviewer_comment_data` |
| `RAD_SCRATCH_ROOT` | `external_data/reviewer_comment_data/scratch_preservation_20260921/files` |
| `RAD_SCRATCH_NFS_ROOT` | Same as `RAD_SCRATCH_ROOT` |

</details>

## Pinned processing code

- [Custom Flexiplex](vendor/flexiplex-audit/README.md): source, patch, build commands and a pre-correction barcode example.
- [FLAMES configurations](docs/pinned_flames_configs.md): exact LR-Split-seq and LongBench alignment code.
- [ScTagger quality generation](source_data/figure_02/quality_generation_contract.json): models and effective sampling seeds. The [recorded-seed adapter](scripts/figure_02/generate_with_recorded_seed.py) applies those seeds when model files move.
