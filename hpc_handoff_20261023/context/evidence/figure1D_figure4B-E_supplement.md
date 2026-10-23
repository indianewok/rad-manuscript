# Supplement: Figure 1D and Figure 4B–E provenance

## Figure 4B–E: source recovered

An exact, SHA-256-verified copy of the saved project was made from the authorized source:
`/Users/cmv/Library/CloudStorage/Dropbox-DartmouthCollege/Chinmay Vaidya/scRNA_Seq_Nanopore_LongRead_Project/Nat Comm/appeal/figure_revisions/092126_Figure_4_CMV_V1.prism`.

The copy is `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/evidence/092126_Figure_4_CMV_V1.prism`. The original was not modified. Archive metadata says created/modified with Prism 11.0.0.93 for Mac; last saved 22 September 2026 at00:58:06Z. This confirms the figure-authoring version, not a SeqKit version.

The saved data sheet **SeqKit stats (all reads)** is `data/sheets/25C36598-E266-51BB-B350-2807CF182B3F/sheet.json`. Its table is `data/tables/3503036B-4EA6-5554-B401-9CEECB8B40A7/data.csv`, containing exactly37 rows. Ordered numerical columns are num_seqs, sum_len, min_len, avg_len, max_len, Q1, Q2, Q3, sum_gap, N50, N50_num, Q20(%), Q30(%), AvgQual, GC(%). The relevant dataset definitions are:

- num_seqs: `data/sets/05BFCDBC-034B-5A3F-A45B-7A558B4CD7C3.json`.
- AvgQual: `data/sets/AFBA5CFB-E0A4-511F-9C50-3E3F5FF64033.json`.
- GC(%): `data/sets/F36F4326-BA43-513D-A723-1E30E7C96B85.json`.

All37 input rows were exported with their saved column names, without calculating new statistics, to `Figure4_SeqKit_stats_saved.csv` in this evidence folder. Its accompanying `Figure4_SeqKit_saved_provenance.json` records the copied-project hash, sheet definition, and column mapping.

**These are long-read input characteristics.** The saved values include ScTagger-L4,993,805 reads (AvgQual20.00; GC49.14%), LongBenchSC-ONT117,002,380 (16.02;45.61%), LongBenchSN-ONT119,016,231 (16.22;44.79%), and LongBenchSC-PB195,242,483 (25.90;45.14%). Thus the caption phrase “short-read data characteristics” does not describe panelsC–E. The barcode references in panelB can originate from short-read data; that does not make the input sequence summaries short-read summaries. These are stated to cover all reads, not a subsample.

Reference whitelist counts and category labels are additionally present in saved sheet **Data11**, `data/sheets/10DE643C-715C-4701-9786-6FDB33CF5B7C/sheet.json`, table `data/tables/21DDD3EA-91C6-4485-955E-8B1CF0644C37/data.csv`. The37 labels comprise2 Synthetic,11 Single cell,12 Single nuclei,9 Visium,3 Targeted LR-Seq. Reference counts match the immune-corrected package: RAGEseq-TNBC-LN5,978, ScMixology2248, ScTagger50/5,000, LongBench5,211/12,012. This independently supports panelB's reference definition.

### Methods text supported now

Input sequence characteristics were summarized from all long reads in each of the37 benchmark inputs with SeqKit. The number of reads, GC percentage, and AvgQual values were taken from the saved SeqKit statistics table. Each plotted observation represented one input file or benchmark input. Reference barcode counts were taken from the corresponding exact synthetic, matched short-read, or on-tissue reference set. Separate technical runs remained separate input entries. The synthetic inputs retained their original uniform Phred20 scores in this dataset-wide comparison.

### Remaining narrow provenance gap

The actual SeqKit invocation and version were not stored in the copied Prism table or its project-info sheet, which has blank protocol/notes fields. No matching all37 execution table was found among the inspected retained metadata. The main text can accurately name the SeqKit output fields now, but should not invent a version or command. In particular, do not reinterpret SeqKit AvgQual as the arithmetic mean of per-base Phred scores without verifying the generating version/implementation. The exact execution record can be added when supplied. No new tests or p-values were calculated.

## Figure 1D: binning recovered; exact plot normalization still open

The retained HD source directory is:
`/Volumes/rad_data/raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts/`.

`aggregate_to_sr16.py:3–10,32–46,55–82` explicitly maps a2µm spot identifier `s_002um_<column>_<row>-1` to a16µm bin by integer-dividing both coordinates by8. Counts are summed across each8×8 block of2µm spots. The output identifier is `s_016um_<column//8>_<row//8>-1`. It emits one column per flowcell: PBC44593,PBC44760,PBC49262,PBC52788. Rows without a mapped spot are excluded.

`bin_overlap_rad_vs_seurat.py:3–8,47–85` identifies the Seurat-input reference as Space Ranger `filtered_feature_bc_matrix` barcodes. It reads the retained SUP-basecall barcode lists at2,8,and16µm. Its RAD spot mapping uses observed barcode-pair-to-spot links from the upstream workflow and can leave unmatched pairs unmapped. This script measures set overlap, not the plotted ncpm; it is evidence for the retained coordinate/reference workflow, not proof of the exact color normalization.

The directory contains `uncorrected_counts_by_sr16.csv`, `canonical_per_spot.csv.gz`, `per_bin_compare_PBC44593.csv.gz`, and `visium_hd_whitelist/`. These are plausible source tables for the PBC44593 map described in the master figure inventory, but no complete plotted-panel export or R plotting command was identified. In addition, `legacy/` contains superseded Hamming-inclusive results. `exact_match_counts.py` estimates a canonical barcode per spot by maximal summed support across four flowcells; that estimation must not be described as a known chemistry mapping or substituted for the final figure method without confirming its use.

The figure caption itself states Space Ranger in_tissue metadata, Seurat, RAD, and log10 ncpm. It mistakenly gives16-mm spots; the actual binning code and VisiumHD identifiers establish16µm. The exact denominator used for CPM, treatment of zero bins or pseudocount, clipping/color limits, Seurat input-count field, selected flowcell, and exact RAD scan/demux output remain unverified. A generic formula log10(10^6×count/sum(count)) would be a plausible interpretation but is **not verified execution evidence** and should not be inserted as fact.

### Methods text supported now

VisiumHD barcode counts were linked to the spatial grid and summarized in16µm bins. Each bin combined an8×8 block of2µm capture positions, with the two grid indices divided by8 and rounded down. Space Ranger in_tissue annotations defined the reference tissue region. [Confirm the exact Seurat count field and RAD source table.] Spatial maps displayed log10-transformed normalized counts per million. [Confirm normalization denominator and handling of zero counts before supplying the full equation.]

### Focused author question

Please identify the script or saved plotting object used for the three-panel PBC44593 Space Ranger/Seurat/RAD map, or confirm: count field for Seurat; RAD scan versus demux counts; whether one or all four flowcells was used; CPM denominator before/after the tissue mask; and whether a pseudocount was added before log10. The8×8 binning and16µm unit are already verified.
