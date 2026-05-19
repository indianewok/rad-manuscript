nolim_rad_rageseq_correction_pairs <- nolim_headers[
  , .N, by = .(final_barcode, original_barcode)
]
setnames(nolim_rad_rageseq_correction_pairs, "N", "read_count")

# Step 2: Compute entropy + Gini per final barcode
nolim_entropy_gini_rad <- nolim_rad_rageseq_correction_pairs[, {
  total <- sum(read_count)
  H <- entropy::entropy(read_count, unit = "log2")
  max_H <- if (.N > 1) log2(.N) else 0
  list(
    shannon_entropy = H,
    gini_index = DescTools::Gini(read_count),
    normalized_entropy = ifelse(max_H > 0, H / max_H, 0),
    unique_corrected_from = .N
  )
}, by = final_barcode]

# Step 3: Top contributor fraction per final barcode
nolim_top_contrib_rad <- nolim_rad_rageseq_correction_pairs[
  , .(top_contribution = max(read_count) / sum(read_count)),
  by = final_barcode
]

# Step 4: Join with wl_lim (assumed keyed by final_barcode)
nolim_rad_lim_total_summary <- merge(wl_nolimlim, nolim_entropy_gini_rad, by.x = "true_barcode", by.y = "final_barcode", all.x = TRUE)
nolim_rad_lim_total_summary <- merge(nolim_rad_lim_total_summary, nolim_top_contrib_rad, by.x = "true_barcode", by.y = "final_barcode", all.x = TRUE)
setnames(nolim_rad_total_summary, old = 'true_barcode', new = 'barcode')
# Step 5: Add derived metrics
nolim_rad_lim_total_summary[, corrected_fraction := corrected_ct / total_ct]
nolim_rad_lim_total_summary[!is.finite(normalized_entropy), normalized_entropy := 0]