suppressPackageStartupMessages({
  library(data.table)
})


SAMPLES <- c("PBC44593", "PBC44760", "PBC49262", "PBC52788")

# ------------------------------------------------------------------
# Per-sample counts and bin classes
# ------------------------------------------------------------------
counts <- fread("supp_fig4_counts.csv")
setnames(counts, "RAD only",    "RAD_only")
setnames(counts, "Seurat only", "Seurat_only")
counts[, total_RAD := Both + RAD_only]
counts[, total_Seurat := Both + Seurat_only]
counts[, pct_double_pos_of_RAD := 100 * Both / total_RAD]

cat("=== Per-sample counts ===\n")
print(counts[, .(sample, Both, RAD_only, Seurat_only,
                 total_RAD, total_Seurat,
                 recovery_pct = round(recovery_pct, 3),
                 pct_double_pos_of_RAD = round(pct_double_pos_of_RAD, 2))])

# ------------------------------------------------------------------
# Ranges across the 4 samples
# ------------------------------------------------------------------
range_fmt <- function(x, digits = 0) {
  sprintf("%s to %s (mean %s)",
          format(round(min(x), digits), big.mark = ","),
          format(round(max(x), digits), big.mark = ","),
          format(round(mean(x), digits), big.mark = ","))
}

cat("\n=== Cross-sample ranges ===\n")
cat("Total valid RAD bins per sample : ", range_fmt(counts$total_RAD), "\n")
cat("Double-positive (Both) per samp : ", range_fmt(counts$Both), "\n")
cat("Single-positive RAD per sample  : ", range_fmt(counts$RAD_only), "\n")
cat("Missed by RAD (Seurat only)     : ", range_fmt(counts$Seurat_only), "\n")
cat("Recovery % of Seurat bins        : ",
    sprintf("%.2f%% to %.2f%% (mean %.2f%%)\n",
            min(counts$recovery_pct), max(counts$recovery_pct),
            mean(counts$recovery_pct)))
cat("Max Seurat_only across samples  : ", max(counts$Seurat_only), "\n")

# ------------------------------------------------------------------
# Single-positive RAD values inside double-positive range
# Use per-sample log1p(ncpm) from the prism_violin wide CSVs.
# ------------------------------------------------------------------
overlap_dt <- rbindlist(lapply(SAMPLES, function(s) {
  d <- fread(file.path("prism_violin",
                       sprintf("%s_log1p_ncpm_by_class.csv", s)),
             na.strings = c("", "NA"))
  tp <- d$TP[!is.na(d$TP)]
  fp <- d$FP[!is.na(d$FP)]
  tp_min <- min(tp); tp_max <- max(tp)
  inside <- fp >= tp_min & fp <= tp_max
  data.table(sample      = s,
             n_RAD_only  = length(fp),
             tp_min      = tp_min,
             tp_max      = tp_max,
             fp_min      = min(fp),
             fp_max      = max(fp),
             n_inside    = sum(inside),
             pct_inside  = 100 * mean(inside))
}))

cat("\n=== Single-positive RAD inside double-positive range ===\n")
print(overlap_dt[, .(sample, n_RAD_only,
                     tp_min = round(tp_min, 3),
                     tp_max = round(tp_max, 3),
                     fp_min = round(fp_min, 3),
                     fp_max = round(fp_max, 3),
                     pct_inside = round(pct_inside, 2))])
cat(sprintf("Pct inside across samples: %.2f%% to %.2f%% (mean %.2f%%)\n",
            min(overlap_dt$pct_inside),
            max(overlap_dt$pct_inside),
            mean(overlap_dt$pct_inside)))

# Pooled across samples
all_tp <- unlist(lapply(SAMPLES, function(s) {
  d <- fread(file.path("prism_violin",
                       sprintf("%s_log1p_ncpm_by_class.csv", s)),
             na.strings = c("", "NA"))
  d$TP[!is.na(d$TP)]
}))
all_fp <- unlist(lapply(SAMPLES, function(s) {
  d <- fread(file.path("prism_violin",
                       sprintf("%s_log1p_ncpm_by_class.csv", s)),
             na.strings = c("", "NA"))
  d$FP[!is.na(d$FP)]
}))
pooled_tp_min <- min(all_tp); pooled_tp_max <- max(all_tp)
pooled_inside <- all_fp >= pooled_tp_min & all_fp <= pooled_tp_max
cat(sprintf("\nPooled: TP range = [%.3f, %.3f], %.2f%% of all single-positive RAD (n=%d) inside\n",
            pooled_tp_min, pooled_tp_max, 100 * mean(pooled_inside),
            length(all_fp)))

# ------------------------------------------------------------------
# Cross-sample Pearson r (off-diagonal)
# ------------------------------------------------------------------
corr <- fread("raw_data/sample_correlations_16um.csv")
off  <- corr[a != b]
cat("\n=== Cross-sample Pearson r (in-tissue, RAD log1p(ncpm)) ===\n")
print(off[, .(a, b, pearson_log1p_intissue = round(pearson_log1p_intissue, 5))])
cat(sprintf("Off-diagonal r (n=%d pairs): %.4f to %.4f (mean %.4f, median %.4f)\n",
            nrow(off), min(off$pearson_log1p_intissue),
            max(off$pearson_log1p_intissue),
            mean(off$pearson_log1p_intissue),
            median(off$pearson_log1p_intissue)))

# ------------------------------------------------------------------
# Save summary file
# ------------------------------------------------------------------
summary_lines <- c(
  "metric,value",
  sprintf("samples,%d", nrow(counts)),
  sprintf("total_valid_RAD_bins_range,%d-%d", min(counts$total_RAD), max(counts$total_RAD)),
  sprintf("total_valid_RAD_bins_mean,%.0f", mean(counts$total_RAD)),
  sprintf("double_positive_bins_range,%d-%d", min(counts$Both), max(counts$Both)),
  sprintf("double_positive_bins_mean,%.0f", mean(counts$Both)),
  sprintf("single_positive_RAD_range,%d-%d", min(counts$RAD_only), max(counts$RAD_only)),
  sprintf("single_positive_RAD_mean,%.0f", mean(counts$RAD_only)),
  sprintf("seurat_only_range,%d-%d", min(counts$Seurat_only), max(counts$Seurat_only)),
  sprintf("seurat_only_max,%d", max(counts$Seurat_only)),
  sprintf("recovery_pct_range,%.2f-%.2f", min(counts$recovery_pct), max(counts$recovery_pct)),
  sprintf("recovery_pct_mean,%.2f", mean(counts$recovery_pct)),
  sprintf("pct_single_pos_RAD_inside_double_pos_range_per_sample_min,%.2f", min(overlap_dt$pct_inside)),
  sprintf("pct_single_pos_RAD_inside_double_pos_range_per_sample_max,%.2f", max(overlap_dt$pct_inside)),
  sprintf("pct_single_pos_RAD_inside_double_pos_range_per_sample_mean,%.2f", mean(overlap_dt$pct_inside)),
  sprintf("pct_single_pos_RAD_inside_double_pos_range_pooled,%.2f", 100 * mean(pooled_inside)),
  sprintf("pearson_r_offdiag_range,%.4f-%.4f", min(off$pearson_log1p_intissue), max(off$pearson_log1p_intissue)),
  sprintf("pearson_r_offdiag_mean,%.4f", mean(off$pearson_log1p_intissue)),
  sprintf("pearson_r_offdiag_median,%.4f", median(off$pearson_log1p_intissue))
)
writeLines(summary_lines, "supp_fig4_paragraph_stats.csv")
cat("\nWrote supp_fig4_paragraph_stats.csv\n")

# Also write the per-sample detailed overlap table
fwrite(overlap_dt, "supp_fig4_overlap_per_sample.csv")
cat("Wrote supp_fig4_overlap_per_sample.csv\n")
