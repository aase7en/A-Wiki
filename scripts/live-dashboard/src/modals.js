// === CHUNK M — Keyboard Shortcuts ===
const SHORTCUTS=[
{key:'/',desc:'โฟกัสช่องค้นหา Skills',action:()=>{setView('skills');setTimeout(()=>$('skills-search')&&$('skills-search').focus(),100);}},
{key:'g s',desc:'ไปที่ Skills tab',action:()=>setView('skills')},
{key:'g c',desc:'ไปที่ Coverage tab',action:()=>setView('coverage')},
{key:'g g',desc:'ไปที่ Graph tab (log)',action:()=>setView('graph')},
{key:'g f',desc:'ไปที่ Flow tab',action:()=>setView('flow')},
{key:'g t',desc:'ไปที่ Timeline tab',action:()=>setView('timeline')},
{key:'g e',desc:'ไปที่ Eval tab (pass@k history)',action:()=>setView('eval')},
{key:'g $',desc:'ไปที่ Cost tab (USD/run estimate)',action:()=>setView('cost')},
{key:'g h',desc:'กลับหน้าแรก (Summary)',action:()=>setView('summary')},
{key:'?',desc:'แสดง/ซ่อน shortcuts help',action:()=>_toggleShortcutsHelp()},
{key:'Escape',desc:'ปิดหน้าต่างบนสุด',action:()=>_closeTopmost()},
];
let _gKey=null,_gKeyTimer=null;
function _closeTopmost(){
// Priority: palette > compare modal > sim modal > skills drawer > shortcuts help > settings
if($('palette-backdrop')&&$('palette-backdrop').style.display!=='none'){closePalette();return;}
if($('compare-backdrop')&&$('compare-backdrop').style.display!=='none'){closeCompareModal();return;}
if($('sim-backdrop')&&$('sim-backdrop').classList.contains('show')){simClose();return;}
if($('skills-detail')&&$('skills-detail').style.transform==='translateX(0)'){skillsCloseDetail();return;}
if($('shortcuts-backdrop')&&$('shortcuts-backdrop').style.display!=='none'){_closeShortcutsHelp();return;}
if($('settings-backdrop')&&$('settings-backdrop').classList.contains('show')){closeSettings();return;}
}
function _toggleShortcutsHelp(){
const bd=$('shortcuts-backdrop'),help=$('shortcuts-help');
const isOpen=bd.style.display!=='none';
if(isOpen){_closeShortcutsHelp();return;}
const list=$('shortcuts-list');
const kbQQ=_loadKeybindings();
list.innerHTML=SHORTCUTS.map(s=>{const eff=kbQQ[s.key]||s.key;const isCustom=!!kbQQ[s.key];return `<div style="display:flex;justify-content:space-between;align-items:center;gap:12px"><span style="color:var(--text-secondary)">${s.desc}</span><kbd style="background:var(--elev-2);padding:3px 10px;border-radius:var(--r-sm);border:1px solid ${isCustom?'var(--accent-warm)':'var(--border2)'};font-family:var(--font-mono);font-size:var(--fs-2xs);color:${isCustom?'var(--accent-warm)':'var(--accent-brand)'};white-space:nowrap">${eff===' '?'Space':eff}${isCustom?' ⚙️':''}</kbd></div>`;}).join('');
bd.style.display='block';help.style.display='block';
_openModalTrap($('shortcuts-help'));
}
function _closeShortcutsHelp(){
$('shortcuts-backdrop').style.display='none';
$('shortcuts-help').style.display='none';
_closeModalTrap();
}
// === CHUNK QQ — Shortcut Customization ===
// Keybindings store: {action_id: user_sequence}. Default = identity (each action
// uses its own SHORTCUTS[].key). Users remap via the customize modal; profile is
// exportable/importable as JSON. localStorage key: awiki-keybindings.
const KEYBINDINGS_KEY='awiki-keybindings';
let _keybindCapture=null;  // {actionId} when capturing, else null
// Resolve the effective sequence for an action: user override → default key.
function _effectiveKey(actionId, defaultKey){
  const kb=_loadKeybindings();
  return kb[actionId]||defaultKey;
}
// Reverse-lookup: given a pressed sequence, find the matching action (checks
// both single-key and two-key "g x" forms).
function _resolveShortcutBySeq(seq){
  const kb=_loadKeybindings();
  for(const s of SHORTCUTS){
    const eff=kb[s.key]||s.key;  // s.key doubles as the action id (identity default)
    if(eff===seq)return s;
  }
  return null;
}
function _loadKeybindings(){
  return _lsGet(KEYBINDINGS_KEY,{});
}
function _saveKeybindings(kb){_lsSet(KEYBINDINGS_KEY,kb);}
function resetKeybindings(){
  _saveKeybindings({});
  toast('↺ คืนค่า shortcuts เริ่มต้นแล้ว');
  if($('keybind-backdrop').style.display!=='none')_renderKeybindList();
  if($('shortcuts-backdrop').style.display!=='none')_toggleShortcutsHelp(),_toggleShortcutsHelp();
}
function exportKeybindings(){
  const kb=_loadKeybindings();
  const blob=new Blob([JSON.stringify({version:1,keybindings:kb},null,2)],{type:'application/json'});
  _downloadBlob(blob,'awiki-keybindings.json');
  toast('📤 ส่งออก keybindings แล้ว');
}
function importKeybindings(ev){
  const f=ev.target.files[0];if(!f)return;
  const rd=new FileReader();
  rd.onload=()=>{
    try{
      const j=JSON.parse(rd.result);
      const kb=(j&&j.keybindings&&typeof j.keybindings==='object')?j.keybindings:j;
      // Validate: only known action ids, values are non-empty strings.
      const valid={};
      const known=new Set(SHORTCUTS.map(s=>s.key));
      Object.keys(kb||{}).forEach(k=>{if(known.has(k)&&typeof kb[k]==='string'&&kb[k].trim())valid[k]=kb[k].trim();});
      _saveKeybindings(valid);
      toast('📥 นำเข้า keybindings แล้ว ('+Object.keys(valid).length+' รายการ)');
      if($('keybind-backdrop').style.display!=='none')_renderKeybindList();
    }catch(e){toast('นำเข้าไม่สำเร็จ: '+e.message,true);}
  };
  rd.readAsText(f);
  ev.target.value='';  // allow re-import of same file
}
function _openKeybindCustomize(){
  $('keybind-backdrop').style.display='block';
  $('keybind-modal').style.display='block';
  _renderKeybindList();
  _openModalTrap($('keybind-modal'));
}
function _closeKeybindCustomize(){
  $('keybind-backdrop').style.display='none';
  $('keybind-modal').style.display='none';
  _closeModalTrap();
  _keybindCapture=null;
}
function _renderKeybindList(){
  const list=$('keybind-list');if(!list)return;
  const kb=_loadKeybindings();
  list.innerHTML=SHORTCUTS.map(s=>{
    const eff=kb[s.key]||s.key;
    const isCustom=!!kb[s.key];
    return `<div style="display:flex;justify-content:space-between;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid var(--border)">
      <span style="color:var(--text-secondary);flex:1">${s.desc}</span>
      <button id="kb-cap-${s.key.replace(/\s|\//g,'_')}" class="set-btn sm" onclick="_startKeyCapture('${s.key}')" style="font-family:var(--font-mono);font-size:var(--fs-2xs);min-width:70px;${isCustom?'border-color:var(--accent-brand);color:var(--accent-brand)':''}">${eff===' '?'Space':eff}</button>
    </div>`;
  }).join('');
}
function _startKeyCapture(actionId){
  _keybindCapture={actionId};
  const safeId=actionId.replace(/\s|\//g,'_');
  const btn=$('kb-cap-'+safeId);if(btn){btn.textContent='กดปุ่ม…';btn.style.borderColor='var(--accent-warm)';btn.style.color='var(--accent-warm)';}
}
// Keydown handler for capture mode (attached once). Enter confirms, Esc cancels.
window.addEventListener('keydown',function(e){
  if(!_keybindCapture)return;
  e.preventDefault();e.stopPropagation();
  const aid=_keybindCapture.actionId;
  const safeId=aid.replace(/\s|\//g,'_');
  const btn=$('kb-cap-'+safeId);
  if(e.key==='Escape'){_keybindCapture=null;if(btn){btn.textContent=aid;btn.style.borderColor='';btn.style.color='';}return;}
  if(e.key==='Enter'){
    // Confirm: use whatever was buffered in _keybindCapture.seq (may be undefined → clear)
    _keybindCapture=null;
    if(btn){btn.textContent=aid;btn.style.borderColor='';btn.style.color='';}
    return;
  }
  // Build sequence: single key, or "g x" if first key is g.
  let seq;
  if(e.key==='g'&&!_keybindCapture.seq){_keybindCapture.seq='g';if(btn)btn.textContent='g …';return;}
  if(_keybindCapture.seq==='g'){seq='g '+e.key.toLowerCase();}
  else{seq=e.key;}
  // Commit immediately on a complete sequence.
  const kb=_loadKeybindings();
  // Don't allow empty / whitespace-only.
  if(seq&&seq.trim()){
    kb[aid]=seq;_saveKeybindings(kb);
    if(btn){btn.textContent=seq===' '?'Space':seq;btn.style.borderColor='var(--accent-brand)';btn.style.color='var(--accent-brand)';}
  }
  _keybindCapture=null;
},true);  // capture phase — runs before the main shortcut handler

// === CHUNK RR — Notification System ===
// Opt-in desktop notifications for key dashboard events. Uses the Web Notification
// API when permission is granted; falls back to toast() when denied/unavailable.
// Preferences persist in localStorage awiki-notif-prefs. Triggers hook into the
// existing SSE handleEvent() dispatch + onHook() + cycle check + skillsLoad().
const NOTIF_PREFS_KEY='awiki-notif-prefs';
const NOTIF_DEFAULTS={registry_update:true,hook_block:true,low_health:false,cycle:true,delegate_fail:true};
const NOTIF_LABELS={registry_update:'Registry อัปเดต',hook_block:'Hook บล็อก',low_health:'Health ต่ำ (<40)',cycle:'พบ circular dependency',delegate_fail:'Delegation ล้มเหลว'};
let _notifLastShown={};  // tag → last ts (dedupe within 10s)
function _notifSupported(){return typeof Notification!=='undefined';}
function _loadNotifPrefs(){return Object.assign({},NOTIF_DEFAULTS,_lsGet(NOTIF_PREFS_KEY,{}));}
function _saveNotifPrefs(p){_lsSet(NOTIF_PREFS_KEY,p);}
function _notifPerm(){return _notifSupported()?Notification.permission:'denied';}
// Fire a notification (title+body). tag dedupes within 10s. Falls back to toast.
function showNotif(title,body,tag){
  try{
    const prefs=_loadNotifPrefs();
    // tag maps to a pref key — respect user opt-out.
    if(tag&&!prefs[tag])return;
    const now=Date.now();
    if(tag&&_notifLastShown[tag]&&now-_notifLastShown[tag]<10000)return;  // dedupe 10s
    if(tag)_notifLastShown[tag]=now;
    const perm=_notifPerm();
    if(perm==='granted'&&_notifSupported()){
      try{new Notification(title,{body:body||'',tag:tag||undefined,silent:false});return;}
      catch(_){}
    }
    // Fallback: in-page toast (always available).
    toast(title+(body?': '+body:''));
  }catch(_){}
}
async function _requestNotifPerm(){
  if(!_notifSupported()){toast('เบราว์เซอร์นี้ไม่รองรับ Web Notification',true);return 'unsupported';}
  try{
    const p=await Notification.requestPermission();
    if(p==='granted'){toast('🔔 เปิดการแจ้งเตือนแล้ว');showNotif('A-Wiki Dashboard','การแจ้งเตือนเปิดใช้งานแล้ว','registry_update');}
    else{toast('การแจ้งเตือนถูกปฏิเสธ — จะใช้ toast แทน');}
    return p;
  }catch(e){toast('ขอ permission ไม่สำเร็จ',true);return 'error';}
}
function openNotifPrefs(){
  $('notif-backdrop').style.display='block';
  $('notif-modal').style.display='block';
  _renderNotifPrefs();
  _openModalTrap($('notif-modal'));
}
function closeNotifPrefs(){
  $('notif-backdrop').style.display='none';
  $('notif-modal').style.display='none';
  _closeModalTrap();
}
function _renderNotifPrefs(){
  const perm=_notifPerm();
  const permRow=$('notif-perm-row');
  const supported=_notifSupported();
  if(!supported){
    permRow.innerHTML='<div style="color:var(--text-tertiary);font-size:var(--fs-2xs)">⚠️ เบราว์เซอร์นี้ไม่รองรับ Web Notification — จะใช้ toast แทน</div>';
  }else if(perm==='granted'){
    permRow.innerHTML='<div style="color:var(--accent-success);font-size:var(--fs-2xs)">✅ สิทธิ์การแจ้งเตือน: เปิดอนุญาตแล้ว</div>';
  }else if(perm==='denied'){
    permRow.innerHTML='<div style="color:var(--text-tertiary);font-size:var(--fs-2xs)">🚫 สิทธิ์ถูกปฏิเสธ — ปลดล็อกใน Site Settings ของเบราว์เซอร์ (จะใช้ toast แทน)</div>';
  }else{
    permRow.innerHTML='<button class="set-btn sm" onclick="_requestNotifPerm()" style="font-size:var(--fs-xs);color:var(--accent-brand)">🔔 เปิดการแจ้งเตือน</button>';
  }
  const prefs=_loadNotifPrefs();
  const list=$('notif-prefs-list');
  list.innerHTML=Object.keys(NOTIF_LABELS).map(k=>{
    const on=!!prefs[k];
    return `<label style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);cursor:pointer">
      <span style="color:var(--text-secondary)">${NOTIF_LABELS[k]}</span>
      <input type="checkbox" ${on?'checked':''} onchange="toggleNotifPref('${k}',this.checked)" style="cursor:pointer;accent-color:var(--accent-brand)">
    </label>`;
  }).join('');
}
function toggleNotifPref(key,val){
  const prefs=_loadNotifPrefs();prefs[key]=val;_saveNotifPrefs(prefs);
}

// === CHUNK UU — Workspace Save/Restore ===
// Snapshot the current dashboard layout (active view + scroll position + open
// detail drawers + all Skills-tab filters) into a named workspace, persisted
// in localStorage. Restore on demand or auto-restore last on boot.
const WORKSPACES_KEY='awiki-workspaces';
const WORKSPACE_LAST_KEY='awiki-workspace-last';
const WORKSPACE_AUTORESTORE_KEY='awiki-workspace-autorestore';
const WORKSPACES_MAX=10;
function _loadWorkspaces(){return _lsGet(WORKSPACES_KEY,[]);}
function _saveWorkspaces(ws){_lsSet(WORKSPACES_KEY,ws);}
// Capture current state into a plain object.
function captureWorkspace(){
  const filters={};
  const a=$('skills-agent-filter');if(a)filters.agent=a.value;
  const d=$('skills-domain-filter');if(d)filters.domain=d.value;
  const q=$('skills-search');if(q)filters.q=q.value;
  const s=$('skills-sort');if(s)filters.sort=s.value;
  filters.invocation=_skillsInv;filters.category=_skillsCat;
  const inst=$('skills-installed-only');filters.installed=!!(inst&&inst.checked);
  // Open drawers: track if skills detail is open + its name.
  const openDrawers=[];
  const sd=$('skills-detail');
  if(sd&&sd.style.transform==='translateX(0)'){openDrawers.push('_skills-detail');}
  return{
    view:currentView,
    scrollY:window.scrollY,
    openDrawers:openDrawers,
    filters:filters,
    savedAt:new Date().toISOString(),
  };
}
function saveWorkspacePrompt(){
  const name=prompt('ตั้งชื่อ workspace:','workspace-'+new Date().toLocaleDateString('th-TH'));
  if(!name||!name.trim())return;
  const ws=_loadWorkspaces();
  // Replace if same name exists; cap at WORKSPACES_MAX.
  const filtered=ws.filter(w=>w.name!==name.trim());
  filtered.unshift({name:name.trim(),...captureWorkspace()});
  _saveWorkspaces(filtered.slice(0,WORKSPACES_MAX));
  _renderWorkspaceList();
  toast('💾 บันทึก workspace "'+name.trim()+'" แล้ว');
}
function restoreWorkspace(ws){
  if(!ws)return;
  closeWorkspaceMenu();
  // Restore view first.
  if(ws.view){try{setView(ws.view);}catch(_){}}
  // Restore Skills filters (apply after skillsLoad if needed).
  const f=ws.filters||{};
  const applyFilters=()=>{
    if(f.agent){const el=$('skills-agent-filter');if(el)el.value=f.agent;}
    if(f.domain){const el=$('skills-domain-filter');if(el)el.value=f.domain;}
    if(f.q){const el=$('skills-search');if(el)el.value=f.q;}
    if(f.sort){const el=$('skills-sort');if(el)el.value=f.sort;}
    if(f.invocation){try{skillsSetInv(f.invocation);}catch(_){}}
    if(f.category){try{skillsSetCat(f.category);}catch(_){}}
    const inst=$('skills-installed-only');if(inst)inst.checked=!!f.installed;
    try{skillsRefresh();}catch(_){}
  };
  if(ws.view==='skills'){setTimeout(applyFilters,350);}
  else{applyFilters();}
  // Restore scroll.
  if(ws.scrollY){setTimeout(()=>window.scrollTo(0,ws.scrollY),500);}
  _lsSet(WORKSPACE_LAST_KEY,{name:ws.name,savedAt:ws.savedAt});
  toast('💾 เรียกคืน workspace "'+ws.name+'" แล้ว');
}
function deleteWorkspace(name){
  const ws=_loadWorkspaces().filter(w=>w.name!==name);
  _saveWorkspaces(ws);
  _renderWorkspaceList();
  toast('ลบ workspace "'+name+'" แล้ว');
}
function openWorkspaceMenu(){
  $('workspace-backdrop').style.display='block';
  $('workspace-modal').style.display='block';
  _renderWorkspaceList();
  const ar=$('workspace-autorestore');
  if(ar)ar.checked=_lsGet(WORKSPACE_AUTORESTORE_KEY,false);
  _openModalTrap($('workspace-modal'));
}
function closeWorkspaceMenu(){
  $('workspace-backdrop').style.display='none';
  $('workspace-modal').style.display='none';
  _closeModalTrap();
}
function _renderWorkspaceList(){
  const list=$('workspace-list');if(!list)return;
  const ws=_loadWorkspaces();
  if(!ws.length){list.innerHTML='<div style="color:var(--text-tertiary);font-size:var(--fs-2xs);padding:8px 0">ยังไม่มี workspace บันทึก</div>';return;}
  list.innerHTML=ws.map(w=>`<div style="display:flex;justify-content:space-between;align-items:center;gap:8px;padding:8px;border:1px solid var(--border2);border-radius:var(--r-md);background:var(--elev-2)">
    <div style="flex:1;cursor:pointer" onclick="restoreWorkspace(${_wsEscape(w)})">
      <div style="color:var(--text-primary);font-weight:600">${w.name}</div>
      <div style="font-size:var(--fs-2xs);color:var(--text-tertiary)">${w.view} · ${(w.savedAt||'').slice(0,10)}</div>
    </div>
    <button onclick="deleteWorkspace('${w.name.replace(/'/g,"")}') " style="background:transparent;border:none;color:var(--text-tertiary);cursor:pointer;font-size:16px;padding:4px" title="ลบ">✕</button>
  </div>`).join('');
}
// Escape a workspace object into a JSON literal safe for onclick="restoreWorkspace(...)".
function _wsEscape(w){return "'"+JSON.stringify(w).replace(/'/g,"\\'")+"'";}
function toggleWorkspaceAutorestore(on){_lsSet(WORKSPACE_AUTORESTORE_KEY,!!on);}
// Boot-time auto-restore (called from boot sequence).
function maybeAutoRestoreWorkspace(){
  if(!_lsGet(WORKSPACE_AUTORESTORE_KEY,false))return;
  const ws=_loadWorkspaces();if(!ws.length)return;
  // Restore the most recent workspace.
  setTimeout(()=>restoreWorkspace(ws[0]),400);
}

// === CHUNK EE — Command Palette ===
let _paletteIndex=[],_paletteSel=0,_paletteResults=[],_paletteDebounce=null;
const PALETTE_ICONS={skill:'🧩',flow:'🌊',view:'📊',shortcut:'⌨️'};
function _paletteBuildIndex(){
  _paletteIndex=[];
  // Skills (from cache if loaded, else fetch)
  if(window._skillsCache&&Array.isArray(_skillsCache)){
    _skillsCache.forEach(s=>{
      if(s.status!=='canonical')return;
      _paletteIndex.push({type:'skill',label:s.name,sub:(s.th_description||'').slice(0,60),action:()=>{setView('skills');setTimeout(()=>skillsOpenDetail(s.name),250);}});
    });
  }
  // Views (9 known)
  [['summary','📊 Summary'],['flow','🌊 Flow'],['timeline','🏊 Timeline'],['graph','🔗 Graph'],['skills','🧩 Skills'],['coverage','📊 Coverage'],['subagents','🔬 Subagents'],['council','🏛️ Council'],['chat','💬 Chat']].forEach(([v,label])=>{
    _paletteIndex.push({type:'view',label:label+' tab',sub:'สลับไปยัง '+label,action:()=>setView(v)});
  });
  // Shortcuts (re-use SHORTCUTS array)
  SHORTCUTS.forEach(s=>{
    if(s.key==='Escape')return;
    _paletteIndex.push({type:'shortcut',label:s.desc,sub:'Shortcut: '+s.key,action:s.action});
  });
}
function _paletteFuzzy(q,target){
  q=q.toLowerCase();target=target.toLowerCase();
  if(target.includes(q))return 1000-target.indexOf(q);
  let ti=0,score=0;
  for(let qi=0;qi<q.length&&ti<target.length;qi++){
    if(target[ti]===q[qi]){score+=2;ti++;}
    else{ti++;qi--;if(qi>0&&ti-target.indexOf(q[0])>q.length*2)break;}
  }
  return score>=q.length*2?score:0;
}
function _paletteRank(q){
  if(!q.trim())return _paletteIndex.slice(0,10);
  const scored=_paletteIndex.map(it=>{
    const s=Math.max(_paletteFuzzy(q,it.label||''),_paletteFuzzy(q,it.sub||''));
    return Object.assign({},it,{_s:s});
  }).filter(it=>it._s>0);
  scored.sort((a,b)=>b._s-a._s);
  return scored.slice(0,10);
}
function _paletteRender(results){
  _paletteResults=results;_paletteSel=0;
  const box=$('palette-results'),empty=$('palette-empty');
  if(!results.length){box.innerHTML='';empty.style.display='block';return;}
  empty.style.display='none';
  box.innerHTML=results.map((it,i)=>{
    const ic=PALETTE_ICONS[it.type]||'▸';
    return `<div class="palette-row${i===0?' sel':''}" data-idx="${i}" onmouseenter="_paletteHover(${i})" onclick="_paletteActivate(${i})" style="display:flex;align-items:center;gap:10px;padding:9px 14px;cursor:pointer;border-radius:var(--r-sm);${i===0?'background:var(--elev-2);':''}">
      <span style="font-size:var(--fs-md)">${ic}</span>
      <div style="flex:1;min-width:0">
        <div style="color:var(--text-primary);font-size:var(--fs-sm);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${(it.label||'').replace(/</g,'&lt;')}</div>
        ${it.sub?`<div style="color:var(--text-tertiary);font-size:var(--fs-2xs);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${(it.sub||'').replace(/</g,'&lt;')}</div>`:''}
      </div>
      <span style="font-size:var(--fs-2xs);color:var(--text-tertiary);text-transform:uppercase;letter-spacing:.5px">${it.type}</span>
    </div>`;
  }).join('');
}
function _paletteHover(i){_paletteSel=i;_paletteHighlight();}
function _paletteHighlight(){
  document.querySelectorAll('.palette-row').forEach((r,i)=>{
    r.style.background=i===_paletteSel?'var(--elev-2)':'';
  });
}
function _paletteActivate(i){
  const it=_paletteResults[i];if(!it)return;
  closePalette();
  try{it.action();}catch(err){toast('palette: '+err.message,true);}
}
function paletteSearchDebounced(){
  clearTimeout(_paletteDebounce);
  _paletteDebounce=setTimeout(()=>{
    _paletteRender(_paletteRank($('palette-input').value));
  },150);
}
async function openPalette(){
  // Ensure skills are loaded so palette can index them
  if(!_skillsCache.length){
    try{
      const r=await fetch('/api/skills?limit=500').then(r=>r.json());
      _skillsCache=r.skills||[];
    }catch(_){}
  }
  _paletteBuildIndex();
  $('palette-backdrop').style.display='block';
  $('palette-modal').style.display='block';
  const inp=$('palette-input');inp.value='';
  // Pre-render with no query (shows first 10 of index)
  _paletteRender(_paletteRank(''));
  setTimeout(()=>inp.focus(),50);
  _openModalTrap($('palette-modal'));
}
function closePalette(){
  $('palette-backdrop').style.display='none';
  $('palette-modal').style.display='none';
  _closeModalTrap();
}
// Palette keyboard nav (arrows + enter) — bound within palette input
window.addEventListener('keydown',function(e){
  if($('palette-modal').style.display==='none')return;
  if(e.key==='ArrowDown'){e.preventDefault();_paletteSel=Math.min(_paletteSel+1,_paletteResults.length-1);_paletteHighlight();var r=document.querySelector('.palette-row.sel');if(r)r.scrollIntoView({block:'nearest'});}
  else if(e.key==='ArrowUp'){e.preventDefault();_paletteSel=Math.max(_paletteSel-1,0);_paletteHighlight();var r=document.querySelector('.palette-row.sel');if(r)r.scrollIntoView({block:'nearest'});}
  else if(e.key==='Enter'){e.preventDefault();_paletteActivate(_paletteSel);}
});
window.addEventListener('keydown',function(e){
const tag=(e.target&&e.target.tagName)||'';
const isInput=(tag==='INPUT'||tag==='TEXTAREA'||tag==='SELECT');
// Ctrl/Cmd+K opens Command Palette everywhere (even in inputs).
if((e.metaKey||e.ctrlKey)&&(e.key==='k'||e.key==='K')){e.preventDefault();openPalette();return;}
// Escape always works (even in inputs).
if(e.key==='Escape'){_closeTopmost();return;}
// CHUNK QQ: build effective-key index honoring user overrides (once per keystroke).
// Each entry: firstKey → {second?: fullSeq, single?: action}. Supports remap of
// single-key shortcuts (e.g. '/' → 'x') and two-key ('g s' → 'h s').
const kbQQ=_loadKeybindings();
// '?' help toggle — check if user remapped it.
const helpEff=kbQQ['?']||'?';
if(e.key===helpEff&&!isInput){e.preventDefault();_toggleShortcutsHelp();return;}
// Skip all other shortcuts when typing in inputs.
if(isInput)return;
// Build the set of first-keys that START any (possibly two-key) shortcut.
const twoKeyFirsts={};
const singleMap={};
SHORTCUTS.forEach(s=>{
  if(s.key==='Escape')return;  // handled above
  if(s.key==='?')return;  // handled above
  const eff=kbQQ[s.key]||s.key;
  const parts=eff.split(' ');
  if(parts.length===2){twoKeyFirsts[parts[0]]=true;}
  else{singleMap[eff]=s;}
});
// Two-key sequence handling: if this key could be a first-key of any two-key seq.
if(twoKeyFirsts[e.key]){
_gKey=e.key;
clearTimeout(_gKeyTimer);
_gKeyTimer=setTimeout(()=>{_gKey=null;},700);
return;
}
if(_gKey){
const combo=_gKey+' '+e.key.toLowerCase();
const sc=_resolveShortcutBySeq(combo);
if(sc){e.preventDefault();_gKey=null;clearTimeout(_gKeyTimer);sc.action();}
return;
}
// Single-key shortcuts (remapped or default).
const sc=_resolveShortcutBySeq(e.key);
if(sc){e.preventDefault();sc.action();}
});
function setTab(b){document.querySelectorAll('.set-tab').forEach(x=>x.classList.remove('active'));
document.querySelectorAll('.set-pane').forEach(p=>p.classList.remove('active'));b.classList.add('active');$(b.dataset.pane).classList.add('active');}
async function loadSettings(){
try{const[models,caps,keys]=await Promise.all([
fetch('/api/models').then(r=>r.json()),fetch('/api/capabilities').then(r=>r.json()),fetch('/api/keys').then(r=>r.json())]);
_caps=caps||_caps;renderModels(models.models||[],keys.keys||[]);renderKeys(keys.keys||[]);}
catch(e){toast('โหลด settings ไม่ได้',true);}}
async function loadModelStationsConfig(){
try{const m=await fetch('/api/models').then(r=>r.json());
(m.models||[]).forEach(md=>{const st=addStation(md.model_id||md.id||md.name);
if(st&&md.enabled===false){st.disabled=true;st.el.classList.add('disabled');}});
// Restore flow stations drag-and-drop order
try{
  const saved=JSON.parse(localStorage.getItem('awiki-flow-stations-order')||'[]');
  if(saved.length){
    const temp={};
    saved.forEach(k=>{if(_stations[k])temp[k]=_stations[k];});
    for(const k in _stations){if(!temp[k])temp[k]=_stations[k];}
    for(const k in _stations){delete _stations[k];}
    for(const k in temp){_stations[k]=temp[k];}
    // Also re-order children in the DOM flow-overlay so on-screen elements match
    const overlay=document.getElementById('flow-overlay');
    if(overlay){
      saved.forEach(k=>{
        const el=overlay.querySelector(`.station[data-key="${k}"]`);
        if(el)overlay.appendChild(el);
      });
    }
  }
}catch(_){}
layoutFlow();
}
catch(e){}}
function famScores(m){const hay=[m.id,m.model_id,m.name,m.provider].join(' ').toLowerCase();
for(const f of Object.values(_caps.families||{}))if((f.match||[]).some(s=>hay.includes(s)))return f;return null;}
function renderModels(models,keys){
const ks={};(keys||[]).forEach(k=>ks[k.name]=k.set);const w=$('models-list');w.innerHTML='';
models.forEach((m,i)=>{
const card=mk('div',`glass-card ${m.id}${m.enabled===false?' disabled':''}`);const f=famScores(m);
const badge=(l,v)=>v==null?'':`<span class="cap-badge ${v>=60?'hi':''}">${l} ${v}</span>`;
const caps=f?`<div class="cap-badges">${badge('SWE',f.swe_bench)}${badge('Term',f.terminal_bench)}${badge('Repo',f.nl2repobench)}${badge('reason',f.reasoning)}${badge('speed',f.speed)}</div>`:'';
const kn=m.key_env||'',hk=ks[kn];
card.innerHTML=`<div class="cfg-row"><span class="cfg-name">${m.name}</span>
<span class="key-status ${hk?'set':'unset'}">${hk?'🔑 set':'🔑 no key'}</span>
<label class="glow-toggle"><input type="checkbox" data-i="${i}" ${m.enabled===false?'':'checked'} aria-label="Enable ${m.name}"><span class="glow-slider"></span></label></div>
<div class="cfg-field"><label>model id</label><input class="cfg-input" data-mid="${i}" value="${m.model_id||''}" placeholder="(default)"></div>${caps}`;
w.appendChild(card);});w._models=models;}
function saveModels(){const w=$('models-list'),models=w._models||[];
w.querySelectorAll('input[type=checkbox]').forEach(cb=>models[+cb.dataset.i].enabled=cb.checked);
w.querySelectorAll('input[data-mid]').forEach(inp=>{const v=inp.value.trim();if(v)models[+inp.dataset.mid].model_id=v;});
fetch('/api/models',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({models})})
.then(r=>r.json()).then(res=>{if(res.ok){toast('✅ บันทึกแล้ว');loadRecommendations();}else toast(res.error||'บันทึกไม่สร็จ',true);})
.catch(()=>toast('บันทึกไม่สำเร็จ',true));}
function renderKeys(keys){const w=$('keys-list');w.innerHTML='';
(keys||[]).forEach(k=>{const card=mk('div','glass-card');
card.innerHTML=`<div class="cfg-row"><span class="cfg-name">${k.name}</span><span class="key-status ${k.set?'set':'unset'}">${k.set?'set':'unset'}</span></div>
<div class="cfg-row"><input class="cfg-input" type="password" data-key="${k.name}" placeholder="วาง API key…"><button class="set-btn sm" data-save="${k.name}">บันทึก</button></div>`;
w.appendChild(card);});
w.querySelectorAll('button[data-save]').forEach(b=>b.onclick=()=>saveKey(b.dataset.save));}
function saveKey(name){const inp=$('keys-list').querySelector(`input[data-key="${name}"]`);const v=inp.value.trim();
if(!v){toast('ใส่ key ก่อน',true);return;}
fetch('/api/keys',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key_name:name,key_value:v})})
.then(r=>r.json()).then(res=>{if(res.ok){inp.value='';toast(`✅ ${name} บันทึก`);loadSettings();}else toast(res.error||'ไม่สำเร็จ',true);})
.catch(()=>toast('ไม่สำเร็จ',true));}
async function loadRecommendations(){
try{const caps=await fetch('/api/capabilities').then(r=>r.json());_caps=caps||_caps;
const rec=caps.recommended_by_task||{};const order=['reason','scan','search'];
const lbl={reason:'reason/compare',scan:'scan',search:'search/lookup'};
const parts=order.filter(t=>rec[t]).map(t=>`<span class="rec-item">🧬 ${lbl[t]} → <b>${rec[t].name}</b> <span style="opacity:.6">(${rec[t].dimension} ${rec[t].score})</span></span>`);
const strip=$('rec-strip');
strip.innerHTML=`<span id="typed-intro" data-typed></span>`+parts.join('');
if(_typedRAF)clearTimeout(_typedRAF);typedStep();
}catch(e){}}
buildOrigin();
