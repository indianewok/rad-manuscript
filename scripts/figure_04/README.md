# RAD barcode discovery for Figure 4

All Figure 4 RAD results use source commit
`4acbe004ba11b150d6832395452632f367a6e6c1` and an explicit maximum adapter
error ratio of 0.3. The [per-input tool table](../../source_data/figure_04/tool_parameters.tsv)
shows each tool's version and command flags for the 37 inputs. The [RAD execution records](../../source_data/figure_04/producing_evidence/current_RAD/) identify the executable and inputs. BLAZE and Flexiplex settings vary by input; read their row
before repeating a comparison.

## Build RAD

Use Linux with GNU time at `/usr/bin/time`, which records the native runtime
and memory use. Build the exact source commit with CMake 3.18 or newer, a C++17
compiler, OpenMP, Zlib, Boost filesystem/iostreams, and `pigz` available. The small build helper
uses a fresh build directory, rejects tracked source changes and records the
compiler configuration, commands, logs and actual executable hash:

```bash
git clone https://github.com/indianewok/rad.git external_data/software/rad
git -C external_data/software/rad checkout --detach 4acbe004ba11b150d6832395452632f367a6e6c1
python3 scripts/figure_04/build_rad.py \
  --rad-source external_data/software/rad \
  --build-dir external_data/software/rad_build_4acbe00 --threads 8
```

From the manuscript repository root, set these variables before copying a
recorded native command. `PATH` selects the pinned build; `RAD_RESOURCES`
lets catalogue aliases such as `10x_3v3` find its matching source resources:

```bash
export RAD_RESOURCES="$PWD/external_data/software/rad/resources"
export PATH="$PWD/external_data/software/rad_build_4acbe00:$PATH"
```

An executable hash can differ across compilers. The runner verifies the exact
source commit and the build receipt, and records your actual executable hash.
It can also enforce an optional `--rad-sha256` pin. The source-commit check selects the 4acbe00 implementation.

## Prepare one input

Choose one JSON record from `source_data/figure_04/run_records/` and obtain its complete FASTQ, matched reference and pinned chemistry catalog. The record specifies its source accession and reference definition.

Read the record's `input_format` before preparing the FASTQ. `fastq.gz` pins the
compressed bytes; `fastq` pins the plain FASTQ bytes. When the record requires
plain FASTQ and the official source is a gzip file, decompress without changing
read order, headers, bases or quality strings:

```bash
gzip -dc official_input.fastq.gz > external_data/figure_04/inputs/DATASET.fastq
```

Pass that plain FASTQ to `--input`. For a tar archive, extract the exact member
listed in `input_acquisition.member`. For Le Brigand MOB, concatenate the gzip
files in the order listed in `input_acquisition.components`.

For a matched official CellRanger barcode file, remove only a terminal `-1`
suffix and retain one 16-base barcode per line; a different gzip timestamp or
compression level is allowed when the canonical matched-set hash agrees.
The run record provides the reference definition and dataset accession.

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

Run from the manuscript repository root with a new output directory:

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

Use the thread count recorded for that input. The runner verifies the catalogue,
reference and input hashes. It writes the executed command, selected list and barcode-set scores. Obtain reference and complete barcode-list inputs from the registered data
source and place them at the locations in each run record. Controlled spatial
data use the registered access process. Use the matched reference definition and source accessions in the record. A reference is accepted when its file SHA256 matches, or when its canonical barcode-set SHA256 matches; the runner records the actual file hash used. Execution records also provide `selected_barcode_sha256`, the hash of the sorted selected barcode set; `score/metrics.json` records the same output-set hash for your run. Equivalent gzip compression or row ordering does not change the canonical reference identity.

## Read the outputs

`score/metrics.csv` contains barcode counts, TP, FP, FN, precision, recall and F1.
`score/barcode_membership.csv` lets you inspect individual calls and reference
membership. TP is the call/reference intersection, FP is calls outside the
reference, and FN is reference members not called. These metrics measure agreement with the matched reference barcode set.

The runner uses the complete input and preserves its sequences and qualities.
It checks the input identity or records the complete input digest before scanning. Empty sequence records are reported separately from the
native processed nonempty-sequence count. Each invocation processes one dataset.
