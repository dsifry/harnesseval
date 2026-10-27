import copy,json,zipfile
from pathlib import Path
from lxml import etree as E
root=Path('/Users/dsifry/Documents/Codex/2026-09-28/we-a'); w=root/'work/bug-icons'
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
def q(s):return '{'+ns[s.split(':')[0]]+'}'+s.split(':')[1]
groups={}
with zipfile.ZipFile(w/'icons-ungrouped.pptx') as src,zipfile.ZipFile(w/'Bug_Icon_Grids.pptx','w',zipfile.ZIP_DEFLATED) as dst:
 for item in src.infolist():
  data=src.read(item.filename)
  if item.filename in [f'ppt/slides/slide{x}.xml' for x in [1,2,3]]:
   n=int(item.filename.split('slide')[-1].split('.')[0]);owner=[4,5,14][n-1]
   doc=E.fromstring(data);tree=doc.find('p:cSld/p:spTree',ns);shapes=tree.findall('p:sp',ns)
   assert len(shapes)==(42 if owner==4 else 147)
   coords=[]
   for i,s in enumerate(shapes):
    pr=s.find('p:nvSpPr/p:cNvPr',ns);pr.set('id',str(i+3));pr.set('name',f'Bug {i+1}')
    state='original benchmark' if owner==4 or owner==5 and i<42 else 'additional verified' if owner==5 else 'found' if i<88 else 'missed'
    pr.set('descr',f'Defect {i+1}: {state}')
    x=s.find('p:spPr/a:xfrm',ns);o=x.find('a:off',ns);e=x.find('a:ext',ns)
    coords.append(tuple(int(v) for v in [o.get('x'),o.get('y'),e.get('cx'),e.get('cy')]))
   x=min(c[0] for c in coords);y=min(c[1] for c in coords);cx=max(c[0]+c[2] for c in coords)-x;cy=max(c[1]+c[3] for c in coords)-y
   group=E.Element(q('p:grpSp'));nv=E.SubElement(group,q('p:nvGrpSpPr'));E.SubElement(nv,q('p:cNvPr'),id='2',name=f'Bug grid for slide {owner}',descr=f'{len(shapes)} editable bug icons');E.SubElement(nv,q('p:cNvGrpSpPr'));E.SubElement(nv,q('p:nvPr'))
   pr=E.SubElement(group,q('p:grpSpPr'));tr=E.SubElement(pr,q('a:xfrm'))
   for tag,attrs in [('a:off',{'x':str(x),'y':str(y)}),('a:ext',{'cx':str(cx),'cy':str(cy)}),('a:chOff',{'x':str(x),'y':str(y)}),('a:chExt',{'cx':str(cx),'cy':str(cy)})]:E.SubElement(tr,q(tag),**attrs)
   for s in shapes:tree.remove(s);group.append(s)
   tree.append(group);groups[owner]=copy.deepcopy(group)
   data=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
  dst.writestr(item,data)
with zipfile.ZipFile(w/'latest-before-bugs.pptx') as src,zipfile.ZipFile(w/'candidate.pptx','w',zipfile.ZIP_DEFLATED) as dst:
 for item in src.infolist():
  data=src.read(item.filename)
  for owner,group in groups.items():
   if item.filename==f'ppt/slides/slide{owner}.xml':
    doc=E.fromstring(data);tree=doc.find('p:cSld/p:spTree',ns)
    charts=tree.findall('p:graphicFrame',ns);assert len(charts)==1
    tree.remove(charts[0]);g=copy.deepcopy(group)
    maxid=max(int(x) for x in doc.xpath('.//p:cNvPr/@id',namespaces=ns))
    for i,p in enumerate(g.findall('.//p:cNvPr',ns),maxid+1):p.set('id',str(i))
    tree.append(g);data=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
  dst.writestr(item,data)
with zipfile.ZipFile(w/'latest-before-bugs.pptx') as a,zipfile.ZipFile(w/'candidate.pptx') as b:
 changed=[x for x in a.namelist() if a.read(x)!=b.read(x)]
 assert set(changed)=={f'ppt/slides/slide{x}.xml' for x in [4,5,14]}
print('Grouped editable pictograms. Candidate only changes slide XML 4, 5 and 14; all text, notes, media and other slide parts preserved.')
