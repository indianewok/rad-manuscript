# RAD barcode processing at commit cb699170

The correction and discovery mechanisms below refer to RAD commit `cb6991705ac0e9c93a108fd439aa0357834cc701`. Source paths and line numbers refer to that commit. Benchmark-specific versions are listed in the [figure guides](../../README.md).

## Exact barcode identity and assignment output

RAD stores selected barcodes in the `true_bcs` multimap and the broader chemistry catalog in the `global_bcs` flat set (`include/rad/barcode_correction.hpp:1955–1958`). Global lookup returns exact keys; insertion stores canonical identities (`937–982`). Precomputed mutation aliases enter the selected multimap only when their sequence is absent from both existing sets (`2175–2205`).

List loading determines the role of each supplied set. With two unequal-sized lists, the smaller becomes selected and the larger becomes global after removing selected identities (`2393–2418`). A single list with at least 100,000 entries becomes global; a smaller list becomes selected (`2366–2391`). Equal-sized lists are merged into the selected set (`2420–2437`).

After normalizing reverse-oriented extracted sequences, RAD applies static-sequence and complexity filters, then checks exact catalog identity before selected-set lookup in both correction modes (`include/rad/sigstring.hpp:1265–1343,1399–1430`). Exact identity can bypass the running-count gate. The write rule is:

```text
write = found_in_true || (true_wl_empty && found_in_global)
```

The rule is implemented at `sigstring.hpp:3440–3471`. FASTQ serializers skip barcode elements with `write=false` (`4881–4884,5042–5045`); a non-bulk record with no remaining barcode is omitted (`4948–4950,5105–5107`). Permissive multi-component processing can emit the remaining accepted barcode components; strict processing requires every component to pass (`3293–3389`).

With a nonempty selected set and a correctly oriented catalog identity, this path preserves selected identities and suppresses assignments for catalog-only identities. It therefore addresses both measured correction modes: reassignment between two different reference-supported identities (Failure Mode 1), and reassignment from a catalog-valid source outside the matched filtered reference into a selected target (Failure Mode 2). The classification script requires an observed source-to-target change; the [Figure 3 guide](../../docs/figure_03.md) gives the exact categories and counting units.

### Reverse-complement lookup discrepancy

The global branch tests membership of `bc` or its reverse complement at `sigstring.hpp:1321`, but retrieves candidates using `bc` alone at line 1322. An RC-only catalog hit can therefore fail candidate retrieval. Ordinary reverse reads are normalized before this branch. Catalog-only output is writable when the selected set is empty; catalog-identity protection requires a supplied catalog.

## Candidate lookup and uniqueness

Lookup structures associate canonical barcodes and precomputed mutation variants with candidate records. Accepted runtime query-to-target assignments are not inserted as a correction cache in `correct_barcode`, `process_single_barcode`, or `apply_barcode_correction` (`sigstring.hpp:1255–1564,3403–3477`).

Multiple lookup hits are sorted by distance, and candidates with a positive direct-observation count are considered. The first distance with one supported candidate can pass; multiple supported candidates at that distance are rejected (`743–779`). This can select a supported, more distant candidate after skipping an unsupported nearer one. Raw abundance does not resolve ties among supported candidates.

Exhaustive search evaluates all canonical candidates in its selected container and requires one best-distance match (`933–939,1007–1072`). For selected sets larger than 10,000, an accepted seed-shortlist result returns immediately; exhaustive fallback follows a failed shortlist (`1184–1235`). Uniqueness is consequently evaluated among the candidates examined at the accepting search stage.

Defensive mode consults the broader catalog before the selected set during direct k-mer and mutation lookup. Offensive mode uses the opposite order (`1127–1175,1512–1549`). Later seed and exhaustive fallback searches use the selected set. Offensive mode is the CLI default (`src/main.cpp:1492`).

## Running-count correction gate

Barcode records contain atomic direct and corrected counters (`barcode_correction.hpp:30–97`). Counts are updated for passing barcode elements after read classification (`sigstring.hpp:2567–2601`). Direct status uses equality to the original extracted sequence or its reverse complement (`3465–3470`). The correction gate at `668–726` applies these checks:

| Current state | Gate behavior |
|---|---|
| Total count is zero | The candidate can pass before a direct observation. |
| Fewer than two direct observations and total at least five in defensive mode or ten in offensive mode | The target is blocked by setting its total to −1. |
| Blocked target with at least two direct observations | The total can reset to the direct count. |
| At least ten total and two direct observations | The prospective corrected fraction `(corrected + 1)/(total + 1)` must be at most 0.80. |
| Exact identity match | The identity branches can bypass the correction gate. |

The total counter doubles as a block sentinel (`719–724`) and can reset to the direct count (`700–705`). Identity calls can subsequently increment direct and total counts (`2586–2590`): for example, −1 can become zero, allowing the zero-total gate to pass (`685–695`).

Counter checks and later increments are separate operations using relaxed atomics. Concurrent records can pass against the same prior state. Five, ten, and 0.80 are thresholds evaluated during processing, rather than fixed limits on final counts or proportions. Multiple-hit resolution invokes the offensive gate internally at line 766, followed by the caller’s configured-mode gate at lines 873, 1360, or 1447.

## Adaptive barcode discovery

The discovery implementation counts catalog-restricted identities and normalizes by all extracted candidates (`include/rad/whitelist_generator.hpp:3029–3087`). Kernel-density estimation uses the Silverman bandwidth and peak criteria at `1797–1818,1848–1904`. Primary saddle selection and the conditional Poisson fallback are implemented at `3197–3269`.

The adjusted hazard is:

```text
H(x) = (1 − exp(−x)) × density(x) / survival(x)
```

Default hazard search requires scores of at least one, at least 50 surviving barcodes, and 5% local prominence (`2174–2183,2314–2317`). The adaptive floor snaps to an observed score and preserves ties (`2606–2666`). It requires at least 50 side-support barcodes and a gain of at least `max(50, ceil(0.01 × old above-floor count))` (`2684–2703`). Rescued-band Poisson checks occur at `2987–3002`.

For expansion of a saddle-selected population, the finite-catalog guard requires:

```text
(K_h − K_0) / (M − K_0) ≤ (M − n_positive) / M
```

Here `K_0` and `K_h` are the populations selected by the preliminary and proposed thresholds, `M` is the chemistry-catalog size, and `n_positive` is the number of catalog barcodes observed at least once (`2159–2167,3352–3448`). The guard applies to expansion of an accepted saddle population. The no-saddle fallback bypasses it (`3394–3402`), and missing or invalid catalog-size inputs allow processing to continue (`3442–3448`).

When a saddle exists, the mixture boundary is diagnostic (`3577–3587`). Final non-hazard collapse rules include a lower tail of at most 10%, narrow groups, or a narrow total range. In the 10–20% tail case, up to 10% of the above-floor population can be rescued (`3605–3687`).

## Measured correction labels

Failure Mode 1 is a reference-supported source barcode changed to a different reference-supported target selected by the tool (`cellranger_to_different_cellranger_K`). Failure Mode 2 is a catalog-valid source barcode outside the filtered reference changed to a selected target (`catalog_noncell_to_selected_A`). The [Figure 3 methods](../../docs/figure_03.md#longbench-correction-categories) define these categories and their counting units.
