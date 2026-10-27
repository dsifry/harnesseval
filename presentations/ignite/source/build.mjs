import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const ROOT='/Users/dsifry/Documents/Codex/2026-09-28/we-a';
const SKILL='/Users/dsifry/.codex/plugins/cache/openai-primary-runtime/presentations/26.904.11930/skills/presentations';
const PY='/Users/dsifry/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')));
const story=JSON.parse(await fs.readFile(path.join(ROOT,'work/improve-v10/story.json'),'utf8'));
const W=1600,H=900,F='Helvetica Neue';
const C={bg:'#101110',white:'#F4F1E9',muted:'#C4C1B9',orange:'#F17A43',gray:'#92938F',dim:'#3D403C'};
const p=Presentation.create({slideSize:{width:W,height:H}});
const allSlides=[];
const noLine={fill:'none',width:0};
function text(s,str,x,y,w,h,size=90,color=C.white,bold=false,font=F){
  const t=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:noLine});
  t.text=str;t.text.style={typeface:font,fontSize:size,color,bold,autoFit:'none'};return t;
}
function title(s,str){return text(s,str,96,72,1408,132,88,C.white,true);}
function sub(s,str){return text(s,str,100,203,1400,75,34,C.muted);}
async function photo(s,file){s.images.add({blob:new Uint8Array(await fs.readFile(path.join(ROOT,'outputs/assets',file))),contentType:'image/png',fit:'cover',position:{left:0,top:0,width:W,height:H},alt:`Generated editorial illustration: ${file}`});}
function dots(s,series,opts={}){
  const cols=opts.cols??21, rows=opts.rows??7;
  const cfg={position:{left:opts.left??640,top:opts.top??270,width:opts.width??845,height:opts.height??500},
    series:series.map(q=>({name:q.name,xValues:q.ids.map(i=>i%cols+1),values:q.ids.map(i=>rows-Math.floor(i/cols)),fill:q.color,line:q.hollow?{fill:C.orange,width:3}:noLine,marker:{symbol:opts.symbol??'circle',size:opts.size??19}})),
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
 title(s,'Inside a review harness');
 text(s,'One prompt',100,220,600,64,40,C.gray,true);
 text(s,'Change',100,309,230,80,48,C.white,true);
 text(s,'Review',730,309,250,80,48,C.white,true);
 text(s,'Findings',1305,309,250,80,48,C.white,true);
 arrow(s,332,345,688,345,C.gray,4);arrow(s,958,345,1258,345,C.gray,4);
 text(s,'A harness',100,472,450,64,40,C.orange,true);
 text(s,'Focused reviews',585,472,640,64,40,C.orange,true);
 text(s,'Change',100,638,230,80,46,C.white,true);
 text(s,'Checks',350,638,210,80,46,C.orange,true);
 text(s,'Combine',1020,638,250,80,46,C.orange,true);
 text(s,'Findings',1305,638,250,80,46,C.white,true);
 arrow(s,290,674,326,674,C.gray,4);
 poly(s,[[542,674],[570,674]],C.orange,4);
 poly(s,[[592,592],[570,592],[570,756],[592,756]],C.orange,4);
 poly(s,[[570,674],[592,674]],C.orange,4);
 [['Security',559],['Architecture',641],['Tests',723]].forEach(([label,y])=>text(s,label,610,y,340,72,44,C.white,true));
 poly(s,[[936,592],[970,592],[970,756],[936,756]],C.orange,4);
 poly(s,[[936,674],[970,674]],C.orange,4);arrow(s,970,674,1000,674,C.orange,4);
 arrow(s,1242,674,1278,674,C.gray,4);
 text(s,'…',733,798,140,60,44,C.gray);
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


function singleBar(s,value,max,color,y,category){
 const ch=s.charts.add('bar',{
  position:{left:590,top:y,width:665,height:118},categories:[category],
  series:[{name:'Metric',values:[value],fill:color,line:noLine}],
  barOptions:{direction:'bar',grouping:'clustered',gapWidth:12},hasLegend:false,
  dataLabels:{showValue:false},
  xAxis:{visible:false,tickLabelPosition:'none',min:0,max,majorGridlines:null,line:noLine},
  yAxis:{visible:false,tickLabelPosition:'none',min:0,max,majorGridlines:null,line:noLine},
  chartFill:C.bg,chartLine:noLine,plotAreaFill:C.bg,plotAreaLine:noLine
 });applyPresentationChartFont(ch,{fontFamily:F});return ch;
}
function pair(s,heading,unit,values,max,labels){
 title(s,heading);text(s,unit,102,205,1398,74,36,C.muted);
 const names=['Fable 5.1','GLM 5.3 Flash'];
 const methods=['Single prompt','Harness'];const efforts=['High reasoning','Low reasoning'];
 [322,590].forEach((y,i)=>{
  const color=i?C.orange:C.gray;
  text(s,names[i],101,y,475,70,49,i?C.orange:C.white,true);
  text(s,methods[i],105,y+68,465,55,36,C.muted);
  text(s,efforts[i],105,y+116,465,55,36,C.muted);
  singleBar(s,values[i],max,color,y+28,`${names[i]} / ${methods[i]} / ${efforts[i]}`);
  text(s,labels[i],1234,y+31,288,118,84,i?C.orange:C.white,true);
 });
}
function uncertainty(s){
 title(s,'Often, no clear difference');
 text(s,'High vs. medium reasoning, original benchmark F1',102,205,1400,74,36,C.muted);
 const labels=['Unresolved','High better','Medium better'];const values=[17,4,1];
 [325,482,639].forEach((y,i)=>{
  text(s,labels[i],102,y+24,475,90,49,i?C.muted:C.white,i===0);
  singleBar(s,values[i],22,i===0?C.orange:C.gray,y,labels[i]);
  text(s,String(values[i]),1290,y+12,230,110,89,i===0?C.orange:C.white,true);
 });
}
function evidence(s){
 title(s,'Evidence you can rerun');
 text(s,'Discourse: re-importing a deleted post',102,215,1400,82,48,C.white);
 text(s,'Before fix',150,393,570,86,51,C.muted);
 text(s,'After fix',938,393,560,86,51,C.muted);
 text(s,'FAIL',134,489,640,205,163,'#DD8978',true);
 text(s,'PASS',919,489,650,205,163,'#9FC9B2',true);
 arrow(s,630,587,840,587,C.gray,5);
 text(s,'Isolated reproduction, verified defect 4-D14',106,778,1370,66,35,C.muted);
}

const ids=(start,n)=>Array.from({length:n},(_,i)=>i+start);
const cats=['Fable 5.1\nSingle prompt\nHigh reasoning','GLM 5.3 Flash\nHarness\nLow reasoning'];
for(let i=0;i<20;i++){
 const s=p.slides.add();allSlides.push(s);s.background.fill=C.bg;
 s.speakerNotes.textFrame.setText(`${story[i].stageCue}\n\n${story[i].script}\n\nSOURCES AND SCOPE\n${story[i].source}\nPrimary research: https://github.com/dsifry/harnesseval/blob/8f634b68664751527a9ad0123d1a082dd70a0931/REPORT.md`);
 switch(i+1){
 case 1: text(s,'I thought',92,173,1410,200,158,C.white,true);text(s,'it was me.',90,390,1420,220,174,C.orange,true);break;
 case 2: text(s,'−',108,274,130,160,128,'#DD8978');text(s,'Is it me?',263,274,1190,160,128,'#A9ACA9');text(s,'+',108,494,130,160,128,'#9FC9B2');text(s,'What works?',263,494,1240,160,128,C.white,true);break;
 case 3: text(s,'Dave Sifry',108.533333,53.333333,730,112,64,C.white);s.images.add({blob:new Uint8Array(await fs.readFile(path.join(ROOT,'outputs/assets/Dave_Sifry_Waving.png'))),contentType:'image/png',fit:'contain',position:{left:1173.333333,top:66.666667,width:320,height:266.666667},alt:'AI-generated portrait of Dave Sifry waving, based on his photograph'});text(s,'2,416',86,144,1450,365,300,C.orange,true);text(s,'AI code reviews',105,475,1380,145,94,C.white,true);text(s,'50 pull requests',109,694,730,112,64,C.white);text(s,'5 codebases',968,694,590,112,64,C.white);break;
 case 4: text(s,'42',80,175,535,325,280,C.white,true);text(s,'known bugs',100,530,525,105,62,C.white,true);dots(s,[{name:'Original benchmark bugs',ids:ids(0,42),color:C.white}]);break;
 case 5: text(s,'+105',80,180,605,300,226,C.orange,true);text(s,'verified defects',100,520,570,90,56,C.white,true);text(s,'147 in total',105,665,550,100,53,C.white,true);dots(s,[{name:'Original benchmark bugs',ids:ids(0,42),color:C.white},{name:'Additional verified defects',ids:ids(42,105),color:C.orange}]);break;
 case 6: harnessDiagram(s);break;
 case 7: title(s,'The harness found more');text(s,'39',82,238,655,325,264,C.orange,true);text(s,'of 42',103,557,560,135,102,C.white,true);text(s,'matched comparisons',105,736,760,81,49,C.white,true);dots(s,[{name:'Harness found more',ids:ids(0,39),color:C.orange},{name:'No increase',ids:ids(39,3),color:C.gray}],{left:810,top:269,width:700,height:478,size:27,cols:6,rows:7,symbol:'square'});break;
 case 8: text(s,'≈10×',82,125,1450,370,284,C.orange,true);text(s,'the tokens',104,550,1380,150,107,C.white,true);text(s,'Median matched comparison',110,754,1250,65,36,C.muted);break;
 case 9: await photo(s,'reasoning-dial.png');text(s,'More\nthinking?',96,270,715,320,120,C.white,true);break;
 case 10: uncertainty(s);break;
 case 11: pair(s,'20 more bugs','Verified bugs across the same six PRs, out of 147',[51,71],90,['51','71']);break;
 case 12: pair(s,'1/55 the API cost','Mean API cost per review, at study list prices',[1.29594,.02354],1.5,['$1.30','$0.024']);break;
 case 13: pair(s,'Nearly twice as fast','Mean elapsed time per review',[147.69631,78.54169],180,['148s','79s']);break;
 case 14: text(s,'59',80,155,570,345,285,C.orange,true);text(s,'bugs still missed',100,532,610,100,58,C.white,true);text(s,'Highest recall: 88 of 147 found',104,785,1380,78,43,C.white);dots(s,[{name:'Found by highest recall configuration',ids:ids(0,88),color:C.white},{name:'Missed by highest recall configuration',ids:ids(88,59),color:C.bg,hollow:true}]);break;
 case 15: evidence(s);break;
 case 16: text(s,'Find bugs.',96,184,1400,200,158,C.white,true);text(s,'Before users do.',94,427,1420,200,136,C.orange,true);break;
 case 17: developerLoop(s);break;
 case 18: text(s,'Use a harness',95,275,1460,255,169,C.orange,true);text(s,'Give reviewers focused jobs',110,578,1350,113,59,C.white);break;
 case 19: text(s,'Start low',94,166,1420,190,156,C.white,true);text(s,'Try open weights',94,422,1430,215,134,C.orange,true);break;
 case 20: text(s,'Follow the',96,187,1410,180,151,C.white,true);text(s,'evidence.',92,411,1420,235,194,C.orange,true);break;
 }
}
await fs.mkdir(path.join(ROOT,'work/improve-v10/previews'),{recursive:true});
await (await PresentationFile.exportPptx(p)).save(path.join(ROOT,'work/improve-v10/candidate.pptx'));
for(let i=0;i<20;i++){
 const preview=await p.export({slide:allSlides[i],format:'png',scale:1});
 await fs.writeFile(path.join(ROOT,`work/improve-v10/previews/slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await preview.arrayBuffer()));
}
console.log('Exported and rendered 20 slides for compatibility repair and validation.');
