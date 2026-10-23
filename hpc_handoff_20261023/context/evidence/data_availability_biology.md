# Data availability: biological source datasets

Verified 22 October 2026. Scope: RAGE-seq, LR-Split-seq, human hippocampal snRNA-seq, and Engblom tonsil data retained in Figures 1–7 or the 37-input barcode benchmark. This report excludes NBC and other analyses exclusive to the removed Figure 8. Only public metadata, repository pages and retained local provenance were read; no sequencing archives were downloaded.

## Text ready to incorporate

RAGE-seq data are available in the European Nucleotide Archive under [PRJEB28878](https://www.ebi.ac.uk/ena/browser/view/PRJEB28878). The cell-line mixture and tumour-draining lymph-node long-read datasets are ERR3268991 and ERR3268990, respectively. Their matched Illumina datasets are ERR3276430 and ERR3276429. LR-Split-seq data are available under [GSE168776](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE168776) and [PRJNA713904](https://www.ncbi.nlm.nih.gov/bioproject/713904); the C2C12 long-read and matched short-read runs are SRR13948564 and SRR13948565. Processed LR-Split-seq matrices and annotations are available as GEO supplementary files.

Human hippocampal long-read and matched 10x Genomics data from Joglekar et al. are openly available through the NeMO Archive collection [dat-717krsa](https://assets.nemoarchive.org/dat-717krsa), in the [human single-nucleus data directory](https://data.nemoarchive.org/biccn/grant/rf1_tilgner/tilgner/transcriptome/sncell/). This collection includes the ten Oxford Nanopore runs from six donors and the matched short-read count matrices. Published cell annotations are available in the [authors’ data repository](https://github.com/noush-joglekar/biccn_tilgner_scisorseq/tree/main/data).

Tonsil sequencing data from Engblom et al., including the eight long-read libraries used in the barcode benchmark, are deposited under controlled access in the European Genome-phenome Archive, dataset [EGAD00001011062](https://ega-archive.org/datasets/EGAD00001011062), study [EGAS00001007337](https://ega-archive.org/studies/EGAS00001007337). Access requires approval from [DAC EGAC00001003294](https://ega-archive.org/dacs/EGAC00001003294), an applicable data-access agreement and ethics approval, and is restricted to noncommercial research by not-for-profit organizations. Associated processed data, metadata, images and analysis scripts are openly available at [Zenodo, DOI 10.5281/zenodo.7961605](https://doi.org/10.5281/zenodo.7961605).

These paragraphs cover only the assigned source families. They must be combined with the other dataset families and a separate, accurate statement about current RAD-derived data and code.

## Accession and match verification

| Dataset used | Long-read source | Matched short-read source | Public evidence and access |
|---|---|---|---|
| RAGE-seq Ramos/Jurkat/monocyte mixture | ERR3268991; ERX3295865; SAMEA5392979 | ERR3276430; ERX3303303; the same sample SAMEA5392979 | [ENA project](https://www.ebi.ac.uk/ena/browser/view/PRJEB28878); both public. The short-read submission is the coordinate-sorted `cell_line_validation_possorted_genome_bam.bam`, not an ENA-generated FASTQ. |
| RAGE-seq TNBC draining lymph node | ERR3268990; ERX3295864; SAMEA5392978 | ERR3276429; ERX3303302; the same sample SAMEA5392978 | [ENA project](https://www.ebi.ac.uk/ena/browser/view/PRJEB28878); both public. The short-read submission is `lymphnode_possorted_genome_bam.bam`. |
| C2C12 LR-Split-seq 1k sublibrary | SRR13948564; GSM5169183, C2C12_long_1k; PacBio Sequel II | SRR13948565; GSM5169184, C2C12_short_1k; Illumina NextSeq 500 | [GEO series](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE168776), [long-read sample](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM5169183), [short-read sample](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM5169184). Public raw reads and GEO processed supplements. |
| Human hippocampus, six donors / ten ONT runs | Exact ten `Hipp_SN_*_ONT*.fastq.tar` files in [NeMO ONT human raw directory](https://data.nemoarchive.org/biccn/grant/rf1_tilgner/tilgner/transcriptome/sncell/oxford_nanopore/human/raw/) | Six donor MEX archives in [NeMO 10x human counts directory](https://data.nemoarchive.org/biccn/grant/rf1_tilgner/tilgner/transcriptome/sncell/10x_v3/human/processed/counts/); underlying reads in [10x human raw directory](https://data.nemoarchive.org/biccn/grant/rf1_tilgner/tilgner/transcriptome/sncell/10x_v3/human/raw/) | Direct public directories; collection explicitly marked open. [Primary paper](https://doi.org/10.1038/s41593-024-01616-4) identifies NeMO dat-717krsa. |
| Eight technical tonsil libraries from six sections | EGA EGAD00001011062 / EGAS00001007337; all eight EGAF file accessions and MD5 checksums matched to the retained input manifest, as detailed below | Shared study processed material in Zenodo 7961605 | [EGA file metadata](https://metadata.ega-archive.org/datasets/EGAD00001011062/files) establishes dataset membership and matching checksums. Controlled access; open [Zenodo archive](https://zenodo.org/records/7961605). |

The RAGE-seq pairings are established directly by identical ENA sample accessions, not by a title-only inference. The [RAGE-seq primary paper](https://doi.org/10.1038/s41467-019-11049-4) also identifies PRJEB28878 as its sequencing deposit.

## Exact hippocampal file correspondence

File names below were found in the public NeMO directory listings and correspond to the ten retained local benchmark inputs. `.fastq.tar` is appended to each ONT basename.

| Donor | ONT basenames | Matched published count archive |
|---|---|---|
| f1 | Hipp_SN_f1_ONT_Run1; Hipp_SN_f1_ONT_Run2 | Hipp_SN_f1_Human_H1539.mex.tar.gz |
| f2 | Hipp_SN_f2_ONT | Hipp_SN_f2_Human_H1364.mex.tar.gz |
| f3 | Hipp_SN_f3_ONT_Run1; Hipp_SN_f3_ONT_Run2 | Hipp_SN_f3_Human_H4676.mex.tar.gz |
| m1 | Hipp_SN_m1_ONT_Run1; Hipp_SN_m1_ONT_Run2; Hipp_SN_m1_ONT_Run3 | Hipp_SN_m1_Human_H6096.mex.tar.gz |
| m2 | Hipp_SN_m2_ONT | Hipp_SN_m2_Human_H1114.mex.tar.gz |
| m3 | Hipp_SN_m3_ONT | Hipp_SN_m3_Human_H5398.mex.tar.gz |

The collection page's displayed download link points to the mouse `scell/` branch. Therefore, retain the explicit human `sncell/` link in the availability statement. The authors’ repository directly links to that human branch. Human files were accessible without authentication. The collection's generic note about controlled-access data is not evidence that these publicly served human files require a DAC application.

## Tonsil access and scope

The access conditions above are stated in the EGA dataset policy. The linked DAC page provides the contact `jakob.michaelsson@ki.se`.

The local benchmark includes `section12`, `section16`, `section17_1T_1B`, `section17_4T_1B`, `section22`, `section31`, `section32_1T_1B` and `section32_4T_1B`: eight technical libraries from six sections. These entries remain in the 37-input benchmark, so their availability statement remains necessary after removal of the Figure 8 spatial receptor analysis. The dataset describes human tonsil samples 1 and 2; eight libraries must not be described as eight donors.

The public [experiment metadata](https://metadata.ega-archive.org/datasets/EGAD00001011062/experiments) lists 86 experiments, including exactly eight PACBIO_SMRT/Sequel experiments described as Long Read-Spatial VDJ. The public [sample metadata](https://metadata.ega-archive.org/datasets/EGAD00001011062/samples) identifies all eight as tonsil2. Seven section labels directly match the benchmark. The retained local input manifest explicitly maps analysis section22 to deposited section21. All eight EGAF accessions occur in the public dataset file list, and all eight public unencrypted MD5 values exactly match the local manifest. This resolves the initial file-mapping uncertainty without downloading controlled-access files.

| Retained analysis library | EGA file accession | Public run accession for corresponding LR sample | MD5 match |
|---|---|---|---|
| section12 | EGAF00008107352 | EGAR00003720678 | Yes |
| section16 | EGAF00008107353 | EGAR00003720681 | Yes |
| section17_1T_1B | EGAF00008107340 | EGAR00003720719 | Yes |
| section17_4T_1B | EGAF00008107344 | EGAR00003720709 | Yes |
| section22, deposited as section21 | EGAF00008107350 | EGAR00003720713 | Yes |
| section31 | EGAF00008107351 | EGAR00003720669 | Yes |
| section32_1T_1B | EGAF00008107341 | EGAR00003720710 | Yes |
| section32_4T_1B | EGAF00008107345 | EGAR00003720715 | Yes |

The EGA file listing reports different file sizes from the local compressed-byte counts, but identical unencrypted MD5 checksums; the checksum comparison is the file-identity check. The audit does not infer the cause of the size discrepancy. The section22 alias is explicit in [input_manifest.tsv, line 6](/Volumes/rad_data/reviewer_comment_data/wl_scan/20260729_spatial_vdj_single_slices_expect2500/input_manifest.tsv:6), with file EGAF00008107350 and MD5 `7d2d4a7d3601c2cd255e70938884fab4`.

## Retained local proof

- [Benchmark inventory](/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/sample_inventory.tsv:8): RAGE-seq rows 8–9; hippocampal runs rows 16–18 and 31–37; tonsil libraries rows 23–30. Row 39 is Visium HD inventory only and is not one of the 37 scalar benchmark inputs.
- [LR-Split-seq matched-data audit](/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/splitseq_shortread_20260727/README.md:8): local read headers establish SRR13948564; lines 12–20 establish matched SRR13948565 and the 1k sublibrary. The same series' 9k and snATAC samples are different inputs.
- [Hippocampal annotation and MEX provenance](/Volumes/rad_data/reviewer_comment_data/tilgner_m1_seurat_reference_mapping_20260806/provenance__SOURCE_AND_CODE_PROVENANCE.tsv:2): published `SR_humanHipp_combined_barcodeCTassignments.gz` and m1 released MEX files, with checksums. The published annotation file SHA-256 is `e088cf6581bf2754bdf1fc913e2ba12e6d8516f4956548b1d7166ac226c515e5`.
- [ENA run metadata](/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/data_availability_metadata/rageseq_ena.tsv): six public RAGE-seq run records, including sample-level matching. The extra primary-tumour runs were not added to the proposed statement.
- [Cell-line short-read XML](/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/data_availability_metadata/rageseq_short.xml) and [lymph-node short-read XML](/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/data_availability_metadata/rageseq_ln_short.xml): public status and submitted BAM paths. Primary XML URLs are `https://www.ebi.ac.uk/ena/browser/api/xml/ERR3276430` and `https://www.ebi.ac.uk/ena/browser/api/xml/ERR3276429`.
- [LR-Split-seq long-read XML](/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/data_availability_metadata/lrsplit_long.xml) and [short-read XML](/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/data_availability_metadata/lrsplit_short.xml): exact run, experiment, sample and platform metadata, from the ENA browser API for SRR13948564 and SRR13948565.
- [NeMO ONT directory snapshot](/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/data_availability_metadata/nemo_oxford_nanopore_raw.html), [matched MEX snapshot](/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/data_availability_metadata/nemo_10x_counts.html), and [matched raw short-read snapshot](/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/data_availability_metadata/nemo_10x_v3_raw.html): exact publicly listed file names. Additional NeMO directory snapshots are in the same metadata directory.
- [EGA study metadata](/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/data_availability_metadata/egas.json): dataset-to-study relation obtained from `https://metadata.ega-archive.org/datasets/EGAD00001011062/studies`.
- [Eight-library EGA checksum verification](/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/data_availability_metadata/ega_eight_library_verification.json): saved comparison of all eight local manifest records against the public [EGA file list snapshot](/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/data_availability_metadata/ega_files.json). Public sample, experiment and run metadata are retained in the same directory as `ega_samples.json`, `ega_datasets_EGAD00001011062_experiments.json` and `ega_runs.json`.

## Remaining availability issue

Source accessions/files are resolved for all four assigned families, including all eight tonsil long-read libraries. Analysis section22 is deposited as section21, as recorded in the retained input manifest and confirmed by the matching EGAF accession and MD5. No further author clarification is needed for that alias.

This audit also does not establish public deposition of current RAD-derived matrices, source data, figures or benchmark outputs. The parent audit found no verified current derived-data deposit; the older reserved Zenodo record 20189813 is private and its retained content is stale. Do not present that record as a public current deposit or substitute an unsupported “available on request” statement. The final manuscript must accurately state the chosen availability plan for newly generated RAD outputs separately.
