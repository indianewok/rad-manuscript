# Flexiplex f0 discovery for P7, P8 and Isosceles

These runs use Flexiplex 1.02.6 with flank edit distance `-f 0`, barcode edit distance `-e 2`, and 16 threads. Filter 1.02 uses the complete 6,794,880-barcode 10x 3v3 catalog.

| Input | Command | Execution record and count-table preview |
|---|---|---|
| P7 | [run_Measles-P7.sh](run_Measles-P7.sh) | [Record](../../../source_data/figure_04/producing_evidence/current_Flexiplex_f0/Measles-P7.json), [counts](../../../source_data/figure_04/producing_evidence/current_Flexiplex_f0/Measles-P7.counts_preview.tsv) |
| P8-enriched | [run_Measles-P8-VDJ-enriched.sh](run_Measles-P8-VDJ-enriched.sh) | [Record](../../../source_data/figure_04/producing_evidence/current_Flexiplex_f0/Measles-P8-VDJ-enriched.json), [counts](../../../source_data/figure_04/producing_evidence/current_Flexiplex_f0/Measles-P8-VDJ-enriched.counts_preview.tsv) |
| P8 | [run_Measles-P8-WTA.sh](run_Measles-P8-WTA.sh) | [Record](../../../source_data/figure_04/producing_evidence/current_Flexiplex_f0/Measles-P8-WTA.json), [counts](../../../source_data/figure_04/producing_evidence/current_Flexiplex_f0/Measles-P8-WTA.counts_preview.tsv) |
| Isosceles ovarian | [run_Isosceles-ovarian-GSE248115.sh](run_Isosceles-ovarian-GSE248115.sh) | [Record](../../../source_data/figure_04/producing_evidence/current_Flexiplex_f0/Isosceles-ovarian-GSE248115.json), [counts](../../../source_data/figure_04/producing_evidence/current_Flexiplex_f0/Isosceles-ovarian-GSE248115.counts_preview.tsv) |

Run from the repository root with the complete input in the run record. Install the executable and filter from the [Flexiplex v1.02.6 release](https://github.com/DavidsonGroup/flexiplex/releases/tag/v1.02.6).

```bash
mkdir -p external_data/software
curl --fail -L https://github.com/DavidsonGroup/flexiplex/releases/download/v1.02.6/flexiplex-v1.02.6.tar.gz \
  -o external_data/software/flexiplex-v1.02.6.tar.gz
printf '21940bf4aaab28819728d22ebae3fafc3ecc8596948b7007d1f30fca64b5d16c  external_data/software/flexiplex-v1.02.6.tar.gz\n' | sha256sum -c -
tar -xzf external_data/software/flexiplex-v1.02.6.tar.gz -C external_data/software
ln -sfn flexiplex-linux external_data/software/flexiplex/bin/flexiplex
export PATH="$PWD/external_data/software/flexiplex/bin:$PATH"
```

Install the [Python 3.9.16 dependencies](requirements.txt) with `python3 -m pip install -r scripts/figure_04/flexiplex_f0/requirements.txt`. The scripts stream the original reads and qualities, then filter the barcode-count table. P8 uses [rapidgzip 0.16.0](https://github.com/mxmlnkn/rapidgzip) to decompress its FASTQ. [SRA converter settings](../README.md#sra-inputs)

```bash
flexiplex -d 10x3v3 -f 0 -e 2 -p 16 -n OUTPUT_PREFIX

python3 external_data/software/flexiplex/scripts/flexiplex_filter/main.py \
  --whitelist external_data/figure_04/catalogues/3M-february-2018-3v3.txt \
  --outfile selected_native.tsv OUTPUT_PREFIX_barcodes_counts.txt
```

The count table gives extracted-read counts by barcode. `selected_native.tsv` gives selected barcodes and their counts. The five-row previews show selected-list and reference membership. Score the selected barcodes against the matched short-read list.

```bash
python3 scripts/figure_04/flexiplex_f0/score_whitelist.py \
  --tool Flexiplex --selected selected_native.tsv \
  --reference MATCHED_REFERENCE.txt.gz --output metrics.tsv
```

Use these checksums to identify the release, filter, and chemistry catalog.

| Artifact | SHA-256 |
|---|---|
| Official v1.02.6 release archive | `21940bf4aaab28819728d22ebae3fafc3ecc8596948b7007d1f30fca64b5d16c` |
| Flexiplex 1.02.6 release binary | `6eee3a7113044d45e106dc74a541b9a53475311449bf49bd91cc912ba911c40e` |
| Filter 1.02 source | `672ab65cc2fe6fe9f48319a632d72e73c75a1d699b04d6b0f4ec887f5e6bfca0` |
| Full 10x 3v3 catalogue | `843a6f7038db8cb3c06f3dc21cc69d04139ffa10689780518d7a9e42dc2e819b` |
