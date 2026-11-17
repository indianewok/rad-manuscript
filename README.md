# RAD manuscript analyses

Methods, commands and source data for the RAD manuscript. [RAD software](https://github.com/indianewok/rad)

| Figure | Analysis | Data and examples |
|---|---|---|
| [1](docs/figure_01.md) | RAD processing, run time, memory and Visium HD barcode recovery | [Source data](source_data/figure_01/README.md) · [Example](data/examples/figure_01/README.md) |
| [2](docs/figure_02.md) | ScTagger barcode discovery, quality sweeps and read assignment | [Source data](source_data/figure_02/README.md) · [Example](data/examples/figure_02/README.md) |
| [3](docs/figure_03.md) | Matched off-list experiments and LongBench FM1/FM2 correction outcomes | [Source data](source_data/figure_03/README.md) · [Example](data/examples/figure_03/) |
| [4](docs/figure_04.md) | Barcode discovery across 37 sequencing inputs | [Source data](source_data/figure_04/README.md) · [Example](data/examples/figure_04/README.md) |
| [5](docs/figure_05.md) | Receptor-read recovery and LR-Split-seq read and UMI counts | [Source data](source_data/figure_05/README.md) · [Example](data/examples/figure_05/PREVIEW.md) |
| [6](docs/figure_06.md) | Genotype-based cell-line assignment in LongBench single nuclei | [Source data](source_data/figure_06/README.md) · [Example](data/examples/figure_06/PREVIEW.md) |
| [7](docs/figure_07.md) | H146-versus-H526 differential expression | [Source data](source_data/figure_07/README.md) · [Example](data/examples/figure_07/PREVIEW.md) |

[Setup](SETUP.md) · [Sequencing accessions](manifests/datasets.tsv) · [Figure gallery](figures/README.md) · [Figure legends](docs/current_figure_legends.md)

The [custom Flexiplex build](vendor/flexiplex-audit/README.md) exposes pre-correction barcodes. The [FLAMES configurations](docs/pinned_flames_configs.md) pin the LR-Split-seq and LongBench processing code.

## Citation and license

[CITATION.cff](CITATION.cff) gives the manuscript citation. Analysis code uses the [MIT license](LICENSE); copied software retains its accompanying license.
