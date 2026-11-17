# Figure 4 source data

Figure 4 compares barcode discovery across 37 sequencing inputs. [Methods and commands](../../docs/figure_04.md)

| Item | Files | Contents |
|---|---|---|
| Sequencing inputs | [sample_inventory.tsv](sample_inventory.tsv), [input_characteristics.tsv](input_characteristics.tsv) | Libraries, run identifiers, and SeqKit summaries, including `AvgQual`. |
| Discovery settings | [tool_parameters.tsv](tool_parameters.tsv), [run_records/](run_records/), [producing_evidence/](producing_evidence/) | Tool flags and versions, input FASTQs, chemistry catalogs, and scoring references. |
| Discovery outputs | [producing_run_evidence.tsv](producing_run_evidence.tsv) | Source tables and paths to selected barcode lists. |
| Barcode scores | [barcode_detection_metrics.tsv](barcode_detection_metrics.tsv) | Calls, reference size, TP, FP, FN, precision, recall, and F1. |
| Figure values | [plotted_checkpoint/plotted_metrics.tsv](plotted_checkpoint/plotted_metrics.tsv) | 111 observations across 37 inputs and three tools. |
| Flexiplex settings | [flexiplex_selected_conditions.tsv](plotted_checkpoint/flexiplex_selected_conditions.tsv) | 22 inputs use flank distance zero, and 15 use flank distance eight. |
| Statistical results | [Paired tables](plotted_checkpoint/), [Friedman](plotted_checkpoint/friedman.tsv), [Dunn](plotted_checkpoint/dunn.tsv) | Input-matched metrics and test results. |

The comparison includes 87 observations from public inputs and 24 from controlled-access Visium inputs. [ScMixology2 commands](../../scripts/figure_04/scmixology2/README.md) · [ERR15095097 scoring record](reference_scoring/ERR15095097.json)

The plotted data folder also contains the original Prism CSV tables. [Panel sources](plotted_checkpoint/panel_bindings.json) · [Medians and test settings](plotted_checkpoint/checkpoint_summary.json)

Check the supplied figure values.

```bash
python3 scripts/figure_04/extract_plotted_prism.py --validate-only \
  --output-dir source_data/figure_04/plotted_checkpoint
```

Extract the figure values from a local Prism project.

```bash
python3 scripts/figure_04/extract_plotted_prism.py \
  --prism "external_data/prism/Figure 4.prism" \
  --producer-metrics source_data/figure_04/barcode_detection_metrics.tsv \
  --output-dir results/figure_04/plotted_checkpoint
```
