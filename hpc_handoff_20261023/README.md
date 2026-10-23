# RAD HPC handoff — 23 October 2026

Start with [HPC_HANDOFF.md](HPC_HANDOFF.md). Give [AGENT_START_HERE.md](AGENT_START_HERE.md) to the HPC agent after cloning this repository. The full handoff is in this directory; no separate ZIP download is required.

The readable [task index](TASK_INDEX.md) covers 36 tasks. The detailed queue is [regeneration_tasks.json](regeneration_tasks.json); the short index is [REGENERATION_MATRIX.tsv](REGENERATION_MATRIX.tsv). [TRANSFER_AND_AVAILABILITY.tsv](TRANSFER_AND_AVAILABILITY.tsv) maps named source assets, local availability and included snapshots. Original absolute paths are provenance and must be mapped to the HPC filesystem.

This is a **private working handoff**, not an upload-ready public data release. It includes manuscript/rebuttal drafts, revision notes, and selected existing code and compact checkpoints. The manuscript code is in the parent directory of this handoff. Large sequencing datasets, BAMs, matrices and the four public RData workspaces are not copied into the handoff. Their retained locations or download/recovery tasks are documented.

The audited manuscript-code baseline is commit `3465937aa6a8e51b9f6989e750d45990a2a3d7d6`, retained in this repository’s Git history. Its tracked-file hashes are in `audit/repository_snapshot.json`. A duplicate nested checkout and the transfer ZIP are omitted from this GitHub edition. References to the original handoff’s `rad-manuscript/` mean this repository root at that audited commit. Create implementation changes on a new branch.

`context/` freezes prior notes and documents. Read [AUTHOR_DECISIONS.md](AUTHOR_DECISIONS.md) first because several old notes are superseded. `code_snapshots/` and `checkpoint_snapshots/` preserve explicitly named files, with original paths and SHA-256 digests under `audit/`. They are transport copies, not a claim that the dependency graph is already complete.

From this directory, verify the GitHub handoff files with `sha256sum -c SHA256SUMS` on Linux. The original local transfer-bundle checksums are retained separately as `audit/local_bundle_SHA256SUMS`. Hashes describe byte identity, not scientific validity. The handoff validation report checks task schema/dependencies, source presence and packaging; the HPC tasks specify the scientific validation still required.

## GitHub transport validation

`audit/package_preflight.json` and the original archive reports describe the earlier local ZIP. `audit/github_payload_validation.json` records checks for this GitHub edition. Map original `/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022/hpc_handoff_20261023/rad-manuscript/` paths to the Git repository root and other paths under that handoff root to this directory. Keep original data paths as provenance while resolving their actual HPC locations.
