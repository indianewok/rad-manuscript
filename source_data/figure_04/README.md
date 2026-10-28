# Figure 4 source data

The [Figure 4 guide](../../docs/figure_04.md) describes barcode discovery across
37 sequencing inputs. `barcode_detection_metrics.tsv` contains three matched
tool observations per input, for 111 rows. Counts satisfy `calls = TP + FP`
and `reference_n = TP + FN`; precision, recall and F1 are calculated from these
barcode-set comparisons.

## Reference sets and barcode calls

The RAGE lymph-node reference contains 5,978 barcodes annotated as T/B-containing.
All 30 Tilgner callsets use donor-matched references.
Four original Visium RAD callsets are missing from their temporary locations;
their metrics and recorded hashes are retained.

ScMixology2 combines native RAD calls with a BLAZE expected-500 selector replay
and a Flexiplex filter replay on common RAD counts. All three sets are rescored
against the reference, and RAD calls are checked against the retained RDS.

Complete public barcode lists and references are in
[data/figure_04](../../data/figure_04/README.md). The portable scorer reproduces
all 87 public input–tool comparisons. The other 24 rows contain aggregate
metrics for controlled-access Visium inputs.

## Paired metrics and input characteristics

`paired_precision.tsv`, `paired_recall.tsv` and `paired_f1.tsv` share the same
37 input IDs. Each observation is a sequencing input, including individual
technical libraries and runs.

`input_characteristics.tsv` joins the saved 37-row all-read SeqKit summary to
the canonical input IDs. `AvgQual` retains the SeqKit summary-field definition.
The ScTagger S/L inputs use uniform Q20 qualities. The original SeqKit invocation
and version are absent from the retained execution records.
