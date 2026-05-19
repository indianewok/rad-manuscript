"""
Build a subsampled GraphPad Prism .pzfx file for supplementary figure 4.

Same structure as build_supp_fig4_prism.py but caps each column at MAX_PER_COL
points (random subsample). Useful for fast Prism opening; the full data is
preserved in the raw_data CSVs.
"""
import csv
import gzip
import os
import random
from xml.sax.saxutils import escape

random.seed(42)

FIG_DIR = "."
OUT_PZFX = "supp_figure_1_violins_and_heatmap_subsampled.pzfx"

SAMPLES = ["PBC44593", "PBC44760", "PBC49262", "PBC52788"]
CLASS_KEYS = ["TP", "FP", "FN", "TN"]
CLASS_LONG = {
    "TP": "Both (RAD+Seurat)",
    "FP": "RAD only",
    "FN": "Seurat only",
    "TN": "Neither",
}
MAX_PER_COL = 20000  # cap per column for fast Prism rendering


def fmt(v: str) -> str:
    if v is None or v == "" or v.lower() == "na":
        return ""
    try:
        f = float(v)
    except ValueError:
        return v
    return f"{f:.4f}"


def subsample(values, k):
    vals = [v for v in values if v != "" and v is not None]
    if len(vals) <= k:
        return vals
    return random.sample(vals, k)


def read_wide_csv(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = [row for row in reader]
    return headers, rows


def column_block(title, values, width=110):
    d_lines = "\n".join(f"        <d>{fmt(v)}</d>" for v in values)
    return (
        f'  <YColumn Width="{width}" Decimals="4" Subcolumns="1">\n'
        f'    <Title>{escape(title)}</Title>\n'
        f'    <Subcolumn>\n'
        f'{d_lines}\n'
        f'    </Subcolumn>\n'
        f'  </YColumn>'
    )


def build_per_sample_violin_table(table_id, sample):
    path = os.path.join(FIG_DIR, "prism_violin",
                        f"{sample}_log1p_ncpm_by_class.csv")
    headers, rows = read_wide_csv(path)
    col_idx = {h: i for i, h in enumerate(headers)}
    columns = {k: subsample([r[col_idx[k]] for r in rows
                             if col_idx[k] < len(r)], MAX_PER_COL)
               for k in CLASS_KEYS}
    title = (f"Panel B — {sample} log1p(ncpm) by class "
             f"(subsampled to {MAX_PER_COL}/group; full data in CSVs)")
    col_xml = "\n".join(
        column_block(f"{k} — {CLASS_LONG[k]}", columns[k])
        for k in CLASS_KEYS
    )
    return (
        f'<Table ID="{table_id}" XFormat="none" YFormat="replicates" '
        f'Replicates="1" TableType="OneWay">\n'
        f'  <Title>{escape(title)}</Title>\n'
        f'{col_xml}\n'
        f'</Table>'
    )


def build_panel_E_table(table_id):
    path = os.path.join(FIG_DIR, "raw_data/panel_E_four_groups_wide.csv")
    headers, rows = read_wide_csv(path)
    cols = {h: subsample([r[i] for r in rows if i < len(r)], MAX_PER_COL)
            for i, h in enumerate(headers)}

    label_map = {
        "double_positive_Percula": "Double-positive Percula",
        "double_positive_RAD":     "Double-positive RAD",
        "single_positive_RAD":     "Single-positive RAD",
        "Neither":                 "Neither",
    }
    title = (f"Panel E - four-group comparison "
             f"(subsampled to {MAX_PER_COL}/group; full data in CSVs)")
    col_xml = "\n".join(
        column_block(label_map.get(h, h), cols[h]) for h in headers
    )
    return (
        f'<Table ID="{table_id}" XFormat="none" YFormat="replicates" '
        f'Replicates="1" TableType="OneWay">\n'
        f'  <Title>{escape(title)}</Title>\n'
        f'{col_xml}\n'
        f'</Table>'
    )


def build_heatmap_table(table_id):
    path = os.path.join(FIG_DIR, "raw_data/sample_correlations_16um.csv")
    headers, rows = read_wide_csv(path)
    idx = {h: i for i, h in enumerate(headers)}
    matrix = {}
    for r in rows:
        a, b = r[idx["a"]], r[idx["b"]]
        matrix[(a, b)] = r[idx["pearson_log1p_intissue"]]

    row_titles_xml = "    <Subcolumn>\n" + "\n".join(
        f"      <d>{escape(s)}</d>" for s in SAMPLES
    ) + "\n    </Subcolumn>"
    row_titles_block = (
        f'  <RowTitlesColumn Width="120">\n'
        f'{row_titles_xml}\n'
        f'  </RowTitlesColumn>'
    )

    y_blocks = []
    for b in SAMPLES:
        values = [matrix.get((a, b), "") for a in SAMPLES]
        y_blocks.append(column_block(b, values, width=90))

    title = ("Panel D — Cross-sample Pearson r "
             "(in_tissue, RAD log1p(ncpm))")
    return (
        f'<Table ID="{table_id}" XFormat="none" YFormat="replicates" '
        f'Replicates="1" TableType="TwoWay">\n'
        f'  <Title>{escape(title)}</Title>\n'
        f'{row_titles_block}\n'
        + "\n".join(y_blocks) + "\n"
        f'</Table>'
    )


def build_info_table(info_id):
    notes = (
        "Supplementary Figure 4 — RAD vs Seurat 16 um Visium-HD comparison.\n\n"
        f"This SUBSAMPLED file caps each violin column at {MAX_PER_COL} "
        f"random points for fast Prism rendering. Full data lives in the "
        f"raw_data/ CSVs and in the *_violins_and_heatmap.pzfx (non-subsampled) "
        f"file.\n\n"
        "Panel B tables (one per sample): log1p(ncpm) per bin by class.\n"
        "  TP = Both, FP = RAD only, FN = Seurat only, TN = Neither.\n\n"
        "Panel E table: shared-TP Seurat vs RAD plus single-positive RAD.\n\n"
        "Panel D table: cross-sample Pearson r of log1p(ncpm), in-tissue bins."
    )
    constants = [
        ("Project",       "RAD paper — Figure 4 Visium"),
        ("Source script", "supp_fig4.R"),
        ("Bin size",      "16 um"),
        ("Samples",       ", ".join(SAMPLES)),
        ("Metric",        "log1p(ncpm)  ;  ncpm = counts * 1e6 / total"),
        ("Subsampling",   f"{MAX_PER_COL} points per column (seed=42)"),
    ]
    const_xml = "\n".join(
        f'  <Constant>\n    <Name>{escape(n)}</Name>\n'
        f'    <Value>{escape(v)}</Value>\n  </Constant>'
        for n, v in constants
    )
    return (
        f'<Info ID="{info_id}">\n'
        f'  <Title>Project notes</Title>\n'
        f'{const_xml}\n'
        f'  <Notes>{escape(notes)}</Notes>\n'
        f'</Info>'
    )


def main():
    table_ids = []
    table_blocks = []
    for s in SAMPLES:
        tid = f"Table_PanelB_{s}"
        table_ids.append(tid)
        table_blocks.append(build_per_sample_violin_table(tid, s))
    panel_E_id = "Table_PanelE_four_groups"
    table_ids.append(panel_E_id)
    table_blocks.append(build_panel_E_table(panel_E_id))
    panel_D_id = "Table_PanelD_correlation_heatmap"
    table_ids.append(panel_D_id)
    table_blocks.append(build_heatmap_table(panel_D_id))

    info_id = "Info0"
    info_block = build_info_table(info_id)
    table_seq_xml = "\n".join(f'  <Ref ID="{t}" />' for t in table_ids)
    info_seq_xml = f'  <Ref ID="{info_id}" />'

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<GraphPadPrismFile PrismXMLVersion="5.00">\n'
        '<Created>\n'
        '  <OriginalVersion CreatedByProgram="Python pzfx builder" '
        'CreatedByVersion="1.0" DateTime="2026-05-12T00:00:00-05:00" />\n'
        '</Created>\n'
        '<InfoSequence>\n'
        f'{info_seq_xml}\n'
        '</InfoSequence>\n'
        '<TableSequence>\n'
        f'{table_seq_xml}\n'
        '</TableSequence>\n'
        + info_block + "\n"
        + "\n".join(table_blocks) + "\n"
        '</GraphPadPrismFile>\n'
    )

    with open(OUT_PZFX, "w", encoding="utf-8") as f:
        f.write(xml)

    size = os.path.getsize(OUT_PZFX) / 1e6
    print(f"Wrote {OUT_PZFX}")
    print(f"Size: {size:.1f} MB")


if __name__ == "__main__":
    main()
