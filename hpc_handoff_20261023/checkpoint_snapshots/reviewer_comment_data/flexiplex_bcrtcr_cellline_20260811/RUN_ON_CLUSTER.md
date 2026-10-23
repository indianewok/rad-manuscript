# Flexiplex BCR/TCR cell-line analysis - cluster run instructions

Goal: compute BCR/TCR read counts per cell type (Ramos / Jurkat / Monocyte /
undetermined) for Flexiplex on the RAGE-seq cell line (ERR3268991). Native
(barcode edit distance 0) and corrected (all assigned) phases. This fills the
Figure 3G-H / Data 11 panels for Flexiplex.

Method match: the manuscript classed each raw read by its best minimap2
(map-ont) alignment to the TRUST4 hg38 BCR/TCR reference. IG* = BCR,
TR* = TCR, no alignment = unmapped. The cell-type map in this folder is the
original Figure 3 typing (1,993 Ramos / 1,572 Jurkat / 20 Monocyte), recovered
from the figure data itself.

This folder already contains every small input:
- `hg38_bcrtcr.fa` - TRUST4 human BCR/TCR reference (620 segments)
- `rageseq_barcode_celltype_map.csv` - barcode to cell type
- `join_flexiplex_bcrtcr.py` - the tabulation script (stdlib only)

## Commands (bash on a compute node; 32 cores, 48 GB suggested)

```bash
WORK=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/flexiplex_bcrtcr_cellline_20260811
FASTQ=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/raw_fastq_datasets/rageseq.fq.gz
SEL=/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/wl_scan/20260730_rageseq_ERR3268991_cellline_control/runs/flexiplex/f8_detection/selected.tsv

cd "$WORK"

# One decompression feeds both tools. Requires bash for tee >( ).
gzip -cd "$FASTQ" \
  | tee >(flexiplex -d 10x3v2 -f 8 -p 24 -k "$SEL" -n rage_flex_f8_full \
            > /dev/null 2> flex_full.log) \
  | minimap2 -x map-ont --secondary=no -t 8 hg38_bcrtcr.fa - 2> mm2_full.log \
  | awk -F'\t' '{print $1"\t"$6"\t"$10}' > rage_bcrtcr_hits.tsv

python3 join_flexiplex_bcrtcr.py
```

Use Flexiplex 1.02.6 if available (the benchmark version; flexiplex-filter
lives in `/dartfs/rc/lab/A/AckermanLab/CMV/PostRot/cmv/miniconda3/bin`). Any
1.02.x works for this fixed-list demux; record the version in the log.

Optional sbatch wrapper:

```bash
#!/bin/bash
#SBATCH --job-name=flex_bcrtcr
#SBATCH --cpus-per-task=32
#SBATCH --mem=48G
#SBATCH --time=04:00:00
set -euo pipefail
# insert the command block above
```

If dartfs streaming is slow, copy the FASTQ to node scratch first and point
FASTQ there. Do not write outputs to scratch; the join outputs must land in
$WORK so the laptop can read them.

## Expected outputs (written to this folder)

- `rage_flex_f8_full_reads_barcodes.txt` - per-read barcode sidecar
- `rage_bcrtcr_hits.tsv` - reduced alignment hits (read, target, matches)
- `flexiplex_bcrtcr_summary.tsv` - celltype x class x phase counts
- `flexiplex_bcrtcr_data11_shape.tsv` - the Data-11 panel layout
- `flexiplex_per_barcode_bcrtcr.tsv` - per-barcode counts

## Concordance checks (against the 2026-07-30 1.02.6 cluster run)

- assigned unique reads: expect about 6,595,231
- ambiguous reads dropped: expect about 69,988
- alignment rate: expect about 60% of reads with a BCR/TCR hit
- barcode hit rate: expect about 30-33% of reads

Report the join script's printed numbers next to these expectations.
