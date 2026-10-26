# Current GitHub main versus working Methods

Audited source: `github_audit/main_cb699170`, exact main commit `cb6991705ac0e9c93a108fd439aa0357834cc701`. Audited manuscript: `extracted/revised_manuscript_v2.txt`, especially lines 67–76 and 92–94. This is a read-only source audit. No manuscript or code changes were made. The developer branch is outside this report. Code paths below are relative to the audited source root; local manuscript lines refer to the extracted text.

## Decision

The working Methods largely match the implemented correction and discovery rules. The most important missing mechanism is the distinction between recognizing an exact catalog barcode and emitting a selected-cell assignment. The most important overstatement is the claim that accepted assignments are cached. Running-count gates must not be presented as strict per-target correction limits or evidence of a molecule's biological source. The measured failure-mode numbering is confirmed below and must replace the biological interpretation in the old artwork.

## Measured failure modes and protections

The preserved plotting script `scratch_preservation_20260921/files/longbench_rad_4acbe00_raw_prism_20260827/scripts/update_raw_longbench_prism.py:183–202` explicitly maps **Failure Mode 1** to `catalog_noncell_to_selected_A` and **Failure Mode 2** to `cellranger_to_different_cellranger_K`. The classifier in the same package, `scripts/analyze_correction_events.py:914–946`, first requires source ≠ target. It assigns the categories as follows:

| Label | Measured source → target relation | Supported interpretation |
|---|---|---|
| Failure mode 1 | Exact extracted source belongs to the chemistry catalog but not the Cell Ranger filtered set; target belongs to the tool's selected set | Change from a catalog-valid, reference-negative source into a selected target. It does not prove ambient RNA, an empty droplet, or an undetected cell. |
| Failure mode 2 | Exact extracted source and a different target both belong to the Cell Ranger filtered set; target also belongs to the tool's selected set | Change between two different short-read-supported barcode identities. It does not by itself establish the molecule's true originating cell. |
| Other reported class | Source is outside the chemistry catalog; target is selected | Noncatalog correction. Membership alone does not prove that the correction recovered the true cell. |

Both measured failures are reduced by the same **identity-first mechanism**, provided the exact source sequence is represented and correctly oriented. When a source barcode is selected, its canonical identity is retained. When the source is only in the broader catalog, it is recognized as that catalog identity and is not emitted as a selected-cell barcode when a nonempty selected set exists. A count-based target gate is a secondary safeguard; it is not an ambient-RNA detector.

### Verified identity and output path

1. `include/rad/barcode_correction.hpp:1955–1958` declares `true_bcs` as a multimap and `global_bcs` as a flat set. Global entries cannot carry query→different-target aliases: `return_putative_correct_bcs` returns exact matching keys at lines 937–958; insertion ignores an observed alias and stores the canonical barcode itself at 967–982.
2. With two unequal-size lists, the smaller becomes the selected set and the larger becomes the global set after selected identities are removed (`barcode_correction.hpp:2393–2418`). With one list, size ≥100,000 is classified as global; smaller lists are classified as selected (2366–2391). Equal-size lists are merged into selected (2420–2437). Thus the semantic roles depend on loading, not just the human names assigned to files.
3. Mutation preparation inserts query aliases into the selected multimap only when their sequence is absent from both existing sets (`barcode_correction.hpp:2175–2205`). Exact selected and catalog identities are protected from those aliases. This is prepared lookup data, not a cache of successful runtime corrections.
4. After normalizing reverse-oriented extracted sequences (`include/rad/sigstring.hpp:1265–1271`), exact catalog lookup precedes selected-set lookup in **both** modes (1320–1343 and 1399–1430). Identity equality bypasses count-gate rejection in these branches. The preliminary static-sequence/complexity filters still run first (1280–1317).
5. `apply_barcode_correction` sets `write = found_in_true || (true_wl_empty && found_in_global)` (`sigstring.hpp:3440–3471`). The FASTQ serializers skip a barcode with `write=false` (4881–4884 and 5042–5045). If no barcode remains, a non-bulk record is omitted (4948–4950 and 5105–5107). Therefore this suppresses a selected-cell assignment, not merely a cosmetic tag. With multiple barcode components, remaining permitted components can still be emitted in permissive mode; strict mode requires every component to pass (3293–3389).

**Scope limit:** the global branch tests membership of `bc` or its reverse complement at `sigstring.hpp:1321`, but obtains candidates using `bc` alone at 1322. An RC-only catalog hit therefore does not have the same identity-retention guarantee. Ordinary reverse reads are normalized first, but incorrectly oriented/custom inputs must not be covered by a universal claim. With no selected set, recognized global identities are writable. With no catalog, catalog-only identity protection is unavailable. No sequence rule can infer a biological origin when extraction/sequencing errors have already changed the observed sequence into another legitimate barcode.

## Concrete amendments to current Methods

### 1. Replace the last two sentences at manuscript line 67

Current: “Barcode records retain counters for direct observations, corrected observations, and total observations. Lookup structures associate observed sequences with candidate barcode records and cache accepted assignments.”

Replacement:

> Barcode records retain running counters for direct and corrected assignments. These counters are updated for passing barcode elements after read classification. Lookup structures associate canonical barcodes and precomputed mutation variants with candidate records. The broader chemistry catalog is stored as an exact-identity set.

Evidence: count update is after classification, `sigstring.hpp:2567–2601`; `raw` versus `corrected` depends on equality to the original extracted sequence or its reverse complement, 3465–3470. Counter atomics are declared and accessed in `barcode_correction.hpp:30–97`. Mutation aliases are prepared at 2175–2205. No insertion of an accepted observed-query→target correction occurs in `correct_barcode`, `process_single_barcode`, or `apply_barcode_correction` (`sigstring.hpp:1255–1564`, 3403–3477). “Cache accepted assignments” should therefore be removed.

### 2. Add this paragraph after manuscript line 68

> When a full chemistry catalog and a sample-specific set are supplied, a correctly oriented exact catalog barcode is checked before fuzzy matching toward the sample-specific set. A barcode present in the selected set retains its canonical identity. A barcode present only in the broader catalog also retains its identity, but it is not written as a selected-cell barcode when a nonempty selected set is present. This prevents that identity path from redirecting an observed catalog barcode to a neighboring selected barcode. It does not identify the biological source of the molecule.

Use “correctly oriented” and “that identity path”; do not replace these with a universal guarantee. Evidence and loader caveats are given above. The statement is also conditional on passing the sequence filters already described in line 68. The known RC-only retrieval discrepancy should be retained as an implementation audit note, not hidden by stronger manuscript wording.

### 3. Retain the distinction between lookup and exhaustive uniqueness; add this sentence after line 70

> Uniqueness is assessed among the candidates examined at each search stage; acceptance from a seed shortlist does not trigger a second exhaustive uniqueness check.

Evidence: multiple lookup hits are sorted by distance, then only candidates with `raw_count > 0` are considered; the first distance with one supported candidate can pass, whereas multiple supported candidates at that distance are rejected (`sigstring.hpp:743–779`). Thus an unsupported nearer candidate can be skipped in favor of a supported more distant candidate, and raw abundance is not used to choose among tied supported candidates. Exhaustive search evaluates all canonical candidates in the selected container and requires one best-distance match (933–939, 1007–1072). For selected sets >10,000, a successful seed result returns immediately; exhaustive fallback runs only after the shortlist fails (1184–1235). The current line 69 already avoids claiming universal indel completeness. Do not describe the whole correction pipeline as a globally unique nearest-neighbor assignment.

### 4. Replace manuscript line 71 with this more precise account

> A running-count check limits correction toward targets with weak direct support. A target with no recorded assignments can pass before it has a direct observation. At a correction check, fewer than two direct observations and a current total of at least five in defensive mode or ten in offensive mode cause the target to be blocked. A blocked target with at least two direct observations can be reset to its direct count. For a target with at least ten total observations and two direct observations, the prospective corrected fraction, calculated as (corrected + 1)/(total + 1), must not exceed 0.80. Exact identity matches can bypass this correction check. These checks use running state and are not strict bounds on the final number or fraction of corrected records. During direct k-mer and mutation-candidate lookup, defensive mode consults the broader catalog before the selected set, whereas offensive mode consults the selected set first. Later seed and exhaustive fallback searches use the selected set. Strict processing of multiple barcode components requires every component to pass.

Evidence: gate implementation `sigstring.hpp:668–726`; identity bypass 1332–1343 and 1418–1430; direct k-mer order 1127–1175; seed/exhaustive selected-only fallback 1184–1235; later mutation order 1512–1549; strict versus permissive policy 3382–3389. Offensive is the CLI default (`src/main.cpp:1492`; help at 46–47).

Implementation qualifications for the audit record:

- The target's total counter is also used as a block sentinel (`total=-1`, 719–724), then can be reset to its raw count (700–705). It is not always an immutable cumulative observation count.
- Two raw observations are the explicit reset condition, but the prose must not claim that this is the **only** way later processing can change the block. Identity calls bypass the rejection and later increment total/raw (2586–2590); for example, a total of −1 can become zero after an identity observation, and the zero-total gate passes at 685–695.
- Counter loads/checks and later increments are separate operations; each individual counter uses relaxed atomics (`barcode_correction.hpp:30–97`). Several concurrent records can pass against the same prior state. No atomic reservation couples the check to the increment. Hence five/ten are check thresholds, not a hard concurrency-safe admission cap, and 0.80 is a prospective check, not a universal final-ratio guarantee.
- Multiple-hit resolution internally calls the offensive gate at 766, followed by the caller's configured-mode check at 873, 1360 or 1447. The final configured gate remains present; avoid describing all internal checks as uniformly mode-specific.

### 5. Replace the classification paragraph at manuscript line 93

> Three source-to-target classes were tabulated. Noncatalog correction comprised an extracted source outside the chemistry catalog assigned to a selected target. Failure mode 1 comprised a catalog-valid source outside the Cell Ranger filtered set assigned to a different selected target. Failure mode 2 comprised a source in the Cell Ranger filtered set assigned to a different target that was also in that set and selected by the tool. These classes describe observed sequence identity and reference-set membership. They do not establish whether a molecule arose from an undetected cell, an empty droplet, or ambient RNA, and they do not establish that a noncatalog correction recovered the true cell.

The current counting-unit paragraph at line 94 should remain: unique original-read–target pairs; same-pair duplicates collapsed; one original read with two targets can contribute to both. The source classifier and plotting mapping cited above support this exact numbering. No change to the numerical analysis is implied.

## Adaptive discovery: mostly consistent, limited reproducibility additions

Lines 73–76 correctly describe catalog-restricted identity counting, normalization by all extracted candidates, KDE/saddle selection, the conditional Poisson fallback, adaptive floor, final hazard review and the diagnostic-only mixture boundary in the presence of a saddle. Independently verified code anchors are:

- Counts, total-extraction denominator and catalog restriction: `include/rad/whitelist_generator.hpp:3029–3087`.
- Silverman bandwidth and peak criteria: 1797–1818 and 1848–1904; primary saddle and Poisson fallback: 3197–3269.
- Hazard definition: `(1-exp(-x))*density/survival`, 2314–2317. Search lower bound 1, at least 50 survivors and prominence 0.05 are default parameters at 2174–2183.
- Adaptive floor snaps to an observed score and preserves count ties (2606–2666), needs at least 50 side-support barcodes and gain at least max(50, ceil(0.01 × old above-floor count)) (2684–2703, defaults in the helper signature). Rescued-band Poisson checks are at 2987–3002.
- Whole-catalog hazard selection and its finite-population guard: 3352–3448. The acceptance formula is `(K_h−K_0)/(M−K_0) ≤ (M−n_positive)/M` (2159–2167). It applies to expansion of an accepted saddle population, not the no-saddle fallback (3394–3402). Missing/invalid catalog size fails open (3442–3448).
- Mixture boundary is diagnostic when a saddle exists (3577–3587). Final non-hazard collapse rules include a ≤10% lower tail, narrow groups, or a narrow total range; the 10–20% tail case can rescue up to 10% of above-floor barcodes (3605–3687).

Suggested short additions, rather than rewriting this already accurate section:

> The adjusted hazard was H(x) = (1 − exp(−x)) f(x)/S(x), where f and S are the density and upper-tail survival function of distinct-barcode scores. Hazard candidates were searched at scores of at least one and required at least 50 surviving barcodes and 5% local prominence.

> For expansion of a saddle-selected set, the finite-catalog guard required (K_h − K_0)/(M − K_0) ≤ (M − n_positive)/M, where K_0 and K_h were the numbers selected by the preliminary and proposed thresholds, M was the catalog size, and n_positive was the number of catalog barcodes observed at least once. This guard was applied only when the catalog-size inputs were valid.

Discovery estimates a set from abundance and sequence identity. It does not independently classify ambient RNA or prove that every selected barcode represents a cell. The output name “high-specificity” is an algorithmic selection label, not a measured guarantee for an unvalidated dataset.

## One related statement outside Methods

The current Results overview at extracted manuscript line 32 still says correction accepts a barcode “only when independently observed in raw reads.” This conflicts with the explicit initial allowance and exact-identity branches. Suggested replacement:

> RAD combines exact catalog identity checks with candidate-uniqueness and running-count filters to limit barcode reassignment.

The original sentence should not remain elsewhere if the corrected Methods explain a finite initial correction allowance.

## Validation scope

This report independently read the pinned main source and the preserved category-assignment scripts. It did not run new simulations, alter code, change benchmark numbers, or edit the manuscript. The algorithm overview should name this exact commit, while each benchmark should retain its own recorded revision (for example 4acbe00) rather than implying every experiment used current main.
