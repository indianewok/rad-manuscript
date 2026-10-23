from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import sys

BASE = Path('/Volumes/rad_data/reviewer_comment_data/paper_revision_20261022')
SRC = Path('/Users/cmv/Desktop/RAD_paper_revision_2026-10-22/sources/RAD R1 figures and legends.docx')
OUT = Path('/Users/cmv/Desktop/RAD_paper_revision_2026-10-22/working/RAD_R1_figures_and_legends_failure_modes_2026-10-22.docx')
FIG = Path(sys.argv[1])
assert FIG.suffix.lower() == '.png' and FIG.exists()
assert not OUT.exists() or '--replace-working' in sys.argv[2:], 'Explicit replacement required for the owned working copy.'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
ns = {'w': W}
q = lambda local: f'{{{W}}}{local}'
digest = lambda b: hashlib.sha256(b).hexdigest()
source_hash = digest(SRC.read_bytes())
with ZipFile(SRC) as z:
    infos = z.infolist()
    original = {i.filename:z.read(i.filename) for i in infos}
data = dict(original)
document = etree.fromstring(data['word/document.xml'])
paragraphs = document.find(q('body')).findall(q('p'))
caption = [p for p in paragraphs if ''.join(p.xpath('.//w:t/text()', namespaces=ns)).startswith('Figure 3.')]
assert len(caption) == 1
caption = caption[0]
original_caption = ''.join(caption.xpath('.//w:t/text()', namespaces=ns))
old_paragraph_xml = [etree.tostring(p) for p in paragraphs]
start = [i for i,child in enumerate(caption) if ''.join(child.xpath('.//w:t/text()', namespaces=ns)) == 'D-G']
assert len(start) == 1
bold_props = deepcopy(caption[start[0]].find(q('rPr')))
normal_props = deepcopy(caption[start[0]+1].find(q('rPr')))
for child in list(caption)[start[0]:]:
    caption.remove(child)

comments = etree.fromstring(data['word/comments.xml'])
old_comments = {c.get(q('id')):etree.tostring(c) for c in comments}
comment_id = str(max(int(c.get(q('id'))) for c in comments) + 1)
anchor_start = etree.Element(q('commentRangeStart'))
anchor_start.set(q('id'), comment_id)
caption.append(anchor_start)
def run(text, bold=False):
    r = etree.SubElement(caption,q('r'))
    r.append(deepcopy(bold_props if bold else normal_props))
    t = etree.SubElement(r,q('t'))
    t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    t.text = text

segments = [
 ('D-G',True),
 ('. Barcode correction was classified by exact observed source-barcode membership (',False),('D',True),
 ('). Corrected off-list: a source outside the complete chemistry catalog was changed to a tool-selected target. Failure mode 1: a catalog-valid source outside the Cell Ranger filtered set was changed to a tool-selected target. Failure mode 2: a source in the Cell Ranger filtered set was changed to a different barcode in that set that was also selected by the tool. Counts used unique original-read–target-barcode pairs. Total counts (',False),('E',True),
 ('), counts per target barcode (',False),('F',True),
 ('), and class percentages among all such pairs assigned by the same tool to each target (',False),('G',True),
 (') were compared across the four LongBench inputs. These classes describe observed barcode changes and reference-set membership; they do not establish cellular origin or correction accuracy.',False),
]
for text,bold in segments:
    run(text,bold)
anchor_end = etree.SubElement(caption,q('commentRangeEnd'))
anchor_end.set(q('id'),comment_id)
reference_run = etree.SubElement(caption,q('r'))
rp = etree.SubElement(reference_run,q('rPr'))
style = etree.SubElement(rp,q('rStyle'))
style.set(q('val'),'CommentReference')
reference = etree.SubElement(reference_run,q('commentReference'))
reference.set(q('id'),comment_id)
comment_text = ('Figure 3D and the failure-mode labels in E-G must use the same measured definitions as this caption: '
 'mode 1 is a catalog-valid source outside the Cell Ranger filtered reference changed to a tool-selected target; '
 'mode 2 is a Cell Ranger source changed to a different Cell Ranger barcode selected by the tool. '
 'The previous ambient-RNA, empty-droplet, and undetected-cell interpretations are not established by these measurements. '
 'Panel D has been replaced with the revised measured-category schematic. The numerical data and all other panels are retained. '
 'Source mapping: update_raw_longbench_prism.py, lines 181-200; analyze_correction_events.py, lines 909-945.')
c = etree.SubElement(comments,q('comment'))
c.set(q('id'),comment_id);c.set(q('author'),'RAD methods audit');c.set(q('initials'),'RAD')
c.set(q('date'),datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
cp=etree.SubElement(c,q('p'));cr=etree.SubElement(cp,q('r'));ct=etree.SubElement(cr,q('t'));ct.text=comment_text

rels = etree.fromstring(data['word/_rels/document.xml.rels'])
matches = [r for r in rels if r.get('Target') == 'media/image3.emf']
assert len(matches) == 1
new_media = 'word/media/image3_failure_modes_20261022.png'
matches[0].set('Target',new_media.removeprefix('word/'))
data[new_media] = FIG.read_bytes()
content_types = etree.fromstring(data['[Content_Types].xml'])
if not any(x.get('Extension') == 'png' for x in content_types):
    default=etree.SubElement(content_types,f'{{{CT}}}Default')
    default.set('Extension','png');default.set('ContentType','image/png')
serialize=lambda root:etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
data['word/document.xml']=serialize(document)
data['word/comments.xml']=serialize(comments)
data['word/_rels/document.xml.rels']=serialize(rels)
data['[Content_Types].xml']=serialize(content_types)
with ZipFile(OUT,'w') as z:
    for info in infos:
        z.writestr(info,data[info.filename])
    z.writestr(new_media,data[new_media])

# Structural and preservation checks are independent of the visual render.
with ZipFile(OUT) as z:
    assert z.testzip() is None
    saved={n:z.read(n) for n in z.namelist()}
assert digest(SRC.read_bytes()) == source_hash
modified=[n for n in original if saved[n] != original[n]]
assert set(modified) <= {'word/document.xml','word/comments.xml','word/_rels/document.xml.rels','[Content_Types].xml'}
assert all(saved[n] == b for n,b in original.items() if n.startswith('word/media/'))
assert len(paragraphs) == len(old_paragraph_xml)
changed_paragraphs=[i for i,p in enumerate(paragraphs) if etree.tostring(p) != old_paragraph_xml[i]]
assert changed_paragraphs == [5]
assert all(etree.tostring(c)==old_comments[c.get(q('id'))] for c in comments if c.get(q('id')) in old_comments)
assert document.xpath('count(.//w:commentRangeStart[@w:id="'+comment_id+'"])',namespaces=ns)==1
assert document.xpath('count(.//w:commentRangeEnd[@w:id="'+comment_id+'"])',namespaces=ns)==1
assert document.xpath('count(.//w:commentReference[@w:id="'+comment_id+'"])',namespaces=ns)==1
assert any(r.get('Type','').endswith('/comments') and r.get('Target')=='comments.xml' for r in rels)
assert any(t.get('PartName')=='/word/comments.xml' for t in content_types)
manifest={
 'source':str(SRC),'source_sha256':source_hash,'output':str(OUT),'output_sha256':digest(OUT.read_bytes()),
 'figure3_png':str(FIG),'figure3_png_sha256':digest(FIG.read_bytes()),
 'changed_original_members':modified,'added_members':[new_media],
 'changed_body_paragraphs':changed_paragraphs,'original_media_all_byte_identical':True,
 'existing_comments_preserved':True,'added_comment_id':comment_id,'added_comment_text':comment_text,
 'original_caption':original_caption,'new_caption':''.join(caption.xpath('.//w:t/text()',namespaces=ns)),
 'visual_qa':'PENDING',
}
(BASE/'evidence/figure3_failure_modes_docx_changes.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'output':str(OUT),'sha256':manifest['output_sha256'],'changed':modified,'comment_id':comment_id},indent=2))
