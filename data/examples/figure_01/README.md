# Figure 1 examples

Use these files to follow the [Figure 1 timing and spatial calculations](../../../docs/figure_01.md) from source records to table rows.

## Timing example

The example is one complete SN-ONT / RAD / four-thread repetition. Its [discovery command](raw_timing/whitelist_detection/command.sh) and [demultiplexing command](raw_timing/demultiplexing/command.sh) identify the inputs and flags. Parse the two GNU-time logs:

```bash
mkdir -p results
python3 scripts/revision/figures_124_steps/read_gnu_time.py \
  data/examples/figure_01/raw_timing/whitelist_detection/metrics.tsv \
  data/examples/figure_01/raw_timing/demultiplexing/metrics.tsv \
  --output results/figure1_parsed_time.tsv
```

[parsed_gnu_time.tsv](parsed_gnu_time.tsv) shows the expected elapsed seconds and maximum RSS for the two phases. Add the wall times and use the larger maximum RSS for the repetition. [accepted_phase_example.tsv](accepted_phase_example.tsv) shows the source-table fields; [combined_example.tsv](combined_example.tsv) shows combined repetitions.

## Spatial example

[hd_grid_example.tsv](hd_grid_example.tsv) shows how bin IDs map to array rows, columns and tissue-mask values. [hd_stage_example.tsv](hd_stage_example.tsv) gives detection and demultiplexing counts for the same bins. Join by `bin_id`.

The [schema](schema.json) defines fields and units. [Source identities](provenance.json) give file hashes and the row numbers selected for these examples. [Complete source tables](../../../source_data/figure_01/) contain all timing and spatial results.
