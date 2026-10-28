# Figures 1, 2, and 4: reconstruction and validation results

This record summarizes the HPC reconstruction of source tables. File identities are recorded in [the output manifest](../manifests/figures_124_outputs.tsv); figure-specific methods and commands are in the [Figure 1](../docs/figure_01.md), [Figure 2](../docs/figure_02.md), and [Figure 4](../docs/figure_04.md) guides.

## Executed commands

```bash
python3 scripts/revision/figures_124.py build
python3 scripts/revision/figures_124_assignment_audit.py --fixtures-only
python3 scripts/revision/figures_124_assignment_audit.py
python3 scripts/revision/figures_124_native_recovery.py
python3 scripts/revision/figures_124_prism_audit.py
python3 scripts/revision/figures_124.py render
python3 scripts/revision/figures_124.py validate
python3 scripts/revision/figures_124_parameters.py
python3 scripts/revision/figures_124_hd_lineage.py
sbatch --parsable scripts/revision/figures_124_fastq_audit.sbatch
```

The full FASTQ audit completed as job 9976816 with exit status 0:0 on CPU-only `standard/s01`: one CPU, 4 GB requested memory, and a 30-minute limit. Elapsed time was 8 min 7 s and peak RSS was 495,924 KiB. The [scheduler record](figures_124_fastq_scheduler.tsv) accompanies the [complete-stream checks](figures_124_fastq_identity.json).

## Numerical comparisons

| Analysis | Result |
|---|---|
| Timing | Reconstructed 108 accepted phases and 54 paired runtime/memory observations from original logs and completion records. Metrics, command hashes, hardware, and input identities match the saved accepted table. |
| Synthetic FASTQ identity | Checked every S/L uniform-Q20 and native-2023 record, gzip CRC, unique identifier, truth count, compressed hash, ordered sequence hash, and quality hash. Historical model files match the recorded bytes and pathname-dependent seed contract. |
| Synthetic discovery | Rescored 144 callsets; exported TP/FP/FN identities; validated 50,000 paired read identifiers, 5,000 truth barcodes, quality means and sample standard deviations, histogram totals, and eleven matched shifts. |
| Synthetic assignment | Rescored 2,822,457 RAD, 2,145,119 Flexiplex, and 4,993,805 BLAZE records. All six-state totals and 52,076 selected-target category values match. Small checks cover each tool’s duplicate-handling rule. |
| Barcode discovery across inputs | Retained all 37 inputs and 111 tool observations; rescored the RAGE immune reference, all 30 Tilgner callset/reference pairs, and three ScMixology2 sources. The source master validator passed 703 checks. |
| Public barcode identifiers | Rescored all 87 public input/tool observations from 105 distinct identifier files. The 24 controlled Visium observations are available as aggregates. |
| Historical corrected Figure 2 Prism source | All 45,000 inspected selected-truth values and blanks match reconstructed arrays. Source hash and structural findings are recorded in the [Prism data checks](../source_data/figure_02/desktop_QA.md). |

The public-identifier comparison can be repeated with:

```bash
python3 scripts/revision/figures_124_steps/rescore_public_identifiers.py \
  --output external_data/temporary/figure4_identifier_rescore.tsv
```

[Public identifier lineage](figures_124_public_identifier_export.json) records the source hashes and normalization. One normalized Tilgner copy differs in raw-file bytes but reproduces the reference-set scores; the [path recovery report](figures_124_native_master_path_recovery.json) identifies it.

## Inputs for further reconstruction

The Figure 1 guide lists the Seurat counts and matrix-creation workflow required for the HD spatial comparison. Its recovered detection counts, grid, and tissue mask have passed the recorded checks. Figure 4’s original SeqKit invocation/version, four historical Visium RAD split callsets, and original statistical settings remain to be recovered. Their retained downstream values and identifiers are available.

The historical paired per-base quality replay file was absent from its recorded path. Current callsets, paired means, and histograms were validated; the later complete-read quality scans are documented separately in the [Nanopore2023](../source_data/figure_02/full_read_quality/README.md) and [Nanopore2018](../source_data/figure_02/full_read_quality_2018/README.md) guides.

The figure images now use saved Dropbox Prism layouts. Their project hashes, layout identifiers, and exported-image hashes are recorded in the [export manifest](../manifests/prism_exports.json).
