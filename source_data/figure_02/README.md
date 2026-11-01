# Figure 2 source data


The [Figure 2 guide](../../docs/figure_02.md) describes the ScTagger quality
sweeps, barcode discovery and read-assignment analysis.

## Barcode discovery and quality scores

`discovery_metrics.tsv` contains 144 tool–condition observations: 96 for the
Nanopore2018 S/L grid and 48 for the Nanopore2023 L grid. Uniform-Q20 controls
are recorded separately. Each selected barcode list is compared with the
corresponding ScTagger truth set. `discovery_callset_manifest.tsv` records file
hashes and sources; `discovery_barcode_identities.tsv.gz` lists every TP, FP and
FN barcode.

The paired quality sample contains 50,000 unique reads spanning all 5,000 L
source barcodes. `quality_summary.tsv`, `reconstructed_full_quality_histograms.tsv`
and `matched_quality_levels.tsv` record sample means and standard deviations,
per-base quality counts and the eleven matched whole-dataset means. Shifts and
clipping are applied to individual base scores before averages are calculated.

The [generation contract](quality_generation_contract.json) specifies the S/L
base seeds, model hashes and effective quality-tape seeds. The
[recorded-seed adapter](../../scripts/figure_02/generate_with_recorded_seed.py)
replaces only the quality-tape seed with its recorded integer when model files
are moved; all per-read seed calculations remain unchanged.

The complete-dataset barcode-quality analyses are described separately for
[Nanopore2018](full_read_quality_2018/README.md) and
[Nanopore2023](full_read_quality/README.md).

## Read assignments

`assignment_states.tsv` partitions all 4,993,805 physical reads for each tool
into five states. Unassigned reads have no retained assignment.

`assignment_per_target.tsv` records selected-list and truth-set membership;
counts are blank for unselected targets.

`correction_only.tsv` uses corrected-correct plus corrected-incorrect reads as
its denominator. BLAZE selected 15 targets outside the truth set, containing
908 incorrect corrections and 183 native incorrect assignments. Restricting
incorrect corrections to truth-set targets removes those 908 events.

RAD uses the full 6,794,880-barcode Cell Ranger catalogue with its supplied 5,000-barcode custom list. [Execution details](producing_evidence/assignment_RAD_run.json) and the [literal command](producing_evidence/assignment_RAD_command.sh) identify both lists. `assignment_RAD_summary.json` records the complete physical-read audit. RAD per-target rows describe the 5,000 supplied truth targets; `assignment_RAD_outside_custom_per_target.tsv` separately reports all emitted targets outside that list. The five-state totals include all retained assignments.
