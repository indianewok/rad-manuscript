#!/usr/bin/env bash
set -Eeuo pipefail

WORK=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811
FASTQ=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/rageseq.fq.gz
SEL=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/wl_scan/20260730_rageseq_ERR3268991_cellline_control/runs/flexiplex/f8_detection/selected.tsv
FLEXIPLEX=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/pkgs/flexiplex-1.02.5-py39h2de1943_0/bin/flexiplex
MINIMAP2=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/pkgs/minimap2-2.26-he4a0461_1/bin/minimap2
LIBSTDCPP=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/pkgs/libstdcxx-ng-13.2.0-hc0a3c3a_7/lib
CONDA_LIB=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/lib
PYTHON=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/bin/python3
FLEX_THREADS=56
MM2_THREADS=20

cd "$WORK"

# Refuse to duplicate a completed or running equivalent run.
for f in rage_flex_f8_full_reads_barcodes.txt rage_bcrtcr_hits.tsv \
         flexiplex_bcrtcr_summary.tsv flexiplex_bcrtcr_data11_shape.tsv \
         flexiplex_per_barcode_bcrtcr.tsv .flexiplex_bcrtcr_running; do
    if [[ -e "$f" ]]; then
        echo "refusing to overwrite existing $WORK/$f" >&2
        exit 70
    fi
done

touch .flexiplex_bcrtcr_running
started_epoch=$(date +%s)
started_iso=$(date --iso-8601=seconds)
printf '%s\n' "$started_iso" > .flexiplex_bcrtcr_started
flex_status_file=.flexiplex_bcrtcr_flexiplex_exit
pipeline_status_file=.flexiplex_bcrtcr_pipeline_exit
rm -f "$flex_status_file" "$pipeline_status_file"

export LD_LIBRARY_PATH="$LIBSTDCPP:$CONDA_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

pipeline_rc=0
set +e
gzip -cd "$FASTQ" \
  | tee >( {
      "$FLEXIPLEX" -d 10x3v2 -f 8 -p "$FLEX_THREADS" -k "$SEL" -n rage_flex_f8_full \
        > /dev/null 2> flex_full.log
      flex_rc=$?
      printf '%s\n' "$flex_rc" > "$flex_status_file"
      exit "$flex_rc"
    } ) \
  | "$MINIMAP2" -x map-ont --secondary=no -t "$MM2_THREADS" hg38_bcrtcr.fa - 2> mm2_full.log \
  | awk -F'\t' '{print $1"\t"$6"\t"$10}' > rage_bcrtcr_hits.tsv
pipeline_rc=$?
set -e

# Process substitution is asynchronous with respect to pipe status. Wait for
# and explicitly capture Flexiplex's exit status so pipefail covers both arms.
for _ in $(seq 1 600); do
    [[ -s "$flex_status_file" ]] && break
    sleep 1
done
if [[ -s "$flex_status_file" ]]; then
    flex_rc=$(<"$flex_status_file")
else
    flex_rc=124
fi
printf '%s\n' "$pipeline_rc" > "$pipeline_status_file"
finished_epoch=$(date +%s)
finished_iso=$(date --iso-8601=seconds)
printf '%s\n' "$finished_iso" > .flexiplex_bcrtcr_finished
printf 'pipeline_rc=%s\nflexiplex_rc=%s\nstarted_epoch=%s\nfinished_epoch=%s\n' \
    "$pipeline_rc" "$flex_rc" "$started_epoch" "$finished_epoch" > .flexiplex_bcrtcr_status
rm -f .flexiplex_bcrtcr_running

if [[ "$pipeline_rc" -ne 0 || "$flex_rc" -ne 0 ]]; then
    exit 1
fi

"$PYTHON" join_flexiplex_bcrtcr.py | tee join_flexiplex_bcrtcr.stdout
