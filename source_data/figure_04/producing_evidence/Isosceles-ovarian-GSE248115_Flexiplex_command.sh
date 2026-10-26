#!/usr/bin/env bash
# verbatim reconstruction of GSE248115_Flexiplex_discovery
bash -o pipefail -c gzip\ -cd\ \'/scratch-nfs/f005f43/rad_biological_benchmark_20260731/raw/GSE248115/SRR26865982_ONT_PromethION.fastq.gz\'\ \|\ \'/scratch/f005f43/measles_p7_p8_four_tool_20260730/tools/flexiplex-v1.02.6/flexiplex-linux\'\ -d\ 10x3v3\ -e\ 2\ -f\ 8\ -p\ 20\ -n\ \'/scratch-nfs/f005f43/rad_biological_benchmark_20260731/runs/GSE248115/Flexiplex/discovery/GSE248115\'\ \>\ /dev/null 
