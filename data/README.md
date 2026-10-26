# Read the data from its source to the figure

Start with the [figure walkthroughs](../README.md). Each begins with the actual
producer versions and parameters, then follows named records through small
scripts to the plotted values.

| Location | Contents | How to use it |
|---|---|---|
| [`examples/`](examples/) | Small real excerpts, with source hashes and selection rules | Open directly on GitHub; follow the worked rows |
| [`../source_data/`](../source_data/) | Complete selected plot/metric tables and schemas | Inspect values, join keys and denominators; rerender a panel |
| [`../manifests/datasets.tsv`](../manifests/datasets.tsv) | Dataset/input IDs, accessions, access status and reference type | Locate the raw acquisition source and distinguish technical inputs |
| [`../manifests/data_files.tsv`](../manifests/data_files.tsv) | Table columns, row counts, byte sizes and SHA-256 hashes | Verify exactly which file is being inspected |
| `../checkpoints/` | Larger local read ledgers, sparse matrices and reference files | Restore the separately packaged checkpoint files; these are excluded from Git |

## The file types

**FASTQ** has four lines per read: identifier, sequence, separator and quality
string. A physical read can produce more than one emitted segment. The example
must say whether it is a physical read or a segment; never infer that from the
number of rows alone.

**Assignment TSVs** retain the original read ID, the tool-selected barcode and,
where available, the observed raw barcode. The diagnostic Flexiplex table keeps
`CellBarcode` and `RawCellBarcode` separately. A barcode that was not selected is
not the same as a selected barcode with zero reads. Figure 3's strict-read
challenge excludes every ID with multiple assignment rows, including identical
duplicates. Its measured-correction analysis instead uses unique read–target
pairs and allows overlapping class flags. The [Figure 3 guide](../docs/figure_03.md)
shows why those denominators differ.

**Matrix Market / MEX** uses separate matrix, feature and barcode files. Integer
row/column coordinates are one-based indexes into the feature/barcode files.
All three files are required. Figure 7 normalization uses each cell's complete
library total before filtering genes; a tiny displayed matrix slice is not a
valid substitute for that total.

**VCF and CellSNP** preserve variant order and cell order. Figure 6 explicitly
records the identical duplicated VCF records present in the selected source;
counts of records and counts of unique variant keys differ. No deduplication or
coordinate conversion is performed silently.

**Plot tables** use stable input/barcode/gene keys and preserve the numerator,
denominator, missingness and transformation. Empty or null fields mean missing
or undefined as specified by the local schema. Zero means an observed zero.
The file inventory's `header_present` field identifies native tables without
headers, including barcode lists and `samtools idxstats` exports. Their first
line is counted as data; the inventory supplies descriptive column names.

## Where full inputs come from

The [dataset registry](../manifests/datasets.tsv) records 37 Figure 4 input
identities, plus Visium HD and LR-Split-seq. Raw-read accessions and matched
reference definitions belong to each input; a study accession alone is not a
file identity. Figure-specific manifests retain exact file hashes and commands.

The eight Engblom/Swedish Visium libraries use controlled EGA access
(`EGAD00001011062`, study `EGAS00001007337`, DAC `EGAC00001003294`). Their raw
reads are not redistributed here. The registry preserves their benchmark
identities; derived-data release eligibility remains part of final release
review. ScMixology2 is explicitly reconstructed and remains in all 37 inputs.

The older published workspace record is not the current data dependency.
Current source tables, schemas and checkpoint instructions replace global
R sessions as the readable entry point. No superseded workspace is deposited in
this tree. Current archival identifiers will be added only after they are verified
and the release is approved.
