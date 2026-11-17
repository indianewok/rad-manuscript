# RAD barcode discovery for Figure 4

Figure 4 uses RAD commit `4acbe004ba11b150d6832395452632f367a6e6c1` with
`scan-wl --max-error 0.3`. BLAZE and Flexiplex settings vary by input.
[Per-input tool settings](../../source_data/figure_04/tool_parameters.tsv) · [RAD commands](../../source_data/figure_04/producing_evidence/current_RAD/)

## Build RAD

Use Linux with GNU time at `/usr/bin/time` to record runtime and memory use.
The build requires CMake 3.18 or newer, a C++17 compiler, OpenMP, Zlib, Boost
filesystem and iostreams, and `pigz`. Use a fresh build directory.

```bash
git clone https://github.com/indianewok/rad.git external_data/software/rad
git -C external_data/software/rad checkout --detach 4acbe004ba11b150d6832395452632f367a6e6c1
python3 scripts/figure_04/build_rad.py \
  --rad-source external_data/software/rad \
  --build-dir external_data/software/rad_build_4acbe00 --threads 8
```

From the repository root, set `PATH` to select this RAD build and
`RAD_RESOURCES` to resolve catalog aliases such as `10x_3v3`.

```bash
export RAD_RESOURCES="$PWD/external_data/software/rad/resources"
export PATH="$PWD/external_data/software/rad_build_4acbe00:$PATH"
```

The runner checks the source commit and build record. Use `--rad-sha256` to
require a particular executable hash.

## Prepare one input

Use the [input record](../../source_data/figure_04/run_records/) to locate
the complete FASTQ, matched reference and chemistry catalog. Obtain access to
controlled spatial inputs through their data repository. Match the recorded
`input_format`. If the source is compressed and the record specifies plain
FASTQ, decompress it directly to retain the read order, headers, bases, and
quality strings.

```bash
gzip -dc official_input.fastq.gz > external_data/figure_04/inputs/DATASET.fastq
```

Pass that plain FASTQ to `--input`. For a tar archive, extract the exact member
listed in `input_acquisition.member`. For Le Brigand MOB, concatenate the gzip
files in the order listed in `input_acquisition.components`.

For a matched Cell Ranger barcode file, remove the terminal `-1` suffix and
retain one 16-base barcode per line. The input check accepts the recorded file
hash or the same sorted barcode set, so gzip metadata and row order can differ.

### SRA inputs

Use the full-quality archive listed in the input record. Keep the recorded
`.sra` basename because it contributes to the FASTQ headers. The benchmark used
SRA Toolkit 3.4.1 and, for P8 whole-transcriptome, pigz 2.4.
[Pinned SRA Toolkit distribution](https://ftp-trace.ncbi.nlm.nih.gov/sra/sdk/3.4.1/sratoolkit.3.4.1-alma_linux64.tar.gz)

| SRA Toolkit artifact | SHA-256 |
|---|---|
| `sratoolkit.3.4.1-alma_linux64.tar.gz` | `f4850a32975596ca0755d928b166ecb0095918284ea992fba10f1acb3fcff64d` |
| `fasterq-dump-orig.3.4.1` | `b3a4dcd4078c1867bc980fecde4333efadd435e5867d7a834cd3b0a40c419d9f` |

Run the command for the selected input in the directory containing its archive.

```bash
set -o pipefail
mkdir -p tmp fasterq_tmp

# Measles P7
fasterq-dump-orig.3.4.1 SRR28349077.sra --split-spot --include-technical --min-read-len 0 \
  --threads 16 --mem 256M --temp tmp --outfile Measles-P7.local3.4.1.fastq.partial

# Measles P8 V(D)J-enriched
fasterq-dump-orig.3.4.1 SRR28349076.sra --split-spot --include-technical --min-read-len 0 \
  --threads 16 --mem 256M --temp tmp --outfile Measles-P8-VDJ-enriched.local3.4.1.fastq.partial

# Measles P8 whole-transcriptome
fasterq-dump-orig.3.4.1 SRR28349078.sra --split-spot --include-technical --min-read-len 0 \
  --stdout --threads 16 --mem 256M --temp fasterq_tmp | pigz -n -c -p 8 > Measles-P8-WTA.fastq.gz

# Isosceles ovarian
fasterq-dump-orig.3.4.1 SRR26865982.sra --split-spot --include-technical --min-read-len 0 \
  --threads 16 --mem 256M --temp tmp --outfile Isosceles-ovarian-GSE248115.local3.4.1.fastq.partial
```

Move each completed output to its FASTQ input path and check it against the
record's read count, base count and digests. Where present,
`sequence_quality_sha256` hashes the sequence and quality lines with LF endings
in read order, with FASTQ headers omitted.

## Run discovery and scoring

Run from the repository root. Use the thread count in the RAD execution
record and a new output directory.

```bash
python3 scripts/figure_04/run_scan.py \
  --dataset-record source_data/figure_04/run_records/DATASET.json \
  --input external_data/figure_04/inputs/DATASET.fastq.gz \
  --rad external_data/software/rad_build_4acbe00/rad \
  --rad-source external_data/software/rad \
  --rad-build-receipt external_data/software/rad_build_4acbe00/build_receipt.json \
  --catalogue external_data/figure_04/catalogues/CATALOGUE \
  --threads 16 \
  --output-dir results/figure_04/DATASET
```

The runner checks input, reference, and catalog identities before discovery.
`command.json` records the executed command. `score/metrics.json` includes the
hash of the sorted selected barcode set.

## Read the outputs

`score/metrics.csv` gives barcode counts, TP, FP, FN, precision, recall, and F1.
`score/barcode_membership.csv` gives each barcode’s call and reference status.
The output distinguishes empty sequence records from the nonempty sequences
processed by RAD. [Scoring definitions](../../docs/figure_04.md#barcode-scoring-and-panel-tables)
