#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(data.table)
  library(ggplot2)
  library(patchwork)
  library(grid)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 1L) stop("usage: generate_combined_figures.R [PACKAGE_ROOT]")

script_args <- commandArgs(trailingOnly = FALSE)
script_path <- sub("^--file=", "", script_args[grepl("^--file=", script_args)][1L])
default_root <- normalizePath(file.path(dirname(script_path), ".."), mustWork = TRUE)
root <- if (length(args) == 1L) normalizePath(args[[1L]], mustWork = TRUE) else default_root
figures_dir <- file.path(root, "figures")
dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)

ova_input_path <- file.path(root, "inputs", "directional_F1_threshold_sweep_grid.tsv")
direct_input_path <- file.path(root, "inputs", "direct_H146_vs_H526_plot_data.tsv.gz")
tools <- c("RAD", "BLAZE", "Flexiplex")
ova_contrasts <- c("H146_vs_rest", "H526_vs_rest")
ova_directions <- c("low", "high")
direct_directions <- c("H526_high", "H146_high")
fdr_grid <- c(1e-8, 1e-6, 1e-5, 1e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1)
log2fc_grid <- c(0.10, 0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00, 2.50, 3.00)
truth_fdr <- 0.05
truth_abs_log2fc <- 1.00
reference_fdr <- 0.05
reference_abs_log2fc <- 1.00
palettes <- c(H146 = "C", H526 = "D")

figure_stems <- c(
  "01_H146_low_high_combined_3tools_F1_threshold_sweep",
  "02_H526_low_high_combined_3tools_F1_threshold_sweep",
  "03_H526_high_H146_high_direct_side_by_side_3tools_F1_threshold_sweep"
)

fdr_label <- function(x) {
  fifelse(x < 1e-3, formatC(x, format = "e", digits = 0), sprintf("%.3f", x))
}

sha256_file <- function(path) {
  strsplit(
    system2("sha256sum", normalizePath(path, mustWork = TRUE), stdout = TRUE),
    "[[:space:]]+"
  )[[1L]][[1L]]
}

add_plot_labels <- function(z) {
  z <- copy(z)
  z[, `:=`(
    tool = factor(tool, levels = tools),
    FDR_factor = factor(fdr_label(tool_BH_FDR_cutoff), levels = rev(fdr_label(fdr_grid))),
    plot_label = sprintf("%.3f", F1)
  )]
  z[is_reference == TRUE & is_best_in_grid == FALSE,
    plot_label := paste0(plot_label, "\nREF")]
  z[is_reference == FALSE & is_best_in_grid == TRUE,
    plot_label := paste0(plot_label, "\nBEST")]
  z[is_reference == TRUE & is_best_in_grid == TRUE,
    plot_label := paste0(plot_label, "\nREF/BEST")]
  z
}

heatmap_layers <- function(z) {
  list(
    geom_tile(color = "white", linewidth = 0.55),
    geom_text(
      aes(label = plot_label), color = "#202124", fontface = "bold",
      size = 2.25, lineheight = 0.84
    ),
    geom_tile(
      data = z[is_reference == TRUE], fill = NA, color = "black", linewidth = 1.05
    ),
    geom_tile(
      data = z[is_best_in_grid == TRUE & is_reference == FALSE],
      fill = NA, color = "#006D5B", linewidth = 0.95, linetype = "dashed"
    )
  )
}

combined_theme <- function() {
  theme_bw(base_size = 11) +
    theme(
      plot.title = element_text(face = "bold", size = 17),
      plot.subtitle = element_text(size = 10.5),
      strip.text.x = element_text(face = "bold", size = 12),
      strip.text.y.left = element_text(face = "bold", size = 11, angle = 0),
      strip.placement = "outside",
      panel.grid = element_blank(),
      panel.spacing = unit(0.8, "lines"),
      axis.text.x = element_text(angle = 45, hjust = 1, size = 8.5),
      axis.text.y = element_text(size = 8.5),
      legend.position = "right"
    )
}

save_figure <- function(plot, stem, width = 18, height = 24) {
  ggsave(
    file.path(figures_dir, paste0(stem, ".png")), plot,
    device = ragg::agg_png, width = width, height = height, dpi = 300, bg = "white"
  )
  ggsave(
    file.path(figures_dir, paste0(stem, ".svg")), plot,
    device = svglite::svglite, width = width, height = height, bg = "white"
  )
}

# Figures 1 and 2: validated one-versus-all scores, shown with signed axes.
ova <- fread(ova_input_path)
ova_required <- c(
  "contrast", "direction", "tool", "tool_BH_FDR_cutoff",
  "tool_abs_log2FC_cutoff", "genes", "truth_positive", "precision", "recall",
  "F1", "is_reference", "is_best_in_grid"
)
stopifnot(all(ova_required %in% names(ova)))
stopifnot(nrow(ova) == 1188L)
stopifnot(!anyDuplicated(ova[, .(
  contrast, direction, tool, tool_BH_FDR_cutoff, tool_abs_log2FC_cutoff
)]))
stopifnot(setequal(ova$contrast, ova_contrasts))
stopifnot(setequal(ova$direction, ova_directions))
stopifnot(setequal(ova$tool, tools))
stopifnot(setequal(ova$tool_BH_FDR_cutoff, fdr_grid))
stopifnot(setequal(ova$tool_abs_log2FC_cutoff, log2fc_grid))
stopifnot(all(ova$genes == 12206L))

prepare_ova_plot_data <- function(z, labels, label_levels) {
  z <- add_plot_labels(z)
  signed_labels <- ifelse(
    z$direction == "low",
    sprintf("-%.2f", z$tool_abs_log2FC_cutoff),
    sprintf("%.2f", z$tool_abs_log2FC_cutoff)
  )
  signed_levels <- c(
    sprintf("-%.2f", rev(log2fc_grid)),
    sprintf("%.2f", log2fc_grid)
  )
  z[, `:=`(
    signed_log2FC_factor = factor(signed_labels, levels = signed_levels),
    column_label = factor(as.character(labels), levels = label_levels)
  )]
  z
}

make_low_high_figure <- function(contrast_i) {
  cell_line <- sub("_vs_rest$", "", contrast_i)
  z <- ova[contrast == contrast_i]
  truth_counts <- unique(z[, .(direction, truth_positive)])
  truth_map <- setNames(truth_counts$truth_positive, truth_counts$direction)
  label_levels <- c(
    sprintf("Low (Illumina truth n = %s)", format(truth_map[["low"]], big.mark = ",")),
    sprintf("High (Illumina truth n = %s)", format(truth_map[["high"]], big.mark = ","))
  )
  labels <- ifelse(z$direction == "low", label_levels[[1L]], label_levels[[2L]])
  z <- prepare_ova_plot_data(z, labels, label_levels)

  ggplot(z, aes(signed_log2FC_factor, FDR_factor, fill = F1)) +
    heatmap_layers(z) +
    facet_grid(
      rows = vars(tool), cols = vars(column_label), switch = "y",
      scales = "free_x", space = "free_x"
    ) +
    scale_fill_viridis_c(
      option = unname(palettes[[cell_line]]), direction = -1,
      limits = c(0, 1), name = "F1"
    ) +
    labs(
      title = sprintf("%s versus all: low and high F1 threshold sweeps", cell_line),
      subtitle = paste0(
        "Rows are tools; left is target-low (negative cutoff), right is target-high (positive cutoff). ",
        "Black = reference; dashed teal = best in grid."
      ),
      x = expression("Tool signed " * log[2] * " fold-change cutoff"),
      y = "Tool BH FDR cutoff"
    ) +
    combined_theme()
}

p_h146 <- make_low_high_figure("H146_vs_rest")
p_h526 <- make_low_high_figure("H526_vs_rest")
save_figure(p_h146, figure_stems[[1L]])
save_figure(p_h526, figure_stems[[2L]])

# Figure 3: recomputed direct H146-versus-H526 scores in both high directions.
direct_data <- fread(cmd = sprintf("gzip -dc %s", shQuote(direct_input_path)))
direct_required <- c(
  "gene_id", "tool", "tool_log2FC", "tool_BH_FDR_common",
  "Illumina_log2FC", "Illumina_BH_FDR_common"
)
stopifnot(all(direct_required %in% names(direct_data)))
direct_data <- direct_data[tool %in% tools]
stopifnot(nrow(direct_data) == 3L * 8135L)
stopifnot(!anyDuplicated(direct_data[, .(tool, gene_id)]))
direct_gene_sets <- lapply(tools, function(tool_i) sort(direct_data[tool == tool_i, gene_id]))
stopifnot(
  identical(direct_gene_sets[[1L]], direct_gene_sets[[2L]]),
  identical(direct_gene_sets[[1L]], direct_gene_sets[[3L]])
)

direct_grid <- CJ(
  direction = direct_directions,
  tool = tools,
  tool_BH_FDR_cutoff = fdr_grid,
  tool_abs_log2FC_cutoff = log2fc_grid,
  unique = TRUE
)

score_direct <- function(direction_i, tool_i, fdr_i, fc_i) {
  z <- direct_data[tool == tool_i]
  if (direction_i == "H526_high") {
    truth <- z$Illumina_BH_FDR_common < truth_fdr &
      z$Illumina_log2FC < -truth_abs_log2fc
    predicted <- z$tool_BH_FDR_common < fdr_i & z$tool_log2FC < -fc_i
  } else if (direction_i == "H146_high") {
    truth <- z$Illumina_BH_FDR_common < truth_fdr &
      z$Illumina_log2FC > truth_abs_log2fc
    predicted <- z$tool_BH_FDR_common < fdr_i & z$tool_log2FC > fc_i
  } else {
    stop(sprintf("unknown direct direction: %s", direction_i))
  }
  tp <- sum(truth & predicted)
  fp <- sum(!truth & predicted)
  fn <- sum(truth & !predicted)
  tn <- sum(!truth & !predicted)
  precision <- if ((tp + fp) > 0L) tp / (tp + fp) else 0
  recall <- if ((tp + fn) > 0L) tp / (tp + fn) else 0
  f1 <- if ((2L * tp + fp + fn) > 0L) 2L * tp / (2L * tp + fp + fn) else 0
  list(
    contrast = "H146_vs_H526_direct", genes = nrow(z),
    truth_positive = sum(truth), predicted_positive = sum(predicted),
    TP = tp, FP = fp, FN = fn, TN = tn,
    precision = precision, recall = recall, F1 = f1
  )
}

direct_scores <- direct_grid[, score_direct(
  direction, tool, tool_BH_FDR_cutoff, tool_abs_log2FC_cutoff
), by = .(direction, tool, tool_BH_FDR_cutoff, tool_abs_log2FC_cutoff)]
setcolorder(direct_scores, c(
  "contrast", "direction", "tool", "tool_BH_FDR_cutoff", "tool_abs_log2FC_cutoff",
  "genes", "truth_positive", "predicted_positive", "TP", "FP", "FN", "TN",
  "precision", "recall", "F1"
))
direct_scores[, is_reference :=
  tool_BH_FDR_cutoff == reference_fdr &
  tool_abs_log2FC_cutoff == reference_abs_log2fc]
direct_scores[, is_best_in_grid := F1 == max(F1), by = .(direction, tool)]
direct_scores[, `:=`(
  FDR_label = fdr_label(tool_BH_FDR_cutoff),
  log2FC_label = sprintf("%.2f", tool_abs_log2FC_cutoff),
  display_label = sprintf("%.3f", F1)
)]
direct_scores[is_reference == TRUE & is_best_in_grid == FALSE,
  display_label := paste0(display_label, " / REF")]
direct_scores[is_reference == FALSE & is_best_in_grid == TRUE,
  display_label := paste0(display_label, " / BEST")]
direct_scores[is_reference == TRUE & is_best_in_grid == TRUE,
  display_label := paste0(display_label, " / REF/BEST")]
setorder(direct_scores, direction, tool, tool_BH_FDR_cutoff, tool_abs_log2FC_cutoff)

direct_grid_out <- file.path(root, "inputs", "direct_H146_H526_F1_threshold_sweep_grid.tsv")
direct_reference_out <- file.path(root, "inputs", "direct_H146_H526_reference_threshold_results.tsv")
direct_best_out <- file.path(root, "inputs", "direct_H146_H526_best_thresholds.tsv")
direct_parameters_out <- file.path(root, "inputs", "direct_H146_H526_analysis_parameters.tsv")
fwrite(direct_scores, direct_grid_out, sep = "\t")
fwrite(direct_scores[is_reference == TRUE], direct_reference_out, sep = "\t")
fwrite(direct_scores[is_best_in_grid == TRUE], direct_best_out, sep = "\t")
fwrite(data.table(
  parameter = c(
    "comparison", "directions", "fixed_truth_FDR", "fixed_truth_abs_log2FC",
    "FDR_grid", "abs_log2FC_grid", "shared_genes", "total_grid_cells"
  ),
  value = c(
    "direct H146 versus H526", "H526-high (negative) and H146-high (positive)",
    truth_fdr, truth_abs_log2fc,
    paste(format(fdr_grid, scientific = TRUE), collapse = ","),
    paste(sprintf("%.2f", log2fc_grid), collapse = ","),
    8135L, nrow(direct_scores)
  )
), direct_parameters_out, sep = "\t")

prepare_direct_plot_data <- function(z, direction_i) {
  z <- add_plot_labels(z)
  if (direction_i == "H526_high") {
    signed_labels <- sprintf("-%.2f", z$tool_abs_log2FC_cutoff)
    signed_levels <- sprintf("-%.2f", rev(log2fc_grid))
  } else {
    signed_labels <- sprintf("%.2f", z$tool_abs_log2FC_cutoff)
    signed_levels <- sprintf("%.2f", log2fc_grid)
  }
  z[, signed_log2FC_factor := factor(signed_labels, levels = signed_levels)]
  z
}

make_direct_high_column <- function(direction_i) {
  cell_line <- sub("_high$", "", direction_i)
  z <- direct_scores[direction == direction_i]
  truth_n <- unique(z$truth_positive)
  stopifnot(length(truth_n) == 1L)
  z <- prepare_direct_plot_data(z, direction_i)
  column_label <- sprintf(
    "%s-high (Illumina truth n = %s)", cell_line, format(truth_n, big.mark = ",")
  )

  ggplot(z, aes(signed_log2FC_factor, FDR_factor, fill = F1)) +
    heatmap_layers(z) +
    facet_grid(rows = vars(tool), switch = "y") +
    scale_fill_viridis_c(
      option = unname(palettes[[cell_line]]), direction = -1,
      limits = c(0, 1), name = sprintf("%s F1", cell_line),
      guide = guide_colorbar(
        title.position = "top", barwidth = unit(5.2, "cm"), barheight = unit(0.35, "cm")
      )
    ) +
    labs(
      title = column_label,
      x = expression("Tool signed " * log[2] * " fold-change cutoff"),
      y = "Tool BH FDR cutoff"
    ) +
    combined_theme() +
    theme(
      plot.title = element_text(face = "bold", size = 13, hjust = 0.5),
      legend.position = "bottom"
    )
}

p_direct_h526 <- make_direct_high_column("H526_high")
p_direct_h146 <- make_direct_high_column("H146_high")
p_direct_compare <- (p_direct_h526 | p_direct_h146) +
  plot_annotation(
    title = "Direct H146 versus H526: high-direction F1 threshold sweeps",
    subtitle = paste0(
      "Left: H526-high (negative direct log2FC); right: H146-high (positive direct log2FC). ",
      "Rows are tools; black = reference; dashed teal = best in grid."
    ),
    theme = theme(
      plot.title = element_text(face = "bold", size = 17),
      plot.subtitle = element_text(size = 10.5)
    )
  )
save_figure(p_direct_compare, figure_stems[[3L]], width = 19, height = 24)

panel_layout <- data.table(
  figure = c(rep(figure_stems[[1L]], 6L), rep(figure_stems[[2L]], 6L), rep(figure_stems[[3L]], 6L)),
  row = rep(rep(seq_along(tools), each = 2L), 3L),
  column = rep(rep(1:2, times = length(tools)), 3L),
  tool = rep(rep(tools, each = 2L), 3L),
  contrast = c(rep("H146_vs_rest", 6L), rep("H526_vs_rest", 6L), rep("H146_vs_H526_direct", 6L)),
  direction = c(
    rep(c("low", "high"), times = 3L),
    rep(c("low", "high"), times = 3L),
    rep(c("H526_high", "H146_high"), times = 3L)
  ),
  palette = c(
    rep("viridis C (plasma)", 6L), rep("viridis D", 6L),
    rep(c("viridis D", "viridis C (plasma)"), times = 3L)
  ),
  x_axis = c(
    rep(c("negative_reversed", "positive"), times = 3L),
    rep(c("negative_reversed", "positive"), times = 3L),
    rep(c("negative_reversed", "positive"), times = 3L)
  )
)
fwrite(panel_layout, file.path(root, "PANEL_LAYOUT.tsv"), sep = "\t")

canonical_ova_root <- paste0(
  "/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/",
  "082426_volcano_plots/SN_ONT_H146_H526_vs_all_directional_F1_sweeps_20260831"
)
canonical_direct_root <- paste0(
  "/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/",
  "082426_volcano_plots/Illumina_tool_confidence_19plots_20260825"
)
packaged_sources <- data.table(
  role = c(
    "directional_grid", "reference_results", "best_results", "analysis_parameters",
    "upstream_source_manifest", "upstream_validation", "upstream_checksums",
    "upstream_readme", "upstream_complete", "direct_plot_data",
    "direct_source_manifest", "direct_validation", "direct_complete"
  ),
  packaged_relative_path = c(
    "inputs/directional_F1_threshold_sweep_grid.tsv", "inputs/reference_threshold_results.tsv",
    "inputs/best_thresholds.tsv", "inputs/analysis_parameters.tsv",
    "inputs/UPSTREAM_SOURCE_INPUT_SHA256.tsv", "inputs/UPSTREAM_VALIDATION.tsv",
    "inputs/UPSTREAM_SHA256SUMS", "inputs/UPSTREAM_README.md", "inputs/UPSTREAM_COMPLETE",
    "inputs/direct_H146_vs_H526_plot_data.tsv.gz", "inputs/DIRECT_SOURCE_INPUT_SHA256.tsv",
    "inputs/DIRECT_VALIDATION.tsv", "inputs/DIRECT_COMPLETE"
  ),
  origin_path = c(
    file.path(canonical_ova_root, "tables", "directional_F1_threshold_sweep_grid.tsv"),
    file.path(canonical_ova_root, "tables", "reference_threshold_results.tsv"),
    file.path(canonical_ova_root, "tables", "best_thresholds.tsv"),
    file.path(canonical_ova_root, "tables", "analysis_parameters.tsv"),
    file.path(canonical_ova_root, "SOURCE_INPUT_SHA256.tsv"),
    file.path(canonical_ova_root, "VALIDATION.tsv"),
    file.path(canonical_ova_root, "SHA256SUMS"),
    file.path(canonical_ova_root, "README.md"),
    file.path(canonical_ova_root, "COMPLETE"),
    file.path(canonical_direct_root, "23_Illumina_vs_RAD_BLAZE_Flexiplex_all_genes_spearman_plot_data.tsv.gz"),
    file.path(canonical_direct_root, "23_Illumina_vs_RAD_BLAZE_Flexiplex_all_genes_SOURCE_INPUT_SHA256.tsv"),
    file.path(canonical_direct_root, "VALIDATION_RAD4acbe00_plot23.tsv"),
    file.path(canonical_direct_root, "COMPLETE_RAD4acbe00_plot23")
  )
)
packaged_sources[, `:=`(
  sha256 = vapply(file.path(root, packaged_relative_path), sha256_file, character(1L)),
  bytes = file.info(file.path(root, packaged_relative_path))$size
)]
stopifnot(all(file.exists(packaged_sources$origin_path)))
stopifnot(all(vapply(packaged_sources$origin_path, sha256_file, character(1L)) == packaged_sources$sha256))
fwrite(packaged_sources, file.path(root, "SOURCE_INPUT_SHA256.tsv"), sep = "\t")

message(sprintf(
  paste0(
    "complete: figures=%d panels=%d ova_rows=%d direct_rows=%d; ",
    "direct_truth_H526=%d,H146=%d; palettes=H146:%s,H526:%s"
  ),
  length(figure_stems), nrow(panel_layout), nrow(ova), nrow(direct_scores),
  unique(direct_scores[direction == "H526_high", truth_positive]),
  unique(direct_scores[direction == "H146_high", truth_positive]),
  palettes[["H146"]], palettes[["H526"]]
))
