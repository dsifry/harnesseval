import fs from 'node:fs/promises';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const root='/Users/dsifry/Documents/Codex/2026-09-28/we-a';
const work=`${root}/work/bug-icons`;
const p=Presentation.create({slideSize:{width:1600,height:900}});
const C={bg:'#101110',ivory:'#F4F1E9',orange:'#F17A43'};
// A native editable pictogram encodes exactly one defect. Symmetric six-leg
// silhouette with two antennae, simplified for small projected chart markers.
const left=[[12,4],[10,4.4],[7,0],[5.5,1.1],[8.2,5.5],[7,7],[7,9],[6,11],[2.1,8.6],[1,10.1],[5.2,13],[4.6,15.6],[0,15.6],[0,17.5],[4.7,17.5],[5.6,20.5],[1.7,23.4],[2.8,25],[6.9,22.3],[8,24.1],[9.8,25.3],[12,25.8]];
const silhouette=[...left,...left.slice(1,-1).reverse().map(([x,y])=>[24-x,y])];
function bug(s,id,x,y,color,hollow=false){
 const w=26.5,h=28.5;
 const sh=s.shapes.add({geometry:'custom',position:{left:x-w/2,top:y-h/2,width:w,height:h},fill:hollow?C.bg:color,line:hollow?{fill:C.orange,width:1.7}:{fill:'none',width:0},customPaths:[{width:24,height:25.8,commands:[...silhouette.map(([x,y],i)=>i?{lineTo:{x,y}}:{moveTo:{x,y}}),{close:{}}]}]});
 // Deliberately no faces, gradients or decorative detail in the evidence marks.
 return sh;
}
for(const num of [4,5,14]){
 const s=p.slides.add();s.background.fill=C.bg;
 const total=num===4?42:147;
 for(let i=0;i<total;i++){
  const color=num===5&&i>=42?C.orange:C.ivory;
  const hollow=num===14&&i>=88;
  bug(s,i,(520.5+(i%21)*27.6475)*4/3,(259.2+Math.floor(i/21)*43.6)*4/3,color,hollow);
 }
 s.speakerNotes.textFrame.setText(`Bug pictogram replacement for slide ${num}. Exactly ${total} editable defect icons. ${num===4?'42 original benchmark bugs.':num===5?'42 original benchmark bugs in ivory and 105 additional verified defects in orange.':'88 found in ivory and 59 missed as orange outlines.'}`);
 const preview=await p.export({slide:s,format:'png',scale:0.75});
 await fs.writeFile(`${work}/bugs-${num}.png`,new Uint8Array(await preview.arrayBuffer()));
}
await (await PresentationFile.exportPptx(p)).save(`${work}/icons-ungrouped.pptx`);
console.log('Prepared 42, 147 and 147 editable bug markers in the existing colors and positions.');
