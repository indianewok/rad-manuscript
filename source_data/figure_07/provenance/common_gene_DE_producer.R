#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(Matrix)
  library(data.table)
  library(scran)
  library(BiocParallel)
  library(ggplot2)
  library(svglite)
  library(ragg)
  library(digest)
})

args <- commandArgs(trailingOnly = TRUE)
command <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", command[grepl("^--file=", command)])
if (length(script_arg) != 1L) stop("Could not resolve script path")
script_dir <- dirname(normalizePath(script_arg, mustWork = TRUE))
out_dir <- if (length(args)) {
  normalizePath(args[[1L]], mustWork = FALSE)
} else {
  script_dir
}
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

default_native_path <- paste0(
  "/scratch-nfs/f005f43/SN_ONT_direct_H146_H526_RAD4acbe00_CT_rerun_20260828/",
  "package/tables/direct_H146_vs_H526_all_deg_results.tsv.gz"
)
default_source_package <-
  "/scratch-nfs/f005f43/SN_ONT_H146_H526_DEG_RAD4acbe00_all_records_20260828"
native_path <- normalizePath(
  if (length(args) >= 2L) args[[2L]] else default_native_path,
  mustWork = TRUE
)
source_package <- normalizePath(
  if (length(args) >= 3L) args[[3L]] else default_source_package,
  mustWork = TRUE
)
matrix_path <- file.path(source_package, "inputs", "illumina_SN", "ill_sn_matrix.mtx.gz")
feature_path <- file.path(source_package, "inputs", "illumina_SN", "ill_sn_features.tsv.gz")
barcode_path <- file.path(source_package, "inputs", "illumina_SN", "ill_sn_barcodes.tsv.gz")
label_path <- file.path(source_package, "inputs", "labels", "Illumina_reference", "donor_ids.tsv")
stopifnot(all(file.exists(c(native_path, matrix_path, feature_path, barcode_path, label_path))))

direct_package <- normalizePath(file.path(dirname(native_path), ".."), mustWork = TRUE)
direct_sha_path <- normalizePath(file.path(direct_package, "SHA256SUMS"), mustWork = TRUE)
direct_complete_path <- normalizePath(file.path(direct_package, "COMPLETE"), mustWork = TRUE)
source_sha_path <- normalizePath(file.path(source_package, "SHA256SUMS"), mustWork = TRUE)
source_complete_path <- normalizePath(file.path(source_package, "COMPLETE"), mustWork = TRUE)

parse_sha_manifest <- function(path) {
  x <- readLines(path, warn = FALSE)
  data.table(
    checksum = sub("^([0-9a-f]{64})[[:space:]]+.*$", "\\1", x),
    relative_path = sub("^[0-9a-f]{64}[[:space:]]+\\*?", "", x)
  )
}
assert_upstream_member <- function(manifest_path, member_path, upstream_root) {
  manifest <- parse_sha_manifest(manifest_path)
  relative <- substring(member_path, nchar(upstream_root) + 2L)
  expected <- digest(file = member_path, algo = "sha256", serialize = FALSE)
  observed <- manifest[relative_path == relative, checksum]
  if (length(observed) != 1L || observed != expected) {
    stop("Upstream checksum membership failure: ", relative)
  }
}
assert_upstream_member(direct_sha_path, native_path, direct_package)
for (path in c(matrix_path, feature_path, barcode_path, label_path)) {
  assert_upstream_member(source_sha_path, normalizePath(path, mustWork = TRUE), source_package)
}

input_manifest <- data.table(
  role = c(
    "sealed_direct_H146_H526_table", "sealed_direct_SHA256SUMS", "sealed_direct_COMPLETE",
    "Illumina_matrix", "Illumina_features", "Illumina_barcodes", "Illumina_labels",
    "sealed_LongBench_SHA256SUMS", "sealed_LongBench_COMPLETE"
  ),
  source_path = c(
    native_path, direct_sha_path, direct_complete_path,
    matrix_path, feature_path, barcode_path, label_path,
    source_sha_path, source_complete_path
  )
)
input_manifest[, sha256 := vapply(source_path, function(path) {
  digest(file = path, algo = "sha256", serialize = FALSE)
}, character(1L))]
input_manifest[, bytes := file.info(source_path)$size]
input_manifest_path <- file.path(
  out_dir,
  "23_Illumina_vs_RAD_BLAZE_Flexiplex_all_genes_SOURCE_INPUT_SHA256.tsv"
)
fwrite(input_manifest, input_manifest_path, sep = "\t")

normalize_barcode <- function(x) sub("-[0-9]+$", "", x)

features <- fread(cmd = paste("gzip -cd", shQuote(feature_path)), header = FALSE)
setnames(features, 1L, "gene_id")
barcodes <- normalize_barcode(fread(
  cmd = paste("gzip -cd", shQuote(barcode_path)), header = FALSE
)[[1L]])
counts_full <- as(readMM(gzfile(matrix_path)), "CsparseMatrix")
stopifnot(nrow(counts_full) == nrow(features), ncol(counts_full) == length(barcodes))
rownames(counts_full) <- features$gene_id
colnames(counts_full) <- barcodes

labels <- fread(label_path)
labels[, barcode := normalize_barcode(cell)]
labels <- labels[donor_id %in% c("H146", "H526")]
idx <- match(labels$barcode, barcodes)
joined <- !is.na(idx)
labels <- labels[joined]
idx <- idx[joined]
pair_counts <- counts_full[, idx, drop = FALSE]
depth <- as.numeric(colSums(pair_counts))
positive <- depth > 0
labels <- labels[positive]
pair_counts <- pair_counts[, positive, drop = FALSE]
depth <- depth[positive]
stopifnot(ncol(pair_counts) == 458L)
stopifnot(identical(as.integer(table(labels$donor_id)[c("H146", "H526")]), c(263L, 195L)))

minimum_detected <- ceiling(0.01 * ncol(pair_counts))
eligible_ids <- rownames(pair_counts)[
  as.numeric(rowSums(pair_counts)) >= 10 &
    as.numeric(rowSums(pair_counts > 0)) >= minimum_detected
]
stopifnot(length(eligible_ids) == 9666L)

tool_order <- c("RAD", "BLAZE", "Flexiplex")
native <- fread(
  native_path,
  select = c(
    "cohort", "gene_id", "gene_symbol",
    "avg_log2FC_H146_vs_H526", "p_value"
  )
)
native <- native[cohort %in% tool_order]
tool_gene_sets <- lapply(tool_order, function(tool_arg) {
  native[cohort == tool_arg, gene_id]
})
common_ids <- sort(unique(Reduce(intersect, c(tool_gene_sets, list(eligible_ids)))))
stopifnot(length(common_ids) == 8135L)

common_counts <- pair_counts[match(common_ids, rownames(pair_counts)), , drop = FALSE]
rownames(common_counts) <- common_ids
norm_linear <- common_counts %*% Diagonal(x = 10000 / depth)
norm_log <- norm_linear
norm_log@x <- log2(norm_log@x + 1)

target <- labels$donor_id == "H146"
groups <- factor(labels$donor_id, levels = c("H526", "H146"))
pw <- pairwiseWilcox(
  norm_log,
  groups = groups,
  direction = "any",
  BPPARAM = SerialParam(progressbar = FALSE)
)
pair_index <- which(pw$pairs$first == "H146" & pw$pairs$second == "H526")
stopifnot(length(pair_index) == 1L)
illumina_stats <- as.data.table(pw$statistics[[pair_index]])
illumina <- data.table(
  gene_id = common_ids,
  Illumina_p_value = as.numeric(illumina_stats$p.value),
  Illumina_log2FC = log2(
    (as.numeric(rowMeans(norm_linear[, target, drop = FALSE])) + 0.1) /
      (as.numeric(rowMeans(norm_linear[, !target, drop = FALSE])) + 0.1)
  )
)
illumina[, Illumina_BH_FDR_common := p.adjust(Illumina_p_value, method = "BH")]
illumina[, Illumina_confidence := -log10(Illumina_BH_FDR_common)]

tool_stats <- native[gene_id %in% common_ids]
tool_stats[, tool_BH_FDR_common := p.adjust(p_value, method = "BH"), by = cohort]
tool_stats[, tool_confidence := -log10(tool_BH_FDR_common)]
setnames(tool_stats, "avg_log2FC_H146_vs_H526", "tool_log2FC")

plot_data <- merge(
  tool_stats[, .(
    tool = cohort,
    gene_id,
    gene_symbol,
    tool_log2FC,
    tool_p_value = p_value,
    tool_BH_FDR_common,
    tool_confidence
  )],
  illumina,
  by = "gene_id",
  sort = FALSE
)
plot_data[, tool := factor(tool, levels = tool_order)]
plot_data[, `:=`(
  Illumina_confidence_cap50 = pmin(Illumina_confidence, 50),
  tool_confidence_cap50 = pmin(tool_confidence, 50)
)]

stopifnot(nrow(plot_data) == 24405L)
stopifnot(all(plot_data[, .N, by = tool]$N == 8135L))
stopifnot(!anyDuplicated(plot_data[, .(tool, gene_id)]))
stopifnot(all(is.finite(plot_data$Illumina_confidence)))
stopifnot(all(is.finite(plot_data$tool_confidence)))
stopifnot(all(is.finite(plot_data$Illumina_log2FC)))
stopifnot(all(is.finite(plot_data$tool_log2FC)))
stopifnot(all(plot_data$Illumina_confidence_cap50 >= 0 & plot_data$Illumina_confidence_cap50 <= 50))
stopifnot(all(plot_data$tool_confidence_cap50 >= 0 & plot_data$tool_confidence_cap50 <= 50))

confidence_stats <- plot_data[, {
  capped_fit <- lm(tool_confidence_cap50 ~ Illumina_confidence_cap50)
  .(
    n_genes = .N,
    Spearman_rho = cor(Illumina_confidence, tool_confidence, method = "spearman"),
    Spearman_rho_capped = cor(
      Illumina_confidence_cap50,
      tool_confidence_cap50,
      method = "spearman"
    ),
    Pearson_r_capped = cor(
      Illumina_confidence_cap50,
      tool_confidence_cap50,
      method = "pearson"
    ),
    OLS_intercept_capped = unname(coef(capped_fit)[[1L]]),
    OLS_slope_capped = unname(coef(capped_fit)[[2L]]),
    Illumina_at_cap = sum(Illumina_confidence >= 50),
    tool_at_cap = sum(tool_confidence >= 50)
  )
}, by = tool]

log2fc_stats <- plot_data[, {
  fc_fit <- lm(tool_log2FC ~ Illumina_log2FC)
  .(
    n_genes = .N,
    Spearman_rho = cor(Illumina_log2FC, tool_log2FC, method = "spearman"),
    Pearson_r = cor(Illumina_log2FC, tool_log2FC, method = "pearson"),
    OLS_intercept = unname(coef(fc_fit)[[1L]]),
    OLS_slope = unname(coef(fc_fit)[[2L]])
  )
}, by = tool]

stopifnot(nrow(confidence_stats) == 3L, nrow(log2fc_stats) == 3L)
stopifnot(identical(as.character(confidence_stats$tool), tool_order))
stopifnot(identical(as.character(log2fc_stats$tool), tool_order))
stopifnot(all(confidence_stats$n_genes == length(common_ids)))
stopifnot(all(log2fc_stats$n_genes == length(common_ids)))
correlation_fields <- c(
  confidence_stats$Spearman_rho,
  confidence_stats$Spearman_rho_capped,
  confidence_stats$Pearson_r_capped,
  log2fc_stats$Spearman_rho,
  log2fc_stats$Pearson_r
)
stopifnot(all(is.finite(correlation_fields)))
stopifnot(all(abs(correlation_fields) <= 1))
stopifnot(all(is.finite(c(
  confidence_stats$OLS_intercept_capped,
  confidence_stats$OLS_slope_capped,
  log2fc_stats$OLS_intercept,
  log2fc_stats$OLS_slope
))))

confidence_stats[, metric := "BH-FDR confidence"]
log2fc_stats[, metric := "log2FC"]
correlation_table <- rbindlist(list(
  confidence_stats[, .(
    metric,
    tool,
    n_genes,
    Spearman_rho,
    Pearson_r = Pearson_r_capped,
    OLS_intercept = OLS_intercept_capped,
    OLS_slope = OLS_slope_capped,
    Spearman_rho_capped,
    Illumina_at_cap,
    tool_at_cap
  )],
  log2fc_stats[, .(
    metric,
    tool,
    n_genes,
    Spearman_rho,
    Pearson_r,
    OLS_intercept,
    OLS_slope,
    Spearman_rho_capped = NA_real_,
    Illumina_at_cap = NA_integer_,
    tool_at_cap = NA_integer_
  )]
), use.names = TRUE)

confidence_stats[, label := sprintf("Spearman rho (uncapped) = %.3f", Spearman_rho)]
log2fc_stats[, label := sprintf("Spearman rho = %.3f", Spearman_rho)]

tool_colors <- c(RAD = "#009E73", BLAZE = "#000000", Flexiplex = "#191970")
threshold <- -log10(0.05)

p_confidence <- ggplot(
  plot_data,
  aes(Illumina_confidence_cap50, tool_confidence_cap50, color = tool)
) +
  geom_abline(
    slope = 1,
    intercept = 0,
    color = "#777C83",
    linewidth = 0.50,
    linetype = "longdash"
  ) +
  geom_vline(
    xintercept = threshold,
    color = "#9A9FA6",
    linewidth = 0.32,
    linetype = "dotted"
  ) +
  geom_hline(
    yintercept = threshold,
    color = "#9A9FA6",
    linewidth = 0.32,
    linetype = "dotted"
  ) +
  geom_point(size = 0.80, alpha = 0.34, stroke = 0) +
  geom_smooth(
    method = "lm",
    formula = y ~ x,
    se = FALSE,
    fullrange = TRUE,
    linewidth = 0.86,
    linetype = "solid"
  ) +
  geom_label(
    data = confidence_stats,
    aes(x = 2.1, y = 47.9, label = label),
    inherit.aes = FALSE,
    hjust = 0,
    vjust = 1,
    size = 3.25,
    color = "#202124",
    fill = scales::alpha("white", 0.90),
    linewidth = 0.25
  ) +
  facet_wrap(~tool, nrow = 1) +
  scale_color_manual(values = tool_colors, guide = "none") +
  coord_fixed(
    ratio = 1,
    xlim = c(0, 50),
    ylim = c(0, 50),
    expand = FALSE,
    clip = "on"
  ) +
  labs(
    title = paste0(
      "Illumina versus RAD, BLAZE, and Flexiplex BH-FDR confidence ",
      "(display capped at 50)"
    ),
    x = expression("Illumina " * -log[10] * "(BH FDR), capped at 50"),
    y = expression("Tool " * -log[10] * "(BH FDR), capped at 50")
  ) +
  theme_bw(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 15, hjust = 0),
    plot.subtitle = element_blank(),
    plot.caption = element_blank(),
    strip.background = element_rect(
      fill = "#F2F3F5",
      color = "#4A4A4A",
      linewidth = 0.4
    ),
    strip.text = element_text(face = "bold", size = 12),
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(color = "#E8EAED", linewidth = 0.28),
    panel.spacing = grid::unit(1.60, "lines"),
    plot.margin = margin(9, 10, 9, 9)
  )

fc_axis_limit <- ceiling(max(abs(c(plot_data$Illumina_log2FC, plot_data$tool_log2FC))))
stopifnot(is.finite(fc_axis_limit), fc_axis_limit > 0)

p_log2fc <- ggplot(plot_data, aes(Illumina_log2FC, tool_log2FC, color = tool)) +
  geom_abline(
    slope = 1,
    intercept = 0,
    color = "#777C83",
    linewidth = 0.50,
    linetype = "longdash"
  ) +
  geom_vline(
    xintercept = 0,
    color = "#9A9FA6",
    linewidth = 0.32,
    linetype = "dotted"
  ) +
  geom_hline(
    yintercept = 0,
    color = "#9A9FA6",
    linewidth = 0.32,
    linetype = "dotted"
  ) +
  geom_point(size = 0.80, alpha = 0.34, stroke = 0) +
  geom_smooth(
    method = "lm",
    formula = y ~ x,
    se = FALSE,
    fullrange = TRUE,
    linewidth = 0.86,
    linetype = "solid"
  ) +
  geom_label(
    data = log2fc_stats,
    aes(
      x = -0.94 * fc_axis_limit,
      y = 0.94 * fc_axis_limit,
      label = label
    ),
    inherit.aes = FALSE,
    hjust = 0,
    vjust = 1,
    size = 3.25,
    color = "#202124",
    fill = scales::alpha("white", 0.90),
    linewidth = 0.25
  ) +
  facet_wrap(~tool, nrow = 1) +
  scale_color_manual(values = tool_colors, guide = "none") +
  coord_fixed(
    ratio = 1,
    xlim = c(-fc_axis_limit, fc_axis_limit),
    ylim = c(-fc_axis_limit, fc_axis_limit),
    expand = FALSE,
    clip = "on"
  ) +
  labs(
    title = "Illumina versus RAD, BLAZE, and Flexiplex H146-vs-H526 log2FC",
    x = expression("Illumina log"[2] * " fold change (H146/H526)"),
    y = expression("Tool log"[2] * " fold change (H146/H526)")
  ) +
  theme_bw(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 15, hjust = 0),
    plot.subtitle = element_blank(),
    plot.caption = element_blank(),
    strip.background = element_rect(
      fill = "#F2F3F5",
      color = "#4A4A4A",
      linewidth = 0.4
    ),
    strip.text = element_text(face = "bold", size = 12),
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(color = "#E8EAED", linewidth = 0.28),
    panel.spacing = grid::unit(1.60, "lines"),
    plot.margin = margin(9, 10, 9, 9)
  )

confidence_stem <- paste0(
  "23_Illumina_vs_RAD_BLAZE_Flexiplex_all_genes_",
  "confidence_cap50_spearman"
)
log2fc_stem <- paste0(
  "23_Illumina_vs_RAD_BLAZE_Flexiplex_all_genes_",
  "log2FC_spearman"
)

ggsave(
  file.path(out_dir, paste0(confidence_stem, ".svg")),
  p_confidence,
  width = 15.5,
  height = 6.25,
  units = "in",
  device = svglite::svglite,
  bg = "white"
)
ggsave(
  file.path(out_dir, paste0(confidence_stem, ".png")),
  p_confidence,
  width = 15.5,
  height = 6.25,
  units = "in",
  dpi = 300,
  device = ragg::agg_png,
  bg = "white"
)
ggsave(
  file.path(out_dir, paste0(log2fc_stem, ".svg")),
  p_log2fc,
  width = 15.5,
  height = 6.25,
  units = "in",
  device = svglite::svglite,
  bg = "white"
)
ggsave(
  file.path(out_dir, paste0(log2fc_stem, ".png")),
  p_log2fc,
  width = 15.5,
  height = 6.25,
  units = "in",
  dpi = 300,
  device = ragg::agg_png,
  bg = "white"
)

fwrite(
  plot_data,
  file.path(
    out_dir,
    "23_Illumina_vs_RAD_BLAZE_Flexiplex_all_genes_spearman_plot_data.tsv.gz"
  ),
  sep = "\t"
)
fwrite(
  correlation_table,
  file.path(
    out_dir,
    "23_Illumina_vs_RAD_BLAZE_Flexiplex_all_genes_spearman_correlations.tsv"
  ),
  sep = "\t"
)

expected_outputs <- file.path(out_dir, c(
  paste0(confidence_stem, c(".png", ".svg")),
  paste0(log2fc_stem, c(".png", ".svg")),
  "23_Illumina_vs_RAD_BLAZE_Flexiplex_all_genes_spearman_plot_data.tsv.gz",
  "23_Illumina_vs_RAD_BLAZE_Flexiplex_all_genes_spearman_correlations.tsv",
  basename(input_manifest_path)
))
stopifnot(all(file.exists(expected_outputs)))
stopifnot(all(file.info(expected_outputs)$size > 0))

message(sprintf(
  paste0(
    "complete: common=%d rows=%d fc_axis_limit=%g; confidence Spearman: %s; ",
    "log2FC Spearman: %s"
  ),
  length(common_ids),
  nrow(plot_data),
  fc_axis_limit,
  paste(
    sprintf("%s=%.12f", confidence_stats$tool, confidence_stats$Spearman_rho),
    collapse = "; "
  ),
  paste(
    sprintf("%s=%.12f", log2fc_stats$tool, log2fc_stats$Spearman_rho),
    collapse = "; "
  )
))
