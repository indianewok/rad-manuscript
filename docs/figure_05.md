# Figure 5 — receptor recovery and LR-Split-seq

Figure 5 compares recovery of receptor reads from a mixture of Ramos B cells, Jurkat T cells and monocytes, then tests demultiplexing of the three-component LR-Split-seq barcode. The receptor experiment uses RAGE-seq accession **ERR3268991**. The LR-Split-seq comparison pairs long-read **SRR13948564** with short-read **SRR13948565** and follows the same 568 published physical cells through both workflows.

![Figure 5](../figures/figure_05/prism/figure_05.png)

## Software and inputs

| Analysis | Software and settings | Code and command |
|---|---|---|
| RAD receptor counts | Intended settings: 10x 3′ layout, offensive correction, generated/whitelist edit distance 2, chunk size 10,000, 32 threads. The successful producing run is still needed. | [Retained execution log](../source_data/figure_05/provenance/RAD_candidate_producer_failure.txt) |
| BLAZE receptor counts | BLAZE 2.6.0a0; 4,505 expected cells, 10x 3v2, 32 threads, edit distance 2 | [Executed command](../source_data/figure_05/provenance/BLAZE_receptor_command.txt) |
| Flexiplex receptor counts | Flexiplex 1.02.5; 10x3v2, flank edit distance 8, 56 threads, 3,259 selected barcodes. Barcode discovery used 1.02.6. | [Wrapper](../source_data/figure_05/provenance/Flexiplex_receptor_producer.sh), [execution and input hashes](../source_data/figure_05/provenance/Flexiplex_receptor_execution.md) |
| Receptor alignment | minimap2 2.26-r1175, `-x map-ont --secondary=no -t 20`; TRUST4 human BCR/TCR reference | Reference SHA-256 `615152a7481d0a68557ab0a84b735d8f25fc1ee9d5076af3b8d31aa7792dc3df` |
| LR-Split-seq RAD | RAD 1.0.2, commit `b6853a3d3d1818130ac364f7937bd0690ae9e385`; `--joint-bc-mode strict`, defensive correction, generated/whitelist edit distance 2, minimum read length 0, chunk size 5,000, four threads | [Barcode processing and strict component acceptance](https://github.com/indianewok/rad/blob/b6853a3d3d1818130ac364f7937bd0690ae9e385/include/rad/sigstring.hpp#L3173-L3288), [barcode/UMI output](https://github.com/indianewok/rad/blob/b6853a3d3d1818130ac364f7937bd0690ae9e385/include/rad/sigstring.hpp#L4377-L4519), [command](../source_data/figure_05/provenance/splitseq/RAD_time.txt), [layout](../data/figure_05/splitseq_reverse_complemented_whitelist_layout.csv) |
| LR-Split-seq component workflow | FLAMES 2.7.1, commit `bf2211a8da1e1c7327370ab12479ae70e1d37cd8`, embedded Flexiplex 1.02.6; three separately matched 8-nt barcode components, barcode edit distance 1 and buffer 1, flank edit distance 3, 10-nt UMI template, terminal fixed eight-thymidine segment, `reverse_complement=FALSE`, four threads | [Executed layout and processing call](https://github.com/indianewok/rad-manuscript/blob/90f819fde9bdf7cf72cb965ff9a9c386c9f588a7/source_data/figure_05/provenance/splitseq/component_runner.R#L67-L107), [FLAMES segment definitions](https://github.com/mritchielab/FLAMES/blob/bf2211a8da1e1c7327370ab12479ae70e1d37cd8/R/find_barcode.R#L87-L143), [component matching](https://github.com/mritchielab/FLAMES/blob/bf2211a8da1e1c7327370ab12479ae70e1d37cd8/src/main-functions/flexiplex.cpp#L305-L362), [command](../source_data/figure_05/provenance/splitseq/component_time.txt) |

The component catalogs contain [96 ligation sequences](../data/figure_05/bc_8nt_v1.csv) and [96 reverse-transcription sequences](../data/figure_05/bc_8nt_v2.csv). The two reverse-transcription primers from each well map to one of 48 physical wells. The long-read input SHA-256 is `62acb6d466c37ba89632081526410bdc3ef73c0c68d778d40e05f03181f2a4f7`.

The LR-Split-seq wrapper calls the FLAMES [C++ demultiplexing entrypoint](https://github.com/mritchielab/FLAMES/blob/bf2211a8da1e1c7327370ab12479ae70e1d37cd8/src/main-functions/flexiplex.cpp#L955-L981) through its [Rcpp binding](https://github.com/indianewok/rad-manuscript/blob/90f819fde9bdf7cf72cb965ff9a9c386c9f588a7/source_data/figure_05/provenance/splitseq/component_runner.R#L41-L65).

## Receptor-read counts

Demultiplexer assignments are joined to receptor alignments by original read ID and to cell annotations by barcode. The [Flexiplex join script](../source_data/figure_05/provenance/join_flexiplex_bcrtcr.py) removes ambiguous read assignments, applies the BCR/TCR alignment rule and aggregates counts by barcode. The cell-identity map contains 1,993 Ramos cells, 1,572 Jurkat cells and 20 monocytes; the discovery reference contains 4,505 cells.

Each receptor class has native and corrected-only counts. In the Flexiplex source table, the column named `corrected` contains native plus corrected reads, so the native count is subtracted to obtain corrected-only reads. The RAD and BLAZE source columns already contain corrected-only counts. For Ramos barcode `AAACCTGAGAATCTCC`, Flexiplex BCR counts are 713 native and 1,413 cumulative, giving 700 corrected-only reads and 1,413 assigned reads.

Run this transformation on the [example input](../data/examples/figure_05/flexiplex_receptor_input.tsv):

```bash
mkdir -p results
python3 scripts/figure_05/exclusive_receptor_counts.py \
  --input data/examples/figure_05/flexiplex_receptor_input.tsv \
  --output results/figure05_receptor_counts.tsv \
  --tool Flexiplex --corrected-column cumulative
```

The [expected output](../data/examples/figure_05/flexiplex_receptor_output.tsv) contains nine receptor-class rows. Use `--corrected-column exclusive` for the RAD and BLAZE tables. The complete [per-cell table](../source_data/figure_05/candidate_receptor_counts.tsv) and [totals](../source_data/figure_05/candidate_receptor_totals.tsv) retain the source selection labels. Their assigned-read totals are 7,808,411 for RAD, 5,588,936 for BLAZE and 6,595,231 for Flexiplex. [Example records and extraction details](../data/examples/figure_05/PREVIEW.md) connect individual assignments to these tables.

## Map LR-Split-seq records to physical cells

The [cell list](../data/figure_05/splitseq_cells.tsv) identifies all 568 published cells. Each cell is defined by its round-3 barcode, round-2 barcode and reverse-transcription well. The published ID concatenates round 3 and round 2, followed by `_` and a zero-based row-major well index: A1 = 0, B11 = 22 and D12 = 47. The [primer map](../data/figure_05/rt_primer_well_map.csv) converts both reverse-transcription primer variants from a well to its T-primer sequence.

| Source field | Conversion |
|---|---|
| Component `Read` | Original `read_id` |
| Component `BC1`, `BC2`, `BC3` | Assignment barcode `BC3_BC2_BC1` |
| Component `UB` | UMI = reverse complement of `UB` |
| Component `FlankEditDist` | Retained flank distance |
| RAD `normalized_barcode`, `umi`, `read_id` | Saved normalized assignments |
| `prism_row_1based`, `sample` | Original Prism row and published sample annotation |

Records with a nonempty barcode and UMI contribute to the comparison. The [normalization code](../scripts/figure_05/normalize_component_stats.py#L17-L24) constructs the barcode and UMI fields; the [cell-level aggregation code](../scripts/figure_05/aggregate_splitseq.py#L30-L67) counts distinct original read IDs and exact UMI strings within each physical cell. Thus, summed read counts represent read–cell pairs. UMI inclusion uses the saved nonempty-string rule.

Normalize the [component example records](../data/examples/figure_05/splitseq/component_native_stats.tsv), then aggregate them by cell:

```bash
python3 scripts/figure_05/normalize_component_stats.py \
  --input data/examples/figure_05/splitseq/component_native_stats.tsv \
  --output results/figure05_component_assignments.tsv
cmp results/figure05_component_assignments.tsv data/examples/figure_05/splitseq/component_assignments.tsv

python3 scripts/figure_05/aggregate_splitseq.py \
  --assignments results/figure05_component_assignments.tsv \
  --cells data/examples/figure_05/splitseq/cells.tsv \
  --rt-primers data/figure_05/rt_primer_well_map.csv --format component \
  --output results/figure05_component_cells.tsv --report results/figure05_component_cells.json
```

The [expected component counts](../data/examples/figure_05/splitseq/component_bounded_counts.tsv) and [RAD counts](../data/examples/figure_05/splitseq/rad_bounded_counts.tsv) cover the example records. For RAD, use `--format rad` and its [assignment file](../data/examples/figure_05/splitseq/rad_assignments.tsv). The [record preview](../data/examples/figure_05/splitseq/PREVIEW.md) and [extraction receipt](../data/examples/figure_05/splitseq/extraction.json) preserve the original source rows.

## Reproduce the complete comparison

Restore the RAD and component Flexiplex assignment checkpoints under `checkpoints/figure_05/`, then run:

```bash
python3 scripts/figure_05/replay_splitseq.py --root .
```

This recounts the complete RAD and component assignment ledgers and compares every read and UMI count with the [568-cell source table](../source_data/figure_05/splitseq_reads_umis_568.tsv). All 2,272 counts match.

| Quantity | RAD ED2 | Component Flexiplex + poly-T |
|---|---:|---:|
| Full-input assignment rows | 2,536,299 | 1,345,255 |
| Distinct original reads across the full input | 2,498,488 | 1,338,285 |
| Fraction of 5,764,421 input reads | 43.34% | 23.22% |
| Read–cell pairs across 568 published cells | 2,078,171 | 1,156,252 |
| Distinct reads among those cells | 2,063,573 | 1,152,260 |
| Median reads per cell | 1,979.5 | 1,102.5 |
| Exact cell–UMI pairs | 1,891,704 | 1,050,292 |
| Median UMIs per cell | 1,866 | 1,042 |

The [summary table](../source_data/figure_05/splitseq_summary.tsv) retains exact numerators and denominators. The component workflow's full-input fraction is 23.22% for distinct reads and 23.34% for assignment rows; the earlier 23.35% annotation requires correction.

The saved read-count comparison uses a [two-sided paired t-test](../source_data/figure_05/splitseq_saved_paired_t_test.json): 568 cell pairs, t = 14.959474687143327, df = 567 and P = 6.890554214980993e-43.

To extract the examples again, run `python3 scripts/figure_05/extract_splitseq_examples.py`.

## Additional source records

Complete reconstruction of the receptor panels requires the successful RAD producing run and the mapping between the retained receptor tables and the plotted datasets. The long-read/short-read UMI comparison also requires its depth-matched short-read checkpoint or the sampling rule and seed.
