# Preserved FLAMES configurations for Figures 5 and 6

The configurations and relevant source files are copied into this repository
and included in the [locked configuration release](https://github.com/indianewok/rad-manuscript/releases/tag/flames-configs-2026-10-30).
The links below identify that preserved release, independently of subsequent
updates or deletion of the upstream repositories.

| Analysis | Preserved configuration |
|---|---|
| LR-Split-seq paper component layout | [config_splitseq.json](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_05/provenance/flames_paper_snapshot/upstream/ChangqingW_FLAMES_figures/files/config_splitseq.json) |
| LR-Split-seq paper complete-cell layout | [config_splitseq_bc.json](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_05/provenance/flames_paper_snapshot/upstream/ChangqingW_FLAMES_figures/files/config_splitseq_bc.json) |
| Figure 5 component ED2 with poly-T | [Executed wrapper](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_05/provenance/flames_paper_snapshot/executed/flexiplex_ed2_native/run_native_ed2.R) |
| Component ED2 without poly-T control | [Executed wrapper](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_05/provenance/flames_paper_snapshot/executed/flexiplex_no_polyt_ed2_native/run_native_ed2.R) |
| Figure 6 native genome alignment | [Exact executed flames_genome_map.json](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_06/provenance/flames_alignment_snapshot/upstream/LongBench_workflow_37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/sub_workflows/lr_sc_sn/config/flames_genome_map.json) |

The original source commits, paths, authorship records and file hashes are
retained in the [origin manifest](../source_data/pinned_flames_configs/origins.json). Successful execution
records accompany the configurations. Package defaults are distinguished from
the explicit Figure 6 configuration.

Verify the preserved files from the repository root:

```bash
python3 scripts/verify_pinned_flames_configs.py
```

The [SHA-256 manifest](../source_data/pinned_flames_configs/files.tsv) checks the complete preserved file
set. The release also supplies a separate archive and checksum file. Citations
can identify the release tag, original upstream commit and exact filename.
Original licenses and attribution remain with the copied source.
