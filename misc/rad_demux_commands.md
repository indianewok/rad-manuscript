# RAD Demux Commands per Dataset

This document catalogs the `rad demux` commands used to generate the demultiplexed data for the RAD paper, organized by dataset and figure.

All paths below use environment variables documented in [../README.md](../README.md) → Setup. Key vars:
- `${RAD_BIN}`, `${GEN_WL_BIN}` — RAD binaries
- `${RAW_FQ}` — root of raw input FASTQs
- `${WL_DIR}` — barcode whitelist directory
- `${RESULTS_BASE}` — root of demultiplexed output
- `${RAD_RESOURCES}` — RAD source-tree resources (read layouts, kit defs)

---

## Figure 2: Benchmarking (Synthetic/ScTagger Data)

### ScTagger L Simulation
```bash
# Location: ${RESULTS_BASE}/synthetic_data/121325_sctagger_L_sim/
# Layout: sctag_lr_layout.csv (22bp primer + 16bp barcode + 10bp UMI + poly-A)
# Whitelist: ${SCTAGGER_GEN_WL} (10x_3v3)
# Note: Exact command.txt not stored; reconstructed from layout/position_map files.
# Earlier debug run at: 121225_sctagger_L_sim_dbg/
```

### ScTagger WL (Whitelist detection run)
```bash
# Location: ${RESULTS_BASE}/synthetic_data/100725_rad_sctagger_wl/
# Layout: sctag_lr_layout.csv
# Whitelist: ${SCTAGGER_GEN_WL} (10x_3v3)
```

**Note:** ScTagger S and M simulation commands were not found in stored logs. These may have been run interactively or from the R API.

---

## Figure 3: RAGEseq Real Data Comparison

### RAGEseq (Total + Analysis)
```bash
# Location: ${RESULTS_BASE}/rageseq/101325_rsq_tot_and_analysis/
# Layout: rsq_layout.csv (22bp primer + 16bp barcode + 10bp UMI + poly-T + read + 23bp rev primer)
# Whitelist format: 10x_3v1
# Whitelist: ${RAGESEQ_WL}
```

### RAGEseq (Global WL)
```bash
# Location: ${RESULTS_BASE}/rageseq/102125_rsq_global_wl/
# Layout: rsq_layout.csv
# Whitelist: ${RAGESEQ_WL} (10x_3v1)
```

### False Positive Whitelist Tests (Figure 3 supplemental)
```bash
# Location: ${RESULTS_BASE}/false_positive_wl/
# Runs: 082825_rad_fp1, 082825_rad_fp2, 082825_rad_fp3
# Layout: rsq_layout.csv (same as RAGEseq)
# Whitelist: ${RAGESEQ_DUMMY_WL} (10x_3v1)
```

---

## Figure 4: Multi-platform Demonstration

### scMixology2 (3 Timing Runs)
```bash
# Location: ${RESULTS_BASE}/scmixology2/
# Runs: 102125_scmix_timing_run_r1, 102425_scmix_timing_run_r2, 102525_scmix_timing_run_r3
# Layout: scmix_layout.csv (22bp primer + 16bp barcode + 10bp UMI + poly-T + read + 23bp rev primer)
# Whitelist: ${SCMIX2_WL} (10x_3v3)
```

### Split-seq
```bash
# Location: ${RESULTS_BASE}/splitseq/
# Runs: 100325_rad_splitseq, 110425_splitseq
# Layout: split_lr_layout.csv (3-barcode structure: bc1 8bp + linker + bc2 8bp + linker + bc3 8bp + 10bp UMI)
# Whitelists: splitseq_bc1, splitseq_bc2 (custom)
```

### NBC BCR Data (Sans Whitelist)
```bash
"${RAD_BIN}" demux \
  -l five_prime \
  -q "${NBC_BCR_FQ}" \
  -t 4 \
  -d "${RESULTS_BASE}/sans_wl/nbc_sans" \
  -o nbc_sans \
  -v \
  -F "${RESULTS_BASE}/sans_wl/nbc_sans/nbc_sans_rad.log"
```

### NBC BCR Data (With Whitelist)
```bash
"${RAD_BIN}" demux \
  -l five_prime \
  -k 10x_5v1 \
  -c "${NBC_WL}" \
  -q "${NBC_BCR_FQ}" \
  -t 4 \
  -d "${RESULTS_BASE}/sans_wl/nbc_wl" \
  -o nbc_wl \
  -v \
  -F "${RESULTS_BASE}/sans_wl/nbc_wl/nbc_wl_rad.log"
```

### NBC BCR Data (custom layout, recent run)
```bash
"${RAD_BIN}" demux -t 4 -v \
  -l /path/to/nbc_layout.csv \
  -q "${NBC_BCR_FQ}" \
  -d /path/to/output/030426_nbc \
  -o nbc
```

### Visium HD Mouse Brain (panels 4I-4K + Supplementary Figure 1)

Public 10X Visium HD murine brain dataset, four replicate sections at 16 µm bin
resolution: `PBC44593`, `PBC44760`, `PBC49262`, `PBC52788`. Run per-sample:

```bash
"${RAD_BIN}" demux \
  -l "${RAD_RESOURCES}/read_layout/visium_hd_read_layout.csv" \
  -k 10x_3v3 \
  -q /path/to/{SAMPLE}.fq.gz \
  -t "$RAD_THREADS" \
  -d "${RESULTS_BASE}/visium_hd/{SAMPLE}" \
  -o {SAMPLE} \
  -v \
  -F "${RESULTS_BASE}/visium_hd/{SAMPLE}/{SAMPLE}_rad.log"
```

> *TODO:* the production command set used to generate
> `figures/supp_figure_1/raw_data/sample_bin_matrix_16um.csv.gz` (the source for
> both panels 4I-4K and Supplementary Figure 1) is not yet captured here.
> Backfill from the figure_4_visium working dir / conversation history.

---

## Figure 5: Clonal Analysis (NBC BCR + Engblom Tonsil Spatial)

Figure 5 uses the NBC BCR demultiplexed output (above) plus an 8-section Engblom
*et al.* Visium tonsil spatial dataset for the spatial clone maps in panels
5E + 5G. Downstream clonotyping is via IgBLAST and custom R pipelines (see
`${PROJECT_SCRIPTS}/rnabloom_to_igblast.sh`, `${PROJECT_SCRIPTS}/generate_ig_mappings.sh`).

### Engblom Visium tonsil spatial — 8 sections × 2 patients

```bash
# Location: ${RESULTS_BASE}/visium_data/
# Samples: pt072_bc1009, pt072_bc1010, pt072_bc1018, pt072_bc1020
#          pt086_bc1011, pt086_bc1016, pt086_bc1018, pt086_bc1020
# Layout: Standard Visium (22bp primer + 16bp barcode + 10bp UMI + poly-T + read + 23bp rev primer)
# Per-barcode whitelists from: ${VISIUM_WL_DIR}/
# Example: pt072_demultiplex_bc1009.txt
#
# Driven by scripts/run_figure_5.sh in the 8-section loop.
```

---

## Common Flag Reference

| Flag | Meaning |
|------|---------|
| `-l` | Read layout (built-in key or CSV path) |
| `-k` | Kit/whitelist type (e.g., `10x_3v3`, `10x_5v1`) |
| `-c` | Custom whitelist CSV path |
| `-q` | Input FASTQ (.fq.gz) |
| `-t` | Number of threads |
| `-n` | Max reads to process |
| `-d` | Output directory |
| `-o` | Output filename prefix |
| `-v` | Verbose mode |
| `-D` | Debug mode |
| `-F` | Log file path |
| `-A` | Aggressive mode (used in development/testing) |

---

## Data Sources

- **Command files:** `${RESULTS_BASE}/sans_wl/*/command.txt`
- **Layout files:** `*_layout.csv` in each run directory
- **Position maps:** `*_position_map.csv` in each run directory
- **Shell history & RStudio history** were also consulted when reconstructing the
  exact invocations above.
