#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "usage: $0 DATASET [DATASET ...]" >&2
    exit 2
fi

run_root=/scratch-nfs/f005f43/longbench_full_demux_20260730
blaze_root="${run_root}/runs/blaze2_2.5.0_longbench_published"
flames_root="${run_root}/runs/flames2.0.1_longbench_published"
runner="${run_root}/scripts/run_longbench_flames_stage.sh"
config_root="${run_root}/provenance/LongBench_workflow_37a9506/lr_sc_sn/config"

run_stage() {
    local dataset=$1
    local stage=$2
    local fastq=$3
    local config=$4
    local outdir="${flames_root}/${dataset}"
    local marker="${outdir}/${stage}.DONE"

    if [[ -e "${marker}" ]]; then
        echo "${dataset}: ${stage} already complete"
        return
    fi

    mkdir -p "${outdir}"
    /usr/bin/time -v -o "${outdir}/${stage}.time.txt" \
        "${runner}" "${fastq}" "${outdir}" "${config}" \
        > "${outdir}/${stage}.log" 2>&1
    touch "${marker}"
}

for dataset in "$@"; do
    case "${dataset}" in
        SC_ONT|SC_PB|SN_ONT|SN_PB) ;;
        *)
            echo "unknown LongBench dataset: ${dataset}" >&2
            exit 2
            ;;
    esac

    blaze_dir="${blaze_root}/${dataset}"
    while [[ ! -e "${blaze_dir}/DONE" ]]; do
        sleep 30
    done

    matched="${blaze_dir}/matched_reads.fastq"
    test -s "${matched}"
    outdir="${flames_root}/${dataset}"

    run_stage "${dataset}" genome_map "${matched}" \
        "${config_root}/flames_genome_map.json"
    run_stage "${dataset}" gene_quant "${matched}" \
        "${config_root}/flames_gene_quant.json"

    dedup="${outdir}/matched_reads_dedup.fastq"
    test -s "${dedup}"
    run_stage "${dataset}" trans_map_and_quant "${dedup}" \
        "${config_root}/flames_trans_map_and_quant.json"

    touch "${outdir}/DONE"
    echo "${dataset}: all FLAMES stages complete at $(date -u +%FT%TZ)"
done
