# -----------------------------------------------------------------------------
# Module: LR-Split-seq data re-run
# -----------------------------------------------------------------------------
list(
  # reference inputs and prior-publication objects
  # round 1 barcodes are missing from the matched short-read metadata's barcode column
  tar_target(
    round_1_barcodes,
    readLines("/vast/scratch/users/wang.ch/FLAMES_benchmark/sequencing_data/LR-Split-seq/bc2.csv")
  ),

  # From previous publication's GEO submission
  tar_target(
    GSM5169183_sc_gene_h5ad,
    "/vast/scratch/users/wang.ch/FLAMES_benchmark/sequencing_data/LR-Split-seq/GSM5169183_sc_gene.h5ad",
    format = "file"
  ),
  tar_target(
    GSM5169183_sc_gene_seurat_h5ad,
    {
      output <- "/vast/scratch/users/wang.ch/FLAMES_benchmark/sequencing_data/LR-Split-seq/GSM5169183_sc_gene.h5seurat"
      SeuratDisk::Convert(
        GSM5169183_sc_gene_h5ad,
        dest = output,
        overwrite = TRUE
      )
      output
    },
    format = "file"
  ),
  tar_target( # convert to SingleCellExperiment
    LR_split_seq_original_sce,
    SeuratDisk::LoadH5Seurat(GSM5169183_sc_gene_seurat_h5ad) |>
      Seurat::as.SingleCellExperiment()
  ),
  tar_target(
    LR_split_seq_original_colData,
    colData(LR_split_seq_original_sce) |>
      as.data.frame() |>
      as_tibble()
  ),
  tar_target(
    LR_split_seq_sr_sce,
    {
      x <- Matrix::readMM("/vast/scratch/users/wang.ch/LR-Split-seq/GSE168776/GSM5169184_C2C12_short_1k.genes.mtx.gz") |>
        t()
      coldata <- read_delim("/vast/scratch/users/wang.ch/LR-Split-seq/GSE168776/GSM5169184_C2C12_short_1k_cell_metadata.csv.gz") |>
        mutate(barcode = paste0(
          str_remove(cell_barcode, "_.*$"),
          round_1_barcodes[rnd1_well + 1]
        )) |>
        select(-`...1`, -cell_barcode, -species)
      rowdata <- read_delim("/vast/scratch/users/wang.ch/LR-Split-seq/GSE168776/GSM5169184_C2C12_short_1k_genes.csv.gz") |>
        select(gene_id, gene_name)
      rownames(x) <- rowdata$gene_name
      colnames(x) <- coldata$barcode
      sr_sce <- SingleCellExperiment::SingleCellExperiment(
        assays = list(counts = x),
        colData = coldata,
        rowData = rowdata
      )
      sr_sce
    }
  ),

  # short-read metadata from previous publication
  # add the missing round 1 barcodes to the barcode column
  tar_target(
    LR_split_short_read_metadata,
    list.files(
      "/vast/scratch/users/wang.ch/FLAMES_benchmark/sequencing_data/LR-Split-seq/short_metadata",
      pattern = "cell_metadata\\.csv\\.gz$",
      full.names = TRUE
    ) |>
      (\(x) setNames(x, x))() |>
      lapply(
        readr::read_csv,
      ) |>
      bind_rows(.id = "filename") |>
      mutate(
        barcode = paste0(
          str_remove(cell_barcode, "_.*$"),
          round_1_barcodes[rnd1_well + 1]
        )
      )
  ),

# various ways of running LR-split-seq data through FLAMES

## -----------------------------------------------------------------------------
## 2-pass FLAMES run, run find_barcodes and filter first, then run FLAMES with filtered barcodes
## -----------------------------------------------------------------------------
  # first-pass FLAMES run for barcode discovery
  tar_target(
    LR_split_seq_pipeline_barcode,
    FLAMES::SingleCellPipeline(
      config_file = FLAMES::create_config(
        "output/LR-Split-seq-barcode",
        pipeline_parameters.demultiplexer = "flexiplex",
        pipeline_parameters.do_isoform_identification = FALSE,
        barcode_parameters.pattern = list(
          UMI = "NNNNNNNNNN",
          BC = "NNNNNNNNGTGGCCGATGTTTCGCATCGGCGTACGACTNNNNNNNNATCCACGTGCTTGAGACTGTGGNNNNNNNN",
          polyT = "TTTTTTTT"
        ),
        barcode_parameters.TSO_seq = "",
        pipeline_parameters.threads = 4,
      ),
      outdir = "output/LR-Split-seq-barcode",
      fastq = "/vast/scratch/users/wang.ch/FLAMES_benchmark/sequencing_data/LR-Split-seq/SRR13948564.fastq",
      annotation = "/stornext/General/data/user_managed/grpu_mritchie_1/Changqing/Genome/mouse/gencode.vM34.annotation.gtf",
      genome_fa = "/stornext/General/data/user_managed/grpu_mritchie_1/Changqing/Genome/mouse/GRCm39.primary_assembly.genome.fa"
    ) |>
      FLAMES::run_step("barcode_demultiplex"),
    deployment = "main"
  ),
  tar_target(
    LR_split_seq_barcode_knee_plot_pdf,
    {
      output <- "output/LR-Split-seq-barcode_knee_plot.pdf"
      p <- FLAMES::plot_demultiplex(
        LR_split_seq_pipeline_barcode
      )$knee_plot +
        ggplot2::scale_x_log10(labels = scales::label_number()) +
        ggplot2::ylab("UMI counts") +
        ggplot2::theme_minimal(base_size = 18)
      ggsave(p, filename = output, width = 6, height = 6)
      output
    },
    format = "file"
  ),

  # select barcodes with >= 100 UMIs and exact match to the barcode pattern
  tar_target(
    LR_split_seq_barcodes,
    {
      output <- "output/LR-Split-seq-barcode/LR_split_seq_barcodes.tsv"
      read_delim(
        LR_split_seq_pipeline_barcode@metadata$barcode_demultiplex$stats_out
      ) |>
        filter(FlankEditDist == 0) |>
        group_by(CellBarcode) |>
        summarise(n = n_distinct(UMI)) |>
        filter(n >= 100) |>
        select(CellBarcode) |>
        write_delim(output, delim = "\t", col_names = FALSE)
      output
    },
    format = "file"
  ),

  # second-pass FLAMES run with selected barcodes
  tar_target(
    LR_split_seq_pipeline,
    FLAMES::SingleCellPipeline(
      config_file = FLAMES::create_config(
        "output/LR-Split-seq",
        pipeline_parameters.demultiplexer = "flexiplex",
        pipeline_parameters.do_isoform_identification = FALSE,
        barcode_parameters.pattern = list(
          UMI = "NNNNNNNNNN",
          BC = "NNNNNNNNGTGGCCGATGTTTCGCATCGGCGTACGACTNNNNNNNNATCCACGTGCTTGAGACTGTGGNNNNNNNN",
          polyT = "TTTTTTTT"
        ),
        barcode_parameters.TSO_seq = "",
        barcode_parameters.max_bc_editdistance = 6,
        pipeline_parameters.threads = 64
      ),
      outdir = "output/LR-Split-seq",
      barcodes_file = LR_split_seq_barcodes,
      fastq = "/vast/scratch/users/wang.ch/FLAMES_benchmark/sequencing_data/LR-Split-seq/SRR13948564.fastq",
      annotation = "/stornext/General/data/user_managed/grpu_mritchie_1/Changqing/Genome/mouse/gencode.vM34.annotation.gtf",
      genome_fa = "/stornext/General/data/user_managed/grpu_mritchie_1/Changqing/Genome/mouse/GRCm39.primary_assembly.genome.fa",
      controllers = list(
        default = create_slurm_controller(1, 24),
        barcode_demultiplex = create_slurm_controller(64, 8),
        genome_alignment = create_slurm_controller(64, 120),
        gene_quantification = create_slurm_controller(64, 120),
        read_realignment = create_slurm_controller(64, 120),
        transcript_quantification = create_slurm_controller(64, 16)
      )
    ) |>
      FLAMES::run_FLAMES(),
    deployment = "main",
    cue = tar_cue(mode = "never")
  ),

  # annotate FLAMES cells with short-read sample metadata
  tar_target(
    LR_split_seq_sce,
    {
      sce <- FLAMES::experiment(LR_split_seq_pipeline)
      sce <- scuttle::addPerCellQC(
        sce,
        subsets = list(mito = str_detect(rowData(sce)$gene_name, "^MT-"))
      ) |>
        scuttle::logNormCounts() |>
        scater::runPCA() |>
        scater::runUMAP() |>
        scuttle::addPerFeatureQC()
      colData(sce)$merged_bc <- paste0(
        substr(colnames(sce), 1, 8),
        substr(colnames(sce), 39, 46),
        substr(colnames(sce), 69, 76)
      )
      metadata <- LR_split_short_read_metadata |>
        filter(basename(filename) == "GSM5169184_C2C12_short_1k_cell_metadata.csv.gz") |>
        distinct(barcode, .keep_all = TRUE)
      sce$sample <- ifelse(
        sce$merged_bc %in% metadata$barcode,
        metadata$sample[match(sce$merged_bc, metadata$barcode)],
        NA_character_
      )
      sce
    }
  ),

  # UMAP comparisons: previously published vs FLAMES outputs
  tar_target(
    LR_split_seq_clusters_umap_pdf,
    {
      output <- "output/LR_split_seq_clusters_umap.pdf"
      sce <- FLAMES::add_gene_counts(
        LR_split_seq_sce,
        "/vast/scratch/users/wang.ch/targets_files/FLAMES_figures/output/LR-Split-seq/gene_count.csv"
      )
      altExp(sce, "gene") <- altExp(sce, "gene") |>
        scuttle::logNormCounts() |>
        scater::runPCA(
          ncomponents = ncol(sce),
          ntop = 20000,
          BSPARAM = BiocSingular::ExactParam()
        ) |>
        scater::runUMAP(ntop = ncol(sce))
      sce$`Previously recovered` <-
        colData(sce)$merged_bc %in% LR_split_seq_original_colData$merged_bc
      reducedDims(sce)$UMAP <- reducedDims(altExp(sce, "gene"))$UMAP

      p <- scater::plotReducedDim(
        sce[, !is.na(sce$sample)],
        "UMAP",
        colour_by = "sample",
        shape_by = "Previously recovered",
        point_size = 5
      ) +
        ggplot2::theme_minimal(base_size = 24) +
        theme(
          axis.text = element_blank(),
          axis.title = element_blank()
        )
      ggsave(p, filename = output, width = 16, height = 8)
      output
    },
    format = "file"
  ),
  tar_target(
    LR_split_seq_previous_clusters_umap_pdf,
    {
      output <- "output/LR_split_seq_previous_clusters_umap.pdf"
      sce <- LR_split_seq_original_sce
      sce$`FLAMES recovered` <- colData(sce)$merged_bc %in% LR_split_seq_sce$merged_bc

      p <- scater::plotReducedDim(
        sce,
        "UMAP",
        colour_by = "sample",
        shape_by = "FLAMES recovered",
        point_size = 1
      )
      ggsave(p, filename = output, width = 7, height = 6)
      output
    },
    format = "file"
  ),
  tar_target( # with same PCA/UMAP parameters to FLAMES
    LR_split_seq_previous_clusters_umap_exact_pdf,
    {
      output <- "output/LR_split_seq_previous_clusters_umap_exact.pdf"
      sce <- LR_split_seq_original_sce |>
        scater::runPCA(
          ncomponents = ncol(LR_split_seq_original_sce),
          ntop = nrow(LR_split_seq_original_sce), # less than 20000
          BSPARAM = BiocSingular::ExactParam()
        ) |>
        scater::runUMAP(ntop = ncol(LR_split_seq_original_sce))
      sce$`FLAMES recovered` <- colData(sce)$merged_bc %in% LR_split_seq_sce$merged_bc

      p <- scater::plotReducedDim(
        sce,
        "UMAP",
        colour_by = "sample",
        shape_by = "FLAMES recovered",
        point_size = 1
      )
      ggsave(p, filename = output, width = 7, height = 6)
      output
    },
    format = "file"
  ),


## -----------------------------------------------------------------------------
## Run LR-split-seq using well barcode list
## -----------------------------------------------------------------------------
  tar_target(
    lr_split_seq_pipeline,
    FLAMES::SingleCellPipeline(
      config_file = "files/config_splitseq.json",
      outdir = "/vast/projects/FLAMES/Changqing/LR-Split-seq-FLAMES",
      barcodes_file = c(
        "bc_8nt_v1" = "/vast/projects/FLAMES/Changqing/LR-splitpipe-flexiplex-mod/barcodes/bc_8nt_v1.csv",
        "bc_8nt_v2" = "/vast/projects/FLAMES/Changqing/LR-splitpipe-flexiplex-mod/barcodes/bc_8nt_v2.csv"
      ),
      fastq = "/vast/scratch/users/wang.ch/FLAMES_benchmark/sequencing_data/LR-Split-seq/SRR13948564.fastq",
      annotation = "/stornext/General/data/user_managed/grpu_mritchie_1/Changqing/Genome/mouse/gencode.vM34.annotation.gtf",
      genome_fa = "/stornext/General/data/user_managed/grpu_mritchie_1/Changqing/Genome/mouse/GRCm39.primary_assembly.genome.fa",
      controllers = list(
        default = create_slurm_controller(1, 24, log_prefix = "splitseq_default"),
        barcode_demultiplex = create_slurm_controller(64, 8, log_prefix = "splitseq_demultiplex"),
        genome_alignment = create_slurm_controller(64, 120, log_prefix = "splitseq_genome_align"),
        gene_quantification = create_slurm_controller(64, 256, log_prefix = "splitseq_gene_quant"),
        read_realignment = create_slurm_controller(64, 120, log_prefix = "splitseq_read_realign"),
        transcript_quantification = create_slurm_controller(64, 16, log_prefix = "splitseq_transcript_quant")
      )
    ) |>
      FLAMES::run_FLAMES(),
    cue = tar_cue(mode = "never")
  ),
  tar_target(
    # gene counts from FLAMES's gene quantification
    lr_split_seq_gene_mtx,
    {
      mtx <- file.path(lr_split_seq_pipeline@outdir, "gene_count.csv") |>
        data.table::fread(data.table = FALSE) |>
        column_to_rownames("V1") |>
        as.matrix()
      mtx[is.na(mtx)] <- 0
      mtx <- Matrix::Matrix(mtx, sparse = TRUE)
      colnames(mtx) <- paste0(
        substr(colnames(mtx), 1, 8),
        substr(colnames(mtx), 10, 17),
        substr(colnames(mtx), 19, 26)
      )
      mtx <- mtx[Matrix::rowSums(mtx) > 0, ]
      gene_df <- rowData(FLAMES::experiment(lr_split_seq_pipeline))
      rownames(mtx) <-
        gene_df$gene_name[match(rownames(mtx), gene_df$gene_id)]
      mtx
    },
    resources = tar_resources(
      crew = tar_resources_crew(controller = "slurm_1c64g")
    )
  ),

  # gene-count library-size diagnostics
  tar_target(
    lr_split_seq_gene_libsizes_tb,
    tibble(
      cell = colnames(lr_split_seq_gene_mtx),
      libsize = colSums(lr_split_seq_gene_mtx)
    ) |>
      left_join(
        select(filter(
          LR_split_short_read_metadata,
          basename(filename) == "GSM5169184_C2C12_short_1k_cell_metadata.csv.gz"
        ), barcode, sample),
        by = c("cell" = "barcode")
      ) |>
      arrange(desc(libsize)) |>
      mutate(rank = row_number())
  ),
  tar_target(
    lr_split_seq_gene_libsizes_plot_pdf,
    format = "file",
    {
      output <- "output/lr_split_seq_gene_libsizes.pdf"
      p <- lr_split_seq_gene_libsizes_tb |>
        filter(libsize >= 20) |>
        ggplot(aes(x = rank, y = libsize, color = sample)) +
        geom_point(size = 0.5, alpha = 0.8) +
        ggplot2::scale_x_log10() +
        ggplot2::scale_y_log10() +
        ggplot2::theme_classic() +
        scale_color_manual(
          values = c(
            "Unannotated" = "grey",
            "MB_cells" = "#1f77b4",
            "MB_nuclei" = "#ff7f0e",
            "MT_nuclei" = "#2ca02c"
          ),
          name = "Sample"
        ) +
        # line at threshold
        geom_vline(xintercept = sum(lr_split_seq_gene_libsizes_tb$libsize >= 150), col = "red") +
        xlab("Cell rank") +
        ylab("Library size (log10 scale)") +
        pdf(output, width = 8, height = 6)
      print(ggExtra::ggMarginal(p, type = "density", margins = "x", groupColour = TRUE))
      dev.off()
      output
    }
  ),

  # UMAP summaries for updated FLAMES runs
  tar_target(
    lr_split_seq_clusters_umap_tb,
    {
      mtx <- lr_split_seq_gene_mtx
      # BLAZE's threshold determination method:
      # mtx <- mtx[, colSums(mtx) >= sort(colSums(mtx), decreasing = TRUE)[1000 * 0.05] * 0.05]
      mtx <- mtx[, colSums(mtx) >= 150]
      sce <- SingleCellExperiment::SingleCellExperiment(
        assays = list(counts = mtx)
      ) |>
        scuttle::addPerCellQC() |>
        scuttle::addPerFeatureQC()

      metadata <- LR_split_short_read_metadata |>
        filter(basename(filename) == "GSM5169184_C2C12_short_1k_cell_metadata.csv.gz")
      sce$sample <- metadata$sample[match(colnames(sce), metadata$barcode)]
      sce$sample[is.na(sce$sample)] <- "Unannotated"
      sce <- sce[rowSums(SummarizedExperiment::assay(sce)) > 0, ]

      sce$previously_reported <-
        colnames(sce) %in% LR_split_seq_original_colData$merged_bc

      sce <- sce |>
        scuttle::logNormCounts(pseudo.count = 1) |>
        scater::runPCA(
          BSPARAM = BiocSingular::ExactParam()
        ) |>
        scater::runUMAP(n_neighbors = 5)

      tibble(
        cell = colnames(sce),
        sample = sce$sample,
        previously_reported = sce$previously_reported,
        UMAP1 = reducedDim(sce, "UMAP")[, 1],
        UMAP2 = reducedDim(sce, "UMAP")[, 2]
      )
    }
  ),
  tar_target(
    lr_split_seq_clusters_umap_pdf,
    format = "file",
    {
      p <- lr_split_seq_clusters_umap_tb |>
        ggplot(aes(x = UMAP1, y = UMAP2, color = sample, shape = previously_reported)) +
        geom_point(size = 5) +
        ggplot2::theme_classic(base_size = 36) +
        scale_color_manual(
          values = c(
            "Unannotated" = "grey",
            "MB_cells" = "#1f77b4",
            "MB_nuclei" = "#ff7f0e",
            "MT_nuclei" = "#2ca02c"
          ),
          name = "Sample"
        ) +
        scale_shape_manual(values = c(16, 17), name = "Previously reported") +
        theme(
          axis.text = element_blank(),
          axis.title = element_blank()
        )
      output <- "output/lr_split_seq_clusters_umap.pdf"
      ggsave(p, filename = output, width = 12, height = 8)
      output
    }
  ),

## -----------------------------------------------------------------------------
## Run LR-split-seq using barcode combination from short-read data
## -----------------------------------------------------------------------------
  # explicit short-read barcode list variant
  tar_target(
    LR_split_short_read_barcodes,
    format = "file",
    {
      output <- "output/LR_split_seq_short_read_barcodes.tsv"
      LR_split_short_read_metadata |>
        filter(basename(filename) == "GSM5169184_C2C12_short_1k_cell_metadata.csv.gz") |>
        distinct(barcode, .keep_all = TRUE) |>
        select(barcode) |>
        write_delim(output, delim = "\t", col_names = FALSE)
      output
    }
  ),
  tar_target(
    LR_split_seq_pipeline_new,
    FLAMES::SingleCellPipeline(
      config_file = "files/config_splitseq_bc.json",
      outdir = "/vast/projects/FLAMES/Changqing/LR-Split-seq-FLAMES-new",
      barcodes_file = c("bc_list" = LR_split_short_read_barcodes),
      fastq = "/vast/scratch/users/wang.ch/FLAMES_benchmark/sequencing_data/LR-Split-seq/SRR13948564.fastq",
      annotation = "/stornext/General/data/user_managed/grpu_mritchie_1/Changqing/Genome/mouse/gencode.vM34.annotation.gtf",
      genome_fa = "/stornext/General/data/user_managed/grpu_mritchie_1/Changqing/Genome/mouse/GRCm39.primary_assembly.genome.fa",
      controllers = list(
        default = create_slurm_controller(1, 24, log_prefix = "splitseq_n_default"),
        barcode_demultiplex = create_slurm_controller(64, 8, log_prefix = "splitseq_n_demultiplex"),
        genome_alignment = create_slurm_controller(64, 120, log_prefix = "splitseq_n_genome_align"),
        gene_quantification = create_slurm_controller(64, 256, log_prefix = "splitseq_n_gene_quant"),
        read_realignment = create_slurm_controller(64, 120, log_prefix = "splitseq_n_read_realign"),
        transcript_quantification = create_slurm_controller(64, 16, log_prefix = "splitseq_n_transcript_quant")
      )
    ) |>
      FLAMES::run_FLAMES(),
    cue = tar_cue(mode = "never")
  ),
  tar_target(
    # gene counts from FLAMES's gene quantification
    LR_split_n_gene_mtx,
    {
      mtx <- file.path(LR_split_seq_pipeline_new@outdir, "gene_count.csv") |>
        data.table::fread(data.table = FALSE) |>
        column_to_rownames("V1") |>
        as.matrix()
      mtx[is.na(mtx)] <- 0
      mtx <- Matrix::Matrix(mtx, sparse = TRUE)
      mtx <- mtx[rowSums(mtx) > 0, ]
      gene_df <- rowData(FLAMES::experiment(LR_split_seq_pipeline_new))
      rownames(mtx) <- gene_df$gene_name[match(rownames(mtx), gene_df$gene_id)]
      mtx
    },
    resources = tar_resources(
      crew = tar_resources_crew(controller = "slurm_1c20g")
    )
  ),
  tar_target(
    LR_split_seq_n_clusters_umap_tb,
    {
      sce <- SingleCellExperiment::SingleCellExperiment(
        assays = list(counts = LR_split_n_gene_mtx)
      )

      metadata <- LR_split_short_read_metadata |>
        filter(basename(filename) == "GSM5169184_C2C12_short_1k_cell_metadata.csv.gz")
      sce$sample <- metadata$sample[match(colnames(sce), metadata$barcode)]
      sce <- sce[rowSums(SummarizedExperiment::assay(sce)) > 0, ]

      sce$previously_reported <-
        colnames(sce) %in% LR_split_seq_original_colData$merged_bc

      sce <- sce |>
        scuttle::logNormCounts() |>
        scater::runPCA(
          BSPARAM = BiocSingular::ExactParam()
        ) |>
        scater::runUMAP(n_neighbors = 4)
      tibble(
        cell = colnames(sce),
        sample = sce$sample,
        previously_reported = sce$previously_reported,
        UMAP1 = reducedDim(sce, "UMAP")[, 1],
        UMAP2 = reducedDim(sce, "UMAP")[, 2]
      )
    }
  ),
  tar_target(
    LR_split_seq_n_clusters_umap_pdf,
    format = "file",
    {
      output <- "output/LR_split_seq_n_clusters_umap.pdf"
      p <- LR_split_seq_n_clusters_umap_tb |>
        ggplot(aes(x = UMAP1, y = UMAP2, color = sample, shape = previously_reported)) +
        geom_point(size = 5) +
        ggplot2::theme_classic(base_size = 24) +
        scale_color_manual(
          values = c(
            "Unannotated" = "grey",
            "MB_cells" = "#1f77b4",
            "MB_nuclei" = "#ff7f0e",
            "MT_nuclei" = "#2ca02c"
          ),
          name = "Sample"
        ) +
        scale_shape_manual(values = c(16, 17), name = "Previously reported") +
        theme(
          axis.text = element_blank(),
          axis.title = element_blank()
        )
      ggsave(p, filename = output, width = 16, height = 8)
      output
    }
  ),

  # correlation benchmarking against original and short-read matrices
  tar_target(
    LR_split_seq_n_gene_corr,
    {
      orig_mtx <- SummarizedExperiment::assay(LR_split_seq_original_sce, "counts")
      flames_mtx <- LR_split_n_gene_mtx
      sr_mtx <- as.matrix(
        SummarizedExperiment::assay(LR_split_seq_sr_sce)
      )

      cells <- intersect(colnames(flames_mtx), colnames(orig_mtx))
      flames_mtx <- flames_mtx[, cells]
      flames_mtx <- flames_mtx[rowSums(flames_mtx) > 0, ]
      orig_mtx <- orig_mtx[, cells]
      orig_mtx <- orig_mtx[rowSums(orig_mtx) > 0, ]

      genes <- Reduce(intersect, list(
        rownames(flames_mtx),
        rownames(orig_mtx),
        rownames(sr_mtx)
      ))
      flames_cell_corr <- unlist(BiocParallel::bplapply(cells, function(cell) {
        cor(sr_mtx[genes, cell], flames_mtx[genes, cell], method = "spearman")
      }, BPPARAM = BiocParallel::MulticoreParam(workers = 4, progressbar = TRUE)))
      orig_cell_corr <- unlist(BiocParallel::bplapply(cells, function(cell) {
        cor(sr_mtx[genes, cell], orig_mtx[genes, cell], method = "spearman")
      }, BPPARAM = BiocParallel::MulticoreParam(workers = 4, progressbar = TRUE)))
      # by gene
      flames_gene_corr <- unlist(BiocParallel::bplapply(genes, function(gene) {
        cor(sr_mtx[gene, cells], flames_mtx[gene, cells], method = "spearman")
      }, BPPARAM = BiocParallel::MulticoreParam(workers = 32, progressbar = TRUE)))
      orig_gene_corr <- unlist(BiocParallel::bplapply(genes, function(gene) {
        cor(sr_mtx[gene, cells], orig_mtx[gene, cells], method = "spearman")
      }, BPPARAM = BiocParallel::MulticoreParam(workers = 32, progressbar = TRUE)))
      tibble(
        cell = cells,
        flames_corr = flames_cell_corr,
        orig_corr = orig_cell_corr
      )
    }
  )
)
