#!/usr/bin/env Rscript
# Figure 3 manuscript claim verification (v2)
# Compares fresh RAD/BLAZE/Flexiplex vs saved workspace + manuscript claims.
# RAD autogen WL built by taking top-N barcodes by total_count from global WL.
#
# Run from this script's directory: `cd figure_3/ && Rscript verify_fig3.R`.
# Path inputs are resolved from these env vars (documented in README.md → Setup):
#   PROJECT_SCRIPTS, RAGESEQ_FULL_WL, RESULTS_BASE, FLEXIPLEX_RESULTS

suppressMessages({
  library(data.table)
  library(rad)
})

env_required <- function(name) {
  val <- Sys.getenv(name)
  if (val == "") stop(name, " env var not set — see README.md → Setup")
  val
}

cat("Loading figure_3_workspace.RData...\n")
load("figure_3_workspace.RData")
source(file.path(env_required("PROJECT_SCRIPTS"), "process_extracted_headers.R"))

# --- TRUTH SOURCES ---
full_wl   <- fread(Sys.getenv("RAGESEQ_FULL_WL",
                              unset = file.path(env_required("WL_DIR"), "rageseq_full_bcs.csv")))$barcode
filt_wl   <- rageseq_true$barcode

# --- FRESH RAD R1 WL (autogen, knee-thresholded) ---
# In original workflow, rad_rsq_counts had 4036 BCs — use top-N=4036 as the autogen WL
cat("\n=== RAD R1 autogen WL (top-4036 by count) ===\n")
rad_global <- fread(file.path(env_required("RESULTS_BASE"),
                              "rageseq/regen_260420/r1_autogen/rsq_whitelist_global.csv"))
setorder(rad_global, -total_count)
rad_fresh_wl_4036 <- rad_global[1:4036, true_barcode]
cat("RAD fresh WL (top-4036): n =", length(rad_fresh_wl_4036), "\n")

# Also compare at top-saved-size for precise match
N_saved <- nrow(rad_rsq_counts)
rad_fresh_wl_saved <- rad_global[1:N_saved, true_barcode]

# --- BLAZE B1 WL ---
blaze_b1_wl <- fread("/tmp/b1_whitelist.csv", header = FALSE)$V1
cat("BLAZE B1 WL: n =", length(blaze_b1_wl), "\n")

# --- BLAZE B2 HS WL (if available) ---
blaze_b2_wl <- NULL
if (file.exists("/tmp/b2_whitelist.csv") && file.size("/tmp/b2_whitelist.csv") > 0) {
  blaze_b2_wl <- fread("/tmp/b2_whitelist.csv", header = FALSE)$V1
  cat("BLAZE B2 HS WL: n =", length(blaze_b2_wl), "\n")
}

# --- Flexiplex F1 WL ---
flex_f1_file <- file.path(env_required("FLEXIPLEX_RESULTS"),
                          "rageseq/regen_260420/f1_autogen/rsq_filtered_whitelist.txt")
flex_lines <- readLines(flex_f1_file)
flex_f1_wl <- character(0)
for (ln in flex_lines) {
  parts <- strsplit(ln, "\t")[[1]]
  if (length(parts) == 2 && nchar(parts[1]) == 16 && grepl("^[ACGT]+$", parts[1]))
    flex_f1_wl <- c(flex_f1_wl, parts[1])
}
cat("Flexiplex F1 WL: n =", length(flex_f1_wl), "\n")

# --- PASS/MISMATCH TRACKER ---
results <- data.table(claim=character(), expected=character(), actual=character(), status=character())
record <- function(claim, expected, actual, tolerance = 0) {
  exp_num <- suppressWarnings(as.numeric(expected))
  act_num <- suppressWarnings(as.numeric(actual))
  ok <- if (!is.na(exp_num) && !is.na(act_num)) abs(exp_num - act_num) <= tolerance
        else identical(as.character(expected), as.character(actual))
  status <- if (ok) "OK" else "MISMATCH"
  results <<- rbind(results, data.table(claim=claim, expected=as.character(expected),
                                         actual=as.character(actual), status=status))
}

# ====== 3B — Detection rates (fresh) ======
cat("\n=== 3B — Detection rates (fresh) ===\n")
rad_full <- 100 * sum(rad_fresh_wl_4036 %in% full_wl) / length(full_wl)
rad_filt <- 100 * sum(rad_fresh_wl_4036 %in% filt_wl) / length(filt_wl)
bz_full  <- 100 * sum(blaze_b1_wl %in% full_wl) / length(full_wl)
bz_filt  <- 100 * sum(blaze_b1_wl %in% filt_wl) / length(filt_wl)
fx_full  <- 100 * sum(flex_f1_wl %in% full_wl) / length(full_wl)
fx_filt  <- 100 * sum(flex_f1_wl %in% filt_wl) / length(filt_wl)
cat(sprintf("RAD   (n=%d): full=%.2f%% | filt=%.2f%%  (claim 87.3 / 91.4)\n", length(rad_fresh_wl_4036), rad_full, rad_filt))
cat(sprintf("BLAZE (n=%d): full=%.2f%% | filt=%.2f%%  (claim 63.6 / 67.9)\n", length(blaze_b1_wl),      bz_full, bz_filt))
cat(sprintf("FLEX  (n=%d): full=%.2f%% | filt=%.2f%%  (Flexiplex not in manuscript text)\n", length(flex_f1_wl), fx_full, fx_filt))
record("3B RAD / full WL (87.3%)",   "87.3", sprintf("%.1f", rad_full), tolerance = 0.5)
record("3B RAD / filt WL (91.4%)",   "91.4", sprintf("%.1f", rad_filt), tolerance = 0.5)
record("3B BLAZE / full WL (63.6%)", "63.6", sprintf("%.1f", bz_full),  tolerance = 0.5)
record("3B BLAZE / filt WL (67.9%)", "67.9", sprintf("%.1f", bz_filt),  tolerance = 0.5)

# BLAZE HS claims
if (!is.null(blaze_b2_wl)) {
  hs_tp_gain <- sum(blaze_b2_wl %in% full_wl) - sum(blaze_b1_wl %in% full_wl)
  fp_b1 <- sum(!blaze_b1_wl %in% full_wl)
  fp_b2 <- sum(!blaze_b2_wl %in% full_wl)
  fp_gain <- fp_b2 - fp_b1
  cat(sprintf("\nBLAZE HS: +%d BCs from full (claim +433); default FPs=%d (claim 91); HS FPs=%d; +FPs=%d (claim +1259)\n",
              hs_tp_gain, fp_b1, fp_b2, fp_gain))
  record("3B BLAZE HS +BCs (433)",    "433",  as.character(hs_tp_gain), tolerance = 30)
  record("3B BLAZE default FPs (91)", "91",   as.character(fp_b1),      tolerance = 20)
  record("3B BLAZE HS +FPs (1,259)",  "1259", as.character(fp_gain),    tolerance = 50)
} else {
  cat("\n[BLAZE B2 HS WL not yet available]\n")
}

# ====== Fresh vs saved WL consistency ======
cat("\n=== Fresh vs saved WL overlap ===\n")
saved_rad_bcs <- unique(rad_rsq_counts$barcode)
ovl_rad <- length(intersect(rad_fresh_wl_saved, saved_rad_bcs))
cat(sprintf("RAD (top-%d): overlap with saved (%d) = %d (%.1f%%)\n",
            N_saved, length(saved_rad_bcs), ovl_rad, 100*ovl_rad/length(saved_rad_bcs)))
ovl_bz <- length(intersect(blaze_b1_wl, blaze_rsq_counts$barcode))
cat(sprintf("BLAZE:         overlap with saved (%d) = %d (%.1f%%)\n",
            length(unique(blaze_rsq_counts$barcode)), ovl_bz,
            100*ovl_bz/length(unique(blaze_rsq_counts$barcode))))
record("RAD fresh top-N matches saved count", as.character(length(saved_rad_bcs)), as.character(length(rad_fresh_wl_saved)))
record("BLAZE fresh == saved",                 "2955", as.character(length(blaze_b1_wl)))

# ====== 3H Missed ======
rad_miss <- sum(!filt_wl %in% rad_fresh_wl_4036)
bz_miss  <- sum(!filt_wl %in% blaze_b1_wl)
cat(sprintf("\n3H Missed: RAD=%d (claim 339); BLAZE=%d (claim 1,257)\n", rad_miss, bz_miss))
record("3H Missed RAD (339)",     "339",  as.character(rad_miss), tolerance = 30)
record("3H Missed BLAZE (1,257)", "1257", as.character(bz_miss),  tolerance = 50)

# ====== 3G/3H/3I (saved workspace — mapping-bound, cannot rebuild from headers alone) ======
cat("\n=== 3G/3H/3I verified against saved workspace ===\n")
cells_rad <- nrow(rad_rsq_counts[in_sr == TRUE])
cells_bz  <- nrow(blaze_rsq_counts[in_sr == TRUE])
record("3G RAD cells (3,574)",   "3574", as.character(cells_rad))
record("3G BLAZE cells (2,656)", "2656", as.character(cells_bz))

rad_ct <- rad_rsq_counts[in_sr == TRUE, .N, by = cell_types]
bz_ct  <- blaze_rsq_counts[in_sr == TRUE, .N, by = cell_types]
record("3H RAD Jurkat (1,570)",   "1570", as.character(rad_ct[cell_types=="Jurkat", N]))
record("3H RAD Ramos (1,993)",    "1993", as.character(rad_ct[cell_types=="Ramos", N]))
record("3H RAD Mono (11)",        "11",   as.character(rad_ct[cell_types=="Monocytes", N]))
record("3H BLAZE Jurkat (1,085)", "1085", as.character(bz_ct[cell_types=="Jurkat", N]))
record("3H BLAZE Ramos (1,559)",  "1559", as.character(bz_ct[cell_types=="Ramos", N]))
record("3H BLAZE Mono (12)",      "12",   as.character(bz_ct[cell_types=="Monocytes", N]))

# 3I — on shared_bcs subset (cells in BOTH tools' output)
shared_rad <- rad_rsq_counts[barcode %in% shared_bcs]
shared_bz  <- blaze_rsq_counts[barcode %in% shared_bcs]
r_ramos_diff <- mean(shared_rad[cell_types=="Ramos", total_cts])  - mean(shared_bz[cell_types=="Ramos", total_cts])
r_jurk_diff  <- mean(shared_rad[cell_types=="Jurkat", total_cts]) - mean(shared_bz[cell_types=="Jurkat", total_cts])
record("3I Ramos reads/cell diff (+232)", "232", sprintf("%.0f", r_ramos_diff), tolerance = 5)
record("3I Jurkat reads/cell diff (+180)", "180", sprintf("%.0f", r_jurk_diff), tolerance = 5)

# 3J
record("3J Ramos cells (409)",  "409", as.character(nrow(subset_filtered_ct_rsq[cell_types=="Ramos"])))
record("3J Jurkat cells (764)", "764", as.character(nrow(subset_filtered_ct_rsq[cell_types=="Jurkat"])))

d <- high_stringency_total_rsq_data
bcr_ramos_diff <- sum(d[demux=="rad"   & cell_types=="Ramos",  mapped_bcr]) -
                  sum(d[demux=="blaze" & cell_types=="Ramos",  mapped_bcr])
tcr_jurk_diff  <- sum(d[demux=="rad"   & cell_types=="Jurkat", mapped_tcr]) -
                  sum(d[demux=="blaze" & cell_types=="Jurkat", mapped_tcr])
record("3J BCR Ramos diff (+59,661)", "59661", as.character(bcr_ramos_diff), tolerance = 500)
record("3J TCR Jurkat diff (+49,002)", "49002", as.character(tcr_jurk_diff), tolerance = 500)

# ====== FINAL REPORT ======
cat("\n\n========== FIGURE 3 — Verification Table ==========\n")
print(results[, .(claim, expected, actual, status)], nrows = 100)
n_ok <- sum(results$status == "OK")
cat(sprintf("\n%d / %d claims match (within tolerance).\n", n_ok, nrow(results)))
if (any(results$status == "MISMATCH")) {
  cat("\nMISMATCH details:\n")
  print(results[status == "MISMATCH"])
}

# Save to file
fwrite(results, "/tmp/fig3_verify_results.csv")
cat("\nResults saved to /tmp/fig3_verify_results.csv\n")
