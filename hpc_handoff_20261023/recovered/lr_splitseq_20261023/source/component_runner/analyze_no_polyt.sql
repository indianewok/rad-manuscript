SET temp_directory = '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/duckdb_tmp';
SET memory_limit = '8GB';
SET threads = 4;

CREATE OR REPLACE TEMP TABLE published AS
SELECT DISTINCT canonical_barcode AS cell
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
  observed.type AS primer_type,
  observed.well,
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
  raw.observed_barcode,
  concat(
    primer.canonical_sequence, '_',
    split_part(raw.observed_barcode, '_', 2), '_',
    split_part(raw.observed_barcode, '_', 3)
  ) AS cell,
  raw.umi,
  primer.primer_type
FROM raw_assignments AS raw
JOIN primer_map AS primer
  ON primer.observed_sequence = split_part(raw.observed_barcode, '_', 1)
WHERE raw.observed_barcode <> ''
  AND raw.umi <> '';

CREATE OR REPLACE TEMP TABLE published_assignments AS
SELECT DISTINCT assignments.*
FROM assignments
JOIN published USING (cell);

CREATE OR REPLACE TEMP TABLE per_published_cell AS
SELECT
  tool,
  cell,
  count(DISTINCT read_id) AS unique_reads,
  count(DISTINCT umi) AS unique_umis
FROM published_assignments
GROUP BY tool, cell;

COPY (
  WITH canonical_counts AS (
    SELECT
      tool,
      count(*) AS canonical_assignment_tuples,
      count(DISTINCT read_id) AS canonical_source_reads,
      count(DISTINCT cell) AS canonical_cells,
      count(DISTINCT (cell, umi)) AS canonical_cell_umis,
      count(*) FILTER (WHERE length(umi) = 10) AS full_10nt_umi_tuples,
      count(*) FILTER (WHERE length(umi) < 10) AS short_umi_tuples
    FROM assignments
    GROUP BY tool
  ),
  raw_counts AS (
    SELECT
      tool,
      count(*) AS raw_assignment_rows,
      count(DISTINCT read_id) AS raw_source_reads,
      count(DISTINCT observed_barcode) AS raw_observed_combinations,
      count(*) FILTER (
        WHERE split_part(observed_barcode, '_', 1)
          NOT IN (SELECT observed_sequence FROM primer_map)
      ) AS unmappable_assignment_rows
    FROM raw_assignments
    GROUP BY tool
  )
  SELECT
    raw_counts.tool,
    5764421 AS input_source_reads,
    raw_counts.raw_assignment_rows,
    raw_counts.raw_source_reads,
    raw_counts.raw_observed_combinations,
    raw_counts.unmappable_assignment_rows,
    canonical_counts.canonical_assignment_tuples,
    canonical_counts.canonical_source_reads,
    canonical_counts.canonical_cells,
    canonical_counts.canonical_cell_umis,
    canonical_counts.full_10nt_umi_tuples,
    canonical_counts.short_umi_tuples
  FROM raw_counts
  JOIN canonical_counts USING (tool)
  ORDER BY tool
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/total_assignment_metrics.tsv'
(HEADER, DELIMITER '\t');

COPY (
  WITH overall AS (
    SELECT
      tool,
      count(DISTINCT read_id) AS unique_reads_across_published_cells,
      count(DISTINCT cell) AS published_cells_detected,
      count(DISTINCT (cell, umi)) AS unique_cell_umi_pairs,
      count(DISTINCT (read_id, cell)) AS unique_read_cell_pairs,
      count(DISTINCT (read_id, cell, umi)) AS unique_read_cell_umi_tuples
    FROM published_assignments
    GROUP BY tool
  ),
  cell_summary AS (
    SELECT
      tool,
      median(unique_reads) AS median_reads_per_published_cell,
      median(unique_umis) AS median_umis_per_published_cell,
      sum(unique_reads) AS sum_per_cell_unique_reads
    FROM per_published_cell
    GROUP BY tool
  )
  SELECT
    overall.tool,
    overall.unique_reads_across_published_cells,
    cell_summary.median_reads_per_published_cell,
    overall.published_cells_detected,
    568 AS published_cells_total,
    overall.unique_cell_umi_pairs,
    cell_summary.median_umis_per_published_cell,
    overall.unique_read_cell_pairs,
    overall.unique_read_cell_umi_tuples,
    cell_summary.sum_per_cell_unique_reads
  FROM overall
  JOIN cell_summary USING (tool)
  ORDER BY overall.tool
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/published_cell_metrics.tsv'
(HEADER, DELIMITER '\t');

COPY (
  SELECT
    tool,
    primer_type,
    count(*) AS assignment_tuples,
    count(DISTINCT read_id) AS source_reads,
    count(DISTINCT observed_barcode) AS observed_combinations,
    count(DISTINCT cell) AS canonical_cells,
    count(DISTINCT read_id) FILTER (
      WHERE cell IN (SELECT cell FROM published)
    ) AS source_reads_in_published_cells,
    count(DISTINCT (cell, umi)) FILTER (
      WHERE cell IN (SELECT cell FROM published)
    ) AS cell_umis_in_published_cells
  FROM assignments
  GROUP BY tool, primer_type
  ORDER BY tool, primer_type
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/primer_call_summary.tsv'
(HEADER, DELIMITER '\t');

CREATE OR REPLACE TEMP TABLE barcode_counts AS
SELECT
  tool,
  cell,
  count(DISTINCT read_id) AS source_reads,
  count(DISTINCT umi) AS distinct_umis,
  cell IN (SELECT cell FROM published) AS is_published
FROM assignments
GROUP BY tool, cell;

COPY (
  WITH ranked AS (
    SELECT
      *,
      row_number() OVER (
        PARTITION BY tool
        ORDER BY distinct_umis DESC, cell
      ) AS barcode_rank
    FROM barcode_counts
  )
  SELECT
    tool,
    count(*) AS observed_combinations,
    count(*) FILTER (WHERE is_published) AS published_observed,
    count(*) FILTER (WHERE NOT is_published) AS off_reference_observed,
    count(*) FILTER (WHERE distinct_umis >= 100) AS combinations_at_100_umis,
    count(*) FILTER (
      WHERE distinct_umis >= 100 AND is_published
    ) AS published_at_100_umis,
    count(*) FILTER (
      WHERE distinct_umis >= 100 AND NOT is_published
    ) AS off_reference_at_100_umis,
    count(*) FILTER (
      WHERE barcode_rank <= 568 AND is_published
    ) AS published_in_top_568,
    count(*) FILTER (
      WHERE barcode_rank <= 568 AND NOT is_published
    ) AS off_reference_in_top_568
  FROM ranked
  GROUP BY tool
  ORDER BY tool
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/combination_ranking_metrics.tsv'
(HEADER, DELIMITER '\t');

COPY (
  WITH thresholds(threshold) AS (
    VALUES (1), (2), (5), (10), (25), (50), (100), (250), (500), (1000)
  )
  SELECT
    counts.tool,
    thresholds.threshold AS minimum_distinct_umis,
    count(*) AS combinations,
    count(*) FILTER (WHERE counts.is_published) AS published,
    count(*) FILTER (WHERE NOT counts.is_published) AS off_reference
  FROM barcode_counts AS counts
  CROSS JOIN thresholds
  WHERE counts.distinct_umis >= thresholds.threshold
  GROUP BY counts.tool, thresholds.threshold
  ORDER BY counts.tool, thresholds.threshold
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/combination_thresholds.tsv'
(HEADER, DELIMITER '\t');

CREATE OR REPLACE TEMP TABLE exact_truth AS
SELECT DISTINCT
  raw.read_id,
  primer.primer_type,
  concat(
    primer.canonical_sequence, '_',
    raw.bc2, '_',
    raw.bc1
  ) AS truth_cell,
  raw.umi AS truth_umi,
  CASE
    WHEN truth_cell IN (SELECT cell FROM published) THEN 'published'
    ELSE 'off_reference'
  END AS truth_class
FROM read_csv_auto(
  '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/reference/raw_exact_rad_constructs.tsv.gz',
  delim = '\t',
  header = true,
  all_varchar = true
) AS raw
JOIN primer_map AS primer
  ON primer.observed_sequence = raw.observed_v2;

SELECT CASE
  WHEN (
    SELECT count(DISTINCT read_id)
    FROM exact_truth
    WHERE truth_class = 'published' AND primer_type = 'T'
  ) = 437006
   AND (
    SELECT count(DISTINCT read_id)
    FROM exact_truth
    WHERE truth_class = 'published' AND primer_type = 'R'
  ) = 388660
  THEN true
  ELSE error(
    'raw-exact truth denominator mismatch; expected published T=437006 and R=388660'
  )
END AS raw_exact_truth_validated;

CREATE OR REPLACE TEMP TABLE scoped_truth AS
SELECT 'all_physical' AS scope, * FROM exact_truth
UNION ALL
SELECT 'published' AS scope, * FROM exact_truth WHERE truth_class = 'published';

COPY (
  WITH
  tools AS (
    SELECT DISTINCT tool FROM assignments
  ),
  truth_reads AS (
    SELECT DISTINCT scope, primer_type, read_id
    FROM scoped_truth
  ),
  denominators AS (
    SELECT
      scope,
      primer_type,
      count(*) AS raw_exact_source_reads
    FROM truth_reads
    GROUP BY scope, primer_type
  ),
  any_calls AS (
    SELECT DISTINCT
      truth.scope,
      truth.primer_type,
      calls.tool,
      truth.read_id
    FROM truth_reads AS truth
    JOIN assignments AS calls USING (read_id)
  ),
  correct_cells AS (
    SELECT DISTINCT
      truth.scope,
      truth.primer_type,
      calls.tool,
      truth.read_id
    FROM scoped_truth AS truth
    JOIN assignments AS calls
      ON calls.read_id = truth.read_id
     AND calls.cell = truth.truth_cell
  ),
  correct_molecules AS (
    SELECT DISTINCT
      truth.scope,
      truth.primer_type,
      calls.tool,
      truth.read_id
    FROM scoped_truth AS truth
    JOIN assignments AS calls
      ON calls.read_id = truth.read_id
     AND calls.cell = truth.truth_cell
     AND calls.umi = truth.truth_umi
  ),
  grouped AS (
    SELECT
      denominators.scope,
      denominators.primer_type,
      tools.tool,
      denominators.raw_exact_source_reads,
      count(any_calls.read_id) AS source_reads_with_any_call,
      count(correct_cells.read_id) AS source_reads_with_correct_cell,
      count(correct_molecules.read_id) AS source_reads_with_exact_cell_umi
    FROM denominators
    CROSS JOIN tools
    LEFT JOIN any_calls
      ON any_calls.scope = denominators.scope
     AND any_calls.primer_type = denominators.primer_type
     AND any_calls.tool = tools.tool
    LEFT JOIN correct_cells
      ON correct_cells.scope = denominators.scope
     AND correct_cells.primer_type = denominators.primer_type
     AND correct_cells.tool = tools.tool
     AND correct_cells.read_id = any_calls.read_id
    LEFT JOIN correct_molecules
      ON correct_molecules.scope = denominators.scope
     AND correct_molecules.primer_type = denominators.primer_type
     AND correct_molecules.tool = tools.tool
     AND correct_molecules.read_id = any_calls.read_id
    GROUP BY
      denominators.scope,
      denominators.primer_type,
      tools.tool,
      denominators.raw_exact_source_reads
  )
  SELECT
    *,
    source_reads_with_any_call - source_reads_with_correct_cell
      AS source_reads_wrong_cell_only,
    raw_exact_source_reads - source_reads_with_any_call
      AS source_reads_without_call,
    source_reads_with_any_call::DOUBLE / raw_exact_source_reads
      AS call_rate,
    source_reads_with_correct_cell::DOUBLE / source_reads_with_any_call
      AS correct_cell_rate_among_called,
    (source_reads_with_any_call - source_reads_with_correct_cell)::DOUBLE
      / source_reads_with_any_call AS wrong_cell_rate_among_called,
    source_reads_with_exact_cell_umi::DOUBLE / source_reads_with_any_call
      AS exact_cell_umi_rate_among_called
  FROM grouped
  ORDER BY scope, primer_type, tool
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/raw_exact_primer_validation.tsv'
(HEADER, DELIMITER '\t');

CREATE OR REPLACE TEMP TABLE pairs(left_tool, right_tool) AS
VALUES
  ('Flexiplex no-polyT', 'Flexiplex polyT'),
  ('Flexiplex no-polyT', 'RAD main ED1'),
  ('Flexiplex polyT', 'RAD main ED1');

CREATE OR REPLACE TEMP TABLE scoped_assignments AS
SELECT 'all_physical' AS scope, tool, read_id, cell, umi
FROM assignments
UNION ALL
SELECT 'published' AS scope, tool, read_id, cell, umi
FROM published_assignments;

CREATE OR REPLACE TEMP TABLE scoped_reads AS
SELECT DISTINCT scope, tool, read_id
FROM scoped_assignments;

CREATE OR REPLACE TEMP TABLE tool_scope_counts AS
SELECT scope, tool, count(*) AS source_reads
FROM scoped_reads
GROUP BY scope, tool;

CREATE OR REPLACE TEMP TABLE shared_reads AS
SELECT
  left_reads.scope,
  pairs.left_tool,
  pairs.right_tool,
  left_reads.read_id
FROM pairs
JOIN scoped_reads AS left_reads
  ON left_reads.tool = pairs.left_tool
JOIN scoped_reads AS right_reads
  ON right_reads.scope = left_reads.scope
 AND right_reads.tool = pairs.right_tool
 AND right_reads.read_id = left_reads.read_id;

CREATE OR REPLACE TEMP TABLE shared_same_cell AS
SELECT DISTINCT
  left_calls.scope,
  pairs.left_tool,
  pairs.right_tool,
  left_calls.read_id
FROM pairs
JOIN scoped_assignments AS left_calls
  ON left_calls.tool = pairs.left_tool
JOIN scoped_assignments AS right_calls
  ON right_calls.scope = left_calls.scope
 AND right_calls.tool = pairs.right_tool
 AND right_calls.read_id = left_calls.read_id
 AND right_calls.cell = left_calls.cell;

CREATE OR REPLACE TEMP TABLE shared_same_cell_umi AS
SELECT DISTINCT
  left_calls.scope,
  pairs.left_tool,
  pairs.right_tool,
  left_calls.read_id
FROM pairs
JOIN scoped_assignments AS left_calls
  ON left_calls.tool = pairs.left_tool
JOIN scoped_assignments AS right_calls
  ON right_calls.scope = left_calls.scope
 AND right_calls.tool = pairs.right_tool
 AND right_calls.read_id = left_calls.read_id
 AND right_calls.cell = left_calls.cell
 AND right_calls.umi = left_calls.umi;

COPY (
  WITH scopes AS (
    SELECT DISTINCT scope FROM scoped_reads
  ),
  shared_counts AS (
    SELECT
      scope,
      left_tool,
      right_tool,
      count(*) AS shared_source_reads
    FROM shared_reads
    GROUP BY scope, left_tool, right_tool
  ),
  same_cell_counts AS (
    SELECT
      scope,
      left_tool,
      right_tool,
      count(*) AS shared_with_any_same_cell
    FROM shared_same_cell
    GROUP BY scope, left_tool, right_tool
  ),
  same_molecule_counts AS (
    SELECT
      scope,
      left_tool,
      right_tool,
      count(*) AS shared_with_any_same_cell_umi
    FROM shared_same_cell_umi
    GROUP BY scope, left_tool, right_tool
  )
  SELECT
    scopes.scope,
    pairs.left_tool,
    pairs.right_tool,
    left_counts.source_reads AS left_source_reads,
    right_counts.source_reads AS right_source_reads,
    shared_counts.shared_source_reads,
    left_counts.source_reads - shared_counts.shared_source_reads
      AS left_only_source_reads,
    right_counts.source_reads - shared_counts.shared_source_reads
      AS right_only_source_reads,
    coalesce(same_cell_counts.shared_with_any_same_cell, 0)
      AS shared_with_any_same_cell,
    shared_counts.shared_source_reads
      - coalesce(same_cell_counts.shared_with_any_same_cell, 0)
      AS shared_without_same_cell,
    coalesce(same_molecule_counts.shared_with_any_same_cell_umi, 0)
      AS shared_with_any_same_cell_umi,
    coalesce(same_cell_counts.shared_with_any_same_cell, 0)::DOUBLE
      / shared_counts.shared_source_reads AS same_cell_rate_among_shared,
    coalesce(same_molecule_counts.shared_with_any_same_cell_umi, 0)::DOUBLE
      / shared_counts.shared_source_reads AS same_cell_umi_rate_among_shared,
    shared_counts.shared_source_reads::DOUBLE
      / (
        left_counts.source_reads
        + right_counts.source_reads
        - shared_counts.shared_source_reads
      ) AS source_read_jaccard
  FROM pairs
  CROSS JOIN scopes
  JOIN tool_scope_counts AS left_counts
    ON left_counts.scope = scopes.scope
   AND left_counts.tool = pairs.left_tool
  JOIN tool_scope_counts AS right_counts
    ON right_counts.scope = scopes.scope
   AND right_counts.tool = pairs.right_tool
  JOIN shared_counts
    ON shared_counts.scope = scopes.scope
   AND shared_counts.left_tool = pairs.left_tool
   AND shared_counts.right_tool = pairs.right_tool
  LEFT JOIN same_cell_counts
    ON same_cell_counts.scope = scopes.scope
   AND same_cell_counts.left_tool = pairs.left_tool
   AND same_cell_counts.right_tool = pairs.right_tool
  LEFT JOIN same_molecule_counts
    ON same_molecule_counts.scope = scopes.scope
   AND same_molecule_counts.left_tool = pairs.left_tool
   AND same_molecule_counts.right_tool = pairs.right_tool
  ORDER BY scopes.scope, pairs.left_tool, pairs.right_tool
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/pairwise_read_overlap.tsv'
(HEADER, DELIMITER '\t');

COPY (
  SELECT
    tool,
    length(umi) AS umi_length,
    count(*) AS assignment_tuples,
    count(DISTINCT read_id) AS source_reads
  FROM assignments
  GROUP BY tool, length(umi)
  ORDER BY tool, umi_length
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/umi_length_distribution.tsv'
(HEADER, DELIMITER '\t');
