args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 7L) {
  stop(
    "usage: run_longbench_flames_stage.R ",
    "MATCHED_FASTQ OUTDIR CONFIG_JSON GTF GENOME_FASTA MINIMAP2 K8"
  )
}

fastq_flames <- normalizePath(args[[1]], mustWork = TRUE)
outdir <- normalizePath(args[[2]], mustWork = TRUE)
config_file <- normalizePath(args[[3]], mustWork = TRUE)
GTF <- normalizePath(args[[4]], mustWork = TRUE)
genome <- normalizePath(args[[5]], mustWork = TRUE)
minimap2 <- normalizePath(args[[6]], mustWork = TRUE)
k8 <- normalizePath(args[[7]], mustWork = TRUE)

suppressPackageStartupMessages(library(FLAMES))

cat("FLAMES_version\t", as.character(packageVersion("FLAMES")), "\n", sep = "")
cat("R_version\t", R.version.string, "\n", sep = "")
cat("config_file\t", config_file, "\n", sep = "")
cat("fastq\t", fastq_flames, "\n", sep = "")
cat("outdir\t", outdir, "\n", sep = "")
cat("gtf\t", GTF, "\n", sep = "")
cat("genome\t", genome, "\n", sep = "")
cat("minimap2\t", minimap2, "\n", sep = "")
cat("k8\t", k8, "\n", sep = "")

sc_long_pipeline(
  fastq = fastq_flames,
  outdir = outdir,
  annot = GTF,
  genome_fa = genome,
  config_file = config_file,
  barcodes_file = "not used",
  minimap2 = minimap2,
  k8 = k8
)
