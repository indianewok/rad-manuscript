# HPC handback template

Use this structure when returning work. Include both the readable report and machine-readable status/validation records.

## Run identity

- Manuscript analysis/release ID:
- Code repository and commit, including local patch hash:
- HPC project root and path-map/config hash:
- Environment/container identities:
- Work performed and date:

## Task status

| Task ID | Status | Earliest input/checkpoint used | Outputs and hashes | Validation report | Difference/decision/next step |
|---|---|---|---|---|---|
| | planned / ready / running / passed / changed-result-review / blocked-missing-asset / blocked-author-decision | | | | |

Use the task IDs in `regeneration_tasks.json`. A task can have a partial handback; name the completed substeps and remaining gate.

## Panel reproducibility

| Figure/panel | Selected experiment | Render from source data | Resume from checkpoint | Raw rerun | Canonical result comparison | Native Prism QA |
|---|---|---|---|---|---|---|
| | | passed / failed / not run | passed / failed / not run | full passed / full failed / pilot only / not run | exact / within declared tolerance / changed / unresolved | passed / pending desktop / not applicable |

Record count units, denominators, tested universes and statistical observation units. For replacement experiments, include a historical-versus-new comparison and the decision that selects the canonical result.

## Discrepancies requiring a decision

For each discrepancy, give the affected task/panel, old result/source, regenerated result/source, identified cause, scientific consequence, and concrete proposed resolution. Attach the evidence needed to decide. Do not request reconfirmation of settled author choices.

## Release readiness

- Source data and schemas:
- Editable and final figure exports:
- Methods/Results/legend/rebuttal evidence mapping:
- Data access and permitted redistribution:
- Zenodo metadata/DOI reconciliation:
- Clean-environment validation:
- Checksum verification:
- Remaining desktop/author actions:
- Proposed upload-ready artifact inventory:

Publishing status: staged for review / author-approved / published (with verified links). Do not label a staged release as published.
