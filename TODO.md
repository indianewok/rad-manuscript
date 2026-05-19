# TODO

Open items for the RAD manuscript repository. Granular figure-polish notes (alignment, font sizes, individual panel cosmetics) live in `to_fix.txt` (gitignored) — this file tracks anything that affects the repo, the data, or someone else's ability to reproduce the work.

---

## Repo plumbing

- [ ] **Vendor `project_specific_scripts/` into this repo.** Today every Rmd resolves `Sys.getenv("PROJECT_SCRIPTS")` and dies if the env var is unset. Move the helpers (`process_extracted_headers.R`, `generate_sctagger_ids.R`, `graphing_*.R`, `comparing_visium_data.R`, `reformat_igblast_genes.R`, `consensus_ig_generator.R`, `extract_rad_headers_new.sh`, `rnabloom_to_igblast.sh`, `generate_ig_mappings.sh`) into a top-level `project_specific_scripts/` here and drop the env-var indirection in favor of a relative `../project_specific_scripts/` default.
- [ ] **Vendor or link `extract_rad_headers_new.sh`** — `scripts/run_figure_2.sh` errors loudly if `EXTRACT_HEADERS` is unset, but the script itself isn't in the repo yet.
- [ ] **End-to-end smoke test post-refactor.** Run `./scripts/run_figure_2.sh analysis` against the Zenodo workspace once external users start cloning, to confirm the env-var resolution chain works clean-room.
- [x] ~~**Compress `figures/figure_4/figure_4.pdf`**~~ — done in commit `9f8869a` (Ghostscript `/printer` profile, 35 MB → 22 MB).

---

## Manuscript / data

- [ ] **Upload the Visium HD mapping bundle to Zenodo** (or extend the existing draft). The supp_figure_1 scripts depend on `visium_hd_mouse_brain_016um_seurat.rds` (384 MB) + `tissue_positions_16um.csv` (full grid) at `$HD_MAPPING_DIR`; neither is in the repo. Document the download path in `data/README.md`.
- [ ] **Publish the Zenodo deposit** ([10.5281/zenodo.20189813](https://doi.org/10.5281/zenodo.20189813)) on manuscript acceptance — the DOI is reserved but the deposit is still a private draft.
- [ ] **Fill in `CITATION.cff`** post-acceptance: journal, DOI, volume/issue, year, `status: published`.
- [ ] **Flip the GitHub repo to public** on acceptance.
- [ ] **Rotate the Zenodo API token** — the previous token's literal value passed through a session transcript before rotation; the new one is in macOS Keychain and shell history. Revoke at zenodo.org/account/settings/applications/ after the upload completes.

---

## Figure science / methods (from `to_fix.txt`)

- [ ] **Fig 3I — recalc + replot as a delta bar.** `figures/figure_3/verify_fig3.R:136-139` already computes the mean-reads-per-cell delta on the shared-barcode subset (claim values +232 Ramos / +180 Jurkat). Replace the paired RAD/BLAZE bars with a single RAD−BLAZE delta bar per cell type; update y-axis label so the "3" character doesn't outsize the rest.
- [ ] **Fig 3D/E false-positive numbers** — resolve which reading of the HS-vs-default claim the manuscript text intends (`figures/figure_3/hs_fp_interpretation.R` flags reading A = "+1259 vs default" vs reading B = "1259 absolute"). Currently ambiguous.
- [ ] **Fig 3 supplemental** — move one of the two heatmaps from the main panel into supplemental.
- [ ] **Fig 5 panel polish** — label panel C, add the NBC label, add clone numbers to E, align vertical axes on C/E and B/D, shrink the all-caps font in E.
- [ ] **Citation fix** — "Wick et al." reference (Fig 2 caption); confirm spelling against source paper.
- [ ] **Tone down overly precise N's** throughout figure captions and panel annotations.
- [ ] **Global font-size pass** across all four figures.
