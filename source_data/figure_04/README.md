# Figure 4 source data

All 37 RAD discovery results use RAD 1.0.2 at commit
`4acbe004ba11b150d6832395452632f367a6e6c1`, explicit adapter error `0.3`,
and the complete selected input.

The `command` column shows the analysis flags with defaults omitted; threads and chemistry have separate columns. Flexiplex’s preset default is `-f 8`; `-f 0` remains explicit when used. The [run records](run_records/) and [producing evidence](producing_evidence/) retain the full commands and settings.

- [Tool versions and flags](tool_parameters.tsv): all 111 input–tool records, with seven columns.
- [Metrics](barcode_detection_metrics.tsv): calls, reference size, TP, FP, FN, precision, recall and F1 for each input and tool.
- [Friedman](friedman.tsv) and [Dunn](dunn.tsv) results: the existing tests recalculated from all 37 paired inputs.
- [Run records](run_records/): per-dataset RAD input identities, full chemistry catalogues and matched references.
- [Current RAD execution records](producing_evidence/current_RAD/): build hashes, commands and counts.
- [Sample inventory](sample_inventory.tsv): the 37 inputs and their library, donor and run relationships.
- [Input characteristics](input_characteristics.tsv): saved all-read SeqKit summaries.

`paired_precision.tsv`, `paired_recall.tsv` and `paired_f1.tsv` share the same
37 input IDs. The [Figure 4 guide](../../docs/figure_04.md) explains reference
definitions and walks from one native command through barcode-set scoring to
the displayed metrics. BLAZE and Flexiplex settings are given separately for
each input. ScMixology2 uses complete-input native runs for all three tools; [its commands](../../scripts/figure_04/scmixology2/README.md) and [execution records](producing_evidence/current_ScMixology2/) give the pinned versions and outputs.

Synthetic references contain known source barcodes. Biological references use
matched filtered short-read barcodes or published spatial masks. The RAGE
lymph-node reference contains 5,978 barcodes annotated as T/B-containing.
The guide describes the unresolved ERR15095097 sample/reference pairing.

The comparison contains 87 observations from public inputs and 24 from
controlled-access Visium inputs. Complete barcode lists are external inputs.
`AvgQual` retains SeqKit's summary-field definition; the original SeqKit
invocation and version are unavailable. ScTagger S/L use uniform Q20 scores.
