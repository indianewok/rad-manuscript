# scripts/

Repo-management utilities. These are **not** part of the figure pipeline — they're one-shot tools for preparing the manuscript artifact for release.

| Script | Purpose |
|--------|---------|
| `zenodo_upload.sh` | Upload the four `.RData` workspaces to Zenodo as a private draft and reserve a DOI. See header comment for usage. |

## `zenodo_upload.sh`

One-time setup:

1. Create a Zenodo personal access token at
   [zenodo.org/account/settings/applications/tokens/new/](https://zenodo.org/account/settings/applications/tokens/new/)
   with scopes `deposit:write` and `deposit:actions`.
2. `export ZENODO_TOKEN=...` in the shell you'll run the script from.

Run modes:

```bash
# Smoke test — create the draft + metadata, skip the 5.8 GB upload
./scripts/zenodo_upload.sh --dry-run

# Full upload
./scripts/zenodo_upload.sh

# Upload was interrupted — resume by reusing the deposit ID printed last time
ZENODO_DEPOSIT_ID=123456 ./scripts/zenodo_upload.sh
```

The script leaves the deposit in **draft** state (private to your Zenodo account). The DOI is reserved at creation time so it can be cited in the manuscript ahead of publication. To make the files publicly accessible, open the printed edit URL and click "Publish" — or set restricted-access / embargo first.
