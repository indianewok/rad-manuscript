
metadata<-data.table::fread(
  "/Volumes/PostRot/swedish_tonsil_spatial/EGAD00001011062_metadata/study_experiment_run_sample.csv", header = TRUE
  )
sample_metadata<-data.table::fread(
  "/Volumes/PostRot/swedish_tonsil_spatial/EGAD00001011062_metadata/sample_file.csv", header = TRUE
  )
LR_metadata<-metadata[grep(pattern = "demultiplex", x = sample_alias),]
LR_metadata<-sample_metadata[,c('sample_alias','file_accession_id')][LR_metadata, on = 'sample_alias']

spaceranger_output<-list.files(
  path = "/Volumes/PostRot/swedish_tonsil_spatial/data/tonsil/5_spatial_GEX/spaceranger_output/", 
  recursive = TRUE, 
  pattern = "csv", 
  full.names = TRUE
) %>% {sapply(., FUN = function(X){
    data.table::fread(X) %>% 
    setnames(., new = c("barcode","in_tissue","x_coord","y_coord","y_coord_pix","x_coord_pix")) %>% 
    .[,barcode := gsub(pattern = "-1", replacement = "", x = barcode)]
  }, simplify = FALSE, USE.NAMES = TRUE)}

names(spaceranger_output)[8]<-"tonsil1_spatialGEX_section_B"
names(spaceranger_output)[7]<-"tonsil1_spatialGEX_section_A"
names(spaceranger_output)[6]<-"tonsil2_LR-SpatialVDJ_section32"
names(spaceranger_output)[5]<-"tonsil2_LR-SpatialVDJ_section31"
names(spaceranger_output)[4]<-"tonsil2_LR-SpatialVDJ_section21"
names(spaceranger_output)[3]<-"tonsil2_LR-SpatialVDJ_section17"
names(spaceranger_output)[2]<-"tonsil2_LR-SpatialVDJ_section16"
names(spaceranger_output)[1]<-"tonsil2_LR-SpatialVDJ_section12"

spaceranger_mappings<-list.files(
  path = "/Volumes/PostRot/swedish_tonsil_spatial/data/tonsil/5_spatial_GEX/spaceranger_output/", 
  recursive = TRUE, 
  pattern = "csv", 
  full.names = TRUE
  ) %>% dirname %>% dirname %>% dirname %>% basename
spaceranger_mappings<-data.table(sample_short = spaceranger_mappings, full_sample_name = names(spaceranger_output))

spaceranger_results<-rbindlist(l = spaceranger_output, idcol = 'sample_title')
spaceranger_results<-spaceranger_results[grep(
  pattern = "tonsil1", x = sample_title, invert = TRUE),][,in_tissue := as.logical(in_tissue)]

rad_barcode_results<-lapply(
  list.files(path = "/Volumes/CMV_SSD_2/results/rad/whitelist_detection/120525_visium_data_results/", pattern = ".csv", 
             recursive = FALSE, full.names = TRUE),
  FUN = function(X){fread(X)
})
names(rad_barcode_results)<-tools::file_path_sans_ext(basename(
  list.files(path = "/Volumes/CMV_SSD_2/results/rad/whitelist_detection/120525_visium_data_results/", pattern = ".csv", 
             recursive = FALSE, full.names = TRUE)
  )
)
rad_barcode_results<-rbindlist(l = rad_barcode_results, idcol = 'sample')
rad_barcode_results<-LR_metadata[,c('file_accession_id','sample_title')][rad_barcode_results, 
                                                                         on = c('file_accession_id' = 'sample')]
rad_section_12<-rad_barcode_results[sample_title == "tonsil2_LR-SpatialVDJ_section12",]
spaceranger_section_12<-spaceranger_results[sample_title == "tonsil2_LR-SpatialVDJ_section12",]
sct12<-rad_section_12[spaceranger_section_12[,c('barcode','in_tissue','x_coord_pix','y_coord_pix')], on = 'barcode']


total_samples<-lapply(
  unique(rad_barcode_results$sample_title), FUN = function(sample){
  print(paste0("Now working on sample: ", sample,"!"))
    
  rad_section<-rad_barcode_results[sample_title == sample,]
  
  
  if(!sample %in% spaceranger_mappings$full_sample_name){
    space_trimmed_sample<-gsub(pattern = "_.T_.B", replacement = "", x = sample)
    space_sample<-spaceranger_mappings[full_sample_name == space_trimmed_sample, sample_short]
  } else {
    space_sample<-spaceranger_mappings[full_sample_name == sample, sample_short]
  }
  
  print(space_sample)
  
  if(!sample %in% spaceranger_mappings$full_sample_name){
    spaceranger_section<-spaceranger_results[sample_title == space_trimmed_sample,]
  } else {
    spaceranger_section<-spaceranger_results[sample_title == sample,]
  }
  merged_section<-rad_section[spaceranger_section[,c('barcode','in_tissue','x_coord_pix','y_coord_pix')], on = 'barcode']
  print(paste0("/Volumes/PostRot/swedish_tonsil_spatial/data/tonsil/5_spatial_GEX/spaceranger_output/",
               space_sample,
               "/outs/spatial/scalefactors_json.json"))
  scales<-jsonlite::fromJSON(txt =paste0("/Volumes/PostRot/swedish_tonsil_spatial/data/tonsil/5_spatial_GEX/spaceranger_output/",
           space_sample,
           "/outs/spatial/scalefactors_json.json")
    )
  merged_section[,y_pix_scaled := y_coord_pix*scales$tissue_hires_scalef][,x_pix_scaled := x_coord_pix*scales$tissue_hires_scalef]

  merged_section[is.na(final_bc_annotation), 
        final_bc_annotation:="undetected"]
  merged_section[is.na(final_barcode), 
        final_barcode := FALSE][is.na(over_threshold), 
                                over_threshold := FALSE][is.na(above_floor), 
                                                         above_floor := FALSE]
  merged_section[is.na(ztpois_percentile), 
        ztpois_percentile := 0][is.na(log1p_ncpm), 
                                count := 0][is.na(ncpm), 
                                            ncpm := 0][is.na(count), 
                                                       count := 0]
  
  merged_section[is.na(sample_title), sample_title := sample]
  merged_section[, class :=
                   fcase(
                     final_barcode &  in_tissue, "TP",
                     final_barcode & !in_tissue, "FP",
                     !final_barcode & !in_tissue, "TN",
                     !final_barcode &  in_tissue, "FN"
                   )
  ]
  print(paste0("Done with sample ", sample, "!"))
  return(merged_section)
})


scales<-jsonlite::fromJSON("/Volumes/PostRot/swedish_tonsil_spatial/data/tonsil/5_spatial_GEX/spaceranger_output/V10T03-276_C1/outs/spatial/scalefactors_json.json")
sct12[,y_pix_scaled := y_coord_pix*scales$tissue_hires_scalef][,x_pix_scaled := x_coord_pix*scales$tissue_hires_scalef]

sct12[, class :=
     fcase(
       final_barcode &  in_tissue, "TP",
       final_barcode & !in_tissue, "FP",
       !final_barcode & !in_tissue, "TN",
       !final_barcode &  in_tissue, "FN"
     )
]

sct12[is.na(final_bc_annotation), 
      final_bc_annotation:="undetected"]
sct12[is.na(final_barcode), 
      final_barcode := FALSE][is.na(over_threshold), 
                              over_threshold := FALSE][is.na(above_floor), 
                                                       above_floor := FALSE]
sct12[is.na(ztpois_percentile), 
      ztpois_percentile := 0][is.na(log1p_ncpm), 
                              count := 0][is.na(ncpm), 
                                          ncpm := 0][is.na(count), 
                                                     count := 0]

sct12[is.na(sample_title), sample_title := "tonsil2_LR-SpatialVDJ_section12"]

he_img<-magick::image_read(
  "/Volumes/PostRot/swedish_tonsil_spatial/data/tonsil/5_spatial_GEX/spaceranger_output/V10T03-276_C1/outs/spatial/tissue_hires_image.png"
  )
he_rast<-as.raster(he_img)
info<-image_info(he_img)
img_w<-info$width
img_h<-info$height

p <- ggplot(sct12, aes(x = y_pix_scaled, y = x_pix_scaled)) +
  annotation_raster(
    he_rast,
    xmin = 0, xmax = img_w,
    ymin = 0, ymax = img_h
  ) +
  geom_point(
    aes(fill = class),
    alpha  = 0.2,
    size   = 1.5,
    shape  = 21,         # circle with fill + border
    color  = "black",    # border outline
    stroke = 0.5
  ) +
  scale_fill_manual(
    values = c(
      "TP"  = "#009A00",  # strong green
      "FP" = "#000000",  # black
      "TN"  = "grey70",   # mid grey
      "FN" = "#66CC66"   # light green
    )
  ) +
  coord_equal() +
  scale_y_reverse() +
  theme_pubr()

p


