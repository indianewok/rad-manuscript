# LongBench demultiplexing benchmark: publication lock

This benchmark keeps publication-replication runs separate from RAD comparison
runs. A published arm is not retuned to match another tool.

## LongBench BLAZE -> FLAMES arm

- Workflow repository: `youyupei/LongBench_workflow`
- Workflow commit: `37a9506df7bcd92c488c0e4b2a5cbe09fa1fc19d`
- BLAZE: `blaze2==2.5.0`
- Threads: 48
- Kit/catalog: BLAZE defaults (`10x 3v3`; packaged 3M February 2018 catalog)
- Full barcode whitelist argument: none
- SC_ONT and SC_PB: `--expect-cells 5000`
- SN_ONT and SN_PB: `--force-cells 10000`
- Output FASTQ: uncompressed `matched_reads.fastq`
- FLAMES: version 2.0.1, using the three JSON configurations from the
  LongBench workflow and GENCODE v44/GRCh38 primary assembly.

The exact BLAZE command template in the authors' Snakemake rule is:

```text
blaze $full_whitelist_arg $arg_cell_calling \
  --output-prefix $out_fn --output-fastq matched_reads.fastq \
  --threads 48 --minimal_stdout INPUT
```

## FLAMESv2-preprint arm

This is a distinct protocol, not the LongBench workflow above. Its published
LongBench S10 supplement uses the first 10 million reads of each dataset
(`head -n 40000000`) and CellRanger-filtered SC/SN barcode allowlists. The SC
allowlist is shared by ONT_SC and PB_SC; the SN allowlist is shared by ONT_SN
and PB_SN. Supplying `barcodes_file` selects FLAMESv2's embedded Flexiplex
route, not BLAZE.

- Figure-code commit: `23ea9e3964dd21cc9155987c859105ba5876eed7`
- Threads: 24
- Strand: `-`
- TSO-prime: 5
- TSO: `AAGCAGTGGTATCAACGCAGAGTACATGGG`
- Cutadapt minimum length: 10
- Flexiplex barcode edit distance: 2
- Flexiplex flank edit distance: 8
- Kit/layout: 10x 3v3, primer `CTACACGACGCTCTTCCGATCT`, BC16, UMI12,
  polyT9
- Read-quality gate: none
- Reference: GRCh38 primary assembly with GENCODE v45 primary-assembly GTF
- Gene quantification: disabled
- Isoform identification: disabled
- Oarfish quantification: enabled

The S10 figure repository does not independently pin the installed FLAMES
package version. The manuscript identifies FLAMESv2 2.0.1 elsewhere and the
published S10 code follows its old API. This caveat is retained in all labels.

## Standalone Flexiplex arm

The standalone paper did not run LongBench. Its benchmark protocol used
Flexiplex v1.01 (`4430f598e8fd312c1a93525c1e61541c073e228f`):

```text
flexiplex -f 0 -p THREADS INPUT > my_barcode_list.txt
flexiplex-filter --whitelist 3M-february-2018.txt \
  --outfile filtered_barcodes.txt flexiplex_barcodes_counts.txt
gunzip -c INPUT.fastq.gz |
  flexiplex -d 10x3v3 -e 2 -k filtered_barcodes.txt -p THREADS |
  gzip > out.fastq.gz
```

The publication deliberately swept known-list barcode edit distance from 0 to
3; edit distance 2 is the tool/preset default selected for the primary
comparison. Published discovery used `-f 0`; preset/default flank edit distance
is 8. Flexiplex has no minimum-read-quality gate.

Running this v1.01 two-pass protocol on all four LongBench files is therefore a
faithful full-data protocol extension, not a claim that the standalone paper
analyzed LongBench. Existing v1.02.6 and instrumented binaries are audit-only
and never replace the pristine v1.01 executable in the primary arm.

## RAD arm

RAD is a current-main comparison arm. It is not described as a replication of
any competitor paper. Its commit, layout, whitelist inputs, and commands are
recorded independently.
