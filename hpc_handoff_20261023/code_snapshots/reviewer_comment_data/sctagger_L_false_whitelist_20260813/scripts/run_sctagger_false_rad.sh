#!/usr/bin/env bash
set -Eeuo pipefail

REP=${1:?replicate number 1..3}
AFFINITY=${2:?taskset CPU list}
BASE=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data
OUT="$BASE/sctagger_L_false_whitelist_20260813/runs/rad/rep${REP}"
INPUT="$BASE/wl_scan/20260731_sctagger_badread_quality_full/inputs/L/flatQ20.fq.gz"
GLOBAL="$BASE/sctagger_L_false_whitelist_20260813/provenance/global_chemistry_10x3v3_bitlist.csv.gz"
TARGET="$BASE/sctagger_L_false_whitelist_20260813/whitelists/false_rep${REP}.txt"
RAD=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/rad/build/rad
LAYOUT="$BASE/sctagger_L_fixed5000_three_tool_20260812/rad/three_prime_10x3v3_umi12_layout.csv"
THREADS=32
PREFIX="L_flatQ20_false_rep${REP}_rad"
mkdir -p "$OUT"
cd "$OUT"
date -u +%FT%TZ > started_utc.txt
printf 'replicate=%s\naffinity=%s\nthreads=%s\n' "$REP" "$AFFINITY" "$THREADS" > run_metadata.tsv
printf 'input\t%s\ninput_sha256\t6f7385468b607cf86c91449b095c2968ee2a5d25ab473901102b87d141543090\n' "$INPUT" >> run_metadata.tsv
printf 'global_whitelist\t%s\nglobal_sha256\t%s\n' "$GLOBAL" "$(sha256sum "$GLOBAL" | awk '{print $1}')" >> run_metadata.tsv
printf 'target_whitelist\t%s\ntarget_sha256\t%s\ntarget_rows\t%s\n' "$TARGET" "$(sha256sum "$TARGET" | awk '{print $1}')" "$(wc -l < "$TARGET")" >> run_metadata.tsv
printf 'rad_binary\t%s\nrad_sha256\t%s\nrad_version\t%s\n' "$RAD" "$(sha256sum "$RAD" | awk '{print $1}')" "$("$RAD" --version 2>&1 | head -1)" >> run_metadata.tsv
printf 'git_commit\tcd0582b2440cde0f35725dc557fa47307d74d374\nlayout\t%s\n' "$LAYOUT" >> run_metadata.tsv
printf 'layout_sha256\t%s\n' "$(sha256sum "$LAYOUT" | awk '{print $1}')" >> run_metadata.tsv
printf 'settings\t10x3v3; bc_correction=offensive; ED=2; whitelist_mutation=2; generated_mutation=2; chunk=5000; umi_rc=default\n' >> run_metadata.tsv
cp -p "$TARGET" supplied_whitelist_used.txt
cmp -s "$TARGET" supplied_whitelist_used.txt
CMD=(taskset -c "$AFFINITY" /usr/bin/time -v -o time.verbose.txt -- "$RAD" demux -l "$LAYOUT" -q "$INPUT" -g "$GLOBAL" -c "$TARGET" -R offensive -M 2 -m 2 -z 5000 -o "$PREFIX" -d "$OUT" -F "$OUT/${PREFIX}.log" -t "$THREADS" -v)
{ printf 'command\t'; printf '%q ' "${CMD[@]}"; printf '\n'; } >> run_metadata.tsv
date -u +%FT%TZ > command_start_utc.txt
set +e
"${CMD[@]}" > stdout.log 2> stderr.log
RC=$?
set -e
printf '%s\n' "$RC" > exit_status.txt
date -u +%FT%TZ > command_end_utc.txt
printf 'exit_status\t%s\n' "$RC" >> run_metadata.tsv
if [[ "$RC" -eq 0 ]]; then touch RAD_EXIT0; else touch RAD_FAILED; fi
exit "$RC"
