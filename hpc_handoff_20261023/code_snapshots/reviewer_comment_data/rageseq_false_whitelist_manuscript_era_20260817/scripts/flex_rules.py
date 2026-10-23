#!/usr/bin/env python3
import subprocess, collections, json, sys, re
B='/Users/cmv/Dropbox (Dartmouth College)/rad_paper_data_backup/103025_results/flexiplex/offlist'
paths={1:f'{B}/offlist_v1/offlist_v1.fastq.gz',2:f'{B}/offlist_v2/offlist_v2.fastq.gz',3:f'{B}/offlist_v3/offlist_v3.fastq.gz'}
paths[3]=f'{B}/offlist_v2/offlist_v3.fastq.gz'
gates={1:1591111,2:1672992,3:1640883}
suf=re.compile(r'_([+-])(\d+)of(\d+)$')
out={}
for r,p in paths.items():
    rec=0; only1of1=0; k1=0; ids=set(); perbc=collections.Counter()
    proc=subprocess.Popen(['seqkit','seq','-n',p],stdout=subprocess.PIPE,text=True,bufsize=1<<20)
    for line in proc.stdout:
        head=line.rstrip('\n')
        cb=head.split('CB:Z:')[1].split('\t')[0].strip()
        core=head.split('\t')[0]
        frag=core.split('#',1)[1]
        m=suf.search(frag)
        rid=frag[:m.start()] if m else frag
        n=int(m.group(3)) if m else 1
        k=int(m.group(2)) if m else 1
        rec+=1; ids.add(rid)
        if k==1: k1+=1
        if n==1:
            only1of1+=1; perbc[cb]+=1
    if proc.wait()!=0: sys.exit('seqkit fail')
    print(f'rep{r}: records={rec} unique_ids={len(ids)} n1only={only1of1} k1={k1} gate={gates[r]}', flush=True)
    print(f'   matches: records={rec==gates[r]} unique={len(ids)==gates[r]} n1only={only1of1==gates[r]} k1={k1==gates[r]}', flush=True)
    out[r]=dict(perbc)
json.dump(out, open('rage_offlist_flex_perbc_n1.json','w'))
print('DONE')
