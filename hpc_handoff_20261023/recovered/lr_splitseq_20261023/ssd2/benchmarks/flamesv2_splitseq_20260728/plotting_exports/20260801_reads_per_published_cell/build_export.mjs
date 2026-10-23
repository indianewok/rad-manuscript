import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/plotting_exports/20260801_reads_per_published_cell";
const csvOutput = path.join(outputDir, "splitseq_published_barcode_read_counts.csv");
const xlsxOutput = path.join(outputDir, "splitseq_published_barcode_read_counts.xlsx");

const sources = {
  master: "/Volumes/CMV_SSD_2/results/misc/splitseq_shortread_umis_20260728/published_568_barcode_map.csv",
  rad: "/Volumes/CMV_SSD_2/results/rad/demultiplexed/splitseq/20260801_reverse_complement_whitelist_clean_main_ed2/analysis/ed1_ed2_per_published_cell.tsv",
  components: "/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/component_no_polyt_t4/per_published_cell_counts.tsv",
  matched: "/Volumes/CMV_SSD_2/benchmarks/flamesv2_splitseq_20260728/joint_matched_split_t4/per_published_cell.tsv",
  historical: path.join(outputDir, "historical_two_pass_per_published_cell.tsv"),
};

function parseDelimited(text, delimiter) {
  const lines = text.trimEnd().split(/\r?\n/);
  const header = lines[0].split(delimiter);
  return lines.slice(1).filter(Boolean).map((line) => {
    const values = line.split(delimiter);
    if (values.length !== header.length) {
      throw new Error(`Malformed row: expected ${header.length} fields, found ${values.length}`);
    }
    return Object.fromEntries(header.map((name, index) => [name, values[index]]));
  });
}

function csvEscape(value) {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function keyedMap(rows, keyField, valueField, filter = () => true) {
  const map = new Map();
  for (const row of rows) {
    if (!filter(row)) continue;
    const key = row[keyField];
    if (map.has(key)) throw new Error(`Duplicate key ${key}`);
    map.set(key, Number(row[valueField]));
  }
  return map;
}

function assertEqual(actual, expected, label) {
  if (actual !== expected) throw new Error(`${label}: expected ${expected}, found ${actual}`);
}

await fs.mkdir(outputDir, { recursive: true });
const [masterText, radText, componentText, matchedText, historicalText] = await Promise.all(
  Object.values(sources).map((source) => fs.readFile(source, "utf8")),
);

const master = parseDelimited(masterText, ",");
const radRows = parseDelimited(radText, "\t");
const componentRows = parseDelimited(componentText, "\t");
const matchedRows = parseDelimited(matchedText, "\t");
const historicalRows = parseDelimited(historicalText, "\t");

assertEqual(master.length, 568, "published-cell row count");
assertEqual(new Set(master.map((row) => row.canonical_barcode)).size, 568, "unique canonical barcodes");

const radEd2 = keyedMap(radRows, "barcode", "reads", (row) => row.tool === "ED2 current main");
const flexPolyT = keyedMap(componentRows, "cell", "tool_reads", (row) => row.tool === "Flexiplex polyT");
const flexNoPolyT = keyedMap(componentRows, "cell", "tool_reads", (row) => row.tool === "Flexiplex no-polyT");
const flamesMatched = keyedMap(matchedRows, "barcode", "joint_flames_reads");
const flamesHistorical = keyedMap(historicalRows, "barcode", "historical_two_pass_reads");

for (const [label, map] of Object.entries({ radEd2, flexPolyT, flexNoPolyT, flamesMatched, flamesHistorical })) {
  assertEqual(map.size, 568, `${label} barcode count`);
  for (const row of master) {
    if (!map.has(row.canonical_barcode)) throw new Error(`${label} missing ${row.canonical_barcode}`);
  }
}

const header = [
  "published_rank",
  "published_index_barcode",
  "published_cell_barcode",
  "sample",
  "canonical_barcode",
  "bam_cb",
  "published_sr_umi_cts",
  "published_lr_umi_cts",
  "rad_ed2_assigned_reads",
  "flex_component_no_polyt_assigned_reads",
  "flex_component_polyt_assigned_reads",
  "flames_matched_split_polyt_assigned_reads",
  "flames_historical_two_pass_assigned_reads",
];

const dataRows = master.map((row) => [
  Number(row.published_rank),
  row.published_index_barcode,
  row.published_cell_barcode,
  row.sample,
  row.canonical_barcode,
  row.bam_cb,
  Number(row.published_sr_umi_cts),
  Number(row.published_lr_umi_cts),
  radEd2.get(row.canonical_barcode),
  flexNoPolyT.get(row.canonical_barcode),
  flexPolyT.get(row.canonical_barcode),
  flamesMatched.get(row.canonical_barcode),
  flamesHistorical.get(row.canonical_barcode),
]);

const expectedSums = {
  8: 2078171,
  9: 2062349,
  10: 1156252,
  11: 2331521,
  12: 2209802,
};
for (const [indexText, expected] of Object.entries(expectedSums)) {
  const index = Number(indexText);
  const actual = dataRows.reduce((sum, row) => sum + row[index], 0);
  assertEqual(actual, expected, `${header[index]} sum`);
}

const csvLines = [header, ...dataRows].map((row) => row.map(csvEscape).join(","));
await fs.writeFile(csvOutput, `${csvLines.join("\n")}\n`, "utf8");

const workbook = Workbook.create();
const dataSheet = workbook.worksheets.add("Per Cell Reads");
const summarySheet = workbook.worksheets.add("Summary");
const methodsSheet = workbook.worksheets.add("Methods");

dataSheet.showGridLines = false;
dataSheet.getRangeByIndexes(0, 0, dataRows.length + 1, header.length).values = [header, ...dataRows];
dataSheet.freezePanes.freezeRows(1);
dataSheet.freezePanes.freezeColumns(4);
dataSheet.getRange(`A1:M1`).format = {
  fill: "#184E77",
  font: { bold: true, color: "#FFFFFF" },
  wrapText: true,
  verticalAlignment: "center",
};
dataSheet.getRange("A1:M569").format.borders = {
  insideHorizontal: { style: "thin", color: "#D9E2E8" },
  bottom: { style: "thin", color: "#AABBC5" },
};
dataSheet.getRange("A2:A569").format.numberFormat = "#,##0";
dataSheet.getRange("G2:M569").format.numberFormat = "#,##0";
dataSheet.getRange("A1:M569").format.rowHeight = 18;
dataSheet.getRange("A1:M1").format.rowHeight = 40;
dataSheet.getRange("A:A").format.columnWidth = 12;
dataSheet.getRange("B:B").format.columnWidth = 21;
dataSheet.getRange("C:C").format.columnWidth = 28;
dataSheet.getRange("D:D").format.columnWidth = 15;
dataSheet.getRange("E:F").format.columnWidth = 34;
dataSheet.getRange("G:M").format.columnWidth = 22;
dataSheet.tables.add("A1:M569", true, "PerCellReadsTable");

summarySheet.showGridLines = false;
summarySheet.getRange("A1:E1").merge();
summarySheet.getRange("A1").values = [["SPLiT-seq published-barcode read-count export"]];
summarySheet.getRange("A1:E1").format = {
  fill: "#184E77",
  font: { bold: true, color: "#FFFFFF", size: 16 },
  verticalAlignment: "center",
};
summarySheet.getRange("A1:E1").format.rowHeight = 30;
summarySheet.getRange("A3:E8").values = [
  ["Run", "Per-barcode read sum", "Globally unique published-cell reads", "Read-cell excess", "Cells with >0 reads"],
  ["RAD ED2", null, 2063573, null, null],
  ["Flexiplex component, no poly-T", null, 2047298, null, null],
  ["Flexiplex component, poly-T", null, 1152260, null, null],
  ["FLAMESv2 MATCHED_SPLIT, poly-T", null, 2305812, null, null],
  ["Historical FLAMES two-pass", null, 2190938, null, null],
];
const dataColumns = ["I", "J", "K", "L", "M"];
for (let row = 4; row <= 8; row += 1) {
  const dataColumn = dataColumns[row - 4];
  summarySheet.getRange(`B${row}`).formulas = [[`=SUM('Per Cell Reads'!${dataColumn}2:${dataColumn}569)`]];
  summarySheet.getRange(`D${row}`).formulas = [[`=B${row}-C${row}`]];
  summarySheet.getRange(`E${row}`).formulas = [[`=COUNTIF('Per Cell Reads'!${dataColumn}2:${dataColumn}569,\">0\")`]];
}
summarySheet.getRange("A3:E3").format = {
  fill: "#2A6F97",
  font: { bold: true, color: "#FFFFFF" },
  wrapText: true,
};
summarySheet.getRange("B4:E8").format.numberFormat = "#,##0";
summarySheet.getRange("A3:E8").format.borders = {
  insideHorizontal: { style: "thin", color: "#D9E2E8" },
  bottom: { style: "thin", color: "#AABBC5" },
};
summarySheet.getRange("A:A").format.columnWidth = 36;
summarySheet.getRange("B:D").format.columnWidth = 24;
summarySheet.getRange("E:E").format.columnWidth = 20;
summarySheet.getRange("A10:E12").merge();
summarySheet.getRange("A10").values = [[
  "Per-barcode values count distinct source reads within each published physical-cell barcode. A source read assigned to multiple cells contributes once to each cell, so column sums are read-cell pairs and exceed globally unique source-read totals. Published-list membership is not independent proof of correct physical-cell assignment.",
]];
summarySheet.getRange("A10:E12").format = {
  fill: "#EAF2F8",
  font: { color: "#1F2937" },
  wrapText: true,
  verticalAlignment: "top",
};

methodsSheet.showGridLines = false;
methodsSheet.getRange("A1:B1").values = [["Field", "Definition / source"]];
methodsSheet.getRange("A1:B1").format = {
  fill: "#184E77",
  font: { bold: true, color: "#FFFFFF" },
};
const methodRows = [
  ["Join key", "canonical_barcode: normalized physical cell in BC3/v2_BC2/v1_BC1/v1 order; R/T primer variants collapse to the same T-primer physical-well key."],
  ["RAD ED2", sources.rad],
  ["Flexiplex component runs", sources.components],
  ["FLAMESv2 MATCHED_SPLIT", sources.matched],
  ["Historical FLAMES two-pass", `${sources.historical}; reconstructed from pass-2 matched_barcode_stat.tsv.gz using the validated composite normalization.`],
  ["Published 568 metadata", sources.master],
  ["Metric", "Distinct source reads assigned to each published barcode. This is an assignment-depth metric, not a truth-conditioned correctness metric."],
];
methodsSheet.getRangeByIndexes(1, 0, methodRows.length, 2).values = methodRows;
methodsSheet.getRange("A1:B8").format.borders = {
  insideHorizontal: { style: "thin", color: "#D9E2E8" },
  bottom: { style: "thin", color: "#AABBC5" },
};
methodsSheet.getRange("A:A").format.columnWidth = 30;
methodsSheet.getRange("B:B").format.columnWidth = 110;
methodsSheet.getRange("B2:B8").format.wrapText = true;
methodsSheet.getRange("A1:B8").format.verticalAlignment = "top";

const inspection = await workbook.inspect({
  kind: "table",
  range: "Summary!A1:E12",
  include: "values,formulas",
  tableMaxRows: 15,
  tableMaxCols: 8,
});
console.log(inspection.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

for (const [sheetName, range, fileName] of [
  ["Per Cell Reads", "A1:M20", "preview_data.png"],
  ["Summary", "A1:E12", "preview_summary.png"],
  ["Methods", "A1:B8", "preview_methods.png"],
]) {
  const preview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(path.join(outputDir, fileName), new Uint8Array(await preview.arrayBuffer()));
}

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(xlsxOutput);

console.log(JSON.stringify({ csvOutput, xlsxOutput, rows: dataRows.length, expectedSums }, null, 2));
