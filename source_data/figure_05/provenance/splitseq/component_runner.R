#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 6L || length(args) > 7L) {
  stop(
    "usage: run_component_no_polyt.R FLAMES_SOURCE INPUT_FASTQ ",
    "OUTDIR THREADS BC_V1 BC_V2 [omit|include]"
  )
}

flames_source <- normalizePath(args[[1]], mustWork = TRUE)
input_fastq <- normalizePath(args[[2]], mustWork = TRUE)
outdir <- normalizePath(args[[3]], mustWork = FALSE)
threads <- as.integer(args[[4]])
bc_v1 <- normalizePath(args[[5]], mustWork = TRUE)
bc_v2 <- normalizePath(args[[6]], mustWork = TRUE)
polyt_mode <- if (length(args) == 7L) args[[7]] else "omit"

if (is.na(threads) || threads < 1L) {
  stop("THREADS must be a positive integer")
}
if (!polyt_mode %in% c("omit", "include")) {
  stop("poly-T mode must be either 'omit' or 'include'")
}
if (!requireNamespace("Rcpp", quietly = TRUE) ||
    !requireNamespace("Rhtslib", quietly = TRUE)) {
  stop("Rcpp and Rhtslib are required")
}

dir.create(outdir, recursive = TRUE, showWarnings = FALSE)
cache_dir <- file.path(dirname(outdir), "sourcecpp_cache_component_no_polyt")
dir.create(cache_dir, recursive = TRUE, showWarnings = FALSE)

cppflags <- paste(capture.output(Rhtslib::pkgconfig("PKG_CPPFLAGS")), collapse = " ")
libs <- paste(capture.output(Rhtslib::pkgconfig("PKG_LIBS")), collapse = " ")
Sys.setenv(
  PKG_CPPFLAGS = paste("-pthread", cppflags),
  PKG_LIBS = paste("-pthread -lz", libs)
)

source_code <- sprintf(
  paste0(
    '#include "%s"\n#include "%s"\n',
    "// [[Rcpp::export]]\n",
    "Rcpp::IntegerVector flames_component_no_polyt(",
    "Rcpp::List segments, Rcpp::List groups, int max_flank_ed, ",
    "Rcpp::StringVector reads_in, Rcpp::String reads_out, ",
    "Rcpp::String stats_out, Rcpp::String bc_out, ",
    "bool reverse_complement, int threads) {",
    "return flexiplex_cpp(",
    "segments, groups, max_flank_ed, reads_in, reads_out, ",
    "stats_out, bc_out, reverse_complement, threads);",
    "}\n"
  ),
  file.path(flames_source, "src/utility/edlib-1.2.7/edlib.cpp"),
  file.path(flames_source, "src/main-functions/flexiplex.cpp")
)

Rcpp::sourceCpp(
  code = source_code,
  cacheDir = cache_dir,
  rebuild = FALSE,
  showOutput = FALSE
)
source(file.path(flames_source, "R/find_barcode.R"))

linker1 <- "GTGGCCGATGTTTCGCATCGGCGTACGACT"
linker2 <- "ATCCACGTGCTTGAGACTGTGG"

# This is byte-for-byte the prior component layout except that the terminal
# FIXED poly-T segment is deliberately omitted.
segments <- list(
  barcode_segment("RANDOM", "NNNNNNNNNN", "UB"),
  barcode_segment(
    "MATCHED", "NNNNNNNN", "BC1", bc_list = bc_v1,
    buffer_size = 1, max_edit_distance = 1
  ),
  barcode_segment("FIXED", linker1, "linker1"),
  barcode_segment(
    "MATCHED", "NNNNNNNN", "BC2", bc_list = bc_v1,
    buffer_size = 1, max_edit_distance = 1
  ),
  barcode_segment("FIXED", linker2, "linker2"),
  barcode_segment(
    "MATCHED", "NNNNNNNN", "BC3", bc_list = bc_v2,
    buffer_size = 1, max_edit_distance = 1
  )
)
if (polyt_mode == "include") {
  segments <- c(
    segments,
    list(barcode_segment("FIXED", "TTTTTTTT", "polyT"))
  )
}

started <- proc.time()
counts <- flames_component_no_polyt(
  segments = segments,
  groups = list(),
  max_flank_ed = 3L,
  reads_in = input_fastq,
  reads_out = file.path(outdir, "demultiplexed.fastq.gz"),
  stats_out = file.path(outdir, "stats.tsv.gz"),
  bc_out = file.path(outdir, "barcode_counts.tsv"),
  reverse_complement = FALSE,
  threads = threads
)
elapsed <- proc.time() - started

write.table(
  data.frame(metric = names(counts), value = as.integer(counts)),
  file.path(outdir, "read_counts.tsv"),
  sep = "\t", quote = FALSE, row.names = FALSE
)
write.table(
  data.frame(
    metric = c("user_seconds", "system_seconds", "elapsed_seconds"),
    value = unname(elapsed[c("user.self", "sys.self", "elapsed")])
  ),
  file.path(outdir, "r_timing.tsv"),
  sep = "\t", quote = FALSE, row.names = FALSE
)

commit <- system2(
  "git",
  c("-C", shQuote(flames_source), "rev-parse", "HEAD"),
  stdout = TRUE
)
writeLines(
  c(
    paste("FLAMES source", flames_source),
    paste("FLAMES commit", commit),
    paste("input", input_fastq),
    paste("threads", threads),
    paste("BC v1 whitelist", bc_v1),
    paste("BC v2 whitelist", bc_v2),
    "BC v1 entries 96",
    "BC v2 entries 96",
    paste("max flank edit distance", 3),
    paste("per component edit distance", 1),
    paste("terminal poly-T segment", polyt_mode)
  ),
  file.path(outdir, "run_manifest.txt")
)

message("Component Flexiplex no-poly-T demultiplexing complete")
