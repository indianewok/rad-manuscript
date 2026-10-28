# Figure 4 — barcode discovery across 37 inputs

Figure 4 compares the precision, recall, and F1 score of barcode discovery across synthetic, single-cell, single-nucleus, targeted long-read, and Visium datasets. Each input has a common reference set and one callset per tool.

![Figure 4](../figures/figure_04/prism/figure_04.png)

## Inputs and reference sets

The [sample inventory](../source_data/figure_04/sample_inventory.tsv) identifies the 37 scored inputs and their library, donor, and sequencing-run relationships. The [metrics table](../source_data/figure_04/barcode_detection_metrics.tsv) contains all 111 input–tool observations. Separate technical libraries and sequencing runs retain separate input identifiers.

Known source barcodes define the synthetic references. Biological inputs use matched filtered short-read barcodes or published spatial masks. For the RAGE-seq TNBC lymph node, the reference comprises deposited short-read barcodes annotated as `T_cell*`, `B_cell*`, or `T_B_doublet`, with `in_deposited_shortread_list=True`. This gives 5,978 reference barcodes: 4,255 T-cell, 1,637 B-cell, and 86 T/B-doublet barcodes. The RAGE-seq cell-line input uses its own 4,505-barcode reference.

ScMixology2 combines a native RAD callset with a BLAZE selector replay on retained BLAZE counts and a Flexiplex filter replay on the common RAD count table. Its matched Cell Ranger reference contains 248 barcodes. RAD selected 279 barcodes, including 233 reference members; BLAZE selected 188, all in the reference; Flexiplex selected 184, including 183 reference members.

## Software and parameters

The [producer records](../source_data/figure_04/producing_evidence/) contain the commands and software identities for each input.

| Input group | RAD | BLAZE | Flexiplex and key settings |
|---|---|---|---|
| ScTagger S/L, uniform Q20 | 1.0.2, `b02ff24110fe45873811d5389d2e58c338045f05`; error 0.3, 3v3.1, chunks of 10,000, 8 threads | 2.6.0a0; expected cells 50/5,000, minimum Q15, 8 threads | 1.02.6; flank distance 8, barcode distance 2, 16 threads |
| RAGE cell line and TNBC lymph node | `cd0582b2440cde0f35725dc557fa47307d74d374` | 2.6.0a0; TNBC expected cells 10,433 | 1.02.6, filter 1.01; 3v2 chemistry, 16-base barcode and 10-base UMI |
| Tilgner m1, three runs | 1.0.2, `613a72e90cb5dfc206db113fd98bca656f0ee6c3`; automatic whitelist, 30 threads | 2.5.0; expected cells 10,205, Q15, barcode distance 2, 48 threads | 1.02.6; discovery flank distance 0, 20 threads |
| Other seven Tilgner inputs | `4acbe00` | Expected cells: f1 8,975; f2 8,850; f3 6,680; m2 10,427; m3 10,574 | Discovery flank distance 0; donor-matched references shared across technical runs |
| MPNST1, two inputs | 1.0.2, `4acbe004ba11b150d6832395452632f367a6e6c1`; error 0.3, 3v3.1, 16 threads | 2.5.0; expected cells 4,500, Q15, barcode distance 2, 16 threads | 1.02.6; 3v3, discovery flank distance 0, 16 threads |
| MPNST2, two inputs | Same RAD build; error 0.3, 3v3, high-specificity mode, 20 threads | 2.5.0; expected cells 11,000, Q15, barcode distance 2, 20 threads | 1.02.6; 3v3, discovery flank distance 0, 20 threads |
| Eight Visium inputs | `5cf1ee6`; error 0.30, Visium 3′ layout | 2.6.0a0; expected cells 2,500 | 1.02.6; 3v2, flank distance 8, selected-list barcode distance 2 |
| ScMixology2 | `2c5a7936e630ccc46548c133855b4bfb4e50f058`; error 0.3, 3v3, chunks of 10,000, 24 threads | Expected-cell-500 selector replay | 1.02.6 filter replay on common counts |

LongBench used RAD `920addacdbf40b815e13a146226e8f4b14a58aaf`, 32 threads, and scan error 0.1; BLAZE 2.5.0 used 48 threads, expected cells 5,000 for single cells and forced cells 10,000 for nuclei. PromethION used RAD `cd0582b`, scan error 0.1 and 32 threads; BLAZE 2.6.0a0 expected 500 cells; Flexiplex 1.02.6 used flank distance 8. P8-WTA used RAD `b02ff24110fe45873811d5389d2e58c338045f05`. LeBrigand combined two accessions and used RAD `920addacdbf40b815e13a146226e8f4b14a58aaf`, BLAZE expected cells 918, and Flexiplex flank distance 8, with 12 threads.

Unrecorded fields include the original Measles P7/P8 RAD build, some Tilgner and LongBench discovery software identities, and the original SeqKit version and full command. Four original Visium RAD split callsets also require recovery; their aggregate metrics and recorded hashes are retained.

## Barcode-set scoring

For a tool callset and its matched reference, true positives are their intersection, false positives are called barcodes outside the reference, and false negatives are reference barcodes absent from the callset. Metrics use distinct barcode identities:

```text
precision = TP / (TP + FP)
recall = TP / (TP + FN)
F1 = 2TP / (2TP + FP + FN)
```

[Paired precision](../source_data/figure_04/paired_precision.tsv), [recall](../source_data/figure_04/paired_recall.tsv), and [F1](../source_data/figure_04/paired_f1.tsv) use the same 37 input rows. Recalculate all metrics and check complete three-tool pairing with:

```bash
mkdir -p results
python3 scripts/revision/figures_124_steps/recompute_detection_metrics.py \
  source_data/figure_04/barcode_detection_metrics.tsv \
  results/figure4_all37.tsv --expected-inputs 37
```

A [three-input example](../data/examples/figure_04/three_input_metrics_example.tsv) contains the complete tool triples for ScTagger-S, ScTagger-L, and RAGE-seq TNBC lymph node. Its [expected output](../data/examples/figure_04/three_input_metrics_recomputed.tsv) can be reproduced with the same command and `--expected-inputs 3`.

## Reproduce scores from the barcode lists

The [public identifier collection](../data/figure_04/README.md) contains selected callsets and references for 29 inputs, covering 87 tool observations. The [identifier manifest](../data/figure_04/identifier_manifest.tsv) records hashes and the controlled-access status of the eight Visium inputs. Identical sets are stored once.

```bash
python3 scripts/revision/figures_124_steps/rescore_public_identifiers.py \
  --output results/figure4_identifier_rescore.tsv
```

The scorer verifies each file hash and reconstructs TP, FP, and FN directly from set membership. All 87 public observations match the saved counts exactly, with metric differences below 1e-9. The output also includes the 24 controlled-access aggregate observations.

The immune-reference example follows annotation labels through reference selection and scoring:

```bash
python3 scripts/revision/figures_124_steps/rescore_immune_reference.py \
  data/examples/figure_04/immune_reference_annotation_example.tsv \
  results/figure4_immune_example.tsv
```

The complete TNBC reference produces these counts:

| Tool | Calls | TP | FP | FN |
|---|---:|---:|---:|---:|
| RAD | 5,605 | 5,490 | 115 | 488 |
| BLAZE | 4,474 | 3,908 | 566 | 2,070 |
| Flexiplex | 3,707 | 3,677 | 30 | 2,301 |

## Input characteristics and reproduction

The [input-characteristics table](../source_data/figure_04/input_characteristics.tsv) joins saved all-read SeqKit summaries to the 37 canonical input identifiers. It includes read counts, total bases, read-length summaries, GC percentage, and quality statistics. ScTagger inputs use uniform Q20. [Schemas](../source_data/figure_04/schemas.json) define all fields and units, and [SeqKit provenance](../source_data/figure_04/seqkit_saved_provenance.json) identifies the saved source.

With the project inputs mounted, reconstruct the source comparisons:

```bash
python3 scripts/revision/figures_124_native_recovery.py --project-root /path/to/rad_data --output-root .
```

Check and plot the deposited tables with:

```bash
python3 scripts/revision/figures_124.py validate --output-root .
python3 scripts/revision/figures_124.py render --output-root .
```

Statistical annotations are retained in the Prism figure; their original analysis settings are required to reproduce those annotations.
