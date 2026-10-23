# Figure 2 native Prism audit

Audit date: 22 October 2026. Read-only inspection of saved archive contents. No Prism file was edited and no statistical test was run.

## Source and scope

- Latest Figure-2-specific file in the explicitly named project directory: `/Users/cmv/Library/CloudStorage/Dropbox-DartmouthCollege/Chinmay Vaidya/scRNA_Seq_Nanopore_LongRead_Project/Nat Comm/appeal/figure_revisions/092126_Figure_2_CMV_V18.prism`.
- Exact copy: `092126_Figure_2_CMV_V18.prism` in this evidence directory. Source and copy SHA256: `d8cc036cdca79d607be863fd15a9bc4721c4e86d09721ea4b368401fa9b3a10c`.
- Saved by Prism 11.0.0.93 for Mac at `2026-09-22T01:30:14Z`; originally created with 10.6.1.799. The archive contains 37 user data sheets, 33 graphs, 13 analyses, and three layouts. Additional data sheets hold analysis views.
- The native archive supplies dataset references and saved data/results. Graph geometry, annotations, and some presentation state are binary. A Prism-rendered export is still required to establish exact visible series, panel labels, and annotations. This audit does not establish unsaved UI state.
- Machine-readable inventory: `figure2_prism_inventory.json`. It contains all graph/layout IDs, each dataset's owning sheet and CSV columns, saved analysis parameters/results, and barcode alignment checks. Exact relevant CSVs are exported under `figure2_native_tables/`, named by data-sheet UUID. Empty cells remain empty.

## Main findings

1. **The main layout retains nanopore2018 +6 BLAZE results.** Its selected-list table has BLAZE TP 5,000 / FP 87 / FN 0. Corrected-correct total is 1,871,785, and native-correct total is 640,957. Separate 2023 quality-sweep tables coexist in the file; their presence does not change these main-layout bindings.
2. **Flexiplex conditions differ between panels.** Main-layout native-per-barcode and correctly-corrected-per-barcode graphs reference the fixed-5,000 condition (sums 685,984 and 2,174,996). Main-layout headline totals reference the self-selected 3,004 condition (463,613 and 1,398,700). The incorrect-per-barcode graph references the self-selected condition, while its calculated RM ANOVA references fixed-5,000 Flexiplex instead.
3. **Incorrect totals are not category-consistent.** Headline RAD 192,090 and Flexiplex 282,077 represent all final-barcode-incorrect assignments in their source scorers; headline BLAZE 135,358 represents corrected-incorrect only and excludes 1,392 native-incorrect assignments. BLAZE all-incorrect is 136,750. The saved file alone cannot establish the correct RAD/Flex native-incorrect partition.
4. **The pies contain additional unsupported arithmetic/category splits.** RAD pie values include 191,845 “Incorrectly corrected” and 245 “Improperly extracted”; Flexiplex includes 281,713 and 364. These are numerically 192,090−245 and 282,077−364. The source Flex scorer identifies 364 as ambiguous, not a subset of the 282,077 incorrect count. Therefore subtraction is not justified by that scorer. RAD's independently verified strict ambiguous count is 9,048; its pie omits that count. The five displayed RAD pie cells sum to 4,984,757, which is 9,048 fewer than the stated 4,993,805 input reads. These pie partitions must be reconciled with record-level truth before treating them as exhaustive.
5. **Some analyses have no saved result, and one calculated analysis uses a different Flexiplex condition than its graph.** Details below. A saved `isCalculated=true` is not proof of an appropriate analysis design.

## Main layout and graph bindings

Main layout: `4B74E124-3EC5-4749-A164-AA426B306E0C`, title “Main Figure.” Archive source: `layouts/<UUID>/sheet.json`, property `linkedGraphSheets`.

| Graph title | Graph UUID | Owning data-sheet UUID | Saved binding / values |
|---|---|---|---|
| correct assignment | `B1B9DD97-D8A6-4176-986D-F1FFE06CC16D` | `4B8EFB7D-5961-4D1B-84F1-D6FA39AF32C7` | RAD 1,944,306; Flex self-selected 1,398,700; BLAZE 1,871,785 |
| incorrect assignment | `78ED1972-AE8E-4FF9-A806-A4C01F8685AE` | `37772031-416B-47A5-AAEF-0FF64BCA23FC` | RAD 192,090; Flex self-selected 282,077; BLAZE 135,358 |
| copy 2E TP--no blaze FP | `F865645E-456D-47FD-8044-D25160387EBA` | `448995F1-96AC-4614-A785-176A654CEC8E` | “WL generated”: BLAZE/Flex/RAD 640,957/463,613/667,965. “5K full”: 0/222,371/0. Thus the second series is an increment, not the complete fixed-5K native count. |
| Copy of Figure 2D, performance parameters | `122822C9-4B03-4D27-B2BE-010D9D86EC90` | `52A2C540-4929-4698-BB41-5176D0B18C1B` | RAD F1/recall/precision 1/1/1; BLAZE 0.991375037177/1/0.982897582072; Flex 0.750624687656/0.6008/1 |
| 2B-C stacked | `2DA077CB-95AE-40D8-AEDB-D86BA89FAACE` | `9FA3BE17-60E1-4F42-8084-62CD9B3AE250` | Rows BLAZE/Flex/RAD; columns TP/FP/FN: 5000/87/0; 3004/0/1996; 5000/0/0 |
| Figure 2G, native match count per true positive (TP) barcode | `C7434C91-4E18-4805-93E3-FCBE8777D387` | `63D81234-28AC-46E8-8332-CB1AE2FC1AFF` | BLAZE + RAD + **fixed-5K Flex**, all 5,000 nonblank rows |
| Figure 2I, corrected assignments per TP barcode | `618D16ED-954A-44DD-B5C8-FA74FF1CD274` | `66EF3D96-C86B-4FA9-ACE5-53621808DA50` | RAD + **fixed-5K Flex** + BLAZE, all 5,000 nonblank rows |
| Figure 2J, incorrect assignments per TP barcode | `3568D2DE-F40D-46FE-B8F5-7C7BB63AA49F` | `98505F94-3866-4F00-A8CD-E076CF542357` | RAD + **self-selected Flex** + BLAZE. BLAZE TP-target subtotal 130,922, not all-target 135,358. |
| RAD read correction types … [Reads] | `B966F8E8-0320-49B2-ACD2-68E5E5FF8904` | `B3E0F44C-855D-4363-A355-2267133BA781` | 667965,1944306,191845,245,2180396 |
| BLAZE read correction types, pie | `83474767-C51C-4BC1-B6AB-E18E9B70436B` | `6A891CCF-953F-4BA6-B06C-DA6B6693C7FE` | 640957,1871785,135358,1392,2344313 |
| Flexiplex read correction types, pie | `98FF29A5-EA42-4F66-9919-ABA4DD8B11C4` | `28DC41C5-EC81-4A2B-87F9-2D94E2314B62` | 463613,1398700,281713,364,2849415 |
| Off-list experiment (ScTagger/Longbench) | `73F311BA-849B-4232-BD38-50F2D99FD8C6` | `969A7A49-AD72-4F65-A725-A8B9E0A0CEC8` | Three data rows (ScTagger-L, LongBench SC-ONT, RAGE-seq); three replicate subcolumns per tool. |
| Copy of ScTagger\|LongBench\|RSQ | `0416174E-A451-4CBA-9CB5-C1A776AB5A54` | `F0694302-5FC9-439B-9C62-B69220EEE154` | Nine bound series: replicate 1 only for each tool/dataset. Different historical RAGE-seq sums occur between this per-barcode table and the preceding replicate-summary table; these are outside the immediate Figure-2 correction repair. |

Pie row order is native, correctly corrected, incorrectly corrected, improperly extracted, not demultiplexed. Graph titles are saved titles and do not establish the final panel lettering in the DOCX.

## Per-barcode datasets and exact replacement candidates

The native, corrected, and incorrect tables contain **identical, lexically ordered 5,000 unique barcode row labels**. They are matched by barcode identity, not independently sorted counts. In all three tables the self-selected Flexiplex series has the same 3,004 nonblank rows and 1,996 blanks. Blanks are not zeros. The complete fixed-5K columns have 5,000 observations.

Columns below use Prism letters. In the exported CSV, column 0 is the barcode row label; A is CSV column 1.

| Table | Column | Dataset UUID | Condition | Nonblank / sum |
|---|---|---|---|---|
| Native | A | `55733904-0FA1-4462-9987-5CDECF83A340` | BLAZE +6 | 5000 / 640957 |
| Native | B | `B7A95E01-DCE4-4964-ADD1-71CF919FE6DE` | RAD | 5000 / 667965 |
| Native | C | `8C506AC1-3D51-473C-A40B-39448CBDE59D` | Flex self-selected | 3004 / 463613 |
| Native | D | `7A817AB2-8B3F-4B5F-85FB-0984A7A35D99` | Flex fixed5K; graph currently binds this | 5000 / 685984 |
| Corrected | A | `25C79583-B71F-4587-A42E-2C295A006D14` | BLAZE +6 | 5000 / 1871785 |
| Corrected | B | `FF40BBC9-474C-49EC-85C5-707493619F18` | RAD | 5000 / 1944306 |
| Corrected | C | `197C841C-A1D9-4BF7-AF25-60A713172056` | Flex self-selected | 3004 / 1398700 |
| Corrected | D | `33CFF86A-A5F5-4454-B030-E0492F0A9B49` | Flex fixed5K; graph currently binds this | 5000 / 2174996 |
| Incorrect | A | `9EAF2EAD-1268-45DD-A97B-95FB03243A40` | BLAZE +6, TP targets only | 5000 / 130922 |
| Incorrect | B | `BA645DAC-CA07-4E30-82F8-81C9505CB8BF` | RAD | 5000 / 192090 |
| Incorrect | C | `594B2375-BAC7-43FF-8B3D-89B48CF0526B` | Flex self-selected; graph binds this | 3004 / 282077 |
| Incorrect | D | `06A86DEC-700A-4815-A53A-023C6531060E` | Flex fixed5K; calculated ANOVA binds this | 5000 / 171592 |

For consistent self-selected Flexiplex plots, the exact existing candidates are Native C and Corrected C, preserving barcode rows and blanks. Choice of whether to analyze only common barcodes, model missing data, or assign zero for a specifically defined missing-output estimand remains a statistical/design decision. No zero fill is authorized by the existing table structure.

## Analyses: absent versus calculated results

Archive paths are `analyses/<UUID>/sheet.json`, `parameters.json`, and `results.json`.

| Analysis UUID | Saved analysis | State and interpretation |
|---|---|---|
| `1692D0EE-34B0-47E1-AA9A-B1A96AD55A39` | FP-barcode descriptive statistics | `isCalculated=false`; results JSON only contains its class. Explicit “recalculation required” result title. No saved numerical result to reuse. |
| `6868ACFE-05E0-455D-B273-BCB0856BE80B` | Corrected-per-barcode mixed-effects analysis | `isCalculated=false`; empty results. Inputs BLAZE, RAD, self-selected Flex C. Parameters specify repeated-measures optional mixed model, assumed sphericity, RAD-versus-all Holm–Sidak. Saved design only, not a result. |
| `AA4C6237-DB10-425A-866F-F7E130BDA8F1` | Incorrect-per-barcode mixed-effects analysis | `isCalculated=false`; empty results. Inputs BLAZE, RAD, self-selected Flex C. No saved numerical result. |
| `E2C721DC-CF0D-45D4-A198-0E9955653EDC` | Native-per-barcode RM ANOVA | Calculated. Inputs BLAZE, RAD, fixed5K Flex D. Saved means 128.1914,133.593,137.1968 and n5000 match its bound columns. Not evidence for the self-selected Flex condition. |
| `BB4EB3C9-1C4C-4843-B4D5-72F9942D120C` | Corrected-per-barcode RM ANOVA | Calculated. Inputs BLAZE, RAD, fixed5K Flex D. Saved means374.357,388.8612,434.9992 and n5000 match its bound columns. Not evidence for self-selected Flex. |
| `5BD85BDF-0140-4146-8921-64C4ABC643C5` | Incorrect-per-barcode RM ANOVA | Calculated. Inputs BLAZE, RAD, fixed5K Flex D, although main graph uses Flex C. Saved means26.1844,38.418,34.3184 and n5000 match fixed5K data. Thus any use for the plotted self-selected Flex comparison is invalid. |

The three calculated per-barcode RM ANOVAs use sphericity correction and Dunnett comparisons versus RAD in their saved parameters/results. These are genuinely saved results; they are not merely empty placeholders. They must be removed from, or reset for, a revised self-selected-condition figure. Their current presence is useful provenance for the fixed5K experiment and does not justify deleting the original source. Keep the untouched evidence copy. Recompute only after the intended observations and test have been selected.

## Separate 2023 candidates

- The latest main file itself includes separate 2023 barcode-quality, precision, recall, and F1 tables. Their full graph/dataset mappings are included in the JSON inventory. Example data sheets: precision `0B4C5B04-EC1C-4F6E-BADF-49CCA5AB649E`; recall `4661BB37-ED86-4A2E-91D5-82CCAE2220E8`; F1 `5E81D226-B97E-43FD-8F96-7D44CC623F4B`; quality distribution `134AC60B-C7BC-5034-8701-54E40D70AB5E`.
- Separate 2023 native provenance candidate: `/Volumes/rad_data/reviewer_comment_data/scratch_preservation_20260921/files/sctagger_prism_nanopore2023_20260913/added_tables.prism`, with sibling `README.md`, `table_spec.json`, `input_provenance.json`, and validation reports. This is a quality/discovery-table addition, not proof of a 2023 demultiplexing run.
- Other exact source-directory candidates are `091326_Figure_2_CMV_V17.prism` and `091526_Figure2-5_CMV_V1.prism`. They were located by names only and were not substituted for V18.

## Supporting source interpretation

The source scorers and quality-condition provenance are documented with line-numbered references in sibling `benchmark_methods.md`. In particular: `sctagger_flexiplex_audit_20260812/join_audit_native.py` classifies ambiguous and incorrect separately; `sctagger_L_rad_fixed5000_adapter_fix_20260817/independent_validation/METHODS.md` defines strict RAD categories; and `LongBench_comps/ScTagger_quality_sweep_20260731/SWEEP_SUMMARY.md` gives the BLAZE native-incorrect and corrected-incorrect totals. The native Prism tables do not override those scorer definitions.
