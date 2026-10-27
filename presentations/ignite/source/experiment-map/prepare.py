from pathlib import Path
import zipfile,copy,json
from lxml import etree as E
w=Path('work/experiment-map');ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
P='{'+ns['p']+'}';A='{'+ns['a']+'}'
with zipfile.ZipFile(w/'latest-before-map.pptx') as z:
 base={x:z.read(x) for x in z.namelist()}
# Add a second temporary slide by cloning the authored slide package and then
# transplanting the exact existing native loop objects, plus a native title.
with zipfile.ZipFile(w/'new-slide-raw.pptx') as z: d={x:z.read(x) for x in z.namelist()}
s1=E.fromstring(d['ppt/slides/slide1.xml']);s2=copy.deepcopy(s1)
st2=s2.find('p:cSld/p:spTree',ns)
for sh in list(st2)[2:]:st2.remove(sh)
original=E.fromstring(base['ppt/slides/slide17.xml'])
for sh in list(original.find('p:cSld/p:spTree',ns))[2:]:st2.append(copy.deepcopy(sh))
# Reuse the authored native text object for the new title.
title=copy.deepcopy(s1.find('p:cSld/p:spTree/p:sp',ns));title.find('.//p:cNvPr',ns).set('id','1000')
title.find('.//a:t',ns).text='Before you commit'
xfrm=title.find('p:spPr/a:xfrm',ns);xfrm.find('a:off',ns).set('x','914400');xfrm.find('a:off',ns).set('y','685800');xfrm.find('a:ext',ns).set('cx','13411200');xfrm.find('a:ext',ns).set('cy','1257300')
for elem in title.findall('.//a:defRPr',ns)+title.findall('.//a:rPr',ns):elem.set('sz','6600')
for color in title.findall('.//a:srgbClr',ns):color.set('val','F4F1E9')
st2.append(title)
loop=json.loads((w/'before/story.json').read_text())[16]
loop.update(title='Before you commit',stageCue='Review before you commit',cue='Review before you commit, then review the fix.',script='Review before you commit. Reproduce the failure. Fix it. Run the test. Then review the fix, too. Check the findings yourself. Find bugs before your users do.',delivery='Follow the loop once, then return to the audience. Finding bugs before users is the goal, not a measured production outcome.')
loop['source']+=' Local development describes the workflow, not local model inference. Finding bugs before users is a goal, not a production outcome measured by this study.'
(w/'loop-story.json').write_text(json.dumps(loop,indent=2,ensure_ascii=False)+'\n')
new=json.loads((w/'new-slide-story.json').read_text())
for i,s,story in [(1,s1,new),(2,s2,loop)]:
 tr=s.find('p:transition',ns)
 if tr is None:tr=E.SubElement(s,P+'transition')
 tr.set('advClick','0');tr.set('advTm','15000')
 d[f'ppt/slides/slide{i}.xml']=E.tostring(s,xml_declaration=True,encoding='UTF-8',standalone=True)
 # Use the presenter's current note hierarchy, with explicit styles per paragraph.
 note=E.fromstring(base['ppt/notesSlides/notesSlide17.xml'])
 note.find('.//p:ph[@type="body"]',ns).set('idx','3')
 note.find('.//p:ph[@type="sldImg"]',ns).set('idx','2')
 body=note.xpath('.//p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]/p:txBody',namespaces=ns)[0]
 for par in list(body.findall('a:p',ns)):body.remove(par)
 texts=[(story['stageCue'],3600,True),('',2400,False),(story['script'],2400,False),('',1200,False),('SOURCES AND SCOPE',1200,True),(story['source'],1200,False),('Primary research: https://github.com/dsifry/harnesseval/blob/8f634b68664751527a9ad0123d1a082dd70a0931/REPORT.md',1200,False)]
 for text,size,bold in texts:
  par=E.SubElement(body,A+'p');ppr=E.SubElement(par,A+'pPr');pr=E.SubElement(ppr,A+'defRPr',sz=str(size),b='1' if bold else '0');E.SubElement(pr,A+'latin',typeface='Helvetica Neue');r=E.SubElement(par,A+'r');r.append(copy.deepcopy(pr));r[0].tag=A+'rPr';E.SubElement(r,A+'t').text=text
 d[f'ppt/notesSlides/notesSlide{i}.xml']=E.tostring(note,xml_declaration=True,encoding='UTF-8',standalone=True)
# Clone known relationships to the second temporary slide.
R='{http://schemas.openxmlformats.org/package/2006/relationships}'
rels=E.fromstring(d['ppt/slides/_rels/slide1.xml.rels'])
for r in rels:
 if r.get('Type').endswith('/notesSlide'):r.set('Target','../notesSlides/notesSlide2.xml')
d['ppt/slides/_rels/slide2.xml.rels']=E.tostring(rels)
nrels=E.fromstring(d['ppt/notesSlides/_rels/notesSlide1.xml.rels'])
for r in nrels:
 if r.get('Type').endswith('/slide'):r.set('Target','../slides/slide2.xml')
d['ppt/notesSlides/_rels/notesSlide2.xml.rels']=E.tostring(nrels)
pres=E.fromstring(d['ppt/presentation.xml']);ids=pres.find('p:sldIdLst',ns);si=E.SubElement(ids,P+'sldId',id='257');si.set('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id','rIdMap2');d['ppt/presentation.xml']=E.tostring(pres)
pr=E.fromstring(d['ppt/_rels/presentation.xml.rels']);E.SubElement(pr,R+'Relationship',Id='rIdMap2',Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide',Target='slides/slide2.xml');d['ppt/_rels/presentation.xml.rels']=E.tostring(pr)
ct=E.fromstring(d['[Content_Types].xml']);C='{http://schemas.openxmlformats.org/package/2006/content-types}'
for part,typ in [('slides/slide2.xml','slide'),('notesSlides/notesSlide2.xml','notesSlide')]:E.SubElement(ct,C+'Override',PartName='/ppt/'+part,ContentType=f'application/vnd.openxmlformats-officedocument.presentationml.{typ}+xml')
d['[Content_Types].xml']=E.tostring(ct)
with zipfile.ZipFile(w/'Experiment_And_Workflow_v2.pptx','w',zipfile.ZIP_DEFLATED) as z:
 for n,v in d.items():z.writestr(n,v)
print('Two-slide insertion source prepared. Native loop preserved; new question and workflow notes styled.')
