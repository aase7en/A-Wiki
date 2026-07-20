// === SUBAGENTS PANE — Observatory: live per-subagent metrics ===
async function subagentsLoad(){
const grid=$('subagents-grid'),empty=$('subagents-empty'),buckets=$('subagents-buckets'),sub=$('subagents-subtitle');
if(!grid)return;
grid.innerHTML='<div style="color:var(--text-tertiary);padding:20px;text-align:center">⏳ กำลังโหลด...</div>';
const winSel=$('subagents-window');
const win=winSel?winSel.value:'86400';
// P2: load alerts in parallel with stats (uses the same window)
subagentsLoadAlerts(win);
try{
const d=await fetch('/api/subagents/stats?since='+encodeURIComponent(win)).then(r=>r.json());
if(d.error)throw new Error(d.error);
const subs=d.by_subagent||{};
const names=Object.keys(subs);
if(!names.length){grid.innerHTML='';empty.style.display='block';buckets.innerHTML='';sub.textContent='ยังไม่มีข้อมูล — เรียก subagent แล้วกลับมาดู';return;}
empty.style.display='none';
const winLbl=win!=='0'?(win>=86400?Math.round(win/86400)+' วัน':win>=3600?Math.round(win/3600)+' ชม.':win+' วิ'):'ทั้งหมด';
sub.textContent=`${d.total_invocations} invocation(s) · ช่วง ${winLbl}`;
grid.innerHTML=names.map(n=>{
const s=subs[n];
const pr=Math.round((s.pass_rate||0)*100);
const prColor=pr>=90?'var(--accent-brand)':pr>=70?'#fbbf24':'#f87171';
const bm=s.best_model||'-';
const bmShort=bm.startsWith('custom:')?bm.split(':').slice(-1)[0]:bm;
const latP50=s.latency_p50_ms||0,latP95=s.latency_p95_ms||0;
const tok=s.tokens_out||0;
return `<div class="glass-card" style="padding:12px;border:1px solid var(--border)">
<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">
<span style="font-family:var(--font-mono);font-size:var(--fs-xs);color:var(--accent-brand);font-weight:700;word-break:break-all">${n}</span>
<span style="font-size:var(--fs-2xs);color:var(--text-tertiary)">${s.count}×</span>
</div>
<div style="display:flex;gap:12px;flex-wrap:wrap;font-size:var(--fs-2xs);color:var(--text-secondary)">
<span>✅ <b style="color:${prColor}">${pr}%</b></span>
<span>⏱️ ${latP50}<span style="color:var(--text-tertiary)">/${latP95}</span>ms</span>
<span>📝 ${tok} tok</span>
</div>
<div style="margin-top:6px;font-size:var(--fs-2xs);color:var(--text-tertiary)">best: <span style="color:#a78bfa">${bmShort}</span>${s.fail?` · ⚠️ ${s.fail} fail`:''}</div>
</div>`;
}).join('');
const bks=d.by_bucket||{};
buckets.innerHTML=Object.keys(bks).length?Object.entries(bks).map(([b,s])=>{
const pr=Math.round((s.pass_rate||0)*100);
const prColor=pr>=90?'var(--accent-brand)':pr>=70?'#fbbf24':'#f87171';
return `<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border)">
<span style="font-family:var(--font-mono);font-size:var(--fs-2xs);color:var(--text-primary)">${b}</span>
<span style="font-size:var(--fs-2xs);color:var(--text-secondary)">${s.count}× · ✅ <b style="color:${prColor}">${pr}%</b> · ⚠️ ${s.fail||0}</span>
</div>`;
}).join(''):'<div style="color:var(--text-tertiary);font-size:var(--fs-2xs);padding:8px">ไม่มีข้อมูล bucket</div>';
}catch(e){grid.innerHTML='<div style="color:var(--accent-danger);padding:20px">⚠️ '+e.message+'</div>';}
}
// === Observatory alerts banner (P2) — pass_rate threshold warnings ===
async function subagentsLoadAlerts(win){
const box=$('observatory-alerts');
if(!box)return;
try{
const d=await fetch('/api/subagents/alerts?since='+encodeURIComponent(win||'86400')).then(r=>r.json());
if(d.error)throw new Error(d.error);
const alerts=d.alerts||[];
if(!alerts.length){box.style.display='none';box.innerHTML='';return;}
box.style.display='block';
box.innerHTML=alerts.map(a=>{
const sev=a.severity==='critical'?'🚨':'⚠️';
const color=a.severity==='critical'?'#f87171':'#fbbf24';
const rate=Math.round((a.pass_rate||0)*100);
const action=a.action?(' · <span style="color:var(--text-tertiary)">'+a.action+'</span>'):'';
return `<div style="display:flex;gap:8px;align-items:flex-start;padding:8px 10px;border-radius:var(--r-md);
background:${a.severity==='critical'?'rgba(248,113,113,.10)':'rgba(251,191,36,.10)'};
border-left:3px solid ${color};margin-bottom:6px;font-size:var(--fs-2xs)">
<span style="font-size:var(--fs-sm);line-height:1">${sev}</span>
<div style="flex:1">
<div style="font-family:var(--font-mono);color:${color};font-weight:700">${a.subagent} · ${rate}% pass (${a.fail}/${a.count} failed)${action}</div>
</div>
</div>`;
}).join('');
}catch(e){box.style.display='none';}
}

let _councilCache=[],_councilPoll=null;
function councilFetchList(){
fetch('/api/council').then(r=>r.json()).then(renderCouncilList).catch(()=>{});
}
function renderCouncilList(d){
const items=(d&&d.councils)||[];_councilCache=items;
const list=$('council-list'),empty=$('council-empty');
list.innerHTML='';
if(!items.length){empty.style.display='block';return;}
empty.style.display='none';
items.forEach(c=>{
const el=mk('div','glass-card council-item');
const q=mk('div','council-q');q.textContent=c.question||'(no question)';
const meta=mk('div','council-meta');
const ok=c.participants_ok||0,tot=c.participants_total||0;
const badge=mk('span','council-badge'+(ok<tot?' warn':''));
badge.textContent=ok+'/'+tot+' ok';
const time=mk('span');time.textContent=c.created_at||'';
meta.append(badge,time);
if(c.has_synthesis){const sy=mk('span','council-badge');sy.textContent='🧠 synthesis';meta.appendChild(sy);}
el.append(q,meta);
el.onclick=()=>councilOpen(c.id);
list.appendChild(el);
});
}
function councilOpen(id){
fetch('/api/council/'+encodeURIComponent(id)).then(r=>r.json()).then(renderCouncilDetail).catch(()=>{});
}
function renderCouncilDetail(c){
if(!c||c.error)return;
$('council-list').style.display='none';$('council-empty').style.display='none';
$('council-detail').style.display='block';
const body=$('council-detail-body');body.innerHTML='';
const h=mk('div','council-q');h.textContent=c.question||'';body.appendChild(h);
(c.participants||[]).forEach(p=>{
const b=mk('div','council-bubble'+(p.status!=='ok'?' fail':''));
const hdr=mk('div','cb-hdr');
hdr.textContent=(p.engine||'?')+' · '+(p.status||'?')+' · '+(p.latency_s!=null?p.latency_s+'s':'');
const txt=mk('div','cb-body');txt.textContent=p.answer||'';
b.append(hdr,txt);body.appendChild(b);
});
if(c.synthesis){
const b=mk('div','council-bubble council-synth');
const hdr=mk('div','cb-hdr');hdr.textContent='🧠 synthesis · '+(c.synthesis.author||'');
const txt=mk('div','cb-body');txt.textContent=c.synthesis.text||'';
b.append(hdr,txt);body.appendChild(b);
}
}
function councilShowList(){
$('council-detail').style.display='none';$('council-list').style.display='block';
if(!_councilCache.length)$('council-empty').style.display='block';
}
function councilStartPoll(){councilFetchList();if(_councilPoll)clearInterval(_councilPoll);_councilPoll=setInterval(councilFetchList,10000);}
function councilStopPoll(){if(_councilPoll){clearInterval(_councilPoll);_councilPoll=null;}}
function pushFailure(ev){
S.failCount++;S.failures.push(ev);bumpCounter('s-fail',S.failCount);
const rail=$('errors-list'),empty=$('errors-empty');if(!rail)return;
if(empty)empty.style.display='none';
const ts=ev.ts?new Date(ev.ts*1000).toLocaleTimeString('en',{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}):'--:--:--';
const tag=ev.type==='delegate_fail'?`✗ ${modelShort(ev.model||'')}`:`🔒 ${(ev.hook||'').replace('check_','').slice(0,18)}`;
const row=mk('div','err-row');
row.innerHTML=`<span class="err-ts">${ts}</span><span class="err-txt">${tag} ${ev.reason||ev.result||''}</span>`;
rail.insertBefore(row,rail.firstChild);
const al=$('aria-live');if(al)al.textContent=`Failure: ${tag}`;
}
function updateCostKPI(tier){
$('cost-tier-big').textContent=tier;$('tier-label').textContent=tier;
const pct=S._tiers[tier]??50;$('tier-fill').style.width=pct+'%';S.tier=tier;
}
function trackDelegation(model){
const id=(model||'').toLowerCase();const f=['gemini','deepseek','llama','qwen','glm'];
const isFree=f.some(x=>id.includes(x));
if(isFree)S.delegateFree++;else S.delegatePaid++;
$('cost-delegations').textContent=(S.delegateFree+S.delegatePaid)+' delegates';
$('cost-ratio').textContent=S.delegateFree+' free / '+S.delegatePaid+' paid';
}
let _lanes={},_lanesRAF=null;
function updateLane(ev){
const model=ev.model||'';if(!model)return;
if(!_lanes[model])_lanes[model]={color:laneColor(model),bars:[],active:null};
const L=_lanes[model];
if(ev.type==='delegate_start')L.active={start:ev.ts,task:ev.task||''};
else if(ev.type==='delegate_done'){if(L.active){L.bars.push({...L.active,end:ev.ts,status:'done',dur:ev.duration_ms});L.active=null;}}
else if(ev.type==='delegate_fail'){if(L.active){L.bars.push({...L.active,end:ev.ts,status:'failed'});L.active=null;}}
drawBranchLines();
if($('timeline-panel').style.display!=='none')renderLanes();
}
function renderLanes(){
if(_lanesRAF){cancelAnimationFrame(_lanesRAF);_lanesRAF=null;}
const body=$('lanes-body'),axis=$('lanes-axis-bar'),empty=$('lanes-empty');if(!body)return;
const now=Date.now()/1000;
const allTs=Object.values(_lanes).flatMap(L=>[...L.bars.map(b=>b.start),...(L.active?[L.active.start]:[])]);
if(!allTs.length){body.innerHTML='';axis.innerHTML='';if(empty)empty.style.display='flex';return;}
if(empty)empty.style.display='none';
const winDur=Math.max(300,now-Math.min(...allTs)+10),winStart=now-winDur;
const pct=ts=>Math.max(0,Math.min(100,(ts-winStart)/winDur*100));
const wpct=(s,e)=>Math.max(.5,pct(e)-pct(s));
axis.innerHTML=[0,1,2,3,4].map(i=>{const t=winStart+winDur*i/4;
const lbl=new Date(t*1000).toLocaleTimeString('en',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
return `<span style="text-align:${i===4?'right':'left'}">${lbl}</span>`;}).join('');
body.innerHTML='';
for(const[model,L]of Object.entries(_lanes)){
const short=model.replace(/\(.*\)/,'').split('/').pop();
const row=mk('div','lane-row'),lbl=mk('div','lane-label');lbl.textContent=short;lbl.title=model;
const track=mk('div','lane-track');
for(const b of L.bars){if(b.end<winStart)continue;
const bar=mk('div',`lane-bar ${b.status}`);
bar.style.cssText=`left:${pct(b.start).toFixed(2)}%;width:${wpct(b.start,b.end).toFixed(2)}%;background:${L.color}`;
bar.title=`${short} — ${b.task} (${((b.end-b.start)*1000)|0}ms)`;track.appendChild(bar);}
if(L.active){const bar=mk('div','lane-bar active');
bar.style.cssText=`left:${pct(L.active.start).toFixed(2)}%;width:${wpct(L.active.start,now).toFixed(2)}%;background:${L.color}`;
bar.title=`${short} — ${L.active.task} (running…)`;track.appendChild(bar);}
row.append(lbl,track);body.appendChild(row);}
if(Object.values(_lanes).some(L=>L.active))_lanesRAF=requestAnimationFrame(()=>setTimeout(renderLanes,500));
}
function drawBranchLines(){
const svg=$('branch-svg');if(!svg)return;
const models=Object.keys(_lanes);if(!models.length){svg.innerHTML='';return;}
const lanesBody=$('lanes-body');
const rows=lanesBody?Array.from(lanesBody.querySelectorAll('.lane-row')):[];
const h=svg.clientHeight||24;
let html='';
rows.forEach((r,i)=>{
const y=(i+0.5)*(h/Math.max(1,rows.length));
const act=r.querySelector('.lane-bar.active');
html+=`<path class="branch-line${act?' active':''}" d="M0 ${h/2} C 30 ${h/2}, 30 ${y}, 80 ${y}"></path>`;
});
svg.innerHTML=html;
}
// T5 DAG shared state. _gData is lazily created in initGraph() AFTER the
// window.vis guard — vis-network comes from a deferred CDN script, so it is
// never defined while this bundle (classic script) executes. A top-level
// `new vis.DataSet()` here killed the whole bundle at boot when the CDN was
// unreachable (and would throw even with network — classic runs before defer).
let _gNet=null,_gData=null;
