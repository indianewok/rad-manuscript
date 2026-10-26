# Figure 4 barcode lists

These files contain the selected tool barcodes and matched reference barcodes
for 29 public inputs, covering 87 input–tool comparisons. Each gzip file contains
sorted, unique 16-nucleotide barcodes, one per line, without a header. Terminal
Cell Ranger `-1` suffixes are removed. Identical sets are stored once and can be
referenced by several manifest rows.

The [identifier manifest](identifier_manifest.tsv) maps all 111 comparisons to
their files and SHA-256 hashes. The eight controlled-access Visium inputs have
24 rows marked `aggregate-only-controlled-access`. Their aggregate metrics are
included in the source tables, and the dataset registry gives the EGA access
identifiers.

The [source and equality report](../../validation/figures_124_public_identifier_export.json)
records the original file identities, selection rules, normalized-content
hashes and TP/FP/FN counts. The RAGE immune reference contains 5,978 barcodes
selected from the membership table. ScMixology2 retains native RAD calls and
reconstructed BLAZE/Flexiplex calls, as described in the [Figure 4 guide](../../docs/figure_04.md).

## Recalculate the metrics

Run from the repository root with Python 3.9 or newer:

```bash
python3 scripts/revision/figures_124_steps/rescore_public_identifiers.py \
  --output /tmp/figure4_identifier_rescore.tsv
```

The scorer verifies file hashes, calculates TP/FP/FN by set intersection and
difference, and compares the results with the saved metrics. Counts must match
exactly; precision, recall and F1 must agree within `1e-9`. The output contains
87 recalculated public comparisons and 24 retained controlled-access aggregate
rows. Counts are numbers of barcodes; precision, recall and F1 are fractions.

To inspect a complete barcode list:

```bash
gzip -dc data/figure_04/identifier_sets/ScTagger-S_flatQ20.RAD.txt.gz
```

To repeat extraction from the project files:

```bash
python3 scripts/revision/figures_124_export_public_sets.py \
  --project-root /path/to/rad_data --output-root .
```

This extraction uses the recorded project and scratch locations for the
Measles and ScMixology2 sources. Four original Visium RAD callsets are missing
from their recorded paths; their aggregate metrics and recorded hashes remain
in the source tables.
