suppressPackageStartupMessages({
  library(Seurat)
  library(data.table)
  library(ggplot2)
  library(viridis)
  library(patchwork)
  library(ggprism)
})

DATA_DIR <- Sys.getenv("HD_MAPPING_DIR")
if (DATA_DIR == "") stop("HD_MAPPING_DIR env var not set \u2014 see ../../README.md \u2192 Setup")
SAMPLES    <- c("PBC44593", "PBC44760", "PBC49262", "PBC52788")
REP_SAMPLE <- "PBC44593"

# ------------------------------------------------------------------
# Knobs
# ------------------------------------------------------------------
DOT_SIZE  <- 0.75     # round dot size for the spatial panels
PAL_BEGIN <- 0.00     # skip the darkest portion of plasma (0 = none, 0.4 = strong)
PAL_END   <- 1.00     # 1.00 keeps the brightest yellow
PAL_TRANS <- "identity"  # "identity" or "sqrt" -- sqrt stretches dark, brightens midtones

# ------------------------------------------------------------------
# Load data
# ------------------------------------------------------------------
tp16 <- fread(file.path(DATA_DIR, "tissue_positions_16um.csv"))
setnames(tp16, "barcode", "sr16")

cat("Loading Seurat...\n")
obj <- readRDS(file.path(DATA_DIR, "visium_hd_mouse_brain_016um_seurat.rds"))
seu_dt <- data.table(sr16 = colnames(obj),
                     seurat_count = obj$nCount_Spatial)
rm(obj); gc()

# log1p(ncpm) on Seurat counts (same recipe as RAD)
total_seu <- sum(seu_dt$seurat_count)
seu_dt[, seurat_log1p_ncpm := log1p(seurat_count * (1e6 / total_seu))]

# RAD log1p_ncpm (rep sample only)
wide  <- fread("sample_bin_matrix_16um.csv.gz")
ccol  <- paste0(REP_SAMPLE, "_count")
total <- sum(wide[[ccol]])
wide[, (paste0(REP_SAMPLE, "_log1p_ncpm")) := log1p(get(ccol) * (1e6 / total))]

grid <- copy(tp16)
grid[, in_tissue_b := in_tissue == 1]
grid <- merge(grid, seu_dt, by = "sr16", all.x = TRUE)
grid[, in_seurat := !is.na(seurat_count)]
grid[is.na(seurat_log1p_ncpm), seurat_log1p_ncpm := NA_real_]

wide_sub <- wide[, c("spaceranger_16um",
                     paste0(REP_SAMPLE, "_log1p_ncpm"),
                     paste0(REP_SAMPLE, "_valid")), with = FALSE]
setnames(wide_sub, "spaceranger_16um", "sr16")
grid <- merge(grid, wide_sub, by = "sr16", all.x = TRUE)

lcol <- paste0(REP_SAMPLE, "_log1p_ncpm")
vcol <- paste0(REP_SAMPLE, "_valid")
grid[is.na(get(vcol)), (vcol) := 0]

# ------------------------------------------------------------------
# Color range: full data range across both Seurat and RAD valid bins,
# so the two log1p_ncpm panels share a single unclipped scale.
# ------------------------------------------------------------------
rad_vals <- grid[get(vcol) == 1, get(lcol)]
seu_vals <- grid[in_seurat == TRUE, seurat_log1p_ncpm]
val_min  <- min(c(rad_vals, seu_vals), na.rm = TRUE)
val_max  <- max(c(rad_vals, seu_vals), na.rm = TRUE)
cat(sprintf("RAD range:    %.3f .. %.3f\n", min(rad_vals), max(rad_vals)))
cat(sprintf("Seurat range: %.3f .. %.3f\n", min(seu_vals), max(seu_vals)))
cat(sprintf("Shared scale: %.3f .. %.3f\n", val_min, val_max))

# ------------------------------------------------------------------
# Bare theme: no axes, no titles, no legend, no margins
# Use geom_raster (one tile per (col,row)) — eliminates the
# moire cross-hatch that geom_point + shape=15 introduces.
# ------------------------------------------------------------------
bare_theme <- theme_void() +
  theme(legend.position  = "none",
        plot.title       = element_blank(),
        plot.subtitle    = element_blank(),
        plot.caption     = element_blank(),
        plot.margin      = margin(0, 0, 0, 0),
        plot.background  = element_rect(fill = "white", color = NA),
        panel.background = element_rect(fill = "white", color = NA))

# Shared bounding box: full grid extent from tp16 — every panel renders into
# the same xlim/ylim so the tissue silhouette aligns across all three.
panel_xlim <- range(grid$array_col)
panel_ylim <- range(-grid$array_row)
cat(sprintf("Panel bounds: x=[%g, %g]  y=[%g, %g]\n",
            panel_xlim[1], panel_xlim[2], panel_ylim[1], panel_ylim[2]))

plasma_scale <- function() {
  scale_color_viridis_c(option = "plasma",
                        begin = PAL_BEGIN, end = PAL_END,
                        limits = c(val_min, val_max),
                        trans  = PAL_TRANS)
}

# panel 1: in_tissue mask
p1 <- ggplot(grid[in_tissue_b == TRUE]) +
  geom_point(aes(x = array_col, y = -array_row),
             color = "#666666", size = DOT_SIZE, shape = 19, stroke = 0) +
  coord_equal(xlim = panel_xlim, ylim = panel_ylim, expand = FALSE) +
  bare_theme

# panel 2: Seurat log1p_ncpm
p2 <- ggplot(grid[in_seurat == TRUE]) +
  geom_point(aes(x = array_col, y = -array_row, color = seurat_log1p_ncpm),
             size = DOT_SIZE, shape = 19, stroke = 0) +
  plasma_scale() +
  coord_equal(xlim = panel_xlim, ylim = panel_ylim, expand = FALSE) +
  bare_theme

# panel 3: RAD log1p_ncpm
p3 <- ggplot(grid[get(vcol) == 1]) +
  geom_point(aes(x = array_col, y = -array_row, color = get(lcol)),
             size = DOT_SIZE, shape = 19, stroke = 0) +
  plasma_scale() +
  coord_equal(xlim = panel_xlim, ylim = panel_ylim, expand = FALSE) +
  bare_theme

ggsave("overview_panel1_in_tissue_bare.png",         p1, width = 6, height = 6, dpi = 400)
ggsave("overview_panel2_seurat_log1p_ncpm_bare.png", p2, width = 6, height = 6, dpi = 400)
ggsave("overview_panel3_rad_log1p_ncpm_bare.png",    p3, width = 6, height = 6, dpi = 400)

# ------------------------------------------------------------------
# Standalone vertical colorbar with numeric labels (user will crop)
# Same plasma scale, same limits — matches both log1p_ncpm panels.
# ------------------------------------------------------------------
cb_df <- data.frame(x = 1, y = seq(val_min, val_max, length.out = 256),
                    z = seq(val_min, val_max, length.out = 256))

# ----- Option (a): linear log1p(ncpm) axis with Prism minor ticks -----
# Major at integer log1p(ncpm); 3 minor ticks between each pair of majors.
cb_major <- seq(ceiling(val_min), floor(val_max), by = 1)
cb_minor <- seq(floor(val_min), ceiling(val_max), by = 0.25)
cb_minor <- cb_minor[cb_minor > val_min & cb_minor < val_max & !(cb_minor %in% cb_major)]

p_cb <- ggplot(cb_df, aes(x = x, y = y, fill = z)) +
  geom_raster() +
  scale_fill_viridis_c(option = "plasma",
                       begin = PAL_BEGIN, end = PAL_END,
                       limits = c(val_min, val_max),
                       trans  = PAL_TRANS,
                       guide = "none") +
  scale_y_continuous(position = "right",
                     breaks = cb_major,
                     minor_breaks = cb_minor,
                     guide = guide_prism_minor(),
                     expand = c(0, 0)) +
  scale_x_continuous(expand = c(0, 0)) +
  labs(y = NULL, x = NULL) +
  theme_prism(base_size = 18, base_family = "Arial",
              border = FALSE, axis_text_angle = 0) +
  theme(axis.text.x  = element_blank(),
        axis.ticks.x = element_blank(),
        axis.title.x = element_blank(),
        panel.grid   = element_blank(),
        axis.line.y         = element_line(color = "black", linewidth = 0.5),
        axis.ticks.y        = element_line(color = "black", linewidth = 0.5),
        axis.ticks.length   = unit(6, "pt"),
        axis.ticks.length.y = unit(6, "pt"),
        axis.text.y  = element_text(size = 18, family = "Arial",
                                    face = "plain",
                                    margin = margin(l = 4)),
        plot.margin  = margin(8, 16, 8, 4))

# ----- Option (b): log-scale ncpm display, Prism hemi-log ticks --------
# Display ncpm values (not log1p(ncpm)) at log-spaced positions; the
# gradient color is still mapped via log1p(ncpm), so positions stay
# faithful to the data.
ncpm_major <- c(2, 10, 50)
ncpm_minor <- c(3:9, 20, 30, 40)
b_major <- log1p(ncpm_major)
b_minor <- log1p(ncpm_minor)
b_major <- b_major[b_major > val_min & b_major < val_max]
b_minor <- b_minor[b_minor > val_min & b_minor < val_max]

p_cb_b <- ggplot(cb_df, aes(x = x, y = y, fill = z)) +
  geom_raster() +
  scale_fill_viridis_c(option = "plasma",
                       begin = PAL_BEGIN, end = PAL_END,
                       limits = c(val_min, val_max),
                       trans  = PAL_TRANS,
                       guide = "none") +
  scale_y_continuous(position = "right",
                     breaks = b_major,
                     labels = ncpm_major[ncpm_major > expm1(val_min) &
                                          ncpm_major < expm1(val_max)],
                     minor_breaks = b_minor,
                     guide = guide_prism_minor(),
                     expand = c(0, 0)) +
  scale_x_continuous(expand = c(0, 0)) +
  labs(y = NULL, x = NULL) +
  theme_prism(base_size = 18, base_family = "Arial",
              border = FALSE, axis_text_angle = 0) +
  theme(axis.text.x  = element_blank(),
        axis.ticks.x = element_blank(),
        axis.title.x = element_blank(),
        panel.grid   = element_blank(),
        axis.line.y         = element_line(color = "black", linewidth = 0.5),
        axis.ticks.y        = element_line(color = "black", linewidth = 0.5),
        axis.ticks.length   = unit(6, "pt"),
        axis.ticks.length.y = unit(6, "pt"),
        axis.text.y  = element_text(size = 18, family = "Arial",
                                    face = "plain",
                                    margin = margin(l = 4)),
        plot.margin  = margin(8, 16, 8, 4))

ggsave("overview_colorbar_plasma_ncpm.png", p_cb_b,
       width = 1.6, height = 5, dpi = 400)

ggsave("overview_colorbar_plasma.png", p_cb, width = 1.6, height = 5, dpi = 400)

# ------------------------------------------------------------------
# Triptych: all three panels + colorbar on the far right, single image.
# patchwork enforces identical panel sizing; colorbar gets a narrow
# relative width with bigger Arial tick labels.
# ------------------------------------------------------------------
p_cb_inline <- p_cb +
  theme(axis.text.y = element_text(size = 18, family = "Arial"),
        plot.margin = margin(8, 12, 8, 4))

triptych <- p1 + p2 + p3 + p_cb_inline +
  plot_layout(nrow = 1, widths = c(1, 1, 1, 0.18))
ggsave("overview_triptych_bare.png", triptych,
       width = 19.5, height = 6, dpi = 400)

# Save the limits so the colorbar can always be regenerated identically
fwrite(data.table(val_min = val_min, val_max = val_max),
       "overview_panels_bare_color_limits.csv")

cat("\nWrote:\n",
    "  overview_panel1_in_tissue_bare.png\n",
    "  overview_panel2_seurat_log1p_ncpm_bare.png\n",
    "  overview_panel3_rad_log1p_ncpm_bare.png\n",
    "  overview_triptych_bare.png\n",
    "  overview_colorbar_plasma.png        (option a: log1p(ncpm) axis)\n",
    "  overview_colorbar_plasma_ncpm.png   (option b: ncpm log-scale axis)\n",
    "  overview_panels_bare_color_limits.csv\n", sep = "")
