# FLAMES configurations for Figures 5 and 6

[Pinned configuration release and checksum files](https://github.com/indianewok/rad-manuscript/releases/tag/flames-configs-2026-10-30)

| Analysis | Configuration |
|---|---|
| LR-Split-seq paper component layout | [config_splitseq.json](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_05/provenance/flames_paper_snapshot/upstream/ChangqingW_FLAMES_figures/files/config_splitseq.json) |
| LR-Split-seq paper complete-cell layout | [config_splitseq_bc.json](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_05/provenance/flames_paper_snapshot/upstream/ChangqingW_FLAMES_figures/files/config_splitseq_bc.json) |
| Figure 5 RAD joint barcode layout | [Archived layout](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/data/figure_05/splitseq_reverse_complemented_whitelist_layout.csv) |
| Figure 5 component ED2 with poly-T | [Executed wrapper](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_05/provenance/flames_paper_snapshot/executed/flexiplex_ed2_native/run_native_ed2.R) |
| Figure 6 native genome alignment | [Exact executed flames_genome_map.json](https://github.com/indianewok/rad-manuscript/blob/flames-configs-2026-10-30/source_data/figure_06/provenance/flames_alignment_snapshot/upstream/LongBench_workflow_37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d/sub_workflows/lr_sc_sn/config/flames_genome_map.json) |

Check the configuration files from the repository root.

```bash
python3 scripts/verify_pinned_flames_configs.py
```

[Source commits and attribution](../source_data/pinned_flames_configs/origins.json) · [File checksums](../source_data/pinned_flames_configs/files.tsv)
