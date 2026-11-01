# FLAMES configurations for Figures 5 and 6

The [configuration release](https://github.com/indianewok/rad-manuscript/releases/tag/flames-configs-2026-10-30) contains the FLAMES configurations, producing wrappers and supporting source used for Figures 5 and 6. The links below identify the fixed release versions.

| Analysis | Configuration |
|---|---|
| LR-Split-seq paper component layout | [config_splitseq.json](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_05/provenance/flames_paper_snapshot/upstream/ChangqingW_FLAMES_figures/files/config_splitseq.json) |
| LR-Split-seq paper complete-cell layout | [config_splitseq_bc.json](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_05/provenance/flames_paper_snapshot/upstream/ChangqingW_FLAMES_figures/files/config_splitseq_bc.json) |
| Figure 5 component ED2 with poly-T | [Executed wrapper](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_05/provenance/flames_paper_snapshot/executed/flexiplex_ed2_native/run_native_ed2.R) |
| Figure 6 native genome alignment | [Exact executed flames_genome_map.json](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_06/provenance/flames_alignment_snapshot/upstream/LongBench_workflow_37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/sub_workflows/lr_sc_sn/config/flames_genome_map.json) |

Source commits, file paths, authors and hashes are in the [origin manifest](../source_data/pinned_flames_configs/origins.json). Execution
records accompany the configurations. The Figure 6 run uses the explicitly
supplied genome-alignment JSON.

Check the configuration files from the repository root:

```bash
python3 scripts/verify_pinned_flames_configs.py
```

The [SHA-256 manifest](../source_data/pinned_flames_configs/files.tsv) lists the complete file set. The release also supplies a separate archive and checksum file. Citations
can identify the release tag, original upstream commit and exact filename.
Original licenses and attribution remain with the copied source.
