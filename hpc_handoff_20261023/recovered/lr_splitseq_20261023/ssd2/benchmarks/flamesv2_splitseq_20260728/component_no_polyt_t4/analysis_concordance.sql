SET temp_directory = '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/duckdb_tmp';
SET memory_limit = '8GB';
SET threads = 4;

CREATE OR REPLACE TEMP TABLE published AS
SELECT
  canonical_barcode AS cell,
  cast(published_sr_umi_cts AS BIGINT) AS published_sr_umis,
  cast(published_lr_umi_cts AS BIGINT) AS published_lr_umis
FROM read_csv_auto(
  '/Volumes/CMV_SSD_2/results/misc/splitseq_shortread_umis_20260728/published_568_barcode_map.csv',
  header = true
);

CREATE OR REPLACE TEMP TABLE v2_metadata AS
SELECT trim(sequence) AS sequence, well, type
FROM read_csv_auto(
  '/Users/cmv/Desktop/tools/LR-splitpipe-master/barcodes/bc_data_v2.csv',
  header = true
);

CREATE OR REPLACE TEMP TABLE primer_map AS
SELECT
  observed.sequence AS observed_sequence,
  canonical.sequence AS canonical_sequence
FROM v2_metadata AS observed
JOIN v2_metadata AS canonical
  ON canonical.well = observed.well
 AND canonical.type = 'T';

CREATE OR REPLACE TEMP TABLE raw_assignments AS
SELECT
  'Flexiplex no-polyT' AS tool,
  read_id,
  barcode AS observed_barcode,
  umi
FROM read_csv_auto(
  '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/assignments.tsv.gz',
  delim = '\t',
  header = true,
  all_varchar = true
)
UNION ALL
SELECT
  'Flexiplex polyT' AS tool,
  read_id,
  barcode AS observed_barcode,
  umi
FROM read_csv_auto(
  '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_polyt_paired_t4/assignments.tsv.gz',
  delim = '\t',
  header = true,
  all_varchar = true
)
UNION ALL
SELECT
  'RAD main ED1' AS tool,
  read_id,
  barcode AS observed_barcode,
  umi
FROM read_csv_auto(
  '/Volumes/CMV_SSD_2/results/rad/demultiplexed/splitseq/20260727_static_collision_fix_full_main_ed1/assignments.tsv.gz',
  delim = '\t',
  header = true,
  all_varchar = true
);

CREATE OR REPLACE TEMP TABLE assignments AS
SELECT DISTINCT
  raw.tool,
  raw.read_id,
  concat(
    primer.canonical_sequence, '_',
    split_part(raw.observed_barcode, '_', 2), '_',
    split_part(raw.observed_barcode, '_', 3)
  ) AS cell,
  raw.umi
FROM raw_assignments AS raw
JOIN primer_map AS primer
  ON primer.observed_sequence = split_part(raw.observed_barcode, '_', 1)
WHERE raw.observed_barcode <> ''
  AND raw.umi <> '';

CREATE OR REPLACE TEMP TABLE tools AS
SELECT DISTINCT tool FROM assignments;

CREATE OR REPLACE TEMP TABLE per_published_cell AS
WITH counts AS (
  SELECT
    assignments.tool,
    assignments.cell,
    count(DISTINCT assignments.umi) AS tool_umis,
    count(DISTINCT assignments.umi) FILTER (
      WHERE length(assignments.umi) = 10
    ) AS full_10nt_tool_umis,
    count(DISTINCT assignments.read_id) AS tool_reads,
    count(DISTINCT assignments.read_id) FILTER (
      WHERE length(assignments.umi) = 10
    ) AS full_10nt_tool_reads
  FROM assignments
  JOIN published USING (cell)
  GROUP BY assignments.tool, assignments.cell
)
SELECT
  tools.tool,
  published.cell,
  published.published_lr_umis,
  published.published_sr_umis,
  coalesce(counts.tool_umis, 0) AS tool_umis,
  coalesce(counts.full_10nt_tool_umis, 0) AS full_10nt_tool_umis,
  coalesce(counts.tool_reads, 0) AS tool_reads,
  coalesce(counts.full_10nt_tool_reads, 0) AS full_10nt_tool_reads
FROM tools
CROSS JOIN published
LEFT JOIN counts
  ON counts.tool = tools.tool
 AND counts.cell = published.cell;

COPY (
  SELECT *
  FROM per_published_cell
  ORDER BY tool, published_lr_umis DESC, cell
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/per_published_cell_counts.tsv'
(HEADER, DELIMITER '\t');

COPY (
  WITH long_form AS (
    SELECT
      tool,
      cell,
      'all_umi_lengths' AS umi_scope,
      tool_umis AS observed_umis,
      published_lr_umis,
      published_sr_umis
    FROM per_published_cell
    UNION ALL
    SELECT
      tool,
      cell,
      'full_10nt_only' AS umi_scope,
      full_10nt_tool_umis AS observed_umis,
      published_lr_umis,
      published_sr_umis
    FROM per_published_cell
  ),
  tied_ranks AS (
    SELECT
      *,
      rank() OVER (
        PARTITION BY tool, umi_scope ORDER BY observed_umis
      ) + (
        count(*) OVER (
          PARTITION BY tool, umi_scope, observed_umis
        ) - 1
      ) / 2.0 AS observed_rank,
      rank() OVER (
        PARTITION BY tool, umi_scope ORDER BY published_lr_umis
      ) + (
        count(*) OVER (
          PARTITION BY tool, umi_scope, published_lr_umis
        ) - 1
      ) / 2.0 AS published_lr_rank,
      rank() OVER (
        PARTITION BY tool, umi_scope ORDER BY published_sr_umis
      ) + (
        count(*) OVER (
          PARTITION BY tool, umi_scope, published_sr_umis
        ) - 1
      ) / 2.0 AS published_sr_rank
    FROM long_form
  )
  SELECT
    tool,
    umi_scope,
    count(*) AS published_cells,
    corr(observed_rank, published_lr_rank)
      AS spearman_vs_published_long_read_umis,
    corr(observed_rank, published_sr_rank)
      AS spearman_vs_published_short_read_umis
  FROM tied_ranks
  GROUP BY tool, umi_scope
  ORDER BY tool, umi_scope
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/per_cell_umi_count_spearman.tsv'
(HEADER, DELIMITER '\t');

COPY (
  WITH all_metrics AS (
    SELECT
      tool,
      count(*) AS assignment_tuples,
      count(*) FILTER (WHERE length(umi) = 10)
        AS full_10nt_assignment_tuples,
      count(DISTINCT read_id) AS source_reads,
      count(DISTINCT read_id) FILTER (WHERE length(umi) = 10)
        AS source_reads_with_full_10nt_umi,
      count(DISTINCT (cell, umi)) AS cell_umis,
      count(DISTINCT (cell, umi)) FILTER (WHERE length(umi) = 10)
        AS full_10nt_cell_umis
    FROM assignments
    GROUP BY tool
  ),
  published_metrics AS (
    SELECT
      tool,
      count(DISTINCT read_id) AS published_source_reads,
      count(DISTINCT read_id) FILTER (WHERE length(umi) = 10)
        AS published_source_reads_with_full_10nt_umi,
      count(DISTINCT (cell, umi)) AS published_cell_umis,
      count(DISTINCT (cell, umi)) FILTER (WHERE length(umi) = 10)
        AS published_full_10nt_cell_umis
    FROM assignments
    JOIN published USING (cell)
    GROUP BY tool
  ),
  per_cell_summary AS (
    SELECT
      tool,
      median(tool_umis) AS median_published_cell_umis,
      median(full_10nt_tool_umis) AS median_published_full_10nt_cell_umis
    FROM per_published_cell
    GROUP BY tool
  )
  SELECT
    all_metrics.*,
    all_metrics.full_10nt_assignment_tuples::DOUBLE
      / all_metrics.assignment_tuples AS full_10nt_assignment_fraction,
    all_metrics.source_reads_with_full_10nt_umi::DOUBLE
      / all_metrics.source_reads AS source_read_full_10nt_fraction,
    all_metrics.full_10nt_cell_umis::DOUBLE
      / all_metrics.cell_umis AS cell_umi_full_10nt_fraction,
    published_metrics.published_source_reads,
    published_metrics.published_source_reads_with_full_10nt_umi,
    published_metrics.published_cell_umis,
    published_metrics.published_full_10nt_cell_umis,
    published_metrics.published_full_10nt_cell_umis::DOUBLE
      / published_metrics.published_cell_umis
      AS published_cell_umi_full_10nt_fraction,
    per_cell_summary.median_published_cell_umis,
    per_cell_summary.median_published_full_10nt_cell_umis
  FROM all_metrics
  JOIN published_metrics USING (tool)
  JOIN per_cell_summary USING (tool)
  ORDER BY tool
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/full_10nt_umi_metrics.tsv'
(HEADER, DELIMITER '\t');
