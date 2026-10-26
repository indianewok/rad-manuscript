# Reproducibility checks

The checks below compare source records, intermediate counts and calculated
metrics with the retained analysis outputs. Detailed reports, input hashes and
commands are linked from each figure guide.

| Figure | Completed checks | Additional inputs needed for a full reconstruction |
|---|---|---|
| [1](figure_01.md) | Parsed 108 timing phases into 54 paired repetitions; verified the Visium HD count stages, 419 × 419 grid and 123,658-bin tissue mask | Selected Seurat `nCount_Spatial` values and the barcode-to-bin generation workflow |
| [2](figure_02.md) | Rescored 144 discovery lists; checked complete FASTQ sequences, IDs and qualities; recounted assignments and 52,076 per-target values | Raw synthetic-generation and tool executions are specified in the figure guide |
| [3](figure_03.md) | Recounted ScTagger and LongBench physical reads; ran all nine RAGE-seq arms on 20,346,396 reads; checked assignment sidecars, correction aggregates and edge cases; passed 414 build checks | Full correction-pair records for recovering overlap between category flags |
| [4](figure_04.md) | Verified 37 inputs and 111 tool observations; reproduced all 87 comparisons for 29 public inputs from deposited barcode lists; checked the input-characteristic joins | Some producing-run records, the original all-input SeqKit execution and four Visium splitRAD temporary callsets |
| [5](figure_05.md) | Checked receptor-count definitions; reproduced all 568 LR-Split-seq cell identities and 2,272 read/UMI counts; independently verified the saved paired t test | Exact receptor producer-to-panel mapping and the Figure 5H depth-matched short-read checkpoint and selection |
| [6](figure_06.md) | Verified donor and CellSNP contents, 12,012 reference identities, BAM/BAI hashes, index/header consistency and fixed-coordinate comparisons | Raw alignment, CellSNP and Vireo reruns use the inputs and commands in the figure guide |
| [7](figure_07.md) | Checked 57,885,606 RAD assignment rows and the count matrices; matched all 24,405 effects and P values; recalculated common-gene BH values and all 594 threshold combinations | Emitted FASTQ and read-to-gene files, segment/orientation identifiers and the selected panel C fit |

The [task registry](../manifests/task_status.tsv) records the corresponding
analysis steps and their dependencies. Controlled-access Figure 4 inputs retain
24 aggregate metric rows; the public barcode-list comparisons can be rerun from
files in this repository.

## Source-table rendering

The [clean-render report](../validation/clean_render.json) records calculations
and plots produced in a separate output directory with the pinned
[Python 3.11 environment](../environments/render-python311.lock.txt). File-access
tracing verifies that the scripts read the declared repository inputs. To repeat
those checks:

```bash
python3 scripts/check_render_isolation.py \
  --python /path/to/render-environment/bin/python --groups 124 3 5 567
```

The report records the script versions, input hashes and generated files for
each group. Figure images exported from the original Prism projects are shown
in the figure guides.

## Data and numerical checks

The [numerical-claim registry](../manifests/results_claims.tsv) links reported
values to their units, denominators, selection rules and source hashes. The file
inventory records the schema and identity of each source table. Rebuild both
with:

```bash
python3 scripts/check_manuscript_claims.py
python3 scripts/check_data_inventory.py
```

The [Flexiplex build check](../validation/software/flexiplex_audit_build.json)
compares upstream and diagnostic builds with the pinned binary on a four-read
fixture. It verifies the pre-correction barcode output used by the assignment
audits.
