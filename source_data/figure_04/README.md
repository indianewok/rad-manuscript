# Figure 4 source data

Start with the [Figure 4 guide](../../docs/figure_04.md) for the 37 inputs, barcode references, software settings and read-to-score commands.

| Step | Files | What to inspect |
|---|---|---|
| Identify an input | [sample_inventory.tsv](sample_inventory.tsv), [input_characteristics.tsv](input_characteristics.tsv) | Dataset, library, sequencing run and all-read SeqKit summaries; `AvgQual` is the SeqKit average-quality field. |
| Read the command | [tool_parameters.tsv](tool_parameters.tsv), [run_records/](run_records/), [producing_evidence/](producing_evidence/) | Tool version, command flags, FASTQ, chemistry catalog, scoring reference and output barcode list. |
| Inspect barcode-set scores | [barcode_detection_metrics.tsv](barcode_detection_metrics.tsv) | Native-run calls, reference size, TP, FP, FN, precision, recall and F1. |
| Read the figure values | [plotted_checkpoint/plotted_metrics.tsv](plotted_checkpoint/plotted_metrics.tsv) | 111 input–tool observations: 37 matched inputs × three tools. |
| Follow the Flexiplex selection | [flexiplex_selected_conditions.tsv](plotted_checkpoint/flexiplex_selected_conditions.tsv) | The higher recorded F1 selects f0 or f8; the same condition supplies precision and recall. There are 22 f0 and 15 f8 selections. |
| Compare tools | [paired tables](plotted_checkpoint/), [Friedman](plotted_checkpoint/friedman.tsv), [Dunn](plotted_checkpoint/dunn.tsv) | Input-matched F1, precision and recall, followed by Friedman tests and two RAD-versus-comparator Dunn comparisons per metric. |

All RAD results use **1.0.2, commit `4acbe004ba11b150d6832395452632f367a6e6c1`, adapter error 0.3 and complete inputs**. [ScMixology2](../../scripts/figure_04/scmixology2/README.md) uses complete-input native runs for all three tools. ScTagger-S/L retain uniform Q20; biological inputs retain their native qualities.

TP is a selected barcode in the matched reference. FP is a selected barcode outside that reference. FN is a reference barcode absent from the selected set. Precision is `TP/(TP+FP)`, recall is `TP/(TP+FN)` and F1 is `2TP/(2TP+FP+FN)`.

Synthetic references contain known source barcodes. Biological references use matched filtered short-read barcodes, deposited targetable-cell annotations or published spatial masks. The RAGE lymph-node reference contains 5,978 T/B-containing barcodes. ERR15095097 uses the MPNST1 reference specified in its [scoring record](reference_scoring/ERR15095097.json). The comparison includes 87 observations from public inputs and 24 from controlled-access Visium inputs.

The figure's paired and modality tables contain the same 333 metric values. [Panel bindings](plotted_checkpoint/panel_bindings.json) identify the source tables and graphs; [checkpoint_summary.json](plotted_checkpoint/checkpoint_summary.json) gives the medians, selected conditions and statistical settings. The folder also includes the native Prism CSV tables.

Check the figure values directly:

```bash
python3 scripts/figure_04/extract_plotted_prism.py --validate-only \
  --output-dir source_data/figure_04/plotted_checkpoint
```

To extract them from a local Prism project:

```bash
python3 scripts/figure_04/extract_plotted_prism.py \
  --prism "external_data/prism/Figure 4.prism" \
  --producer-metrics source_data/figure_04/barcode_detection_metrics.tsv \
  --output-dir results/figure_04/plotted_checkpoint
```
