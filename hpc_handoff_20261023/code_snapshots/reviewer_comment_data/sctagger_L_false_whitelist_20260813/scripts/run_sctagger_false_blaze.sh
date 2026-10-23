#!/usr/bin/env bash
set -Eeuo pipefail

REP=${1:?replicate number 1..3}
AFFINITY=${2:?taskset CPU list}
BASE=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data
OUT="$BASE/sctagger_L_false_whitelist_20260813/runs/blaze/rep${REP}"
INPUT="$BASE/wl_scan/20260731_sctagger_badread_quality_full/inputs/L/flatQ20.fq.gz"
TARGET="$BASE/sctagger_L_false_whitelist_20260813/whitelists/false_rep${REP}.txt"
BLAZE=/scratch/f005f43/blaze2_260a0_native_20260727/venv/bin/blaze
PY=/scratch/f005f43/blaze2_260a0_native_20260727/venv/bin/python
THREADS=32
mkdir -p "$OUT"
cd "$OUT"
date -u +%FT%TZ > started_utc.txt
printf 'replicate=%s\naffinity=%s\nthreads=%s\n' "$REP" "$AFFINITY" "$THREADS" > run_metadata.tsv
printf 'input\t%s\ninput_sha256\t6f7385468b607cf86c91449b095c2968ee2a5d25ab473901102b87d141543090\ninput_reads\t4993805\n' "$INPUT" >> run_metadata.tsv
printf 'target_whitelist\t%s\ntarget_sha256\t%s\ntarget_rows\t%s\n' "$TARGET" "$(sha256sum "$TARGET" | awk '{print $1}')" "$(wc -l < "$TARGET")" >> run_metadata.tsv
printf 'blaze_binary\t%s\nblaze_sha256\t%s\npython\t%s\npython_sha256\t%s\n' "$BLAZE" "$(sha256sum "$BLAZE" | awk '{print $1}')" "$PY" "$(sha256sum "$PY" | awk '{print $1}')" >> run_metadata.tsv
printf 'blaze_version\t2.6.0a0\ndistribution\tblaze2\nupstream_commit\taf8d2cc9f6374caf4d1006d5f8a0e99097211646\n' >> run_metadata.tsv
printf 'settings\t10x3v3; minQ=15; max_edit_distance=2; demultiplexing=enabled; whitelisting=disabled; no_empty_drops\n' >> run_metadata.tsv
cp -p "$TARGET" known_bc_list_used.txt
cmp -s "$TARGET" known_bc_list_used.txt
CMD=(taskset -c "$AFFINITY" /usr/bin/time -v -o blaze.time.txt "$BLAZE" --no-whitelisting --known-bc-list "$TARGET" --10x-kit-version 3v3 --minQ 15 --max-edit-distance 2 --no-emtpy-drops --threads "$THREADS" --output-prefix "$OUT/" --output-fastq matched_reads.fastq.gz --overwrite "$INPUT")
{ printf 'command\t'; printf '%q ' "${CMD[@]}"; printf '\n'; } >> run_metadata.tsv
date -u +%FT%TZ > command_start_utc.txt
set +e
"${CMD[@]}" > blaze.stdout.log 2> blaze.stderr.log
RC=$?
set -e
printf '%s\n' "$RC" > blaze_exit_code.txt
date -u +%FT%TZ > command_end_utc.txt
printf 'exit_status\t%s\n' "$RC" >> run_metadata.tsv
if [[ "$RC" -eq 0 ]]; then touch BLAZE_EXIT0; else touch BLAZE_FAILED; fi
exit "$RC"
