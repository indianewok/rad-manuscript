# Figures

The images below were exported at 300 dpi from the saved Prism projects in
`Nat Comm/appeal/figure_revisions/CURRENT FIGURES`. Each figure links to its
methods, source tables and analysis commands. The [export manifest](../manifests/prism_exports.json)
records the project checksum, layout, linked graphs and image checksum.

## Figure 1: RAD workflow and computational performance

[Analysis guide](../docs/figure_01.md)

![Figure 1](figure_01/prism/figure_01.png)

## Figure 2: Synthetic barcode discovery and read assignment

[Analysis guide](../docs/figure_02.md)

The saved layout shows 87 BLAZE false-positive barcodes; the updated source
tables contain 15.

![Figure 2](figure_02/prism/figure_02.png)

## Figure 3: Off-list assignments and barcode correction

[Analysis guide](../docs/figure_03.md)

The saved layout shows total assigned reads and the original schematic labels.
The guide describes the matched RAGE rerun and measured correction categories.

![Figure 3](figure_03/prism/figure_03.png)

## Figure 4: Barcode detection across sequencing modalities

[Analysis guide](../docs/figure_04.md)

![Figure 4](figure_04/prism/figure_04.png)

## Figure 5: Receptor recovery and LR-Split-seq

[Analysis guide](../docs/figure_05.md)

![Figure 5](figure_05/prism/figure_05.png)

## Figure 6: Genotype analysis in LongBench single-nucleus data

[Analysis guide](../docs/figure_06.md)

![Figure 6](figure_06/prism/figure_06.png)

## Figure 7: Differential cell-line expression

[Analysis guide](../docs/figure_07.md)

Panels A and C retain the earlier analysis; the guide and source tables use the
updated set of 8,135 genes.

![Figure 7](figure_07/prism/figure_07.png)

## Supplementary plots

### ScTagger quality sweep

![ScTagger quality sweep](figure_02/prism/figure_02_supplement.png)

### Input characteristics and modality-specific precision and recall

![Modality comparisons](figure_04/prism/figure_04_supplement.png)

## Exporting the figures

Run the preparation script with the path to `CURRENT FIGURES` and a new working
directory. It copies the projects, selects layouts by their saved identifiers,
and writes a Prism script that exports PNG images into the new working directory.

```bash
python3 scripts/export_prism_figures.py prepare \
  --source-dir '/path/to/CURRENT FIGURES' --work /path/to/prism-export
```

Open the generated `export.pzc` through Prism's **File → Run Script** command.
After it finishes, verify the new images and source checksums, then copy the
verified exports into the repository:

```bash
python3 scripts/export_prism_figures.py verify --work /path/to/prism-export
```

The export script opens copies, selects layouts, exports images and closes each
copy. It contains no data-import, analysis, formatting or save commands.
