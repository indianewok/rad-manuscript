library(data.table)
library(ggplot2)
library(ggpubr)

# ============================================================================
# PR curves for RAD generate_whitelist vs BLAZE on ScTagger L (5000 true BCs)
# ============================================================================

# --- Load ground truth ---
sctagger_truth <- Sys.getenv("SCTAGGER_TRUTH",
                             unset = file.path(Sys.getenv("RAW_FQ"), "sctagger_sim/truth"))
if (!dir.exists(sctagger_truth)) {
  stop("SCTAGGER_TRUTH not found at: ", sctagger_truth,
       " — set SCTAGGER_TRUTH (or RAW_FQ) in your shell env (see README.md → Setup)")
}
truth <- fread(
  cmd = sprintf("gzip -dc %s", shQuote(file.path(sctagger_truth, "L.truth.tsv.gz"))),
  header = FALSE, col.names = c("read_idx", "barcode")
)
truth_bcs <- unique(truth$barcode)
cat("Truth barcodes:", length(truth_bcs), "\n")

# --- RAD: load scored candidates ---
rad <- fread("/tmp/test_wl_L.csv")
rad[, is_true := barcode %in% truth_bcs]
# Score: use ncpm (higher = more likely a real cell)
# For PR curve, we threshold on ncpm: at each unique ncpm value, compute
# precision and recall if we call all barcodes with ncpm >= that threshold
rad_thresholds <- sort(unique(rad$ncpm), decreasing = FALSE)
rad_pr <- rbindlist(lapply(rad_thresholds, function(thr) {
  called <- rad[ncpm >= thr]
  tp <- sum(called$is_true)
  fp <- sum(!called$is_true)
  prec <- tp / (tp + fp)
  rec <- tp / length(truth_bcs)
  data.table(precision = prec, recall = rec, threshold = thr)
}))
# Add the (0, 1) anchor for the start of the curve (very high threshold, 0 recall)
rad_pr <- rbind(data.table(precision = 1, recall = 0, threshold = max(rad$ncpm) + 1), rad_pr)
rad_pr[, tool := "RAD"]

# --- BLAZE: aggregate putative_bc.csv to per-barcode counts ---
blaze_raw <- fread("/tmp/blaze_test_L/putative_bc.csv", select = c("putative_bc"))
blaze_counts <- blaze_raw[, .N, by = putative_bc]
setnames(blaze_counts, c("barcode", "count"))
blaze_counts[, is_true := barcode %in% truth_bcs]

# Same threshold sweep on barcode count
blaze_thresholds <- sort(unique(blaze_counts$count), decreasing = FALSE)
blaze_pr <- rbindlist(lapply(blaze_thresholds, function(thr) {
  called <- blaze_counts[count >= thr]
  tp <- sum(called$is_true)
  fp <- sum(!called$is_true)
  prec <- tp / (tp + fp)
  rec <- tp / length(truth_bcs)
  data.table(precision = prec, recall = rec, threshold = thr)
}))
blaze_pr <- rbind(data.table(precision = 1, recall = 0, threshold = max(blaze_counts$count) + 1), blaze_pr)
blaze_pr[, tool := "BLAZE"]

# --- Compute AUC-PR (trapezoidal) ---
auc_pr <- function(dt) {
  dt <- dt[order(recall)]
  sum(diff(dt$recall) * (head(dt$precision, -1) + tail(dt$precision, -1)) / 2)
}
rad_auc <- auc_pr(rad_pr)
blaze_auc <- auc_pr(blaze_pr)
cat(sprintf("AUC-PR  RAD: %.4f  BLAZE: %.4f\n", rad_auc, blaze_auc))

# --- Combine and plot ---
pr_data <- rbindlist(list(rad_pr, blaze_pr))

# Downsample for plotting (keep all points near interesting regions)
set.seed(42)
pr_plot <- pr_data[, {
  if (.N > 2000) {
    idx <- sort(unique(c(1, .N, seq(1, .N, length.out = 2000))))
    .SD[idx]
  } else {
    .SD
  }
}, by = tool]

p <- ggplot(pr_plot, aes(x = recall, y = precision, color = tool)) +
  geom_line(linewidth = 1) +
  scale_color_manual(
    values = c("RAD" = "#2166AC", "BLAZE" = "#B2182B"),
    labels = c(
      sprintf("RAD (AUC = %.3f)", rad_auc),
      sprintf("BLAZE (AUC = %.3f)", blaze_auc)
    )
  ) +
  labs(
    x = "Recall (Sensitivity)",
    y = "Precision",
    title = "Precision-Recall: Whitelist Detection on ScTagger L (5,000 true barcodes)",
    color = NULL
  ) +
  coord_cartesian(xlim = c(0, 1), ylim = c(0, 1)) +
  theme_pubr() +
  theme(legend.position = c(0.3, 0.2))

ggsave(
  "pr_curve_sctagger_L.pdf",
  plot = p, width = 7, height = 5
)
ggsave(
  "pr_curve_sctagger_L.png",
  plot = p, width = 7, height = 5, dpi = 300
)

cat("Saved pr_curve_sctagger_L.pdf and .png\n")

# --- Print key threshold points ---
cat("\n--- RAD at final_barcode=TRUE threshold ---\n")
rad_final <- rad[final_barcode == "TRUE"]
cat(sprintf("  Threshold ncpm: %.3f\n", min(rad_final$ncpm)))
cat(sprintf("  Barcodes called: %d\n", nrow(rad_final)))
cat(sprintf("  TP: %d  FP: %d\n", sum(rad_final$is_true), sum(!rad_final$is_true)))

cat("\n--- BLAZE at whitelist threshold ---\n")
blaze_wl <- fread("/tmp/blaze_test_L/whitelist.csv", header = FALSE, col.names = "barcode")
blaze_wl[, is_true := barcode %in% truth_bcs]
cat(sprintf("  Barcodes called: %d\n", nrow(blaze_wl)))
cat(sprintf("  TP: %d  FP: %d\n", sum(blaze_wl$is_true), sum(!blaze_wl$is_true)))
