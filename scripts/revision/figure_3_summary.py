#!/usr/bin/env python3
"""Describe the three selected supplied-list draws without hypothesis tests."""
import json
from pathlib import Path
from figure_3 import ROOT, DATASETS, TOOLS, read, write, sha, js


def main():
    source = ROOT / 'source_data/figure_03/offlist_totals.tsv'
    rows = read(source)
    assert len(rows) == 27
    summaries = []
    for dataset in DATASETS:
        for tool in TOOLS:
            arm = sorted((r for r in rows if r['dataset'] == dataset and r['tool'] == tool),
                         key=lambda r: int(r['replicate']))
            assert [int(r['replicate']) for r in arm] == [1, 2, 3]
            assert len({r['input_reads'] for r in arm}) == 1
            assert len({r['target_count'] for r in arm}) == 1
            n, targets = int(arm[0]['input_reads']), int(arm[0]['target_count'])
            counts = [int(r['assigned_count']) for r in arm]
            fractions = [c / n for c in counts]
            assert all(abs(float(r['assignment_fraction']) - f) < 1e-12
                       for r, f in zip(arm, fractions))
            mean = sum(counts) / 3
            summaries.append(dict(
                dataset=dataset, tool=tool, input_physical_reads=n,
                targets_per_list=targets, technical_list_draws=3,
                assigned_rep1=counts[0], assigned_rep2=counts[1], assigned_rep3=counts[2],
                assigned_mean=mean, assigned_min=min(counts), assigned_max=max(counts),
                assignment_fraction_mean=mean/n,
                assignment_fraction_min=min(fractions), assignment_fraction_max=max(fractions),
                assignment_percent_mean=100*mean/n,
                assignment_percent_min=100*min(fractions),
                assignment_percent_max=100*max(fractions),
                mean_assigned_per_target=mean/targets,
                mean_assigned_per_target_min=min(counts)/targets,
                mean_assigned_per_target_max=max(counts)/targets))
    output = ROOT / 'validation/figure_3_offlist_metric_summary.tsv'
    write(output, summaries)
    report = dict(status='passed', source=str(source.relative_to(ROOT)),
                  source_sha256=sha(source), output_sha256=sha(output),
                  numerator='Physical input reads with exactly one assignment row to a supplied false-list target; all rows of multiply assigned IDs are excluded',
                  denominator='Every physical read in the complete input, including unassigned and ambiguous reads',
                  display='100 * numerator / denominator',
                  range='Minimum and maximum over three technical list draws; not a confidence interval',
                  statistics='Descriptive arithmetic only; no new hypothesis tests',
                  summaries=summaries)
    js(ROOT / 'validation/figure_3_offlist_metric_summary.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
