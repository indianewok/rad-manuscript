# LongBench SN-ONT H146/H526 full-cohort DEG methods

## Question

For each barcode-processing tool, what expression differences are observed when **all** Vireo named singlets assigned to H146 or H526 are compared with all named singlets assigned to the other seven cell lines? The primary analysis intentionally does not restrict the tools to common cells or common genes.

## Identity inputs

- RAD: rebuilt SN-ONT Vireo assignments (`RAD_rebuilt`).
- BLAZE: primary panel-matched SN-ONT Vireo assignments.
- Flexiplex: rebuilt SN-ONT Vireo assignments (`Flexiplex_rebuilt`).
- Reference: Illumina SN Vireo assignments from the rebuilt eight-line bulk-genotype panel.

Only named singlets assigned to H146, H1975, H211, H2228, H526, H69, HCC827, or SHP77 are included. Doublets and unassigned barcodes are not treated as cell-line identities.

## Primary native-matrix analysis

Each tool is analyzed on its all-state native SN-ONT MEX matrix. The RAD input is the commit-`4acbe00` full rebuild retaining all output records, including `-CT` concatenate segments; exact `(cell, gene, UMI)` keys are collapsed, and a concatenate segment inherits its frozen parent-read gene call. Every positive-depth named singlet for that tool is retained. The tested-gene universe is defined separately for each tool: at least 10 molecules across its named cohort and detection in at least 1% of its named positive-depth cells. This preserves the additional cells and molecules uniquely made available by each workflow.

For H146 and H526 separately, the target line is contrasted with the pooled other seven named lines. Counts are normalized per cell to CP10K and transformed as `log2(1 + CP10K)`. A two-sided cell-level Wilcoxon rank-sum test is applied. Benjamini-Hochberg correction is performed within tool and contrast. The reported effect size is the conventional `log2((mean target CP10K + 0.1)/(mean rest CP10K + 0.1))`; AUC and target/rest detection fractions are also retained.

- FDR-qualified: BH FDR < 0.05 and expression detected in at least 10% of either group.
- Effect-qualified: FDR-qualified and absolute mean-CP10K log2 fold change >= 0.5.

## Same-Illumina-substrate sensitivity

The public 12,012-cell Illumina SN raw-count matrix is held fixed. It is grouped four separate ways: by RAD labels, BLAZE labels, Flexiplex labels, and Illumina-reference Vireo labels. A tool label is included only when that barcode is present in the Illumina matrix and has positive expression depth. A single fixed Illumina tested-gene universe is used for all four cohorts: at least 10 molecules and detection in at least 1% of all 12,012 Illumina cells. This removes native expression-matrix and tested-gene-universe differences, but the tool-defined cell cohorts remain different.

## Illumina-Vireo-reference-defined marker panels

For H146 and H526, the top 50 positive genes are defined from the Illumina Vireo named-singlet contrast after the same FDR, effect, and detection gates, ranked by descending AUC and then descending log2 fold change. These panels are then measured in each native tool cohort and in each same-Illumina-substrate cohort.

Cell-level panel scores use the exact 50-gene denominator in every cohort. Counts are normalized with the complete cell library size, transformed as `log2(1 + CP10K)`, summed over available marker genes, and divided by 50. A marker gene absent from a native MEX is zero-filled and explicitly counted. Native SN-ONT scoring is cross-modality, although marker selection remains Illumina-reference-defined. Same-Illumina-substrate marker scores are descriptive because reference-panel discovery cells can overlap the tool-defined scoring cohorts.

Exact per-gene marker measurements are recomputed directly from each full matrix for all 50 panel genes, independently of the cohort-specific DEG-universe gate. The package separately reports whether each panel gene passed that gate; genes excluded from a DEG universe are never assigned fabricated FDR or effect-qualified values.

## Cohort composition versus Illumina evidence

For every RAD-, BLAZE-, or Flexiplex-named H146/H526 singlet, the normalized barcode is joined to the complete Illumina Vireo callset and classified as the same named line, another named line, doublet, unassigned, or absent. Illumina-unassigned cells are then joined to the fixed 6,171-cell expression-transfer source from `SN_ONT_expression_supported_rescue_20260810`. An accepted expression label is counted as same or other; a rejected prediction is retained as an abstention, not counted as an incorrect label. All categories close exactly to each tool's full H146/H526 cohort.

## Operational overlap definitions

The primary DEG tables retain tool-specific tested-gene universes. A separate status-union table records, for every gene effect-qualified by at least one tool, whether each other tool called it UP, DOWN, not effect-qualified, or did not test it. The reviewer-safe RAD-only-positive table requires the gene to be effect-qualified UP for RAD and for the Illumina-reference contrast, while both competitors are not effect-qualified UP. “RAD-only” is therefore an operational threshold result, not evidence that the biology is absent from competitor cells.

## Scope

This is one mixed library. Cell-level P values describe within-library cell-line separation and must not be interpreted as biological-replicate-level inference. Results are descriptive cell-line marker analyses intended to compare the biological coherence and expression richness of the full cohorts recovered by the three barcode-processing workflows.
