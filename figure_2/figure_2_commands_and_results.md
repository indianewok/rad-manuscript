# Figure 2: Whitelist Detection Benchmarking — Commands and Results

Date: 2026-03-16

All paths below reference variables defined in [`../config.sh`](../config.sh) (or your local override in `config.local.sh`).

## Software Versions

- **RAD**: commit `2a37ac9e01a453b5d6c1423f1f1b6b7023b8276f` (2026-03-13)
  - Binary: `${RAD_BIN}` (built from the RAD repo)
  - Whitelist generator: `${GEN_WL_BIN}`
  - Note: `generate_whitelist` was patched in this session to support bitlist-encoded
    whitelists (10x kit keys like `10x_3v3`). The fix wires `check_if_bitlist()` +
    `int64_seq::bits_to_sequence()` into the `read_whitelist()` function in
    `src/whitelist_generator.cpp`.
- **BLAZE**: v0.10.1 (pip package `blaze`, accessible as `${BLAZE_BIN}`)

## Input Data

ScTagger synthetic long-read simulations (Sharpington et al.). Paths relative to `${SCTAGGER_SIM}` (= `${RAW_FQ}/sctagger_sim/long-reads`):

| Dataset | FASTQ | True barcodes |
|---------|-------|---------------|
| S | `shuffled_S_lr_synth.fq.gz` | 50 |
| M | `shuffled_M_lr_synth.fq.gz` | 500 |
| L | `shuffled_L_lr_synth.fq.gz` | 5,000 |
| 100K | `100K_downsampled_L_lr_synth.fq.gz` | 5,000 |
| 250K | `250K_downsampled_L_lr_synth.fq.gz` | 5,000 |
| 500K | `500K_downsampled_L_lr_synth.fq.gz` | 5,000 |

Truth files: `${SCTAGGER_TRUTH}/{S,M,L}.truth.tsv.gz`

ScTagger read layout (from `rad list`, key: `sctagger`):
- Primer: `CTACACGACGCTCTTCCGATCT` (22bp)
- Barcode: 16bp, whitelist kit: `10x_3v3`
- UMI: 10bp
- Poly-A tail + read body

## RAD generate_whitelist Commands

All runs used `-e 0.3` (max edit distance ratio for adapter search) and `-w 10x_3v3`
(filter against the 10x 3' v3 global whitelist).

```bash
# Template command (substitute {TAG} and {FASTQ}):
"${GEN_WL_BIN}" \
  -i {FASTQ} \
  -o /tmp/test_wl_{TAG} \
  -p CTACACGACGCTCTTCCGATCT \
  -n 16 \
  -w 10x_3v3 \
  -e 0.3 \
  -t 4
```

Exact commands run (for each `{TAG} ∈ {S, M, L, 100K, 250K, 500K}` against `${SCTAGGER_SIM}/{shuffled,…}_lr_synth.fq.gz`):

```bash
for TAG in S M L 100K 250K 500K; do
  case "$TAG" in
    S|M|L) FQ="${SCTAGGER_SIM}/shuffled_${TAG}_lr_synth.fq.gz" ;;
    *)     FQ="${SCTAGGER_SIM}/${TAG}_downsampled_L_lr_synth.fq.gz" ;;
  esac
  "${GEN_WL_BIN}" -i "$FQ" -o "/tmp/test_wl_${TAG}" \
    -p CTACACGACGCTCTTCCGATCT -n 16 -w 10x_3v3 -e 0.3 -t 4
done
```

## BLAZE Commands

```bash
# Template (substitute {TAG} and {FASTQ}):
mkdir -p /tmp/blaze_test_{TAG}
"${BLAZE_BIN}" \
  --expect-cells 5000 \
  --10x-kit-version 3v3 \
  --threads 4 \
  --no-demultiplexing \
  --overwrite \
  --output-prefix /tmp/blaze_test_{TAG}/ \
  {FASTQ}
```

```bash
for TAG in S M L 100K 250K 500K; do
  case "$TAG" in
    S|M|L) FQ="${SCTAGGER_SIM}/shuffled_${TAG}_lr_synth.fq.gz" ;;
    *)     FQ="${SCTAGGER_SIM}/${TAG}_downsampled_L_lr_synth.fq.gz" ;;
  esac
  mkdir -p "/tmp/blaze_test_${TAG}"
  "${BLAZE_BIN}" --expect-cells 5000 --10x-kit-version 3v3 --threads 4 \
    --no-demultiplexing --overwrite \
    --output-prefix "/tmp/blaze_test_${TAG}/" "$FQ"
done
```

## Results: RAD generate_whitelist

| Dataset | Truth | Detected | TP | FP | FN | Precision | Sensitivity | F1 |
|---------|-------|----------|----|----|----|-----------|-------------|----|
| S | 50 | 50 | 50 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| M | 500 | 521 | 500 | 21 | 0 | 0.960 | 1.000 | 0.980 |
| L | 5,000 | 5,000 | 5,000 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| 100K | 5,000 | 5,400 | 4,126 | 1,274 | 874 | 0.764 | 0.825 | 0.793 |
| 250K | 5,000 | 4,748 | 4,634 | 114 | 366 | 0.976 | 0.927 | 0.951 |
| 500K | 5,000 | 4,840 | 4,834 | 6 | 166 | 0.999 | 0.967 | 0.983 |

## Results: BLAZE

| Dataset | Truth | Detected | TP | FP | FN | Precision | Sensitivity | F1 |
|---------|-------|----------|----|----|----|-----------|-------------|----|
| S | 50 | 79 | 50 | 29 | 0 | 0.633 | 1.000 | 0.775 |
| M | 500 | 628 | 500 | 128 | 0 | 0.796 | 1.000 | 0.886 |
| L | 5,000 | 5,737 | 5,000 | 673 | 0 | 0.883 | 1.000 | 0.938 |
| 100K | 5,000 | 6,244 | 4,567 | 1,677 | 433 | 0.731 | 0.913 | 0.812 |
| 250K | 5,000 | 9,156 | 4,981 | 4,175 | 19 | 0.544 | 0.996 | 0.703 |
| 500K | 5,000 | 5,662 | 4,999 | 663 | 1 | 0.883 | 1.000 | 0.938 |

Note: All BLAZE runs used `--expect-cells 5000 --no-demultiplexing --overwrite`.
BLAZE L whitelist count was 5,737 from the `--overwrite` run (an earlier non-overwrite
run on stale putative_bc.csv produced 6,905, demonstrating non-determinism when
putative barcode counting is interrupted mid-run).

## BLAZE L Summary Statistics (from summary.txt)

- Total reads: 4,993,805
- Reads with unambiguous polyT and adapter: 4,302,026 (86.15%)
- Failed (no polyT/adapter): 527,522 (10.56%)
- Failed (ambiguous strand): 103,448 (2.07%)
- Failed (multiple polyT/adapter): 60,809 (1.22%)

## Output Locations

- RAD whitelist outputs: `/tmp/test_wl_{S,M,L,100K,250K,500K}.{csv,txt}`
- BLAZE outputs: `/tmp/blaze_test_{S,M,L,100K,250K,500K}/`

## Notes

- The `-e 0.3` flag for `generate_whitelist` increases the edit distance tolerance for
  primer search (from default 0.1 to 0.3), pulling in more candidate sequences. This
  substantially improved results on the downsampled datasets where primer matching at
  `-e 0.1` was too stringent.
- The `-w 10x_3v3` flag filters extracted barcodes against the 10x 3' v3 global whitelist
  (6,794,880 barcodes) before threshold/knee calling. Without this flag, the model
  operated on raw 16-mers, producing large numbers of false positives (e.g., 789 FP on L
  at `-e 0.1`, 40,200 "barcodes" on 100K downsampled).
- 100K/250K/500K are downsampled subsets of the L dataset (5,000 true barcodes). At low
  read depths, per-barcode counts are sparse, making knee detection harder.
