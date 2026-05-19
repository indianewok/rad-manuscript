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

### Visium Spatial Data (8 Barcodes)
```bash
# Location: ${RESULTS_BASE}/visium_data/
# Samples: pt072_bc1009, pt072_bc1010, pt072_bc1018, pt072_bc1020
#          pt086_bc1011, pt086_bc1016, pt086_bc1018, pt086_bc1020
# Layout: Standard Visium (22bp primer + 16bp barcode + 10bp UMI + poly-T + read + 23bp rev primer)
# Per-barcode whitelists from: ${VISIUM_WL_DIR}/
# Example: pt072_demultiplex_bc1009.txt
```

### Visium HD
```bash
"${RAD_BIN}" demux \
  -l "${RAD_RESOURCES}/read_layout/visium_hd_read_layout.csv" \
  -n 1000000 \
  -v \
  -o /path/to/output/visium_hd_test_run \
  -t 4 \
  -q /path/to/input/022026_10XHD_rsq.fq.gz
```

---

## Figure 5: Clonal Analysis (Tonsil Data)

Figure 5 uses the NBC BCR and Visium spatial demultiplexed data (see Figure 4 commands above). Downstream clonotyping was done via IgBLAST and custom R pipelines (see `${PROJECT_SCRIPTS}/rnabloom_to_igblast.sh`, `${PROJECT_SCRIPTS}/generate_ig_mappings.sh`).

---

## Whitelist Detection / Sans-WL Benchmarking Runs

### LA1 (Default 10x 3' v3)
```bash
"${RAD_BIN}" demux \
  -l three_prime \
  -q "${LA1_FQ}" \
  -t 4 \
  -d "${RESULTS_BASE}/default_10x3v3" \
  -o la1 \
  -v \
  -F "${RESULTS_BASE}/default_10x3v3/la1_rad.log"
```

### LA2 Sans Whitelist
```bash
"${RAD_BIN}" demux \
  -l three_prime \
  -q "${LA2_FQ}" \
  -t 4 \
  -d "${RESULTS_BASE}/sans_wl/la2_sans" \
  -o la2_sans \
  -v \
  -F "${RESULTS_BASE}/sans_wl/la2_sans/la2_sans_rad.log"
```

### LA2 With Whitelist
```bash
"${RAD_BIN}" demux \
  -l three_prime \
  -k 10x_3v3 \
  -c "${LEENA_WL_DIR}/la2.txt" \
  -q "${LA2_FQ}" \
  -t 4 \
  -d "${RESULTS_BASE}/sans_wl/la2_wl" \
  -o la2_wl \
  -v \
  -F "${RESULTS_BASE}/sans_wl/la2_wl/la2_wl_rad.log"
```

### LA3 Sans Whitelist
```bash
"${RAD_BIN}" demux \
  -l three_prime \
  -q "${LA3_FQ}" \
  -t 4 \
  -d "${RESULTS_BASE}/sans_wl/la3_sans" \
  -o la3_sans \
  -v \
  -F "${RESULTS_BASE}/sans_wl/la3_sans/la3_sans_rad.log"
```

### LA3 With Whitelist
```bash
"${RAD_BIN}" demux \
  -l three_prime \
  -k 10x_3v3 \
  -c "${LEENA_WL_DIR}/la3.txt" \
  -q "${LA3_FQ}" \
  -t 4 \
  -d "${RESULTS_BASE}/sans_wl/la3_wl" \
  -o la3_wl \
  -v \
  -F "${RESULTS_BASE}/sans_wl/la3_wl/la3_wl_rad.log"
```

### LA1mem / LA3mem (Memory Tests)
```bash
# LA1mem sans WL
"${RAD_BIN}" demux \
  -l three_prime \
  -q "${LA1MEM_FQ}" \
  -t 4 \
  -d "${RESULTS_BASE}/sans_wl/la1mem_sans" \
  -o la1mem_sans -v \
  -F "${RESULTS_BASE}/sans_wl/la1mem_sans/la1mem_sans_rad.log"

# LA1mem with WL
"${RAD_BIN}" demux \
  -l three_prime -k 10x_3v3 \
  -c "${LEENA_WL_DIR}/la1_mem.txt" \
  -q "${LA1MEM_FQ}" \
  -t 4 \
  -d "${RESULTS_BASE}/sans_wl/la1mem_wl" \
  -o la1mem_wl -v \
  -F "${RESULTS_BASE}/sans_wl/la1mem_wl/la1mem_wl_rad.log"

# LA3mem sans WL
"${RAD_BIN}" demux \
  -l three_prime \
  -q "${LA3MEM_FQ}" \
  -t 4 \
  -d "${RESULTS_BASE}/sans_wl/la3mem_sans" \
  -o la3mem_sans -v \
  -F "${RESULTS_BASE}/sans_wl/la3mem_sans/la3mem_sans_rad.log"

# LA3mem with WL
"${RAD_BIN}" demux \
  -l three_prime -k 10x_3v3 \
  -c "${LEENA_WL_DIR}/la3_mem.txt" \
  -q "${LA3MEM_FQ}" \
  -t 4 \
  -d "${RESULTS_BASE}/sans_wl/la3mem_wl" \
  -o la3mem_wl -v \
  -F "${RESULTS_BASE}/sans_wl/la3mem_wl/la3mem_wl_rad.log"
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
