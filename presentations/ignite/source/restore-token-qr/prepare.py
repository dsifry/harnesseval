from pathlib import Path
import zipfile,copy
from lxml import etree as E
w=Path('work/restore-token-qr');ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'};A='{'+ns['a']+'}';P='{'+ns['p']+'}'
with zipfile.ZipFile(w/'restored-before-design.pptx') as z:b={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(w/'design-raw.pptx') as z:d={n:z.read(n) for n in z.namelist()}
for dest,source in [(1,10),(2,20)]:
 note=E.fromstring(b[f'ppt/notesSlides/notesSlide{source}.xml'])
 body=note.xpath('.//p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]/p:txBody',namespaces=ns)[0]
 # Preserve the exact spoken cue/script and evidence scope. Add only visual provenance.
 par=E.SubElement(body,A+'p');ppr=E.SubElement(par,A+'pPr');pr=E.SubElement(ppr,A+'defRPr',sz='1200');E.SubElement(pr,A+'latin',typeface='Helvetica Neue');run=E.SubElement(par,A+'r');rpr=copy.deepcopy(pr);rpr.tag=A+'rPr';run.append(rpr);E.SubElement(run,A+'t').text='Visual: AI-generated editorial paper-trail metaphor. The image is not an actual measured bill. The median comparison qualification remains in the spoken script.' if dest==1 else 'Report QR code encodes https://dsifry.github.io/harnesseval exactly. Generated deterministically with Core Image and independently decoded with Apple Vision. Original closing script is unchanged.'
 d[f'ppt/notesSlides/notesSlide{dest}.xml']=E.tostring(note,xml_declaration=True,encoding='UTF-8',standalone=True)
 # Match the notes master to the current native note hierarchy.
 d['ppt/notesMasters/notesMaster1.xml']=b['ppt/notesMasters/notesMaster1.xml']
 doc=E.fromstring(d[f'ppt/slides/slide{dest}.xml']);tr=E.SubElement(doc,P+'transition',advClick='0',advTm='15000');d[f'ppt/slides/slide{dest}.xml']=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
with zipfile.ZipFile(w/'Token_And_Closing.pptx','w',zipfile.ZIP_DEFLATED) as z:
 for n,v in d.items():z.writestr(n,v)
print('Prepared two replacement slides, preserving exact native cue and spoken script.')
