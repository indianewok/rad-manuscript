# Reproduce one Figure4 RAD result

All Figure4 RAD results use source commit
`4acbe004ba11b150d6832395452632f367a6e6c1` and an explicit maximum adapter
error ratio of0.3. The [per-input tool table](../../source_data/figure_04/tool_parameters.tsv)
shows the RAD, BLAZE and Flexiplex versions, threads, chemistry and commands for
each of the37 inputs. The linked current RAD receipts record executable hashes
and input identities. BLAZE and Flexiplex settings vary by input; read their row
before repeating a comparison.

Use Linux with GNU time at `/usr/bin/time`, which records the native runtime
and memory use. Build the exact source commit with CMake3.18 or newer, a C++17
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
It can also enforce an optional `--rad-sha256` pin. A binary from another
commit is not accepted as a verified 4acbe00 build.

Choose one JSON record from `source_data/figure_04/run_records/`, obtain its
complete FASTQ, matched reference and pinned chemistry catalogue, and run from
the manuscript repository root with a new output directory:

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
reference and input hashes. It retains the native command and outputs and then
scores distinct barcode sets. Reference and complete barcode-list inputs are
kept outside Git, at the logical locations in each run record; they are not a
new public barcode-list package. Obtain those inputs from the registered data
source or your local data archive. Controlled spatial data require their
registered access process. Use the matched reference definition and source accessions in the record. A reference is accepted when its file SHA256 matches, or when its canonical barcode-set SHA256 matches; the runner records the actual file hash used. Current execution records also provide `selected_barcode_sha256`, the hash of the sorted selected barcode set; `score/metrics.json` records the same output-set hash for your run. Equivalent gzip compression or row ordering does not change the canonical reference identity.

Read the record's `input_format` before preparing the FASTQ. `fastq.gz` pins the
compressed bytes; `fastq` pins the plain FASTQ bytes. When the record requires
plain FASTQ and the official source is a gzip file, decompress without changing
read order, headers, bases or quality strings:

```bash
gzip -dc official_input.fastq.gz > external_data/figure_04/inputs/DATASET.fastq
```

Then pass that `.fastq` file to `--input`. Do not recompress it for that record.
For an SRA-derived input, read its `input_acquisition` object. It gives the full-quality archive URL, exact archive basename, byte count, MD5 and SHA256; the converter and any compressor versions and executable hashes; and their literal argument lists. Download that archive and keep the recorded `.sra` basename, because the converter uses it in FASTQ read headers. Create the temporary directory named by `--temp` first.

For `fastq.gz`, run the recorded `fasterq` and `pigz` argument lists as a pipeline, writing the compressed output to the record's input path. For `fastq` with compressor method `none`, run the recorded converter command with `--outfile` and move its completed output to the record's input path without compression. The recorded `.partial` output suffix is a filename; keep its bytes unchanged when moving the completed file. Check the expected read and base totals and resulting FASTQ digest before running RAD. When present, `sequence_quality_sha256` hashes each sequence followed by LF and its quality string followed by LF, in read order; it excludes FASTQ headers. These inputs retain the complete original quality strings and technical reads.

For a matched official CellRanger barcode file, remove only a terminal `-1`
suffix and retain one16-base barcode per line; a different gzip timestamp or
compression level is allowed when the canonical matched-set hash agrees.
The run record retains the reference definition and existing dataset source
accessions; it does not invent a reference download location.

`score/metrics.csv` contains barcode counts, TP, FP, FN, precision, recall and F1.
`score/barcode_membership.csv` lets you inspect individual calls and reference
membership. TP is the call/reference intersection, FP is calls outside the
reference, and FN is reference members not called. These are reference-list
agreement measures, not independent proof of biological cell identity.

The runner uses the complete input and preserves its sequences and qualities.
It checks known input identities; where an original input digest was not
recorded, it computes the digest before scanning and records the full-input
selection contract. Empty sequence records are reported separately from the
native processed nonempty-sequence count. The script runs one dataset and does
not submit cluster jobs or change another tool's results.
