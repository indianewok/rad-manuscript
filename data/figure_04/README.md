# Figure 4 selected public identifier sets

These are the actual saved selected barcode identifiers and matched reference identifiers for **29 public inputs, 87 input/tool rows**. Each gzip file contains sorted unique 16-nucleotide identifiers, one per line, without a header. Terminal Cell Ranger `-1` suffixes are removed. Identical sets are stored once and can be referenced by multiple manifest rows.

[identifier_manifest.tsv](identifier_manifest.tsv) maps all 111 selected rows to their current files and SHA256 hashes. Eight controlled-access Visium inputs (24 tool rows) remain explicitly `aggregate-only-controlled-access`; their identifier files are not published. Four of those original RAD callsets are also missing at their recorded paths. No selected set was inferred from aggregate counts.

[Full source lineage and equality checks](../../validation/figures_124_public_identifier_export.json) give the original source path/hash, exact selection rule, normalized-content hash, and TP/FP/FN for every public row. Membership-table selections are recorded explicitly, including the 5,978-barcode RAGE immune reference. ScMixology2 retains its native RAD and reconstructed BLAZE/Flexiplex execution origins. These identifiers are computational barcode sets, not raw sequencing reads.

Run from the repository root using Python 3.9 or newer; no scientific Python packages or mounted project files are required:

```bash
python3 scripts/revision/figures_124_steps/rescore_public_identifiers.py \
  --output /tmp/figure4_identifier_rescore.tsv
```

The small scorer checks each file hash, reconstructs TP/FP/FN by set intersection/difference, and matches counts exactly and floating-point metrics within 1e-9 against the selected table. Its 111-row output labels the 87 independently recomputed public rows and 24 retained controlled aggregate rows separately. Counts are identifier counts; precision/recall/F1 are unitless fractions. It does not rerun discovery tools or statistical analyses.

Inspect an entire small real input:

```bash
gzip -dc data/figure_04/identifier_sets/ScTagger-S_flatQ20.RAD.txt.gz
```

To repeat the source extraction on the authorized project filesystem, use `python3 scripts/revision/figures_124_export_public_sets.py --project-root /path/to/rad_data --output-root .`. That recovery command also uses explicitly recorded retained scratch paths for selected Measles/ScMix sources; the portable scoring command above does not.
