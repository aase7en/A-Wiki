// === SKILLS PANE — universal second brain: load/filter/render skill cards ===
let _skillsCache=[],_skillsInv='all',_skillsCat='',_skillsSearchTimer=null;
const SKILL_DOMAIN_COLORS={code:'#60a5fa',debug:'#f87171',design:'#a78bfa','ux-ui':'#f472b6',trader:'#34d399',medical:'#22d3ee',business:'#fbbf24',data:'#5eead4',engineering:'#fb923c',security:'#ef4444','ai-ops':'#818cf8',productivity:'#a3e635',wiki:'#5eead4',iot:'#06b6d4',env:'#84cc16',pharmacy:'#22d3ee',thai:'#fbbf24',logistics:'#fb923c',network:'#06b6d4',media:'#ec4899',document:'#a78bfa',sre:'#f59e0b'};
function skillsDomainColor(d){return SKILL_DOMAIN_COLORS[d]||'var(--accent-brand)';}
function skillsSearchDebounced(){
if(_skillsSearchTimer)clearTimeout(_skillsSearchTimer);
_skillsSearchTimer=setTimeout(skillsLoad,250);
}
function skillsSetInv(inv){
_skillsInv=inv;
document.querySelectorAll('.skills-inv-btn').forEach(b=>b.classList.toggle('active',b.dataset.inv===inv));
skillsRefresh();
}
function skillsSetCat(cat){
_skillsCat=cat||'';
document.querySelectorAll('.skills-cat-btn').forEach(b=>b.classList.toggle('active',b.dataset.cat===cat));
skillsRefresh();
}
function skillsRefresh(){
if(_skillsView==='graph')skillGraphLoad();else skillsLoad();
syncUrlState();
}
// === CHUNK R — AI-powered skill recommender ===
async function recommendSearch(){
const input=$('skills-recommend');
const q=(input&&input.value||'').trim();
const results=$('skills-recommend-results');
if(!results)return;
if(!q){results.style.display='none';results.innerHTML='';return;}
results.style.display='block';
results.innerHTML='<div style="color:var(--text-tertiary);font-size:var(--fs-2xs);padding:4px">⏳ แนะนำ...</div>';
try{
const r=await fetch('/api/skills/recommend?q='+encodeURIComponent(q)+'&limit=5').then(r=>r.json());
if(r.error)throw new Error(r.error);
if(!r.results.length && !(r.walkthroughs||[]).length){
results.innerHTML='<div style="color:var(--text-tertiary);font-size:var(--fs-2xs);padding:4px">😕 ไม่พบ skill หรือ flow ที่ตรง — ลองคำอื่น</div>';
return;
}
// Walkthrough suggestions (shown first — whole flows beat single skills).
const flows=(r.walkthroughs||[]).map(w=>`<div onclick="simWalkthrough('${w.id}')" style="display:flex;gap:8px;align-items:center;padding:6px 8px;border-radius:var(--r-md);background:var(--elev-2);border:1px solid var(--accent-violet);cursor:pointer;margin-bottom:4px">
<span style="font-size:14px;flex-shrink:0">🎬</span>
<span style="flex:1;font-size:var(--fs-xs);color:var(--accent-violet);font-weight:600">${w.title_th}</span>
<span style="font-size:10px;color:var(--text-tertiary);flex-shrink:0">${w.step_count} ขั้น · ⚡${w.score}</span>
</div>`).join('');
const flowHtml=flows?('<div style="font-size:var(--fs-2xs);color:var(--accent-violet);margin-bottom:4px">🎬 แนะนำ flow:</div>'+flows):'';
const modeBadge=r.mode==='semantic'?'<span style="color:var(--accent-violet)" title="ค้นหาด้วย embedding">🧠 semantic</span>':'<span style="color:var(--text-tertiary)" title="ค้นหาด้วยการตรงคำ">📝 substring</span>';
const skillHtml=r.results.length?('<div style="font-size:var(--fs-2xs);color:var(--accent-brand);margin-bottom:4px'+(flows?';margin-top:6px':'')+'">💡 แนะนำ '+r.total_matched+' skills สำหรับ "'+r.query+'" · '+modeBadge+'</div>'+
r.results.map(res=>{
const d=skillsDomainColor((res.domain||[])[0]||'');
return '<div onclick="skillsOpenDetail(\''+res.name+'\')" style="display:flex;gap:8px;align-items:center;padding:6px 8px;border-radius:var(--r-md);background:var(--elev-2);border:1px solid var(--border2);cursor:pointer;margin-bottom:4px">'+
'<span style="font-family:var(--font-mono);font-size:var(--fs-xs);color:'+d+';font-weight:600;min-width:0;flex-shrink:0">'+res.name+'</span>'+
'<span style="flex:1;font-size:var(--fs-2xs);color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+(res.th_description||'')+'</span>'+
'<span style="font-size:10px;color:var(--accent-warn);flex-shrink:0" title="'+res.match_reason+'">⚡'+res.score+'</span>'+
'</div>';
}).join()):'';
results.innerHTML=flowHtml+skillHtml+'<div style="font-size:10px;color:var(--text-tertiary);margin-top:2px">⚡ = คะแนนความตรง · คลิกเพื่อดูรายละเอียด</div>';
}catch(e){
results.innerHTML='<div style="color:var(--accent-danger);font-size:var(--fs-2xs);padding:4px">❌ '+e.message+'</div>';
}
}
// === CHUNK K — Skill dependency graph (vis-network, separate instance from log graph) ===
let _skillsView='list',_skillGraphNet=null,_skillGraphData=null;
function skillsSetView(v){
_skillsView=v;
document.querySelectorAll('.skills-view-btn').forEach(b=>b.classList.toggle('active',b.dataset.view===v));
const grid=$('skills-grid'),gv=$('skills-graph-vis');
if(v==='graph'){
if(grid)grid.style.display='none';
if(gv)gv.style.display='block';
skillGraphLoad();
}else{
if(grid)grid.style.display='grid';
if(gv)gv.style.display='none';
}
}
async function skillGraphLoad(){
const canvas=$('skills-graph-canvas');
if(!canvas)return;
// Check vis-network availability (CDN may not load offline)
if(typeof vis==='undefined'||!vis.Network){
$('skills-graph-unavailable').style.display='flex';
$('skills-graph-canvas').style.display='none';
return;
}
$('skills-graph-unavailable').style.display='none';
$('skills-graph-canvas').style.display='block';
const stats=$('skills-graph-stats');
if(stats)stats.textContent='⏳ กำลังโหลด graph...';
try{
const qs=skillsBuildQs();
const r=await fetch('/api/skills/graph?all=0'+(qs?('&'+qs):'')).then(r=>r.json());
if(r.error)throw new Error(r.error);
_skillGraphData=r;
const nodes=new vis.DataSet(r.nodes.map(n=>({
id:n.id,label:n.label,
title:(n.title||n.id)+'\n📊 '+(Array.isArray(n.domain)?n.domain.join(','):n.domain)+' · 🔄 '+n.phase,
color:{background:n.color,border:n.color,highlight:{background:n.color,border:'#fff'}},
font:{color:'#f1f5f9',size:13},
})));
const edges=new vis.DataSet(r.edges.map(e=>({
from:e.from,to:e.to,id:e.id,
width:Math.min(e.weight,5),
color:{color:'rgba(148,163,184,'+(0.2+e.weight*0.15)+')',highlight:'#5eead4'},
smooth:{type:'continuous'},
})));
const data={nodes,edges};
const options={
physics:{enabled:true,solver:'barnesHut',barnesHut:{gravitationalConstant:-3000,centralGravity:0.3,springLength:120,springConstant:0.04,damping:0.4}},
interaction:{hover:true,tooltipDelay:50,zoomView:true,dragView:true},
nodes:{shape:'dot',size:14,borderWidth:2},
edges:{arrows:{to:{enabled:false}}},
};
if(_skillGraphNet){_skillGraphNet.destroy();}
_skillGraphNet=new vis.Network(canvas,data,options);
_skillGraphNet.on('click',function(params){
if(params.nodes.length>0){skillsOpenDetail(params.nodes[0]);}
});
if(stats)stats.textContent=`🧬 ${r.stats.nodes} skills · ${r.stats.edges} ความสัมพันธ์`;
// CHUNK HH: surface circular dependencies as a warning banner.
_loadCyclesCheck();
}catch(e){
if(stats)stats.textContent='❌ '+e.message;
}
}
async function _loadCyclesCheck(){
const banner=$('skills-cycles-banner');if(!banner)return;
try{
const c=await fetch('/api/skills/cycles').then(r=>r.json());
if(c.error||!c.has_cycle){banner.style.display='none';return;}
const list=(c.cycles||[]).slice(0,5).map(cy=>cy.join(' → ')).join('<br>');
banner.innerHTML=`⚠️ พบ ${c.count} circular dependency<br><small style="color:var(--text-tertiary)">${list}</small>`;
banner.style.display='block';
showNotif('⚠️ พบ circular dependency',c.count+' รอบใน skill graph','cycle');
announce('พบ '+c.count+' circular dependency ใน skill graph');
}catch(_){banner.style.display='none';}
}
// === CHUNK U — Graph export (SVG + PNG) ===
function graphExportPNG(){
if(!_skillGraphNet){toast('graph ยังไม่โหลด','err');return;}
// vis-network injects <canvas> inside the container div.
const canvas=$('skills-graph-canvas').querySelector('canvas');
if(!canvas){toast('ไม่พบ canvas','err');return;}
try{
canvas.toBlob(function(blob){
if(!blob){toast('❌ export ล้มเหลว','err');return;}
_downloadBlob(blob,'awiki-skill-graph.png');
toast('📥 ดาวน์โหลด PNG แล้ว');
},'image/png');
}catch(e){toast('❌ '+e.message,'err');}
}
function graphExportSVG(){
if(!_skillGraphNet||!_skillGraphData){toast('graph ยังไม่โหลด','err');return;}
// Build SVG from node positions (post-physics) + edge data.
const positions=_skillGraphNet.getPositions();
const nodes=_skillGraphData.nodes;
const edges=_skillGraphData.edges;
if(!nodes.length){toast('ไม่มี node','err');return;}
// Compute bounding box from positions.
let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
for(const id in positions){const p=positions[id];minX=Math.min(minX,p.x);maxX=Math.max(maxX,p.x);minY=Math.min(minY,p.y);maxY=Math.max(maxY,p.y);}
const pad=60;
const w=(maxX-minX)+pad*2,h=(maxY-minY)+pad*2;
const scale=1;
// Edges first (behind nodes).
let edgeSvg='';
for(const e of edges){
const from=positions[e.from],to=positions[e.to];
if(!from||!to)continue;
const x1=(from.x-minX+pad).toFixed(1),y1=(from.y-minY+pad).toFixed(1);
const x2=(to.x-minX+pad).toFixed(1),y2=(to.y-minY+pad).toFixed(1);
const op=Math.min(0.6,0.2+e.weight*0.1).toFixed(2);
edgeSvg+=`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#3a3a6a" stroke-width="${Math.min(e.weight,4)}" opacity="${op}"/>`;
}
// Nodes.
let nodeSvg='';
for(const n of nodes){
const p=positions[n.id];if(!p)continue;
const cx=(p.x-minX+pad).toFixed(1),cy=(p.y-minY+pad).toFixed(1);
const lbl=(n.label||n.id).replace(/&/g,'&amp;').replace(/</g,'&lt;');
nodeSvg+=`<circle cx="${cx}" cy="${cy}" r="8" fill="${n.color}" stroke="${n.color}" stroke-width="2"/>`;
nodeSvg+=`<text x="${cx}" y="${parseInt(cy)+22}" text-anchor="middle" font-family="monospace" font-size="9" fill="#cbd5e1">${lbl}</text>`;
}
const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><rect width="100%" height="100%" fill="#06060d"/>${edgeSvg}${nodeSvg}<text x="${pad}" y="24" font-family="monospace" font-size="14" fill="#5eead4">🧬 Skill Dependency Graph — ${nodes.length} nodes, ${edges.length} edges</text></svg>`;
const blob=new Blob([svg],{type:'image/svg+xml'});
_downloadBlob(blob,'awiki-skill-graph.svg');
toast('📥 ดาวน์โหลด SVG แล้ว');
}
function skillsBuildQs(){
const qs=new URLSearchParams();
const agent=$('skills-agent-filter').value;if(agent&&agent!=='all')qs.set('agent',agent);
const dom=$('skills-domain-filter').value;if(dom)qs.set('domain',dom);
const q=$('skills-search').value.trim();if(q)qs.set('q',q);
if(_skillsInv!=='all')qs.set('invocation',_skillsInv);
if(_skillsCat)qs.set('category',_skillsCat);
const inst=$('skills-installed-only');if(inst&&inst.checked)qs.set('installed','1');
return qs.toString();
}
async function skillsLoad(){
const grid=$('skills-grid'),stats=$('skills-stats'),empty=$('skills-empty');if(!grid)return;
grid.innerHTML='<div style="grid-column:1/-1;text-align:center;color:var(--text-tertiary);padding:30px">⏳ กำลังโหลด...</div>';
try{
const qs=skillsBuildQs();
// CHUNK B10: TTL cache (60s) keyed by query string — avoids re-fetching the
// ~250-skill list every time the user switches back to the Skills tab.
// Invalidated on SSE registry_update and inline skill edits.
const cacheKey='skills:'+qs;
const cached=_cacheGet(cacheKey);
if(cached){
  _skillsCache=cached.skills||[];
  _applySkillsResponse(cached);
  return;
}
// CHUNK MM: record non-empty search query to history.
const qVal=$('skills-search')&&$('skills-search').value.trim();
if(qVal)recordSearchQuery(qVal);
const r=await fetch('/api/skills'+(qs?('?'+qs):'')).then(r=>r.json());
if(r.error)throw new Error(r.error);
// CHUNK B10: cache the response for 60s — keyed by query string.
_cacheSet(cacheKey,r,60);
_applySkillsResponse(r);
}catch(e){grid.innerHTML='<div style="grid-column:1/-1;color:var(--accent-danger);padding:20px">⚠️ '+e.message+'</div>';}
}
// CHUNK B10: apply a skills list response to the DOM (shared between cache hit and fresh fetch).
function _applySkillsResponse(r){
const grid=$('skills-grid'),stats=$('skills-stats'),empty=$('skills-empty');
if(!grid)return;
_skillsCache=r.skills||[];
// Populate agent dropdown on first load
if($('skills-agent-filter').options.length<=1&&(r.agents||[]).length){
(r.agents||[]).forEach(a=>{if(a==='all')return;const o=document.createElement('option');o.value=a;o.textContent='🤖 '+a.charAt(0).toUpperCase()+a.slice(1);$('skills-agent-filter').appendChild(o);});
}
// Populate domain dropdown
const curDom=$('skills-domain-filter').value;
const stats_by_domain=r.stats&&r.stats.by_domain||{};
if($('skills-domain-filter').options.length<=1){
Object.keys(stats_by_domain).forEach(d=>{const o=document.createElement('option');o.value=d;o.textContent=`${d} (${stats_by_domain[d]})`;$('skills-domain-filter').appendChild(o);});
}
// Render (apply client-side sort if requested — CHUNK FF)
if(!_skillsCache.length){grid.innerHTML='';empty.style.display='block';}
else{empty.style.display='none';grid.innerHTML=skillsSortedView().map(skillsRenderCard).join('');}
// Stats line
const st=r.stats||{};
const agentLbl=$('skills-agent-filter').value;
const agentTxt=agentLbl==='all'?'ทุก agent':agentLbl;
stats.innerHTML=`<b style="color:var(--accent-brand)">${r.count}</b> skills สำหรับ <b>${agentTxt}</b> · 🤖 ${st.by_invocation?.auto||0} auto · 👆 ${st.by_invocation?.manual||0} manual · 🔬 ${st.by_category?.subagent||0} subagents · 🇹🇭 ${st.has_thai||0} มีคำอธิบายไทย`;
// CHUNK RR: notify if many critical-health skills loaded.
const crit=_skillsCache.filter(s=>s.health&&s.health.level==='critical');
if(crit.length>=3)showNotif('🩺 Skills สุขภาพวิกฤต',crit.length+' skills มี health < 30 — ไปดูได้ที่ Coverage tab','low_health');
}
// CHUNK C9/E9: keyboard handler for skill cards.
// Enter/Space = open detail, ArrowDown/Up = move between cards, Home/End = first/last.
function _skillCardKeydown(e,name){
if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();skillsOpenDetail(name);return;}
if(e.key!=='ArrowDown'&&e.key!=='ArrowUp'&&e.key!=='ArrowRight'&&e.key!=='ArrowLeft'&&e.key!=='Home'&&e.key!=='End')return;
e.preventDefault();
const grid=$('skills-grid');if(!grid)return;
const cards=Array.from(grid.querySelectorAll('.skill-card'));
const cur=cards.indexOf(e.currentTarget);
if(cur<0)return;
let nxt=cur;
if(e.key==='ArrowDown'||e.key==='ArrowRight')nxt=Math.min(cur+1,cards.length-1);
else if(e.key==='ArrowUp'||e.key==='ArrowLeft')nxt=Math.max(cur-1,0);
else if(e.key==='Home')nxt=0;
else if(e.key==='End')nxt=cards.length-1;
if(nxt!==cur&&cards[nxt]){cards[nxt].focus();cards[nxt].scrollIntoView({block:'nearest',behavior:'smooth'});}
}
function skillsRenderCard(s){
const inv=s.invocation||'manual';
const invIcon=inv==='auto'?'🤖':inv==='both'?'🔀':'👆';
const hasThai=s.th_description?'has-thai':'';
const desc=s.th_description||'<i style="color:var(--text-disabled)">ยังไม่มีคำอธิบายไทย</i>';
const domains=(s.domain||[]).map(d=>`<span class="skill-tag" style="border-color:${skillsDomainColor(d)};color:${skillsDomainColor(d)}">${d}</span>`).join('');
const when=s.when_to_use?`<div class="skill-card-when">💡 ${s.when_to_use}</div>`:'';
const instBadge=s.installed===false?`<span class="skill-card-inst catalog" title="catalog-only (SKILL.md ไม่ได้ติดตั้งบนเครื่องนี้)">📦 catalog</span>`:`<span class="skill-card-inst installed" title="ติดตั้งแล้วบนเครื่องนี้">✅ ติดตั้ง</span>`;
// CHUNK FF: health badge from s.health (score/level/missing).
const healthBadge=s.health?skillsHealthBadge(s.health):'';
// CHUNK WW: pinned badge + toggle (syncs via public registry).
const isPinned=!!s.pinned;
const pinBadge=isPinned?'<span class="skill-tag" style="border-color:var(--accent-warm);color:var(--accent-warm)">📌 pinned</span>':'';
return `<div class="skill-card ${hasThai}" onclick="skillsOpenDetail('${s.name}')" onkeydown="_skillCardKeydown(event,'${s.name}')" role="button" tabindex="0" aria-label="${s.name}: ${(s.th_description||s.name).replace(/"/g,'&quot;').slice(0,80)}" style="--sk-color:${skillsDomainColor((s.domain||[])[0]||'')}${isPinned?';box-shadow:0 0 0 2px var(--accent-warm)':''}">
<div class="skill-card-head"><span class="skill-card-name">${s.name}</span><span class="skill-card-inv ${inv}">${invIcon} ${inv}</span></div>
<div class="skill-card-desc">${desc}</div>${when}
<div class="skill-card-tags">${pinBadge}${domains}${instBadge}${healthBadge}</div>
<div class="skill-card-copy" onclick="event.stopPropagation();copyInvocation('${s.invocation_hint||s.name}','${s.name}')" title="คัดลอกคำสั่ง" role="button" tabindex="0" aria-label="คัดลอกคำสั่งของ ${s.name}">📋</div>
<div class="skill-card-copy" onclick="event.stopPropagation();togglePin('${s.name}')" title="${isPinned?'เลิกปักหมุด':'ปักหมุด (sync ผ่าน git registry)'}" role="button" tabindex="0" aria-label="${isPinned?'เลิกปักหมุด':'ปักหมุด'} ${s.name}" style="right:36px">${isPinned?'⭐':'☆'}</div>
<input type="checkbox" class="skill-card-compare" onclick="event.stopPropagation();toggleCompare('${s.name}')" title="เพิ่ม/ลบ จากการเปรียบเทียบ" aria-label="เปรียบเทียบ ${s.name}" style="position:absolute;top:6px;right:62px;width:16px;height:16px;cursor:pointer;accent-color:var(--accent-brand)">
</div>`;
}
function skillsHealthBadge(h){
if(!h||typeof h.score!=='number')return '';
const lvl=h.level||'ok';
const colors={critical:'#f87171',weak:'#fbbf24',ok:'#86efac',good:'#34d399'};
const labels={critical:'🔴 วิกฤต',weak:'🟠 อ่อน',ok:'🟢 พอใช้',good:'💚 ดี'};
const c=colors[lvl]||colors.ok,lbl=labels[lvl]||labels.ok;
return `<span class="skill-tag" style="border-color:${c};color:${c}" title="Health ${h.score}/100 · ขาด ${(h.missing||[]).length} field">${lbl} ${h.score}</span>`;
}
// CHUNK FF: client-side sort over the rendered cache.
function skillsSortedView(){
const sel=$('skills-sort');const mode=sel?sel.value:'';
// CHUNK WW: client-side pinned-only filter (applied before sort).
const pinFilter=$('skills-pinned-only');
let base=_skillsCache;
if(pinFilter&&pinFilter.checked)base=_skillsCache.filter(s=>s.pinned);
if(!mode)return base;
const arr=base.slice();
if(mode==='health-asc')arr.sort((a,b)=>((a.health&&a.health.score)||0)-((b.health&&b.health.score)||0));
else if(mode==='health-desc')arr.sort((a,b)=>((b.health&&b.health.score)||0)-((a.health&&a.health.score)||0));
else if(mode==='name-asc')arr.sort((a,b)=>(a.name||'').localeCompare(b.name||''));
// CHUNK WW: pinned first, then by name.
else if(mode==='pinned-first')arr.sort((a,b)=>(!!b.pinned===!!a.pinned?0:(!!b.pinned?1:-1))||(a.name||'').localeCompare(b.name||''));
return arr;
}
// CHUNK WW — cross-device pin toggle (writes pinned bool to registry via API).
async function togglePin(name){
const s=_skillsCache.find(x=>x.name===name);
const newVal=!(s&&s.pinned);
try{
const r=await fetch('/api/skills/'+encodeURIComponent(name)+'/edit',{
method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({field:'pinned',value:newVal?'true':'false'})
}).then(r=>r.json());
if(r.error&&!r.ok)throw new Error(r.error);
// CHUNK B10: invalidate skills+coverage caches so other tabs see the pin change.
for(const k in _ttlCache){if(k.startsWith('skills:'))delete _ttlCache[k];}
_cacheInvalidate('coverage');
// Optimistic update of cache + re-render.
if(s)s.pinned=newVal;
skillsApplySort();
toast(newVal?'⭐ ปักหมุดแล้ว (sync ผ่าน git registry — public)':'เลิกปักหมุดแล้ว');
}catch(e){toast('ปักหมุดไม่สำเร็จ: '+e.message,true);}
}
function skillsApplySort(){
// Re-render the grid from the cache (no refetch needed).
const grid=$('skills-grid'),empty=$('skills-empty');
if(!_skillsCache.length){return;}
empty.style.display='none';
grid.innerHTML=skillsSortedView().map(skillsRenderCard).join('');
syncUrlState();
}
// === CHUNK II — Filter Presets ===
const PRESETS_KEY='awiki-filter-presets';
function _currentFilterState(){
return{
agent:$('skills-agent-filter').value||'all',
domain:$('skills-domain-filter').value||'',
inv:_skillsInv||'all',
cat:_skillsCat||'',
installed:($('skills-installed-only')&&$('skills-installed-only').checked)?'1':'',
sort:($('skills-sort')||{}).value||''
};
}
function _loadPresets(){try{return JSON.parse(localStorage.getItem(PRESETS_KEY)||'[]');}catch(_){return[];}}
function _savePresets(arr){try{localStorage.setItem(PRESETS_KEY,JSON.stringify(arr));}catch(_){}}
function renderPresetDropdown(){
const sel=$('skills-preset');if(!sel)return;
const presets=_loadPresets();
const cur=sel.value;
sel.innerHTML='<option value="">📋 Presets</option>'+
presets.map((p,i)=>`<option value="${i}">${p.name}</option>`).join('')+
(presets.length?'<option value="__clear">🗑 ล้างทั้งหมด</option>':'');
if(cur)sel.value=cur;
}
function savePreset(){
const presets=_loadPresets();
const name=prompt('ตั้งชื่อ preset:','preset '+(presets.length+1));
if(!name)return;
const state=_currentFilterState();
// Dedupe by name (overwrite).
const idx=presets.findIndex(p=>p.name===name);
const entry={name,state};
if(idx>=0)presets[idx]=entry;else presets.push(entry);
if(presets.length>10)presets.shift();
_savePresets(presets);
renderPresetDropdown();
toast('⭐ บันทึก preset "'+name+'"');
}
function applyPresetSelect(){
const sel=$('skills-preset');const v=sel.value;if(!v)return;
if(v==='__clear'){
if(confirm('ล้าง preset ทั้งหมด?')){_savePresets([]);renderPresetDropdown();toast('🗑 ล้าง preset แล้ว');}
else{sel.value='';}
return;
}
const presets=_loadPresets();const p=presets[parseInt(v,10)];
if(!p){return;}
applyPresetState(p.state);
sel.value='';
toast('📋 โหลด preset "'+p.name+'"');
}
function applyPresetState(st){
if(!st)return;
$('skills-agent-filter').value=st.agent||'all';
$('skills-domain-filter').value=st.domain||'';
_skillsInv=st.inv||'all';
document.querySelectorAll('.skills-inv-btn').forEach(b=>b.classList.toggle('active',b.dataset.inv===_skillsInv));
_skillsCat=st.cat||'';
document.querySelectorAll('.skills-cat-btn').forEach(b=>b.classList.toggle('active',b.dataset.cat===_skillsCat));
const inst=$('skills-installed-only');if(inst)inst.checked=st.installed==='1';
const srt=$('skills-sort');if(srt)srt.value=st.sort||'';
skillsRefresh();
}
// Initialize preset dropdown on skills load.
function _initPresetDropdown(){renderPresetDropdown();}
// === CHUNK JJ — Multi-Agent Matrix CSV export ===
async function exportMatrixCSV(){
try{
const r=await fetch('/api/skills/matrix').then(r=>r.json());
if(r.error)throw new Error(r.error);
const agents=r.agents||[];
const skills=r.skills||[];
const matrix=r.matrix||{};
// CSV: header = skill, agent1, agent2, ... ; 1/0 per cell.
const header=['skill'].concat(agents);
const rows=skills.map(name=>{
const row=matrix[name]||{};
return [name].concat(agents.map(a=>row[a]?'1':'0'));
});
// Quote skill names (may contain commas in theory).
const csv=[header, ...rows].map(r=>r.map((c,i)=>{
const s=String(c);
return i===0?'"'+s.replace(/"/g,'""')+'"':s;
}).join(',')).join('\r\n');
const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});
_downloadBlob(blob,'awiki-skill-agent-matrix.csv');
toast('📥 ดาวน์โหลด CSV แล้ว ('+skills.length+' skills × '+agents.length+' agents)');
}catch(e){toast('❌ '+e.message,'err');}
}
// === CHUNK KK — Co-occurrence mining (graph from real opens log) ===
let _coOccurMode=false;
function _mineCoOccurrence(){
// Mine awiki-skill-opens: pairs opened within 60s window = co-occur.
const opens=_lsGet(OPENS_KEY,[]);
if(opens.length<5)return null;
// Sort by ts ascending.
opens.sort((a,b)=>(a.ts||0)-(b.ts||0));
const pairCounts={}; // "A|B" -> count (A<B canonical order)
const nodeCounts={};
for(let i=0;i<opens.length;i++){
const ni=opens[i].name;if(!ni)continue;
nodeCounts[ni]=(nodeCounts[ni]||0)+1;
for(let j=i+1;j<opens.length;j++){
const dt=(opens[j].ts||0)-(opens[i].ts||0);
if(dt>60000)break; // outside 60s window
if(dt<0)continue; // skip backwards (shouldn't happen post-sort)
const nj=opens[j].name;if(!nj||nj===ni)continue;
const key=ni<nj?ni+'|'+nj:nj+'|'+ni;
pairCounts[key]=(pairCounts[key]||0)+1;
}
}
// Build nodes + edges (only pairs with weight>=2).
const nodeNames=new Set();
const edges=[];
Object.entries(pairCounts).forEach(([k,w])=>{
if(w<2)return;
const [a,b]=k.split('|');
nodeNames.add(a);nodeNames.add(b);
edges.push({from:a,to:b,weight:w,id:a+'->'+b});
});
const nodes=Array.from(nodeNames).map(n=>({
id:n,label:n,domain:[],phase:'none',color:'#a78bfa',installed:false,_cooccur:nodeCounts[n]||0
}));
return {nodes,edges,stats:{nodes:nodes.length,edges:edges.length,opens:opens.length}};
}
// CHUNK E11: smart suggestions — client-side scoring (frequency × recency × co-occurrence).
// Pure JS, no server call. Returns ranked skills the user is likely to want next.
// Excludes skills opened in the last 24h (user just saw them).
// Returns [] if insufficient telemetry (<5 opens total).
function smartSuggestions(limit){
  limit=limit||5;
  const opens=_lsGet(OPENS_KEY,[]);
  if(opens.length<5)return [];   // min telemetry fallback
  const now=Date.now();
  const cutoff30d=now-30*24*60*60*1000;
  const cutoff24h=now-24*60*60*1000;
  // frequency: count opens in last 30d per skill.
  const freq={};
  let maxFreq=0;
  opens.forEach(o=>{
    if((o.ts||0)<cutoff30d)return;
    freq[o.name]=(freq[o.name]||0)+1;
    if(freq[o.name]>maxFreq)maxFreq=freq[o.name];
  });
  // recency: days since last open per skill.
  const lastOpen={};
  opens.forEach(o=>{
    const t=o.ts||0;
    if(!lastOpen[o.name]||t>lastOpen[o.name])lastOpen[o.name]=t;
  });
  // co-occurrence: reuse _mineCoOccurrence edges.
  const co=_mineCoOccurrence();
  const coEdges=co?(co.edges||[]):[];
  // Find the most-recently-opened skill name (last entry) for co-occurrence lookup.
  const lastSkill=opens.length?(opens[opens.length-1].name||''):'';
  const cooccurForLast={};
  coEdges.forEach(e=>{
    if(e.from===lastSkill)cooccurForLast[e.to]=(cooccurForLast[e.to]||0)+e.weight;
    if(e.to===lastSkill)cooccurForLast[e.from]=(cooccurForLast[e.from]||0)+e.weight;
  });
  let maxCooccur=0;
  Object.values(cooccurForLast).forEach(v=>{if(v>maxCooccur)maxCooccur=v;});
  // Score every candidate skill.
  const candidates=Object.keys(freq).map(name=>{
    // Exclude skills opened in last 24h.
    if((lastOpen[name]||0)>cutoff24h)return null;
    const f=maxFreq?(freq[name]/maxFreq):0;
    const daysSince=(now-(lastOpen[name]||0))/(24*60*60*1000);
    const recencyFactor=Math.max(0,1-daysSince/30);
    const c=maxCooccur?((cooccurForLast[name]||0)/maxCooccur):0;
    const score=f*40+recencyFactor*30+c*30;
    return {name,score:Math.round(score),reason:{
      frequency:freq[name],
      days_since_open:Math.round(daysSince),
      cooccur_with_last:cooccurForLast[name]||0,
    }};
  }).filter(Boolean);
  candidates.sort((a,b)=>b.score-a.score);
  return candidates.slice(0,limit);
}
function toggleCoOccurGraph(){
_coOccurMode=!_coOccurMode;
const btn=$('graph-cooccur-toggle');
const stats=$('skills-graph-stats');
if(btn)btn.style.background=_coOccurMode?'var(--elev-3)':'';
if(btn)btn.textContent=_coOccurMode?'🔗 phase/domain':'📊 ใช้ร่วมกัน';
if(!_coOccurMode){
// Restore default graph.
skillGraphLoad();
return;
}
// Build co-occurrence graph.
const canvas=$('skills-graph-canvas');
if(typeof vis==='undefined'||!vis.Network){toast('vis-network ไม่พร้อม','err');return;}
const data=_mineCoOccurrence();
if(!data){
if(stats)stats.textContent='ยังไม่มีข้อมูลเพียงพอ (ต้องการอย่างน้อย 5 opens)';
toast('ยังไม่มีข้อมูล opens เพียงพอ','err');
return;
}
_skillGraphData=data;
const visNodes=new vis.DataSet(data.nodes.map(n=>({
id:n.id,label:n.label,title:(n._cooccur||0)+' opens',shape:'dot',size:10+Math.min((n._cooccur||0)*2,20),
color:{background:n.color,border:n.color,highlight:{background:n.color,border:n.color}}
})));
const visEdges=new vis.DataSet(data.edges.map(e=>({
from:e.from,to:e.to,width:Math.min(e.weight,8),title:'co-occur ×'+e.weight,
color:{color:'rgba(167,139,250,.5)',highlight:'rgba(167,139,250,.9)'}
})));
const options={physics:{stabilization:{iterations:80}},interaction:{hover:true}};
if(_skillGraphNet){_skillGraphNet.destroy();}
_skillGraphNet=new vis.Network(canvas,{nodes:visNodes,edges:visEdges},options);
_skillGraphNet.on('click',function(p){if(p.nodes.length>0)skillsOpenDetail(p.nodes[0]);});
if(stats)stats.textContent=`📊 ใช้ร่วมกัน: ${data.stats.nodes} skills · ${data.stats.edges} คู่ · ${data.stats.opens} opens`;
}
async function skillsOpenDetail(name){
const drawer=$('skills-detail'),bd=$('skills-detail-backdrop');
drawer.style.transform='translateX(0)';bd.style.display='block';
drawer.innerHTML='<div style="padding:30px;text-align:center;color:var(--text-tertiary)">⏳ กำลังโหลด...</div>';
try{
const s=await fetch('/api/skills/'+encodeURIComponent(name)).then(r=>r.json());
if(s.error)throw new Error(s.error);
// Track recently opened skill for discovery bar.
recordRecentSkill(s.name);
const inv=s.invocation||'manual';
const invIcon=inv==='auto'?'🤖 โหลดอัตโนมัติ':inv==='both'?'🔀 อัตโนมัติ/แมนนวล':'👆 เรียกเอง';
const domains=(s.domain||[]).map(d=>`<span class="skill-tag" style="border-color:${skillsDomainColor(d)};color:${skillsDomainColor(d)}">${d}</span>`).join('');
	const examples=(s.examples||[]).map(ex=>`<div class="skill-example"><div class="skill-example-scenario">📌 ${ex.scenario}</div><div class="skill-example-how">→ ${ex.how}</div></div>`).join('')||'<p style="color:var(--text-disabled);font-size:var(--fs-xs)">ยังไม่มีตัวอย่าง</p>';
	const steps=(s.process_steps||[]).map((st,i)=>`<div class="skill-process-step"><span class="skill-process-step-num">${i+1}</span>${st}</div>`).join('');
	const simBtn=steps?`<button class="skill-sim-btn" onclick="simulateSkill('${s.name}')">🎬 จำลองขั้นตอน (${s.process_steps.length} ขั้น)</button>`:'';
	const instBadge=s.installed?`<span class="skill-tag" style="border-color:var(--accent-success);color:var(--accent-success)">✅ ติดตั้ง</span>`:`<span class="skill-tag" style="border-color:var(--border2);color:var(--text-tertiary)">📦 catalog</span>`;
	const copyBtn=`<button onclick="copyInvocation('${(s.invocation_hint||s.name).replace(/'/g,"\\'")}','${s.name}')" style="background:var(--elev-2);border:1px solid var(--border2);color:var(--text-secondary);border-radius:var(--r-md);padding:6px 10px;cursor:pointer;font-size:var(--fs-2xs);min-height:32px" title="คัดลอกคำสั่งเรียก">📋 ${s.invocation_hint||s.name}</button>`;
	const related=(s.related||[]).map(r=>`<div class="skill-related-item" onclick="skillsOpenDetail('${r.name}')" style="display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:var(--r-md);cursor:pointer;border:1px solid var(--border2);background:var(--elev-2)">
<span style="font-size:14px">${r.installed?'✅':'📦'}</span>
<div style="flex:1;min-width:0">
<div style="font-size:var(--fs-2xs);font-weight:600;color:var(--text-primary);font-family:var(--font-mono)">${r.name}</div>
<div style="font-size:10px;color:var(--text-tertiary);display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden">${r.th_description||'(ยังไม่มีคำอธิบาย)'}</div>
</div></div>`).join('')||'<p style="color:var(--text-disabled);font-size:var(--fs-xs)">ไม่พบ skill ที่เกี่ยวข้อง</p>';
	drawer.innerHTML=`
<div class="skill-detail-hdr">
<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
<div><div class="skill-detail-name">${s.name}</div>
<div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:4px">${domains}<span class="skill-tag">🔄 ${s.lifecycle_phase||'none'}</span><span class="skill-tag">${invIcon}</span>${instBadge}</div></div>
<div style="display:flex;gap:2px">
<button onclick="copySkillLink('${s.name}')" title="คัดลอกลิงก์ skill" style="background:transparent;border:none;color:var(--text-tertiary);font-size:var(--fs-md);cursor:pointer;min-width:32px;min-height:32px">🔗</button>
<button onclick="skillsCloseDetail()" style="background:transparent;border:none;color:var(--text-tertiary);font-size:var(--fs-lg);cursor:pointer;min-width:32px;min-height:32px">✕</button>
</div>
</div></div>
<div class="skill-detail-body">
<div class="skill-detail-section"><h5>📝 คำอธิบาย</h5><p>${s.th_description||'<i style="color:var(--text-disabled)">ยังไม่มีคำอธิบายไทย</i>'}</p></div>
<div class="skill-detail-section"><h5>📋 เรียกใช้</h5>${copyBtn}<div id="skill-run-area" style="margin-top:8px"></div></div>
${s.when_to_use?`<div class="skill-detail-section"><h5>💡 ใช้เมื่อไหร่</h5><p style="color:var(--accent-warn)">${s.when_to_use}</p></div>`:''}
<div class="skill-detail-section"><h5>📌 ตัวอย่างการใช้งาน</h5>${examples}</div>
${steps?`<div class="skill-detail-section"><h5>🎬 ขั้นตอน (สำหรับ simulation)</h5>${steps}${simBtn}</div>`:''}
<div class="skill-detail-section"><h5>🔗 Skills ที่เกี่ยวข้อง</h5><div style="display:flex;flex-direction:column;gap:4px">${related}</div></div>
${(function(){
const h=s.history||{};
const hasVer=h.version&&h.version!=='';
const hasGit=h.last_commit_date||h.commit_count;
// CHUNK SS: first_seen (when the skill was first added to the repo).
const fs=h.first_seen||'';
const fsLine=fs?` · 📅 เพิ่มเมื่อ ${fs}`:'';
// "ใหม่" badge if first_seen is within 30 days.
const isNew=fs&&((Date.now()-new Date(fs+'T00:00:00Z').getTime())<30*24*60*60*1000);
const newBadge=isNew?'<span class="skill-tag" style="border-color:var(--accent-warm);color:var(--accent-warm)">🆕 ใหม่</span>':'';
if(!hasVer&&!hasGit&&!fs)return '';
const verBadge=hasVer?`<span class="skill-tag" style="border-color:var(--accent-violet);color:var(--accent-violet)">v${h.version}</span>`:'<span style="font-size:var(--fs-2xs);color:var(--text-disabled)">ยังไม่กำหนดเวอร์ชัน</span>';
const gitInfo=(hasGit||fs)?`<span style="font-size:var(--fs-2xs);color:var(--text-tertiary)">แก้ล่าสุด ${h.last_commit_date||'-'}${h.commit_count?(' · '+h.commit_count+' commits'):''}${h.last_commit_hash?(' · '+h.last_commit_hash):''}${fsLine}</span>`:'';
const changelogBtn=hasGit?`<button class="set-btn sm" onclick="loadSkillChangelog('${s.name}')" style="padding:3px 8px;font-size:var(--fs-2xs);margin-top:6px" title="ดูประวัติการแก้ไข 5 commits ล่าสุด">📜 ดู changelog</button><div id="changelog-area" style="margin-top:6px"></div>`:'';
return `<div class="skill-detail-section"><h5>📋 เวอร์ชัน</h5><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">${verBadge}${newBadge}${gitInfo}</div>${changelogBtn}</div>`;
})()}
<div class="skill-detail-section"><h5>🔍 รายละเอียดเทคนิค</h5>
<p style="font-size:var(--fs-2xs);color:var(--text-tertiary);font-family:var(--font-mono)">path: ${s.path||'-'}<br>status: ${s.status||'-'} · source: ${s.source||'-'}<br>agents: ${(s.agents||[]).join(', ')||'-'}</p></div>
</div>`;
}catch(e){drawer.innerHTML='<div style="padding:30px;color:var(--accent-danger)">⚠️ '+e.message+'</div>';}
// After render: check if this skill's script is in the run allowlist.
skillRunCheck(s);
}
// === RUN-THIS-SKILL ===
let _runAllowlist=null;
async function _loadRunAllowlist(){
  if(_runAllowlist!==null)return _runAllowlist;
  try{
    const r=await fetch('/api/run/allowlist').then(r=>r.json());
    _runAllowlist=r;
  }catch(e){_runAllowlist={enabled:false,scripts:{}};}
  return _runAllowlist;
}
async function skillRunCheck(skill){
  const area=$('skill-run-area');if(!area)return;
  const al=await _loadRunAllowlist();
  if(!al.enabled){
    area.innerHTML='<p style="font-size:var(--fs-2xs);color:var(--text-disabled);margin:4px 0">▶ รันจาก dashboard ปิดอยู่ (เปิดด้วย <code style="color:var(--text-tertiary)">AWIKI_DASHBOARD_ALLOW_RUN=1</code>)</p>';
    return;
  }
  // Match skill's invocation_hint or path against allowlist keys.
  const hint=(skill.invocation_hint||'').toLowerCase();
  const path=(skill.path||'').toLowerCase();
  let matchedScript=null;
  for(const scriptPath of Object.keys(al.scripts)){
    const sp=scriptPath.toLowerCase();
    if(hint.includes(sp)||path.includes(sp.replace('scripts/',''))){
      matchedScript=scriptPath;break;
    }
  }
  if(!matchedScript){
    area.innerHTML='<p style="font-size:var(--fs-2xs);color:var(--text-disabled);margin:4px 0">script นี้ไม่อยู่ใน allowlist (รันไม่ได้จาก dashboard)</p>';
    return;
  }
  const meta=al.scripts[matchedScript];
  const needsArgs=meta.needs_args;
  area.innerHTML=`
    <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:4px">
      ${needsArgs?'<input id="skill-run-args" type="text" placeholder="args (เช่น MQTT)" style="flex:1;min-width:120px;padding:6px 10px;border-radius:var(--r-md);border:1px solid var(--border2);background:var(--elev-2);color:var(--text-primary);font-size:var(--fs-2xs);min-height:32px">':''}
      <button onclick="skillRunExecute('${matchedScript.replace(/'/g,"\\'")}',${needsArgs})" style="background:var(--accent-success,#34d399);border:none;color:#06060d;border-radius:var(--r-md);padding:6px 14px;cursor:pointer;font-size:var(--fs-2xs);font-weight:600;min-height:32px">▶ รัน</button>
    </div>
    <div id="skill-run-output" style="margin-top:8px"></div>
  `;
}
async function skillRunExecute(script,needsArgs){
  const out=$('skill-run-output');if(!out)return;
  let args=[];
  if(needsArgs){
    const inp=$('skill-run-args');
    const raw=(inp&&inp.value||'').trim();
    if(raw)args=raw.split(/\s+/);
  }
  out.innerHTML='<div style="font-size:var(--fs-2xs);color:var(--text-tertiary);padding:8px">⏳ กำลังรัน...</div>';
  try{
    const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({script,args})}).then(r=>r.json());
    if(r.error){out.innerHTML=`<div style="font-size:var(--fs-2xs);color:var(--accent-danger);padding:8px;border:1px solid var(--accent-danger);border-radius:var(--r-md)">❌ ${r.error}</div>`;return;}
    const okColor=r.ok?'var(--accent-success,#34d399)':'var(--accent-warn,#fbbf24)';
    const stdoutEsc=(r.stdout||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').slice(0,4000);
    const stderrEsc=(r.stderr||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').slice(0,2000);
    out.innerHTML=`
      <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);margin-bottom:4px">
        <span style="color:${okColor};font-weight:600">${r.ok?'✅':'⚠️'}</span>
        exit=${r.exit_code} · ${r.duration_ms}ms
        <button onclick="_copyToClipboard(${JSON.stringify(r.stdout||'')},'คัดลอกผลลัพธ์แล้ว')" style="background:transparent;border:1px solid var(--border2);color:var(--text-tertiary);border-radius:var(--r-sm);padding:2px 6px;cursor:pointer;font-size:10px;margin-left:6px">📋 copy</button>
      </div>
      ${stdoutEsc?`<pre style="background:var(--elev-0,#06060d);color:var(--accent-success,#34d399);padding:8px;border-radius:var(--r-md);font-size:var(--fs-2xs);overflow-x:auto;max-height:300px;white-space:pre-wrap">${stdoutEsc}</pre>`:''}
      ${stderrEsc?`<pre style="background:var(--elev-0,#06060d);color:var(--accent-warn,#fbbf24);padding:8px;border-radius:var(--r-md);font-size:var(--fs-2xs);overflow-x:auto;max-height:150px;white-space:pre-wrap;margin-top:4px">${stderrEsc}</pre>`:''}
    `;
  }catch(e){
    out.innerHTML=`<div style="font-size:var(--fs-2xs);color:var(--accent-danger);padding:8px">❌ ${e.message}</div>`;
  }
}
// === DISCOVERY: recently used + skill-of-the-day ===
const RECENT_KEY='awiki-recent-skills';
const SOTD_KEY='awiki-sotd';
const OPENS_KEY='awiki-skill-opens';
const OPENS_MAX=200;
const TRENDING_DAYS_KEY='awiki-trending-days';
let _trendingDays=_lsGet(TRENDING_DAYS_KEY,7);
function _lsGet(key,def){try{return JSON.parse(localStorage.getItem(key)||'null')||def;}catch(e){return def;}}
function _lsSet(key,val){try{localStorage.setItem(key,JSON.stringify(val));}catch(e){}}
function recordRecentSkill(name){
  let recent=_lsGet(RECENT_KEY,[]);
  recent=[name,...recent.filter(n=>n!==name)].slice(0,8);
  _lsSet(RECENT_KEY,recent);
  // CHUNK Q — also append to full open log (FIFO, max 200).
  let opens=_lsGet(OPENS_KEY,[]);
  opens.push({name:name,ts:Date.now()});
  if(opens.length>OPENS_MAX)opens=opens.slice(opens.length-OPENS_MAX);
  _lsSet(OPENS_KEY,opens);
  renderDiscoveryBar();
}
function trendingSkills(days=7,limit=5){
  const opens=_lsGet(OPENS_KEY,[]);
  if(!opens.length)return [];
  const cutoff=Date.now()-days*24*60*60*1000;
  const recent=opens.filter(o=>o.ts>=cutoff);
  if(!recent.length)return [];
  // Count by name.
  const counts={};
  recent.forEach(o=>{counts[o.name]=(counts[o.name]||0)+1;});
  return Object.entries(counts)
    .sort((a,b)=>b[1]-a[1])
    .slice(0,limit)
    .map(([name,count])=>({name:name,count:count}));
}
function renderDiscoveryBar(){
  const rc=$('recent-chips');if(!rc)return;
  const recent=_lsGet(RECENT_KEY,[]);
  const trending=trendingSkills(_trendingDays,5);
  let html='';
  // Trending section (only if there's data).
  if(trending.length){
    const daysLabel=_trendingDays===30?'30ว':'7ว';
    html+='<span style="font-size:var(--fs-2xs);color:var(--accent-warm);margin-right:2px">📈 Trending ('+daysLabel+'):</span>';
    html+=trending.map(t=>`<span class="skill-tag" style="cursor:pointer;font-size:10px;border-color:var(--accent-warn);color:var(--accent-warn)" onclick="skillsOpenDetail('${t.name}')" title="เปิด ${t.count} ครั้งใน ${_trendingDays} วัน">${t.name} <b>${t.count}</b></span>`).join('');
    // Toggle button 7ว|30ว
    html+=`<span class="skill-tag" style="cursor:pointer;font-size:9px;border-color:var(--border2);color:var(--text-tertiary);padding:1px 5px" onclick="setTrendingDays(${_trendingDays===7?30:7})" title="สลับหน้าต่างเวลา">${_trendingDays===7?'→30ว':'→7ว'}</span>`;
  }
  // Recent section.
  if(recent.length){
    if(html)html+='<span style="width:8px"></span>';
    html+='<span style="font-size:var(--fs-2xs);color:var(--text-tertiary);margin-right:2px">🕘 ล่าสุด:</span>';
    html+=recent.slice(0,5).map(n=>`<span class="skill-tag" style="cursor:pointer;font-size:10px;border-color:var(--border2)" onclick="skillsOpenDetail('${n}')">${n}</span>`).join('');
  }
  rc.innerHTML=html;
}
function setTrendingDays(days){
_trendingDays=days;
_lsSet(TRENDING_DAYS_KEY,days);
renderDiscoveryBar();
}
// === CHUNK MM — Search history (recent query chips) ===
const SEARCH_HISTORY_KEY='awiki-search-history';
const SEARCH_HISTORY_MAX=20;
const SEARCH_HISTORY_TTL_MS=30*24*60*60*1000; // 30 days
function _loadSearchHistory(){
let arr=_lsGet(SEARCH_HISTORY_KEY,[]);
const cutoff=Date.now()-SEARCH_HISTORY_TTL_MS;
arr=arr.filter(e=>e&&e.q&&(e.ts||0)>cutoff);
return arr;
}
function _saveSearchHistory(arr){
try{localStorage.setItem(SEARCH_HISTORY_KEY,JSON.stringify(arr.slice(-SEARCH_HISTORY_MAX)));}catch(_){}
}
function recordSearchQuery(q){
q=(q||'').trim();if(q.length<2)return;
let arr=_loadSearchHistory();
// Dedupe by q (keep latest ts).
arr=arr.filter(e=>e.q!==q);
arr.push({q:q,ts:Date.now()});
if(arr.length>SEARCH_HISTORY_MAX)arr=arr.slice(arr.length-SEARCH_HISTORY_MAX);
_saveSearchHistory(arr);
}
function renderSearchHistoryChips(){
const box=$('skills-search-history');if(!box)return;
const arr=_loadSearchHistory();
// Show only when input is empty + has history + input focused (or was focused).
const inp=$('skills-search');
const show=arr.length>0&&inp&&inp.value.trim()==='';
if(!show){box.style.display='none';return;}
box.style.display='flex';
const recent=arr.slice(-8).reverse(); // latest first
box.innerHTML='<span style="font-size:var(--fs-2xs);color:var(--text-tertiary);margin-right:4px">ค้นล่าสุด:</span>'+
recent.map(e=>`<button class="chat-quick-btn" onclick="useHistoryQuery('${e.q.replace(/'/g,"\\'")}')"
  style="padding:3px 10px;font-size:var(--fs-2xs);border:1px solid var(--border2);background:var(--elev-2);color:var(--text-secondary);border-radius:var(--r-sm);cursor:pointer;min-height:26px"
  title="${e.q}">${e.q.length>20?e.q.slice(0,20)+'…':e.q}</button>`).join('')+
'<span onclick="clearSearchHistory()" style="font-size:var(--fs-2xs);color:var(--text-tertiary);cursor:pointer;margin-left:4px" title="ล้างประวัติ">🗑</span>';
}
function useHistoryQuery(q){
const inp=$('skills-search');if(!inp)return;
inp.value=q;
skillsLoad();
inp.focus();
}
function clearSearchHistory(){
_saveSearchHistory([]);
renderSearchHistoryChips();
toast('🗑 ล้างประวัติการค้นหา');
}
// Focus/blur handlers to show/hide history chips.
document.addEventListener('focusin',function(e){
if(e.target&&e.target.id==='skills-search'){renderSearchHistoryChips();}
});
document.addEventListener('focusout',function(e){
if(e.target&&e.target.id==='skills-search'){
// Delay so chip click registers before hide.
setTimeout(()=>{
const box=$('skills-search-history');
if(box)box.style.display='none';
},200);
}
});
function sotdPick(allSkills){
  // Deterministic by date seed — same skill all day, changes at midnight.
  const today=new Date().toISOString().slice(0,10);
  const stored=_lsGet(SOTD_KEY,{});
  if(stored.date===today&&stored.name){return stored.name;}
  // Pick from skills that have th_description + process_steps (richest view).
  const pool=allSkills.filter(s=>s.th_description&&s.process_steps);
  if(!pool.length)return null;
  // Simple date-seed hash → index.
  let h=0;for(const c of today)h=(h*31+c.charCodeAt(0))>>>0;
  const pick=pool[h%pool.length].name;
  _lsSet(SOTD_KEY,{date:today,name:pick});
  return pick;
}
function sotdOpen(){
  const sotd=_lsGet(SOTD_KEY,{});
  if(sotd.name)skillsOpenDetail(sotd.name);
}
async function loadSotd(){
  // Fetch all skills once (no filter) to pick from.
  try{
    const r=await fetch('/api/skills?limit=500').then(r=>r.json());
    const name=sotdPick(r.skills||[]);
    const chip=$('sotd-chip');
    if(!chip||!name)return;
    chip.style.display='inline-flex';
    chip.innerHTML=`<span style="font-size:var(--fs-2xs);background:var(--elev-2);border:1px solid var(--accent-brand,rgba(120,170,255,.4));color:var(--accent-brand);border-radius:var(--r-md);padding:4px 10px">🎲 Skill แห่งวัน: <b>${name}</b></span>`;
  }catch(e){}
}
function skillsCloseDetail(){
$('skills-detail').style.transform='translateX(100%)';
$('skills-detail-backdrop').style.display='none';
}
// === CHUNK AA — Lazy changelog loader ===
async function loadSkillChangelog(name){
const area=$('changelog-area');
if(!area)return;
if(area.innerHTML){area.innerHTML='';return;} // toggle off
area.innerHTML='<div style="color:var(--text-tertiary);font-size:var(--fs-2xs)">⏳ กำลังโหลด...</div>';
try{
const s=await fetch('/api/skills/'+encodeURIComponent(name)+'?changelog=1').then(r=>r.json());
const cl=(s.history&&s.history.changelog)||[];
if(!cl.length){area.innerHTML='<div style="font-size:var(--fs-2xs);color:var(--text-disabled)">ไม่มีประวัติ</div>';return;}
area.innerHTML=cl.map(c=>`<div style="display:flex;gap:6px;padding:4px 0;border-bottom:1px solid var(--border);font-size:var(--fs-2xs)">
<span style="color:var(--text-tertiary);white-space:nowrap;flex-shrink:0">${c.date}</span>
<span style="color:var(--accent-violet);font-family:var(--font-mono);flex-shrink:0">${c.hash}</span>
<span style="color:var(--text-secondary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c.message}</span>
</div>`).join('');
}catch(e){area.innerHTML='<div style="font-size:var(--fs-2xs);color:var(--accent-danger)">❌ '+e.message+'</div>';}
}

// === CHUNK O — Skill Comparison Mode ===
let _compareSet=new Set();
const COMPARE_MAX=3;
function toggleCompare(name){
if(_compareSet.has(name)){
_compareSet.delete(name);
}else{
if(_compareSet.size>=COMPARE_MAX){
toast(`เปรียบเทียบได้สูงสุด ${COMPARE_MAX} skills`,'err');
// Uncheck the checkbox that was just clicked.
document.querySelectorAll('.skill-card').forEach(card=>{
if(card.querySelector('.skill-card-name')&&card.querySelector('.skill-card-name').textContent===name){
const cb=card.querySelector('.skill-card-compare');if(cb)cb.checked=false;
}
});
return;
}
_compareSet.add(name);
}
updateCompareBar();
// Sync all checkboxes (in case of re-render).
document.querySelectorAll('.skill-card-compare').forEach(cb=>{
const card=cb.closest('.skill-card');
const nm=card&&card.querySelector('.skill-card-name')?card.querySelector('.skill-card-name').textContent:'';
cb.checked=_compareSet.has(nm);
});
}
function updateCompareBar(){
const bar=$('compare-bar');
if(_compareSet.size===0){bar.style.display='none';return;}
bar.style.display='flex';
$('compare-count').textContent=_compareSet.size;
$('compare-names').innerHTML=Array.from(_compareSet).map(n=>
`<span class="skill-tag" style="cursor:pointer;border-color:var(--accent-brand);color:var(--accent-brand)" onclick="toggleCompare('${n}');updateCompareBar();skillsLoad()">${n} ✕</span>`
).join('');
}
function clearCompare(){
_compareSet.clear();
updateCompareBar();
document.querySelectorAll('.skill-card-compare').forEach(cb=>cb.checked=false);
}
async function openCompareModal(){
if(_compareSet.size<2){toast('เลือกอย่างน้อย 2 skills เพื่อเปรียบเทียบ','err');return;}
const names=Array.from(_compareSet);
const content=$('compare-content');
content.innerHTML='<div style="text-align:center;color:var(--text-tertiary);padding:30px">⏳ กำลังโหลด...</div>';
$('compare-backdrop').style.display='block';
$('compare-modal').style.display='block';
try{
const skills=await Promise.all(names.map(n=>fetch('/api/skills/'+encodeURIComponent(n)).then(r=>r.json())));
if(skills.some(s=>s.error))throw new Error('บาง skill โหลดไม่ได้');
renderCompareTable(skills);
// Save last comparison.
_lsSet('awiki-compare-last',names);
}catch(e){
content.innerHTML=`<div style="color:var(--accent-danger);padding:20px">❌ ${e.message}</div>`;
}
_openModalTrap($('compare-modal'));
}
function closeCompareModal(){
$('compare-backdrop').style.display='none';
$('compare-modal').style.display='none';
_closeModalTrap();
}
function _cmpCell(val,defaultValue,isUnique,isEmpty){
// Diff highlight: empty=red bg, unique=green bg, same=normal.
let bg='';
if(isEmpty)bg='background:rgba(248,113,113,0.12);';
else if(isUnique)bg='background:rgba(52,211,153,0.12);';
if(val===undefined||val===null||val==='')return `<td style="padding:6px 8px;color:var(--text-disabled);font-style:italic;${bg}">${defaultValue||'—'}</td>`;
if(Array.isArray(val))return `<td style="padding:6px 8px;color:var(--text-secondary);${bg}">${val.length?val.join(', '):(defaultValue||'—')}</td>`;
return `<td style="padding:6px 8px;color:var(--text-secondary);${bg}">${val}</td>`;
}
function renderCompareTable(skills){
const fields=[
{label:'📝 คำอธิบายไทย',get:s=>s.th_description||''},
{label:'💡 ใช้เมื่อไหร่',get:s=>s.when_to_use||''},
{label:'📋 invocation_hint',get:s=>s.invocation_hint||''},
{label:'🔄 lifecycle_phase',get:s=>s.lifecycle_phase||'none'},
{label:'📂 domain',get:s=>Array.isArray(s.domain)?s.domain.join(', '):(s.domain||'')},
{label:'🤖 invocation',get:s=>s.invocation||'manual'},
{label:'#️⃣ process_steps',get:s=>(s.process_steps||[]).length+' ขั้น'},
{label:'📦 ติดตั้ง',get:s=>s.installed?'✅':'📦 catalog'},
{label:'#️⃣ version',get:s=>s.version||''},
];
const headerCells=skills.map(s=>`<th style="padding:8px;border-bottom:2px solid var(--border2);text-align:left;font-family:var(--font-mono);color:${skillsDomainColor((s.domain||[])[0]||'')};cursor:pointer" onclick="skillsOpenDetail('${s.name}');closeCompareModal()">${s.name}</th>`).join('');
const rows=fields.map(f=>{
const values=skills.map(s=>f.get(s));
// Count occurrences of each value (normalized to string).
const counts={};
values.forEach(v=>{const k=String(v);counts[k]=(counts[k]||0)+1;});
const cells=values.map((v,i)=>{
const k=String(v);
const isUnique=counts[k]===1;
const isEmpty=(v===undefined||v===null||v==='');
return _cmpCell(v,'—',isUnique,isEmpty);
}).join('');
return `<tr><td style="padding:6px 8px;font-weight:600;color:var(--text-tertiary);font-size:var(--fs-2xs);white-space:nowrap;border-right:1px solid var(--border)">${f.label}</td>${cells}</tr>`;
}).join('');
$('compare-content').innerHTML=`<table style="width:100%;border-collapse:collapse;font-size:var(--fs-xs)"><thead><tr><th style="padding:8px;border-bottom:2px solid var(--border2)"></th>${headerCells}</tr></thead><tbody>${rows}</tbody></table><div style="display:flex;gap:12px;margin-top:8px;font-size:var(--fs-2xs);color:var(--text-tertiary)"><span><span style="display:inline-block;width:10px;height:10px;background:rgba(52,211,153,0.3);border-radius:2px;vertical-align:middle"></span> unique</span><span><span style="display:inline-block;width:10px;height:10px;background:rgba(248,113,113,0.3);border-radius:2px;vertical-align:middle"></span> ขาด</span></div><p style="margin:8px 0 0;font-size:var(--fs-2xs);color:var(--text-tertiary)">💡 คลิกชื่อ skill เพื่อดูรายละเอียดเต็ม</p>`;
}
// Copy a deep-link URL for a skill (?skill=<name>) to clipboard.
function copySkillLink(name){
  const url=new URL(window.location.href);
  url.searchParams.set('skill',name);
  // Drop flow= to avoid conflicting deep-links.
  url.searchParams.delete('flow');
  const link=url.toString();
  _copyToClipboard(link,'คัดลอกลิงก์ skill แล้ว');
}
// Copy a deep-link URL for a walkthrough flow (?flow=<id>).
function copyFlowLink(flowId){
  const url=new URL(window.location.href);
  url.searchParams.set('flow',flowId);
  url.searchParams.delete('skill');
  const link=url.toString();
  _copyToClipboard(link,'คัดลอกลิงก์ flow แล้ว');
}
// Shared clipboard helper with execCommand fallback.
function _copyToClipboard(text,successMsg){
  try{
    if(navigator.clipboard&&navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(()=>_flashToast(successMsg)).catch(()=>_copyFallback(text,successMsg));
    }else{_copyFallback(text,successMsg);}
  }catch(e){_copyFallback(text,successMsg);}
}
function _copyFallback(text,msg){
  const ta=document.createElement('textarea');ta.value=text;ta.style.position='fixed';ta.style.opacity='0';
  document.body.appendChild(ta);ta.select();
  try{document.execCommand('copy');_flashToast(msg);}catch(e){console.warn('copy fail',e);}
  document.body.removeChild(ta);
}
function _flashToast(msg){
  let t=$('awiki-toast');
  if(!t){t=document.createElement('div');t.id='awiki-toast';t.style.cssText='position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--elev-2,#14142a);color:var(--text-primary);padding:8px 16px;border-radius:var(--r-md);border:1px solid var(--border2,#26265a);font-size:var(--fs-xs);z-index:9999;opacity:0;transition:opacity .2s';document.body.appendChild(t);}
  t.textContent=msg;t.style.opacity='1';
  clearTimeout(t._timer);t._timer=setTimeout(()=>{t.style.opacity='0';},2000);
}
// === SKILL SIMULATION — particle walkthrough of process_steps ===
const SIM_ICONS=['📥','🔍','🛠️','✅','📋','🚀','🔄','⚙️','🧪','📊'];
let _simSteps=[],_simIdx=-1,_simTimer=null,_simCurrentName=null;

