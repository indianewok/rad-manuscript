#!/usr/bin/env python3
"""Run the two small assignment aggregators and exact selected-table comparison."""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    a=p.parse_args();root=a.root.resolve();scripts=Path(__file__).resolve().parent
    subprocess.run([sys.executable,str(scripts/'check_component_normalization.py'),
        '--native',str(root/'checkpoints/figure_05/component_polyT_native_stats.tsv.gz'),
        '--normalized',str(root/'checkpoints/figure_05/component_polyT_assignments.tsv.gz'),
        '--report',str(root/'validation/figure_05_component_normalization.json')],check=True)
    with tempfile.TemporaryDirectory(prefix='rad_selected_splitseq_') as tmp:
        tmp=Path(tmp)
        for tool,name in [('rad','RAD_ED2_assignments.tsv.gz'),('component','component_polyT_assignments.tsv.gz')]:
            subprocess.run([sys.executable,str(scripts/'aggregate_splitseq.py'),
                '--assignments',str(root/'checkpoints/figure_05'/name),
                '--cells',str(root/'data/figure_05/splitseq_cells.tsv'),
                '--rt-primers',str(root/'data/figure_05/rt_primer_well_map.csv'),
                '--format',tool,'--output',str(tmp/(tool+'.tsv')),
                '--report',str(root/f'validation/figure_05_{tool}_aggregation.json')],check=True)
        subprocess.run([sys.executable,str(scripts/'verify_splitseq_counts.py'),
            '--expected',str(root/'source_data/figure_05/splitseq_reads_umis_568.tsv'),
            '--rad-counts',str(tmp/'rad.tsv'),'--component-counts',str(tmp/'component.tsv'),
            '--rad-report',str(root/'validation/figure_05_rad_aggregation.json'),
            '--component-report',str(root/'validation/figure_05_component_aggregation.json'),
            '--input-reads','5764421','--summary',str(root/'source_data/figure_05/splitseq_summary.tsv'),
            '--report',str(root/'validation/figure_05_splitseq_counts.json')],check=True)

if __name__=='__main__':main()
