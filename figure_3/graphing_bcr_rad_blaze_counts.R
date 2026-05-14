####
blaze_bcr<-data.table::fread(
  "/Users/cmv/Desktop/rad_paper/061125_blaze_bcr_full_timing/extracted_headers.csv")

rad_barcode_counts<-data.table::fread(
  "/Users/cmv/Desktop/rad_paper/061025_rad_nbc_full_timing/nbc_whitelist_true.csv")

raw_blaze_data<-data.table::fread(
  "/Users/cmv/Desktop/rad_paper/061125_blaze_bcr_full_timing/putative_bc.csv", na.strings = "")

raw_blaze_bcs<-raw_blaze_data[,.N,by = 'putative_bc']
processed_blaze_bcs<-blaze_bcr[,.N,by = 'barcode']
rad_barcodes<-rad_barcode_counts[,c('true_barcode','total_count','raw_count','corrected_count')]
setnames(rad_barcodes, c('barcode','total_rad_count','raw_rad_count','corrected_rad_count'))
setnames(processed_blaze_bcs, c('barcode','total_blaze_count'))
setnames(raw_blaze_bcs, c('barcode','raw_blaze_count'))
raw_blaze_bcs<-raw_blaze_bcs[rad_barcodes$barcode,]

####
total_cts<-Reduce(
  function(...){merge(..., all = TRUE, by = "barcode", list(rad_barcodes, raw_blaze_bcs, processed_blaze_bcs))
})

####
ggviolin(percent_of_total_correct, x = 'tool', y = 'percent',
         add = c('boxplot', 'jitter', 'mean_sd'),
         add.params = list(size = 0.3, alpha = 0.2, color = 'tool'),
         draw_quantiles = c(0.25, 0.5, 0.75),
         quantile_lines = list(linetype = "dotted"),  # makes quantile lines dotted
         outlier.shape = 16,
         outlier.size = 2) +
  stat_summary(fun.data = mean_sdl, geom = "errorbar", width = 0.1) +
  stat_summary(fun = mean, geom = "point", shape = 18, size = 3, color = "red") +
  theme(legend.position = "right") +
  labs(y = "Percent of total reads per cell corrected") +
  scale_x_discrete(labels = c("RAD", "BLAZE"))

####
ggscatter(total_cts, x = 'total_blaze_count', y = 'total_rad_count',
          add = "reg.line", conf.int = TRUE, cor.coef = TRUE,
          add.params = list(color = 'red', linetype = 'dashed'), 
          color = ' black', 
          alpha = 0.2, 
          size = 'blaze_percent_of_total_corrected',
          xlab = "Total Count Per Cell (BLAZE)", 
          ylab = "Total Count Per Cell (RAD)", 
          main = "Total Counts Per Cell\nRad vs. BLAZE, BCR Data") + 
  geom_abline(
          slope = 1,
          intercept = 0,
          linetype = 'dashed',
          color = 'blue') + 
  stat_regline_equation(
          aes(label = ..eq.label..), 
              label.x.npc = "left",
              label.y.npc = 0.93)
