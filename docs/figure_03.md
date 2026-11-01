# Figure 3 — assignments to excluded targets and barcode correction

Figure 3 tests how often tools assign reads to supplied target lists that exclude the matched reference, then examines barcode correction in LongBench single-cell and single-nucleus ONT and PacBio data. ScTagger and LongBench supplied-list challenges count original physical reads. The RAGE-seq arm uses historical assignment tables. The correction analysis counts unique original-read–target-barcode pairs.

![Figure 3](../figures/figure_03/prism/figure_03.png)

## Figure legend

Figure 3. Adaptive whitelisting provides high fidelity barcode identification and correction. A-C. Characterization of false positive barcode assignment rate. Using three datasets, random, size matched sets of “off-list” barcodes were provided as the whitelist to each tool and the rate at which reads were assigned to this list was assessed (A). Quantification of total read count (B) and read depth (C) assigned to false positive barcodes by each tool. Statistical significance determined by one-way ANOVA (****p < 0.0001). D-G. Barcode correction outcomes (D). Using the LongBench dataset, the total read counts (E), the read depth (F), and the percentage of reads per barcode (G) derived from corrected off-list or the two failure modes were quantified for each tool.

## Supplied-list challenges

Three target lists were sampled independently for each dataset after removing its matched reference from the chemistry catalog. Every tool received the same complete input and target list within a replicate. Each target-list draw forms one technical replicate.

| Input | Reads | Chemistry catalog | Excluded reference | Target-list size | List seeds |
|---|---:|---|---|---:|---|
| ScTagger-L, uniform Q20 | 4,993,805 | 6,794,880 3v3 barcodes | 5,000 source barcodes | 5,000 | 20260813, 20260814, 20260815 |
| LongBench SC-ONT | 10,000,000 | 6,794,880 3v3 barcodes | 5,211 filtered Cell Ranger barcodes | 5,211 | 2026081301, 2026081302, 2026081303 |
| RAGE-seq cell-line mixture, ERR3268991 | 20,346,396 | 737,280 3v2 barcodes | 4,505 filtered Cell Ranger barcodes | 4,505 | Historical target-list draws |

The LongBench subsample used SeqKit 2.8.2 with seed `2026081326`. List sampling used Python 3.9.16 `random.Random`.

## Software and parameters

| Analysis | RAD | BLAZE | Flexiplex |
|---|---|---|---|
| ScTagger-L and LongBench supplied-list challenges | RAD 1.0.2, `cd0582b2440cde0f35725dc557fa47307d74d374`; offensive correction, mutation limits 2/2, chunks of 5,000, 32 threads, 3v3 layout with 12-base UMI | 2.6.0a0, `af8d2cc9f6374caf4d1006d5f8a0e99097211646`; supplied-list mode, Q15, barcode distance 2, EmptyDrops disabled; 32 threads | Flexiplex 1.02.6, `d84c8ae4f3865052f2b5ecec816949b94682f302`, with raw-barcode diagnostic output; `-d 10x3v3 -f 8 -e 2 -k LIST -p 28`; 4 compression threads |
| LongBench correction analysis | 1.0.2, `4acbe004ba11b150d6832395452632f367a6e6c1`; offensive correction, mutation limits 2/2, minimum read length 85, chunks of 5,000; 24/60/28/60 workers for SC-ONT/SN-ONT/SC-PB/SN-PB, plus 4 compression threads; concatemer records retained | 2.5.0; expected cells 5,000 for single cells, forced cells 10,000 for nuclei; 48 threads, 3v3 defaults, `PYTHONHASHSEED` unset | Flexiplex 1.02.6, `d84c8ae4f3865052f2b5ecec816949b94682f302`, with raw-barcode diagnostic output; discovery flank distance 0; selected-list demultiplexing with flank distance 8, barcode distance 2, and 16 threads |

Flexiplex’s diagnostic field `RawCellBarcode` records the extracted sequence before correction. The [source, patch, binary, and build instructions](../vendor/flexiplex-audit/) define the modified build. Its binary SHA-256 is `38dccd37f1747e5105b62eacde572b7e4c5206fb925dc1fdbe8210ffe8b1e8c4`.

The [BLAZE dependency lock](../environments/figure_3_blaze_2.6.0a0.txt) specifies the supplied-list environment. LongBench correction used BLAZE 2.5.0 at source commit `11994f9c12a6664dfe1679576aaca19b6bfd35c1`.

## ScTagger and LongBench physical-read counts

Tool output identifiers are resolved to original input identifiers by removing the documented orientation, concatemer, or barcode decorations. RAD targets come from `CB:Z:` and raw barcodes from `CR:Z:`. Reverse-orientation RAD raw barcodes are reverse-complemented once. An explicit empty native RAD CR uses the target as its source. BLAZE sources come from its putative-barcode CSV; Flexiplex sources come from its diagnostic table.

For the supplied-list challenges, an original read counts only when it has exactly one assignment record in the complete output. Every identifier with multiple records is excluded, including repeated records to the same target. All supplied targets remain in the per-target table, including those with zero counts.

The [assignment examples](../data/examples/figure_03/selection_manifest.json) connect original identifiers, emitted records, and parsed barcode fields.

Run a complete target-level counting example with:

```bash
mkdir -p results
python3 scripts/revision/figure_3_example_count.py \
  data/examples/figure_03/sctagger_rad_rep1_assignments.tsv \
  data/examples/figure_03/sctagger_rad_rep1_targets.txt results/sc_counts.tsv
```

The [expected output](../data/examples/figure_03/sctagger_rad_rep1_counts.tsv) contains ten reads for `AAACCCACACAGTGAG`. The example includes all assignments to that target and every other record sharing one of those original identifiers. The [duplicate example](../data/examples/figure_03/actual_duplicate_assignments.tsv) contains two records for one original read; both are excluded.

Flexiplex counts use its diagnostic stream. The [diagnostic example](../data/examples/figure_03/longbench_flexiplex_rep1_diagnostic.tsv) contains `Read`, `CellBarcode`, `RawCellBarcode`, `FlankEditDist`, `BarcodeEditDist`, and `UMI`.

For ScTagger and LongBench, the counting workflow partitions the complete input:

```text
input reads = strict assigned reads + excluded ambiguous reads + unassigned reads
```

## Historical RAGE-seq assignment tables

The RAGE-seq comparison uses the cell-line mixture ERR3268991 and three off-list target lists. Historical tool-assignment tables supply the total counts in panel B and the target-count distributions in panel C. Panel C displays the first list draw. The [plotted totals](../source_data/figure_03/plotted_checkpoint/plotted_offlist_totals.tsv) and [target-count observations](../source_data/figure_03/plotted_checkpoint/plotted_offlist_per_target.tsv.gz) preserve these values separately, with their count units and Prism row order.

Panel B shows total assignments for each target-list replicate. Panel C shows the corresponding per-target count distributions. The ScTagger and LongBench arms use the strict physical-read rule above; the RAGE-seq arm uses its historical assignment-table counts. The [Prism provenance](../source_data/figure_03/plotted_checkpoint/plotted_offlist_provenance.json) records the source-file hash, native table members, and graph bindings for both panels.

## LongBench correction categories

The chemistry catalog defines valid barcode sequences, and the matched Cell Ranger filtered set identifies short-read-supported cells or nuclei. Observed source-to-target changes are classified as follows:

| Category | Source-to-target change |
|---|---|
| Corrected off-list | Source outside the chemistry catalog → tool-selected target |
| Failure Mode 1 | Catalog-valid source outside the matched filtered reference → tool-selected target |
| Failure Mode 2 | Source in the matched filtered reference → a different target in that reference and selected by the tool |

Failure Mode 1 measures reassignment from a valid barcode outside the short-read reference into the selected population. Failure Mode 2 measures reassignment between reference-supported cells or nuclei. Each category requires a changed barcode.

Counts use unique `(original_id, target_barcode)` pairs within each category, including RAD concatemer records. Repeated records for the same pair are collapsed within a category. A read assigned to two targets can contribute to both, and a pair with different observed sources can contribute to multiple categories. The denominator `O` comprises all unique assignments to the target, including native assignments and assignments with unavailable source barcodes.

Tool-selected targets are joined by barcode sequence within each dataset. An unselected tool–target combination has count zero and a null percentage. A selected target with `O=0` also has a null percentage. Otherwise, the percentage for each category is `100 × category count / O`.

```bash
python3 scripts/revision/figure_3_example_percent.py \
  data/examples/figure_03/correction_C5_input.tsv results/correction_percent.tsv
```

For the example BLAZE target, 1,861 Failure Mode 2 pairs among 13,809 total pairs give 13.4767%. [Expected output](../data/examples/figure_03/correction_C6_output.tsv), [per-target correction counts and percentages](../source_data/figure_03/correction_per_target.tsv.gz), and [correction totals](../source_data/figure_03/correction_totals.tsv) connect this calculation to panels E–G. The complete tables retain each selected target and its category counts.

## Generate the plotted checkpoint tables

Use the deposited checkpoint tables for the plotted observations. To refresh them from a local author project:

```bash
python3 scripts/figure_03/extract_plotted_offlist.py \
  --prism "external_data/prism/Figure 3.prism" \
  --output-dir results/figure_03/plotted_checkpoint
```

The extractor follows the layout's graph-to-dataset bindings and writes the panel B totals, panel C target observations, and source hashes. The [checkpoint tables](../source_data/figure_03/plotted_checkpoint/) supply the exact plotted observations. The manuscript's off-list comparisons use the one-way ANOVA annotations saved in the Prism project.

For the LongBench correction panels, the [panel definitions](../source_data/figure_03/panel_data_manifest.tsv), [table schema](../source_data/figure_03/schema.json), and [checksums](../source_data/figure_03/checksums.json) identify the source tables, barcode keys, and denominator units. The example counting and percentage commands above reproduce individual calculations from those tables.
