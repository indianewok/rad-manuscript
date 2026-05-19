suppressPackageStartupMessages({
  library(Seurat)
  library(data.table)
})

DATA_DIR <- Sys.getenv("HD_MAPPING_DIR")
if (DATA_DIR == "") stop("HD_MAPPING_DIR env var not set \u2014 see README.md \u2192 Setup")
SAMPLES  <- c("PBC44593", "PBC44760", "PBC49262", "PBC52788")

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

grid <- copy(tp16[, .(sr16)])
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
    sample            = s,
    log1p_ncpm        = grid[[paste0(s, "_log1p_ncpm")]],
    seurat_log1p_ncpm = grid$seurat_log1p_ncpm,
    class             = fifelse(v &  seu, "Both",
                        fifelse(v & !seu, "RAD only",
                        fifelse(!v &  seu, "Seurat only", "Neither")))
  )
}))

dp_percula <- long[class == "Both",     seurat_log1p_ncpm]
dp_rad     <- long[class == "Both",     log1p_ncpm]
sp_rad     <- long[class == "RAD only", log1p_ncpm]
neither    <- long[class == "Neither",  log1p_ncpm]

n_max <- max(length(dp_percula), length(dp_rad), length(sp_rad), length(neither))
pad <- function(v, n) c(v, rep(NA_real_, n - length(v)))

panel_E_wide <- data.table(
  double_positive_Percula = pad(dp_percula, n_max),
  double_positive_RAD     = pad(dp_rad,     n_max),
  single_positive_RAD     = pad(sp_rad,     n_max),
  Neither                 = pad(neither,    n_max)
)
fwrite(panel_E_wide, "panel_E_four_groups_wide.csv", na = "")
cat(sprintf("Wrote panel_E_four_groups_wide.csv  n_DP_Percula=%d  n_DP_RAD=%d  n_SP_RAD=%d  n_Neither=%d\n",
            length(dp_percula), length(dp_rad), length(sp_rad), length(neither)))

# Also export Panel E summary stats
panel_E_stats <- data.table(
  group  = c("double_positive_Percula", "double_positive_RAD",
             "single_positive_RAD",     "Neither"),
  n      = c(length(dp_percula), length(dp_rad), length(sp_rad), length(neither)),
  mean   = c(mean(dp_percula), mean(dp_rad), mean(sp_rad), mean(neither)),
  median = c(median(dp_percula), median(dp_rad), median(sp_rad), median(neither)),
  sd     = c(sd(dp_percula), sd(dp_rad), sd(sp_rad), sd(neither)),
  q25    = c(quantile(dp_percula, 0.25), quantile(dp_rad, 0.25),
             quantile(sp_rad, 0.25),     quantile(neither, 0.25)),
  q75    = c(quantile(dp_percula, 0.75), quantile(dp_rad, 0.75),
             quantile(sp_rad, 0.75),     quantile(neither, 0.75))
)
fwrite(panel_E_stats, "panel_E_four_groups_stats.csv")
print(panel_E_stats)

cat("Done.\n")
