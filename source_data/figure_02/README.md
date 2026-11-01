# Figure 2 source data

The [Figure 2 guide](../../docs/figure_02.md) lists the software versions and commands, then follows the ScTagger-L reads through quality generation, discovery, assignment and counting. There are 4,993,805 input reads from 5,000 known source barcodes.

## Inputs and barcode discovery

| File | Contents |
|---|---|
| [plotted_assignment/discovery_condition_plotted.tsv](plotted_assignment/discovery_condition_plotted.tsv) | Native Nanopore2023 TP, FP, FN, precision, recall and F1 for panels B/C |
| [discovery_callset_manifest.tsv](discovery_callset_manifest.tsv) | Selected barcode lists and their hashes |
| [discovery_barcode_identities.tsv.gz](discovery_barcode_identities.tsv.gz) | Selected barcode sequences and their comparison with the known source barcodes |
| [quality_generation_contract.json](quality_generation_contract.json) and [generation_environment.tsv](generation_environment.tsv) | Generator settings, versions and random streams |
| [quality_summary.tsv](quality_summary.tsv) | Whole-input and barcode quality means, including the native Nanopore2023 condition |

The complete quality-sweep calculations are described in the [Nanopore2023](full_read_quality/) and [Nanopore2018](full_read_quality_2018/) guides.

## Read assignment: panels D–H

| File | Contents |
|---|---|
| [assignment_states.tsv](assignment_states.tsv) | Six-state partition of all input reads for each tool |
| [assignment_per_target.tsv](assignment_per_target.tsv) | Native and corrected counts for the RAD truth-list run and BLAZE/Flexiplex detected-list runs |
| [correction_only.tsv](correction_only.tsv) | Corrected-correct and corrected-incorrect counts and their correction-only denominators |
| [plotted_assignment/panel_per_target.tsv.gz](plotted_assignment/panel_per_target.tsv.gz) | The 43,004 observations selected for panels E, G and H, with barcode identity and assignment condition |
| [plotted_assignment/panel_bindings.json](plotted_assignment/panel_bindings.json) | Graph and dataset identities, native CSV hashes and series totals |

Native-correct, corrected-correct, native-incorrect and corrected-incorrect reads each require exactly one emitted record for the original read. `multiple_outputs_excluded` counts original reads with more than one output. `unassigned` counts input reads without an emitted output. The six states sum to 4,993,805.

Flexiplex panels E/G use all 5,000 supplied truth targets. Its panel H distribution and total bars use the 3,004-target detected list. The `condition` field identifies each series. BLAZE per-barcode distributions use its 5,000 truth targets; total assignment counts also include its fifteen additional selected targets.

## Commands and table generation

The [run files](plotted_assignment/producing_evidence/) contain RAD's native command, source commit, binary and input hashes, supplied lists and layouts, plus the fixed-list Flexiplex command. RAD received the same 5,000 truth barcodes as its global and custom lists. `RAD_input_layout.csv` is the command input; `RAD_layout.csv` is the calibrated output. Command paths use `external_data` and `results` roots.

[Summarize the RAD read audit](../../scripts/figure_02/summarize_plotted_rad_audit.py) to produce [RAD_assignment_states.tsv](plotted_assignment/RAD_assignment_states.tsv), [RAD_assignment_per_target.tsv](plotted_assignment/RAD_assignment_per_target.tsv) and [RAD_assignment_summary.json](plotted_assignment/RAD_assignment_summary.json). [checkpoint_validation.json](plotted_assignment/checkpoint_validation.json) compares those counts with the plotted series.

Extract the panel tables from a Prism project with:

```bash
python3 scripts/figure_02/extract_plotted_prism.py \
  --prism "external_data/prism/Figure 2.prism" \
  --output-dir results/figure_02/plotted_assignment
```

The [worked read examples](../../data/examples/figure_02/) show the raw barcode fields and their classifications. [Table schemas](schemas.json) define the metrics and counting units.
