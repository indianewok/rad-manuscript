#!/usr/bin/env Rscript
# Inventory a saved workspace without restoring it into the global environment.
# No saved function or plotting expression is called and no package is attached.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) stop("Usage: Rscript --vanilla figures_124_inventory_workspace.R INPUT.RData OUTPUT.tsv")
workspace <- new.env(parent = emptyenv())
loaded <- load(args[[1]], envir = workspace, verbose = FALSE)
describe <- function(name, x) {
  at <- attributes(x)
  classes <- if (is.null(at$class)) typeof(x) else paste(at$class, collapse = ",")
  dimensions <- if (is.null(at$dim)) "" else paste(at$dim, collapse = "x")
  if (inherits(x, "data.frame")) dimensions <- paste(.row_names_info(x, 2L), length(x), sep = "x")
  data.frame(object = name, type = typeof(x), class = classes,
             dimensions = dimensions, length = length(x),
             attribute_names = paste(names(at), collapse = ";"),
             field_names = paste(head(at$names, 100L), collapse = ";"),
             stringsAsFactors = FALSE)
}
inventory <- list()
for (name in sort(loaded)) {
  # Active bindings are reported without evaluating their getter.
  if (bindingIsActive(name, workspace)) next
  x <- get(name, envir = workspace, inherits = FALSE)
  inventory[[length(inventory) + 1L]] <- describe(name, x)
  # Metadata slots can be inspected as stored attributes, without Seurat methods.
  for (slot in intersect(names(attributes(x)), c("meta.data", "images", "assays"))) {
    inventory[[length(inventory) + 1L]] <- describe(paste(name, slot, sep = "@"), attr(x, slot))
  }
}
dir.create(dirname(args[[2]]), recursive = TRUE, showWarnings = FALSE)
write.table(do.call(rbind, inventory), args[[2]], sep = "\t", quote = FALSE, row.names = FALSE, na = "")
cat("Inventoried", length(loaded), "saved objects; did not call saved functions.\n")
