# ScMixology2 native barcode discovery

All three tools use the complete 25,164,948-read FASTQ with its original quality scores. The 25,955,360,585-byte FASTQ has SHA-256 `97c03138bd24d33ee63df5ea7a3aadef1b14b4a8271c87e232065363c88107ae`. [ScMixology2 input and reference](../../../source_data/figure_04/run_records/ScMixology2.json)

| Tool | Version | Source commit | Settings |
|---|---|---|---|
| BLAZE | 2.5.1 | `9845ec129624f2210c389e67506e29fab849a23d` | expected cells 500; minimum barcode-base Q15; edit distance 2; 16 threads |
| Flexiplex | 1.02.7 (release v1.02.7.1) | `c85543d820030ae970d6ed8d18d6f1ad9f631911` | 10x3v3; discovery flank distance 0; barcode edit distance 2; 16 threads |

Use Python 3.9.16 and the versions in [requirements.txt](requirements.txt). Install the [BLAZE release](https://pypi.org/project/blaze2/2.5.1/) and [Flexiplex release](https://github.com/DavidsonGroup/flexiplex/releases/tag/v1.02.7.1), including `flexiplex-filter` from the same commit. Put `blaze`, `flexiplex`, and `flexiplex-filter` on `PATH`. [BLAZE run record](../../../source_data/figure_04/producing_evidence/current_ScMixology2/BLAZE.json) · [Flexiplex run record](../../../source_data/figure_04/producing_evidence/current_ScMixology2/Flexiplex.json)

Run from the repository root with the complete FASTQ and 6,794,880-barcode 10x 3v3 catalog.

```bash
bash scripts/figure_04/scmixology2/run_blaze.sh
bash scripts/figure_04/scmixology2/run_flexiplex.sh
```

BLAZE writes `putative_bc.csv` and `whitelist.csv`. Flexiplex writes `ScMixology2_barcodes_counts.txt`, and its filter writes `selected_native.tsv`. Use the 248-barcode short-read reference to score the selected lists.

```bash
python3 scripts/figure_04/scmixology2/score_whitelist.py \
  --tool BLAZE \
  --selected results/figure_04/ScMixology2/BLAZE/whitelist.csv \
  --reference external_data/figure_04/references/ScMixology2.reference.txt.gz \
  --output results/figure_04/ScMixology2/BLAZE/metrics.tsv
python3 scripts/figure_04/scmixology2/score_whitelist.py \
  --tool Flexiplex \
  --selected results/figure_04/ScMixology2/Flexiplex/selected_native.tsv \
  --reference external_data/figure_04/references/ScMixology2.reference.txt.gz \
  --output results/figure_04/ScMixology2/Flexiplex/metrics.tsv
```

Compare the output with the [Figure 4 barcode scores](../../../source_data/figure_04/barcode_detection_metrics.tsv).
