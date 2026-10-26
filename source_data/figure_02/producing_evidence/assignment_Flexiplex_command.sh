#!/usr/bin/env bash
set -u
set -o pipefail

ARM=${1:?arm must be S, L, or RAGE}
W=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/sctagger_flexiplex_audit_20260812
BIN=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/software_pins_20260810/flexiplex_raw_to_assigned_audit/bin/flexiplex_v1.02.6_raw_to_assigned_audit
PKG=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/wl_scan/20260731_sctagger_badread_quality_full
W2=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811
RPKG=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/wl_scan/20260730_rageseq_ERR3268991_cellline_control

case "$ARM" in
  S|L)
    DS=$ARM
    cd "$W" || exit 2
    INPUT="$PKG/inputs/$DS/flatQ20.fq.gz"
    KNOWN="$PKG/runs/flexiplex/$DS/flatQ20/output/${DS}_flatQ20_barcodes_final.txt"
    PREFIX="${DS}_flatQ20_audit"
    SIDECAR="$W/${PREFIX}_reads_barcodes.txt"
    TIMEFILE="$W/${DS}_audit.time.txt"
    RUNNER_LOG="$W/${DS}_audit.runner.log"
    COMPLETE="$W/${DS}_audit.COMPLETE"
    COMMAND="pigz -dc -p 4 $INPUT | /usr/bin/time -v $BIN -d 10x3v3 -p 16 -k $KNOWN -n $PREFIX > /dev/null 2> $TIMEFILE"
    ;;
  RAGE)
    cd "$W2" || exit 2
    INPUT=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/rageseq.fq.gz
    KNOWN="$RPKG/runs/flexiplex/f8_detection/selected.tsv"
    PREFIX=rage_flex_f8_audit
    SIDECAR="$W2/${PREFIX}_reads_barcodes.txt"
    TIMEFILE="$W2/rage_audit.time.txt"
    RUNNER_LOG="$W2/rage_audit.runner.log"
    COMPLETE="$W2/rage_audit.COMPLETE"
    COMMAND="pigz -dc -p 4 $INPUT | /usr/bin/time -v $BIN -d 10x3v2 -f 8 -p 16 -k $KNOWN -n $PREFIX > /dev/null 2> $TIMEFILE"
    ;;
  *) echo "unknown arm: $ARM" >&2; exit 2 ;;
esac

if [[ -e "$SIDECAR" || -e "$COMPLETE" ]]; then
  echo "Refusing to overwrite existing audit output: $SIDECAR or $COMPLETE" >&2
  exit 3
fi
for p in "$INPUT" "$KNOWN" "$BIN"; do
  [[ -r "$p" ]] || { echo "Missing/unreadable input: $p" >&2; exit 4; }
done

start_epoch=$(date +%s)
start_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf 'arm=%s\nstart_utc=%s\nhost=%s\npid=%s\naffinity=%s\ncommand=%s\n' "$ARM" "$start_utc" "$(hostname)" "$$" "$(taskset -pc $$ 2>/dev/null | sed 's/^.*: //')" "$COMMAND" > "$RUNNER_LOG"

set +e
pigz -dc -p 4 "$INPUT" | /usr/bin/time -v "$BIN" \
  $(if [[ "$ARM" == RAGE ]]; then printf '%s' '-d 10x3v2 -f 8'; else printf '%s' '-d 10x3v3'; fi) \
  -p 16 -k "$KNOWN" -n "$PREFIX" > /dev/null 2>> "$TIMEFILE"
pipe_status=("${PIPESTATUS[@]}")
rc_pigz=${pipe_status[0]:-99}
rc_flex=${pipe_status[1]:-99}
set -e
end_epoch=$(date +%s)
end_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf 'end_utc=%s\nelapsed_sec=%s\npigz_exit=%s\nflexiplex_exit=%s\n' "$end_utc" "$((end_epoch-start_epoch))" "$rc_pigz" "$rc_flex" >> "$RUNNER_LOG"

if [[ "$rc_pigz" != 0 || "$rc_flex" != 0 ]]; then
  echo "pipeline failed (pigz=$rc_pigz flexiplex=$rc_flex); see $RUNNER_LOG and $TIMEFILE" >&2
  exit 10
fi
[[ -s "$SIDECAR" ]] || { echo "Missing/empty sidecar: $SIDECAR" >&2; exit 11; }

if [[ "$ARM" == S || "$ARM" == L ]]; then
  python3 "$W/join_audit_native.py" "$SIDECAR" "$W/$DS" >> "$RUNNER_LOG" 2>&1
  join_rc=$?
  printf 'join_exit=%s\n' "$join_rc" >> "$RUNNER_LOG"
  [[ "$join_rc" == 0 ]] || exit 12
fi

printf 'arm=%s\ncompleted_utc=%s\nsidecar=%s\n' "$ARM" "$end_utc" "$SIDECAR" > "$COMPLETE"
echo "completed: $ARM sidecar=$SIDECAR"
