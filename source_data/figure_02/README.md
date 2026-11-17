# Figure 2 source data

[Methods and commands](../../docs/figure_02.md) · [Worked read examples](../../data/examples/figure_02/) · [Table schemas](schemas.json)

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

The November figure uses the [full-catalog RAD run](producing_evidence/assignment_RAD_run.json) and the 3,004-barcode Flexiplex detected list. [RAD assignment summary](assignment_RAD_summary.json) · [November run definitions](../../docs/figure_02.md#assignment-runs-and-plotted-barcode-sets)

## Earlier supplied-list comparison

| File | Contents |
|---|---|
| [assignment_states.tsv](assignment_states.tsv) | Six-state partition of all input reads for each tool |
| [assignment_per_target.tsv](assignment_per_target.tsv) | Native and corrected counts for the RAD truth-list run and BLAZE/Flexiplex detected-list runs |
| [correction_only.tsv](correction_only.tsv) | Corrected-correct and corrected-incorrect counts and their correction-only denominators |
| [plotted_assignment/panel_per_target.tsv.gz](plotted_assignment/panel_per_target.tsv.gz) | The 43,004 observations selected for panels E, G and H, with barcode identity and assignment condition |
| [plotted_assignment/panel_bindings.json](plotted_assignment/panel_bindings.json) | Graph and dataset identities, native CSV hashes and series totals |

The `condition` column distinguishes supplied-list and discovered-list assignments. Flexiplex panels E and G use the 5,000 supplied targets. Panel H uses its 3,004 discovered targets.

## Commands and table generation

`RAD_input_layout.csv` is the supplied layout. `RAD_layout.csv` contains the calibrated layout. [RAD and Flexiplex commands and layouts](plotted_assignment/producing_evidence/)

[RAD counting script](../../scripts/figure_02/summarize_plotted_rad_audit.py) · [State counts](plotted_assignment/RAD_assignment_states.tsv) · [Per-target counts](plotted_assignment/RAD_assignment_per_target.tsv) · [RAD summary](plotted_assignment/RAD_assignment_summary.json) · [Comparison with plotted data](plotted_assignment/checkpoint_validation.json)

Extract the panel tables from a Prism project with:

```bash
python3 scripts/figure_02/extract_plotted_prism.py \
  --prism "external_data/prism/Figure 2.prism" \
  --output-dir results/figure_02/plotted_assignment
```
