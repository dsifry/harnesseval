import fs from 'node:fs/promises';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const w='/Users/dsifry/Documents/Codex/2026-09-28/we-a/work/experiment-map';
const p=Presentation.create({slideSize:{width:1600,height:900}});
const C={bg:'#101110',white:'#F4F1E9',muted:'#C4C1B9',orange:'#F17A43'};
const s=p.slides.add();s.background.fill=C.bg;
function text(str,x,y,width,height,size,color=C.white,bold=true,align='left'){let t=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width,height},fill:'none',line:{fill:'none',width:0}});t.text=str;t.text.style={typeface:'Helvetica Neue',fontSize:size,color,bold,alignment:align,autoFit:'none'};}
text('The planned comparison',96,58,1408,110,76);
for(const [x,count,label] of [[100,'8','models'],[600,'3','review methods'],[1100,'3','reasoning levels']]){
 text(count,x,181,400,305,246,C.orange,true,'center');
 text(label,x-20,505,440,92,50,C.white,true,'center');
}
text('×',490,275,120,130,105,C.muted,false,'center');
text('×',990,275,120,130,105,C.muted,false,'center');
for(const [x,labels] of [[100,['Claude','GPT','GLM (open weights)']],[600,['One prompt','Two harnesses']],[1100,['Low','Medium','High']]]){
 labels.forEach((label,i)=>text(label,x-15,631+i*57,430,65,38,label.startsWith('GLM')?C.orange:C.muted,false,'center'));
}
const story={title:'Which model? Which method? How much reasoning?',cue:'Model, method, reasoning.',stageCue:'Model, method, reasoning',script:'Which model? One prompt or a harness? How much reasoning? Could China’s open-weight GLM models compete? I tested eight models, three review methods, and low, medium and high reasoning.',source:'REPORT.md §2.2. Eight tested models: Claude Fable 5.1, Opus 5, Sonnet 5; GPT-5.6 Sol, GPT-5.6 Terra, GPT-6 Astra; GLM-5.3 and GLM-5.3-Flash. Three methods: an engineered single prompt, Compound Engineering, and metareview. Three effort levels: low, medium, high. The planned 72-cell matrix has 66 complete cells on the primary six-PR sample; six Fable harness cells have partial coverage. The open-weight comparison covers these two GLM deployments, not every Chinese or emerging model. GLM-5.3 used a hosted 4-bit quantized build; the Flash serving build was not documented. Geographic background for GLM: Z.ai/Zhipu official company page, https://www.zhipuai.cn/en/about .',delivery:'Give each question a beat. The family names support the question, not a roster to read aloud. Do not say all 72 configurations were complete.'};
s.speakerNotes.textFrame.setText(`${story.stageCue}\n\n${story.script}\n\nSOURCES AND SCOPE\n${story.source}\nPrimary research: https://github.com/dsifry/harnesseval/blob/8f634b68664751527a9ad0123d1a082dd70a0931/REPORT.md`);
await fs.writeFile(`${w}/new-slide-story.json`,JSON.stringify(story,null,2)+'\n');
await (await PresentationFile.exportPptx(p)).save(`${w}/new-slide-raw.pptx`);
const png=await p.export({slide:s,format:'png',scale:.75});await fs.writeFile(`${w}/new-slide-preview.png`,new Uint8Array(await png.arrayBuffer()));
