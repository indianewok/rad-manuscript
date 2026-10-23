#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(Seurat)
  library(SeuratObject)
  library(Matrix)
  library(ggplot2)
  library(patchwork)
})

args <- commandArgs(trailingOnly = TRUE)
bundle_dir <- if (length(args) >= 1L) normalizePath(args[[1]], mustWork = TRUE) else {
  "/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/LongBench_Illumina_SC_SN_Seurat_UMAP_20260805"
}

input_dir <- file.path(bundle_dir, "input")
object_dir <- file.path(bundle_dir, "objects")
table_dir <- file.path(bundle_dir, "tables")
figure_dir <- file.path(bundle_dir, "figures")
log_dir <- file.path(bundle_dir, "logs")
dir.create(object_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(table_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(log_dir, recursive = TRUE, showWarnings = FALSE)

seed <- 20260805L
set.seed(seed)

required_files <- c(
  "ill_sc_matrix.mtx.gz", "ill_sc_features.tsv.gz", "ill_sc_barcodes.tsv.gz",
  "ill_sn_matrix.mtx.gz", "ill_sn_features.tsv.gz", "ill_sn_barcodes.tsv.gz",
  "ill_sc_vireo_donor_ids.tsv", "ill_sn_vireo_donor_ids.tsv"
)
missing_files <- required_files[!file.exists(file.path(input_dir, required_files))]
if (length(missing_files)) {
  stop("Missing required input files: ", paste(missing_files, collapse = ", "))
}

normalize_barcode <- function(x) sub("-[0-9]+$", "", as.character(x))

read_consensus_labels <- function(modality) {
  annotation_dir <- file.path(input_dir, "merged_annotation", tolower(modality))
  files <- sort(list.files(annotation_dir, pattern = "_BC_list[.]txt$", full.names = TRUE))
  if (!length(files)) stop("No consensus annotation files found in ", annotation_dir)
  pieces <- lapply(files, function(path) {
    barcode <- trimws(readLines(path, warn = FALSE))
    barcode <- barcode[nzchar(barcode)]
    data.frame(
      barcode_core = normalize_barcode(barcode),
      consensus_cell_line = sub("_BC_list[.]txt$", "", basename(path)),
      stringsAsFactors = FALSE
    )
  })
  out <- do.call(rbind, pieces)
  duplicated_keys <- unique(out$barcode_core[duplicated(out$barcode_core)])
  if (length(duplicated_keys)) {
    stop("Consensus cell-line lists overlap for ", length(duplicated_keys), " barcodes")
  }
  out
}

read_vireo <- function(modality) {
  path <- file.path(input_dir, paste0("ill_", tolower(modality), "_vireo_donor_ids.tsv"))
  out <- read.delim(path, check.names = FALSE, stringsAsFactors = FALSE)
  stopifnot("cell" %in% names(out), !anyDuplicated(out$cell))
  out$barcode_core <- normalize_barcode(out$cell)
  names(out)[names(out) != "cell" & names(out) != "barcode_core"] <- paste0(
    "vireo_", names(out)[names(out) != "cell" & names(out) != "barcode_core"]
  )
  out
}

build_metadata <- function(barcodes, modality) {
  barcode_core <- normalize_barcode(barcodes)
  meta <- data.frame(
    barcode = barcodes,
    barcode_core = barcode_core,
    modality = modality,
    stringsAsFactors = FALSE,
    row.names = barcodes
  )

  vireo <- read_vireo(modality)
  vireo_match <- match(barcode_core, vireo$barcode_core)
  vireo_columns <- grep("^vireo_", names(vireo), value = TRUE)
  for (column in vireo_columns) meta[[column]] <- vireo[[column]][vireo_match]

  consensus <- read_consensus_labels(modality)
  consensus_match <- match(barcode_core, consensus$barcode_core)
  meta$consensus_cell_line <- consensus$consensus_cell_line[consensus_match]
  meta$consensus_cell_line[is.na(meta$consensus_cell_line)] <- "not_in_consensus"

  donor <- meta$vireo_donor_id
  meta$vireo_state <- ifelse(
    is.na(donor), "missing",
    ifelse(donor %in% c("doublet", "unassigned"), donor, "named_singlet")
  )
  meta
}

write_csv <- function(x, path) {
  write.csv(x, path, row.names = FALSE, quote = TRUE, na = "")
}

save_plot <- function(plot, stem, width = 10, height = 8) {
  ggsave(file.path(figure_dir, paste0(stem, ".pdf")), plot = plot,
         width = width, height = height, units = "in", limitsize = FALSE)
  png(file.path(figure_dir, paste0(stem, ".png")), width = width, height = height,
      units = "in", res = 180, type = "cairo")
  print(plot)
  dev.off()
}

process_modality <- function(modality) {
  tag <- tolower(modality)
  message("[", modality, "] reading Cell Ranger matrix")
  counts <- ReadMtx(
    mtx = file.path(input_dir, paste0("ill_", tag, "_matrix.mtx.gz")),
    features = file.path(input_dir, paste0("ill_", tag, "_features.tsv.gz")),
    cells = file.path(input_dir, paste0("ill_", tag, "_barcodes.tsv.gz")),
    feature.column = 2L,
    cell.column = 1L,
    unique.features = TRUE,
    strip.suffix = FALSE
  )
  expected_cells <- if (modality == "SC") 5211L else 12012L
  stopifnot(nrow(counts) == 62700L, ncol(counts) == expected_cells)

  metadata <- build_metadata(colnames(counts), modality)
  stopifnot(identical(rownames(metadata), colnames(counts)))

  message("[", modality, "] creating Seurat object without barcode filtering")
  object <- CreateSeuratObject(
    counts = counts,
    assay = "RNA",
    project = paste0("LongBench_Illumina_", modality),
    meta.data = metadata,
    min.cells = 0,
    min.features = 0
  )
  object[["percent.mt"]] <- PercentageFeatureSet(object, pattern = "^MT-")
  object@misc$source <- "LongBench public Illumina Cell Ranger v8.0.1 filtered count matrix"
  object@misc$source_urls <- c(
    matrix = paste0("https://longbench-data.s3.amazonaws.com/processed/count_matrices/ill_", tag, "_matrix.mtx.gz"),
    features = paste0("https://longbench-data.s3.amazonaws.com/processed/count_matrices/ill_", tag, "_features.tsv.gz"),
    barcodes = paste0("https://longbench-data.s3.amazonaws.com/processed/count_matrices/ill_", tag, "_barcodes.tsv.gz")
  )
  object@misc$processing <- list(
    all_cellranger_filtered_barcodes_retained = TRUE,
    normalization = "LogNormalize",
    scale_factor = 10000,
    variable_features = 3000L,
    pca_npcs = 50L,
    graph_and_umap_dims = 1:30,
    cluster_resolution = 0.5,
    umap_n_neighbors = 30L,
    umap_min_dist = 0.3,
    umap_metric = "cosine",
    random_seed = seed
  )

  message("[", modality, "] LogNormalize and variable-feature selection")
  object <- NormalizeData(object, normalization.method = "LogNormalize", scale.factor = 10000,
                          verbose = FALSE)
  object <- FindVariableFeatures(object, selection.method = "vst", nfeatures = 3000,
                                 verbose = FALSE)
  stopifnot(length(VariableFeatures(object)) == 3000L)

  message("[", modality, "] scaling variable features and PCA")
  object <- ScaleData(object, features = VariableFeatures(object), verbose = FALSE)
  object <- RunPCA(object, features = VariableFeatures(object), npcs = 50,
                   approx = TRUE, seed.use = seed, verbose = FALSE)
  stopifnot(ncol(Embeddings(object, "pca")) == 50L)

  message("[", modality, "] neighbors, clustering, and UMAP")
  object <- FindNeighbors(object, reduction = "pca", dims = 1:30, verbose = FALSE)
  object <- FindClusters(object, resolution = 0.5, algorithm = 1,
                         random.seed = seed, verbose = FALSE)
  object <- RunUMAP(
    object,
    reduction = "pca",
    dims = 1:30,
    n.neighbors = 30L,
    min.dist = 0.3,
    metric = "cosine",
    seed.use = seed,
    n.threads = 1L,
    verbose = FALSE
  )
  stopifnot(nrow(Embeddings(object, "umap")) == expected_cells)

  coordinates <- as.data.frame(Embeddings(object, "umap"), stringsAsFactors = FALSE)
  names(coordinates)[1:2] <- c("UMAP_1", "UMAP_2")
  coordinates$barcode <- rownames(coordinates)
  metadata_out <- object[[]]
  metadata_out$barcode <- rownames(metadata_out)
  coordinates <- cbind(
    data.frame(modality = modality, stringsAsFactors = FALSE),
    coordinates[, c("barcode", "UMAP_1", "UMAP_2"), drop = FALSE],
    metadata_out[coordinates$barcode, setdiff(names(metadata_out), "barcode"), drop = FALSE]
  )
  coordinates$seurat_cluster <- as.character(Idents(object)[coordinates$barcode])
  coordinates <- coordinates[, c(
    "modality", "barcode", "UMAP_1", "UMAP_2", "seurat_cluster",
    setdiff(names(coordinates), c("modality", "barcode", "UMAP_1", "UMAP_2", "seurat_cluster"))
  )]

  object_path <- file.path(object_dir, paste0("LongBench_Illumina_", modality, "_Seurat_UMAP.rds"))
  table_path <- file.path(table_dir, paste0("LongBench_Illumina_", modality, "_UMAP_per_barcode.csv"))
  message("[", modality, "] saving object and graph-ready coordinates")
  saveRDS(object, object_path, compress = "gzip")
  write_csv(coordinates, table_path)

  cluster_summary <- as.data.frame(table(
    seurat_cluster = coordinates$seurat_cluster,
    consensus_cell_line = coordinates$consensus_cell_line,
    useNA = "ifany"
  ), stringsAsFactors = FALSE)
  cluster_summary <- cluster_summary[cluster_summary$Freq > 0, , drop = FALSE]
  cluster_summary$modality <- modality
  write.table(
    cluster_summary[, c("modality", "seurat_cluster", "consensus_cell_line", "Freq")],
    file.path(table_dir, paste0("LongBench_Illumina_", modality, "_cluster_by_cell_line.tsv")),
    sep = "\t", row.names = FALSE, quote = FALSE
  )

  p_cluster <- DimPlot(object, reduction = "umap", group.by = "seurat_clusters",
                       label = TRUE, repel = TRUE, raster = TRUE) +
    ggtitle(paste("LongBench Illumina", modality, "- Seurat clusters")) +
    theme_bw(base_size = 11)
  p_cell_line <- DimPlot(object, reduction = "umap", group.by = "consensus_cell_line",
                         label = TRUE, repel = TRUE, raster = TRUE) +
    ggtitle(paste("LongBench Illumina", modality, "- consensus cell line")) +
    theme_bw(base_size = 11)
  p_vireo <- DimPlot(object, reduction = "umap", group.by = "vireo_donor_id",
                     label = TRUE, repel = TRUE, raster = TRUE) +
    ggtitle(paste("LongBench Illumina", modality, "- Illumina Vireo")) +
    theme_bw(base_size = 11)
  save_plot(p_cluster, paste0("LongBench_Illumina_", modality, "_UMAP_clusters"))
  save_plot(p_cell_line, paste0("LongBench_Illumina_", modality, "_UMAP_consensus_cell_line"))
  save_plot(p_vireo, paste0("LongBench_Illumina_", modality, "_UMAP_vireo"))
  save_plot(p_cluster + p_cell_line + p_vireo + plot_layout(ncol = 3),
            paste0("LongBench_Illumina_", modality, "_UMAP_panel"), width = 24, height = 7)

  qc <- data.frame(
    modality = modality,
    input_features = nrow(counts),
    retained_barcodes = ncol(object),
    median_umis = median(object$nCount_RNA),
    median_detected_features = median(object$nFeature_RNA),
    median_percent_mt = median(object$percent.mt),
    variable_features = length(VariableFeatures(object)),
    pca_dimensions = ncol(Embeddings(object, "pca")),
    umap_rows = nrow(Embeddings(object, "umap")),
    clusters = length(unique(Idents(object))),
    vireo_rows_matched = sum(!is.na(object$vireo_donor_id)),
    consensus_rows_matched = sum(object$consensus_cell_line != "not_in_consensus"),
    stringsAsFactors = FALSE
  )

  rm(counts, object)
  invisible(gc())
  list(coordinates = coordinates, qc = qc, cluster_summary = cluster_summary)
}

results <- lapply(c("SC", "SN"), process_modality)
names(results) <- c("SC", "SN")

combined_coordinates <- do.call(rbind, lapply(results, `[[`, "coordinates"))
write_csv(
  combined_coordinates,
  file.path(table_dir, "LongBench_Illumina_SC_SN_UMAP_per_barcode.csv")
)

qc_summary <- do.call(rbind, lapply(results, `[[`, "qc"))
write.table(qc_summary, file.path(table_dir, "QC_summary.tsv"), sep = "\t",
            row.names = FALSE, quote = FALSE)

parameters <- data.frame(
  parameter = c(
    "barcode_filtering", "normalization", "scale_factor", "variable_features",
    "pca_npcs", "neighbor_dims", "cluster_algorithm", "cluster_resolution",
    "umap_dims", "umap_n_neighbors", "umap_min_dist", "umap_metric", "random_seed"
  ),
  value = c(
    "none_after_Cell_Ranger_filtered_matrix", "LogNormalize", "10000", "3000",
    "50", "1:30", "Louvain_algorithm_1", "0.5", "1:30", "30", "0.3",
    "cosine", as.character(seed)
  ),
  stringsAsFactors = FALSE
)
write.table(parameters, file.path(table_dir, "processing_parameters.tsv"), sep = "\t",
            row.names = FALSE, quote = FALSE)

capture.output(sessionInfo(), file = file.path(log_dir, "sessionInfo.txt"))

readme <- c(
  "# LongBench Illumina SC/SN Seurat UMAP bundle",
  "",
  "This bundle contains independently processed Illumina single-cell (SC) and",
  "single-nucleus (SN) reference datasets from the public LongBench Cell Ranger",
  "v8.0.1 filtered count matrices.",
  "",
  "## Scope",
  "",
  "- All 5,211 SC and 12,012 SN Cell Ranger-filtered barcodes are retained.",
  "- SC and SN are normalized and embedded independently; they are not integrated.",
  "- UMAP coordinates are a reproducible analysis product, not coordinates released by LongBench.",
  "- Illumina Vireo calls and LongBench consensus cell-line labels are attached as metadata.",
  "",
  "## Processing",
  "",
  "Seurat v5 LogNormalize (scale factor 10,000), 3,000 variable features, variable-feature",
  "scaling, 50 PCs, neighbors/clustering/UMAP on PCs 1-30, Louvain resolution 0.5,",
  "30 UMAP neighbors, min.dist 0.3, cosine metric, and seed 20260805.",
  "",
  "## Main outputs",
  "",
  "- objects/LongBench_Illumina_SC_Seurat_UMAP.rds",
  "- objects/LongBench_Illumina_SN_Seurat_UMAP.rds",
  "- tables/LongBench_Illumina_SC_UMAP_per_barcode.csv",
  "- tables/LongBench_Illumina_SN_UMAP_per_barcode.csv",
  "- tables/LongBench_Illumina_SC_SN_UMAP_per_barcode.csv",
  "- figures/LongBench_Illumina_{SC,SN}_UMAP_panel.{pdf,png}",
  "",
  "The per-barcode CSVs are the minimal graph-ready layer. The RDS files retain counts,",
  "normalized data, scaled variable features, PCA, neighbors, clusters, UMAP, and metadata.",
  "",
  "## Reproduction",
  "",
  "Run:",
  "",
  "```bash",
  "Rscript --vanilla scripts/build_longbench_illumina_seurat_umap.R <bundle_dir>",
  "```"
)
writeLines(readme, file.path(bundle_dir, "README.md"))

message("Completed LongBench Illumina SC/SN Seurat UMAP bundle at ", bundle_dir)
