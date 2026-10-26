#!/usr/bin/env python3
"""Create a text-only author-review DOCX from the current Figure 1–7 legends.

Original manuscript files are never modified. No figure graphics, relationships,
comments or prior document parts are copied into the new package.
"""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,default=ROOT/'docs/current_figure_legends.md')
p.add_argument('--paragraph-json',type=Path,help='For a Methods-only document, read this private paragraph array instead of Markdown.')
p.add_argument('--figures',type=int,nargs='+',default=[1,2,3,4,5,6,7])
p.add_argument('--output',type=Path,required=True)
p.add_argument('--receipt',type=Path)
a=p.parse_args()
a.receipt=a.receipt or ROOT/'validation'/('current_methods_docx.json' if a.paragraph_json else 'current_legends_docx.json')
if a.paragraph_json:
    a.source=a.paragraph_json
    paragraphs=json.loads(a.source.read_text())
    assert paragraphs[0]=='Methods'
else:
    source=a.source.read_text()
    block=source.split('## Revised legend text\n',1)[1].split('\n## Rebuttal',1)[0]
    paragraphs=[]
    for para in re.split(r'\n\s*\n',block.strip()):
        para=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',para)
        para=para.replace('**Figure','Figure').replace('**Author','Author')
        # Remove Markdown emphasis markers while preserving four significance stars.
        para=para.replace('**: ',': ').replace('.** ','. ').replace('hold:**','hold:')
        para=para.replace('`','').replace('\n',' ')
        paragraphs.append(para)
    assert len(paragraphs)==2*len(a.figures)
    assert [int(re.match(r'Figure (\d+)\.',s).group(1)) for s in paragraphs if re.match(r'Figure (\d+)\.',s)]==a.figures
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
ET.register_namespace('w',W)
def el(name,attrs=None):return ET.Element('{'+W+'}'+name,attrs or {})
document=el('document');body=ET.SubElement(document,'{'+W+'}body')
def paragraph(text,style=None):
    node=ET.SubElement(body,'{'+W+'}p')
    if style:
        pr=ET.SubElement(node,'{'+W+'}pPr');ET.SubElement(pr,'{'+W+'}pStyle',{'{'+W+'}val':style})
    run=ET.SubElement(node,'{'+W+'}r');t=ET.SubElement(run,'{'+W+'}t',{'{http://www.w3.org/XML/1998/namespace}space':'preserve'});t.text=text
title='Current author-review Methods' if a.paragraph_json else 'Current author-review legends — Figures {}–{}'.format(a.figures[0],a.figures[-1])
paragraph(title,'Title')
paragraph('Text-only revision draft, 23 October 2026. Existing statistical statements are preserved. Author notes identify unresolved source/fit documentation. This file contains no artwork.','Subtitle')
for text in paragraphs:paragraph(text)
sect=ET.SubElement(body,'{'+W+'}sectPr')
ET.SubElement(sect,'{'+W+'}pgSz',{'{'+W+'}w':'12240','{'+W+'}h':'15840'})
ET.SubElement(sect,'{'+W+'}pgMar',{ '{'+W+'}'+k:'1440' for k in ('top','right','bottom','left')})
styles='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:pPr><w:spacing w:after="160" w:line="276" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="22"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/><w:rPr><w:i/><w:sz w:val="20"/></w:rPr></w:style>
</w:styles>'''
parts={
'[Content_Types].xml':'''<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>''',
'_rels/.rels':'''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>''',
'word/document.xml':b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'+ET.tostring(document,encoding='utf-8'),
'word/styles.xml':styles,
'word/_rels/document.xml.rels':'''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''}
a.output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(str(a.output),'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in parts.items():z.writestr(name,data)
with zipfile.ZipFile(str(a.output)) as z:
    assert z.testzip() is None
    for name in z.namelist():ET.fromstring(z.read(name))
    assert not any('/media/' in name or '/embeddings/' in name for name in z.namelist())
    doc=ET.fromstring(z.read('word/document.xml'))
    text=' '.join(n.text or '' for n in doc.iter('{'+W+'}t'))
    assert not re.search(r'\bFigure\s+8\b|\b7E\b|E\.\s*Olivia',text)
    assert not any(n.tag.split('}')[-1] in ('drawing','pict','object') for n in doc.iter())
    if not a.paragraph_json:
        assert 'paired two-tailed t-test (****p<0.0001)' in text
        assert 'ANOVA with Dunnett’s multiple hypothesis correction' in text
        assert 'Figure 7C author hold:' in text
receipt=dict(status='passed_structural_checks',source=str(a.source),source_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    output=str(a.output),output_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
    figures=a.figures if not a.paragraph_json else None,document_scope='Methods only' if a.paragraph_json else 'Current legends',media_files=0,drawings=0,original_documents_modified=False,
    checks=['ZIP CRC','all XML well formed','declared current text-only scope','no Figure8/7E placeholder','no embedded media/drawings']+([] if a.paragraph_json else ['F5/F6 statistical wording retained','F7C author hold retained']),
    limitation='text-only scoped author-review draft; native Word load/save and pagination not tested')
a.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
print('Created and structurally checked text-only author-review DOCX:',a.output)
