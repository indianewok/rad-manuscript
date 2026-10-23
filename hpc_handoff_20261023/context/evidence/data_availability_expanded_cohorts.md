# Data availability: expanded whitelist cohorts

Verified 22 October 2026. Scope: the ten benchmark inputs from MPNST (four), PromethION iPSC (one), Isosceles ovarian (one), LeBrigand MOB (one pooled input), and Beaulaurier MMR/Measles (three). Removed NBC/Figure 8 work is excluded. No sequencing data were read or downloaded for this audit; only small local provenance and public metadata were inspected.

## Ready-to-use Data Availability wording

The MPNST long-read data are available under ArrayExpress [E-MTAB-15190](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-15190) and ENA [PRJEB90127](https://www.ebi.ac.uk/ena/browser/view/PRJEB90127) (ERR15095094–ERR15095097). The matched short-read data are available under [E-MTAB-14222](https://www.ebi.ac.uk/biostudies/arrayexpress/studies/E-MTAB-14222) and [PRJEB77277](https://www.ebi.ac.uk/ena/browser/view/PRJEB77277). The iPSC-derived neural progenitor PromethION data are available under [PRJEB54718](https://www.ebi.ac.uk/ena/browser/view/PRJEB54718) (ERR9958135); the published processed reference data are available at [Figshare, doi:10.26188/20335203.v1](https://doi.org/10.26188/20335203.v1). The Isosceles ovarian cell-line mixture is available under [GSE248115](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE248115) and [PRJNA1041796](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1041796). The mouse olfactory bulb spatial data are available under [GSE153859](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE153859) and [PRJNA644362](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA644362) (SRR12157794 and SRR12157795). The Beaulaurier et al. MMR-vaccination data are available under [PRJNA1087553](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1087553). The inputs used were SRR28349077 (P7), SRR28349076 (P8 VDJ-enriched), and SRR28349078 (P8 whole transcriptome), with matched short-read runs SRR28349073 and SRR28349074.

This wording covers these cohorts only. Parent agent will merge it with the other included datasets and any RAD-produced-data deposition statement.

## Exact selected inputs and public verification

| Benchmark label | Actual selected long-read input | Matched short-read/reference material | Study record |
|---|---|---|---|
| MPNST1 scNaUMI-seq MinION | ERR15095094; sample SAMEA118427700 | MPNST1/2020_23; four paired-end lanes ERR13346848, ERR13346853, ERR13346910, ERR13346915 | E-MTAB-15190 / PRJEB90127; short reads E-MTAB-14222 / PRJEB77277 |
| MPNST1 scNaUMI-seq PromethION | ERR15095095; SAMEA118427701 | Same MPNST1 short-read reference | Same |
| MPNST2 ONT protocol | ERR15095096; SAMEA118427702 | MPNST2/2022_26; four paired-end lanes ERR13346861, ERR13346867, ERR13346884, ERR13346900 | Same |
| MPNST2 scNaUMI-seq | ERR15095097; SAMEA118427703 | Same MPNST2 short-read reference | Same |
| PromethION_iPSC | ERR9958135, submitted file `LR_sc-RNA-seq_promethION_LSK110_pass.fastq.gz`; SAMEA110357666 | Published Cell Ranger filtered matrix from the authors' Figshare analysis data, 1,022 retained barcodes | PRJEB54718; doi:10.26188/20335203.v1 |
| Isosceles-ovarian-GSE248115 | SRR26865982, GSM7906077 | GSM7906076 published Cell Ranger barcode file; matched raw Illumina run SRR26865983 was also acquired | GSE248115 / PRJNA1041796; GSE248118 is the broader parent series |
| LeBrigand-MOB | SRR12157794 + SRR12157795, pooled as one input; GSM4656184 | MOB Illumina sample GSM4656181 and its spatial reference/on-tissue mask; matched raw archive run SRR12157784 is contextual, not proof it was reprocessed here | GSE153859 / PRJNA644362 |
| Measles-P7 | SRR28349077, library PAI05989_PAI07242_MMR_P7 | SRR28349073; SAMN40448137 | PRJNA1087553 / SRP495328 |
| Measles-P8-VDJ-enriched | SRR28349076, library PAI92332_MMR_P8_enriched | SRR28349074; SAMN40448136 | Same |
| Measles-P8-WTA | **SRR28349078 only**, library PAM80546_PAM71314_MMR_P8 | Same P8 short-read run SRR28349074 | Same |

The MPNST pairing is independently stated in the [NCBI BioProject record](https://www.ncbi.nlm.nih.gov/bioproject/1350157). The [Hamraoui et al. paper](https://academic.oup.com/nargab/article/8/3/lqag070/8725494) directs readers to E-MTAB-15190. The [BLAZE paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC10077662/) and [authors' repository](https://github.com/youyupei/bc_whitelist_analysis/) verify the iPSC study and processed-data repository. The [Isosceles GEO record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE248115) specifically identifies the three-line ovarian mixture, while [GSM7906077](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM7906077) identifies its PromethION sample. The [MOB GEO sample](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4656184) verifies the olfactory-bulb identity. The [Beaulaurier et al. paper](https://genome.cshlp.org/highwire_display/entity_view/node/1071768/full) gives PRJNA1087553.

## Exact local provenance

All paths in this section are relative to `/Volumes/rad_data/reviewer_comment_data/`.

- Cohort inclusion: `three_tool_whitelist_complete_rageseq_immune_20260901/sample_inventory.tsv`; `master_native_comparison_20260811/provenance/dataset_manifest.tsv`.
- MPNST input names/callsets: `mpnst_native_three_tool_whitelist_20260811/provenance/callset_manifest.tsv`. All sixteen paired short-read FASTQ acquisition markers are preserved under `scratch_preservation_20260921/files/rad_biological_benchmark_20260731/raw/E-MTAB-14222/`; their run IDs and recorded MD5s match public ENA metadata. These markers establish acquisition, and the sample inventory identifies the corresponding Cell Ranger reference used.
- iPSC: `wl_scan/20260730_promethion_four_tool_benchmark/analysis/REPORT.md` identifies the submitted pass FASTQ and MD5 `9673bd0e626a4fe22fd89a1f98a7130c`, exactly matching ENA ERR9958135. `analysis/rad_only_biology/provenance.json` identifies the published `data/hiPSC_diff/cellranger/filtered_feature_bc_matrix.h5` reference from Figshare dataset20335203 and the authors' repository.
- Ovarian: `scratch_preservation_20260921/files/rad_biological_benchmark_20260731/scripts/run_four_tools_GSE248115.sh`, lines23–26, explicitly uses `SRR26865982_ONT_PromethION.fastq.gz` and `GSM7906076_Illumina_CellRanger_barcodes.csv.gz`. Corresponding acquisition markers are preserved in `raw/GSE248115/`. The public GEO filename is `GSM7906076_LIB5445371_SAM24404003_barcodes.csv.gz`.
- MOB: `wl_scan/20260731_lebrigand_MOB_complete_two_accession_benchmark/provenance/input_manifest.tsv` and `scripts/run_combined_benchmark.sh`, lines5–8, explicitly concatenate both runs. Recorded MD5s `ac05146de32ac04bc42e5b6ef36d1a5a` and `d1cd65d8f5a55fb1b189c0019204f872` match the two ENA archive FASTQs exactly.
- P7 and P8 VDJ: `whitelist_native_three_tool_graph_ready_20260810/source_metrics/measles_p7_p8_four_tool_README.md`, Primary raw scope, explicitly maps both ONT and paired Illumina accessions.
- P8 WTA: `scratch_preservation_20260921/files/measles_p8_whole_three_tool_20260801/README.md`, lines3–5; `provenance/run_manifest.tsv`; and `scripts/run_rad.sh`, line6. All specify SRR28349078. The callset metrics reproduce the final cohort values, including RAD10,100, BLAZE10,640, and Flexiplex9,553 selected barcodes. **SRR30903122, a separate P8 R10 run, was not used in this benchmark input.**

## Scope and access details that should not be lost

1. The ten entries are benchmark inputs, not ten independent biological specimens. MPNST has two specimens sequenced through four long-read libraries; Beaulaurier has P7/P8 gates, with two different P8 library types; MOB pools two runs from one sample.
2. The iPSC input is the submitted pass-read collection, not every raw signal/basecall file in PRJEB54718. The paper also includes GridION/Q20 and scmixology2 runs, which should not be implied by the iPSC label.
3. GSE248118 covers additional bulk ovarian datasets. GSE248115 is the exact single-cell subset used here.
4. MOB's submitted source objects are named `mob164315_spatial_nanopore_PAE59649.umifound.bam.1` and `...PAE06474.umifound.bam.1`. The benchmark used their publicly supplied FASTQ conversions (29,773,474 reads). Do not describe these as demonstrated unfiltered full-flowcell raw reads. This is a provenance distinction, not a new numerical audit.
5. ENA currently returns an SRR28349078 record but no mirrored FASTQ URLs and a zero read_count field. **NCBI SRA verifies the actual run as public**, `load_done=true`, `static_data_available=1`, and `total_spots=270994675`, with both original FASTQ parts listed. Therefore the empty ENA FASTQ fields do not mean the run is unavailable or empty. Cite NCBI BioProject/SRA for this input.
6. ENA's instrument_model for ERR15095094 says PromethION, while its sample/library title and the study describe MPNST1 MinION. Preserve the study/sample designation rather than silently relabeling the benchmark from that inconsistent instrument field.
7. No author clarification is required for the accession mappings above. This report does not claim that RAD-generated outputs have been deposited; that is a separate manuscript-wide availability decision.

## Saved primary metadata

Small public records retrieved during this audit are saved in `paper_revision_20261022/evidence/data_availability_public_metadata/`. ENA TSVs include accession links, libraries, samples, read counts, and, where requested, file URLs and MD5s. Each has a neighboring `.url` file recording its exact API request. `SRR28349078_sra.xml` is the NCBI SRA public-run record; `figshare20335203.json` verifies DOI10.26188/20335203.v1; `GSM7906076.txt` gives the original GEO barcode-file URL. No external repository was modified.
