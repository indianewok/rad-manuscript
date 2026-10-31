#!/usr/bin/env python3
"""Recalculate the four Figure 7C free-intercept OLS fits from plotted points."""
import argparse
import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=Path('source_data/figure_07/plotted'))
    parser.add_argument('--output', type=Path, default=Path('results/figure07_panel_c_fits.tsv'))
    parser.add_argument('--report', type=Path, default=Path('results/figure07_panel_c_fits.json'))
    args = parser.parse_args()
    groups = defaultdict(list)
    with gzip.open(args.source_dir/'panel_B_C_points.tsv.gz','rt') as source:
        for row in csv.DictReader(source, delimiter='\t'):
            if row['panel'].startswith('panel_C_'):
                groups[row['panel'], row['series']].append((float(row['x']), float(row['y'])))
    output = []
    maximum_error = 0.0
    for (panel, series), points in sorted(groups.items()):
        n = len(points)
        mean_x = sum(x for x, _ in points)/n
        mean_y = sum(y for _, y in points)/n
        ss_x = sum((x-mean_x)**2 for x, _ in points)
        ss_y = sum((y-mean_y)**2 for _, y in points)
        ss_xy = sum((x-mean_x)*(y-mean_y) for x, y in points)
        slope = ss_xy/ss_x
        intercept = mean_y-slope*mean_x
        r2 = ss_xy*ss_xy/(ss_x*ss_y)
        models = json.loads((args.source_dir/(panel+'_regression_results.json')).read_text())['content']['models']
        model = next(value for value in models.values() if value['id']['col']['title']==series)
        expected = model['value']['model']
        errors = [abs(slope-expected['parameters']['Slope']['estimate']),
                  abs(intercept-expected['parameters']['Y-intercept']['estimate']),
                  abs(r2-expected['goodnessOfFit']['r2'])]
        maximum_error = max(maximum_error,*errors)
        if max(errors)>1e-8 or n!=model['value']['dataSummary']['pointsAnalyzed']:
            raise ValueError('Plotted regression differs from saved Prism result: '+panel+' '+series)
        output.append(dict(panel=panel,series=series,n=n,slope=slope,intercept=intercept,r2=r2))
    if len(output)!=4:
        raise ValueError('Expected four Figure 7C fits')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('w',newline='') as target:
        writer=csv.DictWriter(target,delimiter='\t',fieldnames=['panel','series','n','slope','intercept','r2'],lineterminator='\n')
        writer.writeheader();writer.writerows(output)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(dict(status='PASS',fits=4,max_absolute_error=maximum_error),indent=2)+'\n')
    print(json.dumps(dict(status='PASS',fits=output,max_absolute_error=maximum_error),indent=2))


if __name__=='__main__':
    main()
