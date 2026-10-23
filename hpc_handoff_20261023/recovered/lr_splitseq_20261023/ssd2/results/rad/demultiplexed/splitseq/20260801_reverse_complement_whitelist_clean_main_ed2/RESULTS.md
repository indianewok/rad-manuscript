# RAD SPLiT-seq reverse-complement-whitelist ED2 benchmark

Run date: 2026-08-01

This run used current clean `main` at commit
`b6853a3d3d1818130ac364f7937bd0690ae9e385`, the same input FASTQ,
reverse-complemented whitelist layout, four threads, strict joint mode, and
defensive correction settings used for the prior clean ED1 analysis. Both
`--generated-mutation` and `--whitelist-mutation` were set to 2.

## Headline metrics

| Metric | Prior clean ED1 | Current-main ED2 | ED2 minus ED1 | Relative change |
|---|---:|---:|---:|---:|
| Assigned source reads | 2,372,756 | 2,498,488 | +125,732 | +5.299% |
| Published-cell reads | 2,033,838 | 2,063,573 | +29,735 | +1.462% |
| Published cell-UMIs | 1,863,781 | 1,891,704 | +27,923 | +1.498% |
| Published cells | 568 | 568 | 0 | 0% |
| Median reads per published cell | 1,944.5 | 1,979.5 | +35.0 | +1.800% |
| Median UMIs per published cell | 1,829.0 | 1,866.0 | +37.0 | +2.023% |

## Read-level concordance

ED2 is a strict source-read and call superset of ED1:

- shared assigned reads: 2,372,756;
- ED2-only reads: 125,732;
- ED1-only reads: 0;
- shared reads retaining every ED1 physical-cell+UMI call:
  2,372,756/2,372,756;
- shared reads with an exactly unchanged full call set: 2,364,936;
- shared reads retaining all ED1 calls plus an additional ED2 call: 7,820;
- shared reads losing any ED1 call: 0.

Of the 125,732 ED2-only reads, 29,472 have at least one published-cell
assignment and 96,260 have only off-reference assignments. The published
count includes 141 reads that also have an off-reference assignment.

## Primer-specific published recovery

| Primer | ED1 reads | ED2 reads | Read gain | ED1 cell-UMIs | ED2 cell-UMIs | UMI gain |
|---|---:|---:|---:|---:|---:|---:|
| R | 953,969 | 968,118 | +14,149 | 880,762 | 894,026 | +13,264 |
| T | 1,087,190 | 1,103,108 | +15,918 | 991,571 | 1,006,502 | +14,931 |

On the raw-exact construct panel, ED2 preserves all 423,498 R reads and all
503,375 T reads at the exact physical cell and UMI, with zero wrong-cell or
uncalled reads.

## Combination-space tradeoff

| Metric | ED1 | ED2 |
|---|---:|---:|
| Observed physical combinations | 90,144 | 113,406 |
| Published combinations observed | 568 | 568 |
| Off-reference combinations observed | 89,576 | 112,838 |
| Published combinations with at least 100 UMIs | 557 | 558 |
| Off-reference combinations with at least 100 UMIs | 216 | 292 |
| Published combinations in top 568 | 549 | 549 |
| Off-reference combinations in top 568 | 19 | 19 |

Thus ED2 improves published-cell depth modestly without changing top-568
ranking composition, but it substantially expands the low-count off-reference
combination space. Off-reference cell-UMIs increase by 97,652, compared with
27,923 additional published-cell UMIs.

## Resources

- GNU-time wall time: 3:37.68
- RAD internal wall time: 217.67 seconds
- peak RSS: 266,144 KiB
- input reads: 5,764,421
- exit status: 0

## Provenance caveat

The prior ED1 result was generated before the current-main rebuild. Its source
commit is strongly inferred to be `61e81384431528301b3d8e3b3560f90faf39bec8`,
but its binary checksum was not retained. The adapter calibration values are
identical between runs, and every shared read retains every prior physical
cell+UMI call. ED2 adds a second call to 7,820 shared reads. Nevertheless, a
publication-grade single-variable timing claim should rerun ED1 with the
current binary.

For these text whitelists, whitelist mismatch pre-generation is disabled in
the current correction path. The effective correction change is therefore
the generated-mutation radius of 2; `--whitelist-mutation 2` was retained to
match the project's established ED2 invocation convention.
