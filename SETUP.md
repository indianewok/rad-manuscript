# Setup and analysis

Use the [figure guides](README.md) for the inputs and settings for each analysis.

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

Compare the result with [correction_C6_output.tsv](data/examples/figure_03/correction_C6_output.tsv). The [Figure 3 guide](docs/figure_03.md#longbench-correction-categories) defines the correction categories.

## Work with the complete tables

Open `source_data/figure_XX/README.md` for the file map, field definitions and metric denominators. Follow the corresponding figure guide to count reads, score barcode lists or calculate cell-level results. Figure images are displayed in the [gallery](figures/README.md).

## Process raw reads

Place raw inputs and references under `external_data/`, and assignment tables, alignments and matrices under `checkpoints/`. Use the paths in the figure commands and the accessions in the [dataset registry](manifests/datasets.tsv).

Preserve FASTQ identifiers, sequences, qualities and read order. The [RAGE-seq input guide](docs/rage_public_input_order.md) gives the commands to restore the benchmark order. Set the Slurm account, partition, memory and time for your cluster when using a submission script.

<details>
<summary>Configure external input locations</summary>

Scripts accept explicit input paths or these environment variables.

| Variable | Default relative to this repository |
|---|---|
| `RAD_DATA_ROOT` | `external_data` |
| `RAD_REVIEWER_ROOT` | `external_data/reviewer_comment_data` |
| `RAD_SCRATCH_ROOT` | `external_data/reviewer_comment_data/scratch_preservation_20260921/files` |
| `RAD_SCRATCH_NFS_ROOT` | Same as `RAD_SCRATCH_ROOT` |

</details>

## Pinned processing code

- Flexiplex source, patch, build commands and pre-correction barcode output. [Custom Flexiplex](vendor/flexiplex-audit/README.md)
- LR-Split-seq demultiplexing and LongBench alignment. [FLAMES configurations](docs/pinned_flames_configs.md)
- Badread models and effective sampling seeds. Use the seed adapter when the model files move. [ScTagger quality generation](source_data/figure_02/quality_generation_contract.json) · [Recorded-seed adapter](scripts/figure_02/generate_with_recorded_seed.py)
