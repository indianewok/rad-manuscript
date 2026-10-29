#!/usr/bin/env bash
set -euo pipefail

sample="${1:?usage: run_sample.sh p7|p8}"
root=external_data/reviewer_comment_data/scratch_preservation_20260921/files/measles_p7_p8_four_tool_20260730
threads=24
blaze=external_data/reviewer_comment_data/scratch_preservation_20260921/files/blaze2_260a0_native_20260727/venv/bin/blaze

case "$sample" in
    p7)
        input="$root/input_links/p7_SRR28349077.fastq.gz"
        expected=964
        ;;
    p8)
        input="$root/input_links/p8_vdj_SRR28349076.fastq.gz"
        expected=10299
        ;;
    *)
        echo "Unknown sample: $sample" >&2
        exit 2
        ;;
esac

sample_root="$root/runs/$sample"
status_file="$sample_root/status.log"
mkdir -p "$sample_root/blaze"

status() {
    printf '%s\t%s\n' "$(date -Is)" "$*" >> "$status_file"
}

status "START sample=$sample expected_cells=$expected input=$input"

if [[ ! -f "$sample_root/blaze/DONE" ]]; then
    status "BLAZE 2.6.0a0 selection+demux started threads=$threads"
    PYTHONHASHSEED=0 /usr/bin/time -v -o "$sample_root/blaze/time.txt" \
        "$blaze" \
        --expect-cells "$expected" \
        --10x-kit-version 3v3 \
        --threads "$threads" \
        --max-edit-distance 2 \
        --output-prefix "$sample_root/blaze/" \
        --output-fastq matched_reads.fastq.gz \
        --minimal_stdout \
        --overwrite \
        "$input" \
        > "$sample_root/blaze/stdout.log" \
        2> "$sample_root/blaze/stderr.log"
    touch "$sample_root/blaze/DONE"
    status "BLAZE completed"
fi
