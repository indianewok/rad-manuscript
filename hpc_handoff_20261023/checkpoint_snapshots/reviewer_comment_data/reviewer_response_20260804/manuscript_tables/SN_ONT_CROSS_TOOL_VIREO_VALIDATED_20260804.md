# Validated SN-ONT cross-tool Vireo comparison

Validated 2026-08-04 from the existing RAD/Flexiplex comparison and the durable
panel-matched BLAZE rebuild at:

```text
/scratch-nfs/f005f43/longbench_snont_postdemux_vireo_20260803/
  analysis/post_vireo_comparison_bulk_panel_v1
/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/
  reviewer_response_20260804/objects/longbench/durable_sources/
  BLAZE_panel_matched_20260804
```

The primary reference is the released, independently generated Illumina-SN
Vireo result. It contains 12,012 barcodes: 5,782 named singlets, 59 doublets,
and 6,171 unassigned barcodes. The named-singlet denominator is fixed at 5,782
for every strict cell-line identity result below.

## Main result

| Tool | Named reference selected | Same donor | Different donor | To doublet | To unassigned | Not selected | Strict identity recall | Agreement when both are singlets |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BLAZE | 5,536 | 4,450 | 12 | 766 | 308 | 246 | 76.96% | 99.73% |
| RAD | 5,767 | 5,324 | 32 | 246 | 165 | 15 | 92.08% | 99.40% |
| Flexiplex | 5,756 | 4,674 | 17 | 725 | 340 | 26 | 80.84% | 99.64% |

Every row reconciles exactly to 5,782:

```text
same donor + different donor + doublet + unassigned + not selected = 5,782
```

No selected barcode was missing a Vireo output row for any tool.

The strict identity statistic is `same donor / 5,782`; it deliberately counts
not-selected, doublet, unassigned, and different-donor outcomes as failures.
The conditional agreement statistic is `same donor / (same + different donor)`
and must not be substituted for strict recall.

## Barcode-selection overlap with the Illumina reference

The following uses all 12,012 released Illumina CellSNP/Vireo barcodes as a
proxy reference. A selected barcode outside this set is not automatically a
proven biological false cell; consequently these precision/F1 values should be
described as reference-overlap statistics.

| Tool | Selected | In reference | Outside reference | Reference missed | Precision proxy | Recall proxy | F1 proxy |
|---|---:|---:|---:|---:|---:|---:|---:|
| BLAZE | 10,001 | 9,979 | 22 | 2,033 | 99.78% | 83.08% | 90.66% |
| RAD | 12,423 | 11,821 | 602 | 191 | 95.15% | 98.41% | 96.75% |
| Flexiplex | 12,101 | 11,653 | 448 | 359 | 96.30% | 97.01% | 96.65% |

Among the 5,782 named Illumina singlets, selection recall was 95.75% for
BLAZE, 99.74% for RAD, and 99.55% for Flexiplex.

## Selection versus post-demultiplexing genotype resolution

RAD's 874-cell strict-identity gain over panel-matched BLAZE decomposes arithmetically into:

- 231 fewer named reference cells not selected;
- 520 fewer selected named singlets called doublets;
- 143 fewer selected named singlets called unassigned; and
- an offset of 20 more named donor-to-donor disagreements.

This is an aggregate category decomposition, not proof that a particular
demultiplexer causally changed each individual Vireo call.

Among selected named-reference cells, the fraction that Vireo left as doublet
or unassigned was 19.40% for BLAZE, 7.13% for RAD, and 18.50% for Flexiplex.
Conversely, same-donor recovery among selected named-reference cells was
80.38%, 92.32%, and 81.20%, respectively.

Therefore the defensible biological interpretation is that RAD retained more
Illumina-supported nuclei and produced enough donor-informative post-demux
evidence for more of them to remain resolved as the correct named cell line.
The experiment does **not** show that RAD has the lowest named A-to-B donor
disagreement rate: those counts were 12 for BLAZE, 32 for RAD, and 17 for
Flexiplex, or 0.27%, 0.60%, and 0.36% among cells named as singlets by both
references.

## Doublet-state comparison

Of the 59 Illumina-reference doublets:

| Tool | Retained as doublet | Called named singlet |
|---|---:|---:|
| BLAZE | 53 | 6 |
| RAD | 55 | 4 |
| Flexiplex | 52 | 7 |

## Per-cell-line strict identity recall

| Cell line | Illumina cells | BLAZE | RAD | Flexiplex |
|---|---:|---:|---:|---:|
| H146 | 263 | 27.76% | 63.50% | 33.08% |
| H1975 | 1,471 | 89.19% | 95.51% | 92.05% |
| H211 | 219 | 47.49% | 84.47% | 56.62% |
| H2228 | 1,594 | 88.08% | 95.86% | 91.28% |
| H526 | 195 | 46.15% | 81.54% | 51.28% |
| H69 | 182 | 36.81% | 80.77% | 48.35% |
| HCC827 | 1,193 | 85.08% | 95.73% | 88.18% |
| SHP77 | 665 | 57.89% | 88.87% | 62.26% |

RAD's improvement is strongest for the lower-recovery H146, H211, H526, H69,
and SHP77 populations, while preserving greater than 95% strict identity
recall for the three larger H1975, H2228, and HCC827 populations.

## Provenance and comparability limits

- RAD, BLAZE, and Flexiplex were independently aligned from their complete
  post-demultiplexed SN-ONT FASTQs, then processed with CellSNP-lite 1.2.3 and
  Vireo 0.5.8 against the same reconstructed eight-line bulk panel. All Vireo
  runs used `-t GT --callAmbientRNAs`.
- The reconstructed panel contains 360,814 sites and exactly reproduced all
  12,012 released Illumina-SN hard states, including all 5,782 named singlets
  and 59 doublets. This validates donor naming and the Illumina reference, but
  the panel is not byte-identical to the authors' unreleased private bulk VCF.
- The primary BLAZE row uses the validated 10,001-barcode local whitelist and
  panel-matched rebuild. CellSNP matched 118,378 panel variants and Vireo
  returned one complete row per selected barcode. The BLAZE, RAD, and
  Flexiplex query site counts differ because the post-demultiplexed read sets
  differ; matched panel input does not imply identical observed sites or depth.
- The released BLAZE query and callset remain preserved as a sensitivity check.
  That original-private-panel result has 4,456 same-donor calls and 77.0668%
  strict recall, versus 4,450 and 76.9630% in the panel-matched primary result:
  a difference of six calls and 0.10377 percentage points. The published and
  panel-matched BLAZE barcode lists differ by seven normalized entries and must
  not be silently mixed.
- The published majority-vote merged labels are not an independent truth set
  because they include long-read votes. They should remain a secondary
  reproduction check, not the main biological comparison.
- Vireo state changes establish genotype-resolution outcomes after each
  demultiplexing workflow. They do not by themselves prove the molecular source
  of an individual misassigned read or establish a direct causal mechanism.

## Published BLAZE sensitivity check

| BLAZE source | Same donor | Different donor | To doublet | To unassigned | Not selected | Strict recall |
|---|---:|---:|---:|---:|---:|---:|
| Panel matched (primary) | 4,450 | 12 | 766 | 308 | 246 | 76.9630% |
| Published/private panel (sensitivity) | 4,456 | 12 | 763 | 305 | 246 | 77.0668% |

The near-identity of these results shows that the prior panel asymmetry was not
material to this aggregate conclusion. It does not establish gene-space
equivalence or a per-read causal mechanism.

## Audit checks

- The panel-matched BLAZE durable manifest records sizes and SHA-256 hashes for
  the exact Vireo output, CellSNP order, whitelist, scripts, and provenance.
- The primary five-outcome partitions equal 5,782 for all three tools.
- Cross-line detail rows equal the summary counts: BLAZE 12, RAD 32,
  Flexiplex 17.
- `selected_barcodes == vireo_rows` for every tool and
  `selected_without_vireo_row == 0`.
- BLAZE primary proportions were independently recomputed from the durable
  `analysis/all_tools.per_cell_long.tsv`; no arithmetic inconsistency was found.
- The previously generated published-BLAZE graph-ready tables remain preserved
  as sensitivity/provenance artifacts and are not relabeled as panel matched.

Machine-readable companion:

```text
SN_ONT_CROSS_TOOL_VIREO_VALIDATED_20260804.tsv
SN_ONT_BLAZE_PANEL_PARITY_SENSITIVITY_20260804.tsv
```
