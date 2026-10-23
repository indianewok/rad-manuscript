# Manuscript v2 removal and verification proof

The working manuscript is `/Users/cmv/Desktop/RAD_paper_revision_2026-10-22/working/Manuscript_methods_working_2026-10-22_v2.docx`. It is an annotated Methods draft, not a submission-ready replacement of the complete paper. Version 1 and the source manuscript remain unchanged.

## Authorized changes

- Removed the analyses represented by current Figure 8: receptor assembly/gene annotation, clonotype/isotype analysis, and IGH coverage/spatial clonotype maps.
- Removed NBC/Nojima culture, cell sorting, short-read library preparation, and the targeted long-read protocol whose use for other retained samples was unverified. A comment requests the actual Measles preparation, ethics, replicate, and accession information.
- Removed the corresponding Results subsection, NBC-specific tail of the generalization Results, abstract application claim, overview IGH clause, Figure 8 Discussion claims, NBC availability sentence, class-switch keyword, and original embedded Figure 5 image/legend. The generic final downstream-utility statement remains.
- Retained the tonsil libraries in the 37-input barcode-discovery benchmark and moved the Engblom citation to that inventory paragraph.
- Updated Figure 2 Methods to the unadjusted Badread nanopore2023 quality condition and the newly completed 22 October 2026 cached-table BLAZE assignment replay. Native Phred support is described as 1–90, without claiming generation was clipped. Existing quality-independent RAD/Flexiplex outputs remain explicitly identified. Correction-only pie charts compare corrected-correct with corrected-incorrect reads. Six exclusive input categories are stored separately, with native-incorrect counts excluded from correction totals. The text states the distinct all-selected-target and selected-true-target denominators and the separate Flexiplex native-read reference-list increment.
- Added the replay validation and provenance details as comments, including candidate ordering and the pending native Prism visual/statistical-annotation check.

## Citation and package integrity

Removed original references 28 and 38–46. All remaining references were renumbered and the bibliography reordered by first citation appearance, including manually formatted superscript clusters. The verified first-appearance sequence is 1–36.

Original references 1–26 retain their numbers. Mapping for the rest: 29→27; 30→28; 31→29; 32→30; 33→31; 34→32; 35→33; 27 (Engblom)→34; 36→35; 37→36. Shared references 13, 15, and 22 remain. The copied Engblom field has a new citation-instance ID with identical citation-item IDs, URIs, and item data.

There are 41 retained/new Zotero citation fields and 36 bibliography entries. Retained field metadata is unchanged except for `plainCitation` and `formattedCitation`. Visible labels and both metadata labels agree. Zotero bibliography instruction and field begin/end are preserved. No Zotero item IDs were renumbered.

All tables, styles, settings, font table, numbering, and five packaged media files are byte-identical to v1. One drawing was removed from the body; its unused media payload remains in the package. There are 145 unaffected paragraphs with identical XML. Four additional paragraph changes are verified to contain only numeric-citation changes. The new scope and evidence comments have complete start/end/reference anchors; 21 comments remain.

## Rendered inspection

All 30 pages were visually inspected. After the final correction-only scoring change, pages 15–30 were reopened and inspected; pages 1–14 were verified pixel-identical to their already inspected render. No clipped text, missing glyphs, overlap, broken tables, or orphan headings remain. The Code Availability heading was kept with its paragraph during QA. The actual output preserves the source EMF artwork; the QA-only copy substitutes PNG derivatives of the figures' embedded PDFs because the bundled renderer does not display those EMFs. The output and QA-copy `word/document.xml` are byte-identical.

The original non-Figure-8 embedded figures and their legends still show old artwork and numbering, as explicitly flagged in a Word comment. They must be replaced with updated Figures 1–7 and remaining Results/Discussion callouts reconciled. Old Figure 1C and Figure 4F–H still contain obsolete source content; the current task did not replace these other figures. The retained source Myers reference (now 29) lacks journal/year details. Pending scientific decisions and source gaps are recorded in the comments; no new statistical test choice was assumed.

## Files and hashes

- Source SHA256: `3f5f1f5930967dbb22f6539b1b7f9a3fbafe4d31cadec5b38fae1586a18742c8`
- Version 1 SHA256: `7fe16e783011b8f073cd542bc0dbe54f3696bba35ae8dd527c219210b1ad4482`
- Version 2 SHA256: `67dca207d0e07c42e3dc86f705ce4386dfdef6b1087ff413f8740fd6a42c5254`
- Builder: `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/scripts/build_methods_v2.py`
- Editable Methods sources: `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/scripts/methods_core_v2.txt` and `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/scripts/methods_biology_v2.txt`
- Machine-readable structural proof, exact paragraph removals/changes, and citation mapping: `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/qa/structure_checks_v2.json`
- Rendered QA PDF: `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/qa/revised_manuscript_v2/Manuscript_render_surrogate_v2.pdf`
- Figure 2 replay provenance: `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/prism/blaze2023_assignment_replay/provenance.json`

No source manuscript, v1 manuscript, figure-source document, rebuttal letter, raw data, or source analysis output was modified by this v2 builder.
