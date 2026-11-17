# Figure 1 examples

## Timing example

Parse the GNU-time logs from one four-thread RAD repetition on SN-ONT. The [discovery](raw_timing/whitelist_detection/command.sh) and [demultiplexing](raw_timing/demultiplexing/command.sh) commands give the inputs and flags.

```bash
mkdir -p results
python3 scripts/revision/figures_124_steps/read_gnu_time.py \
  data/examples/figure_01/raw_timing/whitelist_detection/metrics.tsv \
  data/examples/figure_01/raw_timing/demultiplexing/metrics.tsv \
  --output results/figure1_parsed_time.tsv
```

Add the two wall times and use the larger maximum RSS. [Parsed four-thread logs](parsed_gnu_time.tsv) · [16-thread phase records](accepted_phase_example.tsv) · [Combined 16-thread repetitions](combined_example.tsv)

## Spatial example

[hd_grid_example.tsv](hd_grid_example.tsv) shows how bin IDs map to array rows, columns and tissue-mask values. [hd_stage_example.tsv](hd_stage_example.tsv) gives detection and demultiplexing counts for the same bins. Join by `bin_id`.

[Figure 1 guide](../../../docs/figure_01.md) · [Complete tables](../../../source_data/figure_01/) · [Fields and units](schema.json) · [Source files and rows](provenance.json)
