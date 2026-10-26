# Current analysis decisions

These decisions reflect the author's instructions in the 23 October 2026 HPC
revision session and override earlier handoff proposals.

| Topic | Current decision | Consequence |
|---|---|---|
| Repository presentation | Human-readable data and small transformations first | Actual input previews, schemas, output tables and figure proofs are linked from every walkthrough |
| Tool provenance | Exact RAD/BLAZE/Flexiplex versions and parameters at the top of every figure | Different producing runs keep separate pins; unknowns remain explicit |
| Historical material | Do not retain superseded material when an analysis is rerun | Current selected analysis only; recovery/comparison archives live outside this repository |
| Figure 3 RAGE | Run the same matched-list/strict-read procedure used for the other two datasets and compare the conclusion | New run is explicit, fully pinned and replaces the old RAGE outputs after validation |
| Statistics | Do not change existing statistical choices or annotations | No new inferential design is silently substituted; discrepancies in execution provenance remain documented |
| Figure 4 | Include all 37 inputs, including reconstructed ScMixology2 | Preserve input pairing and technical-library relationships |
| Figure 7 | Updated concatemer-aware RAD matrix and common 8,135 genes | Preserve emitted segments, gene inheritance and original UMI-counting rules |
| Figure 7E | Remove | Current Figure 7 is A–D |
| Figure 8 | Removed from current scope | Its dedicated analyses are absent; the eight benchmark Visium libraries remain in Figure 4 |
| Publication | Prepare for review | Do not change repository visibility or publish archival records yet |

The diagnostic Flexiplex patch exposes pre-correction sequence. Its optional
source-set filter must be unset. The deferred ScTagger pathname-independent RNG
change is not part of this revision; preserved model paths/effective seeds define
the selected quality data.

Measured Figure 3 categories retain the accepted observed source/target rules:
changed off-catalog source to a selected target; **Failure Mode 1**, changed
catalog source outside the matched filtered set to a selected target; **Failure
Mode 2**, changed filtered-set source to a different target in both the filtered
and selected sets. Missing source sequence is not a noncatalog observation.
These flags can overlap for a read–target pair. The denominator remains all
unique assignments to that target, not the sum of category counts.
