#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "usage: $0 DATASET rad|blaze|flex_v101|flex_v1026" >&2
    exit 2
fi

dataset=$1
arm=$2
case "${dataset}" in
    SC_ONT|SC_PB)
        library=sc
        cellranger=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/longbench/truth/count_matrix_barcodes/ill_sc_barcodes.tsv.gz
        ;;
    SN_ONT|SN_PB)
        library=sn
        cellranger=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/longbench/truth/count_matrix_barcodes/ill_sn_barcodes.tsv.gz
        ;;
    *)
        echo "unknown dataset: ${dataset}" >&2
        exit 2
        ;;
esac

audit_root=/scratch/f005f43/longbench_full_ab_audit_20260730
producer_root=/scratch-nfs/f005f43/longbench_full_demux_20260730
global_catalog=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/cellranger_whitelists/3M-february-2018-3v3.txt
label_dir=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/longbench/truth/cell_line_annotation/merged_annotation/${library}
analyzer="${audit_root}/scripts/analyze_correction_events.py"
catalog_cache="${audit_root}/reference_cache/3M-february-2018.u32"
grouping_dir="${audit_root}/grouping/${arm}_${dataset}"
out_dir="${audit_root}/results/${arm}/${dataset}"
putative_args=()

case "${arm}" in
    rad)
        producer_done="${producer_root}/runs/rad_920adda_current/${dataset}/DONE"
        assignments="${producer_root}/runs/rad_920adda_current/${dataset}/demux/${dataset}_RAD.fq.gz"
        selected="${producer_root}/runs/rad_920adda_current/${dataset}/scan_wl/${dataset}_RAD.txt"
        tool=rad
        ;;
    blaze)
        producer_done="${producer_root}/runs/blaze2_2.5.0_longbench_published/${dataset}/DONE"
        assignments="${producer_root}/runs/blaze2_2.5.0_longbench_published/${dataset}/matched_reads.fastq"
        selected="${producer_root}/runs/blaze2_2.5.0_longbench_published/${dataset}/whitelist.csv"
        putative="${producer_root}/runs/blaze2_2.5.0_longbench_published/${dataset}/putative_bc.csv"
        putative_args=(--putative-csv "${putative}")
        tool=blaze
        ;;
    flex_v101)
        case "${dataset}" in
            SC_ONT|SN_ONT) ;;
            *)
                echo "${dataset}: published Flexiplex v1.01 discovery failed; no full primary assignment arm" >&2
                exit 4
                ;;
        esac
        producer_done="${audit_root}/flexiplex_v101_output_only/${dataset}/DONE"
        assignments="${audit_root}/flexiplex_v101_output_only/${dataset}/${dataset}_flexiplex_v101_audit_reads_barcodes.txt.gz"
        selected="${producer_root}/runs/flexiplex_v1.01_paper_extension/${dataset}/discovery/filtered_barcodes.txt"
        tool=flexiplex
        ;;
    flex_v1026)
        producer_done="${audit_root}/flexiplex_v1026_current_diagnostic/${dataset}/DONE"
        assignments="${audit_root}/flexiplex_v1026_current_diagnostic/${dataset}/${dataset}_flexiplex_v1026_audit_reads_barcodes.txt.gz"
        source_root=/scratch/f005f43/rad_longbench_20260726/benchmarks/flexiplex_valid_to_valid_correction_audit_20260728
        case "${dataset}" in
            SC_ONT) selected="${source_root}/inputs/SC_flexiplex_whitelist.txt" ;;
            SC_PB) selected="${source_root}/inputs/SC_PB_flexiplex_whitelist.txt" ;;
            SN_ONT) selected="${source_root}/inputs/SN_flexiplex_whitelist.txt" ;;
            SN_PB) selected="${source_root}/inputs/SN_PB_flexiplex_whitelist.txt" ;;
        esac
        tool=flexiplex
        ;;
    *)
        echo "unknown analysis arm: ${arm}" >&2
        exit 2
        ;;
esac

while [[ ! -e "${producer_done}" ]]; do
    sleep 60
done

mkdir -p "${out_dir}" "${grouping_dir}" "$(dirname "${catalog_cache}")"

# A producer-independent arm may be started early while the main orchestrator
# is still waiting on other tools.  Serialize by arm/dataset so that the
# orchestrator cannot launch a duplicate full-file analyzer when it catches up.
exec 9>"${out_dir}/analysis.lock"
flock 9

if [[ -e "${out_dir}/DONE" ]]; then
    echo "${arm}/${dataset}: analysis already complete"
    exit 0
fi

test -s "${assignments}"
test -s "${selected}"
test -s "${cellranger}"
test -s "${global_catalog}"
test -d "${label_dir}"

/usr/bin/time -v -o "${out_dir}/time.txt" \
    python3 "${analyzer}" \
        --tool "${tool}" \
        --dataset "${dataset}" \
        --assignments "${assignments}" \
        "${putative_args[@]}" \
        --selected-whitelist "${selected}" \
        --cellranger-filtered "${cellranger}" \
        --global-catalog "${global_catalog}" \
        --catalog-cache "${catalog_cache}" \
        --label-dir "${label_dir}" \
        --grouping-check sqlite \
        --grouping-db-dir "${grouping_dir}" \
        --decompress-threads 4 \
        --outdir "${out_dir}" \
        > "${out_dir}/stdout.log" 2> "${out_dir}/stderr.log"

awk -F '\t' 'NR > 1 && $2 == "FAIL" {failed++} END {exit(failed ? 1 : 0)}' \
    "${out_dir}/invariants.tsv"
touch "${out_dir}/DONE"
