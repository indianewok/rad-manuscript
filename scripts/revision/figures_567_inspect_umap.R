#!/usr/bin/env Rscript
# Read the retained object without recalculating or altering its embedding.
args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args)==2)
input <- args[[1]]
output <- args[[2]]
dir.create(output, recursive=TRUE, showWarnings=FALSE)
suppressPackageStartupMessages(library(Seurat))
obj <- readRDS(input)
commands <- lapply(obj@commands, function(x) list(name=x@name, time=as.character(x@time.stamp), call=x@call.string, params=x@params))
capture.output(str(commands, max.level=5), file=file.path(output,'umap_object_commands.txt'))
capture.output(sessionInfo(), file=file.path(output,'umap_inspection_session.txt'))
embedding <- Embeddings(obj, reduction='umap')
stopifnot(!anyDuplicated(rownames(embedding)), nrow(embedding)==12012)
write.table(data.frame(cell_barcode=sub('-1$','',rownames(embedding)), object_cell_name=rownames(embedding), UMAP_1=embedding[,1], UMAP_2=embedding[,2]), file=file.path(output,'umap_object_coordinates.tsv'), sep='\t', row.names=FALSE, quote=FALSE)
capture.output(list(input=input, assays=names(obj@assays), reductions=names(obj@reductions), command_names=names(obj@commands), dimensions=dim(obj), object_version=as.character(obj@version)), file=file.path(output,'umap_object_summary.txt'))
