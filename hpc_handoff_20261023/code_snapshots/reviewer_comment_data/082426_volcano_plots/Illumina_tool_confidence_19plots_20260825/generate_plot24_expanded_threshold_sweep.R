#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(ggplot2)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 2L) {
  stop("usage: generate_plot24_expanded_threshold_sweep.R [PLOT23_DATA.tsv.gz] [OUTPUT_ROOT]")
}

script_args <- commandArgs(trailingOnly = FALSE)
script_path <- sub("^--file=", "", script_args[grepl("^--file=", script_args)][1L])
default_root <- normalizePath(dirname(script_path), mustWork = TRUE)
root <- if (length(args) >= 2L) args[[2L]] else default_root
input_path <- if (length(args) >= 1L) args[[1L]] else file.path(
  root,
  "23_Illumina_vs_RAD_BLAZE_Flexiplex_all_genes_spearman_plot_data.tsv.gz"
)
input_path <- normalizePath(input_path, mustWork = TRUE)
dir.create(root, recursive = TRUE, showWarnings = FALSE)

tools <- c("RAD", "BLAZE", "Flexiplex")
fdr_grid <- c(1e-8, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1)
log2fc_grid <- c(0.10, 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00, 2.50, 3.00)
truth_fdr <- 0.05
truth_abs_log2fc <- 1.00
current_fdr <- 0.05
current_abs_log2fc <- 1.00
canonical_plot_root <- paste0(
  "/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/",
  "082426_volcano_plots/Illumina_tool_confidence_19plots_20260825"
)
canonical_plot23_data <- file.path(
  canonical_plot_root,
  "23_Illumina_vs_RAD_BLAZE_Flexiplex_all_genes_spearman_plot_data.tsv.gz"
)
canonical_plot23_manifest <- file.path(
  canonical_plot_root,
  "23_Illumina_vs_RAD_BLAZE_Flexiplex_all_genes_SOURCE_INPUT_SHA256.tsv"
)

fdr_label <- function(x) {
  fifelse(
    x < 1e-3,
    formatC(x, format = "e", digits = 0),
    sprintf("%.3f", x)
  )
}

d <- fread(cmd = sprintf("gzip -dc %s", shQuote(input_path)))
required <- c(
  "gene_id", "tool", "tool_log2FC", "tool_BH_FDR_common",
  "Illumina_log2FC", "Illumina_BH_FDR_common"
)
stopifnot(all(required %in% names(d)))
d <- d[tool %in% tools]
stopifnot(nrow(d) == 3L * 8135L)
stopifnot(!anyDuplicated(d[, .(tool, gene_id)]))
gene_sets <- lapply(tools, function(tool_i) sort(d[tool == tool_i, gene_id]))
stopifnot(identical(gene_sets[[1L]], gene_sets[[2L]]), identical(gene_sets[[1L]], gene_sets[[3L]]))

grid <- CJ(
  tool = tools,
  tool_BH_FDR_cutoff = fdr_grid,
  tool_abs_log2FC_cutoff = log2fc_grid,
  unique = TRUE
)

score_one <- function(tool_i, fdr_i, fc_i) {
  z <- d[tool == tool_i]
  truth <- z$Illumina_BH_FDR_common < truth_fdr &
    z$Illumina_log2FC < -truth_abs_log2fc
  predicted <- z$tool_BH_FDR_common < fdr_i & z$tool_log2FC < -fc_i
  tp <- sum(truth & predicted)
  fp <- sum(!truth & predicted)
  fn <- sum(truth & !predicted)
  tn <- sum(!truth & !predicted)
  precision <- if ((tp + fp) > 0L) tp / (tp + fp) else 0
  recall <- if ((tp + fn) > 0L) tp / (tp + fn) else 0
  f1 <- if ((2L * tp + fp + fn) > 0L) 2L * tp / (2L * tp + fp + fn) else 0
  list(
    genes = nrow(z),
    truth_positive = sum(truth),
    predicted_positive = sum(predicted),
    TP = tp,
    FP = fp,
    FN = fn,
    TN = tn,
    precision = precision,
    recall = recall,
    F1 = f1
  )
}

scores <- grid[, score_one(tool, tool_BH_FDR_cutoff, tool_abs_log2FC_cutoff),
  by = .(tool, tool_BH_FDR_cutoff, tool_abs_log2FC_cutoff)
]
scores[, is_current :=
  tool_BH_FDR_cutoff == current_fdr &
  tool_abs_log2FC_cutoff == current_abs_log2fc
]
scores[, is_best_in_grid := F1 == max(F1), by = tool]
scores[, FDR_label := fdr_label(tool_BH_FDR_cutoff)]
scores[, log2FC_label := sprintf("%.2f", tool_abs_log2FC_cutoff)]
scores[, display_label := sprintf("%.3f", F1)]
scores[is_current == TRUE, display_label := paste0(display_label, "\nCURRENT")]
scores[is_best_in_grid == TRUE & is_current == FALSE, display_label := paste0(display_label, "\nBEST")]

fdr_labels <- fdr_label(fdr_grid)
scores[, FDR_factor := factor(FDR_label, levels = rev(fdr_labels))]
scores[, log2FC_factor := factor(
  log2FC_label,
  levels = sprintf("%.2f", log2fc_grid)
)]
scores[, tool := factor(tool, levels = tools)]

p <- ggplot(scores, aes(log2FC_factor, FDR_factor, fill = F1)) +
  geom_tile(color = "white", linewidth = 0.65) +
  geom_text(aes(label = display_label), color = "#202124", fontface = "bold", size = 3.0, lineheight = 0.88) +
  geom_tile(
    data = scores[is_current == TRUE],
    fill = NA,
    color = "black",
    linewidth = 1.15
  ) +
  geom_tile(
    data = scores[is_best_in_grid == TRUE & is_current == FALSE],
    fill = NA,
    color = "#006D5B",
    linewidth = 1.0,
    linetype = "dashed"
  ) +
  facet_wrap(~tool, nrow = 1) +
  scale_fill_viridis_c(option = "C", direction = -1, limits = c(0, 1), name = "F1") +
  labs(
    title = "H526-high F1 threshold sweep versus fixed Illumina truth",
    x = expression("Tool |" * log[2] * " fold change| cutoff"),
    y = "Tool BH FDR cutoff"
  ) +
  theme_bw(base_size = 12) +
  theme(
    plot.title = element_text(face = "bold", size = 18),
    strip.text = element_text(face = "bold", size = 14),
    panel.grid = element_blank(),
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "right"
  )

stem <- "24_H526_high_F1_threshold_sweep_RAD_BLAZE_Flexiplex"
ggsave(
  file.path(root, paste0(stem, ".png")), p,
  device = ragg::agg_png, width = 24, height = 11.5, dpi = 300, bg = "white"
)
ggsave(
  file.path(root, paste0(stem, ".svg")), p,
  device = svglite::svglite, width = 24, height = 11.5, bg = "white"
)

scores_out <- copy(scores)
scores_out[, `:=`(
  tool = as.character(tool),
  FDR_factor = NULL,
  log2FC_factor = NULL
)]
scores_out[, display_label := gsub("\n", " / ", display_label, fixed = TRUE)]
setorder(scores_out, tool, tool_BH_FDR_cutoff, tool_abs_log2FC_cutoff)
fwrite(scores_out, file.path(root, paste0(stem, "_expanded_grid.tsv")), sep = "\t")

best <- scores_out[is_best_in_grid == TRUE, .(
  tool,
  tool_BH_FDR_cutoff,
  tool_abs_log2FC_cutoff,
  F1,
  precision,
  recall,
  TP,
  FP,
  FN,
  truth_positive,
  predicted_positive
)]
setorder(best, tool, -F1, tool_BH_FDR_cutoff, tool_abs_log2FC_cutoff)
fwrite(best, file.path(root, paste0(stem, "_best_thresholds.tsv")), sep = "\t")

source_paths <- c(
  plot23_data = canonical_plot23_data,
  plot23_source_manifest = canonical_plot23_manifest
)
stopifnot(
  identical(
    unname(tools::md5sum(input_path)),
    unname(tools::md5sum(canonical_plot23_data))
  )
)
source_manifest <- rbindlist(lapply(names(source_paths), function(role_i) {
  path_i <- normalizePath(source_paths[[role_i]], mustWork = TRUE)
  sha_i <- strsplit(system2("sha256sum", path_i, stdout = TRUE), "[[:space:]]+")[[1L]][[1L]]
  data.table(
    role = role_i,
    path = path_i,
    sha256 = sha_i,
    bytes = file.info(path_i)$size
  )
}))
fwrite(source_manifest, file.path(root, paste0(stem, "_SOURCE_INPUT_SHA256.tsv")), sep = "\t")

message(sprintf(
  "complete: genes=%d truth=%d grid=%dx%d cells=%d current F1 %s; best F1 %s",
  unique(scores_out$genes),
  unique(scores_out$truth_positive),
  length(fdr_grid),
  length(log2fc_grid),
  nrow(scores_out),
  paste(sprintf("%s=%.6f", scores_out[is_current == TRUE, tool], scores_out[is_current == TRUE, F1]), collapse = ", "),
  paste(sprintf("%s=%.6f", best$tool, best$F1), collapse = ", ")
))
