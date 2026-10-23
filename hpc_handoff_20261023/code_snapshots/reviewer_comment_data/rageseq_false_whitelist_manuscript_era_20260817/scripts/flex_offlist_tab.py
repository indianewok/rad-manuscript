#!/usr/bin/env python3
import subprocess, collections, json, sys
B='/Users/cmv/Dropbox (Dartmouth College)/rad_paper_data_backup/103025_results/flexiplex/offlist'
paths={1:f'{B}/offlist_v1/offlist_v1.fastq.gz',2:f'{B}/offlist_v2/offlist_v2.fastq.gz',3:f'{B}/offlist_v2/offlist_v3.fastq.gz'}
gates={1:1591111,2:1672992,3:1640883}
out={}
for r,p in paths.items():
    c=collections.Counter()
    proc=subprocess.Popen(['seqkit','seq','-n',p],stdout=subprocess.PIPE,text=True,bufsize=1<<20)
    for line in proc.stdout:
        cb=line.split('CB:Z:')[1].split('\t')[0].strip() if 'CB:Z:' in line else line.split('_',1)[0].lstrip('@')
        c[cb]+=1
    if proc.wait()!=0: sys.exit(f'seqkit failed rep{r}')
    tot=sum(c.values())
    print(f'flex rep{r}: total={tot} gate={gates[r]} match={tot==gates[r]} distinct={len(c)}',flush=True)
    out[r]=dict(c)
json.dump(out,open('rage_offlist_flex_perbc.json','w'))
print('DONE')
