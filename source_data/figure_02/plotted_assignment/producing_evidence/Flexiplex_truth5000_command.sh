#!/usr/bin/env bash
# Portable path form of the recorded command; original byte hash is in source_manifest.json.
set -o pipefail

# Exact pinned pipeline command recorded from the completed run; this file is
# provenance only and is intentionally not executable as a second run.
/usr/bin/time -v -o external_data/reviewer_comment_data/sctagger_L_fixed5000_three_tool_20260812/flexiplex/flexiplex.time.txt \
  taskset -c 32-47,96-111 bash -o pipefail -c \
  'pigz -dc -p 4 "$1" | "$2" -d 10x3v3 -k "$3" -f 8 -e 2 -p 28 -n "$4" 2>"$5" | pigz -p 4 > "$6"' \
  _ \
  external_data/reviewer_comment_data/wl_scan/20260731_sctagger_badread_quality_full/inputs/L/flatQ20.fq.gz \
  external_data/reviewer_comment_data/software_pins_20260810/flexiplex_raw_to_assigned_audit/bin/flexiplex_v1.02.6_raw_to_assigned_audit \
  external_data/reviewer_comment_data/sctagger_L_fixed5000_three_tool_20260812/common/L_truth_5000_barcodes.txt \
  external_data/reviewer_comment_data/sctagger_L_fixed5000_three_tool_20260812/flexiplex/flexiplex_L_flatQ20_fixed5000_audit \
  external_data/reviewer_comment_data/sctagger_L_fixed5000_three_tool_20260812/flexiplex/flexiplex.stderr.log \
  external_data/reviewer_comment_data/sctagger_L_fixed5000_three_tool_20260812/flexiplex/flexiplex_L_flatQ20_fixed5000_audit.fastq.gz
