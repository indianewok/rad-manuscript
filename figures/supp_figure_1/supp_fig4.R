suppressPackageStartupMessages({
  library(Seurat)
  library(data.table)
  library(ggplot2)
  library(viridis)
  library(patchwork)
  library(ggprism)
  library(ggbeeswarm)
})

DATA_DIR <- Sys.getenv("HD_MAPPING_DIR")
if (DATA_DIR == "") stop("HD_MAPPING_DIR env var not set \u2014 see README.md \u2192 Setup")
SAMPLES  <- c("PBC44593", "PBC44760", "PBC49262", "PBC52788")

# ------------------------------------------------------------------
# Original-figure palette
# ------------------------------------------------------------------
ALIGN_PAL <- c(`Both`        = "#2C7FB8",
               `RAD only`    = "#FDAE61",
               `Seurat only` = "#D7191C",
               `Neither`     = "grey70")

# ------------------------------------------------------------------
# Load
# ------------------------------------------------------------------
tp16 <- fread(file.path(DATA_DIR, "tissue_positions_16um.csv"))
setnames(tp16, "barcode", "sr16")

cat("Loading Seurat...\n")
obj <- readRDS(file.path(DATA_DIR, "visium_hd_mouse_brain_016um_seurat.rds"))
seu <- data.table(sr16 = colnames(obj),
                  seurat_count = as.numeric(obj$nCount_Spatial))
rm(obj); gc()
total_seu <- sum(seu$seurat_count)
seu[, seurat_log1p_ncpm := log1p(seurat_count * (1e6 / total_seu))]
seurat_bcs <- seu$sr16

wide <- fread("raw_data/sample_bin_matrix_16um.csv.gz")
for (s in SAMPLES) {
  ccol  <- paste0(s, "_count")
  total <- sum(wide[[ccol]])
  wide[, (paste0(s, "_log1p_ncpm")) := log1p(get(ccol) * (1e6 / total))]
}

grid <- copy(tp16[, .(sr16, array_row, array_col)])
grid[, in_seurat := sr16 %in% seurat_bcs]
keep <- c("spaceranger_16um",
          paste0(SAMPLES, "_count"),
          paste0(SAMPLES, "_log1p_ncpm"),
          paste0(SAMPLES, "_valid"))
wide_sub <- wide[, ..keep]
setnames(wide_sub, "spaceranger_16um", "sr16")
grid <- merge(grid, wide_sub, by = "sr16", all.x = TRUE)
for (s in SAMPLES) for (suf in c("_count","_log1p_ncpm","_valid")) {
  col <- paste0(s, suf); grid[is.na(get(col)), (col) := 0]
}

grid <- merge(grid, seu[, .(sr16, seurat_log1p_ncpm)], by = "sr16", all.x = TRUE)
grid[is.na(seurat_log1p_ncpm), seurat_log1p_ncpm := 0]

long <- rbindlist(lapply(SAMPLES, function(s) {
  v   <- grid[[paste0(s, "_valid")]] == 1
  seu <- grid$in_seurat
  data.table(
    sample     = s,
    array_row  = grid$array_row,
    array_col  = grid$array_col,
    log1p_ncpm = grid[[paste0(s, "_log1p_ncpm")]],
    seurat_log1p_ncpm = grid$seurat_log1p_ncpm,
    class_raw  = fifelse(v &  seu, "Both",
                 fifelse(v & !seu, "RAD only",
                 fifelse(!v &  seu, "Seurat only", "Neither")))
  )
}))
long[, class := factor(class_raw,
                       levels = c("Both", "RAD only", "Seurat only", "Neither"))]

# ------------------------------------------------------------------
# Themes
# ------------------------------------------------------------------
prism_plain <- function(base_size = 12) {
  theme_prism(base_size = base_size, base_family = "Arial",
              border = FALSE, axis_text_angle = 0) +
    theme(text         = element_text(family = "Arial", face = "plain"),
          axis.text    = element_text(family = "Arial", face = "plain"),
          axis.title   = element_text(family = "Arial", face = "plain"),
          axis.line    = element_line(color = "black", linewidth = 0.4),
          axis.ticks   = element_line(color = "black", linewidth = 0.4),
          strip.text   = element_text(family = "Arial", face = "plain"),
          legend.text  = element_text(family = "Arial", face = "plain"),
          legend.title = element_text(family = "Arial", face = "plain"),
          plot.title   = element_text(family = "Arial", face = "plain",
                                      hjust = 0.5),
          plot.margin  = margin(8, 8, 8, 8))
}

bare_theme <- theme_void(base_family = "Arial") +
  theme(legend.position  = "none",
        plot.title       = element_text(family = "Arial", size = 13,
                                        face = "plain", hjust = 0.5,
                                        margin = margin(b = 4)),
        plot.margin      = margin(0, 4, 0, 4),
        plot.background  = element_rect(fill = "white", color = NA),
        panel.background = element_rect(fill = "white", color = NA))

DOT_SIZE <- 0.40

panel_xlim <- range(grid$array_col)
panel_ylim <- range(-grid$array_row)

# ------------------------------------------------------------------
# Shared log10 axis breaks used by Panels B and E.
# ------------------------------------------------------------------
log_major <- c(0.01, 0.1, 1, 10, 100)
log_minor <- as.numeric(outer(2:9, 10^seq(-3, 1), `*`))
log_minor <- log_minor[log_minor >= min(log_major) &
                       log_minor <= max(log_major)]

# Strip-text styling shared by A and B so the per-sample columns align
# with matching title sizes.
sample_strip <- theme(
  strip.text = element_text(family = "Arial", size = 13, face = "plain",
                            margin = margin(b = 4)),
  strip.background = element_blank()
)

# ------------------------------------------------------------------
# Panel A: RAD spatial maps faceted by sample.
# Plotted across all RAD-valid bins (Both + RAD only); plasma scale
# shared across the four facets.
# ------------------------------------------------------------------
rad_valid_vals <- long[class == "Both" | class == "RAD only", log1p_ncpm]
val_min <- min(rad_valid_vals); val_max <- max(rad_valid_vals)

panel_A <- ggplot(long[class == "Both" | class == "RAD only"]) +
  geom_point(aes(x = array_col, y = -array_row, color = log1p_ncpm),
             size = DOT_SIZE, shape = 19, stroke = 0) +
  scale_color_viridis_c(option = "plasma", limits = c(val_min, val_max)) +
  coord_equal(xlim = panel_xlim, ylim = panel_ylim, expand = FALSE) +
  facet_wrap(~ sample, nrow = 1) +
  bare_theme + sample_strip

# ------------------------------------------------------------------
# Panel B: per-sample violins of counts per 16 um bin on a log10 axis,
# using the same four groups as Panel E (DP-Percula, DP-RAD, SP-RAD,
# Neither). Double-positive bins are plotted twice, once with Percula
# counts and once with RAD counts. Zero values are dropped (log axis).
# ------------------------------------------------------------------
panel_B_groups <- c("DP-Percula", "DP-RAD", "SP-RAD", "Neither")

b_dt <- rbindlist(list(
  long[class == "Both",     .(sample, group = "DP-Percula",
                              ncpm = expm1(seurat_log1p_ncpm))],
  long[class == "Both",     .(sample, group = "DP-RAD",
                              ncpm = expm1(log1p_ncpm))],
  long[class == "RAD only", .(sample, group = "SP-RAD",
                              ncpm = expm1(log1p_ncpm))],
  long[class == "Neither",  .(sample, group = "Neither",
                              ncpm = expm1(log1p_ncpm))]
))
b_dt[, group := factor(group, levels = panel_B_groups)]
b_dt <- b_dt[ncpm > 0]

b_pal <- setNames(c("#2C7FB8", "#5BA3D0", "#FDAE61", "grey70"),
                  panel_B_groups)
b_ns <- b_dt[, .(n = .N), by = .(sample, group)]

set.seed(42)
DOT_PER_GROUP <- 1500
b_dots <- b_dt[, .SD[sample(.N, min(.N, DOT_PER_GROUP))],
               by = .(sample, group)]

panel_B <- ggplot(b_dt, aes(x = group, y = ncpm, color = group)) +
  geom_quasirandom(data = b_dots, size = 0.45, stroke = 0, alpha = 0.55,
                   width = 0.32, varwidth = TRUE) +
  stat_summary(fun.min = function(x) quantile(x, 0.25),
               fun.max = function(x) quantile(x, 0.75),
               geom = "errorbar", width = 0.25,
               color = "black", linewidth = 0.5) +
  stat_summary(fun = median, geom = "crossbar",
               aes(ymin = after_stat(y), ymax = after_stat(y)),
               width = 0.40, color = "black", linewidth = 0.5,
               fatten = 0) +
  geom_text(data = b_ns,
            aes(x = group, y = 0.004, label = format(n, big.mark = ",")),
            size = 2.6, color = "grey30", inherit.aes = FALSE,
            family = "Arial") +
  scale_color_manual(values = b_pal, guide = "none") +
  scale_y_log10(breaks = log_major,
                minor_breaks = log_minor,
                labels = expression(10^-2, 10^-1, 10^0, 10^1, 10^2),
                limits = c(0.003, 100),
                guide = guide_prism_minor()) +
  facet_wrap(~ sample, nrow = 1) +
  labs(x = NULL, y = "Counts per 16 um bin") +
  prism_plain(base_size = 12) +
  sample_strip +
  theme(axis.text.x = element_text(angle = 45, hjust = 1, family = "Arial",
                                   face = "plain"))

# ------------------------------------------------------------------
# Panels C, D, E, F: per-sample "RAD only" spatial maps, plasma-colored.
# (Migrated from supp 5; one shared color scale across the 4.)
# ------------------------------------------------------------------
fp_vals <- long[class == "RAD only", log1p_ncpm]
fp_min  <- min(fp_vals); fp_max <- max(fp_vals)

make_fp_panel <- function(s) {
  d_all <- long[sample == s, .(array_row, array_col)]
  d     <- long[sample == s & class == "RAD only"]
  ggplot() +
    geom_point(data = d_all, aes(x = array_col, y = -array_row),
               color = "grey94", size = DOT_SIZE, shape = 19, stroke = 0) +
    geom_point(data = d,
               aes(x = array_col, y = -array_row, color = log1p_ncpm),
               size = DOT_SIZE, shape = 19, stroke = 0) +
    scale_color_viridis_c(option = "plasma", limits = c(fp_min, fp_max)) +
    coord_equal(xlim = panel_xlim, ylim = panel_ylim, expand = FALSE) +
    labs(title = sprintf("%s  RAD only (n=%s)",
                         s, format(nrow(d), big.mark = ","))) +
    bare_theme
}
panel_C <- wrap_elements(full = wrap_plots(lapply(SAMPLES, make_fp_panel),
                                            nrow = 1))

# ------------------------------------------------------------------
# Panel D: cross-sample Pearson correlation heatmap (RAD log1p_ncpm
# on in_tissue bins). Green gradient.
# ------------------------------------------------------------------
corr_dt <- fread("raw_data/sample_correlations_16um.csv")
corr_dt[, a := factor(a, levels = SAMPLES)]
corr_dt[, b := factor(b, levels = SAMPLES)]

panel_D <- ggplot(corr_dt, aes(x = a, y = b, fill = pearson_log1p_intissue)) +
  geom_tile(color = "white", linewidth = 0.5) +
  geom_text(aes(label = sprintf("%.3f", pearson_log1p_intissue)),
            family = "Arial", size = 4, fontface = "plain") +
  scale_fill_gradient(low = "#F1F8E9", high = "#2E7D32",
                      limits = c(0.98, 1.00), guide = "none") +
  coord_equal() +
  labs(x = NULL, y = NULL) +
  prism_plain(base_size = 12) +
  theme(panel.grid = element_blank(),
        axis.line  = element_blank(),
        axis.ticks = element_blank(),
        axis.text.x = element_text(angle = 45, hjust = 1, family = "Arial",
                                   face = "plain"),
        plot.margin = margin(8, 8, 24, 8))

# ------------------------------------------------------------------
# Panel E: kernel-density violins of ncpm on a log10 axis, pooled
# across all four samples, for: double-positive Percula values,
# double-positive RAD values, single-positive RAD values, and
# Neither (RAD values). Zero values are dropped (log10 axis); they
# account for ~27% of the Neither group and 0% of the other three.
# Five major hemi-log ticks (0.01, 0.1, 1, 10, 100) with the 2-9
# intermediate minor ticks in each decade.
# ------------------------------------------------------------------
group_levels <- c("DP-Percula", "DP-RAD", "SP-RAD", "Neither")

e_dt <- rbind(
  data.table(group = group_levels[1],
             value = expm1(long[class == "Both",     seurat_log1p_ncpm])),
  data.table(group = group_levels[2],
             value = expm1(long[class == "Both",     log1p_ncpm])),
  data.table(group = group_levels[3],
             value = expm1(long[class == "RAD only", log1p_ncpm])),
  data.table(group = group_levels[4],
             value = expm1(long[class == "Neither",  log1p_ncpm]))
)
e_dt[, group := factor(group, levels = group_levels)]
e_dt <- e_dt[value > 0]   # drop zeros so log10 is well defined

E_PAL <- setNames(c("#2C7FB8", "#5BA3D0", "#FDAE61", "grey70"), group_levels)

e_n <- e_dt[, .(n = .N), by = group]
# log_major / log_minor reused from Panel B (defined above)

panel_E <- ggplot(e_dt, aes(x = group, y = value, fill = group)) +
  geom_violin(scale = "width", trim = TRUE, alpha = 0.65,
              linewidth = 0.3, color = "grey25") +
  stat_summary(fun.min = function(x) quantile(x, 0.25),
               fun.max = function(x) quantile(x, 0.75),
               geom = "errorbar", width = 0.22,
               color = "black", linewidth = 0.5) +
  stat_summary(fun = median, geom = "crossbar",
               aes(ymin = after_stat(y), ymax = after_stat(y)),
               width = 0.36, color = "black", linewidth = 0.5,
               fatten = 0) +
  geom_text(data = e_n,
            aes(x = group, y = 0.004, label = format(n, big.mark = ",")),
            size = 2.6, color = "grey30", inherit.aes = FALSE,
            family = "Arial") +
  scale_fill_manual(values = E_PAL, guide = "none") +
  scale_y_log10(breaks = log_major,
                minor_breaks = log_minor,
                labels = expression(10^-2, 10^-1, 10^0, 10^1, 10^2),
                limits = c(0.005, 100),
                guide = guide_prism_minor()) +
  labs(x = NULL, y = "Counts per 16 um bin") +
  prism_plain(base_size = 12) +
  theme(axis.text.x = element_text(family = "Arial", face = "plain",
                                   size = 10, lineheight = 0.9))

# ------------------------------------------------------------------
# Compose
# ------------------------------------------------------------------
bottom_row <- panel_D + panel_E + plot_layout(widths = c(1, 1.5))
supp_fig <- panel_A / panel_B / panel_C / bottom_row +
  plot_layout(heights = c(1.0, 0.9, 1.0, 0.9)) +
  plot_annotation(tag_levels = list(c("A", "B", "C", "D", "E")),
                  theme = theme(plot.tag = element_text(family = "Arial",
                                                        face = "plain",
                                                        size = 16)))

# Render PDF first via cairo, then rasterize to PNG via ghostscript so the
# two outputs are pixel-identical. macOS extended attributes can lock an
# existing file against ggsave overwrite, so unlink before writing.
unlink(c("supp_figure_1.pdf", "supp_figure_1.png"))

ggsave("supp_figure_1.pdf", supp_fig,
       width = 14, height = 18, device = cairo_pdf)
cat(sprintf("PDF size: %.1f MB\n",
            file.info("supp_figure_1.pdf")$size / 1e6))

gs_bin <- Sys.which("gs")
if (nzchar(gs_bin)) {
  status <- system2(gs_bin,
                    args = c("-sDEVICE=png16m",
                             "-r400",
                             "-dNOPAUSE", "-dBATCH", "-q",
                             "-sOutputFile=supp_figure_1.png",
                             "supp_figure_1.pdf"))
  if (status != 0) stop("ghostscript conversion failed (status=", status, ")")
} else {
  warning("ghostscript not found, falling back to ggsave PNG")
  ggsave("supp_figure_1.png", supp_fig,
         width = 14, height = 18, dpi = 400)
}
cat("Wrote: supp_figure_1.png and supp_figure_1.pdf\n")

# ------------------------------------------------------------------
# Stats
# ------------------------------------------------------------------
counts_tbl <- long[, .(n = .N), by = .(sample, class)]
counts_wide <- dcast(counts_tbl, sample ~ class, value.var = "n", fill = 0)
counts_wide[, recovery_pct := 100 * Both / (Both + `Seurat only`)]
counts_wide[, total_in_seurat := Both + `Seurat only`]
counts_wide[, total_in_rad    := Both + `RAD only`]
fwrite(counts_wide, "supp_fig4_counts.csv")
print(counts_wide)

class_summary <- long[class != "Neither",
                      .(n = .N,
                        mean   = round(mean(log1p_ncpm), 2),
                        median = round(median(log1p_ncpm), 2),
                        q25    = round(quantile(log1p_ncpm, 0.25), 2),
                        q75    = round(quantile(log1p_ncpm, 0.75), 2)),
                      by = .(sample, class)]
fwrite(class_summary, "supp_fig4_class_logncpm_summary.csv")
print(class_summary)

cat("\nDone.\n")
