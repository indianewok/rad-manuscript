#!/usr/bin/env Rscript
# Sensitivity run: unchanged component engine at ED2, terminal poly(T) omitted.
root <- "/Volumes/CMV_SSD_2/benchmarks/splitseq_component_recovery_20260921/flexiplex_no_polyt_ed2_native"
flames <- "/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/FLAMES"
input <- "/Volumes/CMV_SSD_2/raw_fqs/splitseq.fq.gz"
wlroot <- "/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/inputs/local_whitelists"
v1 <- file.path(wlroot,"bc_8nt_v1.csv")
v2 <- file.path(wlroot,"bc_8nt_v2.csv")
stopifnot(!file.exists(file.path(root,"stats.tsv.gz")))
for (path in c(v1,v2)) {
  values <- trimws(readLines(path))
  stopifnot(length(values)==96L, length(unique(values))==96L,
            all(grepl("^[ACGT]{8}$",values)))
}
commit <- system2("git",c("-C",shQuote(flames),"rev-parse","HEAD"),stdout=TRUE)
stopifnot(identical(commit,"bf2211a8da1e1c7327370ab12479ae70e1d37cd8"))
stopifnot(requireNamespace("Rcpp",quietly=TRUE),requireNamespace("Rhtslib",quietly=TRUE))
cppflags <- paste(capture.output(Rhtslib::pkgconfig("PKG_CPPFLAGS")),collapse=" ")
libs <- paste(capture.output(Rhtslib::pkgconfig("PKG_LIBS")),collapse=" ")
Sys.setenv(PKG_CPPFLAGS=paste("-pthread",cppflags),PKG_LIBS=paste("-pthread -lz",libs))
source_code <- sprintf(paste0(
  '#include "%s"\n#include "%s"\n',
  '// [[Rcpp::export]]\n',
  'Rcpp::IntegerVector run_native(Rcpp::List segments, Rcpp::List groups, ',
  'int max_flank_ed, Rcpp::StringVector reads_in, Rcpp::String reads_out, ',
  'Rcpp::String stats_out, Rcpp::String bc_out, bool reverse_complement, int threads) {',
  'return flexiplex_cpp(segments,groups,max_flank_ed,reads_in,reads_out,stats_out,bc_out,reverse_complement,threads);}\n'),
  file.path(flames,"src/utility/edlib-1.2.7/edlib.cpp"),
  file.path(flames,"src/main-functions/flexiplex.cpp"))
dir.create(file.path(root,"sourcecpp_cache"),showWarnings=FALSE)
Rcpp::sourceCpp(code=source_code,cacheDir=file.path(root,"sourcecpp_cache"),rebuild=FALSE)
source(file.path(flames,"R/find_barcode.R"))
segments <- list(
  barcode_segment("RANDOM","NNNNNNNNNN","UB"),
  barcode_segment("MATCHED","NNNNNNNN","BC1",bc_list=v1,buffer_size=1,max_edit_distance=2),
  barcode_segment("FIXED","GTGGCCGATGTTTCGCATCGGCGTACGACT","linker1"),
  barcode_segment("MATCHED","NNNNNNNN","BC2",bc_list=v1,buffer_size=1,max_edit_distance=2),
  barcode_segment("FIXED","ATCCACGTGCTTGAGACTGTGG","linker2"),
  barcode_segment("MATCHED","NNNNNNNN","BC3",bc_list=v2,buffer_size=1,max_edit_distance=2))
stopifnot(all(vapply(segments[c(2,4,6)],function(s)s@max_edit_distance,numeric(1))==2))
manifest <- c(paste0("FLAMES_commit=",commit),paste0("input=",input),
  "expected_input_reads=5764421","threads=4","per_component_ED=2",
  "per_component_buffer=1","flank_ED=3","polyT=omitted","UB_length=10",
  "full_component_whitelists=96,96,96","whitelist_assignment=v1,v1,v2",
  paste0("v1=",v1),paste0("v2=",v2),"barcode_groups=none",
  "production_source_changes=none","reads_out=/dev/null","stats_out=stats.tsv.gz",
  "purpose=ED2 no-poly(T) sensitivity run; relative to saved no-poly(T) ED1 benchmark only component edit limit changed",
  "timing_note=FASTQ output discarded; not an I/O-matched timing comparison")
writeLines(c("status=running",manifest),file.path(root,"run_manifest.started.txt"))
started <- proc.time()
counts <- run_native(segments,list(),3L,input,"/dev/null",
  file.path(root,"stats.tsv.gz"),file.path(root,"barcode_counts.tsv"),FALSE,4L)
elapsed <- proc.time()-started
stopifnot(unname(counts[["total reads"]])==5764421L)
write.table(data.frame(metric=names(counts),value=as.integer(counts)),
  file.path(root,"read_counts.tsv"),sep="\t",quote=FALSE,row.names=FALSE)
write.table(data.frame(metric=c("user_seconds","system_seconds","elapsed_seconds"),
  value=unname(elapsed[c("user.self","sys.self","elapsed")])),
  file.path(root,"r_timing.tsv"),sep="\t",quote=FALSE,row.names=FALSE)
writeLines(c("status=success",manifest),file.path(root,"run_manifest.txt"))
print(counts)
