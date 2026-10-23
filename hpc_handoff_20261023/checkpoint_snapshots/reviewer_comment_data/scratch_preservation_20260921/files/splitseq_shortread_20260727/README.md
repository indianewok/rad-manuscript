# Matched short-read data for the long-read SPLiT-seq experiment

Workspace: `/scratch-nfs/f005f43/splitseq_shortread_20260727/`
Built 2026-07-27.

## 1. What the long-read file is, and what matches it

`rad_data/raw_fastq_datasets/splitseq.fq.gz` has read headers `@SRR13948564.<n>`.

| | run | GSM | title | platform | spots |
|---|---|---|---|---|---|
| **long read (local)** | SRR13948564 | GSM5169183 | `C2C12_long_1k` | PacBio Sequel II | 5,764,421 |
| **matched short read** | **SRR13948565** | **GSM5169184** | **`C2C12_short_1k`** | Illumina NextSeq 500, paired | **70,535,160** |

Series **GSE168776** / BioProject **PRJNA713904**. Paper: Rebboah et al., LR-Split-seq,
Genome Biology 2021 (PMID 34620214). C2C12 mouse myoblast/myotube, Parse Biosciences
Single Cell Whole Transcriptome Kit (= SPLiT-seq); Illumina side processed with `split-pipe`.

`SRR13948565` is the match: same `_1k` sublibrary, and GEO growth / treatment / extract
protocol fields are **byte-identical** between GSM5169183 and GSM5169184.

Not matched — same series, different material:
- `SRR13948566-571` (GSM5169185-190) = `C2C12_short_9kA..F`, a separate ~9k sublibrary, short-read only.
- `SRR14333205-212` (GSM5267107-114) = snATAC-seq.

## 2. Read 2 architecture (86 nt barcode read)

```
[ UMI 10 ][ BC3 8 ][ LINK_A 30 ][ BC2 8 ][ LINK_B 22 ][ BC1 8 ]
0        10       18           48       56           78      86

LINK_A = GTGGCCGATGTTTCGCATCGGCGTACGACT
LINK_B = ATCCACGTGCTTGAGACTGTGG
```

Read 1 (74 nt) is cDNA and is **not needed** for barcode/UMI work.

This is confirmed independently by the lab's own long-read layout
(`rad_data/20250514_splitseq_out/splitseq_layout.csv`): its `rc_` strand is element-for-element
identical, with the same two linker sequences at the same offsets. **Short-read R2 is in the same
orientation as RAD's `reverse`/`rc_` elements**, so barcode strings join directly with no
reverse-complementing.

Round naming matches RAD's exactly: RAD `barcode_1` = BC1 (round-1 RT), `barcode_2` = BC2
(round-2 ligation), `barcode_3` = BC3 (round-3 ligation). The long-read CSV also carries a
10 nt `umi` element, so UMI-level comparison is possible on both sides.

## 3. Whitelists (the part that bites)

- **Rounds 2 and 3 share one 96-barcode ligation set** with a shared plate map
  (0 well disagreements across all 96). → `ref/lig_bc_well_map.tsv`
- **Round 1 (RT) has its own 96 barcodes, but only 48 wells — exactly 2 barcodes per well.**
  That is the oligo-dT / random-hexamer primer pair in the same well; both label the *same cell*.
  → `ref/rt_bc_well_map.tsv`

  **A raw BC1+BC2+BC3 triple therefore splits every cell in two.** Round 1 must be collapsed to
  its well. The published identifier does exactly this, and this pipeline reproduces it:

  ```
  cell_bc = BC3seq + BC2seq + "_" + rnd1_well        e.g. CAAGGAGCATAGCGAC_22
  ```

- **The complete 96-barcode whitelists already exist locally** at
  `~/whitelists/splitseq_barcodes/`: `bc_8nt_v1.csv` (96, ligation rounds 2 & 3) and
  `bc_8nt_v2.csv` (96, round-1 RT). Both verified **identical** to the sets derived here
  from the reads, and to LR-splitpipe's `bc_data_v1/v2.csv`. `old/read_layouts/splitseq_rl.csv`
  wires them up and confirms the round mapping (`barcode_1`→v2 RT, `barcode_2`/`3`→v1 ligation).
- `20250514_splitseq_out/splitseq_whitelist.csv` is **not** a reference whitelist — it is RAD's
  *observed/corrected output* for that run (note its `total_count` / `corrected_count` /
  `filtered_count` columns). It holds only the 95 per round actually seen, missing `AAACATCG`
  (ligation) and `AAACGATA` (RT). Don't use it as an input whitelist.

Plate layout recovered from round-1 wells: `MB_cells` 0-11, `MB_nuclei` 12-23, `MT_nuclei` 24-47.

## 4. Results

70,535,160 reads parsed; **53,832,603 assigned (76.3%)**; 27,997,009 distinct (cell, UMI) pairs
across 323,418 barcodes. Unassigned reads are dominated by TSO and Illumina adapter read-through
plus NextSeq poly-G, i.e. genuinely non-barcode reads.

| file | contents |
|---|---|
| `results/barcode_umi_counts.tsv.gz` | `cell_bc, umi, n_reads` — every observed UMI (28.0 M rows) |
| `results/umis_per_barcode.tsv` | `cell_bc, bc3/bc2 seq, rnd1/2/3 well, rt_barcodes_reads, n_reads, n_umis_raw, n_umis_collapsed` |
| `results/validation_vs_published.tsv` | per-cell join to the published split-pipe metadata |
| `results/parse_stats.json` | read-level accounting |

### Validation against the published split-pipe output
- **568/568 published cells recovered (100%).**
- Top 568 barcodes by UMI contain 559/568 published cells; top 2000 contain all 568.
- **Pearson r = 0.9853, Spearman r = 0.9908** (my `n_umis_raw` vs published `umi_count`).
- Median ratio mine/published = 1.19 — expected, since split-pipe counts only UMIs on reads that
  align to a gene, whereas this table is barcode-level and makes no alignment requirement.

### Use `n_umis_raw`, not `n_umis_collapsed`
The directional (Hamming-1) UMI collapse **over-merges badly here and should not be used**:

| | vs published `umi_count` |
|---|---|
| `n_umis_raw` | Pearson **0.9853** |
| `n_umis_collapsed` | Pearson 0.8660, median ratio 0.75 |

Reason: the UMI is only 10 nt (4^10 = 1,048,576). The deepest cells hold ~495k distinct UMIs —
**47% occupancy**, so an average UMI has ~14 of its 30 one-mismatch neighbours occupied *by chance*.
Network collapse then chains most of the cell into a few components. The column is retained for
transparency but is not a corrected count at these depths.

## 5. CSV deliverables (`csv/`)

Both files are `cell_bc, umi, n_reads` — `n_reads` is already the count of that UMI in
that barcode, i.e. reads per UMI per cell.

| file | source | rows | notes |
|---|---|---|---|
| `sr_barcode_umi_reads_fastq.csv.gz` | my parse of all 70.5 M raw reads | 27,997,009 | **no alignment filter**; Hamming-1 barcode correction; raw UMIs |
| `sr_barcode_umi_reads_bam.csv.gz` | ENCODE STARsolo `CB`/`UB` | 14,529,564 | corrected barcode + corrected UMI; mapped reads only |
| `sr_umis_per_barcode_bam.csv` | rollup of the above | — | `cell_bc, sample, rnd1_well, n_reads, n_umis` |

### The 568 called cells (`csv/called_cells_*`)

| | cells | reads | UMIs |
|---|---|---|---|
| `called_cells_barcode_umi_reads_fastq.csv.gz` | 568 | 41,274,093 | **17,648,026** |
| `called_cells_barcode_umi_reads_bam.csv.gz` | 568 | 21,338,304 | 9,193,269 |
| published split-pipe `umi_count` | 568 | — | 15,576,257 |

`called_cells_summary.csv` has all of these per cell alongside `rnd1/2/3_well` and
`published_gene_count`. 63% of all UMI rows in both tables belong to these 568 cells; the
other 37% are spread over ~322,850 ambient barcodes.

**Use the FASTQ table for the 568 cells.** It tracks the published counts closely
(17.65 M vs 15.58 M, ratio 1.13 — the residual is split-pipe's gene-assignment requirement).

**The BAM table is NOT depth-matched** and its absolute UMI counts must not be compared to
either of the others: it holds only **52% of the reads** for these cells (21.3 M vs 41.3 M;
per sample 0.61 / 0.46 / 0.52), because ENCODE's deposited FASTQs are already a filtered
subset (~31 M reads) before alignment and `CB`/`UB` dropout. Its value is per-read
*behaviour* (EditDist-2 matching, per-gene `1MM_CR` dedup), not totals — mean reads/UMI
agrees closely with the FASTQ table (2.32 vs 2.34) even though the totals differ ~2x.

The BAM table is ~30% smaller by construction, for two stacking reasons: only mapped reads
are in a BAM at all (8.53 M primary alignments vs my 13.05 M assigned reads for MB_cells),
and reads with `CB:Z:-` or `UB:Z:-` are dropped (603,123 / 1,044,370 / 1,079,683 for
MB_cells / MB_nuclei / MT_nuclei). This is not disagreement between the two tables.

Mean reads/UMI: **2.34** over the 568 called cells (41,274,093 / 17,648,026, FASTQ table);
**1.92** over all barcodes.

### Cross-validation of the two tables
- BAM barcodes are a **strict subset** of the FASTQ ones: 67,422 of 323,418, with
  **0 barcodes present in the BAM but missing from the FASTQ table**. So the Hamming-1
  parse missed nothing STARsolo found, despite STARsolo using looser EditDist-2 matching.
- 568/568 called cells present in both.
- UMIs per cell on the called cells: Pearson **r = 0.930**, median BAM/FASTQ ratio 0.56
  (the alignment + `CB`/`UB` dropout described above).
- **Mean reads per UMI agrees to within 1%: 1.923 (FASTQ) vs 1.942 (BAM).** Absolute counts
  differ ~2× because of the filtering, but the reads-per-UMI statistic itself is stable
  across both — it is the robust quantity to compare RAD against.

### ENCODE source BAMs (`bam/`, mm10 + GENCODE M21, STAR 2.7.10a)
`ENCFF130UOQ` MB_cells (wells 0-11) · `ENCFF340PFO` MB_nuclei (12-23) ·
`ENCFF360KJP` MT_nuclei (24-47). Tags: `CB CR CY UB UR UY gx gn`.
Their STARsolo params independently confirm the parse spec in §2:
`--soloCBposition 0_10_0_17 0_48_0_55 0_78_0_85`, `--soloUMIposition 0_0_0_9`.

Sampling ~3,800 reads from each: 100% of bc1/bc2/bc3 in the whitelists, and rnd1 wells
partition exactly 0-11 / 12-23 / 24-47 with zero leakage.

Reading these BAMs over https emits `samtools view: error closing ...: -1`. It is
**benign** — streamed and locally-downloaded extractions are md5-identical.

## 6. Reproduce

```bash
python3 parse_bc_umi.py \
  --r2 fastq/SRR13948565_2.fastq.gz \
  --rt-map ref/rt_bc_well_map.tsv \
  --lig-map ref/lig_bc_well_map.tsv \
  --outdir results --threads 48
python3 validate.py
```

`dl.sh` re-downloads the run (prefetch + fasterq-dump + pigz; ~22 min on 128 cores).
