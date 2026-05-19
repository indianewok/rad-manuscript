suppressPackageStartupMessages({
  library(Seurat)
  library(data.table)
})

DATA_DIR <- Sys.getenv("HD_MAPPING_DIR")
if (DATA_DIR == "") stop("HD_MAPPING_DIR env var not set \u2014 see README.md \u2192 Setup")
SAMPLES  <- c("PBC44593", "PBC44760", "PBC49262", "PBC52788")

# ------------------------------------------------------------------
# Load Percula (Seurat) counts
# ------------------------------------------------------------------
tp16 <- fread(file.path(DATA_DIR, "tissue_positions_16um.csv"))
setnames(tp16, "barcode", "sr16")

cat("Loading Seurat...\n")
obj <- readRDS(file.path(DATA_DIR, "visium_hd_mouse_brain_016um_seurat.rds"))
seu <- data.table(sr16          = colnames(obj),
                  percula_count = as.numeric(obj$nCount_Spatial))
rm(obj); gc()
total_percula <- sum(seu$percula_count)
seu[, percula_ncpm := percula_count * (1e6 / total_percula)]
seurat_bcs <- seu$sr16

# ------------------------------------------------------------------
# Load RAD counts per sample
# ------------------------------------------------------------------
wide <- fread("raw_data/sample_bin_matrix_16um.csv.gz")
for (s in SAMPLES) {
  ccol  <- paste0(s, "_count")
  total <- sum(wide[[ccol]])
  wide[, (paste0(s, "_ncpm")) := get(ccol) * (1e6 / total)]
}

grid <- copy(tp16[, .(sr16)])
grid[, in_seurat := sr16 %in% seurat_bcs]
keep <- c("spaceranger_16um",
          paste0(SAMPLES, "_count"),
          paste0(SAMPLES, "_ncpm"),
          paste0(SAMPLES, "_valid"))
wide_sub <- wide[, ..keep]
setnames(wide_sub, "spaceranger_16um", "sr16")
grid <- merge(grid, wide_sub, by = "sr16", all.x = TRUE)
for (s in SAMPLES) for (suf in c("_count","_ncpm","_valid")) {
  col <- paste0(s, suf); grid[is.na(get(col)), (col) := 0]
}
grid <- merge(grid, seu[, .(sr16, percula_count, percula_ncpm)],
              by = "sr16", all.x = TRUE)
grid[is.na(percula_count), percula_count := 0]
grid[is.na(percula_ncpm),  percula_ncpm  := 0]

# ------------------------------------------------------------------
# Long table with raw count + ncpm per (sample, bin)
# ------------------------------------------------------------------
long <- rbindlist(lapply(SAMPLES, function(s) {
  v <- grid[[paste0(s, "_valid")]] == 1
  data.table(
    sample        = s,
    rad_count     = grid[[paste0(s, "_count")]],
    rad_ncpm      = grid[[paste0(s, "_ncpm")]],
    percula_count = grid$percula_count,
    percula_ncpm  = grid$percula_ncpm,
    class = fifelse(v &  grid$in_seurat, "Both",
            fifelse(v & !grid$in_seurat, "RAD only",
            fifelse(!v &  grid$in_seurat, "Seurat only", "Neither")))
  )
}))

# ------------------------------------------------------------------
# Build the four Panel E groups
# ------------------------------------------------------------------
dp_percula_count <- long[class == "Both",     percula_count]
dp_percula_ncpm  <- long[class == "Both",     percula_ncpm]
dp_rad_count     <- long[class == "Both",     rad_count]
dp_rad_ncpm      <- long[class == "Both",     rad_ncpm]
sp_rad_count     <- long[class == "RAD only", rad_count]
sp_rad_ncpm      <- long[class == "RAD only", rad_ncpm]
neither_count    <- long[class == "Neither",  rad_count]
neither_ncpm     <- long[class == "Neither",  rad_ncpm]

n_max <- max(length(dp_percula_count), length(dp_rad_count),
             length(sp_rad_count),     length(neither_count))
pad <- function(v, n) c(v, rep(NA_real_, n - length(v)))

raw_counts_wide <- data.table(
  double_positive_Percula = pad(dp_percula_count, n_max),
  double_positive_RAD     = pad(dp_rad_count,     n_max),
  single_positive_RAD     = pad(sp_rad_count,     n_max),
  Neither                 = pad(neither_count,    n_max)
)
ncpm_wide <- data.table(
  double_positive_Percula = pad(dp_percula_ncpm, n_max),
  double_positive_RAD     = pad(dp_rad_ncpm,     n_max),
  single_positive_RAD     = pad(sp_rad_ncpm,     n_max),
  Neither                 = pad(neither_ncpm,    n_max)
)

fwrite(raw_counts_wide, "panel_E_four_groups_raw_counts.csv", na = "")
fwrite(ncpm_wide,       "panel_E_four_groups_ncpm.csv",       na = "")

cat(sprintf("\nWrote raw counts and ncpm wide CSVs (max n = %d rows)\n", n_max))
cat(sprintf("  group sizes: DP Percula=%d  DP RAD=%d  SP RAD=%d  Neither=%d\n",
            length(dp_percula_count), length(dp_rad_count),
            length(sp_rad_count),     length(neither_count)))

# Summary stats on the raw scale
panel_E_raw_stats <- data.table(
  group = c("double_positive_Percula", "double_positive_RAD",
            "single_positive_RAD",     "Neither"),
  n          = c(length(dp_percula_count), length(dp_rad_count),
                 length(sp_rad_count),     length(neither_count)),
  raw_mean   = c(mean(dp_percula_count), mean(dp_rad_count),
                 mean(sp_rad_count),     mean(neither_count)),
  raw_median = c(median(dp_percula_count), median(dp_rad_count),
                 median(sp_rad_count),     median(neither_count)),
  raw_q25    = c(quantile(dp_percula_count, 0.25), quantile(dp_rad_count, 0.25),
                 quantile(sp_rad_count,     0.25), quantile(neither_count, 0.25)),
  raw_q75    = c(quantile(dp_percula_count, 0.75), quantile(dp_rad_count, 0.75),
                 quantile(sp_rad_count,     0.75), quantile(neither_count, 0.75)),
  ncpm_mean   = c(mean(dp_percula_ncpm), mean(dp_rad_ncpm),
                  mean(sp_rad_ncpm),     mean(neither_ncpm)),
  ncpm_median = c(median(dp_percula_ncpm), median(dp_rad_ncpm),
                  median(sp_rad_ncpm),     median(neither_ncpm))
)
fwrite(panel_E_raw_stats, "panel_E_four_groups_raw_stats.csv")
print(panel_E_raw_stats)
cat("Done.\n")
