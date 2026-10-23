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
  canonical.sequence AS canonical_sequence
FROM v2_metadata AS observed
JOIN v2_metadata AS canonical
  ON canonical.well = observed.well
 AND canonical.type = 'T';

CREATE OR REPLACE TEMP TABLE flex_raw AS
SELECT
  read_id,
  barcode AS observed_barcode,
  umi,
  try_cast(flank_edit_distance AS INTEGER) AS flank_edit_distance
FROM read_csv_auto(
  '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/assignments.tsv.gz',
  delim = '\t',
  header = true,
  all_varchar = true
);

CREATE OR REPLACE TEMP TABLE rad_raw AS
SELECT read_id, barcode AS observed_barcode, umi
FROM read_csv_auto(
  '/Volumes/CMV_SSD_2/results/rad/demultiplexed/splitseq/20260727_static_collision_fix_full_main_ed1/assignments.tsv.gz',
  delim = '\t',
  header = true,
  all_varchar = true
);

-- Canonicalize the R and T variants of the third SPLiT-seq barcode to the
-- same physical well. In the normalized strings, this is component 1.
CREATE OR REPLACE TEMP TABLE flex AS
SELECT DISTINCT
  raw.read_id,
  raw.observed_barcode,
  concat(
    primer.canonical_sequence, '_',
    split_part(raw.observed_barcode, '_', 2), '_',
    split_part(raw.observed_barcode, '_', 3)
  ) AS cell,
  raw.umi,
  primer.primer_type,
  raw.flank_edit_distance
FROM flex_raw AS raw
JOIN primer_map AS primer
  ON primer.observed_sequence = split_part(raw.observed_barcode, '_', 1)
WHERE raw.observed_barcode <> ''
  AND raw.umi <> '';

CREATE OR REPLACE TEMP TABLE rad AS
SELECT DISTINCT
  raw.read_id,
  raw.observed_barcode,
  concat(
    primer.canonical_sequence, '_',
    split_part(raw.observed_barcode, '_', 2), '_',
    split_part(raw.observed_barcode, '_', 3)
  ) AS cell,
  raw.umi,
  primer.primer_type
FROM rad_raw AS raw
JOIN primer_map AS primer
  ON primer.observed_sequence = split_part(raw.observed_barcode, '_', 1)
WHERE raw.observed_barcode <> ''
  AND raw.umi <> '';

CREATE OR REPLACE TEMP TABLE flex_published AS
SELECT flex.*
FROM flex
JOIN published USING (cell);

CREATE OR REPLACE TEMP TABLE rad_published AS
SELECT rad.*
FROM rad
JOIN published USING (cell);

-- This is the exact 327,538-read set discussed in pairwise_read_overlap.tsv:
-- Flexiplex assigned the source read to at least one published physical cell,
-- while RAD assigned it to no published physical cell.
CREATE OR REPLACE TEMP TABLE cohort AS
SELECT DISTINCT read_id
FROM flex_published AS flex
WHERE NOT EXISTS (
  SELECT 1
  FROM rad_published AS rad
  WHERE rad.read_id = flex.read_id
);

CREATE OR REPLACE TEMP TABLE flex_cohort AS
SELECT flex.*
FROM flex_published AS flex
JOIN cohort USING (read_id);

CREATE OR REPLACE TEMP TABLE rad_cohort AS
SELECT rad.*
FROM rad
JOIN cohort USING (read_id);

-- Flexiplex appends "_C" when a complete structure is found in both the
-- forward read and its reverse complement. Extract source IDs, match
-- orientation, and that flag from the demultiplexed FASTQ headers.
CREATE OR REPLACE TEMP TABLE flex_header_calls AS
SELECT
  split_part(split_part(line, '#', 2), '_', 1) AS read_id,
  regexp_extract(line, '#[^\t]*_([+-])[0-9]+of', 1) AS orientation,
  regexp_matches(line, '_[+-][0-9]+of[0-9]+_C(\t|$)') AS chimeric
FROM read_csv(
  '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/demultiplexed.fastq.gz',
  header = false,
  delim = '\x1f',
  columns = {'line': 'VARCHAR'},
  quote = '',
  escape = '',
  ignore_errors = true
)
WHERE starts_with(line, '@');

CREATE OR REPLACE TEMP TABLE flex_chimeric_ids AS
SELECT DISTINCT read_id
FROM flex_header_calls
WHERE chimeric;

CREATE OR REPLACE TEMP TABLE flex_orientation_properties AS
SELECT
  cohort.read_id,
  CASE
    WHEN bool_or(header.orientation = '+')
     AND bool_or(header.orientation = '-') THEN '+/-'
    WHEN bool_or(header.orientation = '+') THEN '+'
    WHEN bool_or(header.orientation = '-') THEN '-'
    ELSE 'unknown'
  END AS flex_match_orientation
FROM cohort
JOIN flex_header_calls AS header USING (read_id)
GROUP BY cohort.read_id;

CREATE OR REPLACE TEMP TABLE exact_truth AS
SELECT DISTINCT
  raw.read_id,
  concat(
    primer.canonical_sequence, '_',
    raw.bc2, '_',
    raw.bc1
  ) AS truth_cell,
  raw.umi AS truth_umi,
  primer.primer_type AS truth_primer_type,
  CASE
    WHEN truth_cell IN (SELECT cell FROM published) THEN 'published'
    ELSE 'off_568'
  END AS truth_class
FROM read_csv_auto(
  '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/reference/raw_exact_rad_constructs.tsv.gz',
  delim = '\t',
  header = true,
  all_varchar = true
) AS raw
JOIN primer_map AS primer
  ON primer.observed_sequence = raw.observed_v2;

CREATE OR REPLACE TEMP TABLE flex_properties AS
SELECT
  read_id,
  CASE
    WHEN bool_or(primer_type = 'R') AND bool_or(primer_type = 'T') THEN 'R+T'
    WHEN bool_or(primer_type = 'R') THEN 'R'
    WHEN bool_or(primer_type = 'T') THEN 'T'
    ELSE 'unmapped'
  END AS flex_primer_types,
  min(length(umi)) AS min_umi_length,
  max(length(umi)) AS max_umi_length,
  min(flank_edit_distance) AS min_flank_edit_distance,
  max(flank_edit_distance) AS max_flank_edit_distance,
  count(DISTINCT cell) AS flex_published_cells,
  count(DISTINCT (cell, umi)) AS flex_published_cell_umis
FROM flex_cohort
GROUP BY read_id;

CREATE OR REPLACE TEMP TABLE rad_properties AS
SELECT
  cohort.read_id,
  count(DISTINCT rad_raw.observed_barcode) AS rad_raw_output_barcodes,
  count(DISTINCT rad.cell) AS rad_canonical_cells,
  count(DISTINCT rad.cell) FILTER (
    WHERE rad.cell IN (SELECT cell FROM published)
  ) AS rad_published_cells
FROM cohort
LEFT JOIN rad_raw USING (read_id)
LEFT JOIN rad USING (read_id)
GROUP BY cohort.read_id;

CREATE OR REPLACE TEMP TABLE truth_properties AS
SELECT
  cohort.read_id,
  count(DISTINCT truth.truth_cell) AS exact_truth_cells,
  bool_or(truth.truth_class = 'published') AS exact_truth_has_published_cell,
  bool_or(truth.truth_class = 'off_568') AS exact_truth_has_off_568_cell,
  bool_or(truth.truth_cell = flex.cell) AS exact_truth_matches_flex_cell,
  bool_or(
    truth.truth_cell = flex.cell AND truth.truth_umi = flex.umi
  ) AS exact_truth_matches_flex_cell_umi
FROM cohort
LEFT JOIN exact_truth AS truth USING (read_id)
LEFT JOIN flex_cohort AS flex USING (read_id)
GROUP BY cohort.read_id;

CREATE OR REPLACE TEMP TABLE classified AS
SELECT
  cohort.read_id,
  CASE
    WHEN rad_properties.rad_raw_output_barcodes = 0
      THEN 'no_RAD_output_assignment'
    WHEN rad_properties.rad_canonical_cells = 0
      THEN 'RAD_output_not_canonicalizable'
    WHEN rad_properties.rad_published_cells = 0
      THEN 'RAD_assigned_only_off_568'
    ELSE 'RAD_assigned_published_definition_check'
  END AS rad_fate,
  flex.flex_primer_types,
  flex.min_umi_length,
  flex.max_umi_length,
  flex.min_flank_edit_distance,
  flex.max_flank_edit_distance,
  flex.flex_published_cells,
  flex.flex_published_cell_umis,
  orientation.flex_match_orientation,
  chimeric.read_id IS NOT NULL AS flex_chimeric,
  truth.exact_truth_cells,
  coalesce(truth.exact_truth_has_published_cell, false)
    AS exact_truth_has_published_cell,
  coalesce(truth.exact_truth_has_off_568_cell, false)
    AS exact_truth_has_off_568_cell,
  coalesce(truth.exact_truth_matches_flex_cell, false)
    AS exact_truth_matches_flex_cell,
  coalesce(truth.exact_truth_matches_flex_cell_umi, false)
    AS exact_truth_matches_flex_cell_umi,
  CASE
    WHEN truth.exact_truth_cells = 0
      THEN 'no_raw_exact_panel_support'
    WHEN truth.exact_truth_matches_flex_cell_umi
      THEN 'raw_exact_supports_Flex_cell_and_UMI'
    WHEN truth.exact_truth_matches_flex_cell
      THEN 'raw_exact_supports_Flex_cell_not_UMI'
    WHEN truth.exact_truth_has_published_cell
      THEN 'raw_exact_supports_different_published_cell'
    WHEN truth.exact_truth_has_off_568_cell
      THEN 'raw_exact_supports_off_568_cell'
    ELSE 'raw_exact_other'
  END AS exact_truth_status
FROM cohort
JOIN flex_properties AS flex USING (read_id)
JOIN rad_properties USING (read_id)
JOIN truth_properties AS truth USING (read_id)
JOIN flex_orientation_properties AS orientation USING (read_id)
LEFT JOIN flex_chimeric_ids AS chimeric USING (read_id);

COPY (
  SELECT
    rad_fate,
    count(*) AS source_reads,
    count(*)::DOUBLE / sum(count(*)) OVER () AS fraction_of_327538
  FROM classified
  GROUP BY rad_fate
  ORDER BY source_reads DESC
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/flex_only_rad_fate.tsv'
(HEADER, DELIMITER '\t');

COPY (
  SELECT
    rad_fate,
    flex_primer_types,
    count(*) AS source_reads,
    count(*) FILTER (WHERE flex_chimeric) AS flex_chimeric_source_reads,
    count(*) FILTER (
      WHERE min_umi_length = 10 AND max_umi_length = 10
    ) AS full_10nt_umi_source_reads,
    count(*) FILTER (
      WHERE exact_truth_status <> 'no_raw_exact_panel_support'
    ) AS raw_exact_panel_source_reads
  FROM classified
  GROUP BY rad_fate, flex_primer_types
  ORDER BY rad_fate, flex_primer_types
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/flex_only_by_fate_and_primer.tsv'
(HEADER, DELIMITER '\t');

COPY (
  SELECT
    rad_fate,
    min_umi_length,
    max_umi_length,
    count(*) AS source_reads
  FROM classified
  GROUP BY rad_fate, min_umi_length, max_umi_length
  ORDER BY rad_fate, min_umi_length, max_umi_length
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/flex_only_umi_length.tsv'
(HEADER, DELIMITER '\t');

COPY (
  SELECT
    rad_fate,
    min_flank_edit_distance,
    max_flank_edit_distance,
    count(*) AS source_reads
  FROM classified
  GROUP BY rad_fate, min_flank_edit_distance, max_flank_edit_distance
  ORDER BY rad_fate, min_flank_edit_distance, max_flank_edit_distance
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/flex_only_flank_edit_distance.tsv'
(HEADER, DELIMITER '\t');

COPY (
  SELECT
    rad_fate,
    exact_truth_status,
    count(*) AS source_reads
  FROM classified
  GROUP BY rad_fate, exact_truth_status
  ORDER BY rad_fate, source_reads DESC
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/flex_only_exact_truth.tsv'
(HEADER, DELIMITER '\t');

COPY (
  SELECT
    rad_fate,
    flex_chimeric,
    flex_published_cells,
    flex_published_cell_umis,
    count(*) AS source_reads
  FROM classified
  GROUP BY
    rad_fate,
    flex_chimeric,
    flex_published_cells,
    flex_published_cell_umis
  ORDER BY rad_fate, flex_chimeric, flex_published_cells, flex_published_cell_umis
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/flex_only_multiplicity_and_chimera.tsv'
(HEADER, DELIMITER '\t');

COPY (
  SELECT
    rad_fate,
    flex_match_orientation,
    count(*) AS source_reads
  FROM classified
  GROUP BY rad_fate, flex_match_orientation
  ORDER BY rad_fate, flex_match_orientation
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/flex_only_orientation.tsv'
(HEADER, DELIMITER '\t');

-- For reads that RAD sends only to off-568 combinations, select the closest
-- Flex/RAD cell pair by number of component disagreements and report which
-- barcode component(s) differ. This is a destination description, not an
-- assertion that the RAD or Flexiplex assignment is biologically correct.
CREATE OR REPLACE TEMP TABLE rad_off_pair_candidates AS
SELECT
  flex.read_id,
  flex.cell AS flex_published_cell,
  rad.cell AS rad_off_568_cell,
  flex.primer_type AS flex_primer_type,
  rad.primer_type AS rad_primer_type,
  (
    (split_part(flex.cell, '_', 1) <> split_part(rad.cell, '_', 1))::INTEGER
    + (split_part(flex.cell, '_', 2) <> split_part(rad.cell, '_', 2))::INTEGER
    + (split_part(flex.cell, '_', 3) <> split_part(rad.cell, '_', 3))::INTEGER
  ) AS differing_components,
  concat_ws(
    '+',
    CASE WHEN split_part(flex.cell, '_', 1) <> split_part(rad.cell, '_', 1)
      THEN 'BC3_v2' END,
    CASE WHEN split_part(flex.cell, '_', 2) <> split_part(rad.cell, '_', 2)
      THEN 'BC2_v1' END,
    CASE WHEN split_part(flex.cell, '_', 3) <> split_part(rad.cell, '_', 3)
      THEN 'BC1_v1' END
  ) AS difference_pattern
FROM flex_cohort AS flex
JOIN rad_cohort AS rad USING (read_id)
WHERE flex.read_id IN (
  SELECT read_id
  FROM classified
  WHERE rad_fate = 'RAD_assigned_only_off_568'
);

CREATE OR REPLACE TEMP TABLE rad_off_best_pair AS
SELECT *
FROM rad_off_pair_candidates
QUALIFY row_number() OVER (
  PARTITION BY read_id
  ORDER BY
    differing_components,
    difference_pattern,
    flex_published_cell,
    rad_off_568_cell
) = 1;

COPY (
  SELECT
    differing_components,
    difference_pattern,
    flex_primer_type,
    rad_primer_type,
    count(*) AS source_reads
  FROM rad_off_best_pair
  GROUP BY
    differing_components,
    difference_pattern,
    flex_primer_type,
    rad_primer_type
  ORDER BY
    differing_components,
    difference_pattern,
    flex_primer_type,
    rad_primer_type
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/flex_only_rad_off_568_destinations.tsv'
(HEADER, DELIMITER '\t');

COPY (
  WITH stats AS (
    SELECT
      (SELECT count(*) FROM cohort) AS flex_published_rad_not_published,
      (SELECT count(*) FROM flex_chimeric_ids) AS all_flex_chimeric_source_reads,
      (
        SELECT count(*)
        FROM (
          SELECT read_id
          FROM flex
          GROUP BY read_id
          HAVING count(DISTINCT (cell, umi)) > 1
        )
      ) AS all_flex_multimatch_source_reads,
      (
        SELECT count(*)
        FROM classified
        WHERE flex_chimeric
      ) AS cohort_flex_chimeric_source_reads,
      (
        SELECT count(*)
        FROM classified
        WHERE flex_published_cell_umis > 1
      ) AS cohort_flex_multimatch_source_reads,
      (
        SELECT count(*)
        FROM classified
        WHERE rad_fate = 'RAD_assigned_published_definition_check'
      ) AS cohort_rad_published_definition_check
  )
  SELECT * FROM stats
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/flex_only_validation.tsv'
(HEADER, DELIMITER '\t');

COPY (
  WITH
  flex_molecules AS (
    SELECT DISTINCT 'all' AS umi_scope, cell, umi
    FROM flex_published
    UNION ALL
    SELECT DISTINCT 'full_10nt' AS umi_scope, cell, umi
    FROM flex_published
    WHERE length(umi) = 10
  ),
  rad_molecules AS (
    SELECT DISTINCT 'all' AS umi_scope, cell, umi
    FROM rad_published
    UNION ALL
    SELECT DISTINCT 'full_10nt' AS umi_scope, cell, umi
    FROM rad_published
    WHERE length(umi) = 10
  ),
  joined AS (
    SELECT
      coalesce(flex.umi_scope, rad.umi_scope) AS umi_scope,
      coalesce(flex.cell, rad.cell) AS cell,
      coalesce(flex.umi, rad.umi) AS umi,
      flex.cell IS NOT NULL AS in_flex,
      rad.cell IS NOT NULL AS in_rad
    FROM flex_molecules AS flex
    FULL OUTER JOIN rad_molecules AS rad USING (umi_scope, cell, umi)
  )
  SELECT
    umi_scope,
    CASE
      WHEN in_flex AND in_rad THEN 'shared'
      WHEN in_flex THEN 'Flexiplex_only'
      WHEN in_rad THEN 'RAD_only'
    END AS molecule_set,
    count(*) AS distinct_published_cell_umis
  FROM joined
  GROUP BY umi_scope, molecule_set
  ORDER BY umi_scope, molecule_set
) TO '/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/published_cell_umi_set_overlap.tsv'
(HEADER, DELIMITER '\t');
