#!/usr/bin/env bash
set -euo pipefail

run_root=/scratch-nfs/f005f43/longbench_snont_postdemux_vireo_20260803
panel_root="$run_root/bulk_donor_panel"
scripts="$run_root/scripts/bulk_donor_panel"
raw="$panel_root/raw_fastq"
genome_source=/scratch-nfs/f005f43/longbench_full_demux_20260730/references/gencode_v44/GRCh38.primary_assembly.genome.fa
gtf_source=/scratch-nfs/f005f43/longbench_full_demux_20260730/references/gencode_v44/gencode.v44.annotation.gtf
split_genome="$panel_root/reference/subjunc/genome.500bp-lines.fa"
index="$panel_root/reference/subjunc/genome_index"
index_done="$panel_root/reference/subjunc/INDEX.DONE.tsv"
snp_vcf="$panel_root/reference/genome1K.phase3.SNP_AF5e2.chr1toX.hg38.vcf.gz"
cellsnp=/scratch-nfs/f005f43/rad_biological_benchmark_20260731/env_snp/bin/cellsnp-lite
vireo="$run_root/env_vireo_0.5.8/bin/vireo"
samtools=/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/bin/samtools
bgzip=/scratch-nfs/f005f43/rad_biological_benchmark_20260731/env_snp/bin/bgzip
tabix=/scratch-nfs/f005f43/rad_biological_benchmark_20260731/env_snp/bin/tabix
donors=(H146 H1975 H211 H2228 H526 H69 HCC827 SHP77)
sample_order=H146,H1975,H211,H2228,H526,H69,HCC827,SHP77
mkdir -p "$panel_root"/{alignment,bulk_cellsnp,final,logs,provenance,reference/subjunc,stages,trimmed,validation}

exec > >(tee -a "$panel_root/logs/master.log") 2>&1
printf '[%s] bulk donor panel pipeline start\n' "$(date -u +%FT%TZ)"

expected_raw=(
  H146_S1_R1_001.fastq.gz:3357606456 H146_S1_R2_001.fastq.gz:3410257163
  H1975_S6_R1_001.fastq.gz:3865135203 H1975_S6_R2_001.fastq.gz:3943772293
  H211_S4_R1_001.fastq.gz:3942855733 H211_S4_R2_001.fastq.gz:4019943552
  H2228_S7_R1_001.fastq.gz:4216034833 H2228_S7_R2_001.fastq.gz:4288363124
  H526_S3_R1_001.fastq.gz:3289838644 H526_S3_R2_001.fastq.gz:3355890441
  H69_S2_R1_001.fastq.gz:3752566757 H69_S2_R2_001.fastq.gz:3817102007
  HCC827_S8_R1_001.fastq.gz:4110286697 HCC827_S8_R2_001.fastq.gz:4189731945
  SHP77_S5_R1_001.fastq.gz:3795837834 SHP77_S5_R2_001.fastq.gz:3865599174
)
for spec in "${expected_raw[@]}"; do
  file=${spec%%:*}
  bytes=${spec##*:}
  [[ -r "$raw/$file" && "$(stat -c %s "$raw/$file")" -eq "$bytes" ]] || {
    echo "raw input validation failed: $raw/$file" >&2
    exit 10
  }
done
for input in "$genome_source" "$gtf_source" "$cellsnp" "$vireo" "$samtools" "$bgzip" "$tabix" "$scripts/build_subjunc_index.R"; do
  [[ -r "$input" && -s "$input" ]] || { echo "missing input: $input" >&2; exit 10; }
done
{
  printf 'validated_utc\t%s\n' "$(date -u +%FT%TZ)"
  printf 'raw_fastq_files\t16\n'
  printf 'cell_lines\t8\n'
  printf 'paper_workflow_commit\t37a9506\n'
} > "$panel_root/stages/INPUTS.VALIDATED.tsv"

if [[ ! -s "$index_done" ]]; then
  if [[ -e "$split_genome" || -e "$index.00.b.array" ]]; then
    echo "partial Subjunc reference/index exists without completion marker" >&2
    exit 11
  fi
  printf '[%s] wrapping genome to <=500-base FASTA lines\n' "$(date -u +%FT%TZ)"
  awk '
    /^>/ { print; next }
    {
      while (length($0) > 500) {
        print substr($0, 1, 500)
        $0 = substr($0, 501)
      }
      print
    }
  ' "$genome_source" > "$split_genome"
  awk '!/^>/ && length($0)>500 {bad=1} END{exit bad}' "$split_genome"
  /usr/bin/time -v -o "$panel_root/logs/subjunc_index.time.txt" \
    Rscript "$scripts/build_subjunc_index.R" "$split_genome" "$index" \
    > "$panel_root/logs/subjunc_index.log" 2>&1
  compgen -G "$index.*" > /dev/null || { echo "Rsubread index outputs missing" >&2; exit 11; }
  {
    printf 'completed_utc\t%s\n' "$(date -u +%FT%TZ)"
    printf 'genome_source\t%s\n' "$genome_source"
    printf 'max_fasta_line_bases\t500\n'
    printf 'index_basename\t%s\n' "$index"
  } > "$index_done"
fi

fastp_all_done="$panel_root/stages/FASTP.ALL.DONE.tsv"
if [[ ! -s "$fastp_all_done" ]]; then
  printf '[%s] running paper-default fastp for eight bulk pairs (4 samples concurrently)\n' "$(date -u +%FT%TZ)"
  # A separately launched fastp window is allowed to overlap index construction.
  # If it is still writing a sample, wait for that exact worker before the
  # idempotent per-sample runner is invoked here; never mistake a live output for
  # a stale partial.
  for donor in "${donors[@]}"; do
    if [[ ! -s "$panel_root/trimmed/$donor/FASTP.DONE.tsv" ]] && \
       { [[ -e "$panel_root/trimmed/$donor/${donor}_R1.fastq.gz" ]] || \
         [[ -e "$panel_root/trimmed/$donor/${donor}_R2.fastq.gz" ]]; }; then
      while pgrep -u "$UID" -f "run_fastp_one.sh $donor" > /dev/null; do sleep 30; done
    fi
  done
  printf '%s\n' "${donors[@]}" | xargs -n 1 -P 4 bash "$scripts/run_fastp_one.sh"
  printf 'completed_utc\t%s\n' "$(date -u +%FT%TZ)" > "$fastp_all_done"
else
  printf '[%s] reusing completed eight-sample fastp stage\n' "$(date -u +%FT%TZ)"
fi
for donor in "${donors[@]}"; do [[ -s "$panel_root/trimmed/$donor/FASTP.DONE.tsv" ]]; done

alignment_all_done="$panel_root/stages/ALIGNMENT.ALL.DONE.tsv"
if [[ ! -s "$alignment_all_done" ]]; then
  printf '[%s] running exact paper Subjunc settings (4 samples concurrently)\n' "$(date -u +%FT%TZ)"
  printf '%s\n' "${donors[@]}" | xargs -n 1 -P 4 bash "$scripts/run_align_one.sh"
  printf 'completed_utc\t%s\n' "$(date -u +%FT%TZ)" > "$alignment_all_done"
else
  printf '[%s] reusing completed eight-sample Subjunc stage\n' "$(date -u +%FT%TZ)"
fi
bams=()
for donor in "${donors[@]}"; do
  bam="$panel_root/alignment/$donor/$donor.sorted.bam"
  [[ -s "$panel_root/alignment/$donor/ALIGNMENT.DONE.tsv" && -s "$bam" && -s "$bam.bai" ]]
  "$samtools" quickcheck -v "$bam"
  bams+=("$bam")
done

printf '[%s] waiting for the official hg38 cellSNP common-SNP VCF\n' "$(date -u +%FT%TZ)"
while [[ ! -s "$snp_vcf" ]]; do sleep 30; done
gzip -t "$snp_vcf"
[[ "$(stat -c %s "$snp_vcf")" -eq 92432276 ]] || {
  echo "candidate SNP VCF does not match the official SourceForge object size" >&2
  exit 12
}
header=$(zcat "$snp_vcf" | awk '/^#CHROM/{header=$0} END{print header}')
[[ "$header" == $'#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO' ]] || {
  echo "candidate SNP VCF has an unexpected sample-bearing/header layout" >&2
  exit 12
}
first_record=$(zcat "$snp_vcf" | awk '!/^#/ && first==0{first=$0} END{print first}')
[[ "$first_record" == $'1\t11008\trs575272151\tC\tG\t100\tPASS\tAF=0.0880591' ]] || {
  echo "candidate SNP VCF first record differs from the official cellSNP hg38 object" >&2
  exit 12
}

cellsnp_out="$panel_root/bulk_cellsnp"
if [[ ! -s "$cellsnp_out/CELLSNP.DONE.tsv" ]]; then
  if [[ -e "$cellsnp_out/cellSNP.cells.vcf.gz" ]]; then
    echo "partial CellSNP output exists without completion marker" >&2
    exit 13
  fi
  bam_csv=$(IFS=,; echo "${bams[*]}")
  /usr/bin/time -v -o "$panel_root/logs/bulk_cellsnp.time.txt" \
    "$cellsnp" \
      -s "$bam_csv" \
      -I "$sample_order" \
      -O "$cellsnp_out" \
      -R "$snp_vcf" \
      -p 32 \
      --cellTAG None --UMItag None --gzip --genotype \
      > "$panel_root/logs/bulk_cellsnp.log" 2>&1
  for output in cellSNP.base.vcf.gz cellSNP.cells.vcf.gz cellSNP.samples.tsv cellSNP.tag.AD.mtx cellSNP.tag.DP.mtx; do
    [[ -s "$cellsnp_out/$output" ]] || { echo "missing CellSNP output: $output" >&2; exit 13; }
  done
  observed_order=$(paste -sd, "$cellsnp_out/cellSNP.samples.tsv")
  [[ "$observed_order" == "$sample_order" ]] || { echo "CellSNP donor order mismatch" >&2; exit 13; }
  gzip -t "$cellsnp_out/cellSNP.base.vcf.gz" "$cellsnp_out/cellSNP.cells.vcf.gz"
  printf 'completed_utc\t%s\n' "$(date -u +%FT%TZ)" > "$cellsnp_out/CELLSNP.DONE.tsv"
fi

final_vcf="$panel_root/final/fixed_8line_bulk_illumina_donor_panel.vcf.gz"
if [[ ! -s "$final_vcf" ]]; then
  {
    zcat "$cellsnp_out/cellSNP.cells.vcf.gz" | awk '/^#/'
    zcat "$cellsnp_out/cellSNP.cells.vcf.gz" | awk '!/^#/' | \
      LC_ALL=C sort -k1,1V -k2,2n -k4,4 -k5,5
  } | "$bgzip" -@ 8 -c > "$final_vcf.partial"
  "$tabix" -f -p vcf "$final_vcf.partial"
  mv "$final_vcf.partial" "$final_vcf"
  mv "$final_vcf.partial.tbi" "$final_vcf.tbi"
fi
gzip -t "$final_vcf"
"$tabix" -l "$final_vcf" > "$panel_root/validation/panel_contigs.txt"
python3 "$scripts/validate_panel_vcf.py" "$final_vcf" "$panel_root/validation/panel_structure.json"

validation_vireo="$panel_root/validation/ill_sn_vireo"
published_cellsnp="$run_root/provenance/paper_inputs/ill_sn_cellsnp"
published_labels="$run_root/provenance/paper_inputs/ill_sn_vireo/donor_ids.tsv"
if [[ ! -s "$validation_vireo/VIREO.DONE.tsv" ]]; then
  mkdir -p "$validation_vireo"
  "$vireo" \
    -c "$published_cellsnp" \
    -d "$final_vcf" \
    -o "$validation_vireo" \
    -t GT --callAmbientRNAs -p 16 --noPlot \
    > "$panel_root/logs/validation_ill_sn_vireo.log" 2>&1
  [[ -s "$validation_vireo/donor_ids.tsv" ]]
  printf 'completed_utc\t%s\n' "$(date -u +%FT%TZ)" > "$validation_vireo/VIREO.DONE.tsv"
fi

python3 "$run_root/scripts/donor_panel/compare_vireo_labels.py" \
  --reference "$published_labels" \
  --query "$validation_vireo/donor_ids.tsv" \
  --out-prefix "$panel_root/validation/ill_sn_reproduction" \
  --min-shared-fraction 0.99 \
  --min-both-singlet-agreement 0.95 \
  --min-reference-singlet-correct 0.85 \
  --min-published-doublet-recall 0.70 \
  --require-all-donors

vcf_sha=$(sha256sum "$final_vcf" | awk '{print $1}')
index_sha=$(sha256sum "$final_vcf.tbi" | awk '{print $1}')
site_count=$(zcat "$final_vcf" | awk '!/^#/{n++} END{print n+0}')
{
  printf 'completed_utc\t%s\n' "$(date -u +%FT%TZ)"
  printf 'vcf_sha256\t%s\n' "$vcf_sha"
  printf 'index_sha256\t%s\n' "$index_sha"
  printf 'sample_order\t%s\n' "$sample_order"
  printf 'site_count\t%s\n' "$site_count"
  printf 'structure_validation\tpassed\n'
  printf 'illumina_reproduction_validation\tpassed\n'
} > "$panel_root/validation/BULK_PANEL.VALIDATED.ok"
printf '[%s] bulk panel validated and released: %s\n' "$(date -u +%FT%TZ)" "$final_vcf"
