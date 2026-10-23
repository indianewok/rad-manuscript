# Repository and Zenodo audit — 23 October 2026

Repository: https://github.com/indianewok/rad-manuscript

Historical local checkout: `rad-manuscript/` (the parent repository in this GitHub edition). Audited commit: `3465937aa6a8e51b9f6989e750d45990a2a3d7d6` (29 May 2026). The audit describes that preserved code baseline. The later handoff commit adds documentation and snapshots without changing the analysis code. The repository was reported private by the GitHub connector. Publication of the revised code is a release task.

## Main conclusion

The downloaded repository preserves the older manuscript's Figures 2–5. It is not yet a reproducible build of the current Figures 1–7. Much of the newer analysis is retained on `rad_data`, often with useful intermediate data. The main integration job is to import those executed workflows and their checkpoints, connect them to explicit figure inputs, and validate each connection. Re-running the old top-level shell script will not accomplish this.

## Figure crosswalk

| Existing repository content | Current manuscript destination | Required treatment |
|---|---|---|
| Old Figure 2: ScTagger S/M/L and subsamples | Figure 2 | Replace the experiment registry and plotting inputs with the documented Nanopore2018/Nanopore2023 quality conditions and native discovery comparisons. Keep the old analysis as a historical version. |
| Old Figure 3: RAGE-seq and off-list controls | Parts of Figure 3 and Figure 5A–F | Split the two purposes. Import current ScTagger/LongBench challenges and the LongBench correction audit into Figure 3. Resolve historical RAGE provenance separately. |
| Old Figure 4: scMixology timing | Current Figure 1B–C uses LongBench SN ONT and SC PacBio | Replace dataset, command, timing-log and hardware lineage. Do not relabel old timing numbers. |
| Old Figure 4: Visium HD overview triptych | Figure 1D | Reuse the retained renderer after checking its inputs and parity with the selected artwork. |
| Old Figure 4: LR-Split-seq | Figure 5G–H | Import the final component-based comparison and resolve its test/legend discrepancy. |
| Old Figure 4 NBC content and old Figure 5 clonotypes | Removed Figure 8 | Exclude from the current build. Preserve the old release for historical reproducibility. Engblom libraries still belong in the 37-input benchmark. |
| No current equivalent | Figure 4: 37-input comparison | Import the sample registry, three-tool results, input/reference qualification and statistics. |
| No current equivalent | Figure 6: LongBench genotype analysis | Import bulk donor-panel, per-tool genotype, reference and fixed-coordinate checkpoints. |
| No current equivalent | Figure 7: expression comparison | Import the updated concatemer-aware RAD matrix and 8,135-gene comparison. Figure 7E remains pending. |

## Concrete defects and repairs

Paths below refer to the preserved checkout. Line references apply to the audited commit.

1. **Cached rendering is blocked by unnecessary raw-run requirements.** `scripts/run_all_figures.sh:16–17` requires `RAD_BIN`, `RAW_FQ`, `RESULTS_BASE`, `WL_DIR`, `PROJECT_SCRIPTS` and an executable RAD binary before selecting `analysis` mode. The README says cached rendering needs neither raw FASTQ nor RAD. Validate requirements by stage. Acceptance: a fresh environment with only the release's plot checkpoints and rendering dependencies can render every completed current panel.

2. **A successful raw command does not rebuild the data used by the plots.** The drivers write `.last_demux_paths.txt`, but the Rmd files load a fixed `figure_N_workspace.RData` (`figure_2:20`, `figure_3:20`, `figure_4:23`, `figure_5:23`). No notebook consumes those manifests. Add explicit parse → count → statistics → plot stages that receive the preceding stage's manifest. Acceptance: modifying an upstream input invalidates dependent outputs; a full run cannot silently render the archived workspace.

3. **The top-level build covers only old Figures 2–5.** `scripts/run_all_figures.sh` offers no current Figure 1, 6 or 7, and its Figure 4/5 definitions have changed. Implement the current panel registry and retain a separate legacy entry point. There is no existing current-paper one-command runner to invoke yet.

4. **Three-tool regeneration is incomplete.** The shell drivers mostly execute RAD; setting `BLAZE_BIN` does not add a BLAZE run. Import executed BLAZE and Flexiplex runners, native whitelist discovery, diagnostic extraction and parsing. Capture each actual version, source revision, patch, binary hash, catalog and command. Do not apply one modern RAD commit or the README's BLAZE `v0.10.1` to all historical experiments without evidence.

5. **The synthetic runner has the wrong experiment grid.** `scripts/run_figure_2.sh:64–116` runs S/M/L and downsampled datasets, without the final two quality models and eleven shifts per model. It also skips missing whitelist/demultiplexing outputs with warnings (`:84`, `:111`). Replace it with a manifest-driven condition registry and fatal missing-output checks. The ScTagger component specifies historical replay versus a future path-independent generator.

6. **The historical RAGE replicate driver reuses a single target list.** `scripts/run_figure_3.sh:70` supplies the same `RAGESEQ_DUMMY_WL` in all three iterations. `_lib.sh:74` defaults to `rageseq_dummy_bcs_v1.csv`. That does not reproduce three independently sampled lists. Recover exact executed lists where possible; otherwise label a newly sampled experiment as a replacement. Do not invent historical seeds. Also resolve the old harness's `10x_3v1` chemistry against retained current RAGE evidence.

7. **The timing and spatial branches are not current complete pipelines.** `run_figure_4.sh:39–54` runs old scMixology timing; its HD section (`:105–108`) says the triptych is generated separately. The revised runner must parse measured logs and actually invoke the selected HD renderer. `verify_fig4.R:25–27` assigns hard-coded timing/memory values; this is not a check of a new execution.

8. **Removed workflows can still be run by default.** `run_figure_5.sh` executes NBC/clonotype analysis and loops over a pooled spatial FASTQ (`:79`). That is neither current Figure 5 nor evidence that the eight benchmark libraries were run separately. Remove these branches from the current build; retain historical code and the eight-library benchmark's own native input manifest.

9. **External helper dependencies are unresolved.** Figure 2, 3 and 5 notebooks source `PROJECT_SCRIPTS` even where copies of those helpers are tracked. `_lib.sh:85` needs `extract_rad_headers_new.sh`, which is not in this repository. Some optional IgBLAST helpers produce warnings rather than a failed build. Vendor/version necessary current helpers, record external data separately, and eliminate dependencies on an author's working directory. The renderer also needs an explicit dependency lock including packages omitted from the main list (for example the HD renderer imports `viridis`, `patchwork`, and `ggprism`).

10. **Verification is mostly reporting, and is not part of the build.** `verify_fig2.R:6` returns the text `MISMATCH` instead of failing. `verify_fig3.R:31–36` chooses the top 4,036 barcodes to mimic an old whitelist. `verify_fig4.R` checks constants for runtime. The top-level runner does not invoke these scripts. Retain historical reference numbers as comparison data, then implement schema, identity, conservation and statistical checks that fail with nonzero status. Never truncate or tune output solely to recover a historical claim.

11. **The data-source documentation is incomplete.** README says accessions are in `misc/rad_demux_commands.md`; that file mainly contains historical paths and partially reconstructed commands. Replace this claim with the complete source registry and accession mappings in this handoff's context. `data/README.md` also has `figures/figures/figure_4/` twice and a broken `../rad_demux_commands.md` link. Correct both.

12. **Publication metadata is stale.** README labels the manuscript v9/pre-submission and figures v7; CITATION calls the paper “in preparation.” Update these against the final revision and verified identifiers, without making up a journal DOI or archive DOI.

## Zenodo: verified current state

Public API checked on 23 October 2026: https://zenodo.org/api/records/20189813. The response and the public page are saved under `audit/`. This is a **published, open** record titled “RAD manuscript, R workspaces for figure generation,” not the private draft described by GitHub. Its description covers the older Figures 2–5.

The API's DOI field is **`10.64898/2026.05.29.728810`**, the preprint DOI. GitHub instead claims reserved DOI `10.5281/zenodo.20189813`. Reconcile the record's identifier and related-publication metadata before updating citations. Do not assume a Zenodo DOI merely from the numeric record ID. Use the verified record URL in interim documentation.

| Published file | Bytes | Zenodo MD5 |
|---|---:|---|
| `figure_2_workspace.RData` | 507,559,669 | `06d145b074b05fbfdde13724f1bf4ed2` |
| `figure_3_workspace.RData` | 2,159,314,542 | `385e7d3f4c558d5ea4320ff5cef3b7c2` |
| `figure_4_workspace.RData` | 465,251,189 | `69cb1f8316678bebddb5917f9f2143bb` |
| `figure_5_workspace.RData` | 3,062,509,018 | `312b2d42e54baab630c5522a2693ed0d` |

Total: **6,194,634,418 bytes**. File contents were not downloaded or loaded during this audit. The repository additionally provides SHA-256 digests; verify both after HPC download. Import each workspace into its own empty R environment, index objects/classes/dimensions/key fields, and identify which current panels still use them. The archive currently exposes whole-session R workspaces, not a documented series of resumable checkpoints. A revised release must include explicit table/matrix schemas and stage manifests.

Preserve the published historical archive. Prepare the revised dataset/code release and metadata for author review. Uploading/publishing or changing repository visibility is a separate release action; no such change was made here.

## Verification boundary

This audit examined repository code, retained project notes, selected small tables/manifests, file availability and public Zenodo metadata. Shell syntax checks are recorded in `audit/shell_syntax_checks.json`. It did not execute the old full pipelines, load the four public R workspaces, rerun computational benchmarks, or verify Prism's native rendering/statistics. The per-figure component files distinguish retained checkpoints from reconstructed steps and missing upstream material.
