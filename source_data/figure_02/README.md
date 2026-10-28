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
are moved; all per-read seed calculations remain unchanged. The complete
retained FASTQ identities are verified in
[the input report](../../validation/figures_124_fastq_identity.json).
The historical `sample_replay_evidence.jsonl.gz` file is missing from its recorded
location.

The complete-dataset barcode-quality analyses are described separately for
[Nanopore2018](full_read_quality_2018/README.md) and
[Nanopore2023](full_read_quality/README.md).

## Read assignments

`assignment_six_states.tsv` partitions all 4,993,805 physical reads for each
tool. RAD excludes IDs with multiple output records. Flexiplex collapses
repeated assignments to the same target and excludes IDs assigned to different
targets. Ambiguous BLAZE matcher records remain unassigned.

`assignment_per_target.tsv` records selected-list and truth-set membership;
counts are blank for unselected targets. Recounting the retained read-level
records reproduces all 52,076 selected-target category values. The
[assignment report](../../validation/figures_124_assignment_resume.json) gives
the source hashes and command.

`correction_only.tsv` uses corrected-correct plus corrected-incorrect reads as
its denominator. BLAZE selected 15 targets outside the truth set, containing
908 incorrect corrections and 183 native incorrect assignments. Restricting
incorrect corrections to truth-set targets removes those 908 events.
