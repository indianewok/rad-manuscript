#!/usr/bin/env python3
"""Prepare a private Methods-only paragraph draft; preserve core algorithm text."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source-paragraphs',type=Path,required=True)
p.add_argument('--draft',type=Path,default=ROOT/'docs/manuscript_figures_567.md')
p.add_argument('--figure3-draft',type=Path,default=ROOT/'docs/manuscript_figure_03.md')
p.add_argument('--output-json',type=Path,required=True)
p.add_argument('--receipt',type=Path,default=ROOT/'validation/figures_567_methods_revision.json')
a=p.parse_args();source=json.loads(a.source_paragraphs.read_text());draft=a.draft.read_text()
assert source[59]=='Methods' and source[120]=='Statistical analysis'
def prose(start,end,text=None):
    section=(draft if text is None else text).split(start,1)[1].split(end,1)[0]
    result=[]
    for para in re.split(r'\n\s*\n',section.strip()):
        para=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',para)
        result.append(para.replace('**','').replace('`','').replace('\n',' '))
    return result
f3=prose('## Methods replacement prose\n','## Results replacement prose',a.figure3_draft.read_text())
f5=prose('### Figure 5: receptor candidates and selected LR-Split-seq comparison\n','### Figure 6:')
f6=prose('### Figure 6: genotype producers, denominators and fixed embedding\n','### Figure 7:')
f7=prose('### Figure 7: emitted segments, molecule counting and retained tests\n','## Results replacement prose')
assert f3 and len(f5)==5 and len(f6)==4 and len(f7)==4
out=[];changes=[]
for i in range(59,103):
    paragraph=source[i]
    if i==83:
        paragraph+=' Maximum resident set size was converted from KiB to decimal GB by multiplying by 1,024 and dividing by 1,000,000,000.'
        changes.append(dict(source_paragraph=i,action='add verified memory units'))
    if i==95:
        paragraph='The counting unit was a unique original-read–target-barcode pair within each correction category, including all emitted RAD concatemer records. Repeated records with the same pair were collapsed within a category. A pair could belong to more than one category when emitted records carried different observed sources; category totals were not added to obtain the denominator. Counts were summarized by target barcode and outer-joined between tools. Unselected tool–target combinations had a zero count and undefined percentage; selected targets with no assigned pairs also had an undefined percentage. Each per-target percentage divided its category count by all unique read–target pairs assigned to that barcode by the same tool, including native and source-unavailable pairs.'
        changes.append(dict(source_paragraph=i,action='clarify observed correction-pair categories, overlap and undefined percentages from current Figure3 contract'))
    out.append(paragraph)
    if i==91:
        out.extend(f3)
    if i==102:
        out.append('Author review: the intended Visium HD spatial recipe above is not independently reproduced. The retained detection and demultiplexing count sources measure different stages; the detection totals, complete grid and tissue mask have been verified. Selected Seurat nCount_Spatial values and full barcode-to-bin creation provenance remain unresolved. A verified shared-scale spatial result and final artwork export remain unavailable. Space Ranger here processes converted Nanopore data, not an independent Illumina reference.')
out.extend([source[103],f5[0],source[106],source[107],*f5[1:],
    source[109],f6[0],f6[1],f6[2],source[113],f7[0],source[115],f7[1],f7[2],
    'The adjusted-P cutoffs were 1e-8, 1e-6, 1e-5, 1e-4, 0.001, 0.005, 0.01, 0.05 and 0.1. Absolute log2-fold-change cutoffs were 0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5 and 3. Adjusted P values had to be strictly below the cutoff, and directional log2 fold changes had to strictly exceed the effect cutoff. Illumina reference thresholds remained fixed throughout.',
    'Author review: the original direct Wilcoxon P values and effects are retained. Their current-table lineage was checked exactly; BH, membership and threshold metrics were recomputed. The selected RAD emitted-assignment checkpoint was recovered and its full recorded hash, schema and 57,885,606 rows were verified. It retains original-read IDs, cell barcodes, UMIs, raw barcodes and correction flags; orientation/concatemer suffixes were already removed, and gene IDs and segment coordinates are absent. The emitted RAD FASTQ and frozen read-to-gene source remain unavailable at checked paths, so a complete gene/segment-boundary ledger or upstream replay is not claimed. The exact Figure 7C fit/annotation binding remains unresolved. No replacement inferential procedure has been introduced.',
    source[120],source[121],
    'Author review: existing selected statistical procedures and significance annotations are preserved. The selected LR-Split-seq native record establishes a paired two-sided t test. Figure 6 one-way/two-way ANOVA wording remains an execution-provenance gap: an inspected two-way analysis used different donor counts and cannot bind the selected panel. This draft does not select a replacement test. Newly produced RAGE data require the selected analysis to be recalculated and inspected before prior annotations can be certified.'])
# Algorithm overview and every algorithm paragraph are byte-for-byte preserved.
algorithm=source[60:79]
assert out[1:20]==algorithm
assert source[121] in out
assert not any(re.search(r'\bFigure\s+8\b|\b7E\b',p) for p in out)
a.output_json.parent.mkdir(parents=True,exist_ok=True)
a.output_json.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
receipt=dict(status='passed',source=str(a.source_paragraphs),source_sha256=hashlib.sha256(a.source_paragraphs.read_bytes()).hexdigest(),
    source_paragraph_range_zero_based=[59,121],core_algorithm_range_zero_based=[60,78],core_algorithm_exact=True,
    statistical_paragraph_121_exact=True,output_json=str(a.output_json),output_sha256=hashlib.sha256(a.output_json.read_bytes()).hexdigest(),
    output_paragraphs=len(out),changes=changes+[
        dict(source_paragraphs=[91],action='integrate completed matched RAGE raw experiment and normalized metric'),
        dict(source_paragraphs=[104,105,108],action='selected Split-seq producers, 568 keyed cells, preserved paired t; explicit receptor and depth-matched UMI source holds'),
        dict(source_paragraphs=[110,111,112],action='exact genotype producers; VCF records/duplicates; separate Figure6C denominator; inspected SCT/UMAP recipe'),
        dict(source_paragraphs=[114,116,117,118,119],action='selected4acbe00 segments and exact molecule contract; pair-only8135; log2(1+CP10K); retained tests; F7C hold')],
    draft_sha256=hashlib.sha256(a.draft.read_bytes()).hexdigest(),
    figure3_draft_sha256=hashlib.sha256(a.figure3_draft.read_bytes()).hexdigest(),
    limitation='Methods-only author-review text; remaining scientific source gates and native Word/pagination QA remain pending')
a.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
print('Prepared Methods-only paragraphs; core algorithm and existing statistical paragraph preserved exactly')
