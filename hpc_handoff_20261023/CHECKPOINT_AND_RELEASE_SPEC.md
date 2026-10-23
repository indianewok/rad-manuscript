# Checkpoints, validation and release contract

This is the target specification for the HPC work. The file names and commands proposed here are deliverables to implement, not claims that the current repository already provides them. Existing executable script paths are listed in the per-figure components.

## Three independent levels of reproducibility

1. **Render:** recreate a panel from deposited, small, validated plot-input tables. Requires no original FASTQ, demultiplexer or uncontrolled R session.
2. **Resume:** rebuild plot inputs from a retained checkpoint such as barcode assignments, a BAM/CellSNP bundle, a count matrix or an annotated receptor table. Requires the declared stage dependencies but not all upstream computation.
3. **Raw rerun:** regenerate the selected workflow from its source reads/reference files and pinned software. This establishes upstream provenance and scientific parity. It is needed where a checkpoint is missing or unreliable; it should not be required merely to revise a legend.

Track these levels separately for every panel. A successful render is not a successful raw rerun. A replacement analysis with a different generator, input or tool version is a new run, not an exact historical replay.

## Required manifest and stage records

Use a project-local configuration that maps original roots to HPC roots. Normally, preserve original absolute paths as provenance and map them through configuration. Historical ScTagger replay is an explicit exception: the literal model pathname contributes to the quality RNG seed, so preserve that exact string/contract or declare a separately versioned generator; do not normalize or relocate it silently. Each input receives a stable `asset_id`. At minimum record:

- `asset_id`, dataset/sample/library identity, species, assay, platform, chemistry and public accession/URL;
- original path, HPC path, immutable release-relative path where public;
- file role, format, byte size, cryptographic hash, compression and whether the digest covers compressed bytes or decoded content;
- read/cell/gene counts appropriate to the asset, with the count definition;
- native versus reconstructed input, reconstruction source/recipe and reference truth source;
- access status: public, controlled, author-owned/unreleased, or derived with release eligibility requiring review;
- validation status and evidence path. Use `present_metadata_only`, `verified_content`, `missing_at_checked_path`, `external_restore_required`, `public_download_available`, or `decision_pending` explicitly.

Each stage record must contain `run_id`, parent run/checkpoint IDs and hashes, figure/panels, command and argument vector, code revision and local patch hash, binary/container digest, reference/catalog/model hashes, thread/resource settings, effective random seeds, working directory, start/end time, exit status, stdout/stderr, outputs and validators. A job that exits successfully with absent outputs has failed the stage. Save scheduler job ID and measured runtime/RSS separately from scientific results.

Checkpoint reuse requires matching input hashes, code/configuration fingerprints and validator success. Changing one dependency invalidates only its descendants. A manifest should show whether a checkpoint was copied, recomputed, or newly reconstructed. Write outputs to a temporary stage directory and promote only after successful validation.

## Checkpoints to retain

| Checkpoint | Required contents | Validation and resume purpose |
|---|---|---|
| C0 — sources and references | Sample registry; accessions and file IDs; read source/transform manifests; catalog and filtered barcode lists; primer/layout/reference annotations; environment lock and binary provenance | Stable identities and hashes; unambiguous native/reconstructed status; source download or authorized restore instructions. Starts raw rerun. |
| C1 — exact analysis inputs | Subsample/shuffle order or reproducible mapping; synthetic truth IDs and base sequence hashes; model files, effective seeds and quality summaries; target whitelist for every replicate | Input counts; ID uniqueness; sequence/error invariance across synthetic quality shifts; target-list exclusions and, for supplied-list/off-list challenges, identical target list across tools within each replicate. For Figure 2 native discovery/assignment, preserve each tool's actual selected-list contract instead; those lists are deliberately not identical. Starts tool rerun. |
| C2 — extraction and assignments | Tool-selected whitelist; raw extracted barcode and corrected barcode; original read and emitted segment IDs; UMI where used; orientation; extraction/demux logs; rejected/unassigned reason fields | Ground truth cannot be injected into the Flexiplex diagnostic extraction. Save patch/source. Validate parser identity and orientation, duplicate policy, assignment totals and excluded records. Starts count/metric rebuild. |
| C3 — alignments and annotations | Genome/transcript/reference hashes; BAM/BAI where useful; per-read gene assignment and rejection reason; receptor annotation/read-cell links; bulk donor VCF and per-tool CellSNP matrices with barcodes/sites | BAM/index consistency; CB/UB tagging; exact contig/variant/barcode order; retain original-read-to-segment relation; no silent coordinate or reference conversion. Starts gene/genotype/annotation rebuild. |
| C4 — analytical matrices and labels | Sparse matrix with features/barcodes; count-unit declaration; cell labels; Vireo posterior/assignment output; fixed UMAP coordinates with input and normalization recipe | Shape and key consistency; positive-depth eligibility; doublet/unassigned/missing-row distinction; exact molecule/segment handling. Starts DE and cell summaries. |
| C5 — metrics and statistical inputs | Eligible/tested gene universes; all DE statistics; thresholds and counts; per-input/per-target metrics; statistical observation table including replicate/pair/block IDs | Recompute reported metrics from numerator/denominator; enforce paired design where chosen; distinguish missing from zero; BH family and direction explicit. Starts statistics or plot rebuild. |
| C6 — final panel inputs | One long-format table per panel, with axis values, group/tool/condition, observation keys, uncertainty and provenance; set-membership/Venn tables; pixel/bin coordinates and color limits where relevant | Every plotted value is traceable to a C5/C4 record. Export values before graphical transformation and document transformations. Starts lightweight rendering. |
| C7 — publication artifacts | Editable Prism where used; script-based renderer; PDF/SVG plus PNG proof; captions and statistical output; panel-to-source index; validation report | Check tables, plot values, labels, units, panel identities and source data together. Native Prism recalculation/rendering remains required where Prism owns the analysis. |

Use TSV/CSV for small tables, gzipped TSV or Parquet with an explicit schema for large read-level tables, MEX or another documented sparse format for matrices, VCF/BAM with indices for genomic data, and JSON/YAML for manifests. Save RDS/RData as optional convenience bundles with object indexes and R/session package information. Do not make a whole global R environment the only authoritative checkpoint.

## Counting-unit contracts that must remain separate

- **Figure 2:** retain the complete physical-read truth universe. Export the mutually exclusive final assignment categories and a separate emitted-record table if needed. Retain all six states for total-input accounting. Set the denominator per metric: correction pies use corrected-correct plus corrected-incorrect, not all input reads; unassigned reads remain visible in total-input accounting. Report how multiple/conflicting emitted assignments are resolved. The canonical historical partition must be checked against the preserved native analysis, not inferred from output FASTQ record counts alone.
- **Figure 3 off-list:** ScTagger and LongBench have strict physical-read counting: exclude an entire physical ID if it has more than one assignment row, including duplicates to the same target. Historical RAGE per-barcode tables use assignment records, while saved headline/log totals have additional unresolved differences. Reconcile these deliberately before any combined interpretation. Label legacy units in both tables and legends until a replacement run is adopted.
- **Figure 3 correction:** count unique `(original_read_id, target_barcode)` pairs. Collapse repeated copies of the same pair. A read with two distinct targets can count in both. Per-target percentages use all unique assignments to that target as denominator. Export source membership and changed-barcode predicates so each class can be recomputed. Classification is within each class: different source-bearing records may give the same pair multiple class flags. Preserve source sets and export overlaps; never sum the classes as a disjoint partition or as the Figure 3G denominator. A zero total-assignment denominator gives null, and a missing raw source is not a noncatalog observation.
- **Figure 4:** 37 named inputs, including one reconstructed ScMixology2 input. The same biological material represented by multiple technical libraries is not 37 independent biological replicates. Preserve pairing between tools at the input level.
- **Figure 6:** distinguish selected whitelist membership, positive read/count depth, available Vireo result, confident genotype, doublet and unassigned state. Preserve the fixed short-read reference universe and the denominator for each recall/concordance statistic.
- **Figure 7:** preserve the updated RAD emitted concatemer segments, inherited original-read gene assignment, exact cell–gene–UMI deduplication and missing-UMI rule. Do not replace these with universal physical-read deduplication or per-segment realignment during historical replay.

## Statistical decision record

Before running final hypothesis tests, create a record with panel, response variable, observation unit, paired/block identity, independent replication level, included sample IDs, test, sidedness, covariates, multiple-comparison family and correction, missing-value treatment, and effect/uncertainty definitions. Link author approval or a recorded decision. A legend that names a test is not evidence that that test was executed.

Known unresolved items are listed in `AUTHOR_DECISIONS.md`. The agent can compute descriptive summaries and prepare alternative test designs while waiting. It must not silently choose a new test or turn barcode rows/technical reads into independent replicates to match a desired P value. Export the complete test result table and executed command/session information.

## Validation deliverables

For each stage, emit machine-readable results (`check_id`, expected, observed, tolerance, status, evidence) and a readable short report. Fail on schema/identity/conservation errors. When integer counts should match historical output, require exact equality and list differences. When floating-point values can vary across libraries, declare a scientific tolerance and reason before judging the comparison. For seeded UMAP or parallel numerical work, compare coordinate/neighbor relationships and the selected fixed coordinates under the pinned environment; explain any differing embedding instead of replacing it silently.

Minimum release tests:

1. Rebuild completed panels from deposited C6 tables in a clean environment. No access to an author's home directory or raw data is allowed for this test.
2. Rebuild each C6 table from the highest valid retained upstream checkpoint, with an identity/count/metric comparison to the selected canonical table.
3. Demonstrate the raw-to-checkpoint path for every finalized workflow, or clearly document the missing external asset and acquisition step. For long and costly runs, report `not run`, `pilot only`, or `full passed` honestly; do not infer full success from a sample.
4. Prove resume/invalidation with a small deliberate input/configuration change and a restored baseline. The deliberate change is a workflow test, not a new scientific result.
5. Audit every manuscript/rebuttal number and final panel against `results_claims.tsv`, with figure, table row/key, unit, denominator, test and value. Methods must describe the selected executed pipeline.
6. Compare editable Prism values against canonical tables, recalculate analyses and export graphs in Prism when available. A valid ZIP structure or successful XML edit does not establish correct rendering or statistical execution. If Prism is unavailable on HPC, export canonical tables, a scripted scientific render, the editable Prism copy and a precise desktop QA checklist. Route native reopen/recalculation/export to the author or an agent on a Prism-capable computer; record that gate as pending without blocking independent HPC analysis.

## Proposed revised release layout

```
README.md
CITATION.cff
config/project.example.yaml
manifests/datasets.tsv
manifests/assets.tsv
manifests/panels.tsv
manifests/runs.jsonl
manifests/statistical_decisions.tsv
environments/                     # explicit dependency locks/container recipes
workflows/                        # one tested stage graph, scheduler integration
scripts/                          # versioned analysis, parsing and validators
checkpoints/figure_01/ ... figure_07/
source_data/figure_01/ ... figure_07/
figures/figure_01/ ... figure_07/   # editable and final exports
validation/
methods/provenance_by_paragraph.tsv
results_claims.tsv
SHA256SUMS
```

Use GitHub for code, configuration, schemas, small fixtures, documentation and provenance. Use the updated archival dataset for permitted larger checkpoints, source data, editable figure files and immutable validation reports, with exact filenames/checksums. Keep legacy files/figure numbers clearly mapped to the historical release. For controlled Engblom reads, distribute accession/DAC and authorized acquisition instructions rather than raw read copies; review which derived artifacts may be redistributed under the data agreement. Inspect content, not merely filename, before assigning public release eligibility.

Prepare a release inventory with old artifact → current counterpart → retained/replaced/retired → reason. Prepare Zenodo title, description, version, creators, license, related identifiers and resolved DOI metadata; update the repository, Data Availability and rebuttal links from that same registry. Stage the upload-ready directory and checksum list. Leave actual publishing and visibility changes for the author's release decision.
