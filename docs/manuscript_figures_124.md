# Current manuscript evidence: Figures 1, 2 and 4

These replacement passages describe the selected current analyses. They are a
review draft, not a claim that the complete manuscript or its statistical artwork
has been finalized. The machine-readable [claim registry](../manifests/results_claims.tsv)
contains selected numerical claims with their exact table keys and hashes. Existing inferential
tests and annotations are preserved separately.

## Computational efficiency

Computational efficiency was assessed using complete LongBench single-nucleus
ONT and single-cell PacBio inputs with 119,016,231 and 195,242,483 reads,
respectively. RAD 1.0.2 (4acbe00), BLAZE 2.5.0 (11994f9), and Flexiplex 1.02.6
(d84c8ae) were run at 4, 16 and 64 tool threads, with three computational
repetitions per condition on AMD EPYC 7543 nodes. Each demultiplexing run used
the whitelist selected in its corresponding discovery phase. At 16 threads,
mean total wall times were 1.75, 7.24 and 9.08 hours for RAD, BLAZE and Flexiplex
on SN-ONT, and 1.49, 3.04 and 2.01 hours on SC-PB. Total time is the sum of
the two phases within each repetition. Peak process memory is the larger GNU-time
maximum resident set size, converted from KiB to decimal GB. These are repeated
computational runs on the same inputs.

[Figure 1 source and commands](figure_01.md) provide the complete identities,
resource definitions and phase-specific parameters. The two recovered HD count
sources describe different stages: whitelist detection and demultiplexing. The
selected detection totals match the original valid-pair tables exactly across all
four flow cells. The complete 419×419 grid and 123,658-bin tissue mask are also
recovered and independently matched to the saved Space Ranger barcode sets. The
selected Seurat `nCount_Spatial` values and full barcode-to-bin creation provenance
remain unresolved, so a shared-scale spatial triptych is not yet supported. Coordinates
for that analysis represent **16 µm bins**, not individual cells. The Space Ranger
workflow derives from converted Nanopore reads, not an independent Illumina input.

## Synthetic barcode discovery and assignment

The ScTagger large input contains 4,993,805 reads from 5,000 known source barcodes;
the small input contains 98,873 reads from 50 source barcodes. The selected
quality experiments preserve original read identifiers, nucleotide sequences
and error patterns. Complete input checks confirmed those identities. Discovery
performance is calculated by exact selected-set comparison to the known source
set, and is distinct from read-assignment correctness.

The primary assignment comparison retains the tool-specific selected inputs:
RAD 24d5ce4 with the complete 5,000-source-barcode set as both global and custom
list; Flexiplex 1.02.6 with the diagnostic pre-correction field and its own
3,004-target list; and the BLAZE 2.6.0a0 matching-function replay on the native
nanopore2023 extraction with its 5,015 selected targets. RAD and Flexiplex retain
the uniform-Phred-20 sequence-identical inputs because these procedures do not
use base quality. This is not a claim that the three assignments used an identical
selected whitelist or were all rerun from raw reads in this revision.

Each physical read belongs to one of six mutually exclusive states:
native-correct, corrected-correct, native-incorrect, corrected-incorrect,
multiple-output excluded, or unassigned. The state counts sum to the complete
input for each tool. RAD excludes every identifier with multiple emitted records;
Flexiplex collapses repeated identical-target assignments and excludes conflicting
targets. Missing unselected source barcodes remain blank in the per-target
comparison; selected targets with no reads in a category have zero. Correction-only
fractions exclude native assignments. These definitions and all counts are
inspectable in the [Figure 2 walkthrough](figure_02.md).

The selected quality-generation seed contract includes the literal model-path
strings. A future pathname-independent generator would create a new experiment;
it has not silently replaced these selected data.

## Barcode discovery across 37 inputs

The comparison includes all 37 benchmark inputs and all three tools, yielding
111 observations. ScMixology2 retains a native RAD callset and explicitly
reconstructed BLAZE/Flexiplex counts and filter replays. Separate technical runs remain distinct benchmark entries,
with their shared library/donor context retained; the 37 inputs are not asserted
to be 37 independent biological replicates. Exact known barcodes define simulation
truth. Matched short-read filtered barcodes and published spatial masks are
operational positive references for biological inputs, not exhaustive biological
negative truth.

The RAGE-seq lymph-node positive reference contains 5,978 annotated
adaptive-immune-containing barcodes: 4,255 T cells, 1,637 B cells and 86 T/B
doublets. Epithelial and numeric/unannotated entries are not counted as positives.
Consequently, a call outside this positive reference is an operational false
positive, not proof of an empty or nonimmune biological source.

Using the retained precision/recall/F1 definitions, RAD, BLAZE and Flexiplex have
F1 greater than 0.90 on **26, 19 and 17** of the 37 inputs, respectively. The
current rebuttal should therefore use **17**, not 18, for this Flexiplex statement.
This is a numerical source correction, not a new statistical test. The plotted
read count, GC percentage and average-quality summaries describe each actual
long-read input. They are retained SeqKit summaries; their original complete
invocation/version has not been recovered.

Per-input versions, parameter differences, exact source lists where recovered,
and paired observations are linked from [Figure 4](figure_04.md). No new paired
test or multiplicity correction is proposed in this revision.
