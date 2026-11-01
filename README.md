# RAD manuscript analyses

Data, commands and analysis scripts for the RAD manuscript. Each figure guide follows the input reads through processing, counting and plotting. RAD software is maintained at [indianewok/rad](https://github.com/indianewok/rad).

| Figure | Analysis | Data and examples |
|---|---|---|
| [1](docs/figure_01.md) | RAD processing, run time, memory and Visium HD barcode recovery | [Source data](source_data/figure_01/README.md) · [Example](data/examples/figure_01/README.md) |
| [2](docs/figure_02.md) | ScTagger barcode discovery, quality sweeps and read assignment | [Source data](source_data/figure_02/README.md) · [Example](data/examples/figure_02/README.md) |
| [3](docs/figure_03.md) | Matched off-list experiments and LongBench FM1/FM2 correction outcomes | [Source data](source_data/figure_03/README.md) · [Example](data/examples/figure_03/) |
| [4](docs/figure_04.md) | Barcode discovery across 37 sequencing inputs | [Source data](source_data/figure_04/README.md) · [Example](data/examples/figure_04/README.md) |
| [5](docs/figure_05.md) | Receptor-read recovery and LR-Split-seq read and UMI counts | [Source data](source_data/figure_05/README.md) · [Example](data/examples/figure_05/PREVIEW.md) |
| [6](docs/figure_06.md) | Genotype-based cell-line assignment in LongBench single nuclei | [Source data](source_data/figure_06/README.md) · [Example](data/examples/figure_06/PREVIEW.md) |
| [7](docs/figure_07.md) | H146-versus-H526 differential expression | [Source data](source_data/figure_07/README.md) · [Example](data/examples/figure_07/PREVIEW.md) |

## Follow an analysis

1. Open its figure guide for the input datasets, software versions and command-line settings.
2. Run the small example and compare its output with the supplied result.
3. Use the source tables to follow the complete calculation, or run the raw-read commands with the listed inputs.

[Setup](SETUP.md) covers the analysis environment and input locations. The [dataset list](manifests/datasets.tsv) gives sequencing accessions. The [figure gallery](figures/README.md) displays the figures, and the [legends](docs/current_figure_legends.md) explain their panels.

| Directory | Contents |
|---|---|
| `source_data/figure_XX/` | Input and result tables, field definitions, software settings and run records |
| `data/examples/figure_XX/` | Small read records, counting examples and expected outputs |
| `scripts/figure_XX/` and `scripts/revision/` | Programs referenced by the figure guides |
| `figures/figure_XX/` | Figure images |
| `environments/` | Pinned software dependencies |

The [custom Flexiplex build](vendor/flexiplex-audit/README.md) exposes pre-correction barcodes. The [FLAMES configurations](docs/pinned_flames_configs.md) pin the LR-Split-seq and LongBench processing code.

## Citation and license

[CITATION.cff](CITATION.cff) gives the manuscript citation. Analysis code uses the [MIT license](LICENSE); copied software retains its accompanying license.
