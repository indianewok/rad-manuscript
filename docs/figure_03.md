# Figure 3 — assignments to excluded targets and barcode correction

Figure 3 tests how often tools assign reads to supplied target lists that exclude the matched reference, then examines barcode correction in LongBench single-cell and single-nucleus ONT and PacBio data. The supplied-list challenges count original physical reads. The correction analysis counts unique original-read–target-barcode pairs.

![Figure 3](../figures/figure_03/prism/figure_03.png)

## Supplied-list challenges

Three target lists were sampled independently for each dataset after removing its matched reference from the chemistry catalog. Every tool received the same complete input and target list within a replicate. These list draws are technical randomizations.

| Input | Reads | Chemistry catalog | Excluded reference | Target-list size | List seeds |
|---|---:|---|---|---:|---|
| ScTagger-L, uniform Q20 | 4,993,805 | 6,794,880 3v3 barcodes | 5,000 source barcodes | 5,000 | 20260813, 20260814, 20260815 |
| LongBench SC-ONT | 10,000,000 | 6,794,880 3v3 barcodes | 5,211 filtered Cell Ranger barcodes | 5,211 | 2026081301, 2026081302, 2026081303 |
| RAGE-seq cell-line mixture, ERR3268991 | 20,346,396 | 737,280 3v2 barcodes | 4,505 filtered Cell Ranger barcodes | 4,505 | 2026102301, 2026102302, 2026102303 |

The LongBench subsample used SeqKit 2.8.2 with seed `2026081326`. List sampling used Python 3.9.16 `random.Random`. The RAGE preparation samples without replacement from the sorted catalog after reference exclusion and barcode-suffix normalization.

## Software and parameters

| Analysis | RAD | BLAZE | Flexiplex |
|---|---|---|---|
| RAGE supplied-list challenge | 1.0.2, `cd0582b2440cde0f35725dc557fa47307d74d374`; offensive correction, `-M 2 -m 2 -z 5000`; 16 workers and 2 compression threads | 2.6.0a0, `af8d2cc9f6374caf4d1006d5f8a0e99097211646`; supplied-list mode, Q15, barcode distance 2, EmptyDrops disabled; 16 threads; `PYTHONHASHSEED=20261023` | 1.02.6, `d84c8ae4f3865052f2b5ecec816949b94682f302`, with raw-barcode diagnostic patch; `-d 10x3v2 -f 8 -e 2 -k LIST -p 16`; 2 compression threads |
| ScTagger-L and LongBench supplied-list challenges | Same RAD source commit; offensive correction, mutation limits 2/2, chunks of 5,000, 32 threads, 3v3 layout with 12-base UMI | 2.6.0a0, same source commit; supplied-list mode, Q15, barcode distance 2, EmptyDrops disabled; 32 threads | Same diagnostic build; `-d 10x3v3 -f 8 -e 2 -k LIST -p 28`; 4 compression threads |
| LongBench correction analysis | 1.0.2, `4acbe004ba11b150d6832395452632f367a6e6c1`; offensive correction, mutation limits 2/2, minimum read length 85, chunks of 5,000; 24/60/28/60 workers for SC-ONT/SN-ONT/SC-PB/SN-PB, plus 4 compression threads; concatemer records retained | 2.5.0; expected cells 5,000 for single cells, forced cells 10,000 for nuclei; 48 threads, 3v3 defaults, `PYTHONHASHSEED` unset | Same diagnostic build; discovery flank distance 0; selected-list demultiplexing with flank distance 8, barcode distance 2, and 16 threads |

Flexiplex’s diagnostic field `RawCellBarcode` records the extracted sequence before correction. The [source, patch, binary, and build instructions](../vendor/flexiplex-audit/) define the modified build. Its binary SHA-256 is `38dccd37f1747e5105b62eacde572b7e4c5206fb925dc1fdbe8210ffe8b1e8c4`. Keep `FLEXIPLEX_AUDIT_SOURCE_FILE` unset in the RAGE challenge; the reference is used to exclude targets during list preparation.

The RAGE RAD build has SHA-256 `fc424779c1aba3f112930b4ec8c0dc874b421a217bd53ce6f227e719489a2b2d`. The [BLAZE dependency lock](../environments/figure_3_blaze_2.6.0a0.txt) specifies the environment. The retained ScTagger/LongBench off-list records omit the BLAZE hash seed and optional Flexiplex source-filter environment setting. The LongBench correction records preserve BLAZE 2.5.0 and recovered source commit `11994f9c12a6664dfe1679576aaca19b6bfd35c1`, but omit an executable hash.

## From output records to physical-read counts

Tool output identifiers are resolved to original input identifiers by removing the documented orientation, concatemer, or barcode decorations. RAD targets come from `CB:Z:` and raw barcodes from `CR:Z:`. Reverse-orientation RAD raw barcodes are reverse-complemented once. An explicit empty native RAD CR uses the target as its source. BLAZE sources come from its putative-barcode CSV; Flexiplex sources come from its diagnostic table.

For the supplied-list challenges, an original read counts only when it has exactly one assignment record in the complete output. Every identifier with multiple records is excluded, including repeated records to the same target. All supplied targets remain in the per-target table, including those with zero counts.

The [assignment examples](../data/examples/figure_03/selection_manifest.json) include original reads, emitted records, parsed fields, and their full source hashes. For example:

```text
original read: e7985c56-3434-4733-83c7-41fd5ab8249c
RAD record:    e7985c56-3434-4733-83c7-41fd5ab8249c-F
raw barcode:   TACCCATAGAAACCGC
target:        TACTCATAGAAACCGC
```

This RAGE read has one assignment in the complete RAD replicate-1 output. Its target receives ten physical reads in the [complete target table](../data/examples/figure_03/rage_raw_to_rad_C5_targets.tsv). Those ten contribute to the replicate total of 50,349.

Run a complete target-level counting example with:

```bash
mkdir -p results
python3 scripts/revision/figure_3_example_count.py \
  data/examples/figure_03/sctagger_rad_rep1_assignments.tsv \
  data/examples/figure_03/sctagger_rad_rep1_targets.txt results/sc_counts.tsv
```

The [expected output](../data/examples/figure_03/sctagger_rad_rep1_counts.tsv) contains ten reads for `AAACCCACACAGTGAG`. The example includes all assignments to that target and every other record sharing one of those original identifiers. The [duplicate example](../data/examples/figure_03/actual_duplicate_assignments.tsv) contains two records for one original read; both are excluded.

Flexiplex counts use its diagnostic stream. The [diagnostic example](../data/examples/figure_03/longbench_flexiplex_rep1_diagnostic.tsv) contains the fields `Read`, `CellBarcode`, `RawCellBarcode`, `FlankEditDist`, `BarcodeEditDist`, and `UMI`. The complete stream comparison found 4/1/0 diagnostic-only assignments in the three retained LongBench challenges and zero in ScTagger. The matched RAGE runs contain 119/149/156 diagnostic-only assignments. These records contribute to the diagnostic assignment counts.

The complete counting workflow checks conservation of the input read universe:

```text
input reads = strict assigned reads + excluded ambiguous reads + unassigned reads
```

The source-table summary reports `100 × strict assigned reads / input reads`; saved Prism panel B shows total assigned reads. Panel C uses per-target counts from replicate 1. [Off-list totals](../source_data/figure_03/offlist_totals.tsv) and [per-target counts](../source_data/figure_03/offlist_per_target.tsv.gz) retain the plotted values and denominators.

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

For the example BLAZE target, 1,861 Failure Mode 2 pairs among 13,809 total pairs give 13.4767%. [Expected output](../data/examples/figure_03/correction_C6_output.tsv), [per-target correction counts and percentages](../source_data/figure_03/correction_per_target.tsv.gz), and [correction totals](../source_data/figure_03/correction_totals.tsv) connect this calculation to panels E–G. All twelve complete per-target tables and selected target lists passed identity checks. Reconstruction of individual pair overlaps additionally requires the original source-bearing assignment streams, which are absent from their recorded paths.

## Repeat the matched RAGE experiment

The experiment requires the ordered ERR3268991 FASTQ, Python 3.9.16, `pigz`, and the pinned tools. The [4,505-barcode reference](../data/figure_03/rage_matched_reference_4505.txt) and [3v2 catalog](../data/figure_03/chemistry_3v2_catalog.txt.gz) are included with [hashes](../data/figure_03/source_manifest.tsv). The [public input guide](rage_public_input_order.md) describes acquisition and restoration of the selected read order. RAD calibrates its layout from the start of the input, so the order is retained as part of the experiment.

The ordered-ID checkpoint is `checkpoints/figure_03/rage_matched/counts/input_original_ids.txt.gz`, SHA-256 `e4831a95828b65f21253c9f1058f1af9ef2fa7abe286321d88aaffba12ab2952`. The required canonical ordered-record hash is `a5f866d6180b46e0acbd3aa2526364060c152380714b00ec0ed74b8c1e8c24af`. Preflight checks the complete identifiers, sequences, and qualities against that hash, with 20,346,396 unique reads and 16,466,857,803 sequence bases.

Build RAD from the recorded source and install BLAZE:

```bash
cmake -S /path/to/rad_cd0582_source -B /path/to/rad_build \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
cmake --build /path/to/rad_build -j4
python3.9 -m venv /path/to/blaze_env
/path/to/blaze_env/bin/pip install -r environments/figure_3_blaze_2.6.0a0.txt
/path/to/blaze_env/bin/pip install --no-deps \
  'git+https://github.com/shimlab/BLAZE.git@af8d2cc9f6374caf4d1006d5f8a0e99097211646'
```

The recorded RAD build used GCC 8.5, Boost 1.74, zlib 1.2.11, and `-O3 -DNDEBUG -std=gnu++17 -fopenmp`. Prepare and verify the experiment:

```bash
python3 scripts/revision/figure_3_rage_prepare.py \
  --input /path/to/rageseq.fq.gz \
  --reference data/figure_03/rage_matched_reference_4505.txt \
  --catalog data/figure_03/chemistry_3v2_catalog.txt.gz \
  --rad-source /path/to/rad_cd0582_source --build-rad \
  --blaze-python /path/to/blaze_env/bin/python --blaze-entrypoint /path/to/blaze_env/bin/blaze \
  --flex-binary vendor/flexiplex-audit/bin/flexiplex_v1.02.6_raw_to_assigned_audit
python3 scripts/revision/figure_3_rage_preflight.py
```

Run all three tools with each of the three list replicates, then count:

```bash
python3 scripts/revision/figure_3_rage_run.py RAD 1
python3 scripts/revision/figure_3_rage_run.py BLAZE 1
python3 scripts/revision/figure_3_rage_run.py Flexiplex 1
# Repeat with replicate numbers 2 and 3.
python3 scripts/revision/figure_3_rage_count.py
```

The [scheduler array](../scripts/revision/figure_3_rage_array.sbatch) runs these nine combinations. Complete assignment ledgers and input identifiers are stored under `checkpoints/figure_03/rage_matched/`. The retained ScTagger and LongBench streams can be recounted with `python3 scripts/revision/figure_3_count.py offlist`; all eighteen comparisons matched.

## Summaries and source-table reconstruction

The mean percentage of input reads assigned to excluded targets, with the range across three list draws, is:

| Dataset | RAD | BLAZE | Flexiplex |
|---|---:|---:|---:|
| ScTagger-L | 0.983 (0.981–0.987) | 5.995 (5.891–6.102) | 9.257 (9.187–9.319) |
| LongBench SC-ONT | 0.467 (0.465–0.470) | 10.425 (10.054–10.976) | 13.858 (13.644–14.226) |
| RAGE-seq | 0.248 (0.247–0.250) | 6.889 (6.733–6.975) | 8.035 (7.838–8.144) |

Recreate these arithmetic summaries, rebuild tables from mounted checkpoints, and run the table checks with:

```bash
python3 scripts/revision/figure_3_summary.py
python3 scripts/revision/figure_3.py build --project-root /path/to/reviewer_comment_data
python3 scripts/revision/figure_3.py validate
python3 scripts/revision/figure_3.py render
```

[Panel bindings](../source_data/figure_03/panel_data_manifest.tsv), the [schema](../source_data/figure_03/schema.json), and [checksums](../source_data/figure_03/checksums.json) identify each plot’s table, keys, metric, and units. The renderer produces numerical-check plots from these tables.
