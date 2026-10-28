#!/usr/bin/env bash
set -euo pipefail

ROOT=external_data/reviewer_comment_data/scratch_preservation_20260921/files/rageseq_tnbc_ln_four_tool_20260730
SOURCE_PART=external_data/raw_fastq_datasets/rageseq_tnbc_draining_lymphnode_ERR3268990.fastq.gz.part
SOURCE_FINAL=external_data/raw_fastq_datasets/rageseq_tnbc_draining_lymphnode_ERR3268990.fastq.gz
SOURCE=$SOURCE_PART
INPUT="$ROOT/input/ERR3268990.fastq.gz"
EXPECTED_BYTES=24090380952
EXPECTED_MD5=23177cd143a521db1d7e41fd3e7d1981
EXPECTED_READS=23044761
EXPECTED_BASES=24041380990
RAD_THREADS=16
BLAZE_THREADS=16
FLEX_THREADS=10
FLEX_PIGZ_THREADS=2
FLAMES_THREADS=24
PROMETH_ROOT=external_data/reviewer_comment_data/scratch_preservation_20260921/files/promethion_four_tool_20260729
PROMETH_SELECTION_STATUS="$PROMETH_ROOT/logs/selection_queue.status.log"
PROMETH_SENSITIVITY_STATUS="$PROMETH_ROOT/logs/blaze_expect1022_sensitivity.status.log"

RAD=external_data/temporary/rad-current-f005f43.8ChwC9/build-system/rad
BLAZE=external_data/reviewer_comment_data/scratch_preservation_20260921/files/blaze2_260a0_native_20260727/venv/bin/blaze
FLEX=external_data/temporary/flexiplex_release.GqgaKA/flexiplex/bin/flexiplex-linux
FLEX_FILTER=external_data/software/miniconda3/bin/flexiplex-filter
FLEX_LIB=external_data/software/miniconda3/lib
SEQKIT=external_data/software/miniconda3/bin/seqkit
CONTAINER=external_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/tools/bioconductor_3.23_r4.6.1.sif
R_LIB=external_data/reviewer_comment_data/scratch_preservation_20260921/files/rad_longbench_20260726/tools/Rlib_bioc_3.23
BASILISK_ROOT=external_data/temporary/flamesv2_expect2500.2jtbob
STATUS="$ROOT/run_status.log"

status() {
    printf '%s\t%s\n' "$(date --iso-8601=seconds)" "$*" | tee -a "$STATUS"
}

mkdir -p \
    "$ROOT/analysis" \
    "$ROOT/runs/rad/scan" \
    "$ROOT/runs/rad/demux" \
    "$ROOT/runs/blaze" \
    "$ROOT/runs/blaze_expect6027" \
    "$ROOT/runs/flexiplex/f0_detection" \
    "$ROOT/runs/flexiplex/f0_demux" \
    "$ROOT/runs/flexiplex/f8_detection" \
    "$ROOT/runs/flexiplex/f8_demux" \
    "$ROOT/runs/flamesv2"

status "waiting for ERR3268990 download ($EXPECTED_BYTES bytes)"
while :; do
    if [[ -f "$SOURCE_FINAL" ]]; then
        SOURCE=$SOURCE_FINAL
    else
        SOURCE=$SOURCE_PART
    fi
    current_bytes=$(stat -c %s "$SOURCE" 2>/dev/null || printf 0)
    if (( current_bytes > EXPECTED_BYTES )); then
        status "ERROR source exceeded expected byte count: $current_bytes"
        exit 1
    fi
    if (( current_bytes == EXPECTED_BYTES )); then
        sleep 20
        stable_bytes=$(stat -c %s "$SOURCE")
        if (( stable_bytes == EXPECTED_BYTES )); then
            break
        fi
    fi
    sleep 30
done

status "download reached expected size; verifying official ENA MD5"
observed_md5=$(md5sum "$SOURCE" | awk '{print $1}')
if [[ "$observed_md5" != "$EXPECTED_MD5" ]]; then
    status "ERROR MD5 mismatch: expected=$EXPECTED_MD5 observed=$observed_md5"
    exit 1
fi

status "copying validated source to local NVMe scratch"
cp --reflink=auto "$SOURCE" "$INPUT"
input_bytes=$(stat -c %s "$INPUT")
if (( input_bytes != EXPECTED_BYTES )); then
    status "ERROR local input byte count mismatch: $input_bytes"
    exit 1
fi

status "validating local FASTQ read/base counts"
"$SEQKIT" stats -T "$INPUT" > "$ROOT/input/seqkit_stats.tsv"
observed_reads=$(awk 'NR==2 {print $4}' "$ROOT/input/seqkit_stats.tsv")
observed_bases=$(awk 'NR==2 {print $5}' "$ROOT/input/seqkit_stats.tsv")
if [[ "$observed_reads" != "$EXPECTED_READS" || "$observed_bases" != "$EXPECTED_BASES" ]]; then
    status "ERROR FASTQ stats mismatch: reads=$observed_reads bases=$observed_bases"
    exit 1
fi
if [[ "$SOURCE" == "$SOURCE_PART" ]]; then
    if [[ -e "$SOURCE_FINAL" ]]; then
        status "ERROR refusing to replace existing final source path: $SOURCE_FINAL"
        exit 1
    fi
    status "finalizing validated durable download from .part to .fastq.gz"
    mv "$SOURCE_PART" "$SOURCE_FINAL"
    SOURCE=$SOURCE_FINAL
fi
printf '%s  %s\n' "$EXPECTED_MD5" "$SOURCE" > "$ROOT/input/ERR3268990.official_md5"
status "input validation and durable finalization passed: $SOURCE"

status "waiting for PromethION heavy selection and expect1022 sensitivity to finish before LN wave 1"
while :; do
    selection_complete=false
    sensitivity_complete=false
    if [[ -s "$PROMETH_SELECTION_STATUS" ]] &&
       grep -q $'\tcomplete\tall-selection-tools' "$PROMETH_SELECTION_STATUS"; then
        selection_complete=true
    fi
    if [[ -s "$PROMETH_SENSITIVITY_STATUS" ]] &&
       grep -q $'\tcomplete\tblaze-2.6.0a0-expect1022-callset-only' "$PROMETH_SENSITIVITY_STATUS"; then
        sensitivity_complete=true
    fi
    if [[ "$selection_complete" == true && "$sensitivity_complete" == true ]]; then
        break
    fi
    status "PromethION gate: selection_complete=$selection_complete sensitivity_complete=$sensitivity_complete"
    sleep 60
done
status "PromethION selection gate passed; LN cap remains 56 so later PromethION competitor demux (max 64) keeps combined request <=120"

run_rad() {
    status "RAD scan-wl started"
    /usr/bin/time -v -o "$ROOT/runs/rad/scan/time.txt" \
        "$RAD" scan-wl \
        -i "$INPUT" \
        -o "$ROOT/runs/rad/scan/ERR3268990" \
        -p CTACACGACGCTCTTCCGATCT -n 16 -e 0.3 \
        -w "$ROOT/input/10x_3v2_full_whitelist.txt" \
        -t "$RAD_THREADS" -k 10000 \
        > "$ROOT/runs/rad/scan/stdout.log" \
        2> "$ROOT/runs/rad/scan/stderr.log" || return
    status "RAD demux started"
    /usr/bin/time -v -o "$ROOT/runs/rad/demux/time.txt" \
        "$RAD" demux \
        -l three_prime -q "$INPUT" \
        -g "$ROOT/input/10x_3v2_full_whitelist.txt" \
        -c "$ROOT/runs/rad/scan/ERR3268990.txt" \
        -R offensive -M 2 -m 2 -z 10000 \
        -o ERR3268990 -d "$ROOT/runs/rad/demux" \
        -F "$ROOT/runs/rad/demux/run.log" \
        -t "$RAD_THREADS" \
        > "$ROOT/runs/rad/demux/stdout.log" \
        2> "$ROOT/runs/rad/demux/stderr.log"
}

run_blaze() {
    local output_dir=$1
    local expect_cells=$2
    local label=$3
    local overwrite_mode=$4
    local overwrite_args=()
    if [[ "$overwrite_mode" == "overwrite" ]]; then
        overwrite_args+=(--overwrite)
    fi
    status "$label started"
    (
        cd "$output_dir" || exit
        /usr/bin/time -v -o time.txt \
            "$BLAZE" \
            --expect-cells "$expect_cells" \
            --10x-kit-version 3v2 \
            --threads "$BLAZE_THREADS" \
            --max-edit-distance 2 \
            --output-prefix ./ \
            --output-fastq matched_reads.fastq.gz \
            "${overwrite_args[@]}" "$INPUT" \
            > stdout.log 2> stderr.log
    )
}

run_flex() {
    local error_setting=$1
    local label="f${error_setting}"
    local detection="$ROOT/runs/flexiplex/${label}_detection"
    local demux="$ROOT/runs/flexiplex/${label}_demux"
    status "Flexiplex $label discovery started"
    /usr/bin/time -v -o "$detection/time.txt" \
        bash -o pipefail -c \
        "gzip -cd \"$INPUT\" | \"$FLEX\" -d 10x3v2 -f \"$error_setting\" -p \"$FLEX_THREADS\" -n \"$detection/ERR3268990\"" \
        > "$detection/stdout.log" 2> "$detection/stderr.log" || return
    status "Flexiplex $label filter started"
    LD_LIBRARY_PATH="$FLEX_LIB" \
        /usr/bin/time -v -o "$detection/filter_time.txt" \
        "$FLEX_FILTER" \
        --whitelist "$ROOT/input/10x_3v2_full_whitelist.txt" \
        --outfile "$detection/selected.tsv" \
        "$detection/ERR3268990_barcodes_counts.txt" \
        > "$detection/filter_stdout.log" \
        2> "$detection/filter_stderr.log" || return
    status "Flexiplex $label demux started"
    /usr/bin/time -v -o "$demux/time.txt" \
        bash -o pipefail -c \
        "gzip -cd \"$INPUT\" | \"$FLEX\" -d 10x3v2 -f \"$error_setting\" -p \"$FLEX_THREADS\" -k \"$detection/selected.tsv\" -n \"$demux/ERR3268990\" | pigz -p \"$FLEX_PIGZ_THREADS\" > \"$demux/matched_reads.fastq.gz\"" \
        > "$demux/stdout.log" 2> "$demux/stderr.log"
}

run_flames() {
    local temp_root
    temp_root=$(mktemp -d external_data/temporary/rageseq_ln_flames.XXXXXX) || return
    mkdir -p "$temp_root/tmp" "$temp_root/xdg-data" "$temp_root/xdg-cache"
    status "FLAMESv2/BLAZE 2.5.1 expect10433 started (temp=$temp_root)"
    /usr/bin/time -v -o "$ROOT/runs/flamesv2/time.txt" \
        apptainer exec --cleanenv \
        --bind /dartfs:/dartfs \
        --bind /dartfs-hpc:/dartfs-hpc \
        --bind /scratch:/scratch \
        --bind "$BASILISK_ROOT:$BASILISK_ROOT" \
        --bind "$temp_root:$temp_root" \
        --env R_ENVIRON_USER=/dev/null \
        --env R_PROFILE_USER=/dev/null \
        --env R_LIBS_USER="$R_LIB" \
        --env TMPDIR="$temp_root/tmp" \
        --env BASILISK_EXTERNAL_DIR="$BASILISK_ROOT/basilisk" \
        --env XDG_DATA_HOME="$temp_root/xdg-data" \
        --env XDG_CACHE_HOME="$temp_root/xdg-cache" \
        --env PYENV_ROOT="$temp_root/xdg-data/r-reticulate/pyenv" \
        --env OMP_DYNAMIC=FALSE \
        --env OMP_MAX_ACTIVE_LEVELS=1 \
        --env OMP_NUM_THREADS="$FLAMES_THREADS" \
        --env OMP_PROC_BIND=FALSE \
        --env OMP_PLACES=cores \
        "$CONTAINER" \
        Rscript "$ROOT/scripts/run_flamesv2_blaze_10x.R" \
        "$INPUT" "$ROOT/runs/flamesv2" "$FLAMES_THREADS" 10433 3v2 \
        > "$ROOT/runs/flamesv2/stdout.log" \
        2> "$ROOT/runs/flamesv2/stderr.log"
}

status "wave 1 launch: RAD16 + BLAZE16 + Flex10 + Flex10; max requested workers 52, or 56 while both Flex pigz2 stages overlap"
run_rad & pid_rad=$!
run_blaze "$ROOT/runs/blaze" 10433 "BLAZE 2.6.0a0 expect10433" overwrite & pid_blaze=$!
run_flex 0 & pid_flex0=$!
run_flex 8 & pid_flex8=$!

failures=0
for pair in \
    "RAD:$pid_rad" \
    "BLAZE10433:$pid_blaze" \
    "Flexiplex_f0:$pid_flex0" \
    "Flexiplex_f8:$pid_flex8"
do
    label=${pair%%:*}
    pid=${pair##*:}
    if wait "$pid"; then
        status "$label completed"
    else
        status "ERROR $label failed"
        failures=$((failures + 1))
    fi
done
if (( failures )); then
    status "ERROR $failures wave-1 benchmark tracks failed; wave 2 not started"
    exit 1
fi

status "linking primary BLAZE putative table for expect6027 sensitivity reuse"
ln -s ../blaze/putative_bc.csv "$ROOT/runs/blaze_expect6027/putative_bc.csv"
status "wave 2 launch: reused-putative BLAZE16 + FLAMES24; max requested workers 40"
run_blaze "$ROOT/runs/blaze_expect6027" 6027 "BLAZE 2.6.0a0 expect6027 sensitivity (reused putative table)" reuse & pid_blaze6027=$!
run_flames & pid_flames=$!

failures=0
for pair in \
    "BLAZE6027_reused_putative:$pid_blaze6027" \
    "FLAMESv2:$pid_flames"
do
    label=${pair%%:*}
    pid=${pair##*:}
    if wait "$pid"; then
        status "$label completed"
    else
        status "ERROR $label failed"
        failures=$((failures + 1))
    fi
done
if (( failures )); then
    status "ERROR $failures wave-2 benchmark tracks failed; analysis not started"
    exit 1
fi

status "callset analysis started"
/usr/bin/time -v -o "$ROOT/analysis/analyze_callsets_time.txt" \
    python3 "$ROOT/scripts/analyze_callsets.py" \
    > "$ROOT/analysis/analyze_callsets_stdout.log" \
    2> "$ROOT/analysis/analyze_callsets_stderr.log" || exit

status "BLAZE high-Q selection-mechanism analysis started"
/usr/bin/time -v -o "$ROOT/analysis/analyze_blaze_highq_mechanism_time.txt" \
    python3 "$ROOT/scripts/analyze_blaze_highq_mechanism.py" \
    > "$ROOT/analysis/analyze_blaze_highq_mechanism_stdout.log" \
    2> "$ROOT/analysis/analyze_blaze_highq_mechanism_stderr.log" || exit

status "read-assignment analysis started"
/usr/bin/time -v -o "$ROOT/analysis/analyze_demux_assignments_time.txt" \
    python3 "$ROOT/scripts/analyze_demux_assignments.py" \
    > "$ROOT/analysis/analyze_demux_assignments_stdout.log" \
    2> "$ROOT/analysis/analyze_demux_assignments_stderr.log" || exit

status "BLAZE identical-whitelist assignment reproducibility audit started"
/usr/bin/time -v -o "$ROOT/analysis/analyze_blaze_assignment_nondeterminism_time.txt" \
    python3 "$ROOT/scripts/analyze_blaze_assignment_nondeterminism.py" \
    > "$ROOT/analysis/analyze_blaze_assignment_nondeterminism_stdout.log" \
    2> "$ROOT/analysis/analyze_blaze_assignment_nondeterminism_stderr.log" || exit

status "strict BLAZE raw-to-corrected audit started"
/usr/bin/time -v -o "$ROOT/analysis/audit_blaze_raw_to_corrected_time.txt" \
    python3 "$ROOT/scripts/audit_blaze_raw_to_corrected.py" \
    --matched-fastq "$ROOT/runs/blaze/matched_reads.fastq.gz" \
    --putative-csv "$ROOT/runs/blaze/putative_bc.csv" \
    --truth "$ROOT/input/official_shortread_barcodes_10433.txt" \
    --design-whitelist "$ROOT/input/10x_3v2_full_whitelist.txt" \
    --selected-whitelist "$ROOT/runs/blaze/whitelist.csv" \
    --truth-labels "$ROOT/input/Lymph_node_official_barcodes_labels.tsv.gz" \
    --output "$ROOT/analysis/blaze_raw_to_corrected_metrics.tsv" \
    --examples "$ROOT/analysis/blaze_raw_valid_to_valid_examples.tsv" \
    --label-transitions "$ROOT/analysis/blaze_raw_valid_to_valid_label_transitions.tsv" \
    --barcode-transitions "$ROOT/analysis/blaze_raw_valid_to_valid_barcode_transitions.tsv" \
    > "$ROOT/analysis/audit_blaze_raw_to_corrected_stdout.log" \
    2> "$ROOT/analysis/audit_blaze_raw_to_corrected_stderr.log" || exit

status "strict RAD raw-to-corrected audit started"
/usr/bin/time -v -o "$ROOT/analysis/audit_rad_raw_to_corrected_time.txt" \
    python3 "$ROOT/scripts/audit_rad_raw_to_corrected.py" \
    --fastq "$ROOT/runs/rad/demux/ERR3268990.fq.gz" \
    --truth "$ROOT/input/official_shortread_barcodes_10433.txt" \
    --design-whitelist "$ROOT/input/10x_3v2_full_whitelist.txt" \
    --selected-whitelist "$ROOT/runs/rad/scan/ERR3268990.txt" \
    --truth-labels "$ROOT/input/Lymph_node_official_barcodes_labels.tsv.gz" \
    --output "$ROOT/analysis/rad_raw_to_corrected_metrics.tsv" \
    --examples "$ROOT/analysis/rad_raw_valid_to_valid_examples.tsv" \
    --label-transitions "$ROOT/analysis/rad_raw_valid_to_valid_label_transitions.tsv" \
    > "$ROOT/analysis/audit_rad_raw_to_corrected_stdout.log" \
    2> "$ROOT/analysis/audit_rad_raw_to_corrected_stderr.log" || exit

status "biological-endpoint redirect counterfactual started"
/usr/bin/time -v -o "$ROOT/analysis/analyze_endpoint_redirects_time.txt" \
    python3 "$ROOT/scripts/analyze_endpoint_redirects.py" \
    > "$ROOT/analysis/analyze_endpoint_redirects_stdout.log" \
    2> "$ROOT/analysis/analyze_endpoint_redirects_stderr.log" || exit

status "clone-5 same-read cross-method assignment analysis started"
/usr/bin/time -v -o "$ROOT/analysis/analyze_clone5_cross_method_time.txt" \
    python3 "$ROOT/scripts/analyze_clone5_cross_method.py" \
    > "$ROOT/analysis/analyze_clone5_cross_method_stdout.log" \
    2> "$ROOT/analysis/analyze_clone5_cross_method_stderr.log" || exit

python3 "$ROOT/scripts/summarize_flexiplex_edit_distances.py"
python3 "$ROOT/scripts/make_timing_summary.py"
status "summary plotting started"
/usr/bin/time -v -o "$ROOT/analysis/plot_benchmark_summary_time.txt" \
    python3 "$ROOT/scripts/plot_benchmark_summary.py" \
    > "$ROOT/analysis/plot_benchmark_summary_stdout.log" \
    2> "$ROOT/analysis/plot_benchmark_summary_stderr.log" || exit
status "independent consistency validation started"
/usr/bin/time -v -o "$ROOT/analysis/validate_benchmark_time.txt" \
    python3 "$ROOT/scripts/validate_benchmark.py" \
    > "$ROOT/analysis/validate_benchmark_stdout.log" \
    2> "$ROOT/analysis/validate_benchmark_stderr.log" || exit
status "BENCHMARK_COMPLETE"
