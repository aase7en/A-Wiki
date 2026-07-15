// === app.js — globals, helpers, boot sequence (v8 refactor) ===
const S={connected:false,hookCount:0,eventCount:0,modelsUsed:new Set(),tier:'?',
active:{},activeCount:0,parallelCount:0,failCount:0,failures:[],delegateFree:0,delegatePaid:0,wfTimers:{},_tiers:{'L-1':15,'L0':30,'L1':45,'L2':60,'L3':80,'L4':100}};
const $=id=>document.getElementById(id);
const mk=(t,c)=>{const e=document.createElement(t);if(c)e.className=c;return e;};
const reduceMotion=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function animateCounter(el,target){
if(!el)return;
const cur=parseInt(el.textContent||'0',10)||0;
if(cur===target||reduceMotion){el.textContent=target;return;}
const wrap=el.closest('.stat-item');
const start=performance.now(),dur=480,from=cur;
function step(now){const p=Math.min(1,(now-start)/dur);
el.textContent=Math.round(from+(target-from)*(1-Math.pow(1-p,3)));
if(p<1)requestAnimationFrame(step);}
requestAnimationFrame(step);
if(wrap){wrap.classList.remove('tick');void wrap.offsetWidth;wrap.classList.add('tick');}
}
function bumpCounter(id,n){animateCounter($(id),n);}
const TYPED=[
'Monitoring the swarm…','Cost-first routing active','Senior Critic validates all','Free models preferred'
];
let _typedIdx=0,_typedPos=0,_typedDel=false,_typedRAF=null;
function typedStep(){
const el=$('typed-intro');if(!el)return;
const phrase=TYPED[_typedIdx%TYPED.length];
if(reduceMotion){el.textContent=phrase;return;}
_typedPos+=_typedDel?-1:1;
el.textContent=phrase.slice(0,_typedPos);
let delay=_typedDel?35:70;
if(!_typedDel&&_typedPos>=phrase.length){delay=1400;_typedDel=true;}
else if(_typedDel&&_typedPos<=0){_typedDel=false;_typedIdx++;delay=350;}
_typedRAF=setTimeout(typedStep,delay);
}
typedStep();
const WF={session:$('wf-session'),plan:$('wf-plan'),swarm:$('wf-swarm'),cost:$('wf-cost')};
function hotWf(id,ms=6000){const el=WF[id];if(!el)return;el.classList.remove('hot');void el.offsetWidth;
el.classList.add('hot');clearTimeout(S.wfTimers[id]);S.wfTimers[id]=setTimeout(()=>el.classList.remove('hot'),ms);}
const LANE_COLORS={gemini:'#7ba3ff',deepseek:'#00c4e0',groq:'#ff6b6b',openrouter:'#a0d0a0',
anthropic:'#ff8c69',zhipu:'#c17de8',qwen:'#ffb347',default:'#94a3b8'};
function laneColor(m){for(const[k,v]of Object.entries(LANE_COLORS))if(m.includes(k))return v;return LANE_COLORS.default;}
const MODEL_ICON={gemini:'🏆',deepseek:'🏆',groq:'🏆',openrouter:'🏆',anthropic:'🏆',zhipu:'🏆',qwen:'🏆',default:'🏆'};
const flowSvg=$('flow-svg'),pipeG=$('pipe-g'),particleG=$('particle-g'),flowOverlay=$('flow-overlay'),flowStage=$('flow-stage');
const SVGNS='http://www.w3.org/2000/svg';
const _stations={};
let _originEl=null,_originCore=null;
let _particles=[],_particleRAF=null;
let _stageRO=new ResizeObserver(()=>layoutFlow());
function svgEl(tag,attrs){const e=document.createElementNS(SVGNS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);return e;}
function buildOrigin(){
flowOverlay.innerHTML='';
const wrap=mk('div','origin-wrap');wrap.id='origin-wrap';
_originCore=mk('div','origin-core');_originCore.textContent='🧠';
const nm=mk('div','origin-nm');nm.textContent='Senior Critic';
const st=mk('div','origin-st');st.id='flow-origin-st';
st.innerHTML='<span class="fade-cycle"><span class="word">watching</span><span class="word">validating</span><span class="word">delegating</span></span>';
wrap.append(_originCore,nm,st);flowOverlay.appendChild(wrap);
_originEl=wrap;
}
function addStation(model){
const key=modelKey(model);
if(_stations[key])return _stations[key];
const color=laneColor(model),icon=MODEL_ICON[key]||MODEL_ICON.default,name=modelShort(model);
const wrap=mk('div','station');wrap.dataset.key=key;
const core=mk('div','station-core');core.style.setProperty('--st-color',color);
const ic=mk('div','station-ic');ic.textContent=icon;
const nm=mk('div','station-nm');nm.textContent=name;nm.title=model;
const cnt=mk('div','station-cnt');cnt.textContent='0';
core.append(ic,nm,cnt);wrap.append(core);flowOverlay.appendChild(wrap);
const pipe=svgEl('path',{class:'pipe',d:'M0 0'});
pipe.style.setProperty('--pipe-color',color);
pipeG.appendChild(pipe);
_stations[key]={key,name,color,icon,el:wrap,coreEl:core,cntEl:cnt,pipeEl:pipe,active:false,count:0,disabled:false};
return _stations[key];
}
function layoutFlow(){
const w=flowStage.clientWidth,h=flowStage.clientHeight;
if(w<2||h<2)return;
flowSvg.setAttribute('viewBox',`0 0 ${w} ${h}`);
const ox=Math.max(70,w*0.16),oy=h*0.5;
if(_originEl){_originEl.style.left=ox+'px';_originEl.style.top=oy+'px';}
const keys=Object.keys(_stations);
$('flow-empty').style.display=keys.length?'none':'flex';
if(!keys.length){pipeG.innerHTML='';return;}
const n=keys.length;
keys.forEach((k,i)=>{
const st=_stations[k];
const sx=Math.min(w-92,w*0.80);
const sy=n===1?oy:(h*(i+0.5)/n);
st.el.style.left=sx+'px';st.el.style.top=sy+'px';
const cx=sx-44,cy=sy;
const d=`M${ox+38} ${oy} C ${ox+90} ${oy}, ${cx-60} ${cy}, ${cx} ${cy}`;
st.pipeEl.setAttribute('d',d);
st.pathLen=st.pipeEl.getTotalLength();
st._x1=ox+38;st._y1=oy;st._x2=cx;st._y2=cy;
});
}
function setOriginBusy(busy){if(_originCore)_originCore.classList.toggle('busy',busy);}
function setFlowOriginStatus(txt,color){const el=$('flow-origin-st');if(el){if(txt){el.textContent=txt;el.style.color=color||'';}else el.innerHTML='<span class="fade-cycle"><span class="word">watching</span><span class="word">validating</span><span class="word">delegating</span></span>';}}
function flowActivate(model,task){
const st=addStation(model);layoutFlow();
st.active=true;st.el.classList.remove('done','fail');st.el.classList.add('active');
st.pipeEl.classList.remove('return','fail');st.pipeEl.classList.add('active');
setOriginBusy(true);
st._emit=true;
for(let i=0;i<3;i++)setTimeout(()=>emitParticle(st,'out'),i*120);
setFlowOriginStatus(`→ ${st.name}`,'var(--role-subagent)');
}
function flowComplete(model,ok,durationMs){
const key=modelKey(model);const st=_stations[key];if(!st)return;
st.active=false;st._emit=false;
st.el.classList.remove('active');
st.el.classList.add(ok?'done':'fail');
st.pipeEl.classList.remove('active','fail');
st.pipeEl.classList.add(ok?'return':'fail');
setTimeout(()=>{st.pipeEl.classList.remove('return','fail');},1200);
if(ok){st.count++;st.cntEl.textContent=String(st.count);animateCounter(st.cntEl,st.count);
for(let i=0;i<2;i++)setTimeout(()=>emitParticle(st,'in'),i*110);}
const anyActive=Object.values(_stations).some(s=>s.active);
setOriginBusy(anyActive);
if(!anyActive)setFlowOriginStatus(ok?'validating…':'reviewing…',ok?'var(--accent-success)':'var(--accent-danger)');
}
function emitParticle(st,dir){
if(reduceMotion||!st.pathLen)return;
if(_particles.length>44)_particles.shift();
_particles.push({st,dir:dir||'out',t:0,speed:0.006+Math.random()*0.005,color:st.color,size:1.6+Math.random()*1.8});
if(!_particleRAF)_particleRAF=requestAnimationFrame(particleLoop);
}
function particleLoop(){
if(!_particles.length){_particleRAF=null;return;}
const keep=[];
for(const p of _particles){
p.t+=p.speed;
if(p.t<1.02)keep.push(p);
}
_particles=keep;
particleG.innerHTML='';
for(const p of _particles){
if(!p.st.pipeEl||!p.st.pathLen)continue;
const tt=Math.max(0,Math.min(1,p.t));
const seg=p.dir==='in'?(1-tt):tt;
const pt=p.st.pipeEl.getPointAtLength(p.st.pathLen*seg);
const c=svgEl('circle',{cx:pt.x.toFixed(1),cy:pt.y.toFixed(1),r:p.size.toFixed(1),class:'particle'});
c.style.setProperty('--p-color',p.color);
particleG.appendChild(c);
}
for(const st of Object.values(_stations)){
if(st.active&&st._emit&&Math.random()<0.55)emitParticle(st,'out');
}
_particleRAF=requestAnimationFrame(particleLoop);
}
let _lastEventTs=Date.now();
const verbose=false;
function spawnThought(){if(!verbose)return;}
let currentView='summary';
function setView(v){
currentView=v;
const sm=$('btn-summary'),fl=$('btn-flow'),tl=$('btn-timeline'),gr=$('btn-graph'),sk=$('btn-skills'),ch=$('btn-chat'),co=$('btn-council'),cv=$('btn-coverage'),sb=$('btn-subagents'),an=$('btn-analytics'),ev=$('btn-eval');
sm.classList.toggle('active',v==='summary');fl.classList.toggle('active',v==='flow');tl.classList.toggle('active',v==='timeline');gr.classList.toggle('active',v==='graph');sk.classList.toggle('active',v==='skills');ch.classList.toggle('active',v==='chat');co.classList.toggle('active',v==='council');cv&&cv.classList.toggle('active',v==='coverage');sb&&sb.classList.toggle('active',v==='subagents');an&&an.classList.toggle('active',v==='analytics');ev&&ev.classList.toggle('active',v==='eval');
$('view-summary').style.display=v==='summary'?'flex':'none';
$('flow-panel').style.display=v==='flow'?'flex':'none';
$('timeline-panel').style.display=v==='timeline'?'flex':'none';
$('graph-vis').style.display=v==='graph'?'block':'none';
$('skills-panel').style.display=v==='skills'?'flex':'none';
$('coverage-panel').style.display=v==='coverage'?'flex':'none';
$('analytics-panel').style.display=v==='analytics'?'flex':'none';
$('subagents-panel').style.display=v==='subagents'?'flex':'none';
$('eval-panel').style.display=v==='eval'?'flex':'none';
$('chat-panel').style.display=v==='chat'?'flex':'none';
$('council-panel').style.display=v==='council'?'flex':'none';
if(v==='flow')layoutFlow();
else if(v==='timeline')renderLanes();
else if(v==='graph')initGraph();
if(v==='skills'){skillsLoad();loadWalkthroughs();applyUrlParams();renderDiscoveryBar();loadSotd();_initPresetDropdown();if(window._autoDetectedAgent)_applyAutoDetectedAgent();}
if(v==='coverage')coverageLoad();
if(v==='analytics')analyticsLoad();
if(v==='subagents')subagentsLoad();
if(v==='eval')evalHistoryLoad();
if(v==='council'){councilShowList();councilStartPoll();}else councilStopPoll();
syncUrlState();
}

// === BOOT SEQUENCE (runs after DOM is parsed) ===
