#!/usr/bin/env python3
"""Export only the saved selected Figure 4 public identifier sets and references.

No reads or selectors are run. Source sets must reproduce every selected count
before publication. Controlled-access inputs remain explicit aggregate-only rows.
"""
import argparse
import csv
import gzip
import hashlib
import json
import re
from pathlib import Path
from source_paths import data_root, scratch_root, resolve_source
from figures_124 import REPO, rows, sha, write_json, write_rows


def identifiers(path, column=None, where=None):
    op = gzip.open if path.suffix == '.gz' else open
    with op(path, 'rt') as handle:
        if column:
            values = (r[column] for r in csv.DictReader(handle, delimiter='\t') if where is None or where(r))
        else:
            values = (re.split(r'[\s,]+', line.strip())[0].strip('"') for line in handle if line.strip())
        result = {v.removesuffix('-1') for v in values}
    # Header fields are never accepted as identifiers.
    return {v for v in result if re.fullmatch('[ACGT]{16}', v)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=data_root())
    parser.add_argument('--output-root', type=Path, default=REPO)
    args = parser.parse_args()
    b = args.project_root / 'reviewer_comment_data'
    preserved = b / 'scratch_preservation_20260921/files'
    out = args.output_root
    current = rows(out / 'source_data/figure_04/barcode_detection_metrics.tsv')
    policy_rows = rows(REPO / 'data/figure_04/identifier_manifest.tsv')
    publication_status = {(r['canonical_id'], r['tool']): r['status'] for r in policy_rows}
    expected_keys = {(r['canonical_id'], r['tool']) for r in current}
    if len(publication_status) != len(policy_rows) or set(publication_status) != expected_keys:
        raise ValueError('Identifier manifest must cover every selected input/tool exactly once')
    allowed_statuses = {'public-identifiers-recomputed', 'aggregate-only-controlled-access'}
    if not set(publication_status.values()).issubset(allowed_statuses):
        raise ValueError('Identifier manifest contains an unknown publication status')
    mapping = {}

    def add(sample, tool, path, ref, call_column=None, call_filter=None, ref_column=None, ref_filter=None, note=''):
        mapping[sample, tool] = (path, ref, call_column, call_filter, ref_column, ref_filter, note)

    # Synthetic flat-Q20 experiment, distinct from Figure 2 paired-quality runs.
    p = b / 'wl_scan/20260731_sctagger_badread_quality_full'
    for size in ('S', 'L'):
        ref = p / 'truth' / f'{size}_barcodes.txt'
        for tool, sub in [('RAD', f'rad/{size}/flatQ20/output/scanwl.txt'),
                          ('BLAZE', f'blaze/{size}/flatQ20/output/whitelist.csv'),
                          ('Flexiplex', f'flexiplex/{size}/flatQ20/output/{size}_flatQ20_barcodes_final.txt')]:
            add(f'ScTagger-{size}_flatQ20', tool, p / 'runs' / sub, ref)
    # The complete paired native LongBench producer retained these selected lists.
    p = b / 'LongBench_comps/full_A_to_B_audit_20260731/provenance/selected_whitelists'
    for short in ('SC_ONT', 'SN_ONT', 'SC_PB', 'SN_PB'):
        ref = b / f'LongBench_comps/full_A_to_B_audit_20260731/references/cellranger_filtered/ill_{short[:2].lower()}_barcodes.tsv.gz'
        flex = {'SC_ONT':'SC', 'SN_ONT':'SN'}.get(short, short)
        for tool, sub in [('RAD', f'rad/{short}/{short}_RAD.txt'), ('BLAZE', f'blaze/{short}/whitelist.csv'),
                          ('Flexiplex', f'flex_v1026/{short}/{flex}_flexiplex_whitelist.txt')]:
            add('LongBench-' + short.replace('_', '-'), tool, p / sub, ref)
    # Every native Tilgner callset has a donor-matched released reference.
    p = b / 'tilgner_all10_native_three_tool_whitelist_20260810'
    for r in rows(p / 'provenance/SOURCE_INDEX.tsv'):
        sample, tool = r['Dataset'], r['Tool']
        ref = p / 'reference' / f'{sample.split("_")[2]}.cellranger_filtered_barcodes.txt.gz'
        add(sample, tool, p / 'callsets' / f'{sample}.{tool}.txt', ref)
    # The four public MPNST runs share two distinct matched mouse references.
    for r in rows(b / 'mpnst_native_three_tool_whitelist_20260811/provenance/callset_manifest.tsv'):
        first = 'MPNST1' in r['physical_input_run']
        group, name = ('MPNST1', 'MPNST1_2020_23') if first else ('MPNST2', 'MPNST2_2022_26')
        ref = preserved / f'mpnst_native_three_tool_whitelist_20260811/{group}/reference/{name}.CellRanger9_GRCm39.filtered_barcodes.tsv.gz'
        add(r['physical_input_run'], r['tool'], resolve_source(r['path'],base=b), ref)
    p = b / 'wl_scan/20260730_rageseq_ERR3268991_cellline_control'
    for tool, sub in [('RAD','rad/scan/rageseq.txt'), ('BLAZE','blaze/whitelist.csv'), ('Flexiplex','flexiplex/f8_detection/selected.tsv')]:
        add('RAGEseq-cell-line', tool, p / 'runs' / sub, p / 'input/cellranger_filtered_barcodes.txt')
    # Selected LN reference is the named T/B proxy, not all deposited cells.
    p = b / 'wl_scan/20260730_rageseq_ERR3268990_tnbc_lymphnode_four_tool/analysis/barcode_level_annotations.tsv'
    immune = lambda r: r['in_deposited_shortread_list']=='True' and (r['deposited_label'].startswith(('T_cell','B_cell')) or r['deposited_label']=='T_B_doublet')
    for tool, col in [('RAD','called_RAD'), ('BLAZE','called_BLAZE_2.6.0a0_expect10433'), ('Flexiplex','called_Flexiplex_f8')]:
        add('RAGEseq-TNBC-LN', tool, p, p, 'barcode', lambda r,c=col:r[c]=='True', 'barcode', immune,
            'Call membership uses '+col+'; reference = deposited named T_cell/B_cell/T_B_doublet membership')
    p = b / 'wl_scan/20260730_promethion_four_tool_benchmark'
    for tool, sub in [('RAD','rad_scan_e01/promethion.txt'), ('BLAZE','blaze_expect500/whitelist.csv'), ('Flexiplex','flexiplex_f8/flexiplex_barcodes_final.txt')]:
        add('PromethION_iPSC', tool, p / 'results' / sub, p / 'analysis/barcode_level_annotations.tsv',
            ref_column='barcode', ref_filter=lambda r:r['cellranger_filtered']=='True', note='Reference = saved cellranger_filtered membership, 1022 identifiers')
    p = b / 'wl_scan/20260731_lebrigand_MOB_complete_two_accession_benchmark'
    for tool, name in [('RAD','RAD'), ('BLAZE','BLAZE_expect918'), ('Flexiplex','Flexiplex_f8')]:
        add('LeBrigand-MOB', tool, p / 'callsets' / (name+'.txt'), p / 'tables/per_barcode_membership.tsv',
            ref_column='barcode', ref_filter=lambda r:r['in_tissue']=='1', note='Reference = saved in_tissue membership, 918 identifiers; combined two-accession producer')
    p = scratch_root() / 'measles_p7_p8_four_tool_20260730'
    for short, sample in [('p7','Measles-P7'), ('p8','Measles-P8-VDJ-enriched')]:
        ref = p / 'input_links' / (short+'_shortread_cells.txt')
        for tool, sub in [('RAD', f'input_links/{short}_rad_scanwl.txt'), ('BLAZE', f'runs/{short}/blaze/whitelist.csv'), ('Flexiplex', f'runs/{short}/flexiplex/detection/selected.tsv')]:
            add(sample, tool, p / sub, ref)
    p = preserved / 'measles_p8_whole_three_tool_20260801'
    for tool, sub in [('RAD','rad/scanwl/scanwl.txt'), ('BLAZE','blaze/whitelist.csv'), ('Flexiplex','flexiplex/discovery/selected.tsv')]:
        add('Measles-P8-WTA', tool, p / 'runs' / sub, args.project_root / 'barcode_whitelists/mmr_p8_sc_bcs.txt')
    p = preserved / 'rad_biological_benchmark_20260731'
    ref = p / 'raw/GSE248115/GSM7906076_Illumina_CellRanger_barcodes.csv.gz'
    # RAD's selected true_barcode column is a saved list, not a count-derived threshold.
    rad = p / 'runs/GSE248115/RAD/GSE248115_whitelist_true.csv'
    with rad.open() as f:
        rad_calls = {r['true_barcode'] for r in csv.DictReader(f)}
    for tool, sub in [('RAD','RAD/GSE248115_whitelist_true.csv'), ('BLAZE','BLAZE_expect2462/whitelist.csv'), ('Flexiplex','Flexiplex/discovery/selected.tsv')]:
        add('Isosceles-ovarian-GSE248115', tool, p / 'runs/GSE248115' / sub, ref,
            note='RAD calls are exact saved true_barcode column' if tool=='RAD' else '')
    scmix = json.loads((out / 'validation/figures_124_scmix_rescore.json').read_text())
    sources = {r['role']:resolve_source(r['path'],base=b) for r in scmix['sources']}
    for tool in ('RAD','BLAZE','Flexiplex'):
        add('ScMixology2', tool, sources[tool], sources['truth'],
            'barcode' if tool=='Flexiplex' else None,
            (lambda r:r['dataset']=='scMixology2' and r['method']=='Flexiplex' and r['mode']=='exact_flexiplex_filter_v1.02.6') if tool=='Flexiplex' else None,
            note=('Saved membership rows: dataset=scMixology2, method=Flexiplex, mode=exact_flexiplex_filter_v1.02.6' if tool=='Flexiplex' else 'Saved selected native RAD or BLAZE expect500 selector reconstruction'))

    manifest, checks, objects = [], [], {}
    def save_set(values, sample, role, source, selection):
        body = ''.join(v+'\n' for v in sorted(values)).encode()
        content_sha = hashlib.sha256(body).hexdigest()
        if content_sha not in objects:
            destination = out / 'data/figure_04/identifier_sets' / (sample+'.'+role+'.txt.gz')
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('wb') as f:
                with gzip.GzipFile(fileobj=f, mode='wb', mtime=0, filename='') as z:z.write(body)
            objects[content_sha] = destination.relative_to(out).as_posix()
        return dict(path=objects[content_sha], sha256=sha(out/objects[content_sha]),
                    content_sha256=content_sha, identifiers=len(values), original_source=str(source),
                    original_source_sha256=sha(source), selection=selection)
    for expected in current:
        sample, tool = expected['canonical_id'], expected['tool']
        if publication_status[sample, tool] == 'aggregate-only-controlled-access':
            manifest.append(dict(canonical_id=sample, tool=tool, status='aggregate-only-controlled-access',
                callset_path='', reference_path='', callset_sha256='', reference_sha256='',
                reason='Controlled identifier files excluded; four original Visium RAD callsets also unavailable'))
            continue
        path, ref, col, filt, refcol, reffilt, note = mapping[sample,tool]
        c = rad_calls if (sample,tool)==('Isosceles-ovarian-GSE248115','RAD') else identifiers(path,col,filt)
        t = identifiers(ref,refcol,reffilt)
        got = {'calls':len(c), 'reference_n':len(t), 'tp':len(c&t), 'fp':len(c-t), 'fn':len(t-c)}
        want = {k:int(expected[k]) for k in got}
        if got != want:raise ValueError((sample,tool,got,want,path,ref))
        cs = save_set(c,sample,tool,path,('column '+col+'; ' if col else 'first token, terminal -1 removal; ')+note)
        ts = save_set(t,sample,'reference',ref,('column '+refcol+'; ' if refcol else 'first token, terminal -1 removal; ')+note)
        manifest.append(dict(canonical_id=sample,tool=tool,status='public-identifiers-recomputed',
            callset_path=cs['path'],reference_path=ts['path'],callset_sha256=cs['sha256'],reference_sha256=ts['sha256'],reason=note))
        checks.append(dict(canonical_id=sample,tool=tool,counts=got,callset=cs,reference=ts,status='passed'))
    write_rows(out / 'data/figure_04/identifier_manifest.tsv', manifest)
    write_json(out / 'validation/figures_124_public_identifier_export.json', dict(status='passed',
        code_sha256=sha(Path(__file__)), public_rows=len(checks), aggregate_only_rows=len(current)-len(checks),
        selected_table_sha256=sha(out / 'source_data/figure_04/barcode_detection_metrics.tsv'),
        identifier_manifest_sha256=sha(out / 'data/figure_04/identifier_manifest.tsv'),
        selected_unique_files=len(objects), checks=checks,
        normalization='exact saved selections; first token or named column, terminal -1 removed; sorted unique 16nt ACGT identifiers; no counts-to-callset inference'))
    print(f'Published {len(objects)} distinct identifier files for {len(checks)} public selected rows; {len(current)-len(checks)} aggregate-only controlled rows.')


if __name__ == '__main__':main()
