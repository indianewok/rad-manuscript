# LongBench fixed eight-line bulk donor panel provenance

This directory reconstructs the fixed donor-genotype VCF used by LongBench
from the eight separately sequenced paired-end Illumina bulk RNA-seq libraries.
It does **not** learn donor genotypes from pooled single-cell or single-nucleus
data.

## Author workflow source

The implementation follows commit `37a9506` of
`youyupei/LongBench_workflow`:

- `sub_workflows/sr_bulk/rules/mapping.smk`
- `sub_workflows/sr_bulk/scripts/build_index.R`
- `sub_workflows/sr_bulk/scripts/align_reads.R`
- `rules/sc_cell_line_anno.smk`

The mapping sequence is default paired-end `fastp`, 500-base FASTA line
wrapping, `Rsubread::buildindex`, and `Rsubread::subjunc` with
`reportAllJunctions=TRUE`, `useAnnotation=TRUE`, `input_format="gzFASTQ"`,
`isGTF=TRUE`, and `unique=TRUE`.  The bulk CellSNP command uses the exact paper
sample order:

`H146,H1975,H211,H2228,H526,H69,HCC827,SHP77`

and the official cellSNP 1000 Genomes phase-3 AF>5% hg38 candidate-SNP VCF.

The official candidate VCF was downloaded from:

```text
https://sourceforge.net/projects/cellsnp/files/SNPlist/genome1K.phase3.SNP_AF5e2.chr1toX.hg38.vcf.gz/download
```

It is 92,432,276 bytes with SHA-256
`88e22ea3c4d416aed925e5b3efeb371ef023c954599a325dcb334dffcf6ad707`.
The cellSNP project generated its hg38 object by lifting the original phase-3
VCF, but the compressed file retains source `b37` metadata in its VCF header.
That stale header must not be interpreted as evidence that the data coordinates
were not lifted.  A clean fresh download was validated by compressed size,
gzip CRC/ISIZE, VCF layout, first record, and SHA-256.  It was byte-identical to
the previously staged local file.

An earlier HTTP range-resume attempt produced the expected byte length but
failed gzip CRC and ISIZE validation.  It was quarantined with a
`corrupt_resume_20260803T2003Z` suffix and never promoted or consumed.

The local GENCODE v44 primary-assembly FASTA/GTF are used for human alignment.
The authors' private reference also appended synthetic spike-in contigs.  Those
contigs are not needed for pileup at the human 1000 Genomes SNP sites, but this
difference is documented rather than describing the reconstructed VCF as
byte-identical to the authors' missing private file.

## Public-data absence audit, 2026-08-03

An exhaustive anonymous AWS inventory contained 265 objects.  Twelve VCF/BCF
objects were present: the base and per-cell CellSNP VCFs for each of the six
single-cell/single-nucleus platform datasets.  None was the eight-sample named
bulk donor VCF.  All 32 public archives were raw POD5 archives, all four README
objects were checked, and the sole processed bulk RDS object was a DGE object,
not a genotype panel.  Thus the paper-referenced private donor VCF is not in the
current public bucket.

Audit commands (the complete key list was streamed, not selectively sampled):

```bash
aws s3api list-objects-v2 --no-sign-request --bucket longbench-data \
  --query 'Contents[].{Key:Key,Size:Size}' --output json

aws s3 ls s3://longbench-data/ --no-sign-request --recursive
```

The resulting inventory was counted by object, suffix, and basename pattern;
every VCF/BCF, archive, README, and RDS key was inspected.

## Release contract

No downstream RAD/Flexiplex/BLAZE Vireo job may consume the panel until both
files and the nonempty validation sentinel exist:

```text
final/fixed_8line_bulk_illumina_donor_panel.vcf.gz
final/fixed_8line_bulk_illumina_donor_panel.vcf.gz.tbi
validation/BULK_PANEL.VALIDATED.ok
```

The sentinel is written only after structural/informativeness checks and a
fixed-panel Vireo reproduction audit against the released Illumina-SN labels.
