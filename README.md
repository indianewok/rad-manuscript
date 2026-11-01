# RAD manuscript analyses

This repository describes how the figures in the RAD manuscript were generated.
The workflows follow long-read sequencing data through barcode discovery,
demultiplexing, read assignment and downstream cell-level analysis. The RAD
software is maintained at [indianewok/rad](https://github.com/indianewok/rad).

Each figure guide brings together its inputs, software versions, commands,
counting rules and source tables. The [figure gallery](figures/README.md) provides
the exported figures; the [legends](docs/current_figure_legends.md)
describe the individual panels.

| Figure | Experiment and workflow |
|---|---|
| [1](docs/figure_01.md) | RAD read processing, computational performance and Visium HD spatial barcode recovery |
| [2](docs/figure_02.md) | Barcode discovery and read assignment using the ScTagger simulation and Badread quality models |
| [3](docs/figure_03.md) | Off-list challenges in ScTagger, LongBench and RAGE-seq; FM1 and FM2 correction outcomes |
| [4](docs/figure_04.md) | Barcode discovery across 37 sequencing inputs and their matched references |
| [5](docs/figure_05.md) | Immune-receptor recovery and LR-Split-seq read and UMI counts |
| [6](docs/figure_06.md) | Genotype-based cell-line assignment in LongBench single nuclei |
| [7](docs/figure_07.md) | Differential cell-line expression in LongBench single nuclei |

## Reproduce an analysis

[SETUP.md](SETUP.md) describes the analysis environment and the three starting
points: deposited source tables, intermediate checkpoints and raw sequencing
reads. Follow the corresponding figure guide for the experiment-specific
commands and parameters.

| Directory | Contents |
|---|---|
| `scripts/figure_XX/` | Counting, scoring and plotting programs |
| `source_data/figure_XX/` | Tables used in the figures, with software and input records |
| `data/examples/figure_XX/` | Small source records that illustrate the calculations |
| `figures/figure_XX/` | Exported figures and plotting outputs |
| `environments/` | Pinned analysis dependencies |

The [dataset registry](manifests/datasets.tsv) identifies the sequencing inputs
and their accessions. Figure images are provided with their legends and source
tables. The [export record](source_data/prism_exports.json) identifies the
source-file checksums and layout IDs. Larger FASTQ, alignment and matrix files
are restored separately at the paths used by each workflow.

The [diagnostic Flexiplex source](vendor/flexiplex-audit/README.md) records the
extracted barcode before correction. The [pinned FLAMES configurations](docs/pinned_flames_configs.md)
identify the LR-Split-seq and LongBench alignment settings used in Figures 5
and 6.

## Citation and license

[CITATION.cff](CITATION.cff) gives the manuscript citation. Repository analysis
code is covered by the [MIT license](LICENSE); copied third-party software
retains its accompanying license.
