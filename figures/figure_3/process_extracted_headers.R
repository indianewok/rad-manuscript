process_extracted_rad_headers<-function(path, mode = "regular"){
  header_dt<-data.table::fread(path, na.strings = "")
  header_dt[is.na(original_barcode), original_barcode := final_barcode]
  header_dt[, corrected := ((final_barcode != original_barcode) & (final_barcode != rad::revcomp(original_barcode)))]
  if(mode == "synth"){
    header_dt[,true_barcode:=gsub(pattern = "-.+", replacement = "", x = id)]
    header_dt[, incorrect := ((final_barcode != true_barcode) & (final_barcode != rad::revcomp(true_barcode)))]
  }
  return(header_dt)
}

process_extracted_blaze_headers<-function(path){
  header_dt<-data.table::fread(path, na.strings = "")
  putative_bcs<-data.table::fread(
    list.files(dirname(path), "putative_bc.csv", full.names = TRUE),
    na.strings = "")
  setnames(putative_bcs, old = 'read_id', new = 'id')
  putative_bcs<-putative_bcs[,c('id','putative_bc')]
  header_dt<-putative_bcs[header_dt, on = 'id']
  rm(putative_bcs)
  setnames(header_dt, old = c('putative_bc', 'barcode'), new = c('original_barcode', 'final_barcode'))
  if(any(grepl(header_dt$id, pattern = "\\-\\d+$"))){
    header_dt[,true_barcode := gsub(pattern = "-.+", replacement = "", x = id)]
    header_dt[, incorrect := ((final_barcode != true_barcode) & (final_barcode != rad::revcomp(true_barcode)))]
  }
  header_dt[, corrected := ((final_barcode != original_barcode) & (final_barcode != rad::revcomp(original_barcode)))]
  return(header_dt)
}