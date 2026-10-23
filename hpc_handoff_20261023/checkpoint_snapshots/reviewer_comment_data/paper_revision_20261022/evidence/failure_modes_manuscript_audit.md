# Failure-mode definitions and RAD safeguards

Audit date: 22 October 2026. This audit compares the original manuscript, the current v2 text, the new Figure 3 artwork and legend, the rebuttal and comments, the retained LongBench classification scripts, and the preserved RAD source. No manuscript was edited by this agent.

## Decision and principal finding

The user chose the measured barcode categories. Preserve the analysis-script numbering: **failure mode 1 is a catalog-valid source outside the Cell Ranger filtered reference changed to a tool-selected target; failure mode 2 is a Cell Ranger source changed to another Cell Ranger barcode selected by the tool.** Revise the diagram to these definitions. Neither category establishes the biological source of a molecule. Do not describe mode 1 as a demonstrated missed cell or mode 2 as demonstrated ambient RNA.

The previous Figure 3D artwork used incompatible biological descriptions: mode 1, “improperly correcting undetected, cell-associated barcodes into ‘true’ whitelisted cells”; mode 2, “improperly correcting ambient mRNA and empty droplet barcodes into ‘true’ whitelisted cells.” These were also conceptually reversed relative to the measured classes. Merely swapping those biological labels would still be unsupported.

Artwork inspected directly: `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/extracted/figure_images/paragraph_4_image3.png`.

## Exact operational definitions and source lineage

Let C be the complete chemistry catalog, R the matched Cell Ranger filtered reference, S the tool-selected target list, a the exact extracted source sequence, and b the final assigned sequence. Source-membership classes require an available source sequence and a != b.

| Display label | Measured condition | Retained field |
|---|---|---|
| Corrected off-list | a outside C; b in S | `noncatalog_to_selected` |
| Failure mode 1 | a in C but outside R; b in S | `catalog_noncell_to_selected_A` |
| Failure mode 2 | a in R; b in R and S; a != b | `cellranger_to_different_cellranger_K` |

Authoritative mapping: `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_rad_4acbe00_raw_prism_20260827/scripts/update_raw_longbench_prism.py`, lines 181–200. The script explicitly pairs rows `Corrected from non-whitelist`, `Failure Mode 1`, and `Failure Mode 2` with the three fields above in that order.

Classifier: the same package's `scripts/analyze_correction_events.py`, lines 909–945. A source equal to its target is `native_exact` and is not included in these correction classes. Within source != target, the Cell Ranger branch precedes catalog membership. It requires a selected target; the stricter Cell Ranger-to-Cell Ranger flag additionally requires target membership in R. The script's opening documentation, lines 4–12, explicitly says that only exact observed sources support membership claims and that the catalog-valid, non-Cell-Ranger tier is operational, without a donor or cell-line assignment.

The unit is a unique original-read–target-barcode pair. Repeated records for the same pair collapse. One original read with two targets can contribute to both. These are audit categories, not an exhaustive partition of input reads. Per-target percentages divide by the tool's total unique read–target assignments to that target; zero denominators remain undefined. The Prism update script lines 217–257 directly implement that denominator. Its other fraction-of-total tables at lines 204–214 divide by the sum of three categories and are a different analysis; they must not be silently substituted for Figure 3G.

This update uses RAD revision `4acbe004ba11b150d6832395452632f367a6e6c1`. The barcode-correction namespace in the recovered 4acbe00 source and in `github_audit/main_cb699170/include/rad/sigstring.hpp` was re-compared for this audit: 41,652 characters, byte-identical, SHA256 `5216c5731fc3a28e15e4ad82c6afebce6a8ec278a32e63629eec13864eeccbd9`. The reconstruction provenance is in `evidence/recovered_4acbe00_source/RECOVERY.json`. This comparison verifies the correction namespace; it does not prove every other current source component is identical to the benchmark build.

## Manuscript and rebuttal passages

1. The original manuscript contains no numbered failure-mode definitions. Original paragraph 31 (Method Overview; `extracted/Manuscript.txt:39`) says that RAD accepts a barcode “only when independently observed in raw reads.” The same sentence remains in v2 Results (`extracted/revised_manuscript_v2.txt:32`). This is too absolute: the implemented count gate allows initial corrections before direct observations.
2. Original Methods paragraph 84 (`Manuscript.txt:125`) says ties are broken by “higher empirical read support.” The v2 Methods correctly replaces this with ambiguity rejection and unique-candidate rules (`revised_manuscript_v2.txt:70`). Do not restore abundance-based tie breaking.
3. Original Methods paragraph 85 (`Manuscript.txt:127`) again says a target is accepted “only if it has been independently observed in raw reads” and claims this prevents a rare valid barcode from being reassigned to an abundant neighbor. The raw-support claim is not unconditional, and the target count gate is not the direct mechanism that protects an exact catalog source from reassignment.
4. V2 Methods, “Barcode representation and correction,” lines 68–71, correctly describes filters, candidate ambiguity, the initial allowance, and running-count thresholds. However, “Exact barcode identities are considered before fuzzy matching” does not fully explain the protection: exact identities in the broader catalog are considered before the restricted selected list; catalog-only identities are withheld from selected-cell output rather than converted merely to fit that list.
5. V2 Methods, “Audit of barcode correction in LongBench,” lines 91–94 (class definitions at line 93), already gives the three operational categories and explicitly states: “They do not independently establish the biological origin of a molecule or prove that a noncatalog correction recovered its true cell.” The missing change is to bind the second and third classes explicitly to **failure mode 1** and **failure mode 2**.
6. New-figure document paragraph 5 (`extracted/RAD R1 figures and legends.txt:5`) refers only to “corrected off-list or the two failure modes”; it does not define the numbered modes. This caption should be replaced in the D–G portion as below.
7. The rebuttal contains no numbered definitions or documented biological validation of the modes. Its comments include id96, “update and point out new figure of error correction algo”; id104, “error + single nuclei data GEX”; and id146, “error algo +++”. These are requests for revision, not evidence. Reviewer 1's point at original rebuttal paragraphs 21–23 challenges unsupported error/UMI-inflation claims; the proposed response still speculates. The new reply should point to the measured classes and the implemented safeguards, without claiming ambient detection.

## What the code supports

The current source root is `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/github_audit/main_cb699170/`.

- `include/rad/sigstring.hpp:1255–1280`: reverse-oriented barcode sequences are normalized before barcode correction.
- `sigstring.hpp:1319–1382`: global-catalog lookup occurs before the sample-specific lookup and fuzzy correction. A directly matching identity can pass even if its running count gate fails. The global table is an identity set; the sample-specific table supports mutation associations. This is the direct protection against forcing a correctly extracted catalog barcode into a restricted selected set.
- `sigstring.hpp:3431–3463`: a catalog-only barcode is marked unwritable when a sample-specific set exists. It is not converted into a selected-cell barcode simply because it lies outside that set. If no sample-specific set exists, global-catalog outputs can be written.
- `sigstring.hpp:4881–4884,4948–4950,5042–5045,5105–5107`: unwritable barcode components are omitted from selected-cell output. A non-bulk record with no remaining barcode is omitted. A permissive multi-component record may retain other valid components; do not generalize this to unconditional discard of every read.
- `sigstring.hpp:668–726`: running target counts limit correction-dominated accumulation. Total zero passes. With fewer than two raw observations, the nominal blocking threshold is five total observations in defensive mode or ten in offensive mode. Two raw observations can restore a blocked target. With at least ten total and two raw observations, `(corrected + 1)/(total + 1)` must be <= 0.80. Atomic reads, checks, and increments are separate, so these are acceptance rules rather than a hard concurrent global cap.
- `sigstring.hpp:746–776,1005–1077`: candidate ambiguity is rejected rather than resolved by choosing the most abundant target. Multi-candidate lookup uses directly observed candidates at the first qualifying distance. The exact details differ from the exhaustive route; do not claim every corrected target must have a prior raw observation.

Limits: catalog preservation requires the relevant catalog and a usable correctly oriented extracted sequence. A sequencing error can itself produce another valid catalog sequence, and catalog membership cannot establish a cell of origin. The global reverse-complement-only branch tests both orientations but retrieves the forward key; avoid claiming that every RC-only catalog hit is guaranteed protected. Current Methods' statement that accepted runtime assignments are cached also needs review: the other code audit identified precomputed aliases, not a demonstrated general runtime correction cache. See `evidence/github_main_methods_audit.md` for the independent code review.

## Proposed Methods addition

Place after the exact-identity sentence in “Barcode representation and correction,” or replace that sentence with this passage:

> When a full chemistry catalog and a sample-specific barcode set are supplied, RAD checks the correctly oriented extracted barcode against the catalog before fuzzy correction toward the sample-specific set. An exact catalog barcode outside the selected set retains its sequence and is omitted from selected-cell barcode output. This rule protects catalog identities from reassignment caused only by their absence from the selected set. Sequences without an accepted exact identity remain eligible for correction. Ambiguity rejection and the running target-count checks described below limit these corrections. These checks use sequence identity and observed counts; they do not identify ambient RNA or establish the cellular origin of a read.

The existing detailed gate paragraph should remain, with the limitations above. Do not claim that the gates eliminate either biological failure mechanism.

Replace the numbered-class paragraph in “Audit of barcode correction in LongBench” with:

> Three source-to-target classes were tabulated from exact extracted sequences. Corrected off-list assignments changed a source outside the complete chemistry catalog to a tool-selected target. Failure mode 1 changed a catalog-valid source outside the Cell Ranger filtered set to a tool-selected target. Failure mode 2 changed a source in the Cell Ranger filtered set to a different barcode in that set that was also selected by the tool. These classes describe observed barcode changes and reference-set membership. They do not establish cellular origin or prove that a correction recovered the true cell.

## Figure 3 caption replacement

Retain the existing title and A–C portion. Replace only D–G:

> D–G. Barcode correction was classified by exact observed source-barcode membership (D). Corrected off-list: a source outside the complete chemistry catalog was changed to a tool-selected target. Failure mode 1: a catalog-valid source outside the Cell Ranger filtered set was changed to a tool-selected target. Failure mode 2: a source in the Cell Ranger filtered set was changed to a different barcode in that set that was also selected by the tool. Counts used unique original-read–target-barcode pairs. Total counts (E), counts per target barcode (F), and class percentages among all such pairs assigned by the same tool to each target (G) were compared across the four LongBench inputs. These classes describe observed barcode changes and reference-set membership; they do not establish cellular origin or correction accuracy.

Figure 3D should show the same operational mapping. Do not swap the numerical data columns to preserve the obsolete biological schematic. The parent agent is revising panel D from the recovered vector source. The figure-document copy will preserve all other figures and caption content.
