# Reconstruct the RAGE-seq benchmark input

The ENA submission for **ERR3268991** contains the reads used in the manuscript's RAGE-seq benchmark. Restoring their saved order reproduces the exact decompressed FASTQ, including headers, sequences, qualities and plus lines. The complete comparison covers 20,346,396 unique reads and 16,466,857,803 sequence bases.

## Input files

Download the public FASTQ and restore the selected-order checkpoint and its `input_id_validation.json` receipt under `checkpoints/figure_03/rage_matched/counts/` from the [checkpoint package](release_review.md).

| File or fingerprint | Expected identity |
|---|---|
| ENA `ramos_nanopore.fastq.gz` | 16,675,472,857 bytes; MD5 `93bdd7b64877d96f38720aea13c92bdc` |
| Public compressed FASTQ | SHA-256 `61e883cac86d9d49d89bc7650db0674de89cd2938b253773c1b30bb973409023` |
| `input_original_ids.txt.gz` | 432,145,969 bytes; SHA-256 `e4831a95828b65f21253c9f1058f1af9ef2fa7abe286321d88aaffba12ab2952` |
| Ordered canonical records | SHA-256 `a5f866d6180b46e0acbd3aa2526364060c152380714b00ec0ed74b8c1e8c24af` |
| Exact decompressed FASTQ | SHA-256 `2f4f7e469795b23c15209547909ec791e937058497328ba69d0855274eb380f7` |

The [acquisition receipt](../validation/rage_public_acquisition.json) verifies ENA's published MD5. The [complete comparison](../validation/rage_public_payload_comparison.json) records the matching canonical and decompressed FASTQ hashes. The [identity script](../scripts/revision/figure_3_fastq_identity.py) defines the fingerprints.

## Download the public FASTQ

Run from the repository root:

```bash
python3 scripts/acquire_rage_public.py \
  --output /path/to/public/ramos_nanopore.fastq.gz \
  --connections 4
```

The downloader retrieves [ENA's submitted file](https://ftp.sra.ebi.ac.uk/vol1/run/ERR326/ERR3268991/ramos_nanopore.fastq.gz), verifies its MD5 and writes `/path/to/public/ramos_nanopore.fastq.acquisition.json`.

## Restore the benchmark read order

The reconstruction requires Python 3, GNU `sort` and `pigz`. Allow 24 GB RAM and at least 100 GB of temporary disk space. The [cluster template](../scripts/revision/rage_public_reorder.sbatch) requests six CPUs for verification. The complete verification took about 11 minutes with Python 3.6.8, GNU sort 8.30 and pigz 2.4; writing and compressing the output requires additional time. The [execution record](../validation/rage_public_reorder_submission.json) retains the command and script hashes.

```bash
python3 scripts/figure_03/reorder_public_fastq.py \
  --public /path/to/public/ramos_nanopore.fastq.gz \
  --acquisition-report /path/to/public/ramos_nanopore.fastq.acquisition.json \
  --order checkpoints/figure_03/rage_matched/counts/input_original_ids.txt.gz \
  --identity checkpoints/figure_03/rage_matched/counts/input_id_validation.json \
  --output /path/to/public/rageseq_selected_order.fq.gz \
  --report /path/to/public/reconstruction.json \
  --scratch /path/to/node-local/sort-scratch \
  --sort-threads 3 --sort-memory 6G --pigz-threads 2
```

For verification alone, replace `--output /path/to/public/rageseq_selected_order.fq.gz` with `--verify-only`. This checks the complete ordered stream and records the result without writing a recompressed FASTQ.

The reconstruction proceeds as follows:

1. Verify the public-file hash and the saved-order checksum.
2. Assign each saved read ID its integer position, rejecting duplicate IDs.
3. Read the public FASTQ once. Match each read to its position and send that position plus a lossless encoding of the four original FASTQ lines to external sort. Reject repeated, extra or missing IDs.
4. Decode the sorted records and verify consecutive positions, read and base counts, ordered IDs, sequence/quality content and the complete canonical hash.
5. Publish the compressed output after all checks pass, write the JSON report and remove temporary sort files.

Canonical records are encoded as `uint64be(ID byte length) + ID + uint64be(sequence length) + sequence + quality`, concatenated in the saved order. The ID is the first header token without `@`; CR/LF line endings are removed. The canonical fingerprint measures ID, sequence and quality identity. The separate decompressed-byte fingerprint also checks full headers, plus-line annotations and line endings. The output preserves the original public record bytes.

## Check the reconstruction code

```bash
python3 scripts/revision/rage_public_reorder_fixtures.py
```

The [fixture results](../validation/rage_public_reorder_fixtures.json) cover reversed order, changed header annotations, duplicate/missing/extra IDs, altered sequence or quality, malformed FASTQ, edited order files and external merging. The complete dataset is checked against the fingerprints above before demultiplexing.
