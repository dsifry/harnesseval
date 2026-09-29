import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const ROOT='/Users/dsifry/Documents/Codex/2026-09-28/we-a';
const SKILL='/Users/dsifry/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';
const PY='/Users/dsifry/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')));
const story=JSON.parse(await fs.readFile(path.join(ROOT,'work/deck/story.json'),'utf8'));
const W=1600,H=900,F='Helvetica Neue';
const C={bg:'#101110',white:'#F4F1E9',muted:'#C4C1B9',orange:'#F17A43',gray:'#92938F',dim:'#3D403C'};
const p=Presentation.create({slideSize:{width:W,height:H}});
const allSlides=[];
const noLine={fill:'none',width:0};
function text(s,str,x,y,w,h,size=90,color=C.white,bold=false,font=F){
  const t=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:noLine});
  t.text=str;t.text.style={typeface:font,fontSize:size,color,bold,autoFit:'none'};return t;
}
function title(s,str){return text(s,str,96,72,1408,140,88,C.white,true);}
function sub(s,str){return text(s,str,100,203,1400,75,34,C.muted);}
async function photo(s,file){s.images.add({blob:new Uint8Array(await fs.readFile(path.join(ROOT,'outputs/assets',file))),contentType:'image/png',fit:'cover',position:{left:0,top:0,width:W,height:H},alt:`Generated editorial illustration: ${file}`});}
function dots(s,series,opts={}){
  const cols=opts.cols??21, rows=opts.rows??7;
  const cfg={position:{left:opts.left??640,top:opts.top??270,width:opts.width??845,height:opts.height??500},
    series:series.map(q=>({name:q.name,xValues:q.ids.map(i=>i%cols+1),values:q.ids.map(i=>rows-Math.floor(i/cols)),fill:q.color,line:noLine,marker:{symbol:opts.symbol??'circle',size:opts.size??19}})),
    hasLegend:false,scatterOptions:{style:'marker'},dataLabels:{showValue:false},xAxis:{visible:false,tickLabelPosition:'none',min:0,max:cols+1,majorGridlines:null,line:noLine},yAxis:{visible:false,tickLabelPosition:'none',min:0,max:rows+1,majorGridlines:null,line:noLine},chartFill:C.bg,chartLine:noLine,plotAreaFill:C.bg,plotAreaLine:noLine};
  const ch=s.charts.add('scatter',cfg);applyPresentationChartFont(ch,{fontFamily:F});return ch;
}
function bars(s,categories,values,colors,{max,format='0',labels,unit}={}){
  if(unit)sub(s,unit);
  const ch=s.charts.add('bar',{
    position:{left:120,top:285,width:1360,height:440},categories,
    series:[{name:unit??'Value',values,valuesFormatCode:format,fill:C.orange,line:noLine,points:colors.map((fill,idx)=>({idx,fill,line:noLine})),...(labels?{dataLabelOverrides:labels.map((t,idx)=>({idx,text:t,position:'outEnd',showValue:false,textStyle:{typeface:F,fontSize:64,fill:idx===1?C.orange:C.white,bold:true}}))}:{})}],
    barOptions:{direction:'column',grouping:'clustered',gapWidth:140,varyColors:true},hasLegend:false,
    dataLabels:{showValue:!labels,position:'outEnd',textStyle:{typeface:F,fontSize:64,fill:C.white,bold:true}},
    xAxis:{visible:true,line:{fill:C.dim,width:1},majorGridlines:null,textStyle:{typeface:F,fontSize:38,fill:C.white}},
    yAxis:{visible:false,tickLabelPosition:'none',min:0,max,numberFormatCode:format,majorGridlines:null,line:noLine},
    chartFill:C.bg,chartLine:noLine,plotAreaFill:C.bg,plotAreaLine:noLine
  });applyPresentationChartFont(ch,{fontFamily:F});return ch;
}

function poly(s,pts,color=C.gray,width=4,fill='none'){
 const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]),x=Math.min(...xs),y=Math.min(...ys),w=Math.max(1,Math.max(...xs)-x),h=Math.max(1,Math.max(...ys)-y);
 return s.shapes.add({geometry:'custom',position:{left:x,top:y,width:w,height:h},fill,line:width?{fill:color,width}:noLine,customPaths:[{width:w,height:h,commands:pts.map((p,i)=>i?{lineTo:{x:p[0]-x,y:p[1]-y}}:{moveTo:{x:p[0]-x,y:p[1]-y}})}]});
}
function arrow(s,x1,y1,x2,y2,color=C.gray,width=4){
 poly(s,[[x1,y1],[x2,y2]],color,width);
 const a=Math.atan2(y2-y1,x2-x1),len=16,half=8;
 poly(s,[[x2,y2],[x2-len*Math.cos(a)+half*Math.sin(a),y2-len*Math.sin(a)-half*Math.cos(a)],[x2-len*Math.cos(a)-half*Math.sin(a),y2-len*Math.sin(a)+half*Math.cos(a)],[x2,y2]],color,0,color);
}
function harnessDiagram(s){
 title(s,'Same model. Better process.');
 text(s,'One prompt',100,235,650,70,42,C.gray,true);
 text(s,'Change',100,337,250,90,48,C.white,true);
 text(s,'Review',735,337,245,90,48,C.white,true);
 text(s,'Findings',1260,337,300,90,48,C.white,true);
 arrow(s,335,373,700,373,C.gray);arrow(s,955,373,1224,373,C.gray);
 text(s,'A harness',100,490,550,70,42,C.orange,true);
 text(s,'Change',100,646,250,90,48,C.white,true);
 text(s,'Checks',402,646,200,90,48,C.orange,true);
 text(s,'Combine',1007,646,260,90,48,C.orange,true);
 text(s,'Findings',1260,646,300,90,48,C.white,true);
 text(s,'Focused reviews',650,474,515,70,39,C.orange,true);
 arrow(s,335,681,377,681,C.gray);
 // Three example lenses, not an exhaustive roster or a claimed reviewer count.
 const lens=[['Security',570],['Architecture',646],['Tests',722]];
 for(const [label,y]of lens){
   text(s,label,687,y,310,66,40,C.white,true);
   poly(s,[[604,681],[640,681],[640,y+29],[670,y+29]],C.orange,3);
   poly(s,[[970,y+29],[994,y+29],[994,681],[1000,681]],C.orange,3);
 }
 text(s,'…',780,793,110,60,42,C.muted);
 arrow(s,1228,681,1249,681,C.gray);
}
function developerLoop(s){
 const y=305;
 text(s,'Review',100,y,290,130,72,C.white,true);
 text(s,'Reproduce',450,y,490,130,72,C.white,true);
 text(s,'Fix',1005,y,170,130,72,C.white,true);
 text(s,'Test',1280,y,230,130,72,C.white,true);
 arrow(s,385,364,428,364,C.gray,5);arrow(s,897,364,978,364,C.gray,5);arrow(s,1153,364,1253,364,C.gray,5);
 poly(s,[[1400,445],[1400,651],[220,651],[220,444]],C.orange,6);
 arrow(s,220,499,220,444,C.orange,6);
 text(s,'Repeat',603,684,460,130,96,C.orange,true);
}

const ids=(start,n)=>Array.from({length:n},(_,i)=>i+start);
const cats=['Fable 5.1\nSingle prompt\nHigh reasoning','GLM 5.3 Flash\nHarness\nLow reasoning'];
for(let i=0;i<20;i++){
 const s=p.slides.add();allSlides.push(s);s.background.fill=C.bg;
 s.speakerNotes.textFrame.setText(`${story[i].source}\nPrimary research: https://github.com/dsifry/harnesseval/blob/8f634b68664751527a9ad0123d1a082dd70a0931/REPORT.md`);
 switch(i+1){
 case 1: text(s,'I thought',92,173,1410,200,158,C.white,true);text(s,'it was me.',90,390,1420,220,174,C.orange,true);break;
 case 2: text(s,'−',108,274,130,160,128,'#DD8978');text(s,'Is it me?',263,274,1190,160,128,'#A9ACA9');text(s,'+',108,494,130,160,128,'#9FC9B2');text(s,'What works?',263,494,1240,160,128,C.white,true);break;
 case 3: text(s,'2,416',86,173,700,260,206,C.orange,true);text(s,'AI code reviews',101,447,720,110,76,C.white,true);text(s,'72 configurations',858,90,675,80,46,C.white,true);text(s,'8 models × 3 approaches × 3 effort levels',105,740,1395,66,38,C.white);text(s,'Six-PR coverage: 66 complete, 6 partial',105,810,1395,54,30,C.muted);dots(s,[{name:'Complete configurations',ids:ids(0,72).filter(n=>n<3||n>8),color:C.orange},{name:'Partial configurations',ids:ids(3,6),color:C.gray}],{left:825,top:163,width:665,height:500,size:22,cols:9,rows:8,symbol:'square'});break;
 case 4: text(s,'42',80,175,535,325,280,C.white,true);text(s,'known bugs',100,530,525,105,62,C.white,true);dots(s,[{name:'Original benchmark bugs',ids:ids(0,42),color:C.white}]);break;
 case 5: text(s,'+105',80,180,605,300,226,C.orange,true);text(s,'verified defects',100,520,570,90,56,C.white,true);text(s,'147 in total',105,665,500,80,42,C.muted);dots(s,[{name:'Original benchmark bugs',ids:ids(0,42),color:C.white},{name:'Additional verified defects',ids:ids(42,105),color:C.orange}]);break;
 case 6: harnessDiagram(s);break;
 case 7: text(s,'39',85,110,720,335,290,C.orange,true);text(s,'of 42',105,452,585,130,104,C.white,true);text(s,'matched comparisons',108,616,645,82,49,C.white,true);text(s,'found more bugs',110,710,610,75,45,C.white);dots(s,[{name:'Harness found more',ids:ids(0,39),color:C.orange},{name:'No increase',ids:ids(39,3),color:C.gray}],{left:750,top:135,width:745,height:635,size:27,cols:6,rows:7,symbol:'square'});break;
 case 8: text(s,'10×',85,118,1390,370,310,C.orange,true);text(s,'the tokens',104,550,1380,150,107,C.white,true);text(s,'Median matched comparison',110,754,1250,65,34,C.muted);break;
 case 9: await photo(s,'reasoning-dial.png');text(s,'More\nthinking?',96,270,715,320,120,C.white,true);break;
 case 10: title(s,'Often, no clear gain');bars(s,['No clear winner','High better','Medium better'],[17,4,1],[C.orange,C.gray,C.gray],{max:21,unit:'High vs. medium reasoning on benchmark F1'});break;
 case 11: title(s,'This setup found more');bars(s,cats,[51,71],[C.gray,C.orange],{max:90,unit:'Verified bugs found across six PRs, out of 147'});break;
 case 12: title(s,'1/55 the API cost');bars(s,cats,[1.29594,.02354],[C.gray,C.orange],{max:1.6,format:'$0.000',labels:['$1.30','$0.024'],unit:'Mean API cost per review, at study list prices'});break;
 case 13: title(s,'Nearly twice as fast');bars(s,cats,[147.69631,78.54169],[C.gray,C.orange],{max:180,labels:['148s','79s'],unit:'Mean elapsed time per review'});break;
 case 14: text(s,'59',80,155,570,345,285,C.orange,true);text(s,'bugs missed',100,532,560,100,62,C.white,true);text(s,'Even the best found 88 / 147',104,720,1280,74,40,C.muted);dots(s,[{name:'Found by highest recall configuration',ids:ids(0,88),color:C.white},{name:'Missed by highest recall configuration',ids:ids(88,59),color:C.orange}]);break;
 case 15: text(s,'50 PRs.',93,155,1400,190,166,C.white,true);text(s,'Five codebases.',94,405,1400,200,133,C.orange,true);text(s,'Full campaign: 2,416 healthy reviews',106,707,1350,75,38,C.muted);break;
 case 16: text(s,'Find bugs.',96,184,1400,200,158,C.white,true);text(s,'Before users do.',94,427,1420,200,136,C.orange,true);break;
 case 17: developerLoop(s);break;
 case 18: text(s,'Use a',96,180,1350,170,130,C.white,true);text(s,'harness.',90,365,1420,235,192,C.orange,true);break;
 case 19: text(s,'Start low.',94,166,1420,170,141,C.white,true);text(s,'Try open weights.',94,390,1430,220,137,C.orange,true);break;
 case 20: text(s,'Follow the',96,187,1410,180,151,C.white,true);text(s,'evidence.',92,411,1420,235,194,C.orange,true);break;
 }
}
await fs.mkdir(path.join(ROOT,'work/deck/previews-v9'),{recursive:true});
await (await PresentationFile.exportPptx(p)).save(path.join(ROOT,'work/deck/candidate-v9.pptx'));
for(let i=0;i<20;i++){
 const preview=await p.export({slide:allSlides[i],format:'png',scale:1});
 await fs.writeFile(path.join(ROOT,`work/deck/previews-v9/slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await preview.arrayBuffer()));
}
console.log('Exported and rendered 20 slides for compatibility repair and validation.');
