# Methods

## Read-only provenance

Native MEX matrices, feature tables, barcode tables, Vireo `donor_ids.tsv`
files, and the authoritative stored versus-rest DEG table are read from the
checksum-sealed `SN_ONT_H146_H526_fullcohort_DEG_20260822` package. The
versus-rest annotation IDs come from the checksum-sealed `wilcoxon_auc_rank`
package. `tables/SOURCE_INPUT_SHA256.tsv` records the absolute path, byte size,
and SHA-256 hash of every input. The builder also verifies that every MEX,
label, DEG, universe, and imported rank file is a member of its upstream
package's checksum manifest.

No upstream file or package metadata is modified.

## Set A: existing H146/H526 versus the other seven lines

Every stored native RAD, BLAZE, and Flexiplex coordinate is used unchanged:

`x = stored log2((mean target CP10K + 0.1)/(mean rest CP10K + 0.1))`

`y = -log10(stored BH FDR)`

Here, target is H146 or H526 and rest is the other seven named Vireo cell
lines in that tool's positive-depth native cohort. The 10 UP and 10 DOWN genes
per line are the sealed, cross-tool consensus directional-AUC selections used
in the preceding uncapped figure package. Each selected gene has three
tool-specific points. Thin connectors run directly from BLAZE to RAD and from
Flexiplex to RAD; they are paired comparisons, not temporal trajectories. The
gene is labeled once, anchored at its RAD coordinate.

Background clouds use each tool's native tested-gene universe and therefore
are not point-for-point paired when a gene is absent from another tool's
universe.

## Set B: direct H146 versus H526

### Cells and library sizes

For each tool independently, normalized barcode matching removes a terminal
`-<digits>` suffix. All native-MEX columns with a named Vireo `H146` or `H526`
label and positive total count are retained:

| Tool | H146 | H526 |
|---|---:|---:|
| RAD | 709 | 419 |
| BLAZE | 234 | 185 |
| Flexiplex | 290 | 219 |

Each cell's library size is its column sum over **every feature in the full
native MEX**, before gene filtering. Per-cell linear expression is CP10K:

`CP10K(g,c) = 10,000 * count(g,c) / full_MEX_UMIs(c)`

### Pair-only gene universes

The source native eligibility rule is reapplied to the H146+H526 cells only:
a gene needs at least 10 total molecules and detection in at least 1% of the
positive-depth pair-only cells. Thus the other six lines influence neither
the comparator nor gene eligibility. The resulting universes are 13,504 RAD,
10,926 BLAZE, and 12,160 Flexiplex genes. The minimum detected-cell counts are
12, 5, and 6, respectively.

### Test, effect estimate, and sign

For every eligible gene, a two-sided cell-level Wilcoxon rank-sum test is run
on `log2(1 + CP10K)` with `BiocParallel::SerialParam`; no multicore/fork
backend is used. P values receive Benjamini-Hochberg adjustment within the
single direct contrast and tested universe of each tool.

The x coordinate is:

`log2FC = log2((mean H146 CP10K + 0.1)/(mean H526 CP10K + 0.1))`

Wilcoxon AUC is H146-positive. Therefore:

- positive log2FC and AUC > 0.5 mean **H146-high**;
- negative log2FC and AUC < 0.5 mean **H526-high**.

Rank-biserial effect size is `2*AUC_H146 - 1`. Directional AUC is
`AUC_H146` for H146-high genes and `1-AUC_H146` for H526-high genes.

### Qualification and annotation ranks

The unchanged effect gate requires all of:

- BH FDR < 0.05;
- absolute log2FC >= 0.5;
- detection in at least 10% of H146 or H526 cells.

Within each tool and direction, qualified genes are ranked by decreasing
directional AUC, then decreasing absolute log2FC, increasing FDR, and gene ID.
The independently ranked plot labels `H146#1-10` and `H526#1-10`.

For the fixed cross-tool set, a gene must qualify in the same direction in all
three tools. Consensus order is decreasing median directional AUC, decreasing
minimum directional AUC, decreasing median absolute log2FC, then gene ID. The
same ten genes in each direction are highlighted in all three panels and in
the overlay.

## Exact uncapped graphics

Every plotted y coordinate is exactly `-log10(BH FDR)`. All p values and FDRs
are finite and strictly positive, so no numerical floor is needed. No y cap,
truncation, clipping limit, or free-y facet scale is used. Panels within a
figure share one linear y scale. X viewports are symmetric and include the
complete observed x range.

All SVGs are vector output from `svglite` and contain no embedded raster.
Matching PNG previews are rendered from the identical ggplot objects using
`ragg` at 300 dpi.
