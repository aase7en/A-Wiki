// === app.js — globals, helpers, boot sequence (v8 refactor) ===
const S={connected:false,hookCount:0,eventCount:0,modelsUsed:new Set(),tier:'?',
active:{},activeCount:0,parallelCount:0,failCount:0,failures:[],delegateFree:0,delegatePaid:0,wfTimers:{},_tiers:{'L-1':15,'L0':30,'L1':45,'L2':60,'L3':80,'L4':100}};
const $=id=>document.getElementById(id);
const mk=(t,c)=>{const e=document.createElement(t);if(c)e.className=c;return e;};
const reduceMotion=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
// CHUNK B10: TTL cache for expensive GET APIs (skills list, coverage stats).
// Avoids re-fetching ~250 skills or full coverage matrix on every tab switch.
// Entries: {key: {val, exp}} — exp = absolute ms timestamp.
// Invalidate on SSE registry_update (graph.js) and after inline edits.
const _ttlCache={};
function _cacheSet(key,val,maxAgeSec){
  _ttlCache[key]={val:val,exp:Date.now()+Math.max(0,maxAgeSec)*1000};
}
function _cacheGet(key){
  const e=_ttlCache[key];
  if(!e)return null;
  if(Date.now()>e.exp){delete _ttlCache[key];return null;}
  return e.val;
}
function _cacheInvalidate(key){
  if(key)delete _ttlCache[key];else{for(const k in _ttlCache)delete _ttlCache[k];}
}
// CHUNK G8: shared download helper (deduplicates Blob→<a>→click→revoke pattern).
function _downloadBlob(blob,filename){
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;a.download=filename;document.body.appendChild(a);a.click();document.body.removeChild(a);
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
// CHUNK A11: localStorage backup — export all awiki-* keys.
// Whitelist by prefix so we skip unrelated localStorage from other tools on
// the same origin. Auto-backup key (awiki-auto-backups) is skipped to avoid
// recursion. Schema versioned for future migrations.
const BACKUP_SKIP_KEYS=new Set(['awiki-auto-backups','awiki-last-backup']);
function _collectBackupKeys(){
  const out={};
  for(let i=0;i<localStorage.length;i++){
    const k=localStorage.key(i);
    if(!k||!k.startsWith('awiki-'))continue;
    if(BACKUP_SKIP_KEYS.has(k))continue;
    try{out[k]=JSON.parse(localStorage.getItem(k));}catch(_){out[k]=localStorage.getItem(k);}
  }
  return out;
}
function exportAllBackup(){
  const keys=_collectBackupKeys();
  const payload={
    version:1,
    exported_at:new Date().toISOString(),
    key_count:Object.keys(keys).length,
    keys:keys,
  };
  const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});
  const d=new Date();
  const stamp=d.getFullYear()+String(d.getMonth()+1).padStart(2,'0')+String(d.getDate()).padStart(2,'0');
  _downloadBlob(blob,'awiki-backup-'+stamp+'.json');
  const st=$('backup-status');
  if(st)st.textContent='📤 ส่งออก '+Object.keys(keys).length+' keys เรียบร้อย';
}
function loadBackupPane(){
  const list=$('backup-keys-list');
  if(!list)return;
  const keys=_collectBackupKeys();
  const names=Object.keys(keys).sort();
  let totalBytes=0;
  const rows=names.map(k=>{
    const raw=localStorage.getItem(k)||'';
    const bytes=new Blob([raw]).size;
    totalBytes+=bytes;
    return '<div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid var(--border)"><span style="font-family:var(--font-mono);color:var(--text-secondary)">'+k+'</span><span style="color:var(--text-tertiary)">'+(bytes/1024).toFixed(1)+'KB</span></div>';
  }).join('');
  list.innerHTML=rows||'<div style="color:var(--text-tertiary);padding:8px">ไม่มี awiki-* keys</div>';
  const meter=$('backup-usage-meter');
  if(meter){
    const pct=(totalBytes/(5*1024*1024)*100).toFixed(1);
    const color=pct<60?'var(--accent-success)':pct<85?'var(--accent-warm)':'var(--accent-danger)';
    meter.innerHTML='<div style="font-size:var(--fs-2xs);color:var(--text-tertiary);margin-bottom:3px">localStorage: '+(totalBytes/1024).toFixed(1)+'KB / 5MB ('+pct+'%) · '+names.length+' keys</div><div style="height:6px;background:var(--elev-3);border-radius:3px;overflow:hidden"><div style="height:100%;width:'+Math.min(100,pct)+'%;background:'+color+';transition:width .3s"></div></div>';
  }
}
// CHUNK D9: focus trap + restore for modals (WCAG 2.4.3 Focus Order).
// Usage: _openModalTrap(modalEl) on open, _closeModalTrap() on close.
let _trapLastFocused=null,_trapHandler=null;
function _focusableEls(container){
  return Array.from(container.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')).filter(el=>el.offsetParent!==null&&!el.disabled);
}
function _openModalTrap(modalEl){
  if(!modalEl)return;
  _trapLastFocused=document.activeElement;
  // Move focus into modal
  const focusable=_focusableEls(modalEl);
  if(focusable.length)focusable[0].focus();else modalEl.setAttribute('tabindex','-1'),modalEl.focus();
  // Trap Tab/Shift+Tab
  _trapHandler=function(e){
    if(e.key!=='Tab')return;
    const f=_focusableEls(modalEl);
    if(!f.length)return;
    const first=f[0],last=f[f.length-1];
    if(e.shiftKey){if(document.activeElement===first){e.preventDefault();last.focus();}}
    else{if(document.activeElement===last){e.preventDefault();first.focus();}}
  };
  modalEl.addEventListener('keydown',_trapHandler);
}
function _closeModalTrap(){
  if(_trapHandler){document.removeEventListener('keydown',_trapHandler);_trapHandler=null;}
  if(_trapLastFocused&&typeof _trapLastFocused.focus==='function'){try{_trapLastFocused.focus();}catch(_){}}
  _trapLastFocused=null;
}
// CHUNK F9: screen reader announcement helper (writes to #aria-live, SR reads aloud).
let _announceTimer=null;
function announce(msg){
  const live=$('aria-live');if(!live)return;
  // Clear + re-set so SR re-announces even if same message.
  live.textContent='';
  clearTimeout(_announceTimer);
  _announceTimer=setTimeout(()=>{live.textContent=msg;},100);
}
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
// CHUNK C10: pause the animation loop when not on the Flow view (saves CPU
// when the tab is hidden). Particles are not drained — they resume on return.
if(currentView!=='flow'){_particleRAF=null;return;}
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
// CHUNK C10: track which views have been initialized once this session.
// setView(v) skips the heavy-load call on revisit unless force=true is passed
// (Refresh buttons use force=true to bypass the guard and re-fetch).
const _loaded={};
function setView(v,opts){
const force=opts&&(opts.force===true);
currentView=v;
const sm=$('btn-summary'),fl=$('btn-flow'),tl=$('btn-timeline'),gr=$('btn-graph'),sk=$('btn-skills'),ch=$('btn-chat'),co=$('btn-council'),cv=$('btn-coverage'),sb=$('btn-subagents'),an=$('btn-analytics'),ev=$('btn-eval'),ct=$('btn-cost'),rc=$('btn-race');
sm.classList.toggle('active',v==='summary');fl.classList.toggle('active',v==='flow');tl.classList.toggle('active',v==='timeline');gr.classList.toggle('active',v==='graph');sk.classList.toggle('active',v==='skills');ch.classList.toggle('active',v==='chat');co.classList.toggle('active',v==='council');cv&&cv.classList.toggle('active',v==='coverage');sb&&sb.classList.toggle('active',v==='subagents');an&&an.classList.toggle('active',v==='analytics');ev&&ev.classList.toggle('active',v==='eval');ct&&ct.classList.toggle('active',v==='cost');rc&&rc.classList.toggle('active',v==='race');
// CHUNK B9: update ARIA tab state (roving tabindex — only active tab is focusable).
const tabs=[sm,fl,tl,gr,sk,ch,co,cv,sb,an,ev,ct].filter(Boolean);
const viewMap={summary:'summary',flow:'flow',timeline:'timeline',graph:'graph',skills:'skills',chat:'chat',council:'council',coverage:'coverage',subagents:'subagents',analytics:'analytics',eval:'eval',cost:'cost'};
tabs.forEach(t=>{const tv=viewMap[t.id.replace('btn-','')];const isActive=tv===v;t.setAttribute('aria-selected',isActive?'true':'false');t.setAttribute('tabindex',isActive?'0':'-1');});
// CHUNK B9: arrow-key navigation between tabs (WAI-ARIA tab pattern).
const vtb=document.querySelector('.view-toggle-bar');
if(vtb&&!vtb._arrowBound){vtb._arrowBound=true;vtb.addEventListener('keydown',function(e){if(e.key!=='ArrowRight'&&e.key!=='ArrowLeft')return;const cur=tabs.indexOf(document.activeElement);if(cur<0)return;e.preventDefault();let nxt;if(e.key==='ArrowRight')nxt=(cur+1)%tabs.length;else nxt=(cur-1+tabs.length)%tabs.length;tabs[nxt].focus();setView(viewMap[tabs[nxt].id.replace('btn-','')]);});}
$('view-summary').style.display=v==='summary'?'flex':'none';
$('flow-panel').style.display=v==='flow'?'flex':'none';
$('timeline-panel').style.display=v==='timeline'?'flex':'none';
$('graph-vis').style.display=v==='graph'?'block':'none';
$('skills-panel').style.display=v==='skills'?'flex':'none';
$('coverage-panel').style.display=v==='coverage'?'flex':'none';
$('analytics-panel').style.display=v==='analytics'?'flex':'none';
$('subagents-panel').style.display=v==='subagents'?'flex':'none';
$('eval-panel').style.display=v==='eval'?'flex':'none';
$('cost-panel').style.display=v==='cost'?'flex':'none';
$('race-panel').style.display=v==='race'?'flex':'none';
$('chat-panel').style.display=v==='chat'?'flex':'none';
$('council-panel').style.display=v==='council'?'flex':'none';
if(v==='flow')layoutFlow();
else if(v==='timeline')renderLanes();
else if(v==='graph')initGraph();
// CHUNK C10: skip heavy load on revisit unless force=true (Refresh button).
// First-time visits still load as before; revisit uses cached render.
const already=_loaded[v];
_loaded[v]=true;
if(!already||force){
if(v==='skills'){skillsLoad();loadWalkthroughs();applyUrlParams();renderDiscoveryBar();loadSotd();_initPresetDropdown();if(window._autoDetectedAgent)_applyAutoDetectedAgent();}
if(v==='coverage')coverageLoad();
if(v==='analytics')analyticsLoad();
if(v==='subagents')subagentsLoad();
if(v==='eval'){evalHistoryLoad();suiteEditorInit();}
if(v==='cost')costHistoryLoad();
if(v==='race')raceResultsLoad();
}
if(v==='council'){councilShowList();councilStartPoll();}else councilStopPoll();
syncUrlState();
}

// === BOOT SEQUENCE (runs after DOM is parsed) ===
