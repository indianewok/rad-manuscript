#!/usr/bin/env bash
set -euo pipefail

sample="${1:?usage: run_sample.sh p7|p8}"
root=external_data/reviewer_comment_data/scratch_preservation_20260921/files/measles_p7_p8_four_tool_20260730
threads=24
flex_threads=16
adapter=CTACACGACGCTCTTCCGATCT
design="$root/input_links/10x_3v3_full_whitelist.txt"
rad=external_data/reviewer_comment_data/scratch_preservation_20260921/files/longbench_full_demux_20260730/tools/rad_920adda_edlibfix/build_release/rad
blaze=external_data/reviewer_comment_data/scratch_preservation_20260921/files/blaze2_260a0_native_20260727/venv/bin/blaze
flex="$root/tools/flexiplex-v1.02.6/flexiplex-linux"
flex_audit="$root/tools/flexiplex-v1.02.6/flexiplex-audit"
flex_filter=external_data/software/miniconda3/bin/flexiplex-filter
container=external_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/tools/bioconductor_3.23_r4.6.1.sif
r_lib=external_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/tools/Rlib_bioc_3.23
basilisk_root=external_data/temporary/flamesv2_expect2500.2jtbob

case "$sample" in
    p7)
        input="$root/input_links/p7_SRR28349077.fastq.gz"
        truth="$root/input_links/p7_shortread_cells.txt"
        rad_calls="$root/input_links/p7_rad_scanwl.txt"
        expected=964
        ;;
    p8)
        input="$root/input_links/p8_vdj_SRR28349076.fastq.gz"
        truth="$root/input_links/p8_shortread_cells.txt"
        rad_calls="$root/input_links/p8_rad_scanwl.txt"
        expected=10299
        ;;
    *)
        echo "Unknown sample: $sample" >&2
        exit 2
        ;;
esac

sample_root="$root/runs/$sample"
status_file="$sample_root/status.log"
mkdir -p \
    "$sample_root/rad/demux" \
    "$sample_root/blaze" \
    "$sample_root/flexiplex/detection" \
    "$sample_root/flexiplex/demux" \
    "$sample_root/flexiplex/audit" \
    "$sample_root/flamesv2" \
    "$root/analysis/$sample"

status() {
    printf '%s\t%s\n' "$(date -Is)" "$*" >> "$status_file"
}

status "START sample=$sample expected_cells=$expected input=$input"
ln -sf "$rad_calls" "$sample_root/rad/scanwl.txt"

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

flex_prefix="$sample_root/flexiplex/detection/$sample"
if [[ ! -f "$sample_root/flexiplex/detection/DONE" ]]; then
    status "Flexiplex 1.02.6 f8 discovery started threads=$flex_threads"
    /usr/bin/time -v -o "$sample_root/flexiplex/detection/time.txt" \
        bash -o pipefail -c \
        'gzip -cd "$1" | "$2" -d 10x3v3 -e 2 -f 8 -p "$3" -n "$4" > /dev/null' \
        bash "$input" "$flex" "$flex_threads" "$flex_prefix" \
        > "$sample_root/flexiplex/detection/stdout.log" \
        2> "$sample_root/flexiplex/detection/stderr.log"
    LD_LIBRARY_PATH=external_data/software/miniconda3/lib \
        /usr/bin/time -v -o "$sample_root/flexiplex/detection/filter.time.txt" \
        "$flex_filter" \
        --whitelist "$design" \
        --outfile "$sample_root/flexiplex/detection/selected.tsv" \
        "${flex_prefix}_barcodes_counts.txt" \
        > "$sample_root/flexiplex/detection/filter.stdout.log" \
        2> "$sample_root/flexiplex/detection/filter.stderr.log"
    touch "$sample_root/flexiplex/detection/DONE"
    status "Flexiplex f8 discovery+filter completed"
fi

if [[ ! -f "$sample_root/rad/demux/DONE" ]]; then
    status "RAD demux started threads=$threads"
    /usr/bin/time -v -o "$sample_root/rad/demux/time.txt" \
        "$rad" demux \
        -l three_prime \
        -q "$input" \
        -g "$design" \
        -c "$rad_calls" \
        -R offensive \
        -M 2 \
        -m 2 \
        -z 5000 \
        -o "$sample" \
        -d "$sample_root/rad/demux" \
        -F "$sample_root/rad/demux/run.log" \
        -t "$threads" \
        > "$sample_root/rad/demux/stdout.log" \
        2> "$sample_root/rad/demux/stderr.log"
    touch "$sample_root/rad/demux/DONE"
    status "RAD demux completed"
fi

if [[ ! -f "$sample_root/flexiplex/demux/DONE" ]]; then
    status "Flexiplex f8 demux started threads=$flex_threads"
    /usr/bin/time -v -o "$sample_root/flexiplex/demux/time.txt" \
        bash -o pipefail -c \
        'gzip -cd "$1" | "$2" -d 10x3v3 -e 2 -f 8 -p "$3" -k "$4" -n "$5" | pigz -p 4 > "$6"' \
        bash \
        "$input" \
        "$flex" \
        "$flex_threads" \
        "$sample_root/flexiplex/detection/selected.tsv" \
        "$sample_root/flexiplex/demux/$sample" \
        "$sample_root/flexiplex/demux/matched_reads.fastq.gz" \
        > "$sample_root/flexiplex/demux/stdout.log" \
        2> "$sample_root/flexiplex/demux/stderr.log"
    touch "$sample_root/flexiplex/demux/DONE"
    status "Flexiplex f8 demux completed"
fi

if [[ ! -f "$sample_root/flamesv2/DONE" ]]; then
    temp_root=$(mktemp -d "external_data/temporary/measles_${sample}_flames.XXXXXX")
    mkdir -p "$temp_root/tmp" "$temp_root/xdg-data" "$temp_root/xdg-cache"
    status "FLAMES 2.6.0 embedded BLAZE 2.5.1 started threads=$threads temp=$temp_root"
    /usr/bin/time -v -o "$sample_root/flamesv2/time.txt" \
        apptainer exec --cleanenv \
        --bind /dartfs:/dartfs \
        --bind /dartfs-hpc:/dartfs-hpc \
        --bind /scratch:/scratch \
        --bind "$basilisk_root:$basilisk_root" \
        --bind "$temp_root:$temp_root" \
        --env R_ENVIRON_USER=/dev/null \
        --env R_PROFILE_USER=/dev/null \
        --env R_LIBS_USER="$r_lib" \
        --env TMPDIR="$temp_root/tmp" \
        --env BASILISK_EXTERNAL_DIR="$basilisk_root/basilisk" \
        --env XDG_DATA_HOME="$temp_root/xdg-data" \
        --env XDG_CACHE_HOME="$temp_root/xdg-cache" \
        --env PYENV_ROOT="$temp_root/xdg-data/r-reticulate/pyenv" \
        --env OMP_DYNAMIC=FALSE \
        --env OMP_MAX_ACTIVE_LEVELS=1 \
        --env OMP_NUM_THREADS="$threads" \
        --env OMP_PROC_BIND=FALSE \
        --env OMP_PLACES=cores \
        "$container" \
        Rscript "$root/scripts/run_flamesv2_blaze_10x.R" \
        "$input" "$sample_root/flamesv2" "$threads" "$expected" 3v3 \
        > "$sample_root/flamesv2/stdout.log" \
        2> "$sample_root/flamesv2/stderr.log"
    touch "$sample_root/flamesv2/DONE"
    status "FLAMESv2 completed"
fi

status "callset scoring started"
python3 "$root/scripts/score_callsets.py" \
    --sample "$sample" \
    --truth "$truth" \
    --output "$root/analysis/$sample/callset_metrics.tsv" \
    --callset RAD "$rad_calls" \
    --callset BLAZE "$sample_root/blaze/whitelist.csv" \
    --callset Flexiplex_f8 "$sample_root/flexiplex/detection/selected.tsv" \
    --callset FLAMESv2 "$sample_root/flamesv2/whitelist.csv"

status "RAD correction-flow audit started"
python3 "$root/scripts/audit_rad_flows.py" \
    --fastq "$sample_root/rad/demux/$sample.fq.gz" \
    --truth "$truth" \
    --design "$design" \
    --selected "$rad_calls" \
    --output-dir "$root/analysis/$sample/rad_flow"

status "BLAZE correction-flow audit started"
python3 "$root/scripts/audit_blaze_flows.py" \
    --method BLAZE \
    --matched-fastq "$sample_root/blaze/matched_reads.fastq.gz" \
    --putative-csv "$sample_root/blaze/putative_bc.csv" \
    --truth "$truth" \
    --design "$design" \
    --selected "$sample_root/blaze/whitelist.csv" \
    --output-dir "$root/analysis/$sample/blaze_flow"

status "FLAMES correction-flow audit started"
python3 "$root/scripts/audit_blaze_flows.py" \
    --method FLAMESv2 \
    --matched-fastq "$sample_root/flamesv2/matched_reads.fastq.gz" \
    --putative-csv "$sample_root/flamesv2/putative_bc.csv" \
    --truth "$truth" \
    --design "$design" \
    --selected "$sample_root/flamesv2/whitelist.csv" \
    --output-dir "$root/analysis/$sample/flamesv2_flow"

if [[ ! -f "$sample_root/flexiplex/audit/DONE" ]]; then
    audit_prefix="$sample_root/flexiplex/audit/$sample"
    fifo="${audit_prefix}_reads_barcodes.txt"
    if [[ -e "$fifo" ]]; then
        echo "Refusing stale Flexiplex audit FIFO: $fifo" >&2
        exit 1
    fi
    mkfifo "$fifo"
    cleanup_fifo() {
        exec 9>&- 2>/dev/null || true
        rm -f "$fifo"
    }
    trap cleanup_fifo EXIT
    status "Flexiplex native raw-to-target audit started"
    python3 "$root/scripts/audit_flexiplex_stream.py" \
        --assignments "$fifo" \
        --truth "$truth" \
        --design "$design" \
        --selected "$sample_root/flexiplex/detection/selected.tsv" \
        --output-dir "$root/analysis/$sample/flexiplex_flow" \
        > "$sample_root/flexiplex/audit/counter.stdout.log" \
        2> "$sample_root/flexiplex/audit/counter.stderr.log" &
    counter_pid=$!
    exec 9>"$fifo"
    /usr/bin/time -v -o "$sample_root/flexiplex/audit/time.txt" \
        bash -o pipefail -c \
        'gzip -cd "$1" | "$2" -d 10x3v3 -e 2 -f 8 -p "$3" -k "$4" -n "$5" > /dev/null' \
        bash \
        "$input" \
        "$flex_audit" \
        "$flex_threads" \
        "$sample_root/flexiplex/detection/selected.tsv" \
        "$audit_prefix" \
        > "$sample_root/flexiplex/audit/stdout.log" \
        2> "$sample_root/flexiplex/audit/stderr.log"
    exec 9>&-
    wait "$counter_pid"
    rm -f "$fifo"
    trap - EXIT
    touch "$sample_root/flexiplex/audit/DONE"
    status "Flexiplex native raw-to-target audit completed"
fi

touch "$sample_root/SAMPLE_DONE"
status "DONE sample=$sample"
