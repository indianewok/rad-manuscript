# Reconstruct the selected RAGE-seq read order from ENA

The public ENA submission for `ERR3268991` reproduces the selected manuscript FASTQ **exactly after restoring its read order**. The reconstruction below checks every ordered read ID, sequence and quality against the selected input fingerprint. It does not run RAD, BLAZE or Flexiplex.

**Complete verification passed.** The [public acquisition receipt](../validation/rage_public_acquisition.json) verifies ENA's published MD5. The [full comparison](../validation/rage_public_payload_comparison.json) verifies all **20,346,396 unique read IDs** and **16,466,857,803 sequence bases**, with no missing, extra or duplicate IDs. Both the canonical ordered-record hash and the **exact decompressed FASTQ hash**, including original headers and plus lines, match the selected input after reordering. This was a complete stream comparison, not a sample. No full reordered FASTQ was written during verification; the normal `--output` command below creates one when needed.

| Artifact | Required identity |
|---|---|
| ENA submitted `ramos_nanopore.fastq.gz` | 16,675,472,857 bytes; published MD5 `93bdd7b64877d96f38720aea13c92bdc` |
| Selected physical-read order, `input_original_ids.txt.gz` | SHA-256 `e4831a95828b65f21253c9f1058f1af9ef2fa7abe286321d88aaffba12ab2952` |
| Selected ordered canonical records | SHA-256 `a5f866d6180b46e0acbd3aa2526364060c152380714b00ec0ed74b8c1e8c24af` |
| Exact selected decompressed FASTQ, reproduced by the reordered public stream | SHA-256 `2f4f7e469795b23c15209547909ec791e937058497328ba69d0855274eb380f7` |
| Selected counts | 20,346,396 unique reads; 16,466,857,803 sequence bases |

The verified public compressed file has SHA-256 `61e883cac86d9d49d89bc7650db0674de89cd2938b253773c1b30bb973409023`. The selected-order checkpoint is 432,145,969 bytes. Job `9979121` completed verification in 669.215 seconds on the [explicitly verified CPU-only t02 allocation](../validation/rage_public_reorder_placement.json), with six CPUs and 24 GB requested. The executed versions were Python 3.6.8, GNU sort 8.30 and pigz 2.4; the full [invocation and script hashes](../validation/rage_public_reorder_submission.json) are recorded.

Obtain the selected-order checkpoint and its `input_id_validation.json` receipt at `checkpoints/figure_03/rage_matched/counts/` from the review checkpoint package. These are large generated checkpoints outside Git. The exact selected order cannot be inferred from the ENA filename or read count. The [identity script](../scripts/revision/figure_3_fastq_identity.py) records both files' hashes and the canonical encoding.

## Download the public input

Run from the repository root. The downloader checks the ENA file's published MD5 before publishing its final path and acquisition receipt:

```bash
python3 scripts/acquire_rage_public.py \
  --output /path/to/public/ramos_nanopore.fastq.gz \
  --connections 4
```

The source is the ENA-submitted file at `https://ftp.sra.ebi.ac.uk/vol1/run/ERR326/ERR3268991/ramos_nanopore.fastq.gz`. The acquisition receipt is `/path/to/public/ramos_nanopore.fastq.acquisition.json`.

## Restore the selected order and verify all payloads

Requirements are Python 3, GNU `sort`, and `pigz`. Allow 24 GB RAM and at least 100 GB free temporary space. Use a CPU-only compute allocation for the complete file; the [cluster template](../scripts/revision/rage_public_reorder.sbatch) requests six CPUs and no GPU.

The template requests one hour for verification only. Its allocation was based on a [bounded benchmark](../validation/rage_public_reorder_prefix_benchmark.json) of 100,000 actual public-prefix reads. The complete verification then finished in about 11 minutes; writing and recompressing a full FASTQ takes longer.

For verification alone, replace `--output /path/to/public/rageseq_selected_order.fq.gz` below with `--verify-only`. This sorts and hashes every record, including the exact decompressed bytes, without recompressing or writing a full FASTQ. Its receipt states `full_ordered_stream_verified: true` and `full_fastq_written: false` only after the complete comparison passes. The cluster template uses this mode; readers who need the reconstructed raw input use `--output`.

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

The script performs these steps:

1. Rehash the public compressed file against its acquisition receipt and verify the selected-order checksum.
2. Associate each selected physical read ID with its integer position. Duplicate IDs in the order fail.
3. Read each public FASTQ record once, remove its ID from the expected set, and send its position plus a lossless encoding of its four original lines to external sort. An extra or repeated ID fails; expected IDs left at EOF also fail.
4. Decode sorted records and check continuous positions, the read/base counts, ordered IDs, ordered sequence/quality payloads and complete canonical record hash. Changed sequence or quality fails the full canonical comparison.
5. Publish the gzip output atomically only after every check passes. Preserve a small JSON receipt and any diagnostic logs. Temporary sort files are removed.

The canonical record encoding is `uint64be(ID byte length) + ID + uint64be(sequence length) + sequence + quality`, concatenated in selected order. `ID` is the first header token without `@`; only CR/LF endings are removed. Header descriptions and plus-line annotations are excluded from this comparison. The reconstructed file preserves the public record bytes, so the receipt separately reports whether its **exact decompressed byte hash** also matches the selected FASTQ.

## Check the implementation on small inputs

```bash
python3 scripts/revision/rage_public_reorder_fixtures.py
```

The [fixture receipt](../validation/rage_public_reorder_fixtures.json) covers reversed order, harmless header changes, duplicate/missing/extra IDs, sequence and quality changes, malformed records, edited selected order, and external merging. These are explicitly synthetic software tests. Successful results are independently fingerprinted with the selected-input identity script; they are not evidence that the complete public dataset matches.

The complete selected canonical fingerprint remains the acceptance condition for raw analysis. A prefix benchmark or a matching file size is insufficient.
