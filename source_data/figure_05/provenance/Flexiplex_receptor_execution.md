# Flexiplex receptor-read processing

**Flexiplex 1.02.5**, 10x3v2, flank distance eight, 56 threads and the 3,259-barcode selected list. **minimap2 2.26-r1175** uses `-x map-ont --secondary=no -t 20` against the TRUST4 human BCR/TCR reference. Python **3.9.16** joins barcode assignments, receptor alignments and cell-type annotations.

The [producing script](Flexiplex_receptor_producer.sh) streams the same RAGE-seq FASTQ to Flexiplex and minimap2, writes the barcode and alignment tables, then runs [join_flexiplex_bcrtcr.py](join_flexiplex_bcrtcr.py). It checks both stream branches and the join exit status.

## Inputs

| Input | Size or identity | SHA-256 |
|---|---|---|
| RAGE-seq FASTQ | 20,346,396 reads; 16,922,373,879 compressed bytes | `cfdba50a497dd4f6b24c2a4e730e297a09498ad5fe006f65eee01fa202bcdcec` |
| Selected list | 3,259 unique barcodes; count sum 2,762,471; 69,318 bytes | `6efd9352872b06db447e540457757c3a5e50b00d654bfcd7c6e658e8786a41b9` |
| `hg38_bcrtcr.fa` | TRUST4 human receptor reference | `615152a7481d0a68557ab0a84b735d8f25fc1ee9d5076af3b8d31aa7792dc3df` |
| Cell-type map | `rageseq_barcode_celltype_map.csv` | `5d398b62c37b10e0a080f7e84321c11edb7fb0a1e2badef27209186e57e80f95` |
| Join script | `join_flexiplex_bcrtcr.py` | `5486f574028de3cfd62b505c41d8de2a99ae2c509f93c73ecc314e122bef0b99` |

The producing script names the input locations under `external_data/` and the output directory. Its runtime uses libstdc++ 13.2, gzip 1.9, GNU bash 4.4.20 and GNU Awk 4.2.1.

## Assignment and receptor counts

Flexiplex identifies barcodes in 6,665,219 original reads and emits 6,755,575 diagnostic records. The join excludes 69,988 ambiguous original read IDs and retains **6,595,231 assigned reads**. The tool log reports 45,612 reads with more than one barcode.

| Receptor class | All assigned reads | Native reads |
|---|---:|---:|
| BCR | 2,985,039 | 1,418,603 |
| TCR | 1,126,957 | 536,531 |
| Unmapped | 2,483,235 | 1,097,692 |
| Total | 6,595,231 | 3,052,826 |

The source summary's `corrected` columns contain all assigned reads. Subtract native counts once to obtain corrected-only counts, as shown in the [Figure 5 example](../../../data/examples/figure_05/PREVIEW.md).

The reduced alignment table contains 16,233,872 rows for 11,467,989 unique read IDs: 10,459,673 BCR rows and 5,774,199 TCR rows. The unique alignment rate is 56.3637% of input reads; the barcode-found rate is 32.7587%, and the ambiguity-filtered assignment rate is 32.4147%.

## Outputs

| File | Contents |
|---|---|
| `rage_flex_f8_full_reads_barcodes.txt` | Diagnostic barcode assignments |
| `rage_bcrtcr_hits.tsv` | Read ID, receptor target and alignment-match count |
| `flexiplex_per_barcode_bcrtcr.tsv` | Per-barcode native and cumulative receptor counts |
| `flexiplex_bcrtcr_summary.tsv` | Receptor totals by cell type |
| `flexiplex_bcrtcr_data11_shape.tsv` | Receptor totals in the plotting-table arrangement |

The output tables contain 3,259 selected barcodes and 24 summary rows. The source `SHA256SUMS.txt` identifies the full input, reference, scripts and outputs. Flexiplex, the alignment stream and the join each exited with status zero.
