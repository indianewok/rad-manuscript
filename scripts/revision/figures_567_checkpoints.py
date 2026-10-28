#!/usr/bin/env python3
"""Single-thread full-content validation of retained expression/genotype checkpoints.

This reads existing matrices, variants, and labels; it does not rerun alignment,
CellSNP, Vireo, or differential expression.
"""
import argparse
from array import array
import collections
import csv
import gzip
import hashlib
import json
from pathlib import Path
from source_paths import reviewer_root
import sys
import numpy as np
from figures_567 import sha, read, write


def lines(path):
    return gzip.open(str(path),'rt') if str(path).endswith('.gz') else path.open()


def matrix(path):
    with lines(path) as f:
        assert f.readline().startswith('%%MatrixMarket matrix coordinate integer general')
        line = next(f)
        while line.startswith('%'):line=next(f)
        nr,nc,nnz=map(int,line.split())
        rows,cols=[0]*nr,[0]*nc
        n,total=0,0
        # Matrix Market permits arbitrary ordering. Verify uniqueness independently.
        keys=array('Q')
        for line in f:
            i,j,v=map(int,line.split())
            assert 1<=i<=nr and 1<=j<=nc and v>0, (path,n,i,j,v)
            keys.append((j-1)*nr+i-1)
            n+=1;total+=v;rows[i-1]+=v;cols[j-1]+=v
        assert n==nnz,(path,n,nnz)
        assert len(np.unique(np.frombuffer(keys,dtype=np.uint64)))==nnz, ('duplicate coordinates',path)
    return dict(rows=nr,columns=nc,nnz=nnz,total=total,positive_columns=sum(x>0 for x in cols)),cols


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project-root',type=Path,default=reviewer_root())
    p.add_argument('--output-root',type=Path,default=Path(__file__).resolve().parents[2])
    a=p.parse_args();project=a.project_root;out=a.output_root
    checks=[];assets=[];cohorts=[]
    def asset(path,role):
        assets.append(dict(path=str(path),role=role,bytes=path.stat().st_size,sha256=sha(path)))
    def test(name,condition,observed):
        checks.append(dict(check_id=name,status='passed' if condition else 'failed',observed=observed))
        assert condition,(name,observed)
    try:
        base=project/'LongBench_comps/SN_ONT_H146_H526_fullcohort_DEG_20260822'
        seals={line[66:].strip().lstrip('*'):line[:64] for line in (base/'SHA256SUMS').read_text().splitlines()}
        for tool in ('RAD','BLAZE','Flexiplex'):
            folder=base/'inputs/native'/tool/'all'
            path=folder/'matrix.mtx.gz';stats,depth=matrix(path)
            historical=json.loads((folder/'matrix_stats.json').read_text())
            actual={'n_cells':stats['columns'],'n_genes':stats['rows'],'n_nonzero':stats['nnz'],'total_umis':stats['total']}
            test('F7_'+tool+'_matrix_counts',all(historical[k]==v for k,v in actual.items()),actual)
            features=[x.rstrip('\n').split('\t')[0] for x in lines(folder/'features.tsv.gz')]
            barcodes=[x.strip().removesuffix('-1') if sys.version_info>=(3,9) else x.strip()[:-2] if x.strip().endswith('-1') else x.strip() for x in lines(folder/'barcodes.tsv.gz')]
            test('F7_'+tool+'_matrix_keys',len(features)==stats['rows'] and len(barcodes)==stats['columns'] and len(set(features))==len(features) and len(set(barcodes))==len(barcodes),{'features':len(features),'barcodes':len(barcodes)})
            labels=read(base/'inputs/labels'/tool/'donor_ids.tsv');ld={r['cell'].removesuffix('-1') if sys.version_info>=(3,9) else r['cell'][:-2] if r['cell'].endswith('-1') else r['cell']:r['donor_id'] for r in labels}
            named={'H146','H1975','H211','H2228','H526','H69','HCC827','SHP77'}
            tool_cohort=[]
            for b,d in zip(barcodes,depth):
                label=ld.get(b,'missing_row')
                if label in named and d>0:
                    tool_cohort.append(dict(tool=tool,cell_barcode=b,donor=label,full_library_molecules=d))
            test('F7_'+tool+'_positive_native_named_cohort',len(tool_cohort)=={'RAD':9404,'BLAZE':6478,'Flexiplex':7125}[tool],len(tool_cohort))
            cohorts.extend(tool_cohort)
            for path in (folder/'matrix.mtx.gz',folder/'barcodes.tsv.gz',folder/'features.tsv.gz',base/'inputs/labels'/tool/'donor_ids.tsv'):
                asset(path,'native_expression_matrix_or_labels')
                relative=str(path.relative_to(base))
                test('F7_'+tool+'_'+path.name+'_sealed_hash',seals.get(relative)==assets[-1]['sha256'],assets[-1]['sha256'])
            print(tool+' native matrix checked',flush=True)
        write(out/'source_data/figure_07/native_positive_depth_cohorts.tsv',cohorts)
        panelbase=project/'LongBench_comps/SN_ONT_RAD_bulk_cellline_bundle_20260803'
        vcf=panelbase/'bulk_donor_panel/final/fixed_8line_bulk_illumina_donor_panel.vcf.gz'
        variants=set();variant_lines={};duplicate_rows=[];donors=[];n=0
        with gzip.open(str(vcf),'rt') as f:
            for line in f:
                if line.startswith('#CHROM'):
                    donors=line.rstrip('\n').split('\t')[9:]
                elif not line.startswith('#'):
                    r=line.rstrip('\n').split('\t');n+=1
                    assert len(r)==17 and int(r[1])>0 and len(r[3])==len(r[4])==1
                    key=tuple(r[i] for i in (0,1,3,4))
                    if key in variants:
                        # Preserve the historical panel; row identity includes ordinal.
                        assert variant_lines[key][1]==line, ('conflicting duplicate variant',key)
                        duplicate_rows.append(dict(chrom=key[0],position=key[1],ref=key[2],alt=key[3],first_record=variant_lines[key][0],duplicate_record=n,identical_record=True,policy='retained unchanged; historical panel identity includes record ordinal'))
                    else:variant_lines[key]=(n,line)
                    variants.add(key)
                    assert 'GT' in r[8].split(':')
        test('F6_donor_panel_sites',n==360814,n)
        test('F6_donor_panel_known_identical_duplicate_rows',len(duplicate_rows)==5,{'records':n,'unique_variant_keys':len(variants),'identical_duplicate_rows':len(duplicate_rows),'warning':'360814 is record count; 360809 unique keys. Historical panel preserved without deduplication.'})
        write(out/'source_data/figure_06/donor_panel_duplicate_records.tsv',duplicate_rows)
        test('F6_donor_panel_order',donors==['H146','H1975','H211','H2228','H526','H69','HCC827','SHP77'],donors)
        asset(vcf,'bulk_donor_panel');asset(Path(str(vcf)+'.tbi'),'bulk_donor_panel_index')
        reference=project/'reviewer_response_20260804/objects/longbench/durable_sources/SN_ONT_cross_tool_vireo_20260804/primary_inputs/Illumina_reference/donor_ids.tsv'
        rebuilt=panelbase/'bulk_donor_panel/validation/ill_sn_vireo/donor_ids.tsv'
        ref={r['cell']:r['donor_id'] for r in read(reference)};new={r['cell']:r['donor_id'] for r in read(rebuilt)}
        test('F6_all_Illumina_hard_calls_reproduced',ref==new and len(ref)==12012,{'released':len(ref),'rebuilt':len(new),'different':sum(ref.get(k)!=new.get(k) for k in set(ref)|set(new))})
        asset(reference,'released_Illumina_labels');asset(rebuilt,'reconstructed_panel_Illumina_labels')
        write(out/'source_data/figure_06/donor_panel_validation.tsv',[dict(donor_order=i+1,donor=t,panel_sites=n,Illumina_exact_hard_calls=12012) for i,t in enumerate(donors)])
        # Validate CellSNP dimensions, positive integer counts and variant identities.
        scratch=project/'scratch_preservation_20260921/files/longbench_snont_postdemux_vireo_20260803'
        dirs={'RAD':panelbase/'RAD/cellsnp','Flexiplex':scratch/'cellsnp/Flexiplex','BLAZE':scratch/'rebuilds/BLAZE_rebuilt_bulk_panel_tool_postdemux_20260804T135956Z/cellsnp'}
        records=[]
        for tool,folder in dirs.items():
            bcs=[x.strip() for x in (folder/'cellSNP.samples.tsv').open()]
            sites=[]
            with gzip.open(str(folder/'cellSNP.base.vcf.gz'),'rt') as f:
                for line in f:
                    if line.startswith('#'):continue
                    r=line.split('\t');sites.append(tuple(r[i] for i in (0,1,3,4)))
            duplicate_sites=[k for k,count in collections.Counter(sites).items() if count>1]
            known_duplicate_sites={tuple(str(r[k]) for k in ('chrom','position','ref','alt')) for r in duplicate_rows}
            test('F6_'+tool+'_sites_match_panel',set(sites)<=variants and set(duplicate_sites)<=known_duplicate_sites,{'query_records':len(sites),'query_unique_variant_keys':len(set(sites)),'not_in_panel':len(set(sites)-variants),'duplicate_policy':'retain row order; duplicates must exist in historical donor panel'})
            write(out/('source_data/figure_06/'+tool+'_cellsnp_duplicate_variant_rows.tsv'),[dict(row_index=i+1,chrom=k[0],position=k[1],ref=k[2],alt=k[3]) for i,k in enumerate(sites) if k in duplicate_sites],fields=['row_index','chrom','position','ref','alt'])
            test('F6_'+tool+'_barcodes_unique',len(set(bcs))==len(bcs) and len(bcs)=={'RAD':12423,'BLAZE':10001,'Flexiplex':12101}[tool],len(bcs))
            for typ in ('AD','DP'):
                path=folder/('cellSNP.tag.'+typ+'.mtx');stats,depth=matrix(path)
                test('F6_'+tool+'_'+typ+'_dimensions',stats['rows']==len(sites) and stats['columns']==len(bcs),stats)
                asset(path,'cellsnp_'+typ);records.append(dict(tool=tool,matrix=typ,**stats))
            asset(folder/'cellSNP.base.vcf.gz','cellsnp_variant_order');asset(folder/'cellSNP.samples.tsv','cellsnp_barcode_order')
            print(tool+' CellSNP checked',flush=True)
        write(out/'source_data/figure_06/cellsnp_matrix_summary.tsv',records)
    finally:
        write(out/'validation/figures_567_checkpoint_checks.tsv',checks)
        write(out/'manifests/figures_567_checkpoint_assets.tsv',assets)
    print('Passed '+str(len(checks))+' full-content checkpoint checks',flush=True)


if __name__=='__main__':main()
