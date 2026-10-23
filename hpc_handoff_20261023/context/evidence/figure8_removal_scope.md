# Scope of Figure 8 removal

Audited 22 October 2026. No manuscript or source document was edited. Paragraph indices below are zero-based top-level Word body paragraph indices in the current working DOCX. Original source indices are the bracketed indices in `extracted/Manuscript.txt`.

## Main recommendation

Remove the three downstream receptor-analysis Methods sections, the corresponding Results section, the unsupported application claims elsewhere, and the old Figure 5 artwork/legend embedded in the manuscript. Old Figure 5 is the same analysis as **current Figure 8**. Do not remove current Figure 5, which contains retained RAGE-seq receptor concordance and LR-Split-seq benchmarks.

The NBC culture and sorting methods no longer have a retained figure that uses their data. NBC is expressly excluded from the confirmed 37-input benchmark. The general targeted-library preparation paragraph needs a separate decision only if it is intended to document one of the retained Measles datasets; that shared use has not been established by the retained evidence.

## Definitive analysis Methods removal

Current working source: `/Users/cmv/Desktop/RAD_paper_revision_2026-10-22/working/Manuscript_methods_working_2026-10-22.docx`.

| Heading | Current Word paragraphs | Current draft text lines | Recommendation |
|---|---:|---:|---|
| Immune receptor assembly and gene annotation |125–126|`scripts/methods_biology.txt:34–35`|Remove heading and entire paragraph: RNA-Bloom2, assembled-transcript receptor classification, IgBLAST/IMGT annotation, V-gene allele collapse.|
| Clonotype and isotype analysis |127–128|37–38|Remove heading and entire paragraph: Immcantation, SHazaM, SCOPeR, multi-isotype classification and pheatmap.|
| IGH coverage and spatial clonotype maps |129–131|40–43|Remove heading and both paragraphs: tonsil microenvironment annotation, T2T-CHM13 IGH depth profiles, clone/isotype maps and membrane/secreted states.|

These methods support current Figure 8A–E. No retained Figure 1–7 requires assembled receptors, clonotype assignment, constant-region profiles or secretion-state classification. The retained RAGE-seq analysis uses raw-read alignment to the TRUST4 BCR/TCR reference and must remain: current paragraphs106–108, headed “Receptor assignment in the RAGE-seq cell-line mixture.” The retained tonsil barcode benchmarks and Visium HD spatial comparison must also remain; neither requires the removed clone-level analysis.

## NBC wet-lab methods

| Heading/block | Current Word paragraphs | Recommendation and basis |
|---|---:|---|
| Experimental procedures |132|Remove this parent heading if all three following wet-lab sections are removed.|
| In vitro class switching of human B cells |133–135|Remove. These are Nojima cultured B cells and their feeder/cytokine protocol.|
| Cell sorting and short-read library preparation |136–138|Remove if NBC is removed, as supported by the retained figure scope. These paragraphs concern the cultured cells, switched-B-cell sorting and 10x libraries. They do not describe the public RAGE-seq cell-line mixture or the LongBench nuclei.|
| Targeted long-read library preparation |139–140|The original manuscript places this in the NBC experimental block; no remaining NBC plot needs it. Remove with NBC unless the author establishes that these exact preparation steps also generated retained Measles data. If retained for Measles, relabel its dataset scope and verify its chemistry/basecaller details; do not silently treat the NBC protocol as Measles provenance.|

The retained 37-input inventory explicitly excludes NBC:

`/Volumes/rad_data/reviewer_comment_data/three_tool_whitelist_complete_rageseq_immune_20260901/README.md:11–17` states that the 37 scored inputs omit LR-Split-seq, NBC and AIR-SPACE from that particular panel. LR-Split-seq remains separately in Figure 5; NBC has no equivalent retained separate figure.

`sample_inventory.tsv` in the same package identifies the two RAGE-seq inputs as **RAGEseq-cell-line** and **RAGEseq-TNBC-LN**. TNBC denotes the published draining-lymph-node dataset and is not NBC/Nojima culture. The three retained Measles inputs are **Measles-P7**, **Measles-P8-VDJ-enriched**, and **Measles-P8-WTA**. They are distinct entries; the inventory alone does not establish which preparation protocol generated them.

The original manuscript still has old Figure 4F–H claims involving NBC. Those obsolete prose/figure references cannot serve as justification to keep NBC methods while the authoritative new figures omit that analysis.

## Prose and figure references requiring removal or targeted revision

Original and current pre-Methods paragraph indices are unchanged.

| Location | Source/current paragraph | Action |
|---|---:|---|
| Abstract |19|Remove the final claim that the paper demonstrates single-cell and spatial analysis of B-cell isotype and secretion states. Retain the separate high-definition spatial-demultiplexing claim, which is supported by current Figure 1D.|
| Keywords |22|Remove “class switch recombination” if keywords are to describe the retained analyses. “Immune receptor sequencing” remains applicable to RAGE-seq.|
| RAD overview Results paragraph |31|Remove the final clause describing application to the repetitive IGH constant locus, B-cell evolution and antibody secretion, including its old Figure 1C callout. Retain the RAD workflow/benchmark content.|
| LR-Split/generalizability Results paragraph |48|Keep the LR-Split-seq analysis. Remove or retire the NBC-dependent material beginning “RAD was also applied to a long-read sequencing dataset of cultured B cells…” and the old Figure 4F–H claims. These panels are absent from the new Figures 1–7; the new Figure 4 is the 37-input benchmark and omits NBC.|
| Isotype/clonotype Results section |51–54|Remove the heading and all three paragraphs, including old Figure 5A–E callouts, 10,744-clone/620-multi-isotype claims, microenvironment/secretion-state claims, and the three example clone descriptions.|
| Discussion application paragraph |61|Remove the study-specific application claims from “Here, we show that RAD-processed data can be utilized…” through the claim linking clonotype, isotype, isoform and spatial position in an unpaired workflow. The generic opening about flexible downstream processing and concluding accessibility sentence can be retained or rewritten during the Discussion revision. They must not imply that the removed analysis remains in the paper.|
| Data availability |source121/current145|Remove the final NBC-culture-data sentence if NBC is removed. Retain the RAGE-seq and Engblom tonsil access information because their data remain in the benchmarks.|
| Embedded original Figure 5 |current225 artwork;226 blank;227 legend|Remove the artwork and its entire legend. This is current Figure 8, despite its inherited number.|
| New figure source |`extracted/RAD R1 figures and legends.txt:15`, source paragraph18|Remove current Figure 8 and its complete legend from the working figure copy if that copy is being updated. Preserve the untouched source copy.|
| Old original Figure 1C and Figure 4F–H |current212–213;220–222|These embedded figures/legends are inherited old material. They contain the IGH schematic or NBC analyses absent from the new figure set. Flag for replacement by the authoritative updated Figures1–7; do not delete valid current Figure1D or all of current Figure4 by number alone.|

The broad introduction at source/current paragraph24 can retain general biological motivation about BCRs, TCRs and class switching. It does not claim that this paper performed the removed experiment. References10–14 therefore are not automatically removed. Funding, author contributions and acknowledgements should not be altered solely because a figure is dropped.

## Citation removal: original reference numbers

### Exclusively used by removed receptor/clonotype/IGH analyses

| Original ID | Reference | Retained-use assessment |
|---:|---|---|
|28|Gupta et al., Change-O, Bioinformatics31,3356–3358 (2015)|Used in removed clone Results/Methods only. Remove after those paragraphs are removed.|
|38|Nip, RNA-Bloom, Genome Research30,1339–1349 (2020)|Used in removed assembly paragraph only. Remove.|
|39|Ye et al., IgBLAST, NAR41,W34–W40 (2013)|Used in removed annotation paragraph only. Remove.|
|40|IMGT/V-QUEST reference|Used as a citation in removed annotation paragraph only. Remove; merely mentioning IMGT in a retained library protocol, if any, may warrant a separate appropriate citation rather than preserving an unrelated unused entry.|
|41|Yaari et al., SHM models, Frontiers in Immunology4,358 (2013)|Used in removed clonotype paragraph only. Remove.|
|42|Nouri and Kleinstein, spectral clone clustering, Bioinformatics34,i341–i349 (2018)|Used in removed clonotype paragraph only. Remove.|
|43|Nurk et al., T2T complete human genome, Science376,44–53 (2022)|Used for removed T2T-CHM13 IGH coverage only. Retained DE uses GENCODEv44/GRCh38, not this reference. Remove.|

### Remove if the NBC wet-lab block is removed

| Original ID | Reference | Condition |
|---:|---|---|
|44|Su et al., Efficient Culture of Human Naive and Memory B Cells, J Immunology197,4163–4176 (2016)|NBC culture only; remove with the culture section.|
|45|Abdullah et al., CD8 T-cell repertoire, Immunity58,601–615.e9 (2025)|Cited only for probe design in the targeted-library paragraph. Remove if that paragraph is removed. Retain if its exact protocol is established as needed for Measles.|
|46|nanoporetech/minknow_api, ONT (2026)|Already uncited in the revised Methods draft; original citation belonged to NBC targeted-library basecalling. Remove the orphaned entry unless another retained use is established.|

If all NBC wet-lab content is removed, the removal set is **28 and38–46**, leaving36 of the original46 bibliography entries. This count is a cross-check, not an instruction to renumber by a blind textual replacement. Update all surviving citations and bibliography numbers consistently.

### Shared references that must stay

- **13, Singh/RAGE-seq:** retained cell-line mixture and RAGE-seq benchmark datasets.
- **15, minimap2:** retained raw-read receptor assignment and common-read expression alignment.
- **22, Seurat:** retained RAGE-seq reference processing and single-nucleus visualization context.
- **27, Engblom tonsil dataset:** the eight tonsil Visium benchmark libraries remain in Figure4, even though the current manuscript's formal citations mostly occur in the removed application section. Move or add its citation to the retained dataset/benchmark description rather than dropping it.
- **36, TRUST4, and37, GRCh38:** retained RAGE-seq raw-read BCR/TCR classification. These are not interchangeable with the removed IgBLAST/IMGT/T2T steps.
- **10–12:** general immune-receptor and class-switching background in the Introduction; not exclusive to a removed figure claim.

## Review-comment cleanup

Close or remove only comments anchored exclusively to removed Figure8/NBC text: clone clustering settings, secretion-state definition, IGH coverage settings, assembly provenance and NBC donor/ethics/basecaller details if the entire NBC protocol is removed. Preserve unresolved RAGE receptor-reference, LR-Split, UMAP and statistical comments. Preserve a Measles preparation/accession/ethics question if those newly generated datasets remain and have no separately documented source protocol.
