from pathlib import Path
import json,re,shutil,hashlib,zipfile
from PIL import Image,ImageDraw
r=Path('/Users/dsifry/Documents/Codex/2026-09-28/we-a');w=r/'work/experiment-map';out=r/'outputs'
receipt=json.loads((w/'pptx-validation.json').read_text());final=out/'DaveSifry_VibesVsEvidence_Experiment.pptx'
assert receipt['packageIntegrity']['status']=='pass' and receipt['presentationLayout']['findingCount']==0
assert hashlib.sha256(final.read_bytes()).hexdigest()==receipt['finalSha256']
story=json.loads((w/'story.json').read_text());story[3]['title']='The comparison manifold'
story[4]['delivery']='Preserve the six-PR scope. The answer key was incomplete; that is not a measured comparison of human reviewer performance.'
story[5]['delivery']=story[5]['delivery'].replace('white dots','ivory bug icons').replace('orange dots','orange bug icons')
story[18]['delivery']=story[18]['delivery'].replace('slide 10','the high-versus-medium comparison')
words=sum(len(s['script'].split()) for s in story)
(w/'story.json').write_text(json.dumps(story,ensure_ascii=False,indent=2)+'\n');(r/'work/improve-v10/story.json').write_text(json.dumps(story,ensure_ascii=False,indent=2)+'\n')
old=(out/'Ignite_Rehearsal.md').read_text();shutil.copy2(out/'Ignite_Rehearsal.md',w/'before/Ignite_Rehearsal.md')
header=old.split('## 1.')[0].replace('# Vibes vs. Evidence: rehearsal draft, v10','# Vibes vs. Evidence: current rehearsal draft')
header=re.sub(r'The current draft is \d+ whitespace-counted words, including Dave’s latest direct edits\.',f'The current draft is {words} whitespace-counted words, including Dave’s latest direct edits and slide order.',header)
body=[];cues=['# Vibes vs. Evidence: current rehearsal cues','','Twenty slides, 15 seconds each. These match the current native presenter notes.','','| Time | Slide | Cue |','|---|---|---|']
def t(sec):return f'{sec//60}:{sec%60:02d}'
for i,s in enumerate(story):
 body.append(f'## {i+1}. {s["title"]} ({t(i*15)} to {t((i+1)*15)})\n\n**Cue:** {s["stageCue"]}\n\n{s["script"]}\n\n*Delivery:* {s["delivery"]}\n\n*Evidence boundary:* {s["source"]}\n')
 cues.append(f'| {t(i*15)} | {i+1} | {s["stageCue"]} |')
(out/'Ignite_Rehearsal.md').write_text(header+'\n'.join(body));(out/'Ignite_Cue_Sheet.md').write_text('\n'.join(cues)+'\n')
for name in ['DaveSifry_VibesVsEvidence.pptx','DaveSifry_VibesVsEvidence_WithNotes.pptx']:shutil.copy2(final,out/name)
for name in ['DaveSifry_VibesVsEvidence_Experiment.key','DaveSifry_VibesVsEvidence_WithNotes.key']:shutil.copy2(out/'DaveSifry_VibesVsEvidence.key',out/name)
canvas=Image.new('RGB',(1600,1000),'#20211f');draw=ImageDraw.Draw(canvas)
with zipfile.ZipFile(out/'Updated_Slides_Experiment.zip','w',zipfile.ZIP_DEFLATED) as z:
 for i in range(1,21):
  src=w/'delivery-images'/f'delivery-images.{i:03d}.png';im=Image.open(src);assert im.size==(1200,675)
  for d,name in [('Keynote_Slides','Keynote_Slides'),('Keynote_Slides_Experiment','Keynote_Slides_Experiment')]:shutil.copy2(src,out/d/f'{name}.{i:03d}.png')
  z.write(src,f'Slide_{i:02d}.png');x,y=8+((i-1)%4)*400,8+((i-1)//4)*198;canvas.paste(im.convert('RGB').resize((336,189)),(x+30,y));draw.text((x+9,y+5),str(i),fill='#c4c1b9')
canvas.save(out/'Ignite_Preview.png');canvas.save(out/'Ignite_Preview_Experiment.png')
for name,section in [('Ignite_Design_Direction.md','## September 29: comparison and sequence\n\nSlide 4 uses a three-column 8 × 3 × 3 experiment map. Dave’s edited heading and model/method labels are retained. The isolated failing/passing reproduction is now slide 7, immediately after the verified-defect answer key. The combined before-commit workflow is slide 17. The deck remains twenty slides, each advancing automatically after fifteen seconds. The bug-icon slides are now 5, 6 and 16; the token-cost setup is slide 10.\n'),('Creative_Review_Final.md','## September 29: comparison setup and reordered evidence\n\nA targeted scientific review confirmed the eight-model, three-method, three-effort design and narrowed the China question to the two tested GLM models. It flagged the unsupported human-reviewer-performance claim; the notes now say the answer key was incomplete. A targeted art-direction review recommended the aligned 8 × 3 × 3 layout. Dave then edited its heading and labels in Keynote; those exact edits are retained. Dave moved the failing/passing reproduction to slide 7. The primary agent inspected the final native setup and combined workflow PNGs, preserved the other eighteen slide object trees under the verified reorder, and checked all twenty automatic fifteen-second advances and presenter-note passages. Native PowerPoint package/layout/font checks passed. No new full-deck independent review or aloud rehearsal is claimed.\n')]:
 p=out/name;p.write_text(p.read_text()+'\n'+section)
validation={'slides':20,'seconds_per_slide':15,'script_words':words,'comparison_slide':4,'evidence_slide':7,'workflow_slide':17,'user_edits_preserved':True,'notes_sync':True,'full_timed_rehearsal_performed':False,'files':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['DaveSifry_VibesVsEvidence.key','DaveSifry_VibesVsEvidence.pptx','Ignite_Rehearsal.md','Ignite_Cue_Sheet.md']}}
(w/'delivery-validation.json').write_text(json.dumps(validation,indent=2)+'\n');print(json.dumps(validation,indent=2))
