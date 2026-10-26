# RAD manuscript analyses

This repository contains the data, code and figures for the RAD manuscript. The
analyses compare barcode detection, read assignment and downstream biological
measurements across long-read sequencing datasets. The RAD software is available
at [indianewok/rad](https://github.com/indianewok/rad).

Each figure guide describes the experiment, its inputs, software versions and
analysis steps. Source tables and intermediate files link the plotted values to
the calculations that produced them.

| Figure | Analysis |
|---|---|
| [1](docs/figure_01.md) | RAD workflow, computational efficiency and Visium HD |
| [2](docs/figure_02.md) | Barcode discovery and read assignment in the ScTagger simulation |
| [3](docs/figure_03.md) | Off-list barcode challenges and barcode correction in LongBench |
| [4](docs/figure_04.md) | Barcode detection across 37 sequencing inputs |
| [5](docs/figure_05.md) | Receptor recovery and LR-Split-seq read and molecule counts |
| [6](docs/figure_06.md) | Genotype analysis in LongBench single-nucleus data |
| [7](docs/figure_07.md) | Differential cell-line expression in LongBench single-nucleus data |

[View the figures](figures/README.md) as exported from the saved Prism projects.

## Data and analysis

[SETUP.md](SETUP.md) gives installation instructions and commands for working
from source tables, saved checkpoints or raw reads. The figure guides specify
the software versions and parameters used for each experiment.

- [Data guide](data/README.md): file formats, identifiers and acquisition sources.
- [Dataset registry](manifests/datasets.tsv): input identities, accessions and reference datasets.
- [Examples](data/examples/): selected source records with extraction rules and expected outputs.
- [Source tables](source_data/): complete tables used to calculate the plotted metrics.
- [Figure 4 barcode lists](data/figure_04/README.md): tool and reference lists for the 29 public inputs.
- [File inventory](manifests/data_files.tsv): schemas, row counts and SHA-256 hashes.
- [Reproducibility checks](docs/validation.md): numerical checks and the inputs needed to repeat each analysis.
- [Data packages](docs/release_review.md): checkpoint archives and their contents.

The [diagnostic Flexiplex build](vendor/flexiplex-audit/README.md) records the
barcode sequence before correction. Its source, patch, build instructions and
checks are included with the analysis code.

## Manuscript text

Methods and figure descriptions are grouped by analysis: [Figures 1, 2 and 4](docs/manuscript_figures_124.md),
[Figure 3](docs/manuscript_figure_03.md), and [Figures 5–7](docs/manuscript_figures_567.md).
The [figure legends](docs/current_figure_legends.md) describe each panel.

Citation information is in [CITATION.cff](CITATION.cff). Repository code is
covered by the [MIT license](LICENSE); third-party software notices are in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
