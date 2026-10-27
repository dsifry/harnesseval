from pathlib import Path
import json,re,shutil,hashlib,zipfile
from PIL import Image,ImageDraw
r=Path('/Users/dsifry/Documents/Codex/2026-09-28/we-a');w=r/'work/restore-token-qr';out=r/'outputs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((w/'pptx-validation.json').read_text());final=out/'DaveSifry_VibesVsEvidence_ReportQR.pptx'
assert receipt['packageIntegrity']['status']=='pass' and receipt['presentationLayout']['findingCount']==0
assert sha(final)==receipt['finalSha256']
snapshot=json.loads((w/'native-snapshot.json').read_text())['sha256']
assert sha(w/'native-approved.key')==snapshot
story=json.loads((w/'story.json').read_text());story[18]['title']='Use /low effort';story[9]['delivery']='Let the excessive paper trail set up the cost question. Say "at the median" aloud; keep the slide itself spare. The photograph is a generated visual metaphor, not a measured bill.';story[19]['delivery']='Finish on "Follow the evidence." The QR is an optional route to the full report; allow the audience to scan without reading the URL aloud.'
words=sum(len(s['script'].split()) for s in story);(w/'story.json').write_text(json.dumps(story,ensure_ascii=False,indent=2)+'\n')
old=(out/'Ignite_Rehearsal.md').read_text();shutil.copy2(out/'Ignite_Rehearsal.md',w/'before/Ignite_Rehearsal.md')
header=old.split('## 1.')[0];header=re.sub(r'The current draft is \d+ whitespace-counted words, including Dave’s latest direct edits and slide order\.',f'The current draft is {words} whitespace-counted words, including Dave’s latest direct edits and slide order.',header)
body=[];cues=['# Vibes vs. Evidence: current rehearsal cues','','Twenty slides, 15 seconds each. These match the current native presenter notes.','','| Time | Slide | Cue |','|---|---|---|']
def t(sec):return f'{sec//60}:{sec%60:02d}'
for i,s in enumerate(story):
 body.append(f'## {i+1}. {s["title"]} ({t(i*15)} to {t((i+1)*15)})\n\n**Cue:** {s["stageCue"]}\n\n{s["script"]}\n\n*Delivery:* {s["delivery"]}\n\n*Evidence boundary:* {s["source"]}\n')
 cues.append(f'| {t(i*15)} | {i+1} | {s["stageCue"]} |')
(out/'Ignite_Rehearsal.md').write_text(header+'\n'.join(body));(out/'Ignite_Cue_Sheet.md').write_text('\n'.join(cues)+'\n')
for name in ['DaveSifry_VibesVsEvidence.pptx','DaveSifry_VibesVsEvidence_WithNotes.pptx']:shutil.copy2(final,out/name)
for name in ['DaveSifry_VibesVsEvidence_ReportQR.key','DaveSifry_VibesVsEvidence_WithNotes.key']:shutil.copy2(w/'native-approved.key',out/name);assert sha(out/name)==snapshot
canvas=Image.new('RGB',(1600,1000),'#20211f');draw=ImageDraw.Draw(canvas)
(out/'Keynote_Slides_ReportQR').mkdir(exist_ok=True)
with zipfile.ZipFile(out/'Updated_Slides_ReportQR.zip','w',zipfile.ZIP_DEFLATED) as z:
 for i in range(1,21):
  src=w/'delivery-images'/f'delivery-images.{i:03d}.png';im=Image.open(src);assert im.size==(1200,675)
  for d in ['Keynote_Slides','Keynote_Slides_ReportQR']:shutil.copy2(src,out/d/f'{d}.{i:03d}.png')
  z.write(src,f'Slide_{i:02d}.png');x,y=8+((i-1)%4)*400,8+((i-1)//4)*198;canvas.paste(im.convert('RGB').resize((336,189)),(x+30,y));draw.text((x+9,y+5),str(i),fill='#c4c1b9')
canvas.save(out/'Ignite_Preview.png');canvas.save(out/'Ignite_Preview_ReportQR.png')
section='## September 29: restored token slide and report QR\n\nThe native Keynote had lost slide 10 while the previous verified PowerPoint still contained it. That mismatch was recovered from the intact export. Slide 10 now combines the approved generated paper-trail photograph with editable Helvetica Neue typography. The visible median footer is removed; the median qualification remains in the spoken notes. The closing typography uses equal type sizes and tighter spacing, with a functional QR to https://dsifry.github.io/harnesseval. The checked native snapshot stayed byte-identical across export; Dave continued editing the live canonical deck afterward. The ReportQR Keynote is the frozen verified snapshot, and its exported twenty slides all advance after fifteen seconds. The other eighteen slide object trees and notes 1 through 19 are unchanged from the recovered live baseline; Dave’s closing-script addition "All free, all open source" is retained. Final native PNGs 10 and 20 were visually inspected, and Apple Vision decoded the QR from the exported closing slide. No new independent full-deck review or aloud rehearsal is claimed.\n'
for name in ['Ignite_Design_Direction.md','Creative_Review_Final.md']:
 p=out/name;p.write_text(p.read_text()+'\n'+section)
validation={'slides':20,'seconds_per_slide':15,'script_words':words,'native_snapshot_sha256':snapshot,'native_snapshot_consistent_across_exports':True,'live_native_continued_user_edits_after_snapshot':True,'other_18_slide_objects_preserved':True,'notes_1_through_19_preserved':True,'latest_closing_note_addition_preserved':True,'qr_decoded_from_final_native_slide':'https://dsifry.github.io/harnesseval','full_timed_rehearsal_performed':False,'files':{n:sha(out/n) for n in ['DaveSifry_VibesVsEvidence_ReportQR.key','DaveSifry_VibesVsEvidence.pptx','Ignite_Rehearsal.md','Ignite_Cue_Sheet.md']}}
(w/'delivery-validation.json').write_text(json.dumps(validation,indent=2)+'\n');print(json.dumps(validation,indent=2))
