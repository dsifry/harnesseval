import fs from 'node:fs/promises';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const root='/Users/dsifry/Documents/Codex/2026-09-28/we-a',w=`${root}/work/restore-token-qr`;
const p=Presentation.create({slideSize:{width:1600,height:900}});
const C={bg:'#101110',ivory:'#F4F1E9',orange:'#F17A43',muted:'#C4C1B9'};
function text(s,str,x,y,width,height,size,color,bold=true,alignment='left'){const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width,height},fill:'none',line:{fill:'none',width:0}});sh.text=str;sh.text.style={typeface:'Helvetica Neue',fontSize:size,color,bold,autoFit:'none',alignment};}
async function image(s,file,pos,alt){s.images.add({blob:new Uint8Array(await fs.readFile(`${root}/outputs/assets/${file}`)),contentType:'image/png',fit:'contain',position:pos,alt});}
let s=p.slides.add();s.background.fill=C.bg;
await image(s,'token-paper-trail.png',{left:0,top:0,width:1600,height:900},'Generated editorial photograph of a long paper trail, a metaphor for extra token use.');
text(s,'≈10×',89,252,760,260,210,C.orange);
text(s,'the tokens',102,528,730,145,92,C.ivory);
s.speakerNotes.textFrame.setText('Placeholder replaced with the current native slide 10 notes before import.');
s=p.slides.add();s.background.fill=C.bg;
text(s,'Follow the',96,252,960,186,140,C.ivory);
text(s,'evidence.',96,413,960,186,140,C.orange);
await image(s,'Full_Report_QR.png',{left:1112,top:285,width:376,height:376},'QR code: https://dsifry.github.io/harnesseval');
text(s,'Read the report',1094,686,412,58,32,C.muted,false,'center');
s.speakerNotes.textFrame.setText('Placeholder replaced with the current native closing notes before import.');
await (await PresentationFile.exportPptx(p)).save(`${w}/design-raw.pptx`);
for(let i=0;i<2;i++){const blob=await p.export({slide:p.slides.items[i],format:'png',scale:.75});await fs.writeFile(`${w}/preview-${i+1}.png`,new Uint8Array(await blob.arrayBuffer()));}
