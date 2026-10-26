# Figures 1, 2 and 4 HPC execution record

Implementation is on shared branch `revision/hpc-handoff-20261023`; the parent integration commit supplies the Git revision. Exact implementation/source/output hashes accompany the run records and `manifests/figures_124_outputs.tsv`. Original project assets were read without modification.

## Commands executed

```
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

The full FASTQ audit is job 9976816, COMPLETED 0:0 on CPU-only standard/s01, one allocated CPU, 4G request, 30-minute limit, GPU GRES zero, lsonglab account/current lsonglab_gpu QoS. Observed elapsed time 8m07s and peak RSS 495,924K. The saved scheduler report and GNU-time log accompany the complete-stream result.

## Completed evidence

- F1-02: rebuilt 108 accepted measured phases and 54 paired total-time/process-memory observations. Every selected metric, command hash, hardware stratum and input identity matches the archived accepted table. Recovered original zero-byte COMPLETE markers from scratch and nonempty logs from preservation, without manufacturing any success record.
- F2-01: verified every S/L flatQ20 and native-2023 FASTQ record, gzip CRC, unique ID, truth count, compressed hash, header/sequence hash and quality hash. Literal historical model paths still exist with identical bytes; exact base/effective seeds are frozen. No generator change or replacement experiment.
- F2-02: rescored 144 actual discovery callsets from independently retained truth, exported TP/FP/FN identities, validated 50,000 paired IDs and 5,000 truth barcodes, recomputed all quality means/SDs, checked full histogram conservation and eleven matched shifts.
- F2-03: rescored every retained RAD (2,822,457), Flexiplex (2,145,119) and BLAZE (4,993,805) read-table record. All six-state totals and 52,076 selected-target category values match exactly. Tiny fixtures distinguish RAD exclusion of identical duplicate outputs from Flexiplex collapse of same-target duplicates.
- F2-05: documented pathname-dependent RNG and retained generator unchanged, as directed.
- F4: preserved all 37 paired inputs/111 tool rows, independently rescored RAGE immune reference, all 30 Tilgner callset/reference pairs and three ScMixology2 sources. The upstream 36-native-input validator passes 703 checks after explicit moved-path recovery. Saved SeqKit rows join to all 37 canonical identities.
- Six descriptive figure bundles are available as editable SVG, PDF and PNG: workflow schematic, timing, quality discovery, assignment, all-37 barcode detection and input characteristics. These are review renders without unsupported significance annotations.
- Figure 2 Prism numeric CSV/JSON bindings match 45,000 current selected-truth values and blank cells. The exact corrected source remains unchanged outside the repository; its mixed unrelated/superseded sheets are excluded from this selected-only release.

## Unresolved gates and discrepancies

- F1-03: The wide whitelist-detection table and retained rad_demux table differ in 165,898 shared bins because they describe different processing stages. All four wide totals exactly match the original valid-pair count tables (PBC44593 45,979,761). An identity comparison to the 67,872,744 demultiplexing total is inapplicable. All 175,561 grid IDs and 123,658 in-tissue IDs also exactly match saved raw/filtered SpaceRanger lists; required plotting-grid columns are reconstructed losslessly. Original named positions artifact, full detection-to-bin creation code and selected Seurat count object/provenance remain missing; no triptych is rendered.
- F2-04: native Prism inspection and a clean current native project remain unavailable on HPC; existing statistics and annotations were left unchanged. General structural verification flags duplicate layout object fenIDs 134 and 135 in **both** unchanged V18 and corrected copies. This predates our work; native Prism is required to determine its significance. Do not equate numeric validation with native acceptance.
- F4-02: exact original all-37 SeqKit invocation/version remains unresolved at inspected project logs. Saved values are preserved, not mislabeled as a new all-read summary run.
- F4-03: paired observation tables and descriptive proofs are complete; existing statistical analyses/annotations are preserved by author instruction. Original analysis settings remain a provenance gap, documented in `figures_124_decisions.md`. Technical inputs are not independent biological replicates.
- Four historical Visium split RAD callset paths under `/tmp` remain absent; their retained downstream metrics and checksum metadata are explicit. One normalized Tilgner copy differs from its original raw-file hash but passes independent reference rescore; it is not described as byte-identical.
- The historical paired per-base quality replay file is absent at its checked recorded path. Current callsets, paired mean qualities and histograms are validated; full quality-generator replay is not claimed.
- F1-01 has a pinned code-to-label crosswalk and editable scripted review alternative. Final original-artwork mapping and selection remain with the figure owner.

These runs establish source integrity, checkpoint resumption, independent accounting and scripted rendering. They do not establish new raw demultiplexer runs, native Prism statistics, or complete raw-source acquisition.

Portable identifier rescore: `python3 scripts/revision/figures_124_steps/rescore_public_identifiers.py --output /tmp/figure4_identifier_rescore.tsv` independently matches all 87 public input/tool rows from 105 distinct saved identifier files. The 24 controlled Visium rows remain explicitly aggregate-only. Original source hashes and normalization are in `figures_124_public_identifier_export.json`.
