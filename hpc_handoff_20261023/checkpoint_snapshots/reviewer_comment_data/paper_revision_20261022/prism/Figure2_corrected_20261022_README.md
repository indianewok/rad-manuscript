# Figure 2 corrected data copy — 22 October 2026

`Figure2_corrected_20261022.prism` contains corrected Figure 2 data and retains the source figure's **correction-only** comparison. It is ready for review in Prism. It has not been opened or exported in Prism, in accordance with the decision to open it later. The main layout is named **Main Figure — DATA UPDATED; VISUAL AND STATISTICAL REVIEW PENDING**.

The Dropbox V18 original and preserved evidence copy remain unchanged. Their SHA256 is `d8cc036cdca79d607be863fd15a9bc4721c4e86d09721ea4b368401fa9b3a10c`. This corrected copy has SHA256 `dded389f9d8214278f93d2669c64e704bbf2208c47db96bf57a4ce4c77d6d016`. The earlier five-outcome draft is superseded and is retained only in `superseded_five_outcome_draft/`.

## Corrected data

- BLAZE uses the native, unadjusted nanopore2023 whitelist and the new deterministic assignment replay. Its selected list contains 5,000 truth barcodes and 15 additional barcodes, replacing the older result with 87 additional barcodes.
- RAD uses the verified strict assignment audit. Flexiplex uses its own selected list of 3,004 truth barcodes. Native and corrected per-barcode graph slots that previously contained fixed-5,000 Flexiplex data now contain the verified selected-list values. The 1,996 unselected truth barcodes remain missing, rather than becoming zero observations.
- The native graph retains the source's **222,371-read Flexiplex full-truth 5K reference increment**. It is a reference for the additional native-correct reads obtained under the fixed full-truth list. The corresponding data series is titled “Full-truth 5K reference increment”.
- Error-correction headlines and per-barcode distributions use **corrected incorrect**, excluding native incorrect assignments. The doughnuts plot only corrected-correct and corrected-incorrect counts.

| Tool | Corrected correct | Corrected incorrect | Correction-only denominator | Displayed correct / incorrect |
|---|---:|---:|---:|---|
| RAD | 1,944,306 | 191,519 | 2,135,825 | 91.03% / 8.97% |
| Flexiplex | 1,398,700 | 281,696 | 1,680,396 | 83.24% / 16.76% |
| BLAZE | 1,881,358 | 133,074 | 2,014,432 | 93.4% / 6.6% |

Each doughnut's underlying source table has six mutually exclusive outcomes: native correct, corrected correct, corrected incorrect, native incorrect, multiple outputs excluded and unassigned. All six sum to **4,993,805 input reads**. In both numeric and row-title datasets, rows 0 and 3–5 are excluded, leaving rows 1–2 for the correction-only plot. The plotted denominator is the correction total above, not all input reads. The six-state CSV and correction-total CSV accompany this copy.

For BLAZE, the corrected-incorrect headline includes all 5,015 selected output targets (133,074 assignments). Its per-truth-target plot uses the 5,000 truth rows only (132,166 assignments); 908 corrected-wrong assignments to additional targets are outside that plot. The false-target table retains all 1,091 assignments to 15 additional targets: 908 corrected-wrong and 183 native-wrong. No artificial zero false-target observations were added for RAD or Flexiplex.

“Multiple outputs excluded” retains each tool's audit convention. RAD excludes original read IDs with multiple output records. Flexiplex collapses same-target duplicate outputs and excludes IDs with different final targets. BLAZE has zero separately excluded multiple emitted assignments; native matcher ambiguity remains in Unassigned.

## Statistical and visual review still required

Six affected statistical result caches were cleared and marked for recalculation. No replacement tests or P values were generated. Saved statistical definitions remain for review and do not constitute an approved test choice.

Known manual percentage labels were updated at their original precision using exact same-length text replacements: RAD and BLAZE changed, while Flexiplex was already correct. Every other graph binary byte remains unchanged. The two replacements passed reverse-patch checks.

When the copy is opened in Prism:

1. Check the graph and layout against the updated tables, then save natively.
2. Check the native and corrected Flexiplex per-barcode plots for 3,004 observed values and 1,996 missing truth rows. Confirm that the incorrect distributions show corrected-incorrect assignments.
3. Review the statistical design and replace or remove obsolete significance brackets and stars. Check manual barcode, bar and center labels; static labels such as the old BLAZE false-positive count or incorrect-read count may remain.
4. Confirm that each doughnut shows the two correction outcomes with the denominator above. Confirm the native Flexiplex reference increment and its legend remain clearly identified.
5. Export and inspect the Figure 2 layout. No native export has yet been verified.

## Verification and provenance

The builder's independent read-back validation passed **388 checks**. A second agent's audit passed **499 checks**, including exact canonical values, barcode alignment, Flexiplex missing values, correction-only row exclusions and denominators, the original reference increment, table dimensions and bounds, preserved graph references, removed statistical caches, original CSV history and allowed binary substitutions. These checks establish saved data and archive structure; they do not replace native rendering.

- `Figure2_corrected_20261022_validation.json`: 388-check report.
- `independent_audit.json`: 499-check independent report for this output hash.
- `Figure2_corrected_20261022_change_log.json`: changed archive members, graph contracts and pending review.
- `Figure2_corrected_20261022_source_preservation.json`: post-write hashes of the actual Dropbox source, evidence copy, output and canonical inputs.
- `history_before_20261022/`: original edited CSV tables.
- `blaze2023_assignment_replay/`: replay arrays, manifest and provenance.
- `../evidence/figure2_canonical_rad_flex/`: verified RAD/Flex source arrays.

Changed tables use the existing project's SHA256-prefix refresh-token convention. Table dimensions and populated-row bounds are updated, including the BLAZE false-target table's 15 rows and the six-row pie source tables.
