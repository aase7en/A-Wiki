// === CHUNK LL — 3-state theme: auto (prefers-color-scheme) / dark / green-white ===
const THEME_MODE_KEY='awiki-theme-mode';
// Migrate legacy 'awiki-theme' -> 'awiki-theme-mode' once.
try{
  const legacy=localStorage.getItem('awiki-theme');
  if(legacy!==null&&!localStorage.getItem(THEME_MODE_KEY)){
    // legacy '' meant dark, 'green-white' meant green-white. No 'auto' existed.
    localStorage.setItem(THEME_MODE_KEY,legacy==='green-white'?'green-white':'dark');
  }
}catch(_){}
function _resolvedThemeAttr(mode){
  // mode: 'auto' | 'dark' | 'green-white'. Returns the data-theme attribute value.
  if(mode==='dark')return '';
  if(mode==='green-white')return 'green-white';
  // auto: follow prefers-color-scheme.
  try{
    if(window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)').matches){
      return 'green-white';
    }
  }catch(_){}
  return ''; // dark by default
}
function _themeIcon(mode){
  if(mode==='dark')return '🌑';
  if(mode==='green-white')return '☀';
  return '🌗'; // auto
}
function _applyThemeMode(mode){
  const h=document.documentElement;
  h.setAttribute('data-theme',_resolvedThemeAttr(mode));
  const b=document.getElementById('btn-theme');
  if(b)b.textContent=_themeIcon(mode);
  try{localStorage.setItem(THEME_MODE_KEY,mode);}catch(_){}
}
function toggleTheme(){
  // Cycle: auto -> dark -> green-white -> auto.
  let cur='auto';
  try{cur=localStorage.getItem(THEME_MODE_KEY)||'auto';}catch(_){}
  const next=cur==='auto'?'dark':cur==='dark'?'green-white':'auto';
  _applyThemeMode(next);
}
// On load: apply stored mode + register prefers-color-scheme listener for auto mode.
(function(){
  let mode='auto';
  try{mode=localStorage.getItem(THEME_MODE_KEY)||'auto';}catch(_){}
  _applyThemeMode(mode);
  // If in auto mode, react to OS theme changes without reload.
  try{
    const mq=window.matchMedia('(prefers-color-scheme: light)');
    mq.addEventListener('change',function(){
      let m='auto';try{m=localStorage.getItem(THEME_MODE_KEY)||'auto';}catch(_){}
      if(m==='auto')_applyThemeMode('auto');
    });
  }catch(_){}
})();


const AGENT_TYPES=[{type:"plan",role:"วางแผน",icon:"📋",effort:80},{type:"architect",role:"ออกแบบ",icon:"🏗️",effort:90},{type:"ask",role:"ตอบคำถาม",icon:"💬",effort:30},{type:"code",role:"เขียนโค้ด",icon:"💻",effort:70},{type:"code-reviewer",role:"review",icon:"🔍",effort:60},{type:"code-simplifier",role:"simplify",icon:"✂️",effort:50},{type:"code-skeptic",role:"ตรวจสอบ",icon:"🤔",effort:40},{type:"debug",role:"debug",icon:"🐛",effort:85},{type:"docs-specialist",role:"เขียนdoc",icon:"📝",effort:50},{type:"frontend-specialist",role:"frontend",icon:"🎨",effort:75},{type:"orchestrator",role:"orchestrate",icon:"🎯",effort:95},{type:"test-engineer",role:"test",icon:"🧪",effort:70}];
let _agentOrder=AGENT_TYPES.map(a=>a.type);
function renderAgentChain(){
  const list=document.getElementById('agent-chain-list');if(!list)return;
  try{const saved=JSON.parse(localStorage.getItem('awiki-agent-order')||'[]');if(saved.length)_agentOrder=saved;}catch(_){}
  try{const saved=JSON.parse(localStorage.getItem('awiki-agent-effort')||'[]');saved.forEach(s=>{const a=AGENT_TYPES.find(x=>x.type===s.type);if(a)a.effort=s.effort;});}catch(_){}
  list.innerHTML='';
  _agentOrder.forEach(type=>{
    const a=AGENT_TYPES.find(x=>x.type===type)||{type,role:type,icon:'🤖',effort:50};
    const el=document.createElement('div');
    el.className='agent-item';el.dataset.type=a.type;
    el.style.cssText='display:flex;align-items:center;gap:10px;padding:10px 12px;background:var(--elev-1);border:1px solid var(--border);border-radius:var(--r-md);cursor:default;font-size:var(--fs-sm)';
    el.innerHTML='<span class="drag-handle" style="cursor:grab;color:var(--text-tertiary);user-select:none;font-size:16px">⋮⋮</span><span>'+a.icon+'</span><span style="flex:1;font-weight:600">'+a.role+'</span><span style="color:var(--text-tertiary);font-size:var(--fs-xs)">'+a.type+'</span><input type="range" min="0" max="100" value="'+a.effort+'" style="width:60px;accent-color:var(--accent-brand)" data-type="'+a.type+'" oninput="updateEffort(this)"><span style="font-size:var(--fs-xs);min-width:24px;text-align:right">'+a.effort+'</span>';
    list.appendChild(el);
  });
  try{new Sortable(list,{animation:150,handle:'.drag-handle',onEnd:function(evt){
    const items=list.querySelectorAll('.agent-item');_agentOrder=Array.from(items).map(el=>el.dataset.type);
    localStorage.setItem('awiki-agent-order',JSON.stringify(_agentOrder));
    const s=document.getElementById('agent-saved');s.style.display='inline';setTimeout(()=>{s.style.display='none'},2000);
  }});}catch(_){}
}
function updateEffort(slider){
  const type=slider.dataset.type;const val=parseInt(slider.value);const a=AGENT_TYPES.find(x=>x.type===type);if(a)a.effort=val;
  slider.nextElementSibling.textContent=val;
  localStorage.setItem('awiki-agent-effort',JSON.stringify(AGENT_TYPES.filter(a=>a.effort!==undefined).map(a=>({type:a.type,effort:a.effort}))));
}
renderAgentChain();


// ===== FLOW VIEW NODE DRAG-AND-DROP SORTABLE =====
(function initFlowSortable() {
  const overlay = document.getElementById('flow-overlay');
  if (!overlay) return;

  try {
    new Sortable(overlay, {
      animation: 200,
      draggable: '.station',
      onEnd: function (evt) {
        const stationsList = Array.from(overlay.querySelectorAll('.station'));
        const newKeys = stationsList.map(el => el.dataset.key);
        
        // Re-order the _stations object properties in-place based on on-screen drag order
        const temp = {};
        newKeys.forEach(k => {
          if (_stations[k]) {
            temp[k] = _stations[k];
          }
        });
        
        // Pick up any extra station keys that might not have been in the DOM yet (safety)
        for (const k in _stations) {
          if (!temp[k]) {
            temp[k] = _stations[k];
          }
        }
        
        // Clear and rebuild _stations in-place to respect the new property insertion order
        for (const k in _stations) {
          delete _stations[k];
        }
        for (const k in temp) {
          _stations[k] = temp[k];
        }
        
        // Trigger flow layout redraw so the paths, animation particles, and coordinates align perfectly!
        layoutFlow();
        
        // Optional state saving
        try {
          localStorage.setItem('awiki-flow-stations-order', JSON.stringify(newKeys));
        } catch(_) {}
      }
    });
    console.log("✅ Flow Drag-and-Drop Sortable initialized successfully.");
  } catch(e) {
    console.warn("Could not find Sortable for flow-overlay yet, will retry.", e);
  }
})();

