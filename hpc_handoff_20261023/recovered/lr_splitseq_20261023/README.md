# Recovered LR-Split-seq comparison — 23 October 2026

**The final component-based Flexiplex/FLAMES read-count comparison and the 568-row cell-ID mapping are recovered.** The source was on the newly mounted `CMV_SSD_2` drive. This package supersedes the earlier F5-02 statement that the comparator outputs and row identities were unlocated.

Start with [the original labeled source table](tables/splitseq_published_barcode_read_counts.csv), [the Prism-row-to-cell mapping](prism/prism_row_to_cell.csv), and [the Prism validation report](prism/README.md). Every one of the 3,408 numeric entries in the saved six-column Prism table matches the labeled export in its original order. All 568 cell IDs are unique. The cell identities, samples, primer/well mapping and published short-read UMI annotations also match independent published metadata.

## Selected comparison

| Arm | Recovered execution | Selected per-cell source |
|---|---|---|
| RAD | RAD 1.0.2, commit `b6853a3d3d1818130ac364f7937bd0690ae9e385`; current ED2 run dated 2026-08-01 | [RAD checkpoint](checkpoints/rad_ed2/ed1_ed2_per_published_cell.tsv), filter `tool = ED2 current main` |
| Component Flexiplex with poly-T | FLAMES commit `bf2211a8da1e1c7327370ab12479ae70e1d37cd8`, embedded Flexiplex 1.02.6; three separately matched 8-nt barcode components, edit distance 1 per component, flank edit distance 3, required 8-T segment, four threads | [Component checkpoint](checkpoints/components/per_published_cell_counts.tsv), filter `tool = Flexiplex polyT` |

The component checkpoint lives in a folder called `component_no_polyt_t4`, but it contains both poly-T conditions and an earlier RAD control. The selected run is explicitly `component_polyt_paired_t4`; its saved command passes `include` to [the runner](source/component_runner/run_component_no_polyt.R). Use the executed settings above, rather than the different upstream paper-state example configuration. The no-poly-T, MATCHED_SPLIT and historical two-pass columns are retained only to verify the original six-column export.

The read-count table contains **distinct original reads within each physical cell**. A read assigned to two cells can contribute to each cell. Thus sums across cells are read–cell pairs: RAD **2,078,171**, component poly-T **1,156,252**. The corresponding distinct read totals across the 568 cells are **2,063,573** and **1,152,260**. Primer variants from the same reverse-transcription well are collapsed to the same physical-cell key before counting. The retained per-cell counts require a nonempty UMI, with no requirement that the UMI be exactly ten bases.

## Recovered statistics

Prism's saved analysis explicitly uses a **two-sided paired t test**: t = 14.959474687143327, df = 567, P = 6.890554214980993e-43. The statistic independently recomputes from the recovered rows. This is the P value rounded in the rebuttal; its attribution to Wilcoxon signed-rank is inconsistent with the execution record. The historical test provenance is resolved. A decision to change the final statistical method remains with the author.

## What is included

- Original keyed CSV/XLSX, the export builder, published cell map, per-cell read/UMI counts and control tables needed to verify all Prism columns.
- Selected run manifests, commands/timing logs, barcode layouts, complete 96-entry component catalogs, and the primer-to-well metadata.
- Native component statistics and normalized assignment ledger; [RAD assignment checkpoint restricted to the 568 published cells](checkpoints/rad_ed2/README.md); compact source snapshots and replay validators.
- Verbatim relevant Prism table/analysis components and their hashes. These extracts are evidence, not a standalone editable Prism project.
- Source-to-package transfer manifests and SHA-256 checksums. Original paths in archived scripts are preserved; rebase them explicitly on HPC.

See [portable replay commands](REPLAY.md). `validation/` contains executed validation reports. This recovery validates stored tables and assignment checkpoints; it does not claim a new raw-read demultiplexing run. The full RAD assignment ledger is also preserved under reviewer_comment_data, with its path/hash in `full_rad_checkpoint_copy.json`. The full demultiplexed FASTQs remain at the source locations listed in `external_assets.json`. They are unnecessary for replaying the preserved assignment-to-cell counts, but are relevant for a complete raw-output comparison.

## Remaining Figure 5 work

1. **Bind Figure 5H to the intended UMI analysis.** Current ED2 and component-poly-T per-cell UMI counts are recovered. The separate UMI-intersection candidate uses an earlier RAD ED1 run, and the master Prism file has no Split-seq UMI table. Do not relabel that earlier intersection as the current ED2 result. Rebuild intersections from the selected ledgers and depth-matched short-read checkpoint, or establish the intended historical source before updating the panel.
2. **Reconcile full-input percentages with counting units.** The retained full input has 5,764,421 reads. Current RAD assigns 2,498,488 distinct source reads (43.34%). Component poly-T has 1,338,285 distinct source reads (23.22%) and 1,345,255 assignment rows (23.34%). The displayed 23.35% requires a source/rounding check. Keep these separate from counts restricted to the 568 cells.
3. Preserve the paired-test execution record when correcting the historical test label; obtain the author's choice before substituting a different final test.
4. The original RAD ED2 aggregation producer was not located in the inspected SSD directories or local RAD project. Use the preserved normalized ledger and independent replay validation as the checkpoint; retain the recorded RAD command/layout/version for raw replay.

## HPC continuation

Resume F5-02 from these checkpoints. First run the packaged validators, then write portable paths and environment pins for the recovered execution. Keep the selected ED2/poly-T arms separate from the earlier controls. Return new table hashes and any changes in cells, counts, UMI rules, percentages or statistical output. See [the main task queue](../../regeneration_tasks.json) and [author decisions](../../AUTHOR_DECISIONS.md).
