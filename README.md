# RAD manuscript: from data to figures

This repository explains the selected analyses for **Figures 1–7** of the RAD
manuscript. Open a figure below to see **the exact RAD, BLAZE and Flexiplex
versions and parameters first**, then inspect the input records, follow each
transformation, and compare its output with the figure.

| Figure | Start here | What the walkthrough follows |
|---|---|---|
| 1 | [Workflow, computational efficiency and Visium HD](docs/figure_01.md) | Executed commands and resource logs → phase timings → summaries; spatial count lineage |
| 2 | [ScTagger synthetic benchmark](docs/figure_02.md) | Read sequence/truth and quality models → selected barcodes → assignment categories |
| 3 | [Off-list assignments and measured correction modes](docs/figure_03.md) | Supplied lists and assignment records → physical-read ledger or read–target pairs → per-target metrics |
| 4 | [All 37 benchmark inputs](docs/figure_04.md) | Each tool's selected list and the matched reference → TP/FP/FN → paired input-level metrics |
| 5 | [Receptor and LR-Split-seq analyses](docs/figure_05.md) | Selected assignment ledgers → 568 paired cells → read/UMI counts; receptor and depth-matched UMI source gaps remain explicit |
| 6 | [Genotype comparison](docs/figure_06.md) | Alignment/CellSNP/VCF records → per-cell genotype states → recall and fixed-coordinate overlays |
| 7 | [Expression comparison](docs/figure_07.md) | Sparse molecule matrices and cohorts → common 8,135-gene statistics → directional recovery and threshold grids |

**Figure 7 contains A–D.** Panel E was removed by the author. The current build
has no Figure 8. Superseded analysis outputs and old figure releases are not part
of this working tree.

## Inspect the data without running anything

Each walkthrough includes a small, explicitly labeled excerpt of the actual
input, a column dictionary, and linked intermediate/output tables. Excerpt
manifests give the source hash and the selection rule; examples are not presented
as full datasets. PNG proofs render directly on GitHub, with editable SVG/PDF
exports alongside them.

- [Dataset identities, accessions and access status](manifests/datasets.tsv):
  37 Figure 4 inputs plus Visium HD and LR-Split-seq.
- [Data guide](data/README.md): formats, identifiers, missing values and how to
  move from a readable excerpt to its full source.
- [Small data examples](data/examples/): bounded records used in the walkthroughs.
- [Complete public Figure 4 inputs](data/figure_04/README.md): all 87 tool/reference
  comparisons for the 29 public inputs can be rescored from the deposited lists.
- [Complete plotting tables](source_data/): the values used by the scripted proofs.
- [File hashes and table columns](manifests/data_files.tsv): byte identity and schema index.
- [Current validation and unresolved dependencies](docs/validation.md): which
  steps were rerun, resumed or only inspected.

## Versions and parameters belong to the producing run

The figure walkthroughs specify versions **per experiment**, not one global
version for the whole paper. This matters: Figure 6 genotype alignments and
Figure 7 expression counts use different RAD and alignment producers. A version
string without its source/patch and command is insufficient. Unrecovered settings
are labeled explicitly.

The custom Flexiplex build is provided in
[**vendor/flexiplex-audit/**](vendor/flexiplex-audit/README.md), with the upstream
commit, exact patch, pre-correction `RawCellBarcode` table schema, source and
binary hashes, build instructions, licenses and a working equivalence test.

## Follow one step at a time

Start with the short scripts linked in the chosen figure walkthrough. Each step
names its input columns, transformation, output and checks. The examples are
small enough to inspect before execution. Full checkpoint rebuild commands are
provided separately; no single master runner is required to understand the work.

[SETUP.md](SETUP.md) describes the environment and where full checkpoints belong.
The scripts distinguish three levels: rendering from source tables, resuming
from retained analysis records/matrices, and rerunning producers from raw reads.
A successful render does not establish a raw rerun.

## Scope and manuscript decisions

Existing statistical choices and annotations are preserved at the author's
request. Source-verification plots are labeled as such and are not substitutes
for native statistical recalculation. The selected scientific definitions,
current author decisions, and remaining evidence gaps are recorded in
[docs/decisions.md](docs/decisions.md).

Evidence-linked manuscript drafts cover [Figures 1, 2 and 4](docs/manuscript_figures_124.md),
[Figure 3](docs/manuscript_figure_03.md), [Figures 5–7](docs/manuscript_figures_567.md)
and the [current legends](docs/current_figure_legends.md).

The RAD implementation is at [indianewok/rad](https://github.com/indianewok/rad).
This repository contains the manuscript analysis and its readable data trail.
The versioned public data package will be linked here after release approval.
