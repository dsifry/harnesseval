from pathlib import Path
import copy,json,re,hashlib,zipfile,shutil
from lxml import etree as E
from PIL import Image,ImageDraw
root=Path('/Users/dsifry/Documents/Codex/2026-09-28/we-a');w=root/'work/restore-token-qr';out=root/'outputs'
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
story=json.loads((root/'work/experiment-map/story.json').read_text())
fields={};unchanged={i:i for i in range(1,21) if i not in [10,20]}
with zipfile.ZipFile(w/'restored-before-design.pptx') as before,zipfile.ZipFile(w/'native-delivery.pptx') as after:
 d={n:after.read(n) for n in after.namelist()}
 assert len([n for n in d if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)])==20
 for i in range(1,21):
  slide=E.fromstring(d[f'ppt/slides/slide{i}.xml']);tr=slide.find('p:transition',ns);assert tr.get('advTm')=='15000' and tr.get('advClick')=='0',(i,E.tostring(tr))
  if i in unchanged:
   a=copy.deepcopy(E.fromstring(before.read(f'ppt/slides/slide{unchanged[i]}.xml')).find('p:cSld',ns));b=copy.deepcopy(slide.find('p:cSld',ns))
   for tree in [a,b]:
    for e in tree.findall('.//p:cNvPr',ns):e.set('id','0')
   assert E.tostring(a)==E.tostring(b),('changed slide objects',i)
  note=E.fromstring(d[f'ppt/notesSlides/notesSlide{i}.xml'])
  body=note.xpath('.//p:sp[p:nvSpPr/p:nvPr/p:ph[@type="body"]]/p:txBody',namespaces=ns)[0]
  pars=[''.join(p.xpath('.//a:t/text()',namespaces=ns)) for p in body.findall('a:p',ns)];pars=[t for t in pars if t.strip()];boundary=pars.index('SOURCES AND SCOPE')
  stage=pars[0];script='\n'.join(pars[1:boundary]);assert script,(i,'empty script')
  if i != 20:
   bi=i;baseline=E.fromstring(before.read(f'ppt/notesSlides/notesSlide{bi}.xml'));assert note.xpath('.//a:t/text()',namespaces=ns)==baseline.xpath('.//a:t/text()',namespaces=ns),('changed notes',i)
  story[i-1]['stageCue']=stage;story[i-1]['script']=script
  fields[i]={'slideText':slide.xpath('.//a:t/text()',namespaces=ns),'cue':stage,'script':script}
 # Repair the known Keynote short-series workbook ranges, preserving all data.
 repairs=[]
 for n in list(d):
  if not re.fullmatch(r'ppt/charts/chart\d+\.xml',n):continue
  doc=E.fromstring(d[n]);changed=False
  for ser in doc.findall('.//c:ser',ns):
   if 'No increase' not in ser.xpath('c:tx//c:v/text()',namespaces=ns):continue
   for xp,correct in [('c:xVal/c:numRef/c:f','Sheet1!$D$2:$D$4'),('c:yVal/c:numRef/c:f','Sheet1!$E$2:$E$4'),('c:tx/c:strRef/c:f','Sheet1!$D$1')]:
    e=ser.find(xp,ns)
    if e is not None and e.text!=correct:repairs.append({'part':n,'before':e.text,'after':correct});e.text=correct;changed=True
  if changed:d[n]=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
 with zipfile.ZipFile(w/'candidate.pptx','w',zipfile.ZIP_DEFLATED) as z:
  for n,v in d.items():z.writestr(n,v)
(w/'story.json').write_text(json.dumps(story,ensure_ascii=False,indent=2)+'\n');(w/'current-native-content.json').write_text(json.dumps(fields,ensure_ascii=False,indent=2)+'\n');(w/'chart-export-repair.json').write_text(json.dumps(repairs,indent=2)+'\n')
(w/'native-validation.json').write_text(json.dumps({'slides':20,'timing_seconds':15,'unchanged_slide_objects':unchanged,'notes_1_through_19_preserved':True,'user_closing_script_addition':'All free, all open source.','native_fields':fields,'chart_export_reference_repairs':repairs},indent=2,ensure_ascii=False)+'\n')
assert fields[20]['script'].endswith('All free, all open source. ')
assert fields[19]['slideText'][0]=='Use /low effort'
assert fields[10]['slideText']==['≈10×','the tokens']
assert fields[20]['slideText']==['Follow the','evidence.','Read the report']
assert hashlib.sha256((out/'DaveSifry_VibesVsEvidence.key').read_bytes()).hexdigest()==json.loads((w/'native-snapshot.json').read_text())['sha256']
print('Validated native order, unchanged slides/notes and 20 automatic 15-second slides. Backup prepared.')
