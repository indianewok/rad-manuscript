#!/usr/bin/env bash
set -Eeuo pipefail

REP=${1:?replicate number 1..3}
AFFINITY=${2:?taskset CPU list}
BASE=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data
OUT="$BASE/sctagger_L_false_whitelist_20260813/runs/flexiplex/rep${REP}"
INPUT="$BASE/wl_scan/20260731_sctagger_badread_quality_full/inputs/L/flatQ20.fq.gz"
TARGET="$BASE/sctagger_L_false_whitelist_20260813/whitelists/false_rep${REP}.txt"
BINARY="$BASE/software_pins_20260810/flexiplex_raw_to_assigned_audit/bin/flexiplex_v1.02.6_raw_to_assigned_audit"
PREFIX="$OUT/flexiplex_L_flatQ20_false_rep${REP}_audit"
ASSIGNED="${PREFIX}.fastq.gz"
SIDECAR="${PREFIX}_reads_barcodes.txt"
STDERR_LOG="$OUT/flexiplex.stderr.log"
mkdir -p "$OUT"
cd "$OUT"
date -u +%FT%TZ > started_utc.txt
printf 'replicate=%s\naffinity=%s\nflexiplex_threads=28\npigz_decompress_threads=4\npigz_compress_threads=4\n' "$REP" "$AFFINITY" > run_metadata.tsv
printf 'input\t%s\ninput_sha256\t6f7385468b607cf86c91449b095c2968ee2a5d25ab473901102b87d141543090\ninput_reads\t4993805\n' "$INPUT" >> run_metadata.tsv
printf 'target_whitelist\t%s\ntarget_sha256\t%s\ntarget_rows\t%s\n' "$TARGET" "$(sha256sum "$TARGET" | awk '{print $1}')" "$(wc -l < "$TARGET")" >> run_metadata.tsv
printf 'binary\t%s\nbinary_sha256\t%s\nbinary_version\t1.02.6\nupstream_commit\td84c8ae4f3865052f2b5ecec816949b94682f302\n' "$BINARY" "$(sha256sum "$BINARY" | awk '{print $1}')" >> run_metadata.tsv
printf 'settings\t10x3v3; flank_edit_distance=8; barcode_edit_distance=2; forced_known_list=true; raw_to_assigned_audit=true\n' >> run_metadata.tsv
cp -p "$TARGET" supplied_whitelist_used.txt
cmp -s "$TARGET" supplied_whitelist_used.txt
CMD=(taskset -c "$AFFINITY" /usr/bin/time -v -o flexiplex.time.txt bash -o pipefail -c 'pigz -dc -p 4 "$1" | "$2" -d 10x3v3 -k "$3" -f 8 -e 2 -p 28 -n "$4" 2>"$5" | pigz -p 4 > "$6"' _ "$INPUT" "$BINARY" "$TARGET" "$PREFIX" "$STDERR_LOG" "$ASSIGNED")
{ printf 'command\t'; printf '%q ' "${CMD[@]}"; printf '\n'; } >> run_metadata.tsv
date -u +%FT%TZ > command_start_utc.txt
set +e
"${CMD[@]}" > flexiplex.stdout.log 2> flexiplex.pipeline.stderr.log
RC=$?
set -e
printf '%s\n' "$RC" > flexiplex_exit_code.txt
date -u +%FT%TZ > command_end_utc.txt
printf 'exit_status\t%s\nassigned_output\t%s\nsidecar_output\t%s\n' "$RC" "$ASSIGNED" "$SIDECAR" >> run_metadata.tsv
if [[ "$RC" -eq 0 ]]; then touch FLEXIPLEX_AUDIT_EXIT0; else touch FLEXIPLEX_AUDIT_FAILED; fi
exit "$RC"
