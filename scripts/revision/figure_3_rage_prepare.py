#!/usr/bin/env python3
"""Freeze the current matched RAGE input, references and three target lists."""
import argparse,csv,gzip,hashlib,json,random,shutil,sys
from pathlib import Path
from figure_3 import ROOT,sha,write,js
from figure_3_rage_verify_tools import verify_tools
EXPECTED_CANONICAL_RECORD_SHA256='a5f866d6180b46e0acbd3aa2526364060c152380714b00ec0ed74b8c1e8c24af'
EXPECTED_LIST_SHA256=['f53d0331048592ab4f17f432d30f23444dc2a5314fe25adc63eb01e9eda128f6','ad84e82a4ac9ad3f4e6c5665e2d0ff438369253b851e2197b1c22e0892172864','6e4bf40175775b1a2d6809175eea84611cd2c6ddf42f005fd8a4ffa09344a893']

def decode_bitlist(value):
    bases=[]
    for _ in range(16):bases.append('ACTG'[value&3]);value>>=2
    if value:raise ValueError('Barcode bitlist value exceeds16bases')
    return ''.join(reversed(bases))

def main():
    data=Path('/dartfs/rc/lab/A/AckermanLab/CMV/rad_data')
    base=ROOT/'checkpoints/figure_03/rage_matched';inputs=base/'inputs';inputs.mkdir(parents=True,exist_ok=True)
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=data/'raw_fastq_datasets/rageseq.fq.gz')
    p.add_argument('--reference',type=Path,default=ROOT/'data/figure_03/rage_matched_reference_4505.txt',help='Matched filtered barcodes, plain text or gzip')
    p.add_argument('--catalog',type=Path,default=ROOT/'data/figure_03/chemistry_3v2_catalog.txt.gz',help='Complete3v2 chemistry catalog, plain text or gzip')
    p.add_argument('--rad-source',type=Path,default=base/'tools/rad_cd0582_source')
    p.add_argument('--rad-binary',type=Path,default=base/'tools/rad_cd0582_build/rad')
    p.add_argument('--build-rad',action='store_true',help='Build a new executable from the verified pinned source instead of requiring the exact selected executable hash')
    p.add_argument('--blaze-python',type=Path,default=base/'tools/blaze_2.6.0a0_env/bin/python')
    p.add_argument('--blaze-entrypoint',type=Path,default=base/'tools/blaze_2.6.0a0_env/bin/blaze')
    p.add_argument('--flex-binary',type=Path,default=ROOT/'vendor/flexiplex-audit/bin/flexiplex_v1.02.6_raw_to_assigned_audit')
    a=p.parse_args();raw=a.input.resolve();reference=a.reference.resolve();catalog=a.catalog.resolve()
    software=verify_tools(a.rad_source.resolve(),a.rad_binary.absolute(),a.blaze_python.absolute(),a.blaze_entrypoint.absolute(),a.flex_binary.absolute(),a.build_rad)
    a.rad_binary=Path(software['rad_binary'])
    reference_open=gzip.open if str(reference).endswith('.gz') else open
    with reference_open(reference,'rt') as f:reference_rows=[x.strip().removesuffix('-1') for x in f if x.strip()]
    excluded=sorted(set(reference_rows))
    catalog_open=gzip.open if str(catalog).endswith('.gz') else open
    with catalog_open(catalog,'rb') as f:catalog_bytes=f.read()
    full=sorted({x.strip() for x in catalog_bytes.decode('ascii').splitlines() if x.strip()})
    assert len(reference_rows)==len(excluded)==4505 and len(full)==737280 and set(excluded)<=set(full)
    assert all(len(x)==16 and set(x)<=set('ACGT') for x in full)
    (inputs/'matched_filtered_4505.txt').write_text('\n'.join(excluded)+'\n')
    (inputs/'chemistry_3v2_catalog.txt').write_bytes(catalog_bytes)
    assert sha(inputs/'matched_filtered_4505.txt')=='93f7551ec70c57d5f9e6d8e77f4041d19c99acc9b771e16ce1acf26dfac5ba54'
    assert sha(inputs/'chemistry_3v2_catalog.txt')=='b0dda4b114d8fc7ea8def94fb472e6205c1831a72e3ac245ed13cc332d9f20d1'
    src=a.rad_source.resolve()
    shutil.copyfile(src/'resources/wl/737K-august-2016_bitlist.csv.gz',inputs/'chemistry_3v2_catalog_bitlist.csv.gz')
    with gzip.open(inputs/'chemistry_3v2_catalog_bitlist.csv.gz','rt') as f:decoded=[decode_bitlist(int(line.strip())) for line in f if line.strip()]
    assert len(decoded)==len(set(decoded))==737280 and set(decoded)==set(full),'RAD bitlist differs from the complete plain catalog'
    layout=(src/'resources/read_layout/three_prime_read_layout.csv').read_text(encoding='utf-8-sig').replace('10x_3v3','10x_3v2')
    layout_rows=list(csv.DictReader(layout.splitlines()[1:]));umi=next(r for r in layout_rows if r['id']=='umi');barcode=next(r for r in layout_rows if r['id']=='barcode')
    assert umi['expected_length']=='10' and barcode['expected_length']=='16' and barcode['whitelist']=='10x_3v2','Expected exact3v2/UMI10 layout'
    (inputs/'rage_3v2_umi10_layout.csv').write_text(layout)
    candidates=sorted(set(full)-set(excluded));whitelists=[]
    for rep,seed in enumerate([2026102301,2026102302,2026102303],1):
        targets=sorted(random.Random(seed).sample(candidates,len(excluded)));p=inputs/f'false_rep{rep}.txt';p.write_text('\n'.join(targets)+'\n')
        assert len(targets)==len(set(targets))==4505 and not set(targets)&set(excluded)
        assert sha(p)==EXPECTED_LIST_SHA256[rep-1],'Seeded list bytes differ from the selected experiment; check RNG/version/universe'
        whitelists.append(dict(replicate=rep,seed=seed,rng='Python random.Random MT19937',python=sys.version.split()[0],target_count=4505,path=str(p),sha256=sha(p)))
    flex=a.flex_binary.resolve()
    manifest=dict(experiment_id='rage_matched_offlist_20261023',selection='current authorized matched replication',accession='ERR3268991',input=str(raw),expected_input_bytes=16922373879,expected_input_reads=20346396,expected_input_sha256='cfdba50a497dd4f6b24c2a4e730e297a09498ad5fe006f65eee01fa202bcdcec',input_validation_status='pending_full_preflight',catalog=str(inputs/'chemistry_3v2_catalog.txt'),catalog_sha256=sha(inputs/'chemistry_3v2_catalog.txt'),catalog_entries=len(full),reference=str(inputs/'matched_filtered_4505.txt'),reference_sha256=sha(inputs/'matched_filtered_4505.txt'),excluded_entries=len(excluded),whitelists=whitelists,layout=str(inputs/'rage_3v2_umi10_layout.csv'),layout_sha256=sha(inputs/'rage_3v2_umi10_layout.csv'),bitlist=str(inputs/'chemistry_3v2_catalog_bitlist.csv.gz'),bitlist_sha256=sha(inputs/'chemistry_3v2_catalog_bitlist.csv.gz'),rad_commit='cd0582b2440cde0f35725dc557fa47307d74d374',rad_binary=str(a.rad_binary.resolve()),blaze_version='2.6.0a0',blaze_commit='af8d2cc9f6374caf4d1006d5f8a0e99097211646',blaze_python=str(a.blaze_python.absolute()),blaze_entrypoint=str(a.blaze_entrypoint.resolve()),flex_binary=str(flex),flex_binary_sha256=sha(flex),flex_commit='d84c8ae4f3865052f2b5ecec816949b94682f302',flex_patch_sha256='88dc9cbad139d8ac416803c19c1d4291ebb7e3159f5a1a49205aff59319f86cb',FLEXIPLEX_AUDIT_SOURCE_FILE='UNSET; no truth injection',PYTHONHASHSEED='20261023',tool_threads=16,CPU_allocation=20,semantics='strict physical-read counts: all rows of multiply assigned IDs excluded; zero-count targets retained; valid Flex sidecar-only rows included',statistics='Preserve author-selected statistical choices; no new hypothesis tests in this replication')
    manifest['software_verification']=software
    manifest['reference_original']=dict(path=str(reference),sha256=sha(reference),rows=len(reference_rows),duplicate_normalized_barcodes=0,normalization='Strip terminal -1, require unique16mer catalog barcodes, lexical sort')
    manifest['expected_input_canonical_record_sha256']=EXPECTED_CANONICAL_RECORD_SHA256
    manifest['expected_input_sequence_bases']=16466857803
    manifest['input_identity_policy']='Require exact ordered physical-ID/sequence/quality canonical hash. Record actual compressed hash; input order matters for RAD layout calibration.'
    js(base/'experiment.json',manifest);js(ROOT/'manifests/figure_3_rage_experiment.json',manifest)
    js(base/'input_validation.json',dict(status='requires_preflight',reason='Preparation invalidates any preceding input-validation receipt'))
    write(inputs/'whitelist_manifest.tsv',whitelists)
    print(json.dumps({'prepared':str(base),'input_reads':20346396,'reference':4505,'catalog':737280,'list_seeds':[2026102301,2026102302,2026102303]}))
if __name__=='__main__':main()
