# Figure 4 source data

The [Figure 4 workflow](../../docs/figure_04.md) connects the 37 sequencing inputs, barcode references, native discovery runs, and plotted comparisons.

## Plotted comparison

`plotted_checkpoint/` contains the exact saved manuscript observations:

- `plotted_metrics.tsv`: 111 input–tool observations and 333 precision, recall, and F1 values.
- `paired_f1.tsv`, `paired_precision.tsv`, and `paired_recall.tsv`: the 37 matched input rows, with canonical IDs and displayed names.
- `flexiplex_selected_conditions.tsv`: recorded f0/f8 F1 values and the condition selected for each input. The higher recorded F1 supplies the displayed condition; 22 inputs use f0 and 15 use f8.
- `f1_native.csv`, `precision_native.csv`, `recall_native.csv`, and `flexiplex_variants_native.csv`: unchanged native Prism CSV checkpoints. The `*_modality_native.csv` tables retain the transposed values used by the fifteen modality graphs.
- `friedman.tsv` and `dunn.tsv`: the matched comparisons recalculated from the plotted values; native Prism statistical-result CSVs are retained beside them.
- `panel_bindings.json`: source Prism hash, layout, graph and dataset identifiers, native table hashes, and output hashes.
- `checkpoint_summary.json`: input counts, arithmetic checks, selected conditions, medians, and statistical settings.

Regenerate these checkpoints and statistics with:

```bash
python3 scripts/figure_04/extract_plotted_prism.py \
  --prism "external_data/prism/Figure 4.prism" \
  --producer-metrics source_data/figure_04/barcode_detection_metrics.tsv \
  --output-dir results/figure_04/plotted_checkpoint
python3 scripts/figure_04/extract_plotted_prism.py --validate-only \
  --output-dir results/figure_04/plotted_checkpoint
```

## Native producing records

`barcode_detection_metrics.tsv` retains the calls, reference sizes, TP, FP, and FN from its recorded producing runs. `tool_parameters.tsv`, `run_records/`, and `producing_evidence/` retain their software identities, full commands, and outputs. The top-level paired/statistical tables summarize those producing-run metrics. The manuscript layout's selected Flexiplex conditions are recorded separately in `plotted_checkpoint/`; `producer_comparison.tsv` identifies the changed metric values. Producer counts are preserved without inferring replacement counts from rounded plot values.

All 37 RAD results use RAD 1.0.2 at commit `4acbe004ba11b150d6832395452632f367a6e6c1`, adapter error `0.3`, and the complete selected input. ScMixology2 uses complete-input native runs for all three tools; [its workflow](../../scripts/figure_04/scmixology2/README.md) records the pinned commands and outputs.

Synthetic references contain known source barcodes. Biological references use matched filtered short-read barcodes, deposited targetable cell annotations, or published spatial masks. The RAGE lymph-node reference contains 5,978 T/B-containing barcodes. The guide identifies the MPNST1 reference used for ERR15095097.

`sample_inventory.tsv` identifies all 37 inputs. `input_characteristics.tsv` supplies the saved all-read SeqKit summaries; `AvgQual` follows the source SeqKit field. ScTagger S/L use uniform Q20. The comparison includes 87 observations from public inputs and 24 from controlled-access Visium inputs; complete barcode lists remain external inputs.
