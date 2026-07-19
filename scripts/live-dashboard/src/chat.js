// ===== CHAT CONFIG =====
// CHUNK D15: chat history persistence — refresh ไม่หาย (max 50 messages).
const CHAT_HISTORY_KEY='awiki-chat-history';
const CHAT_HISTORY_MAX=50;
function _loadChatHistory(){try{return JSON.parse(localStorage.getItem(CHAT_HISTORY_KEY)||'[]');}catch(_){return [];}}
function _saveChatHistory(arr){try{localStorage.setItem(CHAT_HISTORY_KEY,JSON.stringify(arr.slice(-CHAT_HISTORY_MAX)));}catch(_){}}
function pushChatHistory(role,text){
  if(!text||typeof text!=='string')return;
  const arr=_loadChatHistory();
  arr.push({role:role,text:text,ts:Date.now()});
  _saveChatHistory(arr);
}
function loadChatHistory(){
  const wrap=document.getElementById('chat-messages');
  if(!wrap)return;
  const arr=_loadChatHistory();
  if(!arr.length)return;
  // Clear "empty state" if present.
  const empty=document.getElementById('chat-empty');
  if(empty)empty.style.display='none';
  arr.forEach(m=>{
    if(!m.text)return;
    // Re-render without re-pushing to history (flag via 4th arg).
    _addChatMessageNoPersist(m.role,m.text);
  });
}
function _addChatMessageNoPersist(role,text){
  // Reuse addChatMessage but skip persist — call with secret 4th arg.
  return addChatMessage(role,text,null,true);
}
function clearChat(){
  if(!confirm('ล้างประวัติแชททั้งหมด?'))return;
  try{localStorage.removeItem(CHAT_HISTORY_KEY);}catch(_){}
  const wrap=document.getElementById('chat-messages');
  if(wrap)wrap.innerHTML='';
  const empty=document.getElementById('chat-empty');
  if(empty)empty.style.display='';
  if(typeof toast==='function')toast('🗑 ล้างประวัติแชทแล้ว');
}

const CHAT_PROFILES = {
  lan:      { name: 'LAN',        url: 'http://pi5-local:8501',         hint: 'ต้องอยู่ใน WiFi เดียวกัน' },
  tailscale:{ name: 'Tailscale',  url: 'http://SET-YOUR-TAILSCALE-IP:8501', hint: 'ต้องเปิด Tailscale บน Pi 5 — แก้ IP ใน Custom หรือ Hermes URL ด้านบน' },
  funnel:   { name: 'Funnel',     url: 'https://pi5.xxx.ts.net',       hint: 'รัน: tailscale funnel 8501' },
  cloudflare:{ name: 'Cloudflare', url: 'https://awiki-hermes.yourdomain.com', hint: 'ผ่าน Cloudflare Tunnel' },
  custom:   { name: 'Custom',     url: '',                              hint: '' }
};
const C = { mode: 'proxy', url: 'http://SET-YOUR-TAILSCALE-IP:8501', key: '', profile: 'tailscale', authToken: '' };
try {
  const saved = JSON.parse(localStorage.getItem('awiki-chat-config') || '{}');
  if (saved.mode) C.mode = saved.mode;
  if (saved.url) C.url = saved.url;
  if (saved.key) C.key = saved.key;
  if (saved.profile) C.profile = saved.profile;
  if (saved.authToken) C.authToken = saved.authToken;
} catch(e) {}

function loadChatSettings() {
  document.querySelectorAll('.chat-mode-opt').forEach(b => b.classList.toggle('active', b.id === 'chat-mode-' + C.mode));
  document.getElementById('chat-direct-cfg').style.display = C.mode === 'direct' ? 'block' : 'none';
  document.getElementById('chat-hermes-url').value = C.url;
  document.getElementById('chat-hermes-key').value = C.key;
  document.getElementById('chat-auth-token').value = C.authToken;
  document.getElementById('chat-test-result').textContent = '';
  document.querySelectorAll('.chat-profile-chip').forEach(c => c.classList.toggle('sel', c.dataset.profile === C.profile));
}

function saveChatSettings() {
  C.mode = document.querySelector('.chat-mode-opt.active')?.id === 'chat-mode-direct' ? 'direct' : 'proxy';
  C.url = document.getElementById('chat-hermes-url').value.trim() || 'http://SET-YOUR-TAILSCALE-IP:8501';
  C.key = document.getElementById('chat-hermes-key').value.trim();
  C.authToken = document.getElementById('chat-auth-token').value.trim();
  localStorage.setItem('awiki-chat-config', JSON.stringify({ mode: C.mode, url: C.url, key: C.key, profile: C.profile, authToken: C.authToken }));
  document.getElementById('chat-test-result').textContent = '✅ Saved';
  document.getElementById('chat-test-result').className = 'chat-test-result ok';
  updateChatStatusBadge();
  ctxToast('Chat settings saved', false);
}

function setChatMode(mode) {
  C.mode = mode;
  document.querySelectorAll('.chat-mode-opt').forEach(b => b.classList.toggle('active', b.id === 'chat-mode-' + mode));
  document.getElementById('chat-direct-cfg').style.display = mode === 'direct' ? 'block' : 'none';
}

function pickChatProfile(profile) {
  C.profile = profile;
  document.querySelectorAll('.chat-profile-chip').forEach(c => c.classList.toggle('sel', c.dataset.profile === profile));
  if (CHAT_PROFILES[profile] && CHAT_PROFILES[profile].url) {
    document.getElementById('chat-hermes-url').value = CHAT_PROFILES[profile].url;
    C.url = CHAT_PROFILES[profile].url;
  }
  if (profile === 'custom') {
    document.getElementById('chat-hermes-url').value = '';
    document.getElementById('chat-hermes-url').focus();
  }
}

async function autoDetectHermes() {
  const result = document.getElementById('chat-test-result');
  result.textContent = '🔍 กำลังค้นหา...';
  result.className = 'chat-test-result';
  const order = ['lan', 'tailscale', 'funnel'];
  for (const key of order) {
    const url = CHAT_PROFILES[key].url;
    if (!url) continue;
    try {
      const resp = await fetch(url + '/health', { method: 'GET', signal: AbortSignal.timeout(3000) });
      if (resp.ok) {
        pickChatProfile(key);
        result.textContent = '✅ เจอ! ' + CHAT_PROFILES[key].name + ' (' + url + ')';
        result.className = 'chat-test-result ok';
        return;
      }
    } catch(e) {}
  }
  result.textContent = '❌ ไม่พบ Hermes — ลองเปิด Funnel หรือตรวจสอบ Pi 5';
  result.className = 'chat-test-result fail';
}

async function testHermesConnection() {
  const url = document.getElementById('chat-hermes-url').value.trim();
  if (!url) { const r = document.getElementById('chat-test-result'); r.textContent = '❌ ใส่ URL ก่อน'; r.className = 'chat-test-result fail'; return; }
  const result = document.getElementById('chat-test-result');
  result.textContent = '⏳ ทดสอบ...';
  result.className = 'chat-test-result';
  const start = Date.now();
  try {
    const resp = await fetch(url + '/health', { method: 'GET', signal: AbortSignal.timeout(5000) });
    const ms = Date.now() - start;
    if (resp.ok) { result.textContent = '✅ Connected! ' + ms + 'ms'; result.className = 'chat-test-result ok'; }
    else { result.textContent = '⚠️ HTTP ' + resp.status + ' — ' + ms + 'ms'; result.className = 'chat-test-result fail'; }
  } catch(e) {
    result.textContent = '❌ ' + (e.name === 'TimeoutError' ? 'หมดเวลา (5s)' : 'เชื่อมต่อไม่ได้');
    result.className = 'chat-test-result fail';
  }
}

function updateChatStatusBadge() {
  const badge = document.getElementById('chat-status');
  if (!badge) return;
  if (C.mode === 'proxy') {
    badge.innerHTML = ''; badge.textContent = '✅ ตอบแล้ว — ' + new Date().toLocaleTimeString('th-TH');
  } else {
    const profile = CHAT_PROFILES[C.profile] || { name: 'Custom' };
    badge.innerHTML = '<span class="chat-status-badge">⚡ Direct: ' + profile.name + '</span>';
  }
}

function ctxToast(msg, isErr) {
  const t = document.getElementById('set-toast');
  t.textContent = msg; t.className = 'set-toast show' + (isErr ? ' err' : '');
  clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('show'), 2500);
}

// ===== CHAT FUNCTIONS (Hermes AI) =====
const HERMES_WEBHOOK = '/api/chat'; // proxied by dashboard server → Hermes
let _chatFiles = [];
let _chatLoading = false;

function onChatFileChange(){
  _chatFiles = Array.from(document.getElementById('chat-file-input').files);
  const badge = document.getElementById('chat-file-count');
  if(_chatFiles.length){
    badge.textContent = _chatFiles.length;
    badge.style.display = 'inline';
  } else {
    badge.style.display = 'none';
  }
}

async function sendChat(){
  if(_chatLoading) return;
  const ta = document.getElementById('chat-textarea');
  const msg = ta.value.trim();
  if(!msg && !_chatFiles.length) return;

  _chatLoading = true;
  document.getElementById('chat-send-btn').disabled = true;
  ta.value = '';
  document.getElementById('chat-empty').style.display = 'none';

  addChatMessage('user', msg, _chatFiles.map(f => f.name));
  const loadId = addChatLoading();
  const statusEl = document.getElementById('chat-status');
  statusEl.textContent = '🧠 Hermes กำลังคิด... (ค้นจาก A-Wiki Brain)';

  try {
    let resp, data;

    if (C.mode === 'direct') {
      const body = JSON.stringify({
        messages: [
          { role: 'system', content: 'You are Hermes, an AI assistant with access to the A-Wiki knowledge base (605+ wiki pages at ~/A-Wiki/wiki/). Use the terminal to search the wiki before answering: `python3 ~/A-Wiki/scripts/search-wiki.py "query"`. For IoT/ESP32/MQTT questions, search wiki/entities/iot/ and wiki/concepts/iot/. For pharmacy questions, search wiki/entities/pharmacy/. Always cite wiki sources. Respond in Thai (ภาษาไทย) unless the user asks in English.' },
          { role: 'user', content: msg }
        ],
        stream: false,
        max_tokens: 4000
      });
      const headers = { 'Content-Type': 'application/json' };
      if (C.key) headers['Authorization'] = 'Bearer ' + C.key;
      else if (C.authToken) headers['Authorization'] = 'Bearer ' + C.authToken;

      resp = await fetch(C.url + '/v1/chat/completions', {
        method: 'POST', headers, body, signal: AbortSignal.timeout(120000)
      });

      removeChatLoading(loadId);

      if (!resp.ok) {
        const err = await resp.text();
        addChatMessage('hermes', '⚠️ Hermes ตอบกลับไม่สำเร็จ\n\nโหมด: Direct (' + (CHAT_PROFILES[C.profile]?.name || 'Custom') + ')\nURL: ' + C.url + '\n' + (err || 'HTTP ' + resp.status));
        statusEl.textContent = '❌ Error: ' + resp.status;
      } else {
        data = await resp.json();
        addChatMessage('hermes', data.choices?.[0]?.message?.content || JSON.stringify(data));
        statusEl.innerHTML = '';
        updateChatStatusBadge();
      }
    } else {
      const formData = new FormData();
      formData.append('prompt', msg);
      _chatFiles.forEach(f => formData.append('files', f));

      const fetchOpts = { method: 'POST', body: formData };
      if (C.authToken) fetchOpts.headers = { 'Authorization': 'Bearer ' + C.authToken };

      resp = await fetch(HERMES_WEBHOOK, fetchOpts);

      removeChatLoading(loadId);

      if (resp.status === 202) {
        const qdata = await resp.json();
        addChatMessage('hermes', '⏳ **คิวเต็ม** — คุณอยู่ในคิวลำดับที่ ' + qdata.position + '\n\nระบบกำลังประมวลผล request อื่นอยู่ กรุณารอสักครู่แล้วลองใหม่');
        statusEl.textContent = '⏳ คิวลำดับที่ ' + qdata.position + ' — ลองใหม่ใน 5 วิ';
      } else if (!resp.ok) {
        const err = await resp.text();
        addChatMessage('hermes', '⚠️ Hermes server ตอบกลับไม่สำเร็จ: ' + (err || resp.status));
        statusEl.textContent = '❌ Error: ' + resp.status;
      } else {
        data = await resp.json();
        addChatMessage('hermes', data.response || data.text || data.message || JSON.stringify(data));
        statusEl.textContent = '✅ ตอบแล้ว — ' + new Date().toLocaleTimeString('th-TH');
      }
    }
  } catch(e) {
    removeChatLoading(loadId);
    if (e.name === 'TimeoutError' || e.name === 'AbortError') {
      addChatMessage('hermes', '⏰ **หมดเวลา** — Hermes ใช้เวลาคิดนานเกินไป (120s)\nลองถามใหม่ด้วยคำถามที่สั้นลง');
    } else if (C.mode === 'direct') {
      addChatMessage('hermes', '🔌 **เชื่อมต่อ Hermes ไม่ได้**\n\nโหมด: Direct (' + (CHAT_PROFILES[C.profile]?.name || 'Custom') + ')\nURL: ' + C.url + '\n\nตรวจสอบ:\n• Pi 5 เปิดอยู่\n• ' + (CHAT_PROFILES[C.profile]?.hint || 'URL ถูกต้อง'));
    } else {
      addChatMessage('hermes', '⚠️ ไม่สามารถเชื่อมต่อ Hermes Server ได้\n\nตรวจสอบว่า:\n• Pi 5 เปิดอยู่และ Tailscale เชื่อมต่อ\n• Hermes Gateway รันอยู่ (port 8644)\n• `dashboard-ensure.sh` รัน proxy ถูกต้อง');
    }
    statusEl.textContent = '🔌 ไม่สามารถเชื่อมต่อ';
  }

  _chatFiles = [];
  document.getElementById('chat-file-input').value = '';
  document.getElementById('chat-file-count').style.display = 'none';
  _chatLoading = false;
  document.getElementById('chat-send-btn').disabled = false;
  ta.focus();
}

function addChatMessage(role, text, files, _skipPersist){
  const wrap = document.getElementById('chat-messages');
  // D15: persist to localStorage unless explicitly skipped (e.g. loading history).
  if(!_skipPersist && role && text)pushChatHistory(role,text);
  const div = document.createElement('div');
  div.className = 'chat-msg ' + role;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'user' ? '👤' : '🧠';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';

  // Simple markdown-like rendering
  let html = text
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');

  if(files && files.length){
    html = '<div>' + files.map(f => '<span class="chat-file-badge">📎 ' + f + '</span>').join('') + '</div>' + html;
  }

  bubble.innerHTML = html;

  const time = document.createElement('div');
  time.className = 'msg-time';
  time.textContent = new Date().toLocaleTimeString('th-TH', {hour:'2-digit',minute:'2-digit'});

  div.append(avatar, bubble);
  wrap.appendChild(div);

  // Scroll to bottom
  wrap.scrollTop = wrap.scrollHeight;
  return div;
}

function addChatLoading(){
  const wrap = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-msg hermes';
  div.id = 'msg-loading';
  div.innerHTML = '<div class=\"msg-avatar\" style=\"background:linear-gradient(135deg,var(--accent-brand),var(--accent-violet))\">🧠</div><div class=\"msg-loading busy\"><div class=\"dot\"></div><div class=\"dot\"></div><div class=\"dot\"></div></div>';
  wrap.appendChild(div);
  wrap.scrollTop = wrap.scrollHeight;
  return 'msg-loading';
}

function removeChatLoading(id){
  const el = document.getElementById(id);
  if(el) el.remove();
}

function quickAsk(q){
  document.getElementById('chat-textarea').value = q;
  sendChat();
}

// ===== ADMIN PANEL =====
async function loadAdminPanel() {
  try {
    // Load stats
    const statsResp = await fetch('/api/auth/stats');
    const stats = await statsResp.json();
    const statsEl = document.getElementById('admin-stats');
    if (stats.tokens_configured === 0) {
      statsEl.innerHTML = '<em>Auth disabled — no tokens configured</em>';
    } else {
      const rows = (stats.usage || []).map(u =>
        '<div style="padding:2px 0">👤 <b>' + (u.name || u.token) + '</b> — ' + u.count + ' requests, last: ' + new Date(u.last_seen * 1000).toLocaleTimeString('th-TH') + '</div>'
      ).join('');
      statsEl.innerHTML = '<div>🔑 ' + stats.tokens_configured + ' tokens configured</div>' + (rows || '<em>ยังไม่มีคนใช้งาน</em>');
    }

    // Load history
    const histResp = await fetch('/api/chat/history?limit=20');
    const hist = await histResp.json();
    const histEl = document.getElementById('admin-history');
    if (hist.history && hist.history.length) {
      histEl.innerHTML = hist.history.map(h =>
        '<div style="padding:4px 0;border-bottom:1px solid var(--border)">' +
        '<b>' + (h.user || '?') + '</b> <span style="color:var(--text-tertiary)">' + new Date(h.ts * 1000).toLocaleTimeString('th-TH') + '</span><br>' +
        '<span style="color:var(--accent-brand)">Q:</span> ' + h.message.substring(0, 120) + '<br>' +
        '<span style="color:var(--accent-success)">A:</span> ' + (h.response || '').substring(0, 200) +
        '</div>'
      ).join('');
    } else {
      histEl.innerHTML = '<em>ยังไม่มีประวัติแชท</em>';
    }
  } catch(e) {
    document.getElementById('admin-stats').textContent = 'โหลดข้อมูลไม่ได้';
  }
}

async function adminAddToken() {
  const inp = document.getElementById('admin-new-token');
  const tok = inp.value.trim();
  const res = document.getElementById('admin-result');
  if (!tok) { res.textContent = '❌ ใส่ token ก่อน'; return; }
  res.textContent = '⏳ กำลังเพิ่ม...';
  try {
    const r = await fetch('/api/admin/tokens/add', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: tok })
    });
    const data = await r.json();
    if (data.ok) { res.textContent = '✅ เพิ่ม token แล้ว'; inp.value = ''; loadAdminPanel(); }
    else res.textContent = '❌ ' + (data.error || 'ไม่สำเร็จ');
  } catch(e) { res.textContent = '❌ เชื่อมต่อไม่ได้'; }
}

async function adminRemoveToken() {
  const inp = document.getElementById('admin-del-token');
  const tok = inp.value.trim();
  const res = document.getElementById('admin-result');
  if (!tok) { res.textContent = '❌ ใส่ token ก่อน'; return; }
  res.textContent = '⏳ กำลังลบ...';
  try {
    const r = await fetch('/api/admin/tokens/remove', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: tok })
    });
    const data = await r.json();
    if (data.ok) { res.textContent = '✅ ลบ token แล้ว'; inp.value = ''; loadAdminPanel(); }
    else res.textContent = '❌ ' + (data.error || 'ไม่สำเร็จ');
  } catch(e) { res.textContent = '❌ เชื่อมต่อไม่ได้'; }
}


// CHUNK D15: boot hook — restore chat history on dashboard load.
try{loadChatHistory();}catch(_){}
