#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 MATCHED_FASTQ OUTDIR CONFIG_JSON" >&2
  exit 2
fi

fastq=$1
outdir=$2
config=$3

case "$(basename "$config")" in
  flames_genome_map.json)
    expected_sha=18dcabed08851f25a2bf7fdf361eaa1ea238afe32e506491d3582fe92d64b2a2
    ;;
  flames_gene_quant.json)
    expected_sha=d42d7a7310983941221bb4f919f35719a41e27ad27d8401763f55ba4312ddc7a
    ;;
  flames_trans_map_and_quant.json)
    expected_sha=435c6c4f7f5ae7b87c5fc6395a10783109289fba4496e5b70fa56aa03f51e27d
    ;;
  *)
    echo "Refusing non-LongBench FLAMES config: $config" >&2
    exit 3
    ;;
esac

observed_sha=$(sha256sum "$config" | awk '{print $1}')
if [[ "$observed_sha" != "$expected_sha" ]]; then
  echo "Config checksum mismatch: $config" >&2
  echo "expected $expected_sha" >&2
  echo "observed $observed_sha" >&2
  exit 4
fi

run_root=/scratch-nfs/f005f43/longbench_full_demux_20260730
sif=$run_root/tools/bioconductor_3.20_r4.4.2.sif
run_lib=$run_root/tools/Rlib_FLAMES_2.0.1
home_lib=/dartfs-hpc/rc/home/3/f005f43/R/x86_64-redhat-linux-gnu-library/4.4
compat=$run_root/tools/el8_compat_libs
basilisk_dir=/scratch/f005f43/longbench_flames201_basilisk
driver=$run_root/scripts/run_longbench_flames_stage.R
genome=$run_root/references/gencode_v44/GRCh38.primary_assembly.genome.fa
gtf=$run_root/references/gencode_v44/gencode.v44.annotation.gtf
minimap2=$run_root/tools/minimap2-2.28_x64-linux/minimap2
k8=$run_root/tools/minimap2-2.28_x64-linux/k8

for required in \
  "$fastq" "$config" "$sif" "$driver" "$genome" "$gtf" "$minimap2" "$k8"
do
  if [[ ! -r "$required" ]]; then
    echo "Missing required input: $required" >&2
    exit 5
  fi
done

mkdir -p "$outdir"

exec apptainer exec \
  --cleanenv \
  --bind /scratch:/scratch \
  --bind /scratch-nfs:/scratch-nfs \
  --env "BASILISK_EXTERNAL_DIR=$basilisk_dir,BASILISK_NO_DESTROY=1,LD_LIBRARY_PATH=$compat,R_LIBS_USER=$run_lib:$home_lib,R_ENVIRON_USER=/dev/null,R_PROFILE_USER=/dev/null" \
  "$sif" \
  Rscript "$driver" \
    "$fastq" \
    "$outdir" \
    "$config" \
    "$gtf" \
    "$genome" \
    "$minimap2" \
    "$k8"
