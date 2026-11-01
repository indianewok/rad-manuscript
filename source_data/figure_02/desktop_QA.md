# Figure 2 data checks

The current RAD assignment uses the complete 6,794,880-barcode Cell Ranger catalogue and the supplied 5,000-barcode custom truth list. The [execution record](producing_evidence/assignment_RAD_run.json) identifies the exact binary, input, layout and both barcode lists.

## Assignment tables

Each tool's five-state partition sums to 4,993,805 physical reads. RAD per-target rows cover the 5,000 supplied truth targets; every emitted outside-custom target is reported separately. Flexiplex has 3,004 native selected targets. BLAZE has 5,015 selected targets, including 15 outside the truth set. Unselected truth targets are blank; a selected target with no reads in a category has zero.

Correction-only fractions use corrected-correct plus corrected-incorrect reads:

| Tool | Corrected assignments | Correct (%) | Incorrect (%) |
|---|---:|---:|---:|
| RAD | 2,026,363 | 91.14 | 8.86 |
| Flexiplex | 1,680,396 | 83.24 | 16.76 |
| BLAZE | 2,014,432 | 93.39 | 6.61 |

[Assignment counts](assignment_states.tsv), [per-target counts](assignment_per_target.tsv) and [correction proportions](correction_only.tsv) provide the complete numerical inputs. The separately labelled Flexiplex full-truth reference increment remains 222,371 reads.

## Plotting and editable project

The deposited source tables preserve the values used in the graphs and layouts. The repository plots are rendered from these source tables with [plot_data.py](../../scripts/figure_02/plot_data.py).

Existing statistical methods and quality-sweep inputs are retained. The [Figure 2 guide](../../docs/figure_02.md) provides the experiment and reproduction commands.
