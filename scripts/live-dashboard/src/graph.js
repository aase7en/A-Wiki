function initGraph(){
const c=$('graph-vis');if(!c||_gNet)return;
const fb=$('graph-unavailable');
if(!window.vis){if(fb)fb.style.display='flex';return;}
if(fb)fb.style.display='none';
if(!_gData)_gData={nodes:new vis.DataSet(),edges:new vis.DataSet()};
_gNet=new vis.Network(c,_gData,{physics:{solver:'barnesHut',barnesHut:{gravitationalConstant:-2000,centralGravity:.3,springLength:150}},
edges:{smooth:{type:'continuous'},width:2,arrows:{to:{enabled:true,scaleFactor:.5}}},
nodes:{shape:'dot',size:16,font:{size:11,color:'#cbd5e1'},borderWidth:2},
interaction:{hover:true,zoomView:true,dragView:true}});
fetch('/api/graph').then(r=>r.json()).then(updateGraph).catch(()=>{});
}
function updateGraph(d){
if(!d||!_gData)return;
S.parallelCount=d.parallel_count||0;
const keep=new Set(d.nodes.map(n=>n.id));
_gData.nodes.getIds().forEach(id=>{if(!keep.has(id))_gData.nodes.remove(id);});
d.nodes.forEach(n=>{const ex=_gData.nodes.get(n.id);
if(!ex||(ex.status!==n.status))_gData.nodes.update(Object.assign({font:{color:'#cbd5e1'}},n,{color:{background:n.color,border:n.color}}));});
const ek=new Set(d.edges.map(e=>`${e.from}→${e.to}`));
_gData.edges.getIds().forEach(id=>{const e=_gData.edges.get(id);if(!ek.has(`${e.from}→${e.to}`))_gData.edges.remove(id);});
d.edges.forEach(e=>{e.id=`${e.from}→${e.to}`;if(!_gData.edges.get(e.id))_gData.edges.add(e);});
updateParallel();
}
let _es=null,_retry=null;
function connect(){
if(_es){_es.close();_es=null;}clearTimeout(_retry);
try{_es=new EventSource('/events');}catch(e){scheduleRetry();return;}
_es.onopen=()=>{S.connected=true;$('live-dot').classList.add('on');$('offline').classList.remove('show');};
_es.onmessage=e=>{try{handleEvent(JSON.parse(e.data));}catch(_){}};
_es.onerror=()=>{S.connected=false;$('live-dot').classList.remove('on');$('offline').classList.add('show');
_es.close();_es=null;scheduleRetry();};
}
function scheduleRetry(){clearTimeout(_retry);_retry=setTimeout(connect,3000);}
function handleEvent(ev){
if(!ev||!ev.type)return;
_lastEventTs=Date.now();
if(ev.type==='backlog_complete'){renderLanes();layoutFlow();return;}
if(ev.type==='log_cleared'){doClearLocal();return;}
if(ev.type==='config_update'){loadRecommendations();loadModelStationsConfig();return;}
if(ev.type==='graph_update'){updateGraph(ev);return;}
if(ev.type==='registry_update'){
// CHUNK GG: registry changed on disk — silently reload the active data
// view so the dashboard reflects new/edited skills without a manual refresh.
// CHUNK B10: invalidate skills+coverage cache so the reload fetches fresh data.
_cacheInvalidate('skills:');
for(const k in _ttlCache){if(k.startsWith('skills:'))delete _ttlCache[k];}
_cacheInvalidate('coverage');
// CHUNK RR: desktop notification (deduped via tag).
showNotif('Registry อัปเดตแล้ว','skills/coverage รีเฟรชอัตโนมัติ','registry_update');
announce('Registry อัปเดตแล้ว — กำลังรีเฟรชข้อมูล');
try{
if(currentView==='skills'){skillsLoad();}
else if(currentView==='coverage'){coverageLoad();}
}catch(_){}
return;
}
switch(ev.type){
case'session_start':onSession(ev);break;
case'hook_check':onHook(ev);break;
case'cost_declare':onCost(ev);break;
case'delegate_start':onDelStart(ev);updateLane(ev);break;
case'delegate_done':onDelDone(ev);updateLane(ev);break;
  case'delegate_fail':onDelFail(ev);updateLane(ev);break;
  case'route_plan':onRoute(ev);break;
}
pushTimeline(ev);
}
function onSession(ev){hotWf('session',8000);setOriginStatus('session started','var(--accent-success)');
spawnThought('🚀 session started',{tone:'green',anchor:'origin'});}
function onHook(ev){
const{hook='',tool='',result='pass',tier=''}=ev;S.hookCount++;bumpCounter('s-hooks',S.hookCount);
if(hook.includes('delegation_gate'))hotWf('plan',5000);
else if(hook.includes('cost_tier'))hotWf('cost',4000);
else if(hook.includes('session'))hotWf('session',6000);
if(tier)setTier(tier);
const strip=$('hook-strip'),b=mk('div',`hook-badge ${result==='block'?'block':result==='warn'?'warn':'pass'}`);
const short=hook.replace('check_','').replace(/_/g,'-').substring(0,18);
b.textContent=(result==='block'?'🔴 ':'✅ ')+short+(tool?' ·'+tool:'')+(tier?' '+tier:'');
strip.insertBefore(b,strip.firstChild);
strip.querySelectorAll('.hook-badge').forEach((el,i)=>{if(i>8)el.remove();else if(i>4)el.classList.add('dim');});
  if(result==='block'){spawnThought(`🔒 ${short} blocked`,{tone:'red',anchor:'origin'});pushFailure(ev);showNotif('🔒 Hook บล็อก',short+(tool?' · '+tool:''),'hook_block');}
  else if(result==='warn')spawnThought(`⚠ ${short}`,{tone:'gold',anchor:'origin'});
}
function onCost(ev){const{tier='?',task=''}=ev;hotWf('cost',5000);setTier(tier);updateCostKPI(tier);
setOriginStatus(`tier ${tier}${task?' · '+task:''}`,'var(--accent-warm)');
spawnThought(`💰 tier ${tier}${task?' · '+task:''}`,{tone:'gold',anchor:'origin'});}
function setTier(tier){
S.tier=tier;$('tier-label').textContent=tier;
const pct=S._tiers[tier]??50;$('tier-fill').style.width=pct+'%';
}
function onDelStart(ev){
const{model='unknown',task='?'}=ev;hotWf('swarm',12000);
const key=modelKey(model);S.modelsUsed.add(key);bumpCounter('s-models',S.modelsUsed.size);
S.active[key]={ts:Date.now(),task,model};S.activeCount++;updateParallel();drawBranchLines();
flowActivate(model,task);
spawnThought(`▸ ${modelShort(model)} · ${task}`,{tone:'violet',anchor:'station',model:key});
setOriginStatus(`→ ${modelShort(model)}`,'var(--role-subagent)');
}
function onDelDone(ev){
const{model='',duration_ms=0}=ev;const key=modelKey(model);const e=S.active[key];if(!e)return;
S.activeCount=Math.max(0,S.activeCount-1);delete S.active[key];updateParallel();drawBranchLines();
flowComplete(model,true,duration_ms);trackDelegation(model);
spawnThought(`✓ ${modelShort(model)} done${duration_ms?' · '+(duration_ms/1000).toFixed(1)+'s':''}`,{tone:'green',anchor:'station',model:key});
if(!S.activeCount)setOriginStatus('validating…','var(--accent-success)');
}
function onDelFail(ev){
const{model='',reason=''}=ev;const key=modelKey(model);if(!S.active[key])return;
S.activeCount=Math.max(0,S.activeCount-1);delete S.active[key];updateParallel();drawBranchLines();
flowComplete(model,false,0);pushFailure(ev);
spawnThought(`✗ ${modelShort(model)} ${reason||'failed'}`,{tone:'red',anchor:'station',model:key});
showNotif('✗ Delegation ล้มเหลว',modelShort(model)+(reason?' · '+reason:''),'delegate_fail');
}
function updateParallel(){
const badge=$('parallel-badge'),count=Math.max(S.activeCount||0,S.parallelCount||0);
bumpCounter('s-par',count);
if(count>0){$('par-count').textContent=count;badge.style.display='inline-flex';}
else badge.style.display='none';
}
function onRoute(ev){
const{model='',rank='',cost_class='',dimension='',score}=ev;
const ri=$('routing-info');if(!ri)return;
ri.style.display='flex';
$('route-text').textContent=`#${rank} → ${modelShort(model)} (${cost_class} class, ${dimension} ${score}pts)`;
}
function setOriginStatus(txt,color){setFlowOriginStatus(txt,color);}
// CHUNK A15: event log ring buffer — keeps last 500 events for search/export
// (DOM caps at 120 rows; ring buffer goes deeper without localStorage cost).
const EVENT_LOG_MAX=500;
let _eventLog=[];
function pushTimeline(ev){
S.eventCount++;bumpCounter('s-events',S.eventCount);
$('event-count').textContent=S.eventCount;
const{type,ts}=ev;const row=mk('div',`ev-row t-${type}${ev.result==='block'?' block':''} new`);
const t=ts?new Date(ts*1000).toLocaleTimeString('en',{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}):'--:--:--';
// B15: data-ts + bookmark star (persisted via awiki-event-bookmarks).
const tsKey=String(ts||'');
const isMarked=_loadEventBookmarks().includes(tsKey);
if(isMarked)row.classList.add('bookmarked');
row.dataset.ts=tsKey;
row.innerHTML=`<span class="ev-time">${t}</span><span class="ev-ic">${evIcon(type,ev.result)}</span><span class="ev-tx">${evText(ev)}</span><span class="ev-star" onclick="event.stopPropagation();toggleEventBookmark('${tsKey}')" style="cursor:pointer;opacity:.6;font-size:var(--fs-2xs)">${isMarked?'⭐':'☆'}</span>`;
// A15: also push to ring buffer for search/export.
_eventLog.push({type:type,ts:ts||0,text:row.textContent,time:t,bookmarked:isMarked});
while(_eventLog.length>EVENT_LOG_MAX)_eventLog.shift();
const tl=$('timeline-list');tl.insertBefore(row,tl.firstChild);
setTimeout(()=>row.classList.remove('new'),800);
  while(tl.children.length>120){const last=tl.lastChild;if(last&&!last.classList.contains('bookmarked'))tl.removeChild(last);else if(last)break;}
}
function filterEvents(){
const v=$('ev-filter').value;
document.querySelectorAll('.ev-row').forEach(r=>{
if(v==='all'){r.style.display='';return;}
if(v==='bookmarked'){r.style.display=r.classList.contains('bookmarked')?'':'none';return;}
const c=r.classList;
const show=(v==='block'&&(c.contains('block')||c.contains('t-delegate_fail')))||
(v==='cost'&&c.contains('t-cost_declare'))||
(v==='delegate'&&(c.contains('t-delegate_start')||c.contains('t-delegate_done')));
r.style.display=show?'':'none';
});
}
// CHUNK A15: text search over event rows (case-insensitive substring match).
let _eventSearchTimer=null;
function eventSearchDebounced(){
if(_eventSearchTimer)clearTimeout(_eventSearchTimer);
_eventSearchTimer=setTimeout(eventSearch,250);
}
function eventSearch(){
const q=($('event-search')&&$('event-search').value||'').trim().toLowerCase();
document.querySelectorAll('.ev-row').forEach(r=>{
if(!q){if(r.style.display==='none'&&!r.classList.contains('search-hidden'))return;r.classList.remove('search-hidden');r.style.display='';return;}
const txt=r.textContent.toLowerCase();
if(txt.indexOf(q)>=0){r.classList.remove('search-hidden');r.style.display='';}
else{r.classList.add('search-hidden');r.style.display='none';}
});
}
// CHUNK B15: event bookmark/pin — persist via awiki-event-bookmarks (array of ts).
const EVENT_BOOKMARKS_KEY='awiki-event-bookmarks';
function _loadEventBookmarks(){try{return JSON.parse(localStorage.getItem(EVENT_BOOKMARKS_KEY)||'[]');}catch(_){return [];}}
function _saveEventBookmarks(arr){try{localStorage.setItem(EVENT_BOOKMARKS_KEY,JSON.stringify(arr));}catch(_){}}
function toggleEventBookmark(ts){
if(!ts)return;
const arr=_loadEventBookmarks();
const idx=arr.indexOf(ts);
if(idx>=0){arr.splice(idx,1);}else{arr.push(ts);}
_saveEventBookmarks(arr);
const row=document.querySelector('.ev-row[data-ts="'+ts+'"]');
if(row){
const isMarked=idx<0;
row.classList.toggle('bookmarked',isMarked);
const star=row.querySelector('.ev-star');
if(star)star.textContent=isMarked?'⭐':'☆';
}
}
// CHUNK C15: export event log as JSON (ring buffer contents + bookmarks).
function exportEventLog(){
if(!_eventLog.length){if(typeof toast==='function')toast('ไม่มี event ให้ส่งออก',true);return;}
const payload={
version:1,
exported_at:new Date().toISOString(),
event_count:_eventLog.length,
events:_eventLog.map(e=>({type:e.type,ts:e.ts,time:e.time,text:e.text,bookmarked:!!e.bookmarked})),
};
const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});
const d=new Date();
const stamp=d.getFullYear()+String(d.getMonth()+1).padStart(2,'0')+String(d.getDate()).padStart(2,'0')+'-'+String(d.getHours()).padStart(2,'0')+String(d.getMinutes()).padStart(2,'0');
_downloadBlob(blob,'awiki-events-'+stamp+'.json');
if(typeof toast==='function')toast('📤 ส่งออก '+_eventLog.length+' events');
}
function evIcon(t,r){return{session_start:'🔌',hook_check:r==='block'?'🔴':'✅',cost_declare:'💰',
delegate_start:'🤖',delegate_done:'✅',delegate_fail:'✗'}[t]||'·';}
function evText(e){const{type,hook='',tool='',result='pass',tier='',model='',task='',reason='',duration_ms=''}=e;
switch(type){
case'session_start':return '<strong>session started</strong>';
case'hook_check':return `<span class="tag">${(hook||'').replace('check_','').replace(/_/g,'-').slice(0,20)}</span>${tool?' → <em>'+tool+'</em>':''} <span class="${result==='block'?'bad':'ok'}">${result}</span>${tier?' <strong>'+tier+'</strong>':''}`;
case'cost_declare':return `cost <strong>${tier||'?'}</strong>${task?' · '+task:''}`;
case'delegate_start':return `→ <strong>${modelShort(model)}</strong> <em>[${task||'?'}]</em>`;
case'delegate_done':return `← <strong>${modelShort(model)}</strong> <span class="ok">done</span>${duration_ms?' · '+(duration_ms/1000).toFixed(1)+'s':''}`;
case'delegate_fail':return `✗ <strong>${modelShort(model)}</strong> <span class="bad">${reason||'failed'}</span>`;
default:return type;}}
function modelKey(m){return(m||'unknown').split('(')[0].trim();}
function modelShort(m){const id=(m||'').toLowerCase();const map=[
['gemini-2.5-flash','Gemini 2.5 Flash'],['gemini','Gemini'],['deepseek-r1','DeepSeek R1'],
['deepseek','DeepSeek'],['llama-3.3-70b','Llama 3.3 70B'],['llama','Llama'],['qwen3-235b','Qwen3 235B'],
['qwen','Qwen'],['claude-haiku','Claude Haiku'],['claude-sonnet','Claude Sonnet'],['gpt-4o-mini','GPT-4o mini'],
['gpt-4o','GPT-4o'],['glm','GLM']];
for(const[k,n]of map)if(id.includes(k))return n;return(m||'?').split('/').pop().slice(0,18);}
function doClear(){fetch('/clear').catch(()=>{});doClearLocal();}
function doClearLocal(){
$('timeline-list').innerHTML='';$('hook-strip').innerHTML='';
_lanes={};S.hookCount=0;S.eventCount=0;S.modelsUsed.clear();S.active={};S.activeCount=0;
$('lanes-body').innerHTML='';$('branch-svg').innerHTML='';
for(const k in _stations){const st=_stations[k];st.active=false;st._emit=false;
st.el.classList.remove('active','done','fail');st.pipeEl.classList.remove('active','return','fail');st.count=0;st.cntEl.textContent='0';}
_particles=[];particleG.innerHTML='';
  bumpCounter('s-hooks',0);bumpCounter('s-models',0);bumpCounter('s-events',0);bumpCounter('s-par',0);bumpCounter('s-fail',0);
  $('parallel-badge').style.display='none';$('event-count').textContent='0';
  S.failCount=0;S.failures=[];S.delegateFree=0;S.delegatePaid=0;
  const el=$('errors-list');if(el)el.innerHTML='';
  const ee=$('errors-empty');if(ee)ee.style.display='flex';
  $('cost-tier-big').textContent='L-1';$('cost-delegations').textContent='0 delegates';$('cost-ratio').textContent='0 free / 0 paid';
  setOriginStatus('watching…','var(--accent-success)');setOriginBusy(false);
}
let _caps={families:{},recommended_by_task:{}};
function toast(msg,err){const t=$('set-toast');t.textContent=msg;t.className='set-toast show'+(err?' err':'');setTimeout(()=>t.className='set-toast',2200);}
function openSettings(){$('settings-backdrop').classList.add('show');$('settings').classList.add('show');loadSettings();_openModalTrap($('settings'));}
function closeSettings(){$('settings-backdrop').classList.remove('show');$('settings').classList.remove('show');_closeModalTrap();}

