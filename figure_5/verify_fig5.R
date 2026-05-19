#!/usr/bin/env Rscript
# Figure 5 — manuscript claim verification
# Run from this script's directory: `cd figure_5/ && Rscript verify_fig5.R`.
suppressMessages(library(data.table))
cat("Loading figure_5_workspace.RData...\n")
load("figure_5_workspace.RData"); cat("Done.\n")

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

# ====== 10,744 B-cell clones ======
cat("\n=== 10,744 B-cell clones ===\n")
n_clones <- nrow(per_clone_id_spots)
record("Total B-cell clones (10,744)", "10744", as.character(n_clones))

# ====== 620 class-switching clones (5.8%) ======
cat("\n=== 620 class-switching clones (5.8%) ===\n")
n_switch <- nrow(multiple_clones)
pct_switch <- 100 * n_switch / n_clones
record("Class-switching clones (620)", "620", as.character(n_switch))
record("Class-switching pct (5.8%)", "5.8", sprintf("%.1f", pct_switch), tolerance = 0.1)

# Heatmaps are in wide format: cols are barcode + isotypes
# ====== Clone 2277 ======
cat("\n=== Clone 2277 ===\n")
h <- clone_2277_heatmap
cat("cols:", paste(names(h), collapse=", "), "\n")
record("Clone 2277 barcodes (61)", "61", as.character(nrow(h)))
iso_bcs_2277 <- sapply(setdiff(names(h), "barcode"), function(c) sum(h[[c]] > 0))
print(iso_bcs_2277)
# Manuscript text labels these as 'reads' but they are actually barcodes expressing each isotype
if ("IGHM"  %in% names(iso_bcs_2277)) record("Clone 2277 IGHM barcodes (33 [mislabeled 'reads'])",  "33", as.character(iso_bcs_2277["IGHM"]))
if ("IGHG2" %in% names(iso_bcs_2277)) record("Clone 2277 IGHG2 barcodes (26 [mislabeled 'reads'])", "26", as.character(iso_bcs_2277["IGHG2"]))

# ====== Clone 5725 ======
cat("\n=== Clone 5725 ===\n")
h <- clone_5725_heatmap
cat("cols:", paste(names(h), collapse=", "), "\n")
record("Clone 5725 barcodes (61)", "61", as.character(nrow(h)), tolerance = 1)
iso_bcs_5725 <- sapply(setdiff(names(h), "barcode"), function(c) sum(h[[c]] > 0))
print(iso_bcs_5725)
if ("IGHG3" %in% names(iso_bcs_5725)) record("Clone 5725 IGHG3 barcodes (34)", "34", as.character(iso_bcs_5725["IGHG3"]))
if ("IGHG1" %in% names(iso_bcs_5725)) record("Clone 5725 IGHG1 barcodes (28)", "28", as.character(iso_bcs_5725["IGHG1"]))

# ====== Clone 7445 ======
cat("\n=== Clone 7445 ===\n")
h <- clone_7445_heatmap
cat("cols:", paste(names(h), collapse=", "), "\n")
record("Clone 7445 barcodes (37)", "37", as.character(nrow(h)))
iso_bcs_7445 <- sapply(setdiff(names(h), "barcode"), function(c) sum(h[[c]] > 0))
print(iso_bcs_7445)

# ====== Final report ======
cat("\n\n========== FIGURE 5 — Verification Table ==========\n")
print(results[, .(claim, expected, actual, status)], nrows = 100)
n_ok <- sum(results$status == "OK")
cat(sprintf("\n%d / %d claims match (within tolerance).\n", n_ok, nrow(results)))
if (any(results$status == "MISMATCH")) {
  cat("\nMISMATCH details:\n")
  print(results[status == "MISMATCH"])
}
fwrite(results, "/tmp/fig5_verify_results.csv")
cat("\nResults saved to /tmp/fig5_verify_results.csv\n")
