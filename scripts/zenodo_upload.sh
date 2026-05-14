#!/usr/bin/env bash
# =============================================================================
# zenodo_upload.sh — upload .RData workspaces to Zenodo as a private draft
# =============================================================================
# Creates a draft deposit (private to your account), reserves a DOI, uploads
# the four .RData workspaces via the bucket API, then leaves the deposit
# UNPUBLISHED so you can review on Zenodo before flipping it public/restricted.
#
# Usage:
#   export ZENODO_TOKEN=...                  # from zenodo.org/account/settings/applications/
#   ./scripts/zenodo_upload.sh               # full run
#   ./scripts/zenodo_upload.sh --dry-run     # create draft + metadata, skip uploads
#   ZENODO_DEPOSIT_ID=123456 ./scripts/zenodo_upload.sh   # resume upload to existing draft
#
# After it finishes:
#   1. Open the printed edit URL in your browser
#   2. Verify metadata, files, and reserved DOI
#   3. Click "Save" (still draft) — or "Publish" when the paper is accepted
# =============================================================================
set -euo pipefail

API="https://zenodo.org/api"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DRY_RUN="false"

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN="true" ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

# ---------- prerequisites ----------------------------------------------------
if [ -z "${ZENODO_TOKEN:-}" ]; then
  echo "ERROR: ZENODO_TOKEN not set. Create one at:"
  echo "  https://zenodo.org/account/settings/applications/tokens/new/"
  echo "Required scopes: deposit:write deposit:actions"
  exit 1
fi

FILES=(
  "${REPO_ROOT}/figure_2/figure_2_workspace.RData"
  "${REPO_ROOT}/figure_3/figure_3_workspace.RData"
  "${REPO_ROOT}/figure_4/figure_4_workspace.RData"
  "${REPO_ROOT}/figure_5/figure_5_workspace.RData"
)
for f in "${FILES[@]}"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: missing $f"; exit 1
  fi
done

command -v jq   >/dev/null || { echo "ERROR: jq not found (brew install jq)";   exit 1; }
command -v curl >/dev/null || { echo "ERROR: curl not found";                   exit 1; }

# Local MD5 for upload verification (Zenodo returns md5, not sha256)
md5_local() {
  if command -v md5sum >/dev/null; then md5sum "$1" | awk '{print $1}'
  else md5 -q "$1"
  fi
}

# ---------- metadata ---------------------------------------------------------
METADATA=$(cat <<'EOF'
{
  "metadata": {
    "title": "RAD manuscript — R workspaces for figure generation",
    "upload_type": "dataset",
    "description": "<p>R workspace files (<code>.RData</code>) containing all intermediate and final analysis objects used to produce Figures 2–5 of the RAD manuscript (Vaidya et al., 2026, in preparation).</p><p>Each <code>figure_N_workspace.RData</code> corresponds to one figure and is consumed by the matching R Markdown notebook in the companion GitHub repository <a href=\"https://github.com/indianewok/rad-manuscript\">indianewok/rad-manuscript</a>.</p><p>Loading a workspace restores all named objects referenced by the figure's Rmd, allowing the figures to be rendered without the underlying raw FASTQ data. SHA-256 checksums and per-workspace contents are documented in <code>data/README.md</code> of the GitHub repo.</p>",
    "creators": [
      {
        "name": "Vaidya, Chinmay M.",
        "affiliation": "Geisel School of Medicine at Dartmouth",
        "orcid": ""
      }
    ],
    "keywords": [
      "single-cell sequencing",
      "long-read sequencing",
      "Oxford Nanopore",
      "barcode demultiplexing",
      "immune receptor",
      "B-cell receptor",
      "spatial transcriptomics",
      "RAD",
      "reproducibility"
    ],
    "access_right": "open",
    "license": "CC-BY-4.0",
    "related_identifiers": [
      {
        "identifier": "https://github.com/indianewok/rad-manuscript",
        "relation": "isSupplementTo",
        "resource_type": "software"
      },
      {
        "identifier": "https://github.com/indianewok/rad",
        "relation": "isSupplementTo",
        "resource_type": "software"
      }
    ],
    "prereserve_doi": true
  }
}
EOF
)

# ---------- create or resume deposit ----------------------------------------
if [ -n "${ZENODO_DEPOSIT_ID:-}" ]; then
  echo ">> Resuming existing deposit ${ZENODO_DEPOSIT_ID}..."
  DEPOSIT_JSON=$(curl -fsS -H "Authorization: Bearer ${ZENODO_TOKEN}" "${API}/deposit/depositions/${ZENODO_DEPOSIT_ID}")
else
  echo ">> Creating new draft deposit on zenodo.org..."
  DEPOSIT_JSON=$(curl -fsS -X POST \
    -H "Authorization: Bearer ${ZENODO_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{}' \
    "${API}/deposit/depositions")
fi

DEPOSIT_ID=$(echo "$DEPOSIT_JSON" | jq -r '.id')
BUCKET_URL=$(echo "$DEPOSIT_JSON" | jq -r '.links.bucket')
EDIT_URL=$(echo  "$DEPOSIT_JSON" | jq -r '.links.html')

if [ -z "$DEPOSIT_ID" ] || [ "$DEPOSIT_ID" = "null" ]; then
  echo "ERROR: failed to create/resume deposit. Response:"; echo "$DEPOSIT_JSON" | jq .
  exit 1
fi
echo "   Deposit ID:  ${DEPOSIT_ID}"
echo "   Bucket URL:  ${BUCKET_URL}"
echo "   Edit URL:    ${EDIT_URL}"

# ---------- attach metadata --------------------------------------------------
echo ">> Setting metadata (title, description, creators, prereserve DOI)..."
META_RESPONSE=$(curl -fsS -X PUT \
  -H "Authorization: Bearer ${ZENODO_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$METADATA" \
  "${API}/deposit/depositions/${DEPOSIT_ID}")

RESERVED_DOI=$(echo "$META_RESPONSE" | jq -r '.metadata.prereserve_doi.doi // empty')
echo "   Reserved DOI: ${RESERVED_DOI:-<not assigned>}"

# ---------- upload files (skip ones already present) ------------------------
if [ "$DRY_RUN" = "true" ]; then
  echo ">> --dry-run: skipping uploads"
else
  EXISTING_FILES=$(echo "$DEPOSIT_JSON" | jq -r '.files[]?.filename' || true)
  for f in "${FILES[@]}"; do
    name=$(basename "$f")
    if echo "$EXISTING_FILES" | grep -qx "$name"; then
      echo ">> Skipping ${name} (already on Zenodo)"
      continue
    fi
    size=$(du -h "$f" | awk '{print $1}')
    echo ">> Uploading ${name} (${size})..."
    local_md5=$(md5_local "$f")
    UPLOAD_RESPONSE=$(curl -fsS --progress-bar \
      --upload-file "$f" \
      -H "Authorization: Bearer ${ZENODO_TOKEN}" \
      "${BUCKET_URL}/${name}")
    remote_md5=$(echo "$UPLOAD_RESPONSE" | jq -r '.checksum' | sed 's/^md5://')
    if [ "$local_md5" = "$remote_md5" ]; then
      echo "   [OK] md5 verified (${remote_md5})"
    else
      echo "   [WARN] md5 mismatch — local=${local_md5} remote=${remote_md5}" >&2
    fi
  done
fi

# ---------- summary ----------------------------------------------------------
cat <<EOF

============================================================
 Done. Deposit is in DRAFT state (private to your account).
============================================================
 Edit URL:        ${EDIT_URL}
 Reserved DOI:    ${RESERVED_DOI:-<reserved via web UI>}
 Resume token:    export ZENODO_DEPOSIT_ID=${DEPOSIT_ID}

Next:
  1. Open the edit URL and verify files + metadata.
  2. Update data/README.md — replace the placeholder DOI with: ${RESERVED_DOI:-<DOI>}
  3. Leave as draft until paper acceptance.
  4. On acceptance: open the deposit and click "Publish".
EOF
