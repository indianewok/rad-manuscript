# Figure 2 — synthetic barcode discovery and read assignment

Figure 2 uses ScTagger reads with known source barcodes to examine barcode discovery as reported base quality changes, then measures correct and incorrect read assignments. The quality sweep preserves nucleotide sequences and sequencing errors across conditions.

[Download the editable Figure 2 Prism project](../figures/figure_02/Figure_02.prism).

## Synthetic reads and quality scores

ScTagger-S contains 98,873 reads from 50 source barcodes; ScTagger-L contains 4,993,805 reads from 5,000 source barcodes. The L input contains 8,394,808,882 bases. The uniform-Q20 and Nanopore2023 L files have the same ordered headers and sequences, with SHA-256 `ca3073f0a44d03b40a5919e01e59a8df89ceceafa086ee7580fae2daa3bf2f61`.

Quality generation used Badread 0.4.1, Python 3.9.16, NumPy 1.23.5, edlib 1.3.9, and the retained Nanopore2018 and Nanopore2023 quality models. Background scores were sampled for the complete read. Within a located 16-base barcode, scores were replaced with draws conditional on local match and error patterns between the observed barcode and its known source sequence. Reads without a located barcode retained their background scores.

Each of the eleven sweep conditions adds a fixed Phred-score offset to every base and clips the result to Q1–Q50. The native Nanopore2023 condition retains the original generated scores. Nanopore2018 offsets were +1, +2, +3, +4, +5, +6, +8, +10, +11, +12, and +13; matched Nanopore2023 offsets were −17, −16, −15, −14, −12, −11, −9, −7, −6, −5, and −4. The [matched-level table](../source_data/figure_02/matched_quality_levels.tsv) gives each pairing. [Generation commands](../source_data/figure_02/generation_environment.tsv) record adapter edit distance 7, boundary slop 8, a 16,777,216-score sampling tape, and four compression threads. S2018 used seed `20260727`; L2018 and L2023 used seed `20260731`. The original generator included the model pathname in its effective quality-tape seed. The [generation contract](../source_data/figure_02/quality_generation_contract.json) records the resulting integers. The [recorded-seed adapter](../scripts/figure_02/generate_with_recorded_seed.py) overrides only the quality-tape seed with the recorded integer when model files are moved; all per-read seed calculations remain unchanged.

The [paired two-read example](../data/examples/figure_02/) shows the same read sequences with uniform and sampled qualities. Compare them with:

```bash
mkdir -p results
python3 scripts/revision/figures_124_steps/compare_fastq_sequences.py \
  data/examples/figure_02/L_flatQ20_first2.fastq \
  data/examples/figure_02/L_native2023_first2.fastq results/figure2_two_reads.tsv
```

## Software and settings

Discovery and assignment used separate runs. [Producer records](../source_data/figure_02/producing_evidence/) contain the commands and software identities.

| Analysis | Tool and build | Settings |
|---|---|---|
| Discovery | RAD 1.0.2, `920addacdbf40b815e13a146226e8f4b14a58aaf` | `scan-wl -p CTACACGACGCTCTTCCGATCT -n 16 -e 0.3 -w 10x_3v3 -t 8 -k 10000 -v` |
| Discovery | BLAZE 2.6.0a0 | Expected cells 50 for S and 5,000 for L; 3v3, minimum Q15, 8 threads, `--no-emtpy-drops --no-demultiplexing`. Nanopore2023 conditions replay the native extraction cache through the pinned selector. |
| Discovery | Flexiplex 1.02.6 | `-d 10x3v3 -e 2 -p 8`, with separate flank-distance-0 and flank-distance-8 tracks, followed by the global 3v3 filter. |
| Assignment | RAD 1.0.2, `24d5ce47e172222c96cd7dd19e94758d32aa5009` | Uniform Q20; 3v3 layout with 12-base UMI; the original 6,794,880-barcode Cell Ranger catalogue supplied globally and all 5,000 truth barcodes supplied as the custom whitelist; `-R offensive -M 2 -m 2 -z 5000 -t 64`. |
| Assignment | Flexiplex 1.02.6, `d84c8ae4f3865052f2b5ecec816949b94682f302`, with raw-barcode diagnostic patch | Uniform Q20; `-d 10x3v3 -p 16 -k SELECTED`, flank distance 8, barcode distance 2; 3,004 native selected targets and four compression threads. |
| Assignment | BLAZE 2.6.0a0 matching-function replay | Native Nanopore2023 extractions, barcode distance 2, minimum Q0, 5,015 selected targets; retained seed-0 candidate order with new candidates appended lexically. |

The BLAZE assignment entrypoint arguments and worker count were not retained. The diagnostic Flexiplex build and patch are available in [vendor/flexiplex-audit](../vendor/flexiplex-audit/).

## Barcode discovery

Callsets were compared with the known source-barcode set. True positives are called source barcodes, false positives are calls outside the source set, and false negatives are source barcodes absent from the callset:

```text
precision = TP / (TP + FP)
recall = TP / (TP + FN)
F1 = 2TP / (2TP + FP + FN)
```

Run a complete ScTagger-S example with:

```bash
python3 scripts/revision/figures_124_steps/score_whitelists.py \
  --truth data/examples/figure_02/S_truth_barcodes.txt \
  --output results/figure2_S_shift1.tsv \
  RAD=data/examples/figure_02/S_shift_p01_RAD.txt \
  BLAZE=data/examples/figure_02/S_shift_p01_BLAZE.txt \
  Flexiplex_f0=data/examples/figure_02/S_shift_p01_Flexiplex_f0.txt \
  Flexiplex_f8=data/examples/figure_02/S_shift_p01_Flexiplex_f8.txt
```

The [expected counts](../data/examples/figure_02/S_shift_p01_metrics.tsv), expressed as TP/FP/FN, are RAD 50/0/0, BLAZE 2/0/48, Flexiplex f0 50/136/0, and Flexiplex f8 50/0/0. The [complete discovery table](../source_data/figure_02/discovery_metrics.tsv) contains 144 observations across the S/L Nanopore2018 and L Nanopore2023 conditions. [Callset hashes](../source_data/figure_02/discovery_callset_manifest.tsv) and [barcode identities](../source_data/figure_02/discovery_barcode_identities.tsv.gz) support direct rescoring. For Nanopore2023 shifts, RAD and Flexiplex reuse callsets because the selected settings depend on sequence; BLAZE replays native extractions with shifted qualities.

## Quality distributions

The distribution panel uses [50,000 paired barcode-quality observations](../source_data/figure_02/paired_50000_barcode_mean_Q.csv.gz), [whole-read and barcode histograms](../source_data/figure_02/reconstructed_full_quality_histograms.tsv), [quality summaries](../source_data/figure_02/quality_summary.tsv), and [matched quality levels](../source_data/figure_02/matched_quality_levels.tsv). The eleven matched whole-read means differ by less than 0.374 Q between models.

Complete-read scans separately summarize qualities for 879,860 exact-match barcode windows and 4,096,300 windows with sequence errors. The 17,645 reads without a located barcode form a separate group. The scans apply each offset and clipping operation to individual base scores before calculating means. Results are in the [Nanopore2023 table](../source_data/figure_02/full_read_quality/full_quality_with_blaze_f1.tsv) and [Nanopore2018 table](../source_data/figure_02/full_read_quality_2018/full_quality_with_blaze_f1.tsv).

The [2023 data guide](../source_data/figure_02/full_read_quality/README.md) follows individual barcode windows through integer quality histograms and group means. The [2018 guide](../source_data/figure_02/full_read_quality_2018/README.md) reconstructs original scores by subtracting one from the retained +1 FASTQ; the model’s Q1–Q28 support makes that transformation exact. The original unshifted 2018 BLAZE callset is unavailable. Full scans use the [2023 scanner](../scripts/figure_02/summarize_full_barcode_quality.py), [2018 scanner](../scripts/figure_02/summarize_full_barcode_quality_2018.py), and shared [barcode locator](../scripts/figure_02/barcode_locator.py).

BLAZE’s discovery filter applies Q15 to the minimum score in an extracted barcode. A Phred shift can move a candidate across this threshold. Thus, matched whole-read means can accompany different barcode-quality distributions and different numbers of candidates passing the filter.

## Read assignment and correction

Read identifiers link each output to its true source barcode. Comparing the extracted barcode with the final target identifies native and corrected assignments; comparing the target with the source barcode identifies correct and incorrect assignments.

[Example RAD](../data/examples/figure_02/RAD_assignment_records_example.tsv), [Flexiplex](../data/examples/figure_02/Flexiplex_assignment_records_example.tsv), and [BLAZE](../data/examples/figure_02/BLAZE_assignment_records_example.tsv) records contain raw, target, and truth barcodes. Classify the RAD example with:

```bash
python3 scripts/revision/figures_124_steps/classify_assignment_preview.py --tool RAD \
  data/examples/figure_02/RAD_assignment_records_example.tsv results/figure2_RAD_records.tsv
```

| State | RAD | Flexiplex | BLAZE |
|---|---:|---:|---:|
| Native correct | 667,984 | 463,613 | 640,957 |
| Corrected correct | 1,846,854 | 1,398,700 | 1,881,358 |
| Corrected incorrect | 179,509 | 281,696 | 133,074 |
| Native incorrect | 571 | 381 | 764 |
| Unassigned | 2,298,887 | 2,849,415 | 2,337,652 |

Each column sums to 4,993,805. [Assignment counts](../source_data/figure_02/assignment_states.tsv), [per-target counts](../source_data/figure_02/assignment_per_target.tsv), and [correction-only proportions](../source_data/figure_02/correction_only.tsv) contain the plotted values. Unassigned reads have no retained assignment. Unselected truth targets are blank in the per-target table; selected targets with no reads in a category have zero. Correction-only denominators include corrected assignments: 2,026,363 for RAD, 1,680,396 for Flexiplex, and 2,014,432 for BLAZE.

RAD uses the original full Cell Ranger catalogue and the 5,000 supplied custom truth barcodes. [Its native command](../source_data/figure_02/producing_evidence/assignment_RAD_command.sh), [execution record](../source_data/figure_02/producing_evidence/assignment_RAD_run.json) and [original-catalogue identity](../source_data/figure_02/producing_evidence/assignment_RAD_original_catalogue.json) specify the exact inputs. Run the command with RAD commit `24d5ce47e172222c96cd7dd19e94758d32aa5009` on `PATH`. The [scoring script](../scripts/figure_02/score_rad_assignments.py) reads the complete input and emitted output; its literal arguments are in the execution record. The per-target RAD arrays cover the supplied 5,000 truth targets. [Outside-custom targets](../source_data/figure_02/assignment_RAD_outside_custom_per_target.tsv) are reported separately; the five-state totals include every retained emitted assignment.

## Current source-data plots

![Barcode discovery across quality conditions](../figures/figure_02/quality_discovery_sweeps.png)

![Physical-read assignments and correction outcomes](../figures/figure_02/assignment_descriptive.png)

Render these plots directly from the deposited tables:

```bash
python3 scripts/figure_02/plot_data.py
```

## Reproduction commands

Rebuild source tables from the mounted project files, or check and plot the deposited tables:

```bash
python3 scripts/revision/figures_124.py build --project-root /path/to/rad_data --output-root .
python3 scripts/revision/figures_124.py validate --output-root .
python3 scripts/figure_02/plot_data.py
```

[Table schemas](../source_data/figure_02/schemas.json) define all fields and units. The shared commands also process Figures 1 and 4.
