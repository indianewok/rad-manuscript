#!/usr/bin/env python3
"""Plot Figure 2 discovery and assignment tables without processing other figures."""
import argparse
import csv
import os
from pathlib import Path
import tempfile

TOOLS = ('RAD', 'BLAZE', 'Flexiplex')
STATES = ('native_correct', 'corrected_correct', 'corrected_incorrect', 'native_incorrect', 'unassigned')
COLORS = {'RAD':'#A3392C', 'BLAZE':'#336B87', 'Flexiplex':'#568A55',
          'Flexiplex_f0':'#94A66F', 'Flexiplex_f8':'#568A55'}
NREADS = 4993805


def rows(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))


def render(source_dir, output_dir):
    args = argparse.Namespace(source_dir=Path(source_dir), output_dir=Path(output_dir))
    sweeps = rows(args.source_dir/'discovery_metrics.tsv')
    states = rows(args.source_dir/'assignment_states.tsv')
    correction = rows(args.source_dir/'correction_only.tsv')
    if len(sweeps) != 144:
        raise ValueError('Expected the complete 144-row discovery grid')
    for tool in TOOLS:
        group = [row for row in states if row['tool'] == tool]
        if len(group) != 5 or {row['state'] for row in group} != set(STATES):
            raise ValueError('Expected five assignment states for '+tool)
        if sum(int(row['reads']) for row in group) != NREADS:
            raise ValueError('Assignment states do not conserve all input reads')
        for row in group:
            if int(row['denominator']) != NREADS or abs(float(row['fraction'])-int(row['reads'])/NREADS) > 1e-12:
                raise ValueError('Assignment fraction differs from its counts')
        corrected = {row['state']:row for row in correction if row['tool'] == tool}
        if set(corrected) != {'corrected_correct','corrected_incorrect'}:
            raise ValueError('Expected two correction-only states for '+tool)
        denominator = sum(int(row['reads']) for row in corrected.values())
        for row in corrected.values():
            if int(row['denominator']) != denominator or abs(float(row['fraction'])-int(row['reads'])/denominator) > 1e-12:
                raise ValueError('Correction-only fraction differs from its counts')
    os.environ.setdefault('MPLCONFIGDIR', tempfile.mkdtemp(prefix='rad_figure02_matplotlib_'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.size':9, 'axes.spines.top':False, 'axes.spines.right':False,
                         'svg.fonttype':'none', 'pdf.fonttype':42, 'axes.titlesize':10,
                         'svg.hashsalt':'rad-manuscript-figure02'})
    args.output_dir.mkdir(parents=True, exist_ok=True)

    def save(figure, name):
        for extension in ('png', 'svg', 'pdf'):
            target = args.output_dir/(name+'.'+extension)
            figure.savefig(target, dpi=180, bbox_inches='tight')
            if extension == 'svg':
                target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines())+'\n')
        plt.close(figure)

    fig, axes = plt.subplots(1, 3, figsize=(11,3.5), constrained_layout=True)
    for axis, (dataset, model) in zip(axes, (('S','nanopore2018'),('L','nanopore2018'),('L','nanopore2023'))):
        for tool in ('RAD','BLAZE','Flexiplex_f0','Flexiplex_f8'):
            group = sorted([row for row in sweeps if (row['dataset'],row['model'],row['tool']) == (dataset,model,tool)],
                           key=lambda row:float(row['full_dataset_mean_Q']))
            axis.plot([float(row['full_dataset_mean_Q']) for row in group], [float(row['f1']) for row in group],
                      '.-', label=tool, color=COLORS[tool])
        axis.set_title(f'ScTagger-{dataset}: {model}')
        axis.set_xlabel('Whole-dataset mean base quality')
        axis.set_ylabel('Barcode discovery F1')
        axis.set_ylim(-.03,1.03)
    axes[0].legend(frameon=False, fontsize=8)
    save(fig, 'quality_discovery_sweeps')

    fig, axes = plt.subplots(1, 2, figsize=(9,4), constrained_layout=True)
    state_colors = ['#4A6F91','#74A889','#C78350','#B64A49','#DDDDDD']
    bottom = np.zeros(3)
    for state, color in zip(STATES, state_colors):
        values = np.array([float(next(row['fraction'] for row in states if row['tool'] == tool and row['state'] == state)) for tool in TOOLS])
        axes[0].bar(TOOLS, values, bottom=bottom, label=state.replace('_',' '), color=color)
        bottom += values
    axes[0].set_ylabel('Fraction of all 4,993,805 physical reads')
    axes[0].legend(fontsize=7, frameon=False, loc='upper center', bbox_to_anchor=(.5,-.1), ncol=2)
    for index, tool in enumerate(TOOLS):
        fraction = float(next(row['fraction'] for row in correction if row['tool'] == tool and row['state'] == 'corrected_incorrect'))
        axes[1].bar(tool, 100*fraction, color=COLORS[tool])
        axes[1].text(index, 100*fraction+.3, f'{100*fraction:.2f}%', ha='center', fontsize=8)
    axes[1].set_ylabel('Incorrect among corrected assignments (%)')
    axes[1].set_ylim(0,20)
    save(fig, 'assignment_descriptive')


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=root/'source_data/figure_02')
    parser.add_argument('--output-dir', type=Path, default=root/'figures/figure_02')
    args = parser.parse_args()
    render(args.source_dir, args.output_dir)


if __name__ == '__main__':
    main()
