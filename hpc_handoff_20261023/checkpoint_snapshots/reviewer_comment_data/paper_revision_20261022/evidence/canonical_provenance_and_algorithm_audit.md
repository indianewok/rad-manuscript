# Canonical source and algorithm audit — 22 October 2026

This is a read-only evidence audit. No source documents or analysis outputs were changed. Paths below are relative to `/Volumes/rad_data/reviewer_comment_data` unless stated otherwise. The named September scratch-preservation folders contain durable copies of their original scratch hierarchies; old absolute paths in their scripts are provenance, not current mounted-drive paths.

## Current result authorities

| Topic | Canonical evidence | Important boundary |
|---|---|---|
| Consolidated native whitelist benchmark | `master_native_comparison_20260811/tables/master_native_comparison_long.csv`, `README.md`, `provenance/dataset_manifest.tsv` | 36 physical native inputs, 108 tool rows; barcode metrics only; does not supersede read/biology analyses. |
| Complete 37-scored-input whitelist handoff | `three_tool_whitelist_complete_rageseq_immune_20260901/README.md`, `complete_three_tool_metrics.tsv`, `sample_inventory.tsv` | Supersedes Aug31 RAGEseq denominator; 37 scored entries plus inventory-only Visium HD. ScMixology2 reconstruction stays separate from native matched statistics. |
| RAGEseq TNBC lymph-node positive reference | Same Sep1 README and `wl_scan/20260730_rageseq_ERR3268990_tnbc_lymphnode_four_tool/analysis/barcode_level_annotations.tsv` | 5,978 annotated T/B/T-B doublets (4,255/1,637/86); 10,433 deposited barcodes is not the positive denominator. Outside-proxy calls are operational false positives, not established biological negatives. |
| Current resource benchmark | `scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/` | Check this before using Aug19 timing package. SN-ONT and SC-PB inputs; source version table in `provenance/software_and_resources.tsv`. |
| Latest synthetic quality sweeps | `scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913/`, `sctagger_nanopore2023_unadjusted_20260913/`, `sctagger_prism_nanopore2023_20260913/` | Must match actual figure conditions; August flat-Q20 and earlier sweeps are distinct, not all superseded. |
| LongBench revised RAD results | `scratch_preservation_20260921/files/longbench_rad_4acbe00_raw_prism_20260827/`, `SN_ONT_RAD_4acbe00_full_matrix_rebuild_20260828/`, and nearby Aug28 DEG packages | Earlier August source tables may describe different RAD records or matrix contract. |
| Tilgner biology | `tilgner_figure_consolidation_20260813/README.md`, `GENEALOGY.tsv`, `SOURCE_MANIFEST.tsv`; `tilgner_rad_umi12_hybrid_20260806/`; `tilgner_m1_seurat_reference_mapping_20260806/` | Final RAD uses UMI12. m1 is one donor/cDNA library and three technical runs. Ten technical runs arise from six donors. |
| TDLN receptor result | `scratch_preservation_20260921/files/tdln_direct_mixcr_20260914/` | Current direct MiXCR. IRA, Canu assemblies, and partial IgBLAST were retired; their historical readmes cannot establish current Methods. |
| LR-Split and HD | `scratch_preservation_20260921/files/rad-spliso-audit-20260905-LtmzYW/`, `rad_spl_hd_benchmark_20260907.lx7i5Q/`, `spl_stereo_gtime_20260908.LZsqCJ/` | Candidate matching required; these are newer than Aug4 FLAMES compatibility folders. |

## Authority and preservation conflicts

`RAD_DISCRETE_RESULTS_INVENTORY_20260801.md` and `LongBench_comps/README.md` are historical snapshots and contain then-pending work subsequently completed. `reviewer_response_20260804/README.md` is also an earlier consolidation, not the final status of every analysis.

`current_material_cleanup_20260921/README.md`, `retirement_evidence.json`, and `scratch_preservation_20260921/README.md` establish the current retained branches. The September preservation retains 17,214 regular payload files (1.067 TB apparent). Raw demultiplexed FASTQs were deliberately excluded where regenerable; this is not proof those inputs are absent everywhere.

Tilgner RAD UMI10 matrices, their 24,193,273 molecule total, and 97.650% agreement are superseded. Current UMI12 values are 28,744,551 exact cell-gene-UMI tuples and 97.7028% same-barcode agreement for 31,235,094 common gene-assigned reads. `081126_Figure_7` uses an older RAD assigned-read contract (72,252,267 reads), so it cannot silently serve as the final UMI12 matrix comparison. `tilgner_prism_graphing_20260810` is a presentation catalog, not primary authority.

## Software version evidence

- Resource benchmark: `scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/provenance/software_and_resources.tsv` records RAD 1.0.2 commit `4acbe004ba11b150d6832395452632f367a6e6c1`, SHA256 `01ae4700f329593487e1b0a3528da009d7e47c82bf213a5f53ba98acad6fda0e`; BLAZE 2.5.0 commit `11994f9c12a6664dfe1679576aaca19b6bfd35c1`; Flexiplex 1.02.6 commit `d84c8ae4f3865052f2b5ecec816949b94682f302`. The RAD binary is preserved in `scratch_preservation_20260921/files/longbench_rad_4acbe00_raw_prism_20260827/tools/rad_4acbe00`.
- Later production source: `scratch_preservation_20260921/files/rad_publish_20260907.f20d1w/staged_source/`. `rad_prior_release_20260907.1Vnvhk/provenance.json` identifies current commit `cb6991705ac0e9c93a108fd439aa0357834cc701` and current binary SHA256 `bc72a2bc865db696234dd3e79e33feeec1ac48844bd0d7777bd013714d54b2ad`; preceding release `24d5ce47e172222c96cd7dd19e94758d32aa5009`. Version string remains 1.0.2, hence version number alone is inadequate. Compiler GCC8.5.0; CMake3.26.5; -O3/-DNDEBUG build evidence in preserved reports.
- `software_pins_20260810/README.md` preserves BLAZE 2.5.0 and 2.6.0a0 replay algorithms and pristine/diagnostic Flexiplex1.02.6. Diagnostic Flexiplex adds RawCellBarcode reporting. Confirm whether a plotted run used pristine or audit build.
- LongBench Flexiplex1.01 quantitative outputs explicitly superseded by1.02.6. Retained old commands are failure/provenance records.

## Algorithm audit against staged cb699170 source

Source root for line numbers: `scratch_preservation_20260921/files/rad_publish_20260907.f20d1w/staged_source/`.

1. Manuscript para75: Edlib HW is infix/semi-global, not 'half-wave (local)'. `include/rad/sigstring.hpp:408-416` selects HW/LOC. Striped Smith-Waterman is the fallback. Preserve existing Edlib and SSW citations.
2. Para79: `int64_seq` stores a vector of64-bit chunks,32 bases per chunk (`barcode_correction.hpp:103-153`), not a universally32-base-limited sequence. The seed implementation itself is single-chunk (<=32bp), so avoid broad longer-barcode claims.
3. Paras79-80: pre-expansion is not the active load path in this source. `read_layout.hpp:1590-1604` builds seeds only when true set>10,000; the `generate_mismatch_barcodes` call is commented out. Do not claim variants are prepopulated for10–30K lists. Entry storage and cached aliases exist independently.
4. Para83: global seed construction skips catalogs>10,000 (`barcode_correction.hpp:2078-2096`). The seed query is an optimization only for true set>10,000 (`sigstring.hpp:1184-1226`) with ED2 then exhaustive fallback. Do not claim all ED1 Levenshtein matches must share fixed-coordinate partitions: indels shift partitions, and the code's own informal comment is insufficient mathematical justification.
5. Para84: `resolve_multiple_hits_simple` chooses a unique raw-supported candidate at the lowest viable distance; multiple candidates at that distance are rejected (`sigstring.hpp:739-778`). Exhaustive search also rejects nonunique minimum-distance hits. There is no general higher-read-count tiebreaker.
6. Paras84–85: raw support is not an unconditional prerequisite. The gate allows total=0; with fewer than2 raw hits it grants a finite initial allowance before rejecting at total>=5 (defensive) or>=10 (offensive). With total>=10 and raw>=2, prospective corrected fraction `(corrected+1)/(total+1)` must be<=0.8 (`sigstring.hpp:668-726`). A blocked target can recover at2 raw observations. This is a running-state filter; it does not prove every accepted correction has prior direct support.
7. Para83: low-complexity/homopolymer tests are conditional on a nonempty static-derived filter set; exact trusted barcode identity can override static-kmer collision (`sigstring.hpp:1280-1317`). The blacklist loader enumerates ED2 variants but inserts them only if they are already present (`read_layout.hpp:1613-1622`); do not assert effective complete ED2 blacklist expansion. Use 'static-element-derived k-mer blacklist' pending author review.
8. Para89 default adapter error is0.3 in staged CLI, not0.1. Dataset commands may explicitly use0.1. Demux uncalibrated fallback is max(1,ceil(0.3*adapter_length)) (`adapter_thresholds.hpp:8-22`). Distinguish scan defaults from measured settings.
9. Para88 omits important current adaptive/hazard rules and incorrectly says posterior50% boundary can override a stable saddle. In `whitelist_generator.hpp:3577-3587` it remains diagnostic when a saddle exists. Default selection is high-specificity final list; above-floor is optional.
10. Para76 describes only F/R duplets. Later staged source also groups complete repeated-orientation molecules from already-computed static locations. `rad_concat_impl_20260907.SLGMky/implementation_report.md` describes candidate07, guard conditions, child naming, and one-thread versus multithread boundaries. It is reuse-only, not exhaustive damaged-repeat recovery. Confirm final paper software freeze before attributing this to older benchmark binaries.

## Whitelist algorithm specifics (for Methods rewrite)

`whitelist_generator.hpp:3042-3087`: for count c_i, x_i=ln(1+10^6*c_i/N), where N is total extracted candidates (not only catalog-matched counts). Optional catalog restriction determines analyzed barcode identities. ZT-Poisson uses mean positive raw count as lambda and its conditional positive-count CDF; do not call this an optimized maximum-likelihood fit.

`1797-1904,2748-2868`: Gaussian KDE uses512 grid points and Silverman bandwidth0.9*min(SD,IQR/1.34)*n^(-1/5), positive fallback bandwidth0.1. Peaks require20% global density and weaker peaks within0.5 log units are suppressed. The valley between two tallest retained peaks is widened to its left plateau boundary. No saddle ->95th-percentile positive-count Poisson fallback.

`1991-2007,2174-2379`: adjusted upper-tail hazard H(x)=(1-exp(-x))*f(x)/S(x), where each distinct barcode contributes once (count-level multiplicity is unique barcodes, not read depth). Search x>=1; candidates need>=50 surviving barcodes and>=5% local prominence. Bandwidth-aware grid has at least512 points and12 intervals/bandwidth.

`2459-2705,2938-3006`: provisional floor2 may be lowered to an observed score supported by minima at0.8h,h,1.25h, spread<=0.5h,>=50 barcodes on the lower side and>=50 additional retained barcodes, with gain>=max(50,ceil(1% of old above-floor set)). Expanded distribution must satisfy hazard<left peak<saddle<right peak and every rescued barcode must meet the95th-percentile Poisson rule.

`3274-3490`: a separate whole-catalog hazard review can replace the preliminary gate with an eligible pre-gate minimum. Below-floor candidates must match the stable feature or lie within0.5 bandwidth of the floor. If expanding an existing stable saddle, the finite-catalog guard requires (K_h-K_0)/(M-K_0)<=(M-n_positive)/M. Above-gate minima are diagnostic only.

`2725-2745,3608-3687`: single interior mode guard requires peak>=floor+2h and Poisson cutoff within2h to the right of that peak. Without hazard ownership, retain all above-floor if low side<=10%, both sides have>=5 barcodes and ranges<=1, or full range<=2; for10–20% low side, rescue up to10% of total above-floor barcodes ranked by count. An accepted whole-catalog hazard owns final cutoff. `3493-3587`: posterior50% boundary can refine only no-saddle fallback.

`rad_catalog_normalization_cohort_20260907.NPaLq6/report.md` is a rejected experiment: substituting catalog size for CPM scaling was NOT adopted. Do not add it as production method.

## Author clarification needed

Which exact RAD commit should Algorithm Overview describe: measured4acbe00, later published/staged cb699170, or a subsequent frozen release? Can bench-specific versions remain explicit in a software/provenance table? No single version describes all cohorts. If current algorithm is desired, the existing absolute raw-support, variant-preexpansion, seed-guarantee, ED2 blacklist and tie-breaking descriptions require factual correction, not stylistic editing.


## Supplemental 4acbe00 comparison (completed)

The full4acbe00 source tree was not identified in the preserved file index. Its executable and two exact source files were recovered without using Desktop source:

- `scratch_preservation_20260921/files/sc_ont_rad_filter_audit_20260827/source/` retains instrumented sigstring.hpp, main.cpp, and the diagnostic patch. Its run script records source commit4acbe004ba11b150d6832395452632f367a6e6c1.
- Reversing that patch on copies recovers sigstring.hpp and main.cpp. Their Git object hashes match the original patch indices exactly: `791a01c84fdd5f2d80e975c7e1dbef370d1424c8` and `317cf2bb23c92241afeee6d9b77ea55d5117710e`.
- Recovered files and manifest: `paper_revision_20261022/evidence/recovered_4acbe00_source/`. The entire barcode-correction block is byte-identical to stagedcb699170 (see function_comparison.json). Thus the corrected descriptions of ties, finite initial correction allowance, and seed/exhaustive routing apply to4acbe00, not just newer code.
- The entire statistical whitelist-selection block in exact archived24d5ce47 source is byte-identical to stagedcb699170. The4acbe00 binary contains the same named adaptive/hazard/finite-population/single-mode/budget features; its logs directly show those rules executing. This establishes feature presence, but is not a claim of exact full4acbe00 header identity.

Definitive run evidence is in `scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543/raw/{SC_PB,SN_ONT}/threads_16/rep_1/RAD/whitelist_detection/attempt_001/stdout.log`:

- SC-PB: initial floor2, KDE saddle3.13906; finite-catalog hazard expansion from4,947 to5,350 selected barcodes accepted; final adjusted-hazard threshold2.48941.
- SN-ONT: initial floor2; KDE saddle2.41025; no eligible pre-gate hazard; final rule af_kde_saddle.

Consequently, hazard-based selection must be described for the4acbe00 timing runs. It should not be portrayed as a September-only addition.

Repeated same-orientation concatemer grouping is different: `scratch_preservation_20260921/files/rad_concat_history_20260907.RlCszv/README.md` reports that4acbe00 recovered only moleculeA fromF/F/F andA/B fromF/R/F; no complete arbitrary-repeat splitter existed in that version. The later candidate07 behavior cannot be attributed to those older runs.
