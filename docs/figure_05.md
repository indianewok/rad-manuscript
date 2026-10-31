# Figure 5 Receptor recovery and LR-Split-seq

Figure 5 tests demultiplexing in two read architectures. Panels A–F measure recovery of B-cell and T-cell receptor reads from the RAGE-seq mixture of Ramos B cells, Jurkat T cells and monocytes. Panels G–H compare barcode assignment and per-cell UMI recovery in the three-component LR-Split-seq library.

![Figure 5](../figures/figure_05/prism/figure_05.png)

## Figure legend

Figure 5. Benchmarking RAD performance on data with complex read structures. A-F. Performance of each tool in demultiplexing and mapping RAGE-seq-derived immune cell receptor reads when applied to a mixed pool of immune cells with distinct receptors. Composition of input cells (A). Comparison of total cells detected by RAD (R, green), Flexiplex (F, light gray), and BLAZE (B, dark gray) (B), number and identity of cell of each type (C), and the number of BCR and TCR reads mapped (D) by each tool. Number of reads with native or corrected barcodes (E) and read counts per barcode (F) mapped to each cell population by each tool. Statistical significance by paired two-tailed t-test (****p<0.0001). G-H. Performance of RAD (green) and FLAMESv2 (gray) in demultiplexing LR-Split-seq data. Number of assigned reads in the LR-Split-seq dataset, requiring all three whitelist-matched barcode components per read (G). Long read and short-read UMI counts per cell were compared for myoblast cells, myoblast nuclei, and myotube nuclei, separately for each tool (H). Dotted lines represent identity (x = y).

[Editable Prism project](../figures/figure_05/Figure_05.prism)

## RAGE-seq receptor recovery

The receptor analysis uses the RAGE-seq cell-line mixture **ERR3268991**. Demultiplexer assignments are joined to receptor alignments by original read ID and to cell-type annotations by barcode. The annotated population contains 1,993 Ramos cells, 1,572 Jurkat cells and 20 monocytes; the barcode-discovery reference contains 4,505 cells.

Reads are aligned to the TRUST4 human BCR/TCR reference with minimap2 2.26-r1175 using `-x map-ont --secondary=no -t 20`. Receptor identity follows the reference sequence of the selected alignment. The reference SHA-256 is `615152a7481d0a68557ab0a84b735d8f25fc1ee9d5076af3b8d31aa7792dc3df`.

The archived [per-cell receptor counts](../source_data/figure_05/candidate_receptor_counts.tsv) and [receptor totals](../source_data/figure_05/candidate_receptor_totals.tsv) provide the input for panels B–F. The [Flexiplex join script](../source_data/figure_05/provenance/join_flexiplex_bcrtcr.py) removes ambiguous read assignments, applies the BCR/TCR alignment rule and aggregates counts by barcode. The BLAZE assignment run used version 2.6.0a0, the 10x 3v2 layout, 4,505 expected cells, edit distance two and 32 threads; its [command](../source_data/figure_05/provenance/BLAZE_receptor_command.txt) records the invocation. Flexiplex receptor assignments used version 1.02.5 with the 10x3v2 layout, flank edit distance eight, 56 threads and 3,259 selected barcodes; barcode discovery used version 1.02.6. Its [wrapper](../source_data/figure_05/provenance/Flexiplex_receptor_producer.sh) and [execution record](../source_data/figure_05/provenance/Flexiplex_receptor_execution.md) identify the inputs and settings.

Each receptor class is divided into native and corrected-only reads. The Flexiplex source column named `corrected` contains native plus corrected reads, so native counts are subtracted once to obtain corrected-only counts. The RAD and BLAZE columns already contain corrected-only counts. For example, Ramos barcode `AAACCTGAGAATCTCC` has 713 native and 1,413 cumulative Flexiplex BCR reads, giving 700 corrected-only reads.

Reproduce this conversion on the supplied example:

```bash
mkdir -p results
python3 scripts/figure_05/exclusive_receptor_counts.py \
  --input data/examples/figure_05/flexiplex_receptor_input.tsv \
  --output results/figure05_receptor_counts.tsv \
  --tool Flexiplex --corrected-column cumulative
```

The [expected output](../data/examples/figure_05/flexiplex_receptor_output.tsv) contains one row per cell and receptor class. Use `--corrected-column exclusive` for RAD and BLAZE. The [record examples](../data/examples/figure_05/PREVIEW.md) connect the source assignments to the per-cell tables. Panel F uses paired, two-sided t-tests on barcode-matched cell counts, as specified in the figure legend.

## LR-Split-seq demultiplexing

The C2C12 LR-Split-seq comparison uses long-read library **SRR13948564**, containing 5,764,421 original reads, and paired short-read library **SRR13948565**. Both demultiplexers receive the complete component catalogs: [96 ligation barcodes](../data/figure_05/bc_8nt_v1.csv) for each ligation round and [96 reverse-transcription barcodes](../data/figure_05/bc_8nt_v2.csv). The two reverse-transcription primers from each well identify one of 48 physical wells. The 568 published cell identities define the cell-level comparison after demultiplexing.

| Workflow | Version and settings | Configuration and execution |
|---|---|---|
| RAD | Version 1.0.2, commit `b6853a3d3d1818130ac364f7937bd0690ae9e385`; strict joint-barcode mode, defensive correction, generated and whitelist edit distances two, minimum read length zero, chunk size 5,000, four threads | [Command](../source_data/figure_05/provenance/splitseq/RAD_time.txt), [read layout](../data/figure_05/splitseq_reverse_complemented_whitelist_layout.csv) |
| FLAMESv2 component workflow | FLAMES 2.7.1, commit `bf2211a8da1e1c7327370ab12479ae70e1d37cd8`, containing Flexiplex 1.02.6; three 8-nt barcode components, per-component edit distance two and buffer one, flank edit distance three, 10-nt UMI, terminal T8 segment, `reverse_complement=FALSE`, four threads | [Executed ED2 wrapper](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_05/provenance/flames_paper_snapshot/executed/flexiplex_ed2_native/run_native_ed2.R), [run manifest](../source_data/figure_05/provenance/splitseq/component_ED2_run_manifest.txt) |

The long-read input SHA-256 is `62acb6d466c37ba89632081526410bdc3ef73c0c68d778d40e05f03181f2a4f7`. The [preserved configuration archive](pinned_flames_configs.md) contains the FLAMES authors’ [component layout](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_05/provenance/flames_paper_snapshot/upstream/ChangqingW_FLAMES_figures/files/config_splitseq.json) and the executed ED2 wrapper, together with their source versions. Panels G–H use the ED2 component workflow above.

## Physical-cell and UMI counting

The [published cell map](../source_data/figure_05/provenance/splitseq/published_568_barcode_map.csv) links all 568 cells to the short-read UMI counts and the sample classes `MB_cells`, `MB_nuclei` and `MT_nuclei`. Cell identity combines the round-3 barcode, round-2 barcode and reverse-transcription well. Published IDs concatenate the first two barcodes and append a zero-based row-major well index: A1 is zero, B11 is 22 and D12 is 47. The [primer map](../data/figure_05/rt_primer_well_map.csv) converts both reverse-transcription primer variants from a well to its T-primer sequence.

| Component output | Normalized field |
|---|---|
| `Read` | Original read ID |
| `BC1`, `BC2`, `BC3` | Assignment barcode `BC3_BC2_BC1` |
| `UB` | Reverse-complemented UMI |
| `FlankEditDist` | Flank edit distance |

The [normalizer](../scripts/figure_05/normalize_component_stats.py) performs these conversions. The [aggregation script](../scripts/figure_05/aggregate_splitseq.py) counts distinct original read IDs and distinct exact UMI strings within each physical cell. A record contributes when its barcode and UMI are nonempty; all retained UMI lengths contribute. Summed per-cell read counts therefore represent read–cell pairs. Panel G instead uses original read IDs deduplicated across the full input.

Normalize and count the supplied records:

```bash
python3 scripts/figure_05/normalize_component_stats.py \
  --input data/examples/figure_05/splitseq/component_native_stats.tsv \
  --output results/figure05_component_assignments.tsv
python3 scripts/figure_05/aggregate_splitseq.py \
  --assignments results/figure05_component_assignments.tsv \
  --cells data/examples/figure_05/splitseq/cells.tsv \
  --rt-primers data/figure_05/rt_primer_well_map.csv --format component \
  --output results/figure05_component_cells.tsv \
  --report results/figure05_component_cells.json
```

Use `--format rad` for the [RAD example assignments](../data/examples/figure_05/splitseq/rad_assignments.tsv). The [example counts](../data/examples/figure_05/splitseq/component_bounded_counts.tsv) and [record description](../data/examples/figure_05/splitseq/PREVIEW.md) show the transformation from assignment records to physical-cell counts.

## Panels G and H

Panel G reports the fraction of input reads assigned with three valid barcode components. RAD assigns 2,498,488 distinct original reads, and the FLAMESv2 component workflow assigns 1,346,238, corresponding to 43.34% and 23.35% of the full input.

Panel H uses `published_sr_umi_cts` on the X axis and the exact long-read UMI count for the same physical cell on the Y axis. Each workflow retains its native read depth. Ordinary least-squares fits use untransformed UMI counts and a free intercept; both display axes are logarithmic. The [568-cell source table](../source_data/figure_05/splitseq_umi_panel_ED2_568.tsv), separate [myoblast-cell](../source_data/figure_05/splitseq_umi_panel_ED2_MB_cells.tsv), [myoblast-nucleus](../source_data/figure_05/splitseq_umi_panel_ED2_MB_nuclei.tsv) and [myotube-nucleus](../source_data/figure_05/splitseq_umi_panel_ED2_MT_nuclei.tsv) tables, and [regression coefficients](../source_data/figure_05/splitseq_umi_panel_ED2_regressions.tsv) supply the panel values.

| Sample | Physical cells | RAD UMIs | FLAMESv2 component UMIs |
|---|---:|---:|---:|
| Myoblast cells | 112 | 695,248 | 449,592 |
| Myoblast nuclei | 158 | 662,758 | 321,852 |
| Myotube nuclei | 298 | 533,698 | 281,300 |
| Total | 568 | 1,891,704 | 1,052,744 |

Restore the files in the [checkpoint manifest](../source_data/figure_05/provenance/splitseq/umi_panel_ED2_checkpoints.tsv) under `checkpoints/figure_05/`, then regenerate the complete per-cell table:

```bash
python3 scripts/figure_05/replay_splitseq_umi_panel.py --output-dir results/figure05_ED2
```

The replay checks each cell ID and per-cell read and UMI count against the source table. [Input hashes](../source_data/figure_05/splitseq_umi_panel_ED2_files.tsv) identify the assignment files, and the [Prism validation record](../source_data/figure_05/provenance/splitseq/umi_panel_ED2_validation.json) identifies the data tables, graphs and layout used for panel H.
