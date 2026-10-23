#!/usr/bin/env python3
# Assemble the RAGE-seq false-whitelist manuscript-era package.
# Mirrors the sctagger_L_false_whitelist_20260813 conventions:
# wide CSV rows pair by lexical sampled-whitelist rank within each replicate,
# identity-bearing long TSV keeps barcode/replicate/rank/tool/count.
# Semantics per tool (documented in README):
#   RAD    - emitted records per barcode (128-147 read IDs per replicate emit
#            two records; record-level retained to match the manuscript columns).
#   BLAZE  - record-level counts recovered from the manuscript Figure 3E sheet
#            (raw runs not archived; BLAZE emits at most one record per read).
#   Flexiplex - emitted records per barcode (record-level, matching the RAD and
#            BLAZE column semantics); a strict companion table excludes read IDs
#            with more than one emitted record.
import json, csv, os

S = '/private/tmp/claude-501/-Users-cmv-Desktop/9662965c-f2c1-4519-9736-aa517675a169/scratchpad'
P = f'{S}/rage_pkg'
rad = json.load(open(f'{S}/rage_offlist_rad_perbc.json'))
blaze = json.load(open(f'{S}/rage_offlist_blaze_perbc.json'))
flex = json.load(open(f'{S}/rage_offlist_flex_perbc.json'))
flex_strict = json.load(open(f'{S}/rage_offlist_flex_perbc_strict.json'))

tools = {'RAD': rad, 'BLAZE': blaze, 'Flexiplex': flex}
reps = ('1', '2', '3')

# Gates.
assert tuple(sum(rad[r].values()) for r in reps) == (49816, 49942, 49232)
assert tuple(sum(blaze[r].values()) for r in reps) == (1355389, 1403176, 1357996)
for r in reps:
    u = set(rad[r])
    for name, d in tools.items():
        assert set(d[r]) == u, f'universe mismatch {name} rep{r}'
    assert len(u) == 4505

# Wide CSV: rows are lexical rank 1..4505 within each replicate.
orders = {r: sorted(rad[r]) for r in reps}
hdr = [f'{t}_rep{r}' for t in ('RAD', 'BLAZE', 'Flexiplex') for r in reps]
with open(f'{P}/results/false_target_assigned_reads_wide.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(hdr)
    for i in range(4505):
        w.writerow([tools[t][r].get(orders[r][i], 0)
                    for t in ('RAD', 'BLAZE', 'Flexiplex') for r in reps])

# Long identity-bearing TSV.
with open(f'{P}/results/false_target_assigned_reads_long.tsv', 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['barcode', 'replicate', 'rank', 'tool', 'count'])
    for r in reps:
        for i, bc in enumerate(orders[r], 1):
            for t in ('RAD', 'BLAZE', 'Flexiplex'):
                w.writerow([bc, f'rep{r}', i, t, tools[t][r].get(bc, 0)])

# Strict Flexiplex companion (identity-bearing).
with open(f'{P}/results/flexiplex_strict_per_barcode.tsv', 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['barcode', 'replicate', 'rank', 'strict_count', 'record_count'])
    for r in reps:
        for i, bc in enumerate(orders[r], 1):
            w.writerow([bc, f'rep{r}', i, flex_strict[r].get(bc, 0), flex[r].get(bc, 0)])

# Totals with full accounting.
flex_recs = {'1': 1597157, '2': 1679710, '3': 1647416}
flex_log = {'1': 1591111, '2': 1672992, '3': 1640883}
with open(f'{P}/results/read_level_totals.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['tool', 'replicate', 'per_cell_table_sum', 'figure_3D_total', 'notes'])
    fig3d = {'RAD': (49816, 49942, 49232), 'BLAZE': (1354508, 1402306, 1357281),
             'Flexiplex': (1591111, 1672992, 1640883)}
    for t in ('RAD', 'BLAZE', 'Flexiplex'):
        for j, r in enumerate(reps):
            s = sum(tools[t][r].values())
            note = ''
            if t == 'RAD':
                note = 'record-level; 128/143/147 duplicate read IDs per rep'
            if t == 'BLAZE':
                note = 'sheet records exceed 3D total; 3D counted reads'
            if t == 'Flexiplex':
                note = (f'record-level; strict_sum={sum(flex_strict[r].values())}, '
                        f'log reads-with-barcode={flex_log[r]}, '
                        f'ambiguous read IDs excluded')
            w.writerow([t, f'rep{r}', s, fig3d[t][j], note])

print('wide/long/totals written')
for t in ('RAD', 'BLAZE', 'Flexiplex'):
    print(t, [sum(tools[t][r].values()) for r in reps])
