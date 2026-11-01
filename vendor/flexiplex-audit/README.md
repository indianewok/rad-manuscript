# Flexiplex with pre-correction barcode output

This build writes the barcode sequence extracted before correction. Use the pinned source or Linux binary below for the manuscript's raw-to-assigned barcode analyses.

| Component | Pin |
|---|---|
| Upstream | Flexiplex **1.02.6**, commit `d84c8ae4f3865052f2b5ecec816949b94682f302` |
| Local change | [raw_cell_barcode_audit.patch](patches/raw_cell_barcode_audit.patch) |
| Patch SHA-256 | `88dc9cbad139d8ac416803c19c1d4291ebb7e3159f5a1a49205aff59319f86cb` |
| Modified source SHA-256 | `fb3f841074f39c3b56af4979adf850066d9215afe227111280ba14ed46c47541` |
| Linux x86-64 binary | [flexiplex_v1.02.6_raw_to_assigned_audit](bin/flexiplex_v1.02.6_raw_to_assigned_audit) |
| Binary SHA-256 | `38dccd37f1747e5105b62eacde572b7e4c5206fb925dc1fdbe8210ffe8b1e8c4` |
| Alignment dependency | Included Edlib **1.2.7** source |
| Build flags | `-Ofast -pthread -std=c++11` |
| Required environment | `FLEXIPLEX_AUDIT_SOURCE_FILE` **unset** |

The upstream and Edlib licenses are preserved in [licenses/](licenses/).
[manifest.json](manifest.json) records the identity of each source and binary file.
The provided executable is dynamically linked Linux x86-64, with an embedded
GCC 8.5.0 compiler record. Its required symbol versions, including
`GLIBCXX_3.4.22` and `GLIBC_2.14`, are recorded in
[binary_platform.json](binary_platform.json). Rebuild from source for a different
runtime; a rebuild has its own executable hash.

## What the diagnostic table contains

The output is `PREFIX_reads_barcodes.txt`, with these tab-separated columns:

| Column | Meaning |
|---|---|
| `Read` | Original read identifier; a read can have multiple assignment records |
| `CellBarcode` | Selected barcode after Flexiplex correction |
| `RawCellBarcode` | Extracted `exact_bc` sequence before correction |
| `FlankEditDist` | Edit distance of the flank match |
| `BarcodeEditDist` | Edit distance used for the selected barcode match |
| `UMI` | Extracted UMI |

`RawCellBarcode` records the observed sequence. Leave the optional source-set filter `FLEXIPLEX_AUDIT_SOURCE_FILE` unset, as in the command below. Apply the figure-specific physical-read or read–target-pair counting rule to the diagnostic records.

## Build and check

From the repository root:

```bash
mkdir -p results
python3 vendor/flexiplex-audit/build_and_check.py --output results/flexiplex-audit-build
```

The script checks pinned source hashes, reapplies the patch, checks that the
result equals the pinned modified source, and compiles both upstream and
diagnostic executables. A four-read designed fixture covers an exact barcode,
a corrected barcode, a reverse-strand read and a read without the adapter.
It checks that the rebuilt and pinned diagnostic binaries agree, that all common
sidecar columns and emitted FASTQs match the upstream binary, and that the new
column records the actual extracted sequence. The build report records the fixture results and executable hashes.

For a 10x 3′ v3 supplied-list assignment run:

```bash
env -u FLEXIPLEX_AUDIT_SOURCE_FILE \
  results/flexiplex-audit-build/audit \
  -d 10x3v3 -f 8 -e 2 -p 16 \
  -k targets.txt -n sample input.fastq > sample.assigned.fastq
```

Use the **figure-specific command table** for chemistry, discovery flank threshold, target list, threads and input. The command above performs supplied-list demultiplexing with flank distance eight.

## Pinning and hosting this build

Pin this directory to the manuscript repository's full Git commit. Record the upstream commit, patch SHA-256 and binary SHA-256 shown above. Use the supplied binary for the recorded executable identity on compatible Linux x86-64 systems; the build report records a rebuilt executable's compiler, hash and fixture results.

To host a separate release, tag the modified source, for example `flexiplex-1.02.6-rad-audit.1`, and attach the source archive, Linux binary, `SHA256SUMS` and build report to a GitHub Release. Use a distinct tag for this modified build. A fork can retain the upstream parent, apply the exact patch and pin the resulting full commit in each figure's command record.
