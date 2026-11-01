#!/usr/bin/env python3
"""Recalculate selected numerical prose claims from current figure tables.

This does not select or run a new inferential test. Correlations repeat the
existing Figure 7 concordance definition over all 8,135 common genes.
"""
import csv
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean, median

from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
claims = []


def read(relative):
    path = ROOT / relative
    opener = gzip.open if path.suffix == '.gz' else open
    with opener(str(path), 'rt') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))


def add(key, figure, value, unit, denominator, source, selection, meaning):
    claims.append(dict(claim_id=key, figure=figure, value=value, unit=unit,
                       denominator=denominator, source=source,
                       source_sha256=hashlib.sha256((ROOT/source).read_bytes()).hexdigest(),
                       selection=selection, meaning=meaning))


timing = 'source_data/figure_01/timing_summary.tsv'
for row in read(timing):
    if row['threads'] == '16' and row['metric'] == 'total_wall_hours':
        add('F1_16threads_'+row['dataset']+'_'+row['tool'], '1', row['mean'],
            'wall hours', '3 computational repetitions', timing,
            'threads=16; metric=total_wall_hours; dataset='+row['dataset']+'; tool='+row['tool'],
            'Mean discovery plus assignment time; repetitions are not biological samples.')

assignment = 'source_data/figure_02/assignment_states.tsv'
assignment_rows = read(assignment)
for tool in ('RAD', 'BLAZE', 'Flexiplex'):
    selected = [r for r in assignment_rows if r['tool'] == tool]
    assert len(selected) == 6
    assert sum(int(r['reads']) for r in selected) == 4993805
    for row in selected:
        add('F2_'+tool+'_'+row['state'], '2', row['reads'], 'physical reads',
            row['denominator'], assignment, 'tool='+tool+'; state='+row['state'],
            'One mutually exclusive state; tool-specific duplicate rules are documented in Figure 2.')

offlist = 'source_data/figure_03/offlist_totals.tsv'
offlist_rows = read(offlist)
assert len(offlist_rows) == 27
for dataset, denominator in (('ScTagger-L', 4993805), ('LongBench SC-ONT', 10000000), ('RAGE-seq', 20346396)):
    for tool in ('RAD', 'BLAZE', 'Flexiplex'):
        selected = [r for r in offlist_rows if r['dataset'] == dataset and r['tool'] == tool]
        assert len(selected) == 3 and {int(r['replicate']) for r in selected} == {1,2,3}
        assert {int(r['input_reads']) for r in selected} == {denominator}
        units = {r['unit'] for r in selected}
        assert len(units) == 1
        unit = units.pop()
        percentages = [100*int(r['assigned_count'])/denominator for r in selected]
        criterion = 'dataset='+dataset+'; tool='+tool+'; replicates=1,2,3'
        for label, value in (('mean',mean(percentages)), ('minimum',min(percentages)), ('maximum',max(percentages))):
            add('F3_'+dataset+'_'+tool+'_assigned_percent_'+label, '3', value,
                'assignments per 100 input reads', denominator, offlist, criterion,
                label.capitalize()+' across three supplied-list draws; counting unit: '+unit+'.')
        add('F3_'+dataset+'_'+tool+'_assigned_reads_mean', '3', mean(int(r['assigned_count']) for r in selected),
            unit, '3 supplied-list draws', offlist, criterion,
            'Mean of the three totals plotted in panel B.')

discovery = 'source_data/figure_04/plotted_checkpoint/plotted_metrics.tsv'
discovery_rows = read(discovery)
assert len(discovery_rows) == 111
assert len({r['canonical_id'] for r in discovery_rows}) == 37
assert len({(r['canonical_id'],r['tool']) for r in discovery_rows}) == 111
expected_ids = {r['canonical_id'] for r in discovery_rows}
for tool in ('RAD', 'BLAZE', 'Flexiplex'):
    selected = [r for r in discovery_rows if r['tool'] == tool]
    assert {r['canonical_id'] for r in selected} == expected_ids
    add('F4_'+tool+'_F1_above_0.90', '4', sum(float(r['f1']) > .9 for r in selected),
        'benchmark inputs', 37, discovery, 'tool='+tool+'; f1>0.90',
        'All 37 inputs retained, including reconstructed ScMixology2 and related technical inputs.')

splitseq = 'source_data/figure_05/splitseq_reads_umis_568.tsv'
splitseq_rows = read(splitseq)
assert len(splitseq_rows) == len({r['published_cell_barcode'] for r in splitseq_rows}) == 568
assert {int(r['prism_row_1based']) for r in splitseq_rows} == set(range(1,569))
splitseq_summary = 'source_data/figure_05/splitseq_summary.tsv'
splitseq_summaries = {r['tool']:r for r in read(splitseq_summary)}
for tool, prefix in (('RAD','rad'), ('Component Flexiplex polyT','component_polyt')):
    summary = splitseq_summaries[tool]
    assert int(summary['input_source_reads']) == 5764421
    assert int(summary['published_cells']) == 568
    for field, expected, unit in (
        ('read_cell_pairs',sum(int(r[prefix+'_reads']) for r in splitseq_rows),'distinct read–cell pairs'),
        ('cell_umi_pairs',sum(int(r[prefix+'_umis']) for r in splitseq_rows),'distinct cell–UMI pairs'),
        ('median_reads',median(int(r[prefix+'_reads']) for r in splitseq_rows),'reads per cell'),
        ('median_umis',median(int(r[prefix+'_umis']) for r in splitseq_rows),'UMIs per cell')):
        assert float(summary[field]) == expected
        add('F5_'+prefix+'_'+field,'5',expected,unit,568,splitseq,
            'all 568 keyed cells; '+prefix+'_reads / '+prefix+'_umis; '+field,
            'Selected ED2 / component poly-T comparison; nonempty UMI required, without a fixed UMI-length filter.')
    percentage = 100*int(summary['full_unique_source_reads'])/5764421
    assert abs(percentage-float(summary['full_unique_source_read_percent'])) < 1e-12
    add('F5_'+prefix+'_full_unique_source_read_percent','5',percentage,
        'percent of input physical reads',5764421,splitseq_summary,'tool='+tool,
        'Distinct original reads across the complete input; separate from assignment-row or read–cell-pair counts.')
    add('F5_'+prefix+'_published_unique_source_reads','5',int(summary['published_unique_source_reads']),
        'distinct physical reads','568 published cells',splitseq_summary,'tool='+tool,
        'Original read identifiers counted once across the selected cells, even if a read maps to multiple cells.')
genotypes = 'source_data/figure_06/genotype_summary.tsv'
for row in read(genotypes):
    denominator = int(row['reference_denominator'])
    assert denominator == 5782
    assert sum(int(row[x]) for x in ('same','different','doublet','unassigned','not_selected','missing_row')) == denominator
    add('F6_'+row['tool']+'_same', '6', row['same'], 'reference singlets', denominator,
        genotypes, 'tool='+row['tool']+'; outcome=same', 'Correct named singlets in the fixed reference population.')
    add('F6_'+row['tool']+'_recall', '6', int(row['same'])/denominator, 'fraction', denominator,
        genotypes, 'tool='+row['tool']+'; same/reference_denominator', 'Strict recall; all reference singlets remain in the denominator.')

expression = 'source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz'
expression_rows = read(expression)
assert len(expression_rows) == 24405
for tool in ('RAD', 'BLAZE', 'Flexiplex'):
    selected = [r for r in expression_rows if r['tool'] == tool]
    assert len(selected) == 8135
    truth = [float(r['Illumina_BH_FDR_common']) < .05 and abs(float(r['Illumina_log2FC'])) > 1 for r in selected]
    called = [float(r['tool_BH_FDR_common']) < .05 and abs(float(r['tool_log2FC'])) > 1 for r in selected]
    supported = sum(t and c and float(r['tool_log2FC'])*float(r['Illumina_log2FC']) > 0
                    for r,t,c in zip(selected,truth,called))
    assert sum(truth) == 1181
    criterion = 'tool='+tool+'; both BH_FDR<0.05 and abs(log2FC)>1; same direction'
    add('F7_'+tool+'_supported', '7', supported, 'genes', 1181, expression, criterion,
        'Updated common-gene analysis used by panel D; same-direction Illumina-supported calls.')
    add('F7_'+tool+'_called', '7', sum(called), 'genes', 8135, expression,
        'tool='+tool+'; tool BH_FDR<0.05 and abs(log2FC)>1', 'All tool calls, independent of reference support.')
    add('F7_'+tool+'_sensitivity', '7', supported/sum(truth), 'fraction', 1181,
        expression, criterion, 'Supported calls divided by all fixed Illumina truth calls.')
    add('F7_'+tool+'_precision', '7', supported/sum(called), 'fraction', sum(called),
        expression, criterion, 'Supported calls divided by all tool calls.')
    for metric,tool_column,reference_column in (
        ('signed_effect','tool_log2FC','Illumina_log2FC'),
        ('uncapped_confidence','tool_confidence','Illumina_confidence')):
        rho = float(spearmanr([float(r[tool_column]) for r in selected],
                             [float(r[reference_column]) for r in selected])[0])
        add('F7_'+tool+'_rho_'+metric, '7', rho, 'Spearman rho', 8135, expression,
            'tool='+tool+'; all common genes; '+tool_column+' versus '+reference_column,
            'Existing concordance statistic; no P value or new test family is introduced.')

destination = ROOT/'manifests/results_claims.tsv'
destination.parent.mkdir(parents=True, exist_ok=True)
with destination.open('w', newline='') as handle:
    writer = csv.DictWriter(handle, fieldnames=list(claims[0]), delimiter='\t', lineterminator='\n')
    writer.writeheader()
    writer.writerows(claims)
report_path = ROOT/'validation/manuscript_claims.json'
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(
    dict(status='passed', claims=len(claims), new_inferential_tests=0,
         scope='Selected numerical summaries from deposited figure tables; panel-specific sources retained; no raw tool execution'), indent=2)+'\n')
print('Wrote', len(claims), 'traceable current claims to', destination)
