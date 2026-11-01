# RAD barcode-processing reference

These steps describe RAD commit `cb6991705ac0e9c93a108fd439aa0357834cc701`. The [benchmark versions and flags](../../docs/figure_01.md#software-and-benchmark-settings) identify the timed runs. Source references below use this commit: [barcode_correction.hpp](https://github.com/indianewok/rad/blob/cb6991705ac0e9c93a108fd439aa0357834cc701/include/rad/barcode_correction.hpp), [sigstring.hpp](https://github.com/indianewok/rad/blob/cb6991705ac0e9c93a108fd439aa0357834cc701/include/rad/sigstring.hpp), [whitelist_generator.hpp](https://github.com/indianewok/rad/blob/cb6991705ac0e9c93a108fd439aa0357834cc701/include/rad/whitelist_generator.hpp) and [main.cpp](https://github.com/indianewok/rad/blob/cb6991705ac0e9c93a108fd439aa0357834cc701/src/main.cpp).

## 1. Load barcode lists and check exact identity

RAD stores selected barcodes in the `true_bcs` multimap and the broader chemistry catalog in the `global_bcs` flat set (`include/rad/barcode_correction.hpp:1955–1958`). Global lookup returns exact keys; insertion stores canonical identities (`937–982`). Precomputed mutation aliases enter the selected multimap only when their sequence is absent from both existing sets (`2175–2205`).

List loading determines the role of each supplied set. With two unequal-sized lists, the smaller becomes selected and the larger becomes global after removing selected identities (`2393–2418`). A single list with at least 100,000 entries becomes global; a smaller list becomes selected (`2366–2391`). Equal-sized lists are merged into the selected set (`2420–2437`).

After normalizing reverse-oriented extracted sequences, RAD applies static-sequence and complexity filters, then checks exact catalog identity before selected-set lookup in both correction modes (`include/rad/sigstring.hpp:1265–1343,1399–1430`). Exact identity can bypass the running-count gate. The write rule is:

```text
write = found_in_true || (true_wl_empty && found_in_global)
```

The rule is implemented at `sigstring.hpp:3440–3471`. FASTQ serializers skip barcode elements with `write=false` (`4881–4884,5042–5045`); a non-bulk record with no remaining barcode is omitted (`4948–4950,5105–5107`). Permissive multi-component processing can emit the remaining accepted barcode components; strict processing requires every component to pass (`3293–3389`).

With a nonempty selected set and a correctly oriented catalog identity, selected identities are writable and catalog-only identities are suppressed. The measured correction categories compare observed source and assigned target barcodes; their definitions appear below and in the [Figure 3 guide](../../docs/figure_03.md).

### Orientation and output rules

Reverse reads are normalized before global-catalog lookup. The global branch tests membership of `bc` or its reverse complement at `sigstring.hpp:1321`; candidate retrieval uses the `bc` key at line 1322. A reverse-complement-only membership hit with no `bc` key yields no candidate. A supplied catalog provides catalog-identity protection. Catalog-only output is writable when the selected set is empty.

## 2. Find a unique correction target

Lookup structures contain canonical barcodes and precomputed mutation variants associated with candidate records. The runtime functions `correct_barcode`, `process_single_barcode` and `apply_barcode_correction` query these structures without inserting the accepted query-to-target assignment (`sigstring.hpp:1255–1564,3403–3477`).

Multiple lookup hits are sorted by distance, and candidates with a positive direct-observation count are considered. The first distance with one supported candidate can pass; multiple supported candidates at that distance are rejected (`743–779`). An unsupported nearer candidate is skipped; a supported, more distant candidate can be selected. Ties among supported candidates are rejected.

Exhaustive search evaluates all canonical candidates in its selected container and requires one best-distance match (`933–939,1007–1072`). For selected sets larger than 10,000, an accepted seed-shortlist result returns immediately; exhaustive fallback follows a failed shortlist (`1184–1235`). Uniqueness is consequently evaluated among the candidates examined at the accepting search stage.

Defensive mode consults the broader catalog before the selected set during direct k-mer and mutation lookup. Offensive mode uses the opposite order (`1127–1175,1512–1549`). Later seed and exhaustive fallback searches use the selected set. Offensive mode is the CLI default (`src/main.cpp:1492`).

## 3. Apply the running-count gate

Barcode records contain atomic direct and corrected counters (`barcode_correction.hpp:30–97`). Counts are updated for passing barcode elements after read classification (`sigstring.hpp:2567–2601`). Direct status uses equality to the original extracted sequence or its reverse complement (`3465–3470`). The correction gate at `668–726` applies these checks:

| Current state | Gate behavior |
|---|---|
| Total count is zero | The candidate can pass before a direct observation. |
| Fewer than two direct observations and total at least five in defensive mode or ten in offensive mode | The target is blocked by setting its total to −1. |
| Blocked target with at least two direct observations | The total can reset to the direct count. |
| At least ten total and two direct observations | The prospective corrected fraction `(corrected + 1)/(total + 1)` must be at most 0.80. |
| Exact identity match | The identity branches can bypass the correction gate. |

The total counter doubles as a block sentinel (`719–724`) and can reset to the direct count (`700–705`). Identity calls can subsequently increment direct and total counts (`2586–2590`): for example, −1 can become zero, allowing the zero-total gate to pass (`685–695`).

Counter checks and later increments are separate operations using relaxed atomics. Concurrent records can pass against the same prior state. The thresholds five, ten and 0.80 are evaluated against the counters available when each record is processed. Multiple-hit resolution invokes the offensive gate internally at line 766, followed by the caller’s configured-mode gate at lines 873, 1360, or 1447.

## 4. Select a barcode shortlist

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

Here `K_0` and `K_h` are the populations selected by the preliminary and proposed thresholds, `M` is the chemistry-catalog size, and `n_positive` is the number of catalog barcodes observed at least once (`2159–2167,3352–3448`). The guard is evaluated when expanding an accepted saddle population with a valid catalog size. The no-saddle fallback proceeds directly (`3394–3402`); missing or invalid catalog-size inputs also allow processing to continue (`3442–3448`).

When a saddle exists, the mixture boundary is diagnostic (`3577–3587`). Final non-hazard collapse rules include a lower tail of at most 10%, narrow groups, or a narrow total range. In the 10–20% tail case, up to 10% of the above-floor population can be rescued (`3605–3687`).

## 5. Classify observed correction outcomes

Failure Mode 1 is a reference-supported source barcode changed to a different reference-supported target selected by the tool (`cellranger_to_different_cellranger_K`). Failure Mode 2 is a catalog-valid source barcode outside the filtered reference changed to a selected target (`catalog_noncell_to_selected_A`). The [Figure 3 methods](../../docs/figure_03.md#longbench-correction-categories) define these categories and their counting units.
