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
    // CHUNK D11: per-key Clear button (with confirm) reclaims quota granularly.
    return '<div style="display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid var(--border);gap:6px"><span style="font-family:var(--font-mono);color:var(--text-secondary);flex:1;overflow:hidden;text-overflow:ellipsis">'+k+'</span><span style="color:var(--text-tertiary);font-size:var(--fs-2xs);white-space:nowrap">'+(bytes/1024).toFixed(1)+'KB</span><button onclick="clearBackupKey(\''+k+'\')" style="background:transparent;border:none;color:var(--accent-danger);cursor:pointer;font-size:var(--fs-2xs);padding:0 4px" title="ล้าง key นี้">🗑</button></div>';
  }).join('');
  list.innerHTML=rows||'<div style="color:var(--text-tertiary);padding:8px">ไม่มี awiki-* keys</div>';
  const meter=$('backup-usage-meter');
  if(meter){
    const pct=(totalBytes/(5*1024*1024)*100).toFixed(1);
    const color=pct<60?'var(--accent-success)':pct<85?'var(--accent-warm)':'var(--accent-danger)';
    meter.innerHTML='<div style="font-size:var(--fs-2xs);color:var(--text-tertiary);margin-bottom:3px">localStorage: '+(totalBytes/1024).toFixed(1)+'KB / 5MB ('+pct+'%) · '+names.length+' keys</div><div style="height:6px;background:var(--elev-3);border-radius:3px;overflow:hidden"><div style="height:100%;width:'+Math.min(100,pct)+'%;background:'+color+';transition:width .3s"></div></div>';
  }
}
function clearBackupKey(k){
  if(!confirm('ล้าง key "'+k+'" ออกจาก localStorage?'))return;
  try{localStorage.removeItem(k);}catch(_){}
  toast('🗑 ล้าง '+k+' แล้ว');
  loadBackupPane();
}
// CHUNK B11: import backup — validate schema, show selective restore modal.
// User picks which keys to restore via checkboxes; only checked keys are
// written. Rejects payloads missing version or with unsupported version.
let _pendingBackup=null;
function _validateBackupPayload(j){
  if(!j||typeof j!=='object')return 'ไม่ใช่ JSON object';
  if(j.version!==1)return 'schema version ไม่รองรับ (ต้องเป็น 1)';
  if(!j.keys||typeof j.keys!=='object')return 'ไม่มี keys field';
  return null;
}
function importBackup(ev){
  const f=ev.target.files[0];if(!f)return;
  const rd=new FileReader();
  rd.onload=()=>{
    try{
      const j=JSON.parse(rd.result);
      const err=_validateBackupPayload(j);
      if(err){toast('❌ '+err,true);return;}
      _pendingBackup=j;
      _showRestoreModal(j);
    }catch(e){toast('❌ JSON parse ไม่ได้: '+e.message,true);}
  };
  rd.readAsText(f);
  ev.target.value='';
}
function _showRestoreModal(j){
  const names=Object.keys(j.keys).sort();
  if(!names.length){toast('ไฟล์ backup ว่าง',true);return;}
  // Build modal in-place (reuses the keybind-modal pattern).
  let m=document.getElementById('backup-restore-modal');
  if(!m){
    m=document.createElement('div');
    m.id='backup-restore-modal';
    m.style.cssText='position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:var(--elev-1);border:1px solid var(--border2);border-radius:var(--r-lg);padding:20px 24px;z-index:460;max-width:480px;width:90vw;max-height:80vh;overflow-y:auto;box-shadow:var(--shadow-lg)';
    document.body.appendChild(m);
  }
  const rows=names.map((k,i)=>{
    const cur=localStorage.getItem(k);
    const curNote=cur!==null?'<span style="color:var(--accent-warn);font-size:10px"> (จะทับ)</span>':'<span style="color:var(--accent-success);font-size:10px"> (ใหม่)</span>';
    return '<label style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:var(--fs-xs)"><input type="checkbox" data-backup-key="'+k+'" checked style="cursor:pointer;accent-color:var(--accent-brand)"><span style="font-family:var(--font-mono);color:var(--text-secondary)">'+k+'</span>'+curNote+'</label>';
  }).join('');
  m.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><h3 style="margin:0;font-size:var(--fs-md);color:var(--accent-brand)">📥 Restore Backup</h3><button onclick="document.getElementById(\'backup-restore-modal\').style.display=\'none\'" style="background:transparent;border:none;color:var(--text-tertiary);font-size:18px;cursor:pointer">✕</button></div><p style="margin:0 0 10px;font-size:var(--fs-2xs);color:var(--text-tertiary)">เลือก keys ที่จะกู้คืน — เฉพาะที่ติ๊กเท่านั้นที่จะถูกเขียนทับ</p><div style="max-height:300px;overflow-y:auto;margin-bottom:12px">'+rows+'</div><div style="display:flex;gap:6px"><button class="set-btn sm" onclick="_applySelectedBackup()" style="background:var(--accent-success);color:var(--elev-0);font-weight:600">✅ กู้คืนที่เลือก</button><button class="set-btn sm" onclick="document.getElementById(\'backup-restore-modal\').style.display=\'none\'" style="color:var(--text-tertiary)">ยกเลิก</button></div>';
  m.style.display='block';
}
function _applySelectedBackup(){
  if(!_pendingBackup){return;}
  const m=document.getElementById('backup-restore-modal');
  const boxes=m?m.querySelectorAll('input[data-backup-key]:checked'):[];
  const selected=new Set(Array.from(boxes).map(b=>b.dataset.backupKey));
  let applied=0;
  selected.forEach(k=>{
    const val=_pendingBackup.keys[k];
    try{localStorage.setItem(k,JSON.stringify(val));applied++;}catch(_){}
  });
  if(m)m.style.display='none';
  _pendingBackup=null;
  toast('✅ กู้คืน '+applied+' keys เรียบร้อย — รีเฟรช dashboard เพื่อเห็นผล');
  const st=$('backup-status');
  if(st)st.textContent='📥 กู้คืน '+applied+' keys เมื่อสักครู่';
  loadBackupPane();
}
// CHUNK C11: auto-backup — snapshot localStorage every 7 days.
// Stored in awiki-auto-backups (max 3, FIFO). Checked at boot via
// _maybeAutoBackup(). Skipped from export whitelist (BACKUP_SKIP_KEYS).
const AUTO_BACKUP_KEY='awiki-auto-backups';
const AUTO_BACKUP_LAST='awiki-last-backup';
const AUTO_BACKUP_MAX=3;
const AUTO_BACKUP_INTERVAL_MS=7*24*60*60*1000; // 7 days
function autoBackup(){
  const keys=_collectBackupKeys();
  const snap={version:1,saved_at:new Date().toISOString(),keys:keys};
  let snaps=[];
  try{snaps=JSON.parse(localStorage.getItem(AUTO_BACKUP_KEY)||'[]');}catch(_){snaps=[];}
  snaps.push(snap);
  // FIFO cap: keep the 3 most recent (slice from the end).
  while(snaps.length>AUTO_BACKUP_MAX)snaps.shift();
  try{
    localStorage.setItem(AUTO_BACKUP_KEY,JSON.stringify(snaps));
    localStorage.setItem(AUTO_BACKUP_LAST,String(Date.now()));
  }catch(_){/* quota — drop oldest and retry once */}
}
function _maybeAutoBackup(){
  let last=0;
  try{last=parseInt(localStorage.getItem(AUTO_BACKUP_LAST)||'0',10)||0;}catch(_){last=0;}
  if(Date.now()-last>AUTO_BACKUP_INTERVAL_MS)autoBackup();
}
// CHUNK A13: Help pane content — rendered in JS (not inline HTML) to keep
// the HTML budget small. Covers v8-v12 features + basics + tips + shortcuts.
const DASHBOARD_VERSION='v13.0.0';
function renderHelpContent(){
  const pane=document.getElementById('pane-help');
  if(!pane)return;
  pane.innerHTML=''
    +'<div class="set-note">📖 คู่มือ Dashboard — version '+DASHBOARD_VERSION+'</div>'
    +'<div style="margin-top:10px;display:flex;flex-direction:column;gap:10px">'
    // Basics section
    +'<div class="glass-card" style="padding:12px">'
    +'<div style="font-weight:600;color:var(--accent-brand);margin-bottom:6px">📖 พื้นฐาน</div>'
    +'<ul style="margin:0;padding-left:18px;font-size:var(--fs-xs);color:var(--text-secondary);line-height:1.6">'
    +'<li><b>🌊 Flow</b> — จุดกำเนิด (🧠 Senior Critic) ส่งข้อมูลไหลทางท่อไปยังแต่ละ model</li>'
    +'<li><b>🏊 Timeline</b> — lanes แตกแขนงตามเวลา; เขียว=สำเร็จ แดง=ล้มเหลว</li>'
    +'<li><b>🔗 Graph</b> — knowledge-graph ของ session/task/agent</li>'
    +'<li><b>🧩 Skills</b> — catalog ทั้งหมด + คำอธิบายไทย + simulation; filter ตาม agent</li>'
    +'<li><b>Event Log</b> (ขวา) — timeline เหตุการณ์สด · <b>cost tier</b> L-1 ถูก → L4 แพง</li>'
    +'</ul></div>'
    // What's new in v10-v12
    +'<div class="glass-card" style="padding:12px;border-color:var(--accent-violet)"'
    +'><div style="font-weight:600;color:var(--accent-violet);margin-bottom:6px">✨ ใหม่ใน v10-v12</div>'
    +'<ul style="margin:0;padding-left:18px;font-size:var(--fs-xs);color:var(--text-secondary);line-height:1.6">'
    +'<li><b>💾 Backup</b> (v11) — Settings → 💾 Backup: export/import preferences, auto-backup 7 วัน, usage meter</li>'
    +'<li><b>🎨 Theme Editor</b> (v12) — Settings → 🎨 Theme: ปรับสี 8 tokens, live preview, preset save</li>'
    +'<li><b>📱 Mobile Responsive</b> (v12) — view-toggle-bar scroll, skills-grid 2-up, modals 95vw บนมือถือ</li>'
    +'<li><b>🔮 Smart Suggestions</b> (v11) — discovery bar แนะนำ skills จาก frequency × recency × co-occurrence</li>'
    +'<li><b>⚡ Performance</b> (v10) — CDN defer, TTL cache (skills 60s / coverage 30s), lazy view init</li>'
    +'<li><b>🧪 Playwright Tests</b> (v10) — browser smoke tests (optional: npm i && npx playwright install chromium)</li>'
    +'</ul></div>'
    // Tips
    +'<div class="glass-card" style="padding:12px">'
    +'<div style="font-weight:600;color:var(--accent-warm);margin-bottom:6px">💡 Tips</div>'
    +'<ul style="margin:0;padding-left:18px;font-size:var(--fs-xs);color:var(--text-secondary);line-height:1.6">'
    +'<li>กด <kbd style="background:var(--elev-2);padding:1px 6px;border-radius:3px;border:1px solid var(--border2)">?</kbd> เพื่อดู keyboard shortcuts</li>'
    +'<li>กด <kbd style="background:var(--elev-2);padding:1px 6px;border-radius:3px;border:1px solid var(--border2)">Ctrl/⌘+K</kbd> เพื่อเปิด Command Palette</li>'
    +'<li><b>?agent=zcode</b> ใน URL — filter skills ตาม agent ที่ใช้</li>'
    +'<li>Workspace 💾 — บันทึก tab + scroll + filters เป็น workspace เพื่อเรียกคืน</li>'
    +'<li>Compare ⚖️ — เปรียบเทียบ skills 2-3 ตัวพร้อมกัน</li>'
    +'</ul></div>'
    // Health check section
    +'<div class="glass-card" style="padding:12px">'
    +'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">'
    +'<div style="font-weight:600;color:var(--accent-success)">🩺 ตรวจสุขภาพ Dashboard</div>'
    +'<button onclick="runHealthCheck()" style="padding:5px 12px;border-radius:var(--r-md);border:1px solid var(--accent-success);background:var(--elev-2);color:var(--accent-success);font-size:var(--fs-2xs);cursor:pointer">ตรวจเลย</button>'
    +'</div>'
    +'<div id="health-check-result" style="font-size:var(--fs-xs)">กดปุ่มเพื่อตรวจ SSE/API/localStorage/CDN</div>'
    +'</div>'
    +'</div>';
}
// CHUNK B13: first-run toast tour — 7 steps guiding new users through key features.
// Uses a custom overlay (not the auto-hide toast) so Next/Skip stay clickable.
// State: awiki-tour-completed (bool), awiki-tour-step (0-6) for resume.
// _tourActive flag suppresses other toasts during the tour.
const TOUR_COMPLETED_KEY='awiki-tour-completed';
const TOUR_STEP_KEY='awiki-tour-step';
let _tourActive=false;
const TOUR_STEPS=[
  {title:'ยินดีต้อนรับสู่ A-Wiki Dashboard 👋',body:'นี่คือศูนย์กลางสำหรับติดตาม swarm, skills, และ cost. ทัวร์นี้ 7 ขั้น — ใช้เวลา ~1 นาที.'},
  {title:'🧩 Skills tab',body:'คลิก Skills เพื่อดู skill catalog ทั้งหมด — คำอธิบายไทย + simulation + filter ตาม agent ที่ใช้.'},
  {title:'💡 Recommender',body:'ใน Skills tab มีช่อง "อยากทำ..." — พิมพ์เช่น "แก้ bug" แล้วระบบจะแนะนำ skill ที่เกี่ยวข้อง.'},
  {title:'⚙️ Settings',body:'คลิก ⚙️ เพื่อตั้งค่า models, API keys, agent chain, และดู features ใหม่ๆ.'},
  {title:'🎨 Theme Editor',body:'Settings → 🎨 Theme: ปรับสี dashboard 8 tokens ได้ตามใจ — live preview ทันที.'},
  {title:'💾 Backup',body:'Settings → 💾 Backup: สำรอง preferences ทั้งหมดเป็น JSON — ย้ายระหว่างเครื่องได้.'},
  {title:'⌨️ Shortcuts + 🩺 Health',body:'กด ? เพื่อดู keyboard shortcuts. ใน Help (📖) มีปุ่มตรวจสุขภาพ dashboard. ทัวร์จบแล้ว!'},
];
function _tourShowOverlay(){
  let ov=document.getElementById('tour-overlay');
  if(!ov){
    ov=document.createElement('div');
    ov.id='tour-overlay';
    ov.style.cssText='position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--elev-1);border:1px solid var(--accent-brand);border-radius:var(--r-lg);padding:16px 20px;z-index:500;max-width:440px;width:92vw;box-shadow:var(--shadow-lg)';
    document.body.appendChild(ov);
  }
  return ov;
}
function startTour(){
  let step=0;
  try{step=parseInt(localStorage.getItem(TOUR_STEP_KEY)||'0',10)||0;}catch(_){step=0;}
  _tourActive=true;
  _tourShowStep(step);
}
function _tourShowStep(i){
  if(i>=TOUR_STEPS.length){_tourEnd();return;}
  try{localStorage.setItem(TOUR_STEP_KEY,String(i));}catch(_){}
  const step=TOUR_STEPS[i];
  const ov=_tourShowOverlay();
  const isLast=i===TOUR_STEPS.length-1;
  ov.innerHTML=''
    +'<div style="font-size:var(--fs-xs);color:var(--text-tertiary);margin-bottom:4px">ทัวร์ '+(i+1)+'/'+TOUR_STEPS.length+'</div>'
    +'<div style="font-weight:700;color:var(--accent-brand);margin-bottom:6px;font-size:var(--fs-sm)">'+step.title+'</div>'
    +'<div style="font-size:var(--fs-xs);color:var(--text-secondary);line-height:1.5;margin-bottom:12px">'+step.body+'</div>'
    +'<div style="display:flex;gap:6px;justify-content:flex-end">'
    +'<button onclick="_tourSkip()" style="background:transparent;border:none;color:var(--text-tertiary);cursor:pointer;font-size:var(--fs-xs);padding:4px 10px">ข้าม</button>'
    +'<button onclick="_tourNext()" style="background:var(--accent-brand);color:var(--elev-0);border:none;border-radius:var(--r-sm);cursor:pointer;font-size:var(--fs-xs);padding:6px 14px;font-weight:600">'+(isLast?'เสร็จสิ้น ✓':'ถัดไป →')+'</button>'
    +'</div>';
  ov.style.display='block';
}
function _tourNext(){
  let cur=0;try{cur=parseInt(localStorage.getItem(TOUR_STEP_KEY)||'0',10)||0;}catch(_){}
  _tourShowStep(cur+1);
}
function _tourSkip(){_tourEnd();}
function _tourEnd(){
  _tourActive=false;
  try{localStorage.setItem(TOUR_COMPLETED_KEY,'1');}catch(_){}
  const ov=document.getElementById('tour-overlay');
  if(ov)ov.style.display='none';
}
function _maybeStartTour(){
  let done=false;
  try{done=localStorage.getItem(TOUR_COMPLETED_KEY)==='1';}catch(_){}
  if(!done)setTimeout(startTour,2500);
}
// CHUNK C13: dashboard health check — async checks with 5s timeout each.
// Renders a checklist (✅/❌/ℹ️) into the Help pane.
const HEALTH_CHECK_TIMEOUT=5000;
async function runHealthCheck(){
  const target=document.getElementById('health-check-result');
  if(!target)return;
  target.innerHTML='<div style="color:var(--text-tertiary);font-size:var(--fs-xs)">⏳ กำลังตรวจ...</div>';
  const results=[];
  // 1. SSE connection
  const dot=document.getElementById('live-dot');
  const sseOk=dot&&dot.classList.contains('on');
  results.push({ok:sseOk,label:'SSE Connection',detail:sseOk?'เชื่อมต่อแล้ว':'ยังไม่ได้เชื่อมต่อ',info:false});
  // 2. API responsiveness (with timeout)
  try{
    const ctrl=new AbortController();
    const to=setTimeout(()=>ctrl.abort(),HEALTH_CHECK_TIMEOUT);
    const t0=Date.now();
    const r=await fetch('/api/skills?limit=1',{signal:ctrl.signal});
    clearTimeout(to);
    const ms=Date.now()-t0;
    results.push({ok:r.ok&&ms<5000,label:'API Response',detail:'/api/skills '+ms+'ms',info:false});
  }catch(e){
    results.push({ok:false,label:'API Response',detail:'timeout/error: '+(e.message||e),info:false});
  }
  // 3. localStorage usage
  let lsBytes=0;
  try{for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);lsBytes+=(k||'').length+(localStorage.getItem(k)||'').length;}}catch(_){}
  const lsPct=(lsBytes/(5*1024*1024)*100);
  results.push({ok:lsPct<80,label:'localStorage',detail:lsBytes+'B ('+lsPct.toFixed(1)+'% of 5MB)',info:false});
  // 4. CDN loaded (vis-network + sortablejs)
  const visOk=typeof window.vis!=='undefined';
  const sortOk=typeof window.Sortable!=='undefined';
  results.push({ok:visOk&&sortOk,label:'CDN Libraries',detail:'vis:'+visOk+' sortable:'+sortOk,info:false});
  // 5. Playwright (info only — optional dep, not a failure)
  results.push({ok:true,label:'Playwright',detail:'optional dep — run npm i to enable browser tests',info:true});
  // Render
  target.innerHTML=results.map(r=>{
    const icon=r.info?'ℹ️':(r.ok?'✅':'❌');
    const color=r.info?'var(--text-tertiary)':(r.ok?'var(--accent-success)':'var(--accent-danger)');
    return '<div style="display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--border)"><span style="font-size:var(--fs-sm)">'+icon+'</span><span style="font-weight:600;color:'+color+';font-size:var(--fs-xs);min-width:120px">'+r.label+'</span><span style="color:var(--text-tertiary);font-size:var(--fs-2xs);font-family:var(--font-mono)">'+r.detail+'</span></div>';
  }).join('');
}
// CHUNK D13: "What's new" badge — red dot on Settings cog when version changes.
// Compares awiki-seen-version against DASHBOARD_VERSION. Clicking Settings clears it.
const SEEN_VERSION_KEY='awiki-seen-version';
function updateWhatsNewBadge(){
  let seen='';
  try{seen=localStorage.getItem(SEEN_VERSION_KEY)||'';}catch(_){}
  const badge=document.getElementById('whats-new-badge');
  if(!badge)return;
  if(seen!==DASHBOARD_VERSION){
    badge.style.display='inline-block';
    badge.title='มี features ใหม่ใน '+DASHBOARD_VERSION+' — ดูใน Help (📖)';
  }else{
    badge.style.display='none';
  }
}
function clearWhatsNewBadge(){
  try{localStorage.setItem(SEEN_VERSION_KEY,DASHBOARD_VERSION);}catch(_){}
  updateWhatsNewBadge();
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
// CHUNK C11: check if a weekly auto-backup is due (non-blocking, ~1ms).
try{_maybeAutoBackup();}catch(_){}
// CHUNK B13: start first-run tour for new users (2.5s delay after boot).
try{_maybeStartTour();}catch(_){}
// CHUNK D13: show "what's new" badge if version changed.
try{updateWhatsNewBadge();}catch(_){}
