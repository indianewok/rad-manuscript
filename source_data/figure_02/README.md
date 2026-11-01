# Figure 2 source data

These tables connect the ScTagger-L source barcodes, native tool outputs, and datasets selected in the saved manuscript Prism layout. The [Figure 2 workflow](../../docs/figure_02.md) gives the generation, discovery, assignment, and counting procedures.

## Plotted checkpoint

| File | Content |
|---|---|
| `plotted_assignment/discovery_condition_plotted.tsv` | Native Nanopore2023 TP, FP, FN, precision, recall, and F1 for panels B and C |
| `assignment_states.tsv` | Six-state partition of all 4,993,805 input reads for each tool |
| `assignment_per_target.tsv` | Native and corrected assignment counts for the RAD truth-list run and the BLAZE/Flexiplex detected-list runs |
| `correction_only.tsv` | Corrected-correct and corrected-incorrect counts and their correction-only denominators |
| `plotted_assignment/panel_per_target.tsv.gz` | The 43,004 observations selected for panels E, G, and H, with barcode identity and assignment condition |
| `plotted_assignment/panel_bindings.json` | Source Prism hash, layout, graph and dataset identifiers, native CSV hashes, and series totals |

Native-correct, corrected-correct, native-incorrect, and corrected-incorrect reads each require one emitted record for the original input read. Reads with multiple outputs are counted separately in `multiple_outputs_excluded`. `unassigned` contains input reads with no emitted output. The six states sum to the complete input.

Panel E and panel G use the supplied-5,000-target Flexiplex run; panel H and the Flexiplex total bars use its 3,004-target detected-list run. The `condition` field in the panel checkpoint identifies each series. The BLAZE per-barcode distributions use its 5,000 truth targets, while assignment totals also include its fifteen additional selected targets.

## Producing records

`plotted_assignment/producing_evidence/` contains the RAD command, layout, source commit, binary and input hashes, and the fixed-list Flexiplex command and provenance. RAD received the same 5,000 truth barcodes as its global and custom lists. `RAD_input_layout.csv` is the command input; `RAD_layout.csv` is the calibrated output layout. Command paths use portable `external_data` and `results` roots; the manifest retains original file hashes alongside the archived-copy hashes. The accompanying patch is the git-format-patch representation of commit `24d5ce47`, already included in that commit.

The complete RAD audit is summarized by `scripts/figure_02/summarize_plotted_rad_audit.py`. Its outputs are `RAD_assignment_states.tsv`, `RAD_assignment_per_target.tsv`, and `RAD_assignment_summary.json` under `plotted_assignment/`. `checkpoint_validation.json` records comparison of the recomputed counts with the plotted series.

The deposited panel checkpoint supplies the plotted observations. To refresh it from a local author project:

```bash
python3 scripts/figure_02/extract_plotted_prism.py \
  --prism "external_data/prism/Figure 2.prism" \
  --output-dir results/figure_02/plotted_assignment
```

## Input quality and discovery records

`discovery_condition_plotted.tsv` under `plotted_assignment/` selects the native Nanopore2023 condition. `discovery_callset_manifest.tsv` and `discovery_barcode_identities.tsv.gz` identify the selected barcode lists and their comparison with the source barcodes. `quality_generation_contract.json` and `generation_environment.tsv` define the generator and random streams. The native Nanopore2023 row in `quality_summary.tsv` records the complete input's base and barcode quality means.
