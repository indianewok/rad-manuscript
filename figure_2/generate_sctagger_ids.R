generate_sctagger_ids<-function(input_fq, truth_csv, output_fq){
  fqs<-rad::read_fastqas(fn = input_fq)
  truth<-data.table::fread(truth_csv)
  fqs[,id := truth$V2]
  fqs[,id := paste0("@",id, "-", seq_len(.N)), by = id]
  rad::write_fastqas(df = fqs, fn = output_path)
}