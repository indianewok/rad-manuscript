#!/usr/bin/env python3
import subprocess, collections, json, sys, re
B='/Users/cmv/Dropbox (Dartmouth College)/rad_paper_data_backup/103025_results/flexiplex/offlist'
paths={1:f'{B}/offlist_v1/offlist_v1.fastq.gz',2:f'{B}/offlist_v2/offlist_v2.fastq.gz',3:f'{B}/offlist_v2/offlist_v3.fastq.gz'}
suf=re.compile(r'_([+-])(\d+)of(\d+)$')
out={}
for r,p in paths.items():
    recs=[]
    proc=subprocess.Popen(['seqkit','seq','-n',p],stdout=subprocess.PIPE,text=True,bufsize=1<<20)
    for line in proc.stdout:
        head=line.rstrip('\n')
        cb=head.split('CB:Z:')[1].split('\t')[0].strip()
        frag=head.split('\t')[0].split('#',1)[1]
        m=suf.search(frag)
        rid=frag[:m.start()] if m else frag
        recs.append((rid,cb))
    if proc.wait()!=0: sys.exit('seqkit fail')
    mult=collections.Counter(r0 for r0,_ in recs)
    amb={i for i,c in mult.items() if c>1}
    per=collections.Counter(cb for rid,cb in recs if rid not in amb)
    print(f'rep{r}: records={len(recs)} ambiguous_ids={len(amb)} strict_total={sum(per.values())} distinct={len(per)}',flush=True)
    out[r]=dict(per)
json.dump(out,open('rage_offlist_flex_perbc_strict.json','w'))
# RAD multiplicity check
import csv
D='/Users/cmv/Dropbox (Dartmouth College)/rad_paper_data_backup/121325_results/rad/demultiplexed/false_positive_wl'
for r in (1,2,3):
    ids=collections.Counter()
    with open(f'{D}/082825_rad_fp{r}/extracted_headers.csv') as f:
        rd=csv.reader(f); next(rd)
        for row in rd: ids[row[0]]+=1
    dup=sum(1 for c in ids.values() if c>1)
    print(f'rad fp{r}: ids={len(ids)} duplicate_ids={dup}',flush=True)
print('DONE')
