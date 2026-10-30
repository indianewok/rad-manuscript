# Publication-locked LongBench FLAMES environment

## Scope

This environment reproduces the official LongBench BLAZE-to-FLAMES arm. It is
separate from the FLAMESv2 supplementary S10 arm, which used GENCODE v45.
LongBench uses GENCODE v44 and the three committed LongBench FLAMES JSON files.

## LongBench workflow source

- Repository commit: `37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d`
- FLAMES rule:
  `/tmp/LongBench_workflow/sub_workflows/lr_sc_sn/rules/flames.smk`
- Rule SHA-256:
  `7d1e5b967c7d37b6cf7dc37ede15e4a3356c4f524a80fbfc3f218c6201808f37`
- Genome-map config SHA-256:
  `18dcabed08851f25a2bf7fdf361eaa1ea238afe32e506491d3582fe92d64b2a2`
- Gene-quant config SHA-256:
  `d42d7a7310983941221bb4f919f35719a41e27ad27d8401763f55ba4312ddc7a`
- Transcript-map-and-quant config SHA-256:
  `435c6c4f7f5ae7b87c5fc6395a10783109289fba4496e5b70fa56aa03f51e27d`

The Snakemake rules request 48 CPUs, but each committed FLAMES JSON file sets
`pipeline_parameters.threads` to 32. FLAMES 2.0.1 passes that JSON value to its
mapping and quantification functions, so a faithful run must not override it.

## FLAMES and runtime

- FLAMES source:
  `/scratch-nfs/f005f43/longbench_full_demux_20260730/tools/FLAMES_2.0.1`
- FLAMES commit:
  `4b6058f58c5b19365919990b3f2c1053f2035b01`
- Installed package library:
  `/scratch-nfs/f005f43/longbench_full_demux_20260730/tools/Rlib_FLAMES_2.0.1`
- Confirmed package version: `2.0.1`
- Container:
  `/scratch-nfs/f005f43/longbench_full_demux_20260730/tools/bioconductor_3.20_r4.4.2.sif`
- Container SHA-256:
  `11c4c3dcd0f38a2a2287b89a6b5bf39a0920b057872e926721f6bda80438f912`
- Container source digest:
  `sha256:5053f59de1c1a79b5a05d820ba722bae62ded0c1042e547189aa0226f111ea7e`
- Runtime: R 4.4.2, Bioconductor 3.20
- Compatible R 4.4 dependency library:
  `/dartfs-hpc/rc/home/3/f005f43/R/x86_64-redhat-linux-gnu-library/4.4`
- EL8 compatibility libraries:
  `/scratch-nfs/f005f43/longbench_full_demux_20260730/tools/el8_compat_libs`
- Prewarmed FLAMES basilisk cache:
  `/scratch/f005f43/longbench_flames201_basilisk`

The default home-directory basilisk cache exceeded the home quota. The
publication-locked environment was therefore prewarmed under node-local
`/scratch`. Full runs must set `BASILISK_EXTERNAL_DIR` to that path.

## Alignment tools

- LongBench minimap2:
  `/scratch-nfs/f005f43/longbench_full_demux_20260730/tools/minimap2-2.28_x64-linux/minimap2`
- Version: `2.28-r1209`
- k8:
  `/scratch-nfs/f005f43/longbench_full_demux_20260730/tools/minimap2-2.28_x64-linux/k8`
- Official minimap2 archive SHA-256:
  `51f2cf0e486d0f9f88ace1aa58fdc56571382a676ea0889ae607301c60693377`
- FLAMES internal samtools version: `1.21`
- Prewarmed internal tool environment:
  `/scratch/f005f43/longbench_flames201_basilisk/1.18.0/FLAMES/2.0.1/bins_env`

## LongBench GENCODE v44 references

- FASTA:
  `/scratch-nfs/f005f43/longbench_full_demux_20260730/references/gencode_v44/GRCh38.primary_assembly.genome.fa`
- Compressed FASTA MD5: `9c3fc2ca260a767530dddb0f26721a6b` (verified)
- GTF:
  `/scratch-nfs/f005f43/longbench_full_demux_20260730/references/gencode_v44/gencode.v44.annotation.gtf`
- Compressed GTF MD5: `ee330cfe6d0654ba9b9cf434d5c1bfb1` (verified)

## Required execution environment

Use these variables for every FLAMES stage:

```bash
export BASILISK_EXTERNAL_DIR=/scratch/f005f43/longbench_flames201_basilisk
export BASILISK_NO_DESTROY=1
export LD_LIBRARY_PATH=/scratch-nfs/f005f43/longbench_full_demux_20260730/tools/el8_compat_libs
export R_LIBS_USER=/scratch-nfs/f005f43/longbench_full_demux_20260730/tools/Rlib_FLAMES_2.0.1:/dartfs-hpc/rc/home/3/f005f43/R/x86_64-redhat-linux-gnu-library/4.4
export R_ENVIRON_USER=/dev/null
export R_PROFILE_USER=/dev/null
```

Within the container, each published stage calls:

```r
sc_long_pipeline(
    fastq = fastq_flames,
    outdir = outdir,
    annot = GTF,
    genome_fa = genome,
    config_file = config_file,
    barcodes_file = "not used",
    minimap2 = minimap2,
    k8 = k8
)
```

Run the three unmodified configs in this order:

1. `flames_genome_map.json`
2. `flames_gene_quant.json`
3. `flames_trans_map_and_quant.json`

## Smoke validation

- Result:
  `/scratch-nfs/f005f43/longbench_full_demux_20260730/provenance/flames_2.0.1_smoke_localcache`
- Status: exit 0
- Input: bundled 10-read demultiplexed FLAMES example
- Config: the unmodified LongBench `flames_genome_map.json`
- Output: 10 total reads, 10 mapped primary reads, 0 secondary reads
- Produced and indexed:
  `align2genome.bam`, `align2genome.bam.bai`, and `transcript_assembly.fa`
- Logged minimap2 command includes the publication settings
  `-ax splice -y -t 32 -k14 --secondary=no --seed 2023`,
  the generated junction BED, and `--junc-bonus 1`.
