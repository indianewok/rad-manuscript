"""
Build a small GraphPad Prism file for Panel E only, with values on the raw
count scale and on the (non-log) ncpm scale. Saved with a .prism extension
per request; the content is the standard Prism XML (PZFX) schema, so if a
particular Prism version refuses the .prism extension you can rename the
file to .pzfx and it will open.
"""
import csv
import os
from xml.sax.saxutils import escape

FIG_DIR = "."
OUT_PATH = "supp_figure_1_panelE_raw.prism"

GROUP_LABELS = {
    "double_positive_Percula": "Double-positive Percula",
    "double_positive_RAD":     "Double-positive RAD",
    "single_positive_RAD":     "Single-positive RAD",
    "Neither":                 "Neither",
}
HEADER_ORDER = list(GROUP_LABELS.keys())


def fmt_count(v: str) -> str:
    if v is None or v == "" or v.lower() == "na":
        return ""
    try:
        f = float(v)
    except ValueError:
        return v
    if f.is_integer():
        return str(int(f))
    return f"{f:.4f}"


def fmt_ncpm(v: str) -> str:
    if v is None or v == "" or v.lower() == "na":
        return ""
    try:
        f = float(v)
    except ValueError:
        return v
    return f"{f:.4f}"


def read_wide(path):
    with open(path, "rt") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = [r for r in reader]
    return headers, rows


def column_block(title, values, fmt_fn, width=140):
    d_lines = "\n".join(f"        <d>{fmt_fn(v)}</d>" for v in values)
    return (
        f'  <YColumn Width="{width}" Decimals="4" Subcolumns="1">\n'
        f'    <Title>{escape(title)}</Title>\n'
        f'    <Subcolumn>\n'
        f'{d_lines}\n'
        f'    </Subcolumn>\n'
        f'  </YColumn>'
    )


def build_table(table_id, title, csv_path, fmt_fn):
    headers, rows = read_wide(csv_path)
    cols = {h: [] for h in headers}
    for r in rows:
        for i, h in enumerate(headers):
            cols[h].append(r[i] if i < len(r) else "")
    col_xml = "\n".join(
        column_block(GROUP_LABELS.get(h, h), cols[h], fmt_fn)
        for h in HEADER_ORDER if h in cols
    )
    return (
        f'<Table ID="{table_id}" XFormat="none" YFormat="replicates" '
        f'Replicates="1" TableType="OneWay">\n'
        f'  <Title>{escape(title)}</Title>\n'
        f'{col_xml}\n'
        f'</Table>'
    )


def build_info(info_id):
    notes = (
        "Supplementary Figure 4, Panel E. Bin-level values on the raw count "
        "scale (Table 1) and on the (non-log) ncpm scale (Table 2). ncpm = "
        "count * 1e6 / total_count_for_that_pipeline (Percula uses a single "
        "total across the reference; RAD uses per-sample totals).\n\n"
        "Double-positive Percula and Double-positive RAD are the same bin "
        "set (called valid by both pipelines) plotted with Percula counts "
        "vs RAD counts respectively. Single-positive RAD and Neither are "
        "RAD-derived values for bins called valid only by RAD and bins "
        "called valid by neither pipeline.\n\n"
        "File extension: .prism. The XML format inside is the standard "
        "Prism PZFX schema. If your Prism version does not open .prism, "
        "rename to .pzfx."
    )
    constants = [
        ("Source script",  "supp_fig4.R + export_panel_E_raw.R"),
        ("Bin size",       "16 um"),
        ("Pipelines",      "Percula (10X Visium HD SpaceRanger) and RAD"),
        ("Scales",         "raw UMI counts and ncpm (count * 1e6 / total)"),
    ]
    const_xml = "\n".join(
        f'  <Constant>\n    <Name>{escape(n)}</Name>\n'
        f'    <Value>{escape(v)}</Value>\n  </Constant>'
        for n, v in constants
    )
    return (
        f'<Info ID="{info_id}">\n'
        f'  <Title>Panel E notes</Title>\n'
        f'{const_xml}\n'
        f'  <Notes>{escape(notes)}</Notes>\n'
        f'</Info>'
    )


def main():
    raw_path  = os.path.join(FIG_DIR, "raw_data/panel_E_four_groups_raw_counts.csv")
    ncpm_path = os.path.join(FIG_DIR, "raw_data/panel_E_four_groups_ncpm.csv")

    raw_id   = "Table_PanelE_raw_counts"
    ncpm_id  = "Table_PanelE_ncpm"
    info_id  = "Info0"

    raw_table = build_table(
        raw_id,
        "Panel E - raw UMI counts per bin (4 pooled groups)",
        raw_path, fmt_count
    )
    ncpm_table = build_table(
        ncpm_id,
        "Panel E - ncpm per bin (counts per million, not log-transformed)",
        ncpm_path, fmt_ncpm
    )
    info_block = build_info(info_id)

    table_seq = "\n".join(f'  <Ref ID="{t}" />' for t in [raw_id, ncpm_id])
    info_seq  = f'  <Ref ID="{info_id}" />'

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<GraphPadPrismFile PrismXMLVersion="5.00">\n'
        '<Created>\n'
        '  <OriginalVersion CreatedByProgram="Python pzfx builder" '
        'CreatedByVersion="1.0" DateTime="2026-05-12T00:00:00-05:00" />\n'
        '</Created>\n'
        '<InfoSequence>\n'
        f'{info_seq}\n'
        '</InfoSequence>\n'
        '<TableSequence>\n'
        f'{table_seq}\n'
        '</TableSequence>\n'
        + info_block + "\n"
        + raw_table + "\n"
        + ncpm_table + "\n"
        '</GraphPadPrismFile>\n'
    )

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(xml)
    size_mb = os.path.getsize(OUT_PATH) / 1e6
    print(f"Wrote {OUT_PATH}")
    print(f"Size: {size_mb:.1f} MB")
    print(f"Tables: {raw_id}, {ncpm_id}")


if __name__ == "__main__":
    main()
