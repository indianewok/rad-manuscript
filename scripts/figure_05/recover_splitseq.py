#!/usr/bin/env python3
"""Promote selected current LR-Split-seq sources from the validated upload.

The original upload stays external. Only RAD ED2 and component poly-T outputs
enter current tables; older comparison columns are used only for identity QA.
"""
import argparse
import csv
import gzip
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RECOVERY=Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data/paper_revision_20261022/lr_splitseq_recovery_20261023')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def read(path):
    with path.open() as f:return list(csv.DictReader(f,delimiter=',' if path.suffix=='.csv' else '\t'))


def write(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--recovery-root',type=Path,default=RECOVERY/'package')
    p.add_argument('--full-rad-ledger',type=Path,default=RECOVERY/'external_checkpoints/rad_ed2_all_assignments_normalized.tsv.gz')
    p.add_argument('--output-root',type=Path,default=ROOT)
    a=p.parse_args();r=a.recovery_root;o=a.output_root;assets=[]
    def record(path,role,output='',selection='byte-identical selected evidence'):
        assets.append(dict(source_path=str(path),source_sha256=sha(path),source_bytes=path.stat().st_size,
                           role=role,output=output,selection=selection))
    def copy(src,dst,role):
        dst=o/dst;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
        record(src,role,str(dst.relative_to(o)))
    master=read(r/'reference/published_568_barcode_map.csv')
    keyed=read(r/'tables/splitseq_published_barcode_read_counts.csv')
    prism_path=r/'prism/native_components/data/tables/954A959E-2630-403B-89C7-8EEBAF7A986A/data.csv'
    with prism_path.open() as f:prism=list(csv.reader(f))
    columns=['rad_ed2_assigned_reads','flex_component_no_polyt_assigned_reads','flex_component_polyt_assigned_reads',
             'flames_matched_split_polyt_assigned_reads','flames_historical_two_pass_assigned_reads','rad_ed2_assigned_reads']
    assert len(master)==len(keyed)==len(prism)==568
    assert prism==[[row[c] for c in columns] for row in keyed]
    assert [int(row['published_rank']) for row in keyed]==list(range(1,569))
    assert len({x['canonical_barcode'] for x in keyed})==len({x['published_cell_barcode'] for x in keyed})==568
    assert all({k:row[k] for k in master[0]}==m for row,m in zip(keyed,master))
    rt=read(r/'reference/bc_data_v2.csv');t_by_sequence={x['sequence'].strip():x['well'] for x in rt if x['type']=='T'}
    def well_index(well):
        value=(ord(well[0])-ord('A'))*12+int(well[1:])-1
        assert 0<=value<48
        return str(value)
    for row in master:
        rt_bc,b2,b3=row['canonical_barcode'].split('_')
        assert row['published_cell_barcode']==b3+b2+'_'+well_index(t_by_sequence[rt_bc])
        assert row['bam_cb']=='_'.join([b3,b2,rt_bc])
    cells=[dict(prism_row_1based=i,published_cell_barcode=x['published_cell_barcode'],canonical_barcode=x['canonical_barcode'],
                sample=x['sample'],rt_well=well_index(t_by_sequence[x['canonical_barcode'].split('_')[0]]),
                rt_plate_well=t_by_sequence[x['canonical_barcode'].split('_')[0]]) for i,x in enumerate(master,1)]
    write(o/'data/figure_05/splitseq_cells.tsv',cells)
    record(r/'reference/published_568_barcode_map.csv','physical_cell_map','data/figure_05/splitseq_cells.tsv','all568 original rows; selected ID/sample fields, no reordering')
    record(r/'tables/splitseq_published_barcode_read_counts.csv','original_keyed_read_export',selection='all3408 numeric values verified externally; only RAD ED2/polyT fields promoted')
    record(prism_path,'native_numeric_identity',selection='all3408 cells checked; superseded comparator columns not published')
    rad_src=r/'checkpoints/rad_ed2/ed1_ed2_per_published_cell.tsv'
    component_src=r/'checkpoints/components/per_published_cell_counts.tsv'
    rad={x['barcode']:x for x in read(rad_src) if x['tool']=='ED2 current main'}
    component={x['cell']:x for x in read(component_src) if x['tool']=='Flexiplex polyT'}
    assert set(rad)==set(component)=={x['canonical_barcode'] for x in cells}
    table=[]
    for cell,original in zip(cells,keyed):
        key=cell['canonical_barcode'];rr=rad[key];cc=component[key]
        assert rr['reads']==original['rad_ed2_assigned_reads']
        assert cc['tool_reads']==original['flex_component_polyt_assigned_reads']
        table.append(dict(cell,rad_reads=int(rr['reads']),component_polyt_reads=int(cc['tool_reads']),
                          rad_umis=int(rr['umis']),component_polyt_umis=int(cc['tool_umis'])))
    write(o/'source_data/figure_05/splitseq_reads_umis_568.tsv',table)
    record(rad_src,'selected_RAD_per_cell_checkpoint','source_data/figure_05/splitseq_reads_umis_568.tsv','tool=ED2 current main; 568 cells')
    record(component_src,'selected_component_per_cell_checkpoint','source_data/figure_05/splitseq_reads_umis_568.tsv','tool=Flexiplex polyT; nonempty UMI, no length10 restriction; 568 cells')
    copy(r/'reference/bc_data_v2.csv','data/figure_05/rt_primer_well_map.csv','96_RT_primers_to48_physical_wells')
    # Preserve the independent existing short-read identity reference; do not infer pairing by its row order.
    reference=o/'source_data/figure_05/splitseq_reference_568_cells.csv'
    if reference.exists():
        sr={x['cell_bc']:x for x in read(reference)}
        assert set(sr)=={x['published_cell_barcode'] for x in master}
        for x in master:
            q=sr[x['published_cell_barcode']]
            assert q['sample']==x['sample']
            assert int(q['published_umi_count'])==int(x['published_sr_umi_cts'])
    package=r/'ssd2/benchmarks/flamesv2_splitseq_20260728'
    rad_run=r/'ssd2/results/rad/demultiplexed/splitseq/20260801_reverse_complement_whitelist_clean_main_ed2'
    component_run=package/'component_polyt_paired_t4'
    evidence=o/'source_data/figure_05/provenance/splitseq';evidence.mkdir(parents=True,exist_ok=True)
    for source,name in [(rad_run/'rad.time.txt','RAD_time.txt'),(rad_run/'rad_layout.csv','RAD_executed_layout.csv'),
                        (rad_run/'rad_position_map.csv','RAD_position_map.csv'),
                        (component_run/'run_manifest.txt','component_run_manifest.txt'),
                        (component_run/'workflow.time.txt','component_time.txt'),
                        (component_run/'workflow.stdout.log','component_stdout.log'),
                        (component_run/'read_counts.tsv','component_native_read_counts.tsv'),
                        (r/'source/component_runner/run_component_no_polyt.R','component_runner.R'),
                        (package/'FLAMES/DESCRIPTION','FLAMES_DESCRIPTION'),
                        (package/'FLAMES/R/find_barcode.R','find_barcode.R'),
                        (package/'FLAMES/src/main-functions/flexiplex.cpp','flexiplex.cpp'),
                        (package/'FLAMES/src/main-functions/flexiplex.h','flexiplex.h')]:
        copy(source,str((evidence/name).relative_to(o)),'selected_producer_evidence')
    source=rad_run/'run_manifest.txt'
    selected_lines=[x for x in source.read_text().splitlines() if not x.startswith(('comparison_baseline=','comparison_note='))]
    (evidence/'RAD_run_manifest.txt').write_text('\n'.join(selected_lines)+'\n')
    record(source,'selected_RAD_run_manifest',str((evidence/'RAD_run_manifest.txt').relative_to(o)),
           'selected run fields retained; unrelated comparison_baseline/comparison_note lines omitted')
    for name in ['bc_8nt_v1.csv','bc_8nt_v2.csv']:
        copy(package/'inputs/local_whitelists'/name,'data/figure_05/'+name,'executed_component_catalog')
    for name in ['splitseq_bc1_reverse_complement.txt','splitseq_bc2_reverse_complement.txt','splitseq_reverse_complemented_whitelist_layout.csv']:
        copy(package/'reverse_complemented_whitelist_test_20260728'/name,'data/figure_05/'+name,'executed_RAD_layout_or_catalog')
    analysis=r/'prism/native_components/analyses/F616A250-536B-42B0-B4E6-23C2BF786E46'
    for name in ['parameters.json','results.json','sheet.json']:
        copy(analysis/name,'source_data/figure_05/provenance/splitseq/paired_t_'+name,'selected_saved_Prism_analysis')
    result=json.loads((analysis/'results.json').read_text())['content']['pairedTTestModel']['pairedTTest']
    settings=json.loads((analysis/'parameters.json').read_text())['content']
    assert settings['experimentalDesign']=='PAIRED_T_TEST' and settings['options']['pValueTailType']=='P_VALUE_TWO_TAILED'
    stat=dict(analysis_uid=analysis.name,test='two-sided paired t test',n=568,t=result['t'],df=int(result['df']),
              p_value=result['pValue']['value'],alpha=settings['options']['significanceLevel'],
              source='saved native Prism values; procedure and annotations not replaced',
              difference='RAD minus component polyT; swapDirection=true in native settings',
              artwork_scope='native dataset binding verified; final exported panel/annotation appearance still requires artwork QA')
    (o/'source_data/figure_05/splitseq_saved_paired_t_test.json').write_text(json.dumps(stat,indent=2)+'\n')
    checkpoint_rows=[]
    full_info=json.loads((r/'full_rad_checkpoint_copy.json').read_text())
    assert sha(a.full_rad_ledger)==full_info['sha256']
    for source,name in [(a.full_rad_ledger,'RAD_ED2_assignments.tsv.gz'),
                        (component_run/'assignments.tsv.gz','component_polyT_assignments.tsv.gz'),
                        (component_run/'stats.tsv.gz','component_polyT_native_stats.tsv.gz')]:
        dest='checkpoints/figure_05/'+name;copy(source,dest,'current_assignment_checkpoint')
        checkpoint_rows.append(dict(path=dest,bytes=(o/dest).stat().st_size,sha256=sha(o/dest)))
    write(o/'manifests/figure_05_staged_checkpoints.tsv',checkpoint_rows)
    write(o/'manifests/figure_05_splitseq_sources.tsv',assets)
    registry=o/'manifests/figures_567_tool_parameters.tsv'
    if registry.exists():
        parameter_rows=read(registry)
        parameter_rows=[x for x in parameter_rows if not (x['figure']=='05' and (x['component'].startswith('LR-Split RAD /') or x['component'] in ['RAD (LR-Split-seq ED2)','FLAMES component Flexiplex (poly-T)']))]
        for x in parameter_rows:
            if x['figure']=='05':x['panels']=x['panels'].replace('; LR-Split panels unresolved','')
        fields=list(parameter_rows[0]);meta=dict(x.split('=',1) for x in selected_lines if '=' in x)
        def command(path):
            return next(x.split('Command being timed: ',1)[1].strip().strip('"') for x in path.read_text().splitlines() if 'Command being timed:' in x)
        def parameter(**kwargs):
            row={k:'' for k in fields};row.update(kwargs);parameter_rows.append(row)
        parameter(figure='05',panels='selected LR-Split read comparison; current per-cell UMIs, Figure5H binding pending',
            component='RAD (LR-Split-seq ED2)',version=meta['rad_version'],commit=meta['rad_commit'],binary_sha256=meta['binary_sha256'],
            argv=command(rad_run/'rad.time.txt'),chemistry_layout='LR-Split-seq; three8nt components; reverse-complemented catalogs; exact layout SHA256 '+meta['layout_sha256'],
            whitelist='96 ligation and96 RT component sequences; 48 paired RT wells; selected files in data/figure_05',
            reference='568 published physical cells, GSM5169184; input SRR13948564 SHA256 '+meta['input_sha256'],
            seed='No RNG seed explicitly recorded in producing argv',threads=meta['threads'],
            evidence='source_data/figure_05/provenance/splitseq/RAD_run_manifest.txt; source_data/figure_05/provenance/splitseq/RAD_time.txt',
            limitations='Successful saved producer, not a new raw execution; original tally script replaced only by exact validated checkpoint aggregation')
        parameter(figure='05',panels='selected LR-Split read comparison; current per-cell UMIs, Figure5H binding pending',
            component='FLAMES component Flexiplex (poly-T)',version='FLAMES2.7.1; embedded Flexiplex1.02.6',commit='bf2211a8da1e1c7327370ab12479ae70e1d37cd8',
            binary_sha256='compiled shared-object hash unrecovered; executed flexiplex.cpp source SHA256 '+sha(package/'FLAMES/src/main-functions/flexiplex.cpp'),
            argv=command(component_run/'workflow.time.txt'),chemistry_layout='three separately MATCHED8nt components ED1/buffer1; flankED3; UMI10 template; terminal FIXED8T included; reverse_complement=FALSE',
            whitelist='bc_8nt_v1.csv96 ligation; bc_8nt_v2.csv96 RT; exact selected catalogs in data/figure_05',
            reference='Same568 published physical cells; input SRR13948564, 5764421 original reads',seed='No explicit RNG seed in executed deterministic wrapper',threads='4',
            evidence='source_data/figure_05/provenance/splitseq/component_run_manifest.txt; source_data/figure_05/provenance/splitseq/component_time.txt; source_data/figure_05/provenance/splitseq/component_stdout.log; source_data/figure_05/provenance/splitseq/component_runner.R',
            limitations='Exact R/Rcpp/Rhtslib versions and compiled shared-object hash unrecovered; no BLAZE arm in this selected LR-Split comparison')
        write(registry,parameter_rows)
    # Source snapshots retain their own licenses even in a fresh output tree.
    for name in ['FLAMES_GPL-3.txt','embedded_Flexiplex_MIT.txt']:
        source=ROOT/'source_data/figure_05/provenance/splitseq/licenses'/name
        target=evidence/'licenses'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if source.resolve()!=target.resolve():shutil.copyfile(source,target)
    report=dict(status='passed selected source promotion',incoming_git_commit='07b39852cf436ad729cd7e4271c786a8c956fa1f',
        package_root=str(r),rows=568,native_numeric_cells_compared=3408,same_original_row_order=True,
        physical_keys_unique=True,source_reference_identity=True,raw_demultiplexing_rerun=False,
        selected_arms=['ED2 current main','Flexiplex polyT'],code_sha256=sha(Path(__file__)),
        primary_table_sha256=sha(o/'source_data/figure_05/splitseq_reads_umis_568.tsv'),
        remaining='Assignment aggregation replay follows separately. Figure5H intended depth-matched SR checkpoint/selection and panel binding unrecovered; no depth rule invented.')
    (o/'validation/figure_05_splitseq_recovery.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Promoted selected568-row comparison, exact producer pins and three current assignment checkpoints.')


if __name__=='__main__':main()
