#!/usr/bin/env python3
"""Recover C4/C5 checkpoints and rebuild auditable current-paper Figures 5–7.

Build is a checkpoint-resume operation, never a raw rerun. Render needs only the
deposited source_data directory. Pending panel decisions are recorded explicitly.
"""
import argparse
import collections
import csv
import datetime
from decimal import Decimal, ROUND_HALF_UP
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ('RAD', 'BLAZE', 'Flexiplex')
CHECKS = []
ASSETS = []


def sha(path):
    h = hashlib.sha256()
    with open(str(path), 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def read(path, delimiter=None):
    path = Path(path)
    delimiter = delimiter or (',' if '.csv' in path.name else '\t')
    with (gzip.open(str(path), 'rt') if path.suffix == '.gz' else path.open()) as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def write(path, rows, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not fields:
        fields = list(rows[0]) if rows else []
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter='\t')
        w.writeheader()
        w.writerows(rows)


def check(name, observed, expected=True, evidence='', tolerance=0):
    good = abs(observed - expected) <= tolerance if tolerance else observed == expected
    def compact(x):
        if isinstance(x, set):
            return dict(n=len(x), sorted_key_sha256=hashlib.sha256('\n'.join(sorted(x)).encode()).hexdigest())
        return x
    CHECKS.append(dict(check_id=name, observed=compact(observed), expected=compact(expected),
                       tolerance=tolerance, status='passed' if good else 'failed', evidence=evidence))
    if not good:
        raise ValueError('{}: observed {!r}, expected {!r}'.format(name, observed, expected))


def record(path, role):
    p = Path(path)
    ASSETS.append(dict(path=str(p), role=role, bytes=p.stat().st_size,
                       sha256=sha(p), validation='verified_content' if role != 'provenance' else 'hashed_only'))


def copy(src, dst, role='checkpoint'):
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(str(src), str(dst))
    record(src, role)
    check('copy_' + dst.name, sha(dst), sha(src), str(dst))


def bh(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    out, last = [0.] * len(values), 1.
    for i in range(len(order) - 1, -1, -1):
        last = min(last, values[order[i]] * len(order) / (i + 1))
        out[order[i]] = last
    return out


def siglabel(value, digits=2):
    x = Decimal(str(value))
    return str(x.quantize(Decimal('1e{}'.format(x.adjusted() - digits + 1)), rounding=ROUND_HALF_UP)) if x else '0'


def expression(project, out):
    base = project / '082426_volcano_plots/SN_ONT_H146_H526_vs_all_combined_F1_sweeps_20260831/inputs'
    dest = out / 'source_data/figure_07'
    source = base / 'direct_H146_vs_H526_plot_data.tsv.gz'
    copy(source, dest / source.name)
    lineage = project / 'LongBench_comps/SN_ONT_H146_H526_fullcohort_DEG_20260822/provenance/RAD_4acbe00_full_rebuild_20260828'
    copy(lineage/'source_manifest.tsv',dest/'RAD_emitted_segment_source_manifest.tsv','provenance')
    summary_source = lineage / 'build_summary.json'
    record(summary_source, 'selected_matrix_production_provenance')
    original_summary = json.loads(summary_source.read_text())
    summary_keys = ('assignment_corrected_records', 'assignment_exact_records',
                    'assignment_records', 'created_utc', 'host', 'n_cells',
                    'n_genes', 'n_nonzero', 'parent_gene_caveat', 'platform',
                    'python', 'numpy', 'scipy', 'rad_commit', 'records_with_gene',
                    'records_without_gene', 'scope', 'started_validation_utc')
    current_summary = {k: original_summary[k] for k in summary_keys}
    current_summary['total_molecules'] = original_summary['new_total_umis']
    current_summary['source_summary_sha256'] = sha(summary_source)
    current_summary['curation'] = 'Selected matrix production fields only; full original receipt remains at the external source path recorded in the asset manifest.'
    (dest / 'RAD_emitted_segment_build_summary.json').write_text(json.dumps(current_summary, indent=2)+'\n')
    check('F7_selected_matrix_molecules', current_summary['total_molecules'], 22875174)
    check('F7_selected_assignment_count_conservation', current_summary['assignment_exact_records'] + current_summary['assignment_corrected_records'], current_summary['assignment_records'])
    data = read(source)
    check('F7_common_rows', len(data), 24405)
    by_tool = {t: [x for x in data if x['tool'] == t] for t in TOOLS}
    common = {x['gene_id'] for x in by_tool['RAD']}
    check('F7_common_genes', len(common), 8135)
    (dest / 'matrix_production_record.md').write_text('''# Selected Figure 7 matrix and direct-contrast production record

The native SN-ONT RAD matrix was produced with RAD commit
`4acbe004ba11b150d6832395452632f367a6e6c1`, retaining all emitted records,
including concatemer-derived `-CT` segments. The selected matrix has **45,224
genes × 12,423 cells**, **15,772,545 nonzero coordinates** and **22,875,174
molecules**. Each emitted segment inherits the frozen original-read gene
assignment. Exact cell–gene–UMI keys are collapsed; records without a UMI count
individually. This contract does not independently establish segment-specific
gene alignments.

The selected direct H146-versus-H526 comparison uses **8,135 common eligible
genes** and **24,405 tool/gene rows**. Its raw P values and effects exactly match
the selected native direct-test output; common-family BH adjustment, supported
membership and all 594 threshold combinations have been independently checked.
The direct comparison is current; it is not awaiting a separate expression
rerun. The original emitted FASTQ and frozen read-gene file remain unavailable
at the checked paths, so complete upstream replay is not claimed.

The selected emitted-assignment checkpoint was recovered and fully verified:
57,885,606 five-field rows cover all 12,423 selected barcodes. It retains read
IDs, cell barcodes, UMIs, raw barcodes and correction flags. The extractor
removed orientation/concatemer suffixes; gene IDs and segment coordinates are
absent. This is a recovered C2 assignment source, not a complete gene/segment
ledger.

- [Current direct comparison source](direct_H146_vs_H526_plot_data.tsv.gz)
- [Selected matrix production fields](RAD_emitted_segment_build_summary.json)
- [Matrix and label content validation](../../validation/figures_567_checkpoint_checks.tsv)
- [Direct P-value/effect lineage validation](../../validation/figures_567_direct_test_lineage.json)
- [Recovered assignment validation](../../validation/figures_567_assignment_recovery.json)
- [Recovered assignment access and hash](../../manifests/figures_567_assignment_access.tsv)
- [Current walkthrough and exact producer parameters](../../docs/figure_07.md)

The original uncurated production receipt remains in the external source
project. Its SHA-256 is retained in the selected matrix summary and input
manifest; superseded comparison results are not reproduced here.
''')
    for t, rows in by_tool.items():
        check('F7_' + t + '_gene_identity', {x['gene_id'] for x in rows} == common and len(rows) == 8135)
        for prefix in ('tool', 'Illumina'):
            q = bh([float(x[prefix + '_p_value']) for x in rows])
            error = max(abs(a - float(b[prefix + '_BH_FDR_common'])) for a, b in zip(q, rows))
            check('F7_' + t + '_' + prefix + '_BH', error, 0., tolerance=1e-12)
    # Same reference values must be attached to every tool for a given gene.
    ref = {x['gene_id']: x for x in by_tool['RAD']}
    for t in TOOLS[1:]:
        check('F7_' + t + '_reference_identity', all(all(x[k] == ref[x['gene_id']][k] for k in ('Illumina_p_value', 'Illumina_log2FC', 'Illumina_BH_FDR_common')) for x in by_tool[t]))
    write(dest / 'common_genes.tsv', [dict(gene_id=x) for x in sorted(common)])
    membership, regions, supported = [], collections.Counter(), collections.Counter()
    lookup = {t: {x['gene_id']: x for x in rows} for t, rows in by_tool.items()}
    for g in sorted(common):
        r = ref[g]
        truth = float(r['Illumina_BH_FDR_common']) < .05 and abs(float(r['Illumina_log2FC'])) > 1
        flags = {}
        for t in TOOLS:
            x = lookup[t][g]
            flags[t] = int(truth and float(x['tool_BH_FDR_common']) < .05 and abs(float(x['tool_log2FC'])) > 1 and float(x['tool_log2FC']) * float(r['Illumina_log2FC']) > 0)
            supported[t] += flags[t]
        region = ''.join(str(flags[t]) for t in TOOLS)
        if region != '000':
            regions[region] += 1
        membership.append(dict(gene_id=g, gene_symbol=r['gene_symbol'], Illumina_truth=int(truth), direction='H146_high' if float(r['Illumina_log2FC']) > 0 else 'H526_high', region=region, **flags))
    check('F7_supported_recoveries', dict(supported), {'RAD': 654, 'BLAZE': 522, 'Flexiplex': 556})
    expected_regions = {'100': 117, '010': 29, '001': 26, '110': 29, '101': 66, '011': 22, '111': 442}
    check('F7_Venn_regions', dict(regions), expected_regions)
    write(dest / 'directional_membership.tsv', membership)
    write(dest / 'venn_regions.tsv', [dict(region=k, RAD=int(k[0]), BLAZE=int(k[1]), Flexiplex=int(k[2]), genes=regions[k]) for k in sorted(regions)])
    # Rebuild every integer and metric in the selected two-direction grid.
    historical = read(base / 'direct_H146_H526_F1_threshold_sweep_grid.tsv')
    record(base / 'direct_H146_H526_F1_threshold_sweep_grid.tsv', 'comparison')
    grid = []
    for old in historical:
        t, direction = old['tool'], old['direction']
        sign = 1 if direction == 'H146_high' else -1
        p, fc = float(old['tool_BH_FDR_cutoff']), float(old['tool_abs_log2FC_cutoff'])
        truth = {g for g, r in ref.items() if float(r['Illumina_BH_FDR_common']) < .05 and sign * float(r['Illumina_log2FC']) > 1}
        pred = {x['gene_id'] for x in by_tool[t] if float(x['tool_BH_FDR_common']) < p and sign * float(x['tool_log2FC']) > fc}
        tp, fp, fn, tn = len(pred & truth), len(pred - truth), len(truth - pred), len(common - pred - truth)
        values = dict(TP=tp, FP=fp, FN=fn, TN=tn, genes=len(common), truth_positive=len(truth), predicted_positive=len(pred))
        values.update(precision=tp / float(tp + fp) if tp + fp else 0., recall=tp / float(tp + fn) if tp + fn else 0., F1=2 * tp / float(2 * tp + fp + fn) if 2 * tp + fp + fn else 0.)
        for k, v in values.items():
            if abs(float(old[k]) - v) > 1e-12:
                raise ValueError('F7 grid mismatch {} {} {} {} {}'.format(t, direction, p, fc, k))
        row = dict(tool=t, direction=direction, tool_BH_FDR_cutoff=p, tool_abs_log2FC_cutoff=fc, **values)
        # Historical table stores two significant digits; artwork uses one.
        row['display_label_2sig'] = siglabel(row['F1'])
        row['display_label_1sig'] = siglabel(row['F1'], 1)
        grid.append(row)
    check('F7_threshold_grid_exact_integer_and_metric_comparison', len(grid), 594)
    display_source = project / 'paper_revision_20261022/evidence/figure7D_current_heatmap_match.tsv'
    record(display_source, 'artwork_numeric_comparison')
    displayed = read(display_source)
    rebuilt = {(r['tool'],r['direction'],r['tool_BH_FDR_cutoff'],r['tool_abs_log2FC_cutoff']):r for r in grid}
    check('F7_all_artwork_display_labels_half_up', sum(float(r['figure_display']) == float(rebuilt[r['tool'],r['direction'],float(r['FDR_cutoff']),float(r['log2FC_cutoff'])]['display_label_1sig']) for r in displayed), 594)
    check('F7_truth_H146', len([r for r in ref.values() if float(r['Illumina_BH_FDR_common']) < .05 and float(r['Illumina_log2FC']) > 1]), 412)
    check('F7_truth_H526', len([r for r in ref.values() if float(r['Illumina_BH_FDR_common']) < .05 and float(r['Illumina_log2FC']) < -1]), 769)
    write(dest / 'threshold_grid.tsv', grid)
    # A documented candidate fit; exact final workbook is still an author gate.
    fits, fit_points = [], []
    for direction, sign in [('H146_high', 1), ('H526_high', -1)]:
        genes = [g for g, r in ref.items() if float(r['Illumina_BH_FDR_common']) < .05 and sign * float(r['Illumina_log2FC']) > 1]
        for tool in ('RAD', 'Flexiplex'):
            xs = [-math.log10(float(lookup['BLAZE'][g]['tool_BH_FDR_common'])) for g in genes]
            ys = [-math.log10(float(lookup[tool][g]['tool_BH_FDR_common'])) for g in genes]
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
            fits.append(dict(direction=direction, tool=tool, n=len(xs), slope=slope, intercept=my - slope * mx, method='OLS; estimated intercept; uncapped; all directional Illumina truth genes', status='candidate_requires_artwork_fit_confirmation'))
            fit_points.extend(dict(gene_id=g, direction=direction, tool=tool, BLAZE_confidence=x, tool_confidence=y) for g, x, y in zip(genes, xs, ys))
    write(dest / 'confidence_fit_candidates.tsv', fits)
    write(dest / 'confidence_fit_points.tsv', fit_points)
    (dest / 'panel_status.json').write_text(json.dumps({'7A': 'recomputed_from_updated_C5', '7B': 'updated_common_universe_volcano; final_annotation_selection_pending', '7C': 'candidate_fit_requires_author_confirmation', '7D': 'all_594_grid_cells_recomputed', '7E': 'removed_by_author_2026-10-23; current Figure 7 contains A-D'}, indent=2) + '\n')


def genotype(project, out):
    src = project / 'reviewer_response_20260804/manuscript_tables/SN_ONT_cross_tool_vireo_per_cell_graph_ready.csv'
    record(src, 'C4_per_cell_genotype')
    data = read(src)
    check('F6_union_barcode_unique', len({r['cell_barcode'] for r in data}), len(data))
    reference = [r for r in data if r['illumina_reference_present'] == 'TRUE']
    check('F6_reference_cells', len(reference), 12012)
    counts = collections.Counter(r['illumina_reference_state'] for r in reference)
    check('F6_reference_states', dict(counts), {'named_singlet': 5782, 'doublet': 59, 'unassigned': 6171})
    prefixes = {'RAD': 'rad', 'BLAZE': 'blaze_panel_matched', 'Flexiplex': 'flexiplex'}
    long, summaries, per_donor, union, native_totals = [], [], [], [], []
    for t, p in prefixes.items():
        for r in data:
            union.append(dict(cell_barcode=r['cell_barcode'],tool=t,reference_present=int(r['illumina_reference_present']=='TRUE'),reference_state=r['illumina_reference_state'],reference_label=r['illumina_reference_label'],selected=int(r[p+'_query_selected']=='TRUE'),query_state=r[p+'_vireo_state'],query_label=r[p+'_vireo_label']))
        selected_rows=[r for r in union if r['tool']==t and r['selected']]
        check('F6_'+t+'_complete_selected_universe',len(selected_rows),{'RAD':12423,'BLAZE':10001,'Flexiplex':12101}[t])
        native_counts=collections.Counter(r['query_label'] for r in selected_rows if r['query_state']=='named_singlet')
        native_totals.extend(dict(tool=t,donor=k,nuclei=v,count_unit='selected named Vireo singlets, including outside Illumina reference; no positive-expression-depth filter') for k,v in sorted(native_counts.items()))
        for r in reference:
            state = r[p + '_vireo_state']
            selected = r[p + '_query_selected'] == 'TRUE'
            label = r[p + '_vireo_label']
            if not selected:
                outcome = 'not_selected'
            elif state == 'named_singlet' and r['illumina_reference_state'] == 'named_singlet':
                outcome = 'same' if label == r['illumina_reference_label'] else 'different'
            elif state in ('doublet', 'unassigned', 'named_singlet'):
                outcome = state
            else:
                outcome = 'missing_row'
            long.append(dict(cell_barcode=r['cell_barcode'], tool=t, reference_state=r['illumina_reference_state'], reference_label=r['illumina_reference_label'], selected=int(selected), query_state=state, query_label=label, outcome=outcome))
        sub = [r for r in long if r['tool'] == t and r['reference_state'] == 'named_singlet']
        cnt = collections.Counter(r['outcome'] for r in sub)
        expected = {'RAD': (5324,32,246,165,15), 'BLAZE': (4450,12,766,308,246), 'Flexiplex': (4674,17,725,340,26)}[t]
        check('F6_' + t + '_strict_outcomes', tuple(cnt[k] for k in ('same','different','doublet','unassigned','not_selected')), expected)
        check('F6_' + t + '_no_missing_selected_row', cnt['missing_row'], 0)
        summaries.append(dict(tool=t, reference_denominator=5782, same=cnt['same'], different=cnt['different'], doublet=cnt['doublet'], unassigned=cnt['unassigned'], not_selected=cnt['not_selected'], missing_row=cnt['missing_row'], strict_recall=cnt['same']/5782., conditional_concordance=cnt['same']/float(cnt['same']+cnt['different'])))
        for donor in sorted(set(r['reference_label'] for r in sub)):
            rows = [r for r in sub if r['reference_label'] == donor]
            c = collections.Counter(r['outcome'] for r in rows)
            per_donor.append(dict(tool=t, donor=donor, library='LongBench_SN_ONT', independent_libraries=1, reference_cells=len(rows), same=c['same'], different=c['different'], doublet=c['doublet'], unassigned=c['unassigned'], not_selected=c['not_selected'], strict_recall=c['same']/float(len(rows))))
    dest = out / 'source_data/figure_06'
    preserved=project/'scratch_preservation_20260921/files/longbench_snont_postdemux_vireo_20260803'
    commands=[]
    for tool in TOOLS:
        command_file=(preserved/'rebuilds/BLAZE_rebuilt_bulk_panel_tool_postdemux_20260804T135956Z/logs/cellsnp.time.txt') if tool=='BLAZE' else preserved/('logs/'+tool+'_cellsnp.time.txt')
        record(command_file,'executed_command')
        command=next(line.strip() for line in command_file.read_text().splitlines() if 'Command being timed:' in line)
        check('F6_'+tool+'_executed_CB_UB_contract',all(x in command for x in ('--cellTAG CB','--UMItag UB','--minMAF 0.1','--minCOUNT 10','--genotype')))
        commands.append(dict(tool=tool,command=command,source=str(command_file),source_sha256=sha(command_file)))
    write(dest/'executed_cellsnp_commands.tsv',commands)
    copy(project/'LongBench_comps/SN_ONT_RAD_bulk_cellline_bundle_20260803/bulk_donor_panel/provenance/runtime_manifest.tsv',dest/'bulk_panel_runtime_manifest.tsv','provenance')
    write(dest / 'per_cell_genotype.tsv', long)
    write(dest / 'union_per_cell_genotype.tsv', union)
    write(dest / 'selected_nuclei_by_donor.tsv', native_totals)
    write(dest / 'genotype_summary.tsv', summaries)
    write(dest / 'statistical_observations.tsv', per_donor)
    coords_src = project / 'LongBench_comps/SN_ONT_expression_supported_rescue_20260810/tables/prism/illumina_fixed_umap_graph_ready.csv'
    record(coords_src, 'fixed_coordinates')
    coords = read(coords_src)
    cdict = {r['cell_barcode']: r for r in coords}
    check('F6_coordinate_identity', set(cdict), {r['cell_barcode'] for r in reference})
    coordinates = [dict(cell_barcode=r['cell_barcode'], UMAP_1=r['UMAP_1'], UMAP_2=r['UMAP_2']) for r in coords]
    write(dest / 'fixed_coordinates.tsv', coordinates)
    overlays = [dict(r, UMAP_1=cdict[r['cell_barcode']]['UMAP_1'], UMAP_2=cdict[r['cell_barcode']]['UMAP_2']) for r in long]
    write(dest / 'genotype_overlay.tsv', overlays)
    object_coords = dest / 'umap_object_coordinates.tsv'
    if object_coords.exists():
        oc = {r['cell_barcode']: r for r in read(object_coords)}
        check('F6_object_coordinate_identity', set(oc), set(cdict))
        error = max(abs(float(oc[g][k])-float(cdict[g][k])) for g in cdict for k in ('UMAP_1','UMAP_2'))
        check('F6_SCT_object_matches_fixed_coordinates', error, 0., tolerance=1e-12)


def receptor(project, out):
    dest = out / 'source_data/figure_05'
    combined = []
    for tool in TOOLS:
        src = project / ('flexiplex_bcrtcr_cellline_20260811/flexiplex_per_barcode_bcrtcr.tsv' if tool == 'Flexiplex' else 'rad_blaze_bcrtcr_cellline/{}_per_barcode_bcrtcr.tsv'.format(tool))
        record(src, 'candidate_per_cell_receptor_checkpoint')
        rows = read(src)
        check('F5_' + tool + '_unique_barcodes', len({r['barcode'] for r in rows}), len(rows))
        for r in rows:
            for rec in ('bcr','tcr','unmapped'):
                native = int(r['native_' + rec])
                corrected = int(r['corrected_' + rec])
                if tool == 'Flexiplex':
                    corrected -= native
                if corrected < 0:
                    raise ValueError('negative exclusive corrected receptor count')
                combined.append(dict(tool=tool, barcode=r['barcode'], celltype=r['celltype'], receptor=rec, native=native, corrected_only=corrected, assigned=native+corrected, selection='candidate_run_not_bound_to_final_artwork'))
    write(dest / 'candidate_receptor_counts.tsv', combined)
    summary = []
    for t in TOOLS:
        sub = [r for r in combined if r['tool'] == t]
        summary.append(dict(tool=t, native=sum(r['native'] for r in sub), corrected_only=sum(r['corrected_only'] for r in sub), assigned=sum(r['assigned'] for r in sub)))
    check('F5_Flex_assigned', next(r['assigned'] for r in summary if r['tool']=='Flexiplex'), 6595231)
    write(dest / 'candidate_receptor_totals.tsv', summary)
    labels = project / 'flexiplex_bcrtcr_cellline_20260811/rageseq_barcode_celltype_map.csv'
    copy(labels, dest / 'candidate_cell_identity_map.csv')
    label_rows=read(labels)
    check('F5_candidate_identity_map_rows',len({r['barcode'] for r in label_rows}),3585)
    write(dest/'candidate_identity_summary.tsv',[dict(celltype=k,cells=v,source='candidate_3585_identity_map_not_4505_discovery_reference') for k,v in sorted(collections.Counter(r['celltype'] for r in label_rows).items())])
    split = project / 'scratch_preservation_20260921/files/splitseq_shortread_20260727/csv/called_cells_summary.csv'
    copy(split, dest / 'splitseq_reference_568_cells.csv')
    check('F5_split_reference_cells', len(read(split)), 568)
    recovery = project / 'paper_revision_20261022/lr_splitseq_recovery_20261023'
    subprocess.run([sys.executable, str(ROOT/'scripts/figure_05/recover_splitseq.py'),
                    '--recovery-root', str(recovery/'package'),
                    '--full-rad-ledger', str(recovery/'external_checkpoints/rad_ed2_all_assignments_normalized.tsv.gz'),
                    '--output-root', str(out)], check=True)
    subprocess.run([sys.executable, str(ROOT/'scripts/figure_05/replay_splitseq.py'), '--root', str(out)], check=True)
    selected = read(dest/'splitseq_reads_umis_568.tsv')
    check('F5_split_selected_physical_cells',len({r['canonical_barcode'] for r in selected}),568)
    for field,total in [('rad_reads',2078171),('component_polyt_reads',1156252),
                        ('rad_umis',1891704),('component_polyt_umis',1050292)]:
        check('F5_split_'+field,sum(int(r[field]) for r in selected),total,
              '568 explicitly mapped physical cells; current ledger replay')
    check('F5_split_replayed_numeric_counts',json.loads((out/'validation/figure_05_splitseq_counts.json').read_text())['integer_counts_compared'],2272)
    record(recovery/'package/tables/splitseq_published_barcode_read_counts.csv','selected_keyed_Prism_row_identity_source')


def write_reports(out):
    write(out / 'validation/figures_567_checks.tsv', CHECKS)
    write(out / 'manifests/figures_567_assets.tsv', ASSETS)
    checks = [dict(x, observed=str(x['observed']), expected=str(x['expected'])) for x in CHECKS]
    (out / 'validation/figures_567_checks.json').write_text(json.dumps(checks, indent=2) + '\n')


def render(out, only=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'svg.fonttype':'none', 'pdf.fonttype':42, 'font.size':9})
    colors = {'RAD':'#4995a4','BLAZE':'#b15959','Flexiplex':'#c6aa58'}
    def save(fig, figure, name):
        dest = out / 'figures' / figure
        dest.mkdir(parents=True, exist_ok=True)
        for ext in ('svg','pdf','png'):
            fig.savefig(str(dest/(name+'.'+ext)), dpi=180, bbox_inches='tight')
        plt.close(fig)
    if only in (None, '06'):
        summary=read(out/'source_data/figure_06/genotype_summary.tsv')
        fig,ax=plt.subplots(figsize=(6,3.7))
        for i,row in enumerate(summary):
            ax.bar(i,float(row['strict_recall'])*100,color=colors[row['tool']])
            ax.text(i,float(row['strict_recall'])*100+1,'{}/5782'.format(row['same']),ha='center',fontsize=8)
        ax.set(xticks=range(3),xticklabels=[x['tool'] for x in summary],ylabel='Strict identity recall (%)',ylim=(0,103))
        ax.spines['top'].set_visible(False);ax.spines['right'].set_visible(False)
        save(fig,'figure_06','genotype_strict_recall')
        overlay=read(out/'source_data/figure_06/genotype_overlay.tsv')
        cmap={'same':'#498a65','different':'#c34f4f','doublet':'#bb85b4','unassigned':'#aaaaaa','not_selected':'#dddddd','missing_row':'#111111','named_singlet':'#99b5bf'}
        fig,axes=plt.subplots(1,3,figsize=(11,3.5))
        for ax,t in zip(axes,TOOLS):
            rows=[r for r in overlay if r['tool']==t and r['reference_state'] in ('named_singlet','doublet')]
            for state in cmap:
                s=[r for r in rows if r['outcome']==state]
                if s:ax.scatter([float(r['UMAP_1']) for r in s],[float(r['UMAP_2']) for r in s],s=2,color=cmap[state],label=state,rasterized=True)
            ax.set_title(t);ax.set_xlabel('Fixed UMAP 1');ax.set_ylabel('Fixed UMAP 2')
        axes[-1].legend(markerscale=3,fontsize=6,loc='upper left',bbox_to_anchor=(1,1))
        save(fig,'figure_06','genotype_fixed_umap')
        ref=[r for r in overlay if r['tool']=='RAD']
        donors=sorted({r['reference_label'] for r in ref if r['reference_state']=='named_singlet'})
        palette=plt.get_cmap('tab10')
        fig,ax=plt.subplots(figsize=(5.3,4.3))
        for label in ['unassigned','doublet']+donors:
            rows=[r for r in ref if r['reference_label']==label]
            color='#efbba8' if label=='unassigned' else '#bdbdbd' if label=='doublet' else palette(donors.index(label))
            ax.scatter([float(r['UMAP_1']) for r in rows],[float(r['UMAP_2']) for r in rows],s=2,color=color,label=label,rasterized=True)
        ax.set_xlabel('Fixed UMAP 1');ax.set_ylabel('Fixed UMAP 2');ax.set_title('Independent Illumina reference: all 12,012 nuclei')
        ax.legend(markerscale=3,fontsize=6,loc='upper left',bbox_to_anchor=(1,1))
        save(fig,'figure_06','A_reference_fixed_umap')
        native=read(out/'source_data/figure_06/selected_nuclei_by_donor.tsv');donors=sorted({r['donor'] for r in native})
        fig,ax=plt.subplots(figsize=(8,3.7))
        for i,t in enumerate(TOOLS):
            counts={r['donor']:int(r['nuclei']) for r in native if r['tool']==t}
            ax.bar(np.arange(len(donors))+(i-1)*.25,[counts.get(d,0) for d in donors],width=.25,color=colors[t],label=t)
        ax.set_xticks(range(len(donors)));ax.set_xticklabels(donors);ax.set_ylabel('Selected nuclei with named genotype');ax.legend()
        save(fig,'figure_06','C_native_selected_nuclei_by_donor')
    if only in (None, '07'):
        # Region plot preserves exact Venn counts without requiring opaque workbook state.
        venn=read(out/'source_data/figure_07/venn_regions.tsv')
        fig,ax=plt.subplots(figsize=(7,3.4))
        labels=[' + '.join(t for t in TOOLS if int(r[t])) for r in venn]
        ax.bar(range(7),[int(r['genes']) for r in venn],color='#4995a4')
        ax.set_xticks(range(7));ax.set_xticklabels(labels,rotation=30,ha='right')
        ax.set_ylabel('Same-direction Illumina-supported genes')
        for i,r in enumerate(venn):ax.text(i,int(r['genes'])+3,r['genes'],ha='center')
        save(fig,'figure_07','A_updated_supported_intersections')
        from matplotlib.patches import Circle
        fig,ax=plt.subplots(figsize=(5,4.5))
        for t,xy in [('RAD',(-.65,.45)),('BLAZE',(.65,.45)),('Flexiplex',(0,-.65))]:
            ax.add_patch(Circle(xy,1.12,facecolor=colors[t],edgecolor=colors[t],alpha=.3))
        positions={'100':(-1.12,.7),'010':(1.12,.7),'001':(0,-1.25),'110':(0,1.0),'101':(-.67,-.52),'011':(.67,-.52),'111':(0,.08)}
        for r in venn:ax.text(*positions[r['region']],r['genes'],ha='center',va='center',fontsize=13)
        ax.text(-1.1,1.65,'RAD',ha='center');ax.text(1.1,1.65,'BLAZE',ha='center');ax.text(0,-1.95,'Flexiplex',ha='center')
        ax.set_xlim(-1.9,1.9);ax.set_ylim(-2.1,1.9);ax.set_aspect('equal');ax.axis('off')
        ax.set_title('Same-direction Illumina-supported DE genes\n8,135 common eligible genes',fontsize=10)
        save(fig,'figure_07','A_updated_venn_schematic')
        direct=read(out/'source_data/figure_07/direct_H146_vs_H526_plot_data.tsv.gz')
        fig,axes=plt.subplots(1,3,figsize=(11,3.5),sharey=True)
        for ax,t in zip(axes,TOOLS):
            rows=[r for r in direct if r['tool']==t]
            ax.scatter([float(r['tool_log2FC']) for r in rows],[-math.log10(float(r['tool_BH_FDR_common'])) for r in rows],s=2,color=colors[t],alpha=.5,rasterized=True)
            for gene in ('ASCL1','POU2F3'):
                for r in rows:
                    if r['gene_symbol']==gene:
                        x,y=float(r['tool_log2FC']),-math.log10(float(r['tool_BH_FDR_common']))
                        ax.scatter([x],[y],s=12,color='#b22222');ax.annotate(gene,(x,y),xytext=(3,4),textcoords='offset points',fontsize=7,color='#b22222')
            ax.axvline(-1,linestyle=':',linewidth=.6,color='grey');ax.axvline(1,linestyle=':',linewidth=.6,color='grey');ax.axhline(-math.log10(.05),linestyle=':',linewidth=.6,color='grey')
            ax.set_title(t);ax.set_xlabel('log2 fold change: H146 / H526')
        axes[0].set_ylabel('−log10(BH FDR; common gene family)')
        fig.tight_layout();save(fig,'figure_07','B_updated_common_universe_volcano')
        grid=read(out/'source_data/figure_07/threshold_grid.tsv')
        fig,axes=plt.subplots(2,3,figsize=(13,7))
        for row,direction in enumerate(('H146_high','H526_high')):
            for col,tool in enumerate(('RAD','Flexiplex','BLAZE')):
                sub=[r for r in grid if r['tool']==tool and r['direction']==direction]
                ps=sorted({float(r['tool_BH_FDR_cutoff']) for r in sub});fcs=sorted({float(r['tool_abs_log2FC_cutoff']) for r in sub})
                lookup={(float(r['tool_BH_FDR_cutoff']),float(r['tool_abs_log2FC_cutoff'])):float(r['F1']) for r in sub}
                mat=np.array([[lookup[p,fc] for fc in fcs] for p in ps]);ax=axes[row,col]
                im=ax.imshow(mat,origin='lower',aspect='auto',vmin=0,vmax=1,cmap='YlGnBu')
                ax.set_xticks(range(len(fcs)));ax.set_xticklabels(['{:g}'.format(x) for x in fcs],rotation=45)
                ax.set_yticks(range(len(ps)));ax.set_yticklabels(['{:g}'.format(x) for x in ps]);ax.set_title(tool+' '+direction.replace('_',' '));ax.set_xlabel('Absolute log2 fold change cutoff');ax.set_ylabel('BH FDR cutoff')
                for y in range(len(ps)):
                    for x in range(len(fcs)):ax.text(x,y,siglabel(mat[y,x],1),ha='center',va='center',fontsize=5,color='white' if mat[y,x]>.6 else 'black')
        fig.tight_layout();save(fig,'figure_07','D_updated_threshold_grid')
        points=read(out/'source_data/figure_07/confidence_fit_points.tsv');fits=read(out/'source_data/figure_07/confidence_fit_candidates.tsv')
        fig,axes=plt.subplots(1,2,figsize=(9,4))
        for ax,direction in zip(axes,('H146_high','H526_high')):
            for t in ('RAD','Flexiplex'):
                rows=[r for r in points if r['direction']==direction and r['tool']==t];fit=next(r for r in fits if r['direction']==direction and r['tool']==t)
                ax.scatter([float(r['BLAZE_confidence']) for r in rows],[float(r['tool_confidence']) for r in rows],s=3,alpha=.35,color=colors[t])
                xs=np.array([0,max(float(r['BLAZE_confidence']) for r in rows)]);ax.plot(xs,float(fit['intercept'])+xs*float(fit['slope']),color=colors[t],label='{} slope {:.4f}'.format(t,float(fit['slope'])))
            ax.set_title(direction.replace('_',' '));ax.set_xlabel('BLAZE −log10(BH FDR)');ax.set_ylabel('Tool −log10(BH FDR)');ax.legend(fontsize=7)
        fig.suptitle('Candidate updated confidence fit — presentation pending author review',fontsize=9)
        fig.tight_layout(rect=(0,0,1,.93));save(fig,'figure_07','C_candidate_updated_confidence')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['build','render','validate'])
    p.add_argument('--project-root',type=Path,default=Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data/reviewer_comment_data'))
    p.add_argument('--output-root',type=Path,default=ROOT)
    args=p.parse_args();out=args.output_root.resolve()
    if args.mode=='build':
        try:
            expression(args.project_root,out);genotype(args.project_root,out);receptor(args.project_root,out)
        finally:
            write_reports(out)
        outputs=[]
        for folder in ('figure_05','figure_06','figure_07'):
            for path in sorted((out/'source_data'/folder).rglob('*')):
                if path.is_file():outputs.append(dict(path=str(path.relative_to(out)),sha256=sha(path),bytes=path.stat().st_size))
        manifest=dict(mode='checkpoint_resume',raw_rerun='not_run',argv=sys.argv,code_sha256=sha(__file__),completed_utc=datetime.datetime.utcnow().isoformat()+'Z',checks=len(CHECKS),python=sys.version,outputs=outputs)
        (out/'manifests/figures_567_run.json').write_text(json.dumps(manifest,indent=2)+'\n')
    elif args.mode=='render':
        render(out)
    else:
        checks=read(out/'validation/figures_567_checks.tsv')
        if not checks or any(r['status']!='passed' for r in checks):
            raise SystemExit('scientific checkpoint checks failed')
        for path in ('source_data/figure_07/threshold_grid.tsv','source_data/figure_06/genotype_summary.tsv','source_data/figure_05/candidate_receptor_counts.tsv'):
            if not (out/path).is_file():raise SystemExit('missing '+path)
        manifest=json.loads((out/'manifests/figures_567_run.json').read_text())
        for item in manifest['outputs']:
            path=out/item['path']
            if not path.is_file() or sha(path)!=item['sha256']:
                raise SystemExit('checkpoint changed after validation: '+str(path))
        print('{} checkpoint checks passed; raw and author gates remain explicit'.format(len(checks)))


if __name__=='__main__':
    main()
