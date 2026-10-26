#!/usr/bin/env python3
"""Check HD detection-count totals and document different processing stages.

Reads barcode-count tables, not raw sequencing reads; runs no hypothesis tests.
No positions, expression values, or missing bins are imputed.
"""
import argparse,csv,gzip,json,sys
from pathlib import Path
from figures_124 import REPO,sha,rows,write_rows,write_json
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--project-root',type=Path,default=Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data'))
p.add_argument('--output-root',type=Path,default=REPO)
a=p.parse_args();out=a.output_root
base=a.project_root/'raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr'
wide_path=out/'checkpoints/figure_01/sample_bin_matrix_16um.csv.gz';wide=rows(wide_path)
flows=['PBC44593','PBC44760','PBC49262','PBC52788'];result=[]
for flow in flows:
 source=base/'valid_pair_output'/f'{flow}_wl_valid_pairs.csv.gz'
 n=total=0
 with gzip.open(source,'rt') as f:
  for row in csv.DictReader(f):n+=1;total+=int(row['count'])
 count=sum(int(float(r[flow+'_count'])) for r in wide)
 if total!=count:raise ValueError((flow,'detection pair total differs from wide',total,count))
 result.append(dict(flowcell=flow,valid_pair_rows=n,valid_pair_count_total=total,wide_count_total=count,
                    equality='exact total equality; per-bin mapping provenance still incomplete',
                    source_path=str(source),source_sha256=sha(source)))
 print(flow,n,total,'equals wide',flush=True)
write_rows(out/'source_data/figure_01/hd_stage_counts.tsv',result)
cmp_path=base/'uncorrected_spot_counts/per_bin_compare_PBC44593.csv.gz';cmp=rows(cmp_path)
comparison={r['sr16']:r for r in cmp}
differ=sum(int(float(r['PBC44593_count']))!=int(comparison[r['spaceranger_16um']]['rad_demux']) for r in wide if r['spaceranger_16um'] in comparison)
report=dict(status='different_processing_stages; identity-comparison-assumption_rejected',
    command=[sys.executable,*sys.argv],script_sha256=sha(Path(__file__)),
    scientific_scope='Whitelist-detection valid-pair counts versus retained rad_demux counts. Different counting stages cannot be required to agree.',
    wide_source=dict(path=str(wide_path),sha256=sha(wide_path),rows=len(wide),total_PBC44593=45979761),
    detection_sources=result,comparison_source=dict(path=str(cmp_path),sha256=sha(cmp_path),rows=len(cmp),column='rad_demux',total=sum(int(r['rad_demux']) for r in cmp)),
    different_shared_bins=differ,no_values_changed=True,no_statistics_run=True,
    limitation='Matching total does not prove every barcode-to-bin mapping. Full wide-table creation provenance, selected Seurat nCount_Spatial object, and named tissue-position source remain unrecovered. No triptych is rendered.')
write_json(out/'validation/figures_124_hd_lineage.json',report)
