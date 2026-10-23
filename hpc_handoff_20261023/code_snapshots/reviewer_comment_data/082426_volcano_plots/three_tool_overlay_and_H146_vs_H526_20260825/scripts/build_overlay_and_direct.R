#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(Matrix)
  library(data.table)
  library(scran)
  library(BiocParallel)
  library(ggplot2)
  library(ggrepel)
  library(digest)
  library(svglite)
  library(ragg)
})

options(stringsAsFactors = FALSE)
set.seed(20260825)

argv <- commandArgs(trailingOnly = TRUE)
default_source <- "/scratch-nfs/f005f43/SN_ONT_H146_H526_DEG_RAD4acbe00_all_records_20260828"
default_rank <- "/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/082426_volcano_plots/wilcoxon_auc_rank"
source_package <- if (length(argv) >= 1L) normalizePath(argv[[1L]], mustWork = TRUE) else default_source
rank_package <- if (length(argv) >= 2L) normalizePath(argv[[2L]], mustWork = TRUE) else default_rank

command <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", command[grepl("^--file=", command)])
if (length(script_arg) != 1L) stop("Could not resolve script path")
script_dir <- dirname(normalizePath(script_arg, mustWork = TRUE))
package_dir <- normalizePath(file.path(script_dir, ".."), mustWork = TRUE)
figure_dir <- file.path(package_dir, "figures")
table_dir <- file.path(package_dir, "tables")
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(table_dir, recursive = TRUE, showWarnings = FALSE)

tools <- c("RAD", "BLAZE", "Flexiplex")
tool_colors <- c(RAD = "#0072B2", BLAZE = "#D55E00", Flexiplex = "#009E73")
tool_shapes <- c(RAD = 16, BLAZE = 17, Flexiplex = 15)
focus_lines <- c("H146", "H526")
direct_directions <- c("H526_high", "H146_high")
direction_colors <- c(H526_high = "#2166AC", H146_high = "#B2182B")
direction_fills <- c(H526_high = "#67A9CF", H146_high = "#EF8A8A")
fdr_cutoff <- 0.05
lfc_cutoff <- 0.5
detection_gate <- 0.10
pseudocount <- 0.1

source_deg_path <- normalizePath(
  file.path(source_package, "results", "tables", "all_deg_results.tsv.gz"),
  mustWork = TRUE
)
source_universe_path <- normalizePath(
  file.path(source_package, "results", "tables", "gene_universes_and_joins.tsv"),
  mustWork = TRUE
)
source_sha_path <- normalizePath(file.path(source_package, "SHA256SUMS"), mustWork = TRUE)
source_complete_path <- normalizePath(file.path(source_package, "COMPLETE"), mustWork = TRUE)
rank_consensus_path <- normalizePath(
  file.path(rank_package, "tables", "top10_cross_tool_consensus_wilcoxon_auc_ranks.tsv"),
  mustWork = TRUE
)
rank_sha_path <- normalizePath(file.path(rank_package, "SHA256SUMS"), mustWork = TRUE)
rank_complete_path <- normalizePath(file.path(rank_package, "COMPLETE"), mustWork = TRUE)

native_paths <- lapply(tools, function(tool) {
  list(
    matrix = normalizePath(file.path(source_package, "inputs", "native", tool, "all", "matrix.mtx.gz"), mustWork = TRUE),
    features = normalizePath(file.path(source_package, "inputs", "native", tool, "all", "features.tsv.gz"), mustWork = TRUE),
    barcodes = normalizePath(file.path(source_package, "inputs", "native", tool, "all", "barcodes.tsv.gz"), mustWork = TRUE),
    labels = normalizePath(file.path(source_package, "inputs", "labels", tool, "donor_ids.tsv"), mustWork = TRUE)
  )
})
names(native_paths) <- tools

input_rows <- list(
  data.table(role = "authoritative_native_DEG_table", source_path = source_deg_path),
  data.table(role = "authoritative_gene_universe_table", source_path = source_universe_path),
  data.table(role = "authoritative_source_SHA256SUMS", source_path = source_sha_path),
  data.table(role = "authoritative_source_COMPLETE", source_path = source_complete_path),
  data.table(role = "sealed_AUC_consensus_top10", source_path = rank_consensus_path),
  data.table(role = "sealed_AUC_rank_SHA256SUMS", source_path = rank_sha_path),
  data.table(role = "sealed_AUC_rank_COMPLETE", source_path = rank_complete_path)
)
for (tool in tools) {
  for (kind in c("matrix", "features", "barcodes", "labels")) {
    input_rows[[length(input_rows) + 1L]] <- data.table(
      role = paste0(tool, "_native_", kind),
      source_path = native_paths[[tool]][[kind]]
    )
  }
}
source_manifest <- rbindlist(input_rows)
source_manifest[, sha256 := vapply(source_path, function(path) {
  digest(file = path, algo = "sha256", serialize = FALSE)
}, character(1L))]
source_manifest[, bytes := file.info(source_path)$size]
fwrite(source_manifest, file.path(table_dir, "SOURCE_INPUT_SHA256.tsv"), sep = "\t")

parse_sha_manifest <- function(path) {
  x <- readLines(path, warn = FALSE)
  data.table(
    checksum = sub("^([0-9a-f]{64})[[:space:]]+.*$", "\\1", x),
    relative_path = sub("^[0-9a-f]{64}[[:space:]]+\\*?", "", x)
  )
}
assert_upstream_member <- function(manifest_path, member_path, upstream_root) {
  m <- parse_sha_manifest(manifest_path)
  relative <- substring(member_path, nchar(upstream_root) + 2L)
  expected <- digest(file = member_path, algo = "sha256", serialize = FALSE)
  observed <- m[relative_path == relative, checksum]
  if (length(observed) != 1L || observed != expected) {
    stop("Upstream checksum membership failure: ", relative)
  }
}
assert_upstream_member(source_sha_path, source_deg_path, source_package)
assert_upstream_member(source_sha_path, source_universe_path, source_package)
assert_upstream_member(rank_sha_path, rank_consensus_path, rank_package)
for (tool in tools) {
  for (kind in c("matrix", "features", "barcodes", "labels")) {
    assert_upstream_member(source_sha_path, native_paths[[tool]][[kind]], source_package)
  }
}

fallback_label <- function(symbol, gene_id) {
  fifelse(is.na(symbol) | trimws(symbol) == "", gene_id, symbol)
}
normalize_barcode <- function(x) sub("-[0-9]+$", "", x)
read_features <- function(path) {
  x <- fread(cmd = paste("gzip -cd", shQuote(path)), header = FALSE, sep = "\t")
  setnames(x, seq_len(min(3L, ncol(x))), c("gene_id", "gene_symbol", "feature_type")[seq_len(min(3L, ncol(x)))])
  if (anyDuplicated(x$gene_id)) stop("Duplicate feature gene IDs: ", path)
  x
}
read_barcodes <- function(path) {
  x <- normalize_barcode(fread(cmd = paste("gzip -cd", shQuote(path)), header = FALSE)[[1L]])
  if (anyDuplicated(x)) stop("Duplicate normalized matrix barcodes: ", path)
  x
}
read_counts <- function(path) {
  x <- as(readMM(gzfile(path)), "CsparseMatrix")
  if (any(x@x < 0) || any(abs(x@x - round(x@x)) > 1e-8)) stop("Non-integer counts: ", path)
  x
}
read_labels <- function(path) {
  x <- fread(path)
  required <- c("cell", "donor_id", "prob_max", "prob_doublet", "n_vars")
  if (length(setdiff(required, names(x)))) stop("Vireo label schema mismatch: ", path)
  x[, barcode := normalize_barcode(cell)]
  if (anyDuplicated(x$barcode)) stop("Duplicate normalized Vireo barcodes: ", path)
  x
}

# ---------------------------------------------------------------------------
# Set A: unchanged authoritative native H146/H526 versus-rest coordinates.
# ---------------------------------------------------------------------------
stored_all <- fread(source_deg_path)
native_vs_rest <- stored_all[
  analysis_mode == "native" & cohort %in% tools & cell_line %in% focus_lines
]
if (uniqueN(native_vs_rest, by = c("cohort", "cell_line")) != 6L) stop("Expected six native versus-rest strata")
if (anyDuplicated(native_vs_rest, by = c("cohort", "cell_line", "gene_id"))) stop("Duplicate versus-rest gene rows")
if (any(!is.finite(native_vs_rest$FDR)) || any(native_vs_rest$FDR <= 0) || any(native_vs_rest$FDR > 1)) {
  stop("Versus-rest FDR must be finite in (0,1]")
}
native_vs_rest[, neg_log10_FDR := -log10(FDR)]
native_vs_rest[, display_gene := fallback_label(gene_symbol, gene_id)]
native_vs_rest[, cohort := factor(cohort, levels = tools)]
setorder(native_vs_rest, cell_line, cohort, gene_id)
fwrite(native_vs_rest, file.path(table_dir, "native_H146_H526_vs_rest_overlay_coordinates.tsv.gz"), sep = "\t")

stored_consensus <- fread(rank_consensus_path)
if (nrow(stored_consensus) != 40L || anyDuplicated(stored_consensus, by = c("cell_line", "direction", "gene_id"))) {
  stop("Unexpected sealed versus-rest consensus table")
}
existing_fixed_ids <- stored_consensus[, .(
  cell_line,
  direction,
  gene_id,
  gene_symbol,
  selection_rank = as.integer(consensus_rank)
)]
existing_fixed_ids[, direct_direction := fifelse(direction == "up", "H146_or_H526_target_high", "target_low")]
existing_fixed <- merge(
  native_vs_rest,
  existing_fixed_ids[, .(cell_line, direction, gene_id, selection_rank)],
  by = c("cell_line", "direction", "gene_id"),
  all = FALSE,
  allow.cartesian = TRUE
)
if (nrow(existing_fixed) != 120L || any(existing_fixed$effect_qualified != TRUE)) {
  stop("Versus-rest fixed selection must be 20 genes x 2 lines x 3 tools")
}
existing_fixed[, rank_label := paste0(fifelse(direction == "up", "U", "D"), selection_rank)]
existing_fixed[, plot_label := paste0(rank_label, "  ", display_gene)]
existing_fixed[, cohort := factor(cohort, levels = tools)]
setorder(existing_fixed, cell_line, direction, selection_rank, cohort)
fwrite(existing_fixed, file.path(table_dir, "native_vs_rest_fixed_consensus_overlay_selection.tsv"), sep = "\t")

# ---------------------------------------------------------------------------
# Set B: direct all-H146 versus all-H526 within each native tool cohort.
# Positive log2FC and AUC > 0.5 always mean H146-high.
# ---------------------------------------------------------------------------
native_universe <- native_vs_rest[, .(
  n_rows = .N,
  unique_gene_ids = uniqueN(gene_id)
), by = .(cohort, cell_line)]
if (any(native_universe$n_rows != native_universe$unique_gene_ids)) stop("Universe has duplicate IDs")
stored_universe_sets <- lapply(tools, function(tool) {
  a <- native_vs_rest[cohort == tool & cell_line == "H146", as.character(gene_id)]
  b <- native_vs_rest[cohort == tool & cell_line == "H526", as.character(gene_id)]
  if (!identical(a, b)) {
    if (!setequal(a, b)) stop("Frozen tested universe differs between stored focus contrasts for ", tool)
    a <- sort(a)
  }
  a
})
names(stored_universe_sets) <- tools

direct_parts <- list()
cell_parts <- list()
universe_parts <- list()
serial_param <- SerialParam(progressbar = FALSE)

for (tool in tools) {
  message("Direct H146 versus H526: reading ", tool)
  paths <- native_paths[[tool]]
  feat <- read_features(paths$features)
  bc <- read_barcodes(paths$barcodes)
  mat <- read_counts(paths$matrix)
  if (nrow(mat) != nrow(feat) || ncol(mat) != length(bc)) stop("MEX dimension mismatch: ", tool)
  rownames(mat) <- feat$gene_id
  colnames(mat) <- bc
  labels_all <- read_labels(paths$labels)
  labels <- labels_all[donor_id %in% focus_lines]
  idx <- match(labels$barcode, bc)
  in_matrix <- !is.na(idx)
  labels <- labels[in_matrix]
  idx <- idx[in_matrix]
  counts_full <- mat[, idx, drop = FALSE]
  depth <- as.numeric(colSums(counts_full))
  positive <- depth > 0
  labels <- labels[positive]
  idx <- idx[positive]
  depth <- depth[positive]
  counts_full <- mat[, idx, drop = FALSE]
  if (!identical(as.character(labels$barcode), colnames(counts_full))) stop("Cell join order mismatch: ", tool)
  observed_counts <- labels[, .N, by = donor_id]
  expected_counts <- data.table(
    donor_id = focus_lines,
    N = c(
      c(RAD = 709L, BLAZE = 234L, Flexiplex = 290L)[[tool]],
      c(RAD = 419L, BLAZE = 185L, Flexiplex = 219L)[[tool]]
    )
  )
  observed_counts[, line_order := match(donor_id, focus_lines)]
  setorder(observed_counts, line_order)
  observed_counts[, line_order := NULL]
  if (!identical(observed_counts$donor_id, expected_counts$donor_id) || !identical(as.integer(observed_counts$N), expected_counts$N)) {
    stop("Unexpected direct cohort sizes for ", tool)
  }

  # Reapply the source analysis' native eligibility rule to this pair-only
  # cohort. Therefore cells from the other six lines have no influence on
  # either the test or the gene universe. Full-MEX depth was already computed
  # above, before any gene filtering.
  pair_min_detected_cells <- ceiling(0.01 * ncol(counts_full))
  pair_total_by_gene <- as.numeric(rowSums(counts_full))
  pair_detected_by_gene <- as.numeric(rowSums(counts_full > 0))
  pair_keep_gene <- pair_total_by_gene >= 10 & pair_detected_by_gene >= pair_min_detected_cells
  tested_ids <- rownames(mat)[pair_keep_gene]
  expected_tested_genes <- c(RAD = 13504L, BLAZE = 10926L, Flexiplex = 12160L)[[tool]]
  if (length(tested_ids) != expected_tested_genes) {
    stop("Unexpected pair-only tested universe for ", tool, ": ", length(tested_ids), " != ", expected_tested_genes)
  }
  row_idx <- which(pair_keep_gene)
  counts <- counts_full[row_idx, , drop = FALSE]
  rownames(counts) <- tested_ids
  norm_linear <- counts %*% Diagonal(x = 10000 / depth)
  norm_log <- norm_linear
  norm_log@x <- log2(norm_log@x + 1)
  target <- labels$donor_id == "H146"
  groups <- factor(ifelse(target, "H146", "H526"), levels = c("H526", "H146"))
  message("Direct Wilcoxon ", tool, " (SerialParam; ", sum(target), " H146 vs ", sum(!target), " H526)")
  pw <- pairwiseWilcox(norm_log, groups = groups, direction = "any", BPPARAM = serial_param)
  pair_idx <- which(pw$pairs$first == "H146" & pw$pairs$second == "H526")
  if (length(pair_idx) != 1L) stop("Could not identify H146-first pair for ", tool)
  stat_df <- pw$statistics[[pair_idx]]
  stat_gene_ids <- rownames(stat_df)
  stat <- as.data.table(stat_df)
  if (!is.null(stat_gene_ids) && length(stat_gene_ids) == length(tested_ids) && !identical(stat_gene_ids, tested_ids)) {
    stop("scran statistic row order mismatch: ", tool)
  }
  pct_h146 <- as.numeric(rowMeans(counts[, target, drop = FALSE] > 0))
  pct_h526 <- as.numeric(rowMeans(counts[, !target, drop = FALSE] > 0))
  mean_h146 <- as.numeric(rowMeans(norm_linear[, target, drop = FALSE]))
  mean_h526 <- as.numeric(rowMeans(norm_linear[, !target, drop = FALSE]))
  mean_log_h146 <- as.numeric(rowMeans(norm_log[, target, drop = FALSE]))
  mean_log_h526 <- as.numeric(rowMeans(norm_log[, !target, drop = FALSE]))
  annot <- feat[match(tested_ids, gene_id), .(gene_id, gene_symbol)]
  ans <- data.table(
    contrast = "H146_vs_H526",
    cohort = tool,
    gene_id = tested_ids,
    gene_symbol = annot$gene_symbol,
    n_H146 = sum(target),
    n_H526 = sum(!target),
    pct_H146 = pct_h146,
    pct_H526 = pct_h526,
    mean_cp10k_H146 = mean_h146,
    mean_cp10k_H526 = mean_h526,
    mean_log2norm_H146 = mean_log_h146,
    mean_log2norm_H526 = mean_log_h526,
    avg_log2FC_H146_vs_H526 = log2((mean_h146 + pseudocount) / (mean_h526 + pseudocount)),
    AUC_H146 = as.numeric(stat$AUC),
    p_value = as.numeric(stat$p.value)
  )
  ans[, FDR := p.adjust(p_value, method = "BH")]
  ans[, passes_detection_gate := pct_H146 >= detection_gate | pct_H526 >= detection_gate]
  ans[, fdr_qualified := FDR < fdr_cutoff & passes_detection_gate]
  ans[, effect_qualified := fdr_qualified & abs(avg_log2FC_H146_vs_H526) >= lfc_cutoff]
  ans[, direction := fifelse(
    effect_qualified & avg_log2FC_H146_vs_H526 > 0,
    "H146_high",
    fifelse(effect_qualified & avg_log2FC_H146_vs_H526 < 0, "H526_high", "not_effect_qualified")
  )]
  ans[, abs_log2FC := abs(avg_log2FC_H146_vs_H526)]
  ans[, directed_AUC := fifelse(direction == "H146_high", AUC_H146,
    fifelse(direction == "H526_high", 1 - AUC_H146, NA_real_))]
  ans[, rank_biserial_H146 := 2 * AUC_H146 - 1]
  if (any(!is.finite(ans$p_value)) || any(ans$p_value <= 0) || any(ans$p_value > 1)) stop("Direct p-value outside (0,1]: ", tool)
  if (any(!is.finite(ans$FDR)) || any(ans$FDR <= 0) || any(ans$FDR > 1)) stop("Direct FDR outside (0,1]: ", tool)
  if (any(ans$AUC_H146 < 0 | ans$AUC_H146 > 1 | !is.finite(ans$AUC_H146))) stop("Direct AUC outside [0,1]: ", tool)
  ans[, neg_log10_FDR := -log10(FDR)]
  ans[, display_gene := fallback_label(gene_symbol, gene_id)]
  setorder(ans, FDR, -abs_log2FC, gene_id)
  direct_parts[[tool]] <- ans

  cell_parts[[tool]] <- data.table(
    cohort = tool,
    barcode = labels$barcode,
    original_cell_field = labels$cell,
    cell_line = labels$donor_id,
    prob_max = labels$prob_max,
    prob_doublet = labels$prob_doublet,
    n_vars = labels$n_vars,
    total_umis_full_native_mex = depth,
    positive_depth = TRUE,
    matrix_column_index = idx
  )
  universe_parts[[tool]] <- data.table(
    cohort = tool,
    matrix_genes = nrow(mat),
    matrix_cells = ncol(mat),
    Vireo_rows_total = nrow(labels_all),
    Vireo_H146_H526_rows = sum(labels_all$donor_id %in% focus_lines),
    H146_H526_labels_in_matrix = sum(in_matrix),
    H146_H526_positive_depth_cells = nrow(labels),
    H146_cells = sum(target),
    H526_cells = sum(!target),
    pair_only_min_detected_cells = pair_min_detected_cells,
    pair_only_tested_genes = length(tested_ids),
    stored_all_eight_line_tested_genes_for_reference = length(stored_universe_sets[[tool]]),
    full_MEX_UMIs_in_direct_cells = sum(depth),
    universe_definition = "pair-only native universe: >=10 molecules and detected in >=1% of named positive-depth H146+H526 cells; other six lines do not affect eligibility"
  )
  rm(mat, counts_full, counts, norm_linear, norm_log, pw, stat_df, stat, ans)
  invisible(gc())
}

direct <- rbindlist(direct_parts, use.names = TRUE)
direct[, cohort := factor(cohort, levels = tools)]
direct_cells <- rbindlist(cell_parts, use.names = TRUE)
direct_cells[, cohort := factor(cohort, levels = tools)]
direct_universe <- rbindlist(universe_parts, use.names = TRUE)
direct_universe[, cohort := factor(cohort, levels = tools)]
setorder(direct, cohort, gene_id)
setorder(direct_cells, cohort, cell_line, barcode)
setorder(direct_universe, cohort)
fwrite(direct, file.path(table_dir, "direct_H146_vs_H526_all_deg_results.tsv.gz"), sep = "\t")
fwrite(direct_cells, file.path(table_dir, "direct_H146_H526_cell_cohort.tsv.gz"), sep = "\t")
fwrite(direct_universe, file.path(table_dir, "direct_H146_H526_gene_universe_and_join.tsv"), sep = "\t")

direct_summary <- direct[, .(
  n_H146 = unique(n_H146),
  n_H526 = unique(n_H526),
  tested_genes = .N,
  fdr_qualified = sum(fdr_qualified),
  effect_qualified = sum(effect_qualified),
  H146_high_effect_qualified = sum(direction == "H146_high"),
  H526_high_effect_qualified = sum(direction == "H526_high"),
  minimum_FDR = min(FDR),
  maximum_neg_log10_FDR = max(neg_log10_FDR),
  median_abs_log2FC_effect = median(abs_log2FC[effect_qualified]),
  median_directed_AUC_effect = median(directed_AUC[effect_qualified])
), by = cohort]
setorder(direct_summary, cohort)
fwrite(direct_summary, file.path(table_dir, "direct_H146_vs_H526_DEG_summary.tsv"), sep = "\t")

# Independent directional AUC top ten in each tool.
tool_top <- direct[effect_qualified == TRUE]
setorder(tool_top, cohort, direction, -directed_AUC, -abs_log2FC, FDR, gene_id)
tool_top[, auc_rank := seq_len(.N), by = .(cohort, direction)]
tool_top10 <- tool_top[auc_rank <= 10L]
if (nrow(tool_top10) != 60L || !all(tool_top10[, sort(auc_rank) == 1:10, by = .(cohort, direction)]$V1)) {
  stop("Direct tool-specific top-ten failure")
}
tool_top10[, rank_label := paste0(fifelse(direction == "H146_high", "H146#", "H526#"), auc_rank)]
tool_top10[, plot_label := paste0(rank_label, "  ", display_gene)]
setorder(tool_top10, cohort, direction, auc_rank)
fwrite(tool_top10, file.path(table_dir, "direct_tool_specific_directional_AUC_top10.tsv"), sep = "\t")

# Cross-tool consensus requires qualification and identical direction in all tools.
qualified <- direct[effect_qualified == TRUE]
common_state <- qualified[, .(
  tools_qualified = uniqueN(cohort),
  direction_states = uniqueN(direction),
  consensus_direction = direction[[1L]]
), by = gene_id][tools_qualified == 3L & direction_states == 1L]
common_long <- merge(
  qualified,
  common_state[, .(gene_id, consensus_direction)],
  by = "gene_id",
  all = FALSE
)
if (any(common_long$direction != common_long$consensus_direction)) stop("Direct consensus direction mismatch")
consensus <- common_long[, .(
  gene_symbol = {
    z <- gene_symbol[!is.na(gene_symbol) & trimws(gene_symbol) != ""]
    if (length(z)) z[[1L]] else NA_character_
  },
  median_AUC_H146 = median(AUC_H146),
  median_rank_biserial_H146 = median(rank_biserial_H146),
  median_directed_AUC = median(directed_AUC),
  minimum_directed_AUC = min(directed_AUC),
  median_abs_log2FC = median(abs_log2FC),
  maximum_FDR = max(FDR)
), by = .(direction = consensus_direction, gene_id)]
setorder(consensus, direction, -median_directed_AUC, -minimum_directed_AUC, -median_abs_log2FC, gene_id)
consensus[, consensus_rank := seq_len(.N), by = direction]
consensus_top10 <- consensus[consensus_rank <= 10L]
if (nrow(consensus_top10) != 20L || !all(consensus_top10[, sort(consensus_rank) == 1:10, by = direction]$V1)) {
  stop("Direct cross-tool consensus top-ten failure")
}
consensus_top10[, rank_label := paste0(fifelse(direction == "H146_high", "H146#", "H526#"), consensus_rank)]
consensus_top10[, display_gene := fallback_label(gene_symbol, gene_id)]
consensus_top10[, plot_label := paste0(rank_label, "  ", display_gene)]
setorder(consensus_top10, direction, consensus_rank)
fwrite(consensus_top10, file.path(table_dir, "direct_cross_tool_consensus_directional_AUC_top10.tsv"), sep = "\t")

direct_fixed <- merge(
  direct,
  consensus_top10[, .(direction, gene_id, selection_rank = consensus_rank, rank_label, plot_label)],
  by = c("direction", "gene_id"),
  all = FALSE,
  allow.cartesian = TRUE
)
if (nrow(direct_fixed) != 60L || any(direct_fixed$effect_qualified != TRUE)) {
  stop("Direct fixed consensus expansion must be 20 genes x 3 tools")
}
setorder(direct_fixed, direction, selection_rank, cohort)
fwrite(direct_fixed, file.path(table_dir, "direct_fixed_consensus_plot_selection.tsv"), sep = "\t")

y_ranges <- rbindlist(list(
  native_vs_rest[, .(
    contrast = paste0(cell_line, "_vs_other7"),
    tested_genes = .N,
    minimum_FDR = min(FDR),
    maximum_neg_log10_FDR = max(neg_log10_FDR)
  ), by = .(cohort, cell_line)][, cell_line := NULL],
  direct[, .(
    contrast = "H146_vs_H526",
    tested_genes = .N,
    minimum_FDR = min(FDR),
    maximum_neg_log10_FDR = max(neg_log10_FDR)
  ), by = cohort]
), fill = TRUE)
y_ranges[, cohort := factor(cohort, levels = tools)]
setorder(y_ranges, contrast, cohort)
fwrite(y_ranges, file.path(table_dir, "exact_uncapped_y_ranges.tsv"), sep = "\t")

# ---------------------------------------------------------------------------
# Plotting.
# ---------------------------------------------------------------------------
save_pair <- function(plot, basename, width = 24, height = 11.5, plot_set, panels, full_points, selected_points, labels) {
  svg_name <- paste0(basename, ".svg")
  png_name <- paste0(basename, ".png")
  ggsave(file.path(figure_dir, svg_name), plot, width = width, height = height,
    units = "in", device = svglite::svglite, bg = "white")
  ggsave(file.path(figure_dir, png_name), plot, width = width, height = height,
    units = "in", dpi = 300, device = ragg::agg_png, bg = "white")
  data.table(
    plot_set = plot_set,
    svg_path = file.path("figures", svg_name),
    png_preview_path = file.path("figures", png_name),
    svg_width_inches = width,
    svg_height_inches = height,
    png_width_pixels = as.integer(width * 300),
    png_height_pixels = as.integer(height * 300),
    png_dpi = 300L,
    panels_n = panels,
    full_points_n = full_points,
    selected_point_instances_n = selected_points,
    labels_n = labels,
    y_cap_applied = FALSE,
    y_floor_applied = FALSE,
    embedded_raster_in_svg = FALSE
  )
}

base_theme <- theme_bw(base_size = 11.2) +
  theme(
    plot.title = element_text(face = "bold", size = 15.5),
    plot.subtitle = element_text(size = 10.5, margin = margin(b = 8)),
    strip.text = element_text(face = "bold", size = 11.8, lineheight = 1.05),
    strip.background = element_rect(fill = "#F1F3F5", color = "#B5BAC1"),
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(color = "#ECEEF1", linewidth = 0.28),
    axis.title = element_text(size = 11.3),
    axis.text = element_text(size = 9.3),
    legend.position = "top",
    plot.caption = element_text(hjust = 0, size = 7.7, color = "#444444", lineheight = 1.07),
    plot.margin = margin(10, 22, 10, 10)
  )

overlay_label_layers <- function(label_data, x_limits) {
  list(
    geom_text_repel(
      data = label_data[direction %in% c("down", "H526_high")],
      aes(x = label_x, y = label_y, label = plot_label),
      inherit.aes = FALSE, xlim = c(x_limits[[1L]], -0.15),
      size = 2.6, fontface = "bold", seed = 20260825,
      max.overlaps = Inf, min.segment.length = 0, segment.size = 0.25,
      box.padding = 0.28, point.padding = 0.15, force = 8, force_pull = 0.15,
      max.iter = 200000, max.time = 25
    ),
    geom_text_repel(
      data = label_data[direction %in% c("up", "H146_high")],
      aes(x = label_x, y = label_y, label = plot_label),
      inherit.aes = FALSE, xlim = c(0.15, x_limits[[2L]]),
      size = 2.6, fontface = "bold", seed = 20260825,
      max.overlaps = Inf, min.segment.length = 0, segment.size = 0.25,
      box.padding = 0.28, point.padding = 0.15, force = 8, force_pull = 0.15,
      max.iter = 200000, max.time = 25
    )
  )
}

make_existing_overlay <- function(lines, basename, title) {
  d <- copy(native_vs_rest[cell_line %in% lines])
  h <- copy(existing_fixed[cell_line %in% lines])
  d[, cohort := factor(cohort, levels = tools)]
  h[, cohort := factor(cohort, levels = tools)]
  rad_anchor <- h[cohort == "RAD", .(
    cell_line, gene_id,
    rad_x = avg_log2FC,
    rad_y = neg_log10_FDR,
    plot_label,
    direction
  )]
  connector_data <- merge(
    h[cohort != "RAD", .(
      cell_line, gene_id,
      competitor = as.character(cohort),
      competitor_x = avg_log2FC,
      competitor_y = neg_log10_FDR
    )],
    rad_anchor[, .(cell_line, gene_id, rad_x, rad_y)],
    by = c("cell_line", "gene_id"), all = FALSE
  )
  label_data <- rad_anchor[, .(
    cell_line, gene_id,
    label_x = rad_x,
    label_y = rad_y,
    plot_label,
    direction
  )]
  observed_abs <- max(abs(d$avg_log2FC))
  x_max <- max(8, ceiling(observed_abs))
  p <- ggplot(d, aes(avg_log2FC, neg_log10_FDR)) +
    geom_hline(yintercept = -log10(0.05), color = "#858B92", linewidth = 0.34, linetype = "dotted") +
    geom_vline(xintercept = c(-0.5, 0.5), color = "#858B92", linewidth = 0.34, linetype = "dotted") +
    geom_vline(xintercept = 0, color = "#4A4A4A", linewidth = 0.38, linetype = "solid") +
    geom_point(aes(color = cohort, shape = cohort), alpha = 0.16, size = 0.50, stroke = 0) +
    geom_segment(
      data = connector_data,
      aes(x = competitor_x, y = competitor_y, xend = rad_x, yend = rad_y),
      inherit.aes = FALSE, color = "#25282C", alpha = 0.58, linewidth = 0.38
    ) +
    geom_point(
      data = h, aes(color = cohort, shape = cohort),
      size = 2.45, alpha = 0.94, stroke = 0.30
    ) +
    overlay_label_layers(label_data, c(-x_max, x_max)) +
    facet_wrap(~cell_line, nrow = 1, scales = "fixed") +
    scale_color_manual(values = tool_colors, breaks = tools) +
    scale_shape_manual(values = tool_shapes, breaks = tools) +
    scale_x_continuous(expand = expansion(mult = c(0.015, 0.015))) +
    scale_y_continuous(expand = expansion(mult = c(0.012, 0.09))) +
    coord_cartesian(xlim = c(-x_max, x_max), clip = "off") +
    labs(
      title = title,
      subtitle = "All three complete native DEG clouds are overlaid; each selected gene's competitor coordinates connect directly to RAD and are labeled once at RAD",
      x = "log2 fold change of target/rest mean CP10K",
      y = expression(-log[10]("BH FDR")),
      color = "Tool", shape = "Tool",
      caption = paste(
        "Existing authoritative contrasts: H146 or H526 versus the other seven named lines in each tool-native cohort.",
        "Fixed selected genes are the same sealed cross-tool directional-AUC consensus top 10 UP and DOWN per line.",
        "Exact stored FDR coordinates are used. The y-axis is linear and shared, with no cap, p-value floor, clipping, or free-y scaling.",
        "Background clouds have tool-specific native tested-gene universes; only selected genes are paired by ID. One-time labels are anchored at RAD.",
        sep = "\n"
      )
    ) + base_theme
  save_pair(p, basename, width = 24, height = 11.5, plot_set = "existing_native_vs_rest_overlay",
    panels = length(lines), full_points = nrow(d), selected_points = nrow(h), labels = nrow(label_data))
}

direct_x_max <- max(6, ceiling(max(abs(direct$avg_log2FC_H146_vs_H526))))

make_direct_overlay <- function() {
  d <- copy(direct)
  h <- copy(direct_fixed)
  rad_anchor <- h[cohort == "RAD", .(
    gene_id,
    rad_x = avg_log2FC_H146_vs_H526,
    rad_y = neg_log10_FDR,
    plot_label,
    direction
  )]
  connector_data <- merge(
    h[cohort != "RAD", .(
      gene_id,
      competitor = as.character(cohort),
      competitor_x = avg_log2FC_H146_vs_H526,
      competitor_y = neg_log10_FDR
    )],
    rad_anchor[, .(gene_id, rad_x, rad_y)],
    by = "gene_id", all = FALSE
  )
  label_data <- rad_anchor[, .(
    gene_id,
    label_x = rad_x,
    label_y = rad_y,
    plot_label,
    direction
  )]
  p <- ggplot(d, aes(avg_log2FC_H146_vs_H526, neg_log10_FDR)) +
    geom_hline(yintercept = -log10(0.05), color = "#858B92", linewidth = 0.34, linetype = "dotted") +
    geom_vline(xintercept = c(-0.5, 0.5), color = "#858B92", linewidth = 0.34, linetype = "dotted") +
    geom_vline(xintercept = 0, color = "#4A4A4A", linewidth = 0.38, linetype = "solid") +
    geom_point(aes(color = cohort, shape = cohort), alpha = 0.16, size = 0.50, stroke = 0) +
    geom_segment(
      data = connector_data,
      aes(x = competitor_x, y = competitor_y, xend = rad_x, yend = rad_y),
      inherit.aes = FALSE, color = "#25282C", alpha = 0.58, linewidth = 0.38
    ) +
    geom_point(data = h, aes(color = cohort, shape = cohort), size = 2.45, alpha = 0.94, stroke = 0.30) +
    overlay_label_layers(label_data, c(-direct_x_max, direct_x_max)) +
    scale_color_manual(values = tool_colors, breaks = tools) +
    scale_shape_manual(values = tool_shapes, breaks = tools) +
    scale_x_continuous(expand = expansion(mult = c(0.015, 0.015))) +
    scale_y_continuous(expand = expansion(mult = c(0.012, 0.09))) +
    coord_cartesian(xlim = c(-direct_x_max, direct_x_max), clip = "off") +
    labs(
      title = "Direct H146 versus H526: RAD, BLAZE, and Flexiplex overlaid",
      subtitle = "All positive-depth tool-native Vireo H146 and H526 cells only; each competitor coordinate connects directly to RAD and is labeled once at RAD",
      x = "log2 fold change of mean CP10K (H146 / H526)",
      y = expression(-log[10]("BH FDR")),
      color = "Tool", shape = "Tool",
      caption = paste(
        "Positive x and AUC > 0.5 mean H146-high; negative x and AUC < 0.5 mean H526-high.",
        "RAD: 709 H146 / 419 H526; BLAZE: 234 / 185; Flexiplex: 290 / 219. Full native-MEX cell depth defines CP10K.",
        "Two-sided cell-level Wilcoxon on log2(1+CP10K), BH within tool; pair-only native eligibility universe (>=10 molecules and >=1% detection).",
        "Gate: FDR < 0.05, |log2FC| >= 0.5, and >=10% detection in H146 or H526. Exact uncapped FDR; no floor or free-y scale.",
        sep = "\n"
      )
    ) + base_theme
  save_pair(p, "direct_H146_vs_H526_fixed_consensus_three_tool_overlay_uncapped",
    width = 24, height = 11.5, plot_set = "direct_fixed_consensus_overlay", panels = 1L,
    full_points = nrow(d), selected_points = nrow(h), labels = nrow(label_data))
}

side_label_layers <- function(labels) {
  common <- list(
    aes(label = plot_label, color = direction),
    size = 2.48, fontface = "bold", seed = 20260825,
    max.overlaps = Inf, min.segment.length = 0, segment.size = 0.24,
    segment.alpha = 0.68, box.padding = 0.27, point.padding = 0.14,
    force = 7, force_pull = 0.17, max.iter = 200000, max.time = 25
  )
  list(
    do.call(geom_text_repel, c(list(data = labels[direction == "H526_high"],
      xlim = c(-direct_x_max + 0.15, -0.15)), common)),
    do.call(geom_text_repel, c(list(data = labels[direction == "H146_high"],
      xlim = c(0.15, direct_x_max - 0.15)), common))
  )
}

make_direct_side_by_side <- function(selection, basename, title, subtitle, plot_set) {
  d <- copy(direct)
  h <- copy(selection)
  make_panel <- function(tool, n146, n526) paste0(
    as.character(tool), "\nH146 n=", format(n146, big.mark = ","),
    "; H526 n=", format(n526, big.mark = ",")
  )
  d[, panel_label := make_panel(cohort, n_H146, n_H526)]
  h[, panel_label := make_panel(cohort, n_H146, n_H526)]
  panel_levels <- unique(d[order(cohort), panel_label])
  d[, panel_label := factor(panel_label, levels = panel_levels)]
  h[, panel_label := factor(panel_label, levels = panel_levels)]
  h[, direction := factor(direction, levels = direct_directions)]
  p <- ggplot(d, aes(avg_log2FC_H146_vs_H526, neg_log10_FDR)) +
    geom_hline(yintercept = -log10(0.05), color = "#858B92", linewidth = 0.34, linetype = "dotted") +
    geom_vline(xintercept = c(-0.5, 0.5), color = "#858B92", linewidth = 0.34, linetype = "dotted") +
    geom_vline(xintercept = 0, color = "#4A4A4A", linewidth = 0.38, linetype = "solid") +
    geom_point(data = d[effect_qualified == FALSE], color = "#C7CBD1", alpha = 0.31, size = 0.53) +
    geom_point(data = d[effect_qualified == TRUE], color = "#7C8490", alpha = 0.40, size = 0.64) +
    geom_point(data = h, aes(fill = direction, color = direction), shape = 21,
      stroke = 0.72, size = 2.42, alpha = 0.94) +
    side_label_layers(h) +
    facet_wrap(~panel_label, nrow = 1, scales = "fixed") +
    scale_color_manual(values = direction_colors, breaks = direct_directions,
      labels = c("H526-high", "H146-high")) +
    scale_fill_manual(values = direction_fills, breaks = direct_directions,
      labels = c("H526-high", "H146-high")) +
    scale_x_continuous(expand = expansion(mult = c(0.012, 0.012))) +
    scale_y_continuous(expand = expansion(mult = c(0.012, 0.08))) +
    coord_cartesian(xlim = c(-direct_x_max, direct_x_max), clip = "off") +
    labs(
      title = title,
      subtitle = subtitle,
      x = "log2 fold change of mean CP10K (H146 / H526)",
      y = expression(-log[10]("BH FDR")),
      color = NULL, fill = NULL,
      caption = paste(
        "Positive x means H146-high; negative x means H526-high. Directional AUC ranks separation consistency after the fixed qualification gate.",
        "Two-sided Wilcoxon on log2(1+CP10K), BH within each tool/direct contrast; pair-only native eligibility and all named positive-depth H146/H526 cells.",
        "The three panels share one linear y scale. Exact FDR is shown with no cap, numerical floor, truncation, or free-y scaling.",
        "Cell-level contrasts from one mixed library are descriptive and are not biological-replicate inference.",
        sep = "\n"
      )
    ) + base_theme
  save_pair(p, basename, width = 24, height = 11.5, plot_set = plot_set, panels = 3L,
    full_points = nrow(d), selected_points = nrow(h), labels = nrow(h))
}

figure_manifest <- rbindlist(list(
  make_existing_overlay(
    focus_lines,
    "native_H146_H526_vs_rest_fixed_consensus_three_tool_overlay_uncapped",
    "Native H146/H526 versus-rest volcanoes: all three tools overlaid"
  ),
  make_existing_overlay(
    "H146",
    "native_H146_vs_rest_fixed_consensus_three_tool_overlay_uncapped",
    "H146 versus the other seven lines: all three tools overlaid"
  ),
  make_existing_overlay(
    "H526",
    "native_H526_vs_rest_fixed_consensus_three_tool_overlay_uncapped",
    "H526 versus the other seven lines: all three tools overlaid"
  ),
  make_direct_overlay(),
  make_direct_side_by_side(
    direct_fixed,
    "direct_H146_vs_H526_fixed_consensus_three_tools_side_by_side_uncapped",
    "Direct H146 versus H526: same consensus genes in every tool",
    "The same cross-tool consensus directional-AUC top 10 H146-high and H526-high genes are highlighted and ranked in all panels",
    "direct_fixed_consensus_side_by_side"
  ),
  make_direct_side_by_side(
    tool_top10,
    "direct_H146_vs_H526_tool_specific_top10_three_tools_side_by_side_uncapped",
    "Direct H146 versus H526: independent tool-specific AUC top tens",
    "Each tool independently labels H146#1-10 and H526#1-10 after the identical qualification gate",
    "direct_tool_specific_side_by_side"
  )
))
fwrite(figure_manifest, file.path(table_dir, "FIGURE_MANIFEST.tsv"), sep = "\t")

writeLines(capture.output(sessionInfo()), file.path(package_dir, "R_sessionInfo.txt"))
message("Built overlay/direct package at ", package_dir)
