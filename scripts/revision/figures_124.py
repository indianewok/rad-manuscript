#!/usr/bin/env python3
"""Build retained Figure1/2 inputs, validate current Figure4 tables and render source data.

This does not rerun demultiplexing, invent missing historical settings or execute
unapproved inferential tests. Build reads original project assets and writes only
under --output-root. Render/validate use deposited source_data alone.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import math
import os
import platform
import re
import shutil
import statistics
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from source_paths import data_root, scratch_root, scratch_nfs_root, resolve_source

REPO = Path(__file__).resolve().parents[2]
TOOLS = ('RAD', 'BLAZE', 'Flexiplex')
COLORS = {'RAD':'#A3392C', 'BLAZE':'#336B87', 'Flexiplex':'#568A55',
          'Flexiplex_f0':'#94A66F', 'Flexiplex_f8':'#568A55'}
STATES = ('native_correct', 'corrected_correct', 'corrected_incorrect',
          'native_incorrect', 'unassigned')
NREADS = 4993805
TIMING = 'scratch_preservation_20260921/files/three_tool_phase_benchmark_20260902_parallel_epyc7543'
SWEEP = 'LongBench_comps/ScTagger_quality_sweep_20260731'
EXTENDED = 'scratch_preservation_20260921/files/sctagger_nanopore2023_extended_sweep_20260913'
NATIVE = 'scratch_preservation_20260921/files/sctagger_nanopore2023_unadjusted_20260913'
REVISION = 'paper_revision_20261022'



def assignment_state_counts(raw_counts):
    """Combine discarded multiple-output reads with other unassigned reads.

    Producer checkpoints call discarded reads ``ambiguous``; the independent
    read-table audit calls them ``excluded_multiple_outputs``. Neither is a
    separate plotted state. Their tool-specific duplicate rules are unchanged.
    """
    counts = {state: int(raw_counts.get(state, 0)) for state in STATES}
    counts['unassigned'] += int(raw_counts.get('excluded_multiple_outputs', 0))
    counts['unassigned'] += int(raw_counts.get('ambiguous', 0))
    return counts


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def rows(path):
    p = Path(path)
    op = gzip.open if p.suffix == '.gz' else open
    with op(p, 'rt', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t' if '.tsv' in p.name else ','))


def write_rows(path, data, fields=None):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = list(data)
    fields = fields or list(data[0])
    tmp = p.with_name(p.name + '.tmp')
    with tmp.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter='\t' if '.tsv' in p.name else ',',
                           lineterminator='\n', extrasaction='raise')
        w.writeheader()
        w.writerows(data)
    tmp.replace(p)


def write_json(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    tmp.replace(p)


class Build:
    def __init__(self, args):
        self.project = args.project_root.resolve()
        self.base = self.project / 'reviewer_comment_data'
        self.out = args.output_root.resolve()
        self.checks = []
        self.assets = []
        self.tasks = []

    def check(self, key, condition, expected, observed, evidence):
        self.checks.append(dict(check_id=key, expected=expected, observed=observed,
                               tolerance='exact unless explicitly stated',
                               status='passed' if condition else 'failed', evidence=str(evidence)))
        if not condition:
            raise ValueError(f'{key}: expected {expected}; observed {observed}')

    def source(self, relative, role='retained_checkpoint'):
        p = resolve_source(relative, base=self.base)
        if not p.is_file():
            self.assets.append(dict(path=str(p), status='missing_at_checked_path', role=role))
            raise FileNotFoundError(p)
        item = dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p),
                    hash_scope='file_bytes', role=role, status='verified_content')
        self.assets.append(item)
        return p

    def copy(self, source, dest):
        p = self.source(source)
        target = self.out / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
        return target

    def task(self, task_id, status, completed, gate='', resume='passed', raw='not run'):
        self.tasks.append(dict(id=task_id, status=status, completed=completed,
                               next_dependency=gate, resume=resume, raw=raw,
                               evidence='validation/figures_124_build.json'))

    def timing(self):
        source_script = self.source(TIMING + '/scripts/collect_results.py', 'executed_historical_collector')
        vendored = Path(__file__).with_name('figures_124_collect_timing.py')
        self.check('timing_collector_identity', sha(vendored) == sha(source_script), sha(source_script), sha(vendored), vendored)
        spec = importlib.util.spec_from_file_location('revision_timing_collector', vendored)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        # Preservation moved nonempty files but left zero-byte COMPLETE/log
        # files on scratch. Rejoin actual files; never manufacture a marker.
        preserved=self.base/TIMING/'raw'
        original=scratch_nfs_root() / 'three_tool_phase_benchmark_20260902_parallel_epyc7543/raw'
        recovered=[]
        with tempfile.TemporaryDirectory(prefix='rad_timing_union_') as tmp:
            union=Path(tmp)/'raw'
            for root in (preserved,original):
                if not root.is_dir(): continue
                for source in sorted(root.rglob('*')):
                    if not source.is_file() or source.name=='.DS_Store': continue
                    relative=source.relative_to(root)
                    target=union/relative
                    if target.exists():
                        if sha(target)!=sha(source):
                            raise ValueError('conflicting timing archive member: '+str(relative))
                        continue
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.symlink_to(source)
                    recovered.append(dict(relative_path=str(relative),source_path=str(source),bytes=source.stat().st_size,sha256=sha(source)))
            all_records, selected = mod.collect(union)
            # Export stable logical paths, and resolve them through the
            # explicit source registry rather than ephemeral union paths.
            for record in all_records:
                for field,value in record.items():
                    if isinstance(value,str): record[field]=value.replace(str(union),'timing_raw_union')
        write_rows(self.out/'source_data/figure_01/timing_raw_source_registry.tsv',recovered)
        accepted = [r for r in all_records if r['accepted'] == 'true']
        self.check('timing_108_accepted_phases', len(selected) == len(accepted) == 108,
                   108, {'selected':len(selected),'accepted':len(accepted)}, TIMING + '/raw')
        archived = rows(self.source(TIMING + '/provenance/all_runs_long.tsv'))
        key = lambda r: tuple(r[x] for x in ('dataset','tool','threads','replicate','phase'))
        old = {key(r):r for r in archived if r['accepted']=='true'}
        fields = ('elapsed_seconds','gnu_time_max_rss_kib','metrics_sha256','command_sha256',
                  'input_sha256_preverified','expected_reads','cpu_model','exit_status')
        diffs = []
        for r in accepted:
            for f in fields:
                if r[f] != old[key(r)][f]:
                    diffs.append([*key(r), f, old[key(r)][f], r[f]])
        self.check('timing_raw_logs_equal_archived', not diffs, 'all accepted measured fields equal', diffs, TIMING)
        self.check('timing_hardware_stratum', all('EPYC 7543' in r['cpu_model'] and r['exit_status']=='0' for r in accepted),
                   'AMD EPYC 7543 and zero exits', sorted(set(r['cpu_model'] for r in accepted)), TIMING)
        write_rows(self.out/'source_data/figure_01/accepted_phase_records.tsv', accepted)
        groups = defaultdict(list)
        for r in accepted:
            groups[tuple(r[x] for x in ('dataset','tool','threads','replicate'))].append(r)
        combined = []
        for k, pair in sorted(groups.items()):
            self.check('timing_phase_pair_'+'_'.join(k), {x['phase'] for x in pair}=={'whitelist_detection','demultiplexing'},
                       'one detection and one demultiplexing phase', [x['phase'] for x in pair], TIMING)
            combined.append(dict(zip(('dataset','tool','threads','replicate'),k),
                                 total_wall_seconds=sum(float(x['elapsed_seconds']) for x in pair),
                                 total_wall_hours=sum(float(x['elapsed_seconds']) for x in pair)/3600,
                                 max_process_rss_GB=max(int(x['gnu_time_max_rss_kib']) for x in pair)*1024/1e9,
                                 memory_definition='max GNU time process maxRSS over phases; decimal GB'))
        write_rows(self.out/'source_data/figure_01/combined_replicates.tsv',combined)
        summary=[]
        for dataset in ('SN-ONT','SC-PB'):
            for tool in TOOLS:
                for threads in (4,16,64):
                    group=[r for r in combined if (r['dataset'],r['tool'],r['threads'])==(dataset,tool,str(threads))]
                    for metric in ('total_wall_hours','max_process_rss_GB'):
                        values=[r[metric] for r in group]
                        summary.append(dict(dataset=dataset,tool=tool,threads=threads,metric=metric,n=len(values),
                                            mean=statistics.mean(values),sd=statistics.stdev(values),
                                            minimum=min(values),maximum=max(values)))
        write_rows(self.out/'source_data/figure_01/timing_summary.tsv',summary)
        expected={('SN-ONT','RAD'):1.75,('SN-ONT','BLAZE'):7.24,('SN-ONT','Flexiplex'):9.08,
                  ('SC-PB','RAD'):1.49,('SC-PB','BLAZE'):3.04,('SC-PB','Flexiplex'):2.01}
        observed={(x['dataset'],x['tool']):round(x['mean'],2) for x in summary if x['threads']==16 and x['metric']=='total_wall_hours'}
        self.check('timing_16thread_historical_means', observed==expected, str(expected), str(observed), 'combined_replicates.tsv')
        for name in ('input_manifest.tsv','software_and_resources.tsv'):
            self.copy(TIMING+'/provenance/'+name, 'source_data/figure_01/'+name)
        self.task('F1-02','passed','Reparsed accepted GNU-time records and reconstructed 108 phases / 54 paired totals; historical values match exactly.',
                  'Final artwork must retain declared process-RSS definition and selected error-bar convention.')

    def figure2(self):
        folder = self.out/'source_data/figure_02'
        sweep2018=rows(self.source(SWEEP+'/ALL_TOOLS_SWEEP_WITH_QUALITY.tsv'))
        sweepboth=rows(self.source(EXTENDED+'/results/all_tools_both_models.tsv'))
        self.check('sweep_2018_shape',len(sweep2018)==96,96,len(sweep2018),SWEEP)
        self.check('sweep_L_both_models_shape',len(sweepboth)==96,96,len(sweepboth),EXTENDED)
        normalized=[]
        for r in sweep2018:
            normalized.append(dict(dataset=r['dataset'],model='uniform_Q20' if r['quality_tag']=='flatQ20' else 'nanopore2018',
                                   condition=r['quality_tag'],shift=r['phred_shift'],tool=r['tool'],
                                   full_dataset_mean_Q=r['mean_all_base_q'],calls=r['calls'],tp=r['tp'],fp=r['fp'],fn=r['fn'],
                                   precision=r['precision'],recall=r['recall'],f1=r['f1'],
                                   origin='archived full FASTQ benchmark',source_table=SWEEP+'/ALL_TOOLS_SWEEP_WITH_QUALITY.tsv'))
        for r in sweepboth:
            if r['quality_model']!='nanopore2023': continue
            normalized.append(dict(dataset='L',model=r['quality_model'],condition=r['condition'],shift=r['shift'],tool=r['tool'],
                                   full_dataset_mean_Q=r['full_dataset_mean_Q'],calls=r['calls'],tp=r['tp'],fp=r['fp'],fn=r['fn'],
                                   precision=r['precision'],recall=r['recall'],f1=r['f1'],origin=r['result_origin'],
                                   source_table=EXTENDED+'/results/all_tools_both_models.tsv'))
        self.check('sweep_complete_selected_grid',len(normalized)==144,144,len(normalized),'discovery_metrics.tsv')
        for i,r in enumerate(normalized):
            check_metrics(r,50 if r['dataset']=='S' else 5000)
        self.check('sweep_metric_conservation',True,'144 exact count identities; metric absolute tolerance 1e-9',144,'discovery_metrics.tsv')
        write_rows(folder/'discovery_metrics.tsv',normalized)
        truthsets={}
        for dataset in ('S','L'):
            truthfile=self.source(scratch_root() / 'sctagger_sl_three_tool_quality_20260731/inputs'/(dataset+'_truth_barcodes.txt'),'synthetic_truth')
            truthsets[dataset]={x.strip() for x in truthfile.read_text().splitlines() if x.strip()}
            self.check('sweep_truth_'+dataset,len(truthsets[dataset])==(50 if dataset=='S' else 5000),
                       50 if dataset=='S' else 5000,len(truthsets[dataset]),truthfile)
        source2023={(r['condition'],r['tool']):r['source_whitelist'] for r in sweepboth if r['quality_model']=='nanopore2023'}
        callmanifest=[]
        identities=folder/'discovery_barcode_identities.tsv.gz'
        identities.parent.mkdir(parents=True,exist_ok=True)
        # Deterministic gzip header avoids introducing wall-clock-dependent bytes.
        with identities.open('wb') as rawfile:
            import io
            with gzip.GzipFile(fileobj=rawfile,mode='wb',mtime=0,filename='') as compressed:
                with io.TextIOWrapper(compressed,newline='') as textfile:
                    w=csv.writer(textfile,delimiter='\t',lineterminator='\n')
                    w.writerow(['dataset','model','condition','tool','barcode','classification'])
                    for r in normalized:
                        if r['model']=='nanopore2023':
                            original=source2023[(r['condition'],r['tool'])]
                            source=resolve_source(original,base=self.base)
                        else:
                            filename={'RAD':'rad/scanwl.txt','BLAZE':'blaze/whitelist.csv',
                                      'Flexiplex_f0':'flex_f0/selected.txt','Flexiplex_f8':'flex_f8/selected.txt'}[r['tool']]
                            source=scratch_root() / 'sctagger_sl_three_tool_quality_20260731/runs'/r['dataset']/r['condition']/filename
                            original=str(source)
                        source=self.source(source,'selected_discovery_whitelist')
                        calls=set()
                        for line in source.read_text().splitlines():
                            value=re.split(r'[\t, ]+',line.strip())[0]
                            if len(value)==16 and set(value)<=set('ACGT'):calls.add(value)
                        truthset=truthsets[r['dataset']]
                        got=[len(calls),len(calls&truthset),len(calls-truthset),len(truthset-calls)]
                        want=[int(r[k]) for k in ('calls','tp','fp','fn')]
                        self.check('discovery_rescore_'+'_'.join(r[k] for k in ('dataset','model','condition','tool')),got==want,want,got,source)
                        for bc in sorted(calls|truthset):
                            label='TP' if bc in calls and bc in truthset else ('FP' if bc in calls else 'FN')
                            w.writerow([r[k] for k in ('dataset','model','condition','tool')]+[bc,label])
                        callmanifest.append(dict(dataset=r['dataset'],model=r['model'],condition=r['condition'],tool=r['tool'],
                                                 original_path=original,resolved_path=str(source),sha256=sha(source),calls=len(calls)))
        write_rows(folder/'discovery_callset_manifest.tsv',callmanifest)
        paired_path=self.source(EXTENDED+'/quality/paired_50000_barcode_mean_Q.csv')
        paired=rows(paired_path)
        self.check('quality_paired_sample_identity',len(paired)==50000 and len({r['read_id'] for r in paired})==50000 and
                   {r['truth_barcode'] for r in paired}==truthsets['L'],
                   '50000 unique read IDs spanning all 5000 truth barcodes',
                   [len(paired),len({r['read_id'] for r in paired}),len({r['truth_barcode'] for r in paired})],paired_path)
        qualitysummary=rows(self.source(EXTENDED+'/quality/quality_summary.tsv'))
        for r in qualitysummary:
            values=[float(x[r['label']]) for x in paired]
            self.check('quality_sample_mean_sd_'+r['label'],
                       abs(statistics.mean(values)-float(r['sample_mean_barcode_Q']))<1e-9 and
                       abs(statistics.stdev(values)-float(r['sample_SD']))<1e-9,
                       'mean and sample SD within 1e-9',[statistics.mean(values),statistics.stdev(values)],paired_path)
        hist=rows(self.source(EXTENDED+'/quality/reconstructed_full_quality_histograms.tsv'))
        bycondition=defaultdict(list)
        for r in hist:bycondition[(r['model'],r['condition'])].append(r)
        for key,group in bycondition.items():
            got=[sum(int(x[k]) for x in group) for k in ('whole_base_count','barcode_base_count','truth_located_barcode_window_min_count')]
            self.check('quality_hist_conservation_'+'_'.join(key),got==[8394808882,16*4976160,4976160],
                       [8394808882,16*4976160,4976160],got,'reconstructed_full_quality_histograms.tsv')
        matching=rows(self.source(EXTENDED+'/quality/matched_quality_levels.tsv'))
        self.check('quality_11_matched_shifts',len(matching)==11 and max(abs(float(r['mean_Q_difference2023_minus2018'])) for r in matching)<.374,
                   '11 mean-matched shifts; maximum absolute Q difference <0.374',
                   [len(matching),max(abs(float(r['mean_Q_difference2023_minus2018'])) for r in matching)],'matched_quality_levels.tsv')
        with (folder/'paired_50000_barcode_mean_Q.csv.gz').open('wb') as rawfile:
            with gzip.GzipFile(fileobj=rawfile,mode='wb',mtime=0,filename='') as stream:stream.write(paired_path.read_bytes())
        write_rows(folder/'quality_summary.tsv',qualitysummary)
        write_rows(folder/'reconstructed_full_quality_histograms.tsv',hist)
        write_rows(folder/'matched_quality_levels.tsv',matching)
        self.copy(SWEEP+'/quality_conditions.tsv','source_data/figure_02/quality_conditions_2018.tsv')
        self.copy(EXTENDED+'/blaze_replay/native_validation.json','source_data/figure_02/native_selector_validation.json')
        canonical=json.loads(self.source(REVISION+'/evidence/figure2_canonical_rad_flex/canonical_results.json').read_text())
        blaze=json.loads(self.source(REVISION+'/prism/blaze2023_assignment_replay/metrics.json').read_text())
        source_arrays={t:REVISION+'/evidence/figure2_canonical_rad_flex/'+t+'_selected_per_barcode.csv' for t in ('RAD','Flexiplex')}
        source_arrays['BLAZE']=REVISION+'/prism/blaze2023_assignment_replay/BLAZE_selected_per_barcode.csv'
        truth_path=self.source('sctagger_L_fixed5000_three_tool_20260812/common/L_truth_5000_barcodes.txt','independent_header_derived_truth')
        truth={x.strip() for x in truth_path.read_text().splitlines() if x.strip()}
        self.check('RAD_targets_equal_independent_truth',truth=={x['barcode'] for x in rows(self.source(source_arrays['RAD']))},
                   'exact truth target set equality',len(truth),truth_path)
        self.check('sctagger_L_truth_size',len(truth)==5000,5000,len(truth),source_arrays['RAD'])
        arrays=[];states=[];correction=[]
        expected={'RAD':[667965,1944306,191519,571,2189444],
                  'Flexiplex':[463613,1398700,281696,381,2849415],
                  'BLAZE':[640957,1881358,133074,764,2337652]}
        for tool in TOOLS:
            source=rows(self.source(source_arrays[tool]))
            self.check(tool+'_unique_selected_targets',len({r['barcode'] for r in source})==len(source),
                       len(source),len({r['barcode'] for r in source}),source_arrays[tool])
            d=canonical[tool]['counts'] if tool!='BLAZE' else blaze
            counts=assignment_state_counts(d)
            self.check(tool+'_assignment_states',list(counts.values())==expected[tool] and sum(counts.values())==NREADS,
                       expected[tool],list(counts.values()),source_arrays[tool])
            for state,n in counts.items():
                states.append(dict(tool=tool,state=state,reads=n,denominator=NREADS,fraction=n/NREADS,count_unit='unique physical read'))
            for field in ('native_correct','corrected_correct','corrected_incorrect','native_incorrect'):
                obs=sum(int(r[field]) for r in source)
                self.check(tool+'_array_sum_'+field,obs==counts[field],counts[field],obs,source_arrays[tool])
            selected={r['barcode']:r for r in source}
            for bc in sorted(truth|set(selected)):
                r=selected.get(bc)
                arrays.append(dict(tool=tool,barcode=bc,is_truth=int(bc in truth),selected=int(r is not None),
                                   **{field:int(r[field]) if r is not None else '' for field in ('native_correct','corrected_correct','native_incorrect','corrected_incorrect')}))
            denom=counts['corrected_correct']+counts['corrected_incorrect']
            for state in ('corrected_correct','corrected_incorrect'):
                correction.append(dict(tool=tool,state=state,reads=counts[state],denominator=denom,fraction=counts[state]/denom))
        write_rows(folder/'assignment_states.tsv',states)
        write_rows(folder/'assignment_per_target.tsv',arrays)
        write_rows(folder/'correction_only.tsv',correction)
        write_rows(folder/'truth_barcodes.tsv',[dict(barcode=x) for x in sorted(truth)])
        extra=[r for r in arrays if r['tool']=='BLAZE' and not r['is_truth']]
        self.check('BLAZE_extra_targets',len(extra)==15 and sum(r['corrected_incorrect'] for r in extra)==908 and sum(r['native_incorrect'] for r in extra)==183,
                   '15 targets, 908 corrected incorrect, 183 native incorrect',
                   [len(extra),sum(r['corrected_incorrect'] for r in extra),sum(r['native_incorrect'] for r in extra)],'assignment_per_target.tsv')
        self.task('F2-02','passed','Rescored all 144 actual discovery whitelists; exported TP/FP/FN identities; checked 50,000 paired IDs, all quality means/SDs, full histogram conservation and 11 matched shifts.',
                  'F2-04 author/native-graphics review. Historical per-base sample replay file missing at checked path; quality-generator raw replay not performed.')
        resume_report=self.out/'validation/figures_124_assignment_resume.json'
        full_resume=False
        if resume_report.exists():
            report=json.loads(resume_report.read_text())
            full_resume=(report.get('status')=='passed' and len(report.get('expected_table_hashes',{}))==2 and
                         all(sha(self.out/p)==h for p,h in report.get('expected_table_hashes',{}).items()) and
                         all(r['status']=='passed' for r in report.get('tools',{}).values()) and len(report.get('tools',{}))==3)
        self.task('F2-03','passed' if full_resume else 'ready',
                  'Complete read-table resumption and all 52,076 selected-target category values match; five-state totals/missingness reconcile.' if full_resume else
                  'All five-state totals, selected-target arrays, missing-target policy and BLAZE extra targets independently reconcile.',
                  'Native Prism/statistical gates remain F2-04; raw tool rerun not performed.' if full_resume else
                  'Complete per-read upstream identity comparison remains; retained per-target checkpoint resumption passed.')
        contract=dict(seeds={'nanopore2018_S':20260727,'nanopore2018_L':20260731,'nanopore2023_L':20260731},
                      effective_quality_tape_seeds={'nanopore2018_S':16211358332209865628,
                                                   'nanopore2018_L':11835179057691093796,
                                                   'nanopore2023_L':6475178776901811265},
                      model_files={model:'source_data/figure_02/models/'+model+'.gz'
                                   for model in ('nanopore2018','nanopore2023')},
                      model_sha256={},
                      rng_contract='Use effective_quality_tape_seeds unchanged for exact reproduction.')
        for filename in ('nanopore2018.gz','nanopore2023.gz'):
            self.copy(SWEEP+'/code/models/'+filename,'source_data/figure_02/models/'+filename)
        model_locations={'nanopore2018':scratch_root()/'rad_sctagger_badread_quality_20260727/models/nanopore2018.gz',
                         'nanopore2023':self.base/'LongBench_comps/ScTagger_nanopore2023_Q15_Q20_20260819/models/nanopore2023.gz'}
        for model,location in model_locations.items():
            path=self.source(location,'quality_model_source')
            contract['model_sha256'][model]=sha(folder/'models'/(model+'.gz'))
            self.check('quality_model_bytes_'+model,sha(path)==sha(folder/'models'/(model+'.gz')),
                       sha(folder/'models'/(model+'.gz')),sha(path),path)
        self.copy(SWEEP+'/code/SOURCE_MANIFEST.tsv','source_data/figure_02/generator_source_manifest.tsv')
        self.copy(NATIVE+'/validation/full_fastq_validation.json','source_data/figure_02/native_fastq_validation.json')
        self.copy(NATIVE+'/provenance/generation_environment.tsv','source_data/figure_02/generation_environment.tsv')
        inputaudit=self.out/'validation/figures_124_fastq_identity.json'
        fresh=False
        if inputaudit.exists():
            audit=json.loads(inputaudit.read_text());fresh=audit.get('status')=='passed'
        write_json(folder/'quality_generation_contract.json',contract)
        self.task('F2-01','passed' if fresh else 'running','Verified model bytes, generator hashes and recorded RNG seeds.',
                  'Complete FASTQ identity audit passed; raw generator replay remains separate.' if fresh else
                  'Fresh complete FASTQ identity audit job 9976816; no source sequence was rewritten.',resume='passed' if fresh else 'partial')
        self.task('F2-05','passed','Recorded the effective quality-tape seeds.',
                  'Code change deferred by author; not a release gate.',resume='not applicable')
        # Read the immutable source; its unrelated/obsolete sheets are not published.
        prism=self.source(REVISION+'/prism/Figure2_corrected_20261022.prism')
        self.check('corrected_Prism_closed_hash',sha(prism)=='dded389f9d8214278f93d2669c64e704bbf2208c47db96bf57a4ce4c77d6d016',
                   'dded389f9d8214278f93d2669c64e704bbf2208c47db96bf57a4ce4c77d6d016',sha(prism),prism)
        self.task('F2-04','blocked-native-desktop-QA','Verified immutable external corrected Prism source; published only selected current canonical arrays/correction proportions.',
                  'Existing statistics/annotations preserved by author instruction; native desktop reopen/save/export remains unavailable; see desktop_QA.md.',resume='passed; native Prism pending')

    def figure4(self):
        """Validate current deposited Figure4 data without restoring other runs."""
        folder=self.out/'source_data/figure_04'
        metrics=rows(folder/'barcode_detection_metrics.tsv')
        inventory=rows(folder/'sample_inventory.tsv')
        ids=[r['canonical_id'] for r in inventory]
        self.check('F4_current_37_inputs',len(ids)==len(set(ids))==37,37,len(ids),folder/'sample_inventory.tsv')
        keys={(r['canonical_id'],r['tool']) for r in metrics}
        self.check('F4_current_111_pairs',len(metrics)==111 and keys=={(x,t) for x in ids for t in TOOLS},
                   'same37 inputs with three tools',len(metrics),folder/'barcode_detection_metrics.tsv')
        for r in metrics:check_metrics(r,int(r['reference_n']))
        parameters=rows(folder/'tool_parameters.tsv')
        self.check('F4_current_parameter_pairs',len(parameters)==111 and
                   {(r['dataset'],r['tool']) for r in parameters}==keys,
                   'same111 input/tool records',len(parameters),folder/'tool_parameters.tsv')
        parameter_fields=['dataset','tool','version','command']
        self.check('F4_current_parameter_columns',bool(parameters) and list(parameters[0])==parameter_fields,
                   parameter_fields,list(parameters[0]) if parameters else [],folder/'tool_parameters.tsv')
        rad=[r for r in parameters if r['tool']=='RAD']
        receipts={r['dataset']:json.loads((folder/'producing_evidence/current_RAD'/(r['dataset']+'.json')).read_text()) for r in rad}
        self.check('F4_current_RAD_source',len(rad)==37 and all(
                   receipts[r['dataset']]['source_commit']=='4acbe004ba11b150d6832395452632f367a6e6c1' and
                   receipts[r['dataset']]['dataset_id']==r['dataset'] and receipts[r['dataset']]['max_error']==0.3
                   for r in rad),'RAD4acbe00, recorded error0.3',len(rad),folder/'tool_parameters.tsv')
        for metric in ('precision','recall','f1'):
            paired=rows(folder/('paired_'+metric+'.tsv'))
            self.check('F4_current_paired_'+metric,[r['paired_input_id'] for r in paired]==ids,
                       'same37 input order',len(paired),folder/('paired_'+metric+'.tsv'))
            for r in paired:
                for tool in TOOLS:
                    expected=next(x[metric] for x in metrics if x['canonical_id']==r['paired_input_id'] and x['tool']==tool)
                    if r[tool]!=expected:raise ValueError('Current paired metric differs from source table')
        self.task('F4-01','ready','Validated current37 input triples, count/metric identities and pinned RAD parameters.',
                  'Current paired tables retain the saved Friedman/Dunn methods; native Prism recalculation/export remains a separate private handoff.')

    def hd(self):
        folder=self.out/'source_data/figure_01'
        wide=rows(self.source(REPO/'checkpoints/figure_01/sample_bin_matrix_16um.csv.gz'))
        cmp=rows(self.source(self.project/'raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts/per_bin_compare_PBC44593.csv.gz'))
        ref={r['sr16']:r for r in cmp}
        difference=[]
        for r in wide:
            k=r['spaceranger_16um']
            if k in ref and int(float(r['PBC44593_count']))!=int(ref[k]['rad_demux']):
                difference.append(dict(bin_id=k,wide_table_count=int(float(r['PBC44593_count'])),
                                       retained_comparison_count=int(ref[k]['rad_demux']),RAD_valid=r['PBC44593_valid']))
        stage_report=self.out/'validation/figures_124_hd_lineage.json'
        stage_evidence=json.loads(stage_report.read_text()) if stage_report.exists() else {}
        stage_bound=(stage_evidence.get('wide_source',{}).get('sha256')==sha(REPO/'checkpoints/figure_01/sample_bin_matrix_16um.csv.gz')
                     and stage_evidence.get('comparison_source',{}).get('sha256')==sha(self.project/'raw_fastq_datasets/complex_outsourced_datasets/visium_hd_lr/uncorrected_spot_counts/per_bin_compare_PBC44593.csv.gz')
                     and stage_evidence.get('status')=='different_processing_stages; identity-comparison-assumption_rejected')
        self.checks.append(dict(check_id='HD_representative_RAD_count_stage_comparison',
                    expected='identity equality is inapplicable across detection and demultiplexing stages' if stage_bound else 'source-stage provenance required before identity comparison',
                    observed=len(difference),tolerance='exact difference count; not a like-for-like validation',
                    status='not-applicable-different-processing-stages' if stage_bound else 'source-lineage-unresolved',
                    evidence='validation/figures_124_hd_lineage.json' if stage_bound else 'source_data/figure_01/hd_stage_differences.tsv'))
        write_rows(folder/'hd_stage_differences.tsv',difference,
                   ['bin_id','wide_table_count','retained_comparison_count','RAD_valid'])
        total=sum(float(r['PBC44593_count']) for r in wide)
        plot=[]
        for r in wide:
            count=float(r['PBC44593_count']);valid=int(r['PBC44593_valid'])
            if valid and count<=0: raise ValueError('RAD-valid HD bin has nonpositive count')
            plot.append(dict(bin_id=r['spaceranger_16um'],array_row=r['array_row'],array_col=r['array_col'],
                             in_tissue=r['in_tissue'],RAD_count=count,RAD_valid=valid,
                             RAD_log10_CPM=math.log10(count*1e6/total) if count>0 else '',
                             RAD_denominator=total,flowcell='PBC44593',bin_size_um=16))
        write_rows(folder/'hd_RAD_bins.tsv',plot)
        grid_report=self.out/'validation/figures_124_hd_grid_reconstruction.json'
        grid_evidence=json.loads(grid_report.read_text()) if grid_report.exists() else {}
        grid_bound=(grid_evidence.get('grid_rows')==175561 and grid_evidence.get('in_tissue_rows')==123658 and
                    grid_evidence.get('source',[{}])[0].get('sha256')==sha(folder/'hd_RAD_bins.tsv'))
        write_json(folder/'hd_plot_contract.json',dict(flowcell='PBC44593',bin_size_um=16,RAD_total_before_grid_merge=total,
                   transformation='log10(count*1e6/total), no pseudocount',
                   shared_color_range='pending Seurat nCount_Spatial metadata',
                   Seurat_source='Space Ranger converted Nanopore reads, not independent matched Illumina',
                   status='partial; triptych not rendered',RAD_count_stage='whitelist-detection valid-pair counts; whole-table totals independently equal all four original pair-count sources',
                   other_RAD_source_stage='retained rad_demux column; not an identity-equivalent count source',
                   per_bin_creation_provenance='unrecovered; total equality alone does not prove barcode-to-bin mapping',
                   required_grid_columns='reconstructed with exact raw/filtered reference identity' if grid_bound else 'not yet independently reconstructed'))
        self.task('F1-03','blocked-missing-asset',
                  f'Exported wide-table16um detection counts and exact denominator; {len(difference)} differences from retained rad_demux are a comparison across processing stages, not evidence of changed equivalent counts.' if stage_bound else 'Exported wide-table counts; processing-stage provenance still requires reconciliation.',
                  'Recover selected Seurat nCount_Spatial object/creation provenance and full barcode-to-bin count-creation code. Required grid/mask fields have been reconstructed and independently matched to raw/filtered reference barcode sets.' if grid_bound else 'Recover named Seurat/tissue-position assets and full barcode-to-bin creation provenance before shared-scale triptych. Complete detection-count totals match four original pair-count tables; this alone does not prove every bin mapping.',resume='passed scoped stage/totals audit; missing native spatial assets')

    def schematic(self):
        audit=self.source(REVISION+'/evidence/github_main_methods_audit.md','pinned_algorithm_source_audit')
        self.copy(audit,'source_data/figure_01/pinned_algorithm_audit.md')
        for path in ('include/rad/barcode_correction.hpp','include/rad/sigstring.hpp','include/rad/whitelist_generator.hpp'):
            self.source(REVISION+'/github_audit/main_cb699170/'+path,'pinned_algorithm_source')
        nodes=[
            dict(step='Read structure annotation',role='demultiplexing',description='Define static elements and variable barcode, UMI and captured-read elements.',code_anchor='pinned source audit; layout parsing'),
            dict(step='Position mapping',role='demultiplexing',description='Locate static elements and extract variable sequences with strand normalization.',code_anchor='sigstring.hpp:1265-1271'),
            dict(step='Identity and correction',role='demultiplexing',description='Check correctly oriented exact catalog/selected identities; apply staged candidate and running-count checks.',code_anchor='sigstring.hpp:1320-1343,1399-1430; barcode_correction.hpp:2393-2437'),
            dict(step='Selected-cell output',role='demultiplexing',description='With a nonempty selected list, emit permitted selected barcode elements; strict mode requires every component.',code_anchor='sigstring.hpp:3293-3389,3440-3471,4881-4884'),
            dict(step='Adapter-based discovery',role='whitelist discovery',description='Extract candidate barcodes and count catalog identities using the declared all-extraction denominator.',code_anchor='whitelist_generator.hpp:3029-3087'),
            dict(step='Adaptive selection',role='whitelist discovery',description='Use density/saddle selection, conditional fallback, adaptive floor and final hazard review.',code_anchor='whitelist_generator.hpp:3197-3269,3352-3448')]
        write_rows(self.out/'source_data/figure_01/algorithm_crosswalk.tsv',nodes)
        self.task('F1-01','ready','Crosswalk ties workflow labels to main cb699170 source hashes; distinct archived timing pin retained. Editable scripted review schematic supplied.',
                  'Final source/artwork selection remains; review diagram is not asserted identical to original embedded artwork.',resume='passed code/label crosswalk')

    def finish(self):
        write_json(self.out/'validation/figures_124_build.json',dict(
            status='available-stages-completed-with-gates',
            created_at_utc=datetime.now(timezone.utc).isoformat(), command=[sys.executable,*sys.argv],
            code_sha256=sha(Path(__file__)), python=platform.python_version(),
            task_results=self.tasks, checks=self.checks, source_assets=self.assets,
            scope='checkpoint reconstruction and validation; no full raw reruns; no unapproved hypothesis tests'))
        write_json(self.out/'manifests/figures_124_tasks.json',self.tasks)


def check_metrics(row, reference_n):
    tp,fp,fn,calls=(int(row[x]) for x in ('tp','fp','fn','calls'))
    if min(tp,fp,fn,calls)<0 or calls!=tp+fp or reference_n!=tp+fn:
        raise ValueError('count conservation failure: '+str(row))
    values={'precision':tp/calls if calls else 0,'recall':tp/reference_n if reference_n else 0,
            'f1':2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0}
    for metric,v in values.items():
        if not math.isfinite(float(row[metric])) or abs(float(row[metric])-v)>1e-9:
            raise ValueError(f'metric mismatch {metric}: {row}')


def validate(out):
    """Portable checks use only deposited source data and fail nonzero."""
    checks=[]
    def record(name,ok,detail):
        checks.append(dict(check_id=name,status='passed' if ok else 'failed',evidence=detail))
        if not ok: raise ValueError(name+': '+str(detail))
    f1=rows(out/'source_data/figure_01/combined_replicates.tsv')
    record('timing_complete_pairs',len(f1)==54 and len({tuple(r[k] for k in ('dataset','tool','threads','replicate')) for r in f1})==54,len(f1))
    for r in f1:
        record('timing_positive_'+str(tuple(r[k] for k in ('dataset','tool','threads','replicate'))),float(r['total_wall_hours'])>0 and float(r['max_process_rss_GB'])>0,r['tool'])
    sweeps=rows(out/'source_data/figure_02/discovery_metrics.tsv')
    record('discovery_complete_grid',len(sweeps)==144 and len({tuple(r[k] for k in ('dataset','model','condition','tool')) for r in sweeps})==144,len(sweeps))
    for r in sweeps: check_metrics(r,50 if r['dataset']=='S' else 5000)
    assignments=rows(out/'source_data/figure_02/assignment_states.tsv')
    for tool in TOOLS:
        rr=[r for r in assignments if r['tool']==tool]
        record('state_conservation_'+tool,len(rr)==len(STATES) and {r['state'] for r in rr}==set(STATES) and sum(int(r['reads']) for r in rr)==NREADS,len(rr))
    arrays=rows(out/'source_data/figure_02/assignment_per_target.tsv')
    record('array_unique_keys',len(arrays)==len({(r['tool'],r['barcode']) for r in arrays}),len(arrays))
    for r in arrays:
        fields=[r[k] for k in ('native_correct','corrected_correct','native_incorrect','corrected_incorrect')]
        if (r['selected']=='0' and fields!=['']*4) or (r['selected']=='1' and any(x=='' or int(x)<0 for x in fields)):
            raise ValueError('selected/missingness violation '+str(r))
    metrics=rows(out/'source_data/figure_04/barcode_detection_metrics.tsv')
    record('all37_tool_pairs',len(metrics)==111 and len({r['canonical_id'] for r in metrics})==37 and len({(r['canonical_id'],r['tool']) for r in metrics})==111,len(metrics))
    for r in metrics: check_metrics(r,int(r['reference_n']))
    ids={r['canonical_id'] for r in metrics}
    inventory=rows(out/'source_data/figure_04/sample_inventory.tsv')
    record('inventory_current37',len(inventory)==37 and {r['canonical_id'] for r in inventory}==ids,len(inventory))
    for name in ('precision','recall','f1'):
        pairs=rows(out/f'source_data/figure_04/paired_{name}.tsv')
        record('matched_'+name,len(pairs)==37 and {r['paired_input_id'] for r in pairs}==ids,len(pairs))
        for r in pairs:
            for tool in TOOLS:
                value=next(x[name] for x in metrics if x['tool']==tool and x['canonical_id']==r['paired_input_id'])
                if r[tool]!=value: raise ValueError('paired value differs from source')
    char=rows(out/'source_data/figure_04/input_characteristics.tsv')
    record('characteristics_same37',len(char)==37 and {r['canonical_id'] for r in char}==ids,len(char))
    write_json(out/'validation/figures_124_portable.json',dict(status='passed',checks=checks,
               scope='deposited-table schema, identity, conservation, pairing and metric checks'))
    return checks


def render(out):
    validate(out)
    os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'rad-manuscript-matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                         'svg.fonttype':'none','pdf.fonttype':42,'axes.titlesize':10})
    exports=[]
    def save(fig,number,name):
        p=out/f'figures/figure_{number:02d}'
        p.mkdir(parents=True,exist_ok=True)
        for ext in ('svg','pdf','png'):
            f=p/(name+'.'+ext);fig.savefig(f,dpi=180,bbox_inches='tight');exports.append(str(f.relative_to(out)))
        plt.close(fig)
    timing=rows(out/'source_data/figure_01/combined_replicates.tsv')
    fig,axs=plt.subplots(2,2,figsize=(8,6),constrained_layout=True)
    for col,dataset in enumerate(('SN-ONT','SC-PB')):
        for row,metric in enumerate(('total_wall_hours','max_process_rss_GB')):
            ax=axs[row,col]
            for offset,tool in enumerate(TOOLS):
                means=[];sds=[]
                for threads in (4,16,64):
                    v=[float(r[metric]) for r in timing if (r['dataset'],r['tool'],r['threads'])==(dataset,tool,str(threads))]
                    means.append(statistics.mean(v));sds.append(statistics.stdev(v))
                    ax.scatter([threads]*len(v),v,color=COLORS[tool],s=12,alpha=.5)
                ax.errorbar([4,16,64],means,yerr=sds,label=tool,color=COLORS[tool],marker='o',capsize=3)
            ax.set_xscale('log',base=2);ax.set_xticks([4,16,64],['4','16','64']);ax.set_xlabel('Requested worker threads')
            ax.set_ylabel('Total wall time (hours)' if row==0 else 'Maximum process RSS (GB)');ax.set_title(dataset)
    axs[0,0].legend(frameon=False);fig.suptitle('Accepted EPYC 7543 runs; mean ± SD, three repetitions',fontsize=11)
    save(fig,1,'timing_descriptive')
    nodes=rows(out/'source_data/figure_01/algorithm_crosswalk.tsv')
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    fig,ax=plt.subplots(figsize=(10,3.8));ax.set_xlim(0,10);ax.set_ylim(0,4);ax.axis('off')
    top=[r for r in nodes if r['role']=='demultiplexing'];bottom=[r for r in nodes if r['role']=='whitelist discovery']
    for i,r in enumerate(top):
        x=.15+i*2.5
        ax.add_patch(FancyBboxPatch((x,2.35),2.1,.8,boxstyle='round,pad=0.1',facecolor='#F3E4DF',edgecolor=COLORS['RAD']))
        ax.text(x+1.05,2.75,r['step'].replace(' and ','\nand ').replace('structure annotation','structure\nannotation'),ha='center',va='center',fontsize=10)
        if i<3:ax.add_patch(FancyArrowPatch((x+2.2,2.75),(x+2.4,2.75),arrowstyle='-|>',mutation_scale=14,color='#555555'))
    for i,r in enumerate(bottom):
        x=.15+i*2.5
        ax.add_patch(FancyBboxPatch((x,.7),2.1,.8,boxstyle='round,pad=0.1',facecolor='#DCE9ED',edgecolor=COLORS['BLAZE']))
        ax.text(x+1.05,1.1,r['step'].replace(' ','\n',1),ha='center',va='center',fontsize=10)
    ax.add_patch(FancyArrowPatch((2.35,1.1),(2.55,1.1),arrowstyle='-|>',mutation_scale=14,color='#555555'))
    ax.annotate('Selected list',xy=(6.2,2.25),xytext=(5.5,1.1),ha='center',arrowprops={'arrowstyle':'->','color':'#555555'},fontsize=9)
    ax.text(.15,3.65,'RAD workflow review — source pin cb699170',fontsize=13)
    ax.text(.15,.15,'Exact-identity behavior depends on orientation and loaded-list roles; sequence membership does not establish biological origin.',fontsize=8)
    save(fig,1,'workflow_schematic_review')
    sweeps=rows(out/'source_data/figure_02/discovery_metrics.tsv')
    fig,axs=plt.subplots(1,3,figsize=(11,3.5),constrained_layout=True)
    for ax,(dataset,model) in zip(axs,(('S','nanopore2018'),('L','nanopore2018'),('L','nanopore2023'))):
        for tool in ('RAD','BLAZE','Flexiplex_f0','Flexiplex_f8'):
            group=sorted([r for r in sweeps if (r['dataset'],r['model'],r['tool'])==(dataset,model,tool)],key=lambda x:float(x['full_dataset_mean_Q']))
            ax.plot([float(r['full_dataset_mean_Q']) for r in group],[float(r['f1']) for r in group],'.-',label=tool,color=COLORS[tool])
        ax.set_title(f'ScTagger-{dataset}: {model}');ax.set_xlabel('Whole-dataset mean base quality');ax.set_ylabel('Barcode discovery F1');ax.set_ylim(-.03,1.03)
    axs[0].legend(frameon=False,fontsize=8);save(fig,2,'quality_discovery_sweeps')
    states=rows(out/'source_data/figure_02/assignment_states.tsv')
    fig,axs=plt.subplots(1,2,figsize=(9,4),constrained_layout=True)
    statecolors=['#4A6F91','#74A889','#C78350','#B64A49','#DDDDDD']
    bottom=np.zeros(3)
    for s,color in zip(STATES,statecolors):
        vals=np.array([float(next(r['fraction'] for r in states if r['tool']==t and r['state']==s)) for t in TOOLS])
        axs[0].bar(TOOLS,vals,bottom=bottom,label=s.replace('_',' '),color=color);bottom+=vals
    axs[0].set_ylabel('Fraction of all 4,993,805 physical reads');axs[0].legend(fontsize=7,frameon=False,loc='upper center',bbox_to_anchor=(.5,-.1),ncol=2)
    corr=rows(out/'source_data/figure_02/correction_only.tsv')
    for i,t in enumerate(TOOLS):
        fraction=float(next(r['fraction'] for r in corr if r['tool']==t and r['state']=='corrected_incorrect'))
        axs[1].bar(t,100*fraction,color=COLORS[t]);axs[1].text(i,100*fraction+.3,f'{100*fraction:.2f}%',ha='center',fontsize=8)
    axs[1].set_ylabel('Incorrect among corrected assignments (%)');axs[1].set_ylim(0,20)
    save(fig,2,'assignment_descriptive')
    metrics=rows(out/'source_data/figure_04/barcode_detection_metrics.tsv')
    fig,axs=plt.subplots(1,3,figsize=(10,3.5),constrained_layout=True)
    for ax,metric in zip(axs,('precision','recall','f1')):
        pairs=rows(out/f'source_data/figure_04/paired_{metric}.tsv')
        for r in pairs:
            ax.plot(range(3),[float(r[t]) for t in TOOLS],color='#CCCCCC',linewidth=.5,zorder=1)
        for i,t in enumerate(TOOLS):
            vals=[float(r[t]) for r in pairs]
            bp=ax.boxplot([vals],positions=[i],widths=.4,showfliers=False,whis=(0,100),patch_artist=True,
                          boxprops={'facecolor':'white','edgecolor':COLORS[t]},medianprops={'color':COLORS[t]},manage_ticks=False)
            ax.scatter(np.full(len(vals),i),vals,s=9,c=COLORS[t],zorder=3)
        ax.set_xticks(range(3),TOOLS,rotation=20);ax.set_ylabel(metric.capitalize());ax.set_ylim(-.03,1.04)
    fig.suptitle('All 37 paired inputs; median and min–max; descriptive reconstruction',fontsize=11)
    save(fig,4,'barcode_detection_all37_descriptive')
    characteristics=rows(out/'source_data/figure_04/input_characteristics.tsv')
    fig,axs=plt.subplots(1,3,figsize=(10,4),constrained_layout=True)
    for ax,(field,label) in zip(axs,(('num_seqs','Input reads'),('AvgQual','Saved SeqKit AvgQual'),('GC(%)','GC (%)'))):
        for i,r in enumerate(characteristics):ax.scatter(i,float(r[field]),s=18,color='#336B87')
        ax.set_xlabel('Input index in deposited table');ax.set_ylabel(label)
        if field=='num_seqs':ax.set_yscale('log')
    fig.suptitle('Saved all-read input characteristics; exact SeqKit invocation unresolved',fontsize=10)
    save(fig,4,'input_characteristics_descriptive')
    write_json(out/'validation/figures_124_render.json',dict(status='passed',exports=exports,
               matplotlib=matplotlib.__version__,numpy=np.__version__,source_data_only=True,
               scientific_status='descriptive review renders; no final inferential annotation or native Prism recalculation'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('build','render','validate'))
    p.add_argument('--project-root',type=Path,default=data_root())
    p.add_argument('--output-root',type=Path,default=REPO)
    args=p.parse_args();out=args.output_root.resolve()
    if args.mode=='build':
        b=Build(args)
        try:
            b.timing(); b.figure2(); b.figure4(); b.hd(); b.schematic()
        finally:
            b.finish()
        validate(out)
    elif args.mode=='render':render(out)
    else:validate(out)
    label='available checkpoint stages completed; unresolved gates recorded' if args.mode=='build' else 'passed'
    print(f'{args.mode}: {label}; outputs under {out}')


if __name__=='__main__':
    main()
