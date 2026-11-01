# ScMixology2 native barcode discovery

All three tools use the complete 25,164,948-read FASTQ with its original quality scores. Its SHA-256 is `97c03138bd24d33ee63df5ea7a3aadef1b14b4a8271c87e232065363c88107ae` (25,955,360,585 bytes). The [input record](../../../source_data/figure_04/run_records/ScMixology2.json) identifies the source data and the matched 248-barcode scoring reference.

| Tool | Version | Source commit | Settings |
|---|---|---|---|
| BLAZE | 2.5.1 | `9845ec129624f2210c389e67506e29fab849a23d` | expected cells 500; minimum barcode-base Q15; edit distance 2; 16 threads |
| Flexiplex | 1.02.7 (release v1.02.7.1) | `c85543d820030ae970d6ed8d18d6f1ad9f631911` | 10x3v3; discovery flank distance 0; barcode edit distance 2; 16 threads |

The [BLAZE](../../../source_data/figure_04/producing_evidence/current_ScMixology2/BLAZE.json) and [Flexiplex](../../../source_data/figure_04/producing_evidence/current_ScMixology2/Flexiplex.json) execution records include software hashes, full commands, input identities and output metrics. The software environment used Python 3.9.16 and the package versions in [requirements.txt](requirements.txt). Install the pinned [BLAZE release](https://pypi.org/project/blaze2/2.5.1/) and [Flexiplex release](https://github.com/DavidsonGroup/flexiplex/releases/tag/v1.02.7.1), and expose the executables as `blaze`, `flexiplex` and `flexiplex-filter` on `PATH`. The Flexiplex filter comes from the same source commit as its release.

Run these from the repository root after acquiring the external input and full 10x3v3 chemistry catalogue:

```bash
bash scripts/figure_04/scmixology2/run_blaze.sh
bash scripts/figure_04/scmixology2/run_flexiplex.sh
```

Each script contains its native command. BLAZE writes `putative_bc.csv` and `whitelist.csv`. Flexiplex writes `ScMixology2_barcodes_counts.txt`; its filter writes `selected_native.tsv`. The chemistry catalogue contains all 6,794,880 allowed barcode sequences. The 248-barcode short-read reference is used only to score the selected lists.

Recalculate the barcode-set metrics from the selected lists:

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

For a selected barcode set C and the reference R, TP is |C∩R|, FP is |C−R| and FN is |R−C|. The [metrics table](../../../source_data/figure_04/barcode_detection_metrics.tsv) reports those counts and precision, recall and F1. The execution records identify the complete selected lists.
