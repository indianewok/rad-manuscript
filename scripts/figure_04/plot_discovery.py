#!/usr/bin/env python3
"""Plot the current Figure 4 barcode-set metrics, retaining all paired inputs."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import tempfile

TOOLS = ['RAD', 'BLAZE', 'Flexiplex']
COLORS = ['#BD704B', '#527B9B', '#6E9878']
METRICS = [('precision', 'Precision'), ('recall', 'Recall'), ('f1', 'F1')]


def read_metrics(path):
    with path.open(newline='') as handle:
        rows = list(csv.DictReader(handle, delimiter='\t'))
    datasets = list(dict.fromkeys(row['canonical_id'] for row in rows))
    by_key = {(row['canonical_id'], row['tool']): row for row in rows}
    if len(rows) != 111 or len(datasets) != 37 or len(by_key) != 111:
        raise ValueError('Expected 37 inputs and exactly three tool observations per input')
    if set(by_key) != {(dataset, tool) for dataset in datasets for tool in TOOLS}:
        raise ValueError('Incomplete tool pairing')
    for row in rows:
        calls, reference, tp, fp, fn = (int(row[key]) for key in ['calls', 'reference_n', 'tp', 'fp', 'fn'])
        if calls != tp + fp or reference != tp + fn or min(tp, fp, fn) < 0:
            raise ValueError('Inconsistent barcode counts: ' + row['canonical_id'])
        expected = [tp / calls if calls else 0, tp / reference, 2 * tp / (calls + reference)]
        if any(abs(float(row[key]) - value) > 1e-9 for (key, _), value in zip(METRICS, expected)):
            raise ValueError('Metric differs from its counts: ' + row['canonical_id'])
    return datasets, by_key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metrics', type=Path, default=Path('source_data/figure_04/barcode_detection_metrics.tsv'))
    parser.add_argument('--output-dir', type=Path, default=Path('figures/figure_04'))
    parser.add_argument('--statistics-dir', type=Path, default=Path('source_data/figure_04'))
    args = parser.parse_args()
    datasets, by_key = read_metrics(args.metrics)
    receipt = json.loads((args.statistics_dir/'statistics.json').read_text())
    if receipt['metrics_sha256'] != hashlib.sha256(args.metrics.read_bytes()).hexdigest():
        raise ValueError('Statistics do not match this metrics table; run statistics.py first')
    expected_settings = {'matched_inputs': 37, 'tools': TOOLS, 'control': 'RAD',
                         'comparisons_per_metric': 2, 'alpha': 0.05}
    if any(receipt['method_settings'].get(key) != value for key, value in expected_settings.items()):
        raise ValueError('Statistics settings differ from the Figure 4 analysis')
    dunn_path = args.statistics_dir/'dunn.tsv'
    if receipt['outputs']['dunn.tsv']['sha256'] != hashlib.sha256(dunn_path.read_bytes()).hexdigest():
        raise ValueError('Dunn results changed after calculation')
    with dunn_path.open(newline='') as handle:
        dunn = list(csv.DictReader(handle, delimiter='\t'))
    tests = {(row['metric'], row['comparator']): row for row in dunn}
    if len(dunn) != 6 or set(tests) != {(key, tool) for key, _ in METRICS for tool in TOOLS[1:]}:
        raise ValueError('Expected two RAD comparisons per metric')
    os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'rad-figure04-matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.size': 10, 'svg.fonttype': 'none', 'pdf.fonttype': 42,
                         'axes.spines.top': False, 'axes.spines.right': False})
    args.output_dir.mkdir(parents=True, exist_ok=True)

    def save(figure, name):
        for extension in ['svg', 'pdf', 'png']:
            target = args.output_dir / (name + '.' + extension)
            figure.savefig(target, dpi=250, bbox_inches='tight')
            if extension == 'svg':
                target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines()) + '\n')
        plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(10, 4.1), constrained_layout=True)
    for axis, (key, title) in zip(axes, METRICS):
        for dataset in datasets:
            axis.plot(range(3), [float(by_key[dataset, tool][key]) for tool in TOOLS],
                      color='#D3D3D3', linewidth=0.55, zorder=1)
        for index, (tool, color) in enumerate(zip(TOOLS, COLORS)):
            values = [float(by_key[dataset, tool][key]) for dataset in datasets]
            axis.scatter([index] * len(values), values, color=color, s=18,
                         edgecolors='white', linewidths=0.25, zorder=2)
            median = float(np.median(values))
            axis.plot([index - 0.18, index + 0.18], [median] * 2, color='black', linewidth=1.7, zorder=3)
        for column, tool in enumerate(TOOLS[1:], 1):
            p_value = float(tests[key, tool]['p_adjusted'])
            if not 0 <= p_value <= 1:
                raise ValueError('Invalid adjusted P-value')
            height = 1.055 + (column-1)*0.105
            axis.plot([0, 0, column, column], [height, height+0.015, height+0.015, height],
                      color='black', linewidth=0.7)
            label = 'P < 0.0001' if p_value < 0.0001 else f'P = {p_value:.4f}'
            axis.text(column/2, height+0.023, label, ha='center', fontsize=8)
        axis.set(xticks=range(3), xticklabels=TOOLS, ylim=(-0.035, 1.245),
                 yticks=[0, 0.25, 0.5, 0.75, 1], xlim=(-0.45, 2.45), ylabel=title)
    save(figure, 'barcode_discovery_paired')

    # The displayed values make individual datasets inspectable in GitHub.
    figure, axes = plt.subplots(1, 3, figsize=(12.5, 12), constrained_layout=True)
    for index, (axis, (key, title)) in enumerate(zip(axes, METRICS)):
        values = np.array([[float(by_key[dataset, tool][key]) for tool in TOOLS] for dataset in datasets])
        axis.imshow(values, cmap='YlGnBu', vmin=0, vmax=1, aspect='auto')
        axis.set(xticks=range(3), xticklabels=TOOLS, yticks=range(len(datasets)),
                 yticklabels=datasets if index == 0 else [], title=title)
        axis.tick_params(axis='y', length=0, labelsize=8)
        axis.tick_params(axis='x', bottom=False, top=True, labelbottom=False, labeltop=True)
        for row in range(len(datasets)):
            for column in range(3):
                value = values[row, column]
                axis.text(column, row, f'{value:.3f}', ha='center', va='center', fontsize=8,
                          color='white' if value >= 0.65 else 'black')
        for boundary in np.arange(0.5, len(datasets), 1):
            axis.axhline(boundary, color='white', linewidth=0.3)
        for spine in axis.spines.values():
            spine.set_visible(False)
    save(figure, 'barcode_discovery_by_input')
    print(f'Plotted {len(datasets)} paired inputs from {args.metrics}')


if __name__ == '__main__':
    main()
