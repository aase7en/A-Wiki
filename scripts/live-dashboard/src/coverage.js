// === COVERAGE VIEW — registry health metrics from /api/coverage ===
const COVERAGE_FIELD_LABELS={
  th_description:'คำอธิบายไทย',
  when_to_use:'ใช้เมื่อไหร่',
  examples:'ตัวอย่าง',
  process_steps:'ขั้นตอน (workflow)',
  invocation_hint:'invocation_hint',
  invocation:'invocation enum'
};
function coverageBarColor(pct){
  if(pct>=90)return 'var(--accent-green)';
  if(pct>=60)return 'var(--accent-warn)';
  return 'var(--accent-danger)';
}
function coverageRenderOverall(container,data){
  // Big horizontal bars — one per tracked field, sorted by coverage asc (worst first).
  const fields=Object.keys(COVERAGE_FIELD_LABELS);
  const rows=fields.map(f=>({f,label:COVERAGE_FIELD_LABELS[f],pct:data.overall[f]||0}))
    .sort((a,b)=>a.pct-b.pct);
  container.innerHTML=rows.map(r=>`
    <div style="margin-bottom:10px">
      <div style="display:flex;justify-content:space-between;font-size:var(--fs-2xs);margin-bottom:3px">
        <span style="color:var(--text-secondary)">${r.label}</span>
        <span style="color:${coverageBarColor(r.pct)};font-weight:600">${r.pct.toFixed(1)}%</span>
      </div>
      <div style="height:8px;background:var(--elev-3,#1a1a2e);border-radius:4px;overflow:hidden">
        <div style="height:100%;width:${r.pct}%;background:${coverageBarColor(r.pct)};transition:width .4s"></div>
      </div>
    </div>`).join('');
}
function coverageRenderHeatmap(container,buckets,labelFn){
  // Compact heatmap: rows=entities, cols=fields, cell color by %.
  const fields=Object.keys(COVERAGE_FIELD_LABELS);
  const entities=Object.keys(buckets).sort();
  if(!entities.length){container.innerHTML='<p style="color:var(--text-disabled);font-size:var(--fs-2xs)">ไม่มีข้อมูล</p>';return;}
  let html='<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:var(--fs-2xs)"><thead><tr>';
  html+='<th style="text-align:left;padding:4px 6px;color:var(--text-tertiary);font-weight:500;border-bottom:1px solid var(--border)"></th>';
  for(const f of fields){
    html+=`<th style="text-align:center;padding:4px 3px;color:var(--text-tertiary);font-weight:500;border-bottom:1px solid var(--border);writing-mode:vertical-rl;transform:rotate(180deg);height:60px">${COVERAGE_FIELD_LABELS[f]}</th>`;
  }
  html+='</tr></thead><tbody>';
  for(const e of entities){
    const b=buckets[e];
    html+=`<tr><td style="padding:4px 6px;color:var(--text-secondary);white-space:nowrap;font-weight:500">${labelFn(e)}</td>`;
    for(const f of fields){
      const pct=b[f]||0;
      const color=coverageBarColor(pct);
      // Cell background opacity scales with coverage.
      const opacity=pct>=90?0.55:pct>=60?0.4:0.3;
      html+=`<td style="text-align:center;padding:2px"><div title="${e} · ${COVERAGE_FIELD_LABELS[f]}: ${pct.toFixed(0)}%" style="background:${color}${Math.round(opacity*255).toString(16).padStart(2,'0')};color:var(--text-primary);padding:4px 5px;border-radius:3px;min-width:30px;font-weight:600;font-size:10px">${pct.toFixed(0)}</div></td>`;
    }
    html+='</tr>';
  }
  html+='</tbody></table></div>';
  container.innerHTML=html;
}
function coverageRenderMissing(container,data){
  // Show fields that still have missing entries (sorted by missing count desc).
  const fields=Object.keys(COVERAGE_FIELD_LABELS);
  const rows=fields.map(f=>({f,label:COVERAGE_FIELD_LABELS[f],missing:data.missing[f]||[]}))
    .filter(r=>r.missing.length>0)
    .sort((a,b)=>b.missing.length-a.missing.length);
  if(!rows.length){container.innerHTML='<p style="color:var(--accent-green);font-size:var(--fs-2xs)">✅ ครบทุก field แล้ว</p>';return;}
  container.innerHTML=rows.map(r=>{
    const preview=r.missing.slice(0,8).map(n=>`<span class="skill-tag" style="cursor:pointer;font-size:10px;border-color:var(--accent-brand);color:var(--accent-brand)" onclick="coverageEditInline('${n}','${r.f}')" title="คลิกเพื่อแก้ ${r.label}">${n} ✏️</span>`).join(' ');
    const extra=r.missing.length>8?`<span style="color:var(--text-tertiary);font-size:10px">+${r.missing.length-8} อื่นๆ</span>`:'';
    return `<div style="margin-bottom:10px">
      <div style="display:flex;justify-content:space-between;font-size:var(--fs-2xs);margin-bottom:4px">
        <span style="color:var(--text-secondary)">${r.label}</span>
        <span style="color:var(--accent-warn);font-weight:600">ขาด ${r.missing.length}</span>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:3px">${preview}${extra}</div>
    </div>`;
  }).join('');
}
// === CHUNK W — Coverage inline editor ===
let _covEditField=null;
function coverageEditInline(name,field){
  const bd=$('compare-backdrop'),modal=$('compare-modal'); // reuse compare modal containers
  if(!bd||!modal){toast('modal ไม่พร้อม','err');return;}
  const fieldLabels={th_description:'คำอธิบายไทย',when_to_use:'ใช้เมื่อไหร่',invocation_hint:'invocation hint'};
  bd.style.display='block';
  modal.style.display='block';
  modal.innerHTML=`
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
      <h3 style="margin:0;font-size:var(--fs-md);color:var(--accent-brand)">✏️ แก้ ${fieldLabels[field]||field}</h3>
      <button onclick="closeCompareModal()" style="background:transparent;border:none;color:var(--text-tertiary);font-size:18px;cursor:pointer">✕</button>
    </div>
    <div style="font-family:var(--font-mono);font-size:var(--fs-xs);color:var(--text-tertiary);margin-bottom:8px">${name}</div>
    <textarea id="cov-edit-textarea" style="width:100%;min-height:120px;background:var(--elev-2);border:1px solid var(--border2);border-radius:var(--r-md);color:var(--text-primary);padding:10px;font-size:var(--fs-sm);font-family:inherit;resize:vertical" placeholder="พิมพ์ ${fieldLabels[field]||field}..."></textarea>
    <div id="cov-edit-status" style="font-size:var(--fs-2xs);color:var(--text-tertiary);margin-top:6px"></div>
    <div style="display:flex;gap:8px;margin-top:12px;justify-content:flex-end">
      <button class="set-btn sm" onclick="coverageOpenSkill('${name}')" style="color:var(--text-tertiary)">📂 เปิดใน Skills tab</button>
      <button class="set-btn sm" onclick="closeCompareModal()" style="color:var(--text-tertiary)">ยกเลิก</button>
      <button class="set-btn sm" onclick="coverageEditSave('${name}','${field}')" style="background:var(--accent-brand);color:var(--elev-0);font-weight:600">💾 บันทึก</button>
    </div>`;
}
async function coverageEditSave(name,field){
  const ta=$('cov-edit-textarea');
  const status=$('cov-edit-status');
  if(!ta)return;
  const value=ta.value.trim();
  if(!value){status.textContent='⚠️ ไม่สามารถเว้นว่างได้';status.style.color='var(--accent-warn)';return;}
  if(value.length>2000){status.textContent='⚠️ ยาวเกินไป (สูงสุด 2000 ตัวอักษร)';status.style.color='var(--accent-warn)';return;}
  status.textContent='⏳ กำลังบันทึก...';status.style.color='var(--text-tertiary)';
  try{
    const r=await fetch('/api/skills/'+encodeURIComponent(name)+'/edit',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({field:field,value:value})
    }).then(r=>r.json());
    if(r.ok){
      closeCompareModal();
      toast('✅ บันทึก '+field+' สำหรับ '+name);
      coverageLoad(); // refresh coverage stats
    }else{
      status.textContent='❌ '+(r.error||'บันทึกล้มเหลว');status.style.color='var(--accent-danger)';
    }
  }catch(e){
    status.textContent='❌ '+e.message;status.style.color='var(--accent-danger)';
  }
}
function coverageOpenSkill(name){
  // Switch to Skills view + open detail drawer for that skill.
  setView('skills');
  setTimeout(()=>skillsOpenDetail(name),250);
}
let _covCache=null;
async function coverageLoad(){
  const overall=$('coverage-overall'),sub=$('coverage-subtitle');
  if(overall){overall.innerHTML='<div style="text-align:center;color:var(--text-tertiary);padding:20px;font-size:var(--fs-2xs)">⏳ กำลังโหลด...</div>';}
  try{
    const data=await fetch('/api/coverage').then(r=>r.json());
    if(data.error)throw new Error(data.error);
    _covCache=data;
    if(sub){sub.textContent=`${data.total} canonical skills · ติดตาม ${data.fields.length} fields`;}
    coverageRenderOverall($('coverage-overall'),data);
    coverageRenderHeatmap($('coverage-by-domain'),data.by_domain,x=>`📂 ${x}`);
    coverageRenderHeatmap($('coverage-by-agent'),data.by_agent,x=>`🤖 ${x.charAt(0).toUpperCase()+x.slice(1)}`);
    coverageRenderHeatmap($('coverage-by-phase'),data.by_phase,x=>{
      const phaseNames={define:'Define',plan:'Plan',build:'Build',verify:'Verify',review:'Review',ship:'Ship',meta:'Meta',none:'—'};
      return `🔄 ${phaseNames[x]||x}`;
    });
    coverageRenderMissing($('coverage-missing'),data);
    // CHUNK VV: load review queue alongside.
    reviewQueueLoad();
    // Populate comparison dropdowns if empty.
    const selA=$('cov-cmp-a'),selB=$('cov-cmp-b');
    if(selA&&selA.options.length===0){
      const agents=Object.keys(data.by_agent||{});
      for(const sel of [selA,selB]){
        for(const a of agents){
          const o=document.createElement('option');o.value=a;o.textContent=a;sel.appendChild(o);
        }
      }
      if(agents.length>=2){selA.value=agents[0];selB.value=agents[1];}
    }
  }catch(e){
    if(overall){overall.innerHTML=`<div style="color:var(--accent-danger);font-size:var(--fs-2xs)">❌ ${e.message}</div>`;}
  }
}
// === CHUNK VV — Review Queue (low-health skills, fix-tracked) ===
const REVIEW_DONE_KEY='awiki-review-done';
async function reviewQueueLoad(){
  const list=$('review-queue-list'),count=$('review-queue-count'),prog=$('review-queue-progress');
  if(!list)return;
  const thrSel=$('review-threshold');
  const threshold=thrSel?parseInt(thrSel.value,10):60;
  list.innerHTML='<div style="color:var(--text-tertiary);font-size:var(--fs-2xs);padding:8px">⏳ กำลังโหลด...</div>';
  try{
    const r=await fetch('/api/skills/review?threshold='+threshold).then(r=>r.json());
    const queue=r.queue||[];
    count.textContent='('+queue.length+' skills)';
    if(!queue.length){list.innerHTML='<div style="color:var(--accent-success);font-size:var(--fs-2xs);padding:8px">✅ ไม่มี skills ที่ต่ำกว่า threshold — ดีมาก!</div>';prog.innerHTML='';return;}
    const done=_lsGet(REVIEW_DONE_KEY,[]);
    const doneCount=queue.filter(s=>done.includes(s.name)).length;
    prog.innerHTML=`<div style="font-size:var(--fs-2xs);color:var(--text-tertiary);margin-bottom:4px">ทำเสร็จ ${doneCount}/${queue.length}</div><div style="height:6px;background:var(--elev-2);border-radius:3px;overflow:hidden"><div style="height:100%;width:${queue.length?(doneCount/queue.length*100):0}%;background:var(--accent-success);transition:width .3s"></div></div>`;
    list.innerHTML=queue.map(s=>{
      const isDone=done.includes(s.name);
      const lvlColor=s.level==='critical'?'var(--accent-danger)':s.level==='weak'?'var(--accent-warm)':'var(--text-tertiary)';
      return `<div style="display:flex;align-items:center;gap:8px;padding:8px;border:1px solid var(--border2);border-radius:var(--r-md);background:${isDone?'var(--elev-1)':'var(--elev-2)'};margin-bottom:6px;${isDone?'opacity:.6':''}">
        <input type="checkbox" ${isDone?'checked':''} onchange="toggleReviewDone('${s.name}',this.checked)" style="cursor:pointer;accent-color:var(--accent-success)" title="ทำเสร็จ">
        <div style="flex:1;cursor:pointer" onclick="setView('skills');setTimeout(()=>skillsOpenDetail('${s.name}'),300)">
          <div style="color:var(--text-primary);font-weight:600;${isDone?'text-decoration:line-through':''}">${s.name}</div>
          <div style="font-size:var(--fs-2xs);color:var(--text-tertiary)">ขาด ${(s.missing||[]).length} fields · ${(s.domain||[]).join(', ')||'-'}</div>
        </div>
        <span class="skill-tag" style="border-color:${lvlColor};color:${lvlColor};font-size:var(--fs-2xs)">${s.level} ${s.score}</span>
        <button class="set-btn sm" onclick="coverageEditInline('${s.name}','${(s.missing||[])[0]||'th_description'}')" style="padding:3px 8px;font-size:var(--fs-2xs);color:var(--accent-brand)" title="แก้ไข field ที่ขาด">✏️</button>
      </div>`;
    }).join('');
  }catch(e){list.innerHTML='<div style="color:var(--accent-danger);font-size:var(--fs-2xs);padding:8px">⚠️ '+e.message+'</div>';}
}
function toggleReviewDone(name,done){
  const arr=_lsGet(REVIEW_DONE_KEY,[]);
  if(done){if(!arr.includes(name))arr.push(name);}
  else{const i=arr.indexOf(name);if(i>=0)arr.splice(i,1);}
  _lsSet(REVIEW_DONE_KEY,arr);
  reviewQueueLoad();  // refresh progress bar
}
async function coverageCompare(){
  const a=$('cov-cmp-a').value,b=$('cov-cmp-b').value;
  const out=$('coverage-compare');
  if(!a||!b){out.innerHTML='<p style="color:var(--text-disabled);font-size:var(--fs-2xs)">เลือก agent 2 ตัว</p>';return;}
  out.innerHTML='<div style="color:var(--text-tertiary);font-size:var(--fs-2xs);padding:8px">⏳ กำลังเปรียบเทียบ...</div>';
  try{
    const data=await fetch('/api/coverage?compare='+encodeURIComponent(a+','+b)).then(r=>r.json());
    const diff=data.diff;
    if(!diff){out.innerHTML='<p style="color:var(--text-disabled);font-size:var(--fs-2xs)">ไม่มีข้อมูล diff</p>';return;}
    const onlyA=diff.only_a||[],onlyB=diff.only_b||[];
    out.innerHTML=`
      <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:10px">
        <div style="text-align:center"><div style="font-size:var(--fs-lg);font-weight:700;color:var(--accent-success)">${diff.shared}</div><div style="font-size:var(--fs-2xs);color:var(--text-tertiary)">shared</div></div>
        <div style="text-align:center"><div style="font-size:var(--fs-lg);font-weight:700;color:var(--accent-warn)">${diff.only_a_count}</div><div style="font-size:var(--fs-2xs);color:var(--text-tertiary)">เฉพาะ ${diff.agent_a}</div></div>
        <div style="text-align:center"><div style="font-size:var(--fs-lg);font-weight:700;color:var(--accent-cool)">${diff.only_b_count}</div><div style="font-size:var(--fs-2xs);color:var(--text-tertiary)">เฉพาะ ${diff.agent_b}</div></div>
      </div>
      ${onlyA.length?`<div style="margin-bottom:8px"><div style="font-size:var(--fs-2xs);color:var(--accent-warn);margin-bottom:4px">เฉพาะ ${diff.agent_a} (${onlyA.length}):</div><div style="display:flex;flex-wrap:wrap;gap:3px">${onlyA.slice(0,15).map(n=>`<span class="skill-tag" style="cursor:pointer;font-size:10px" onclick="coverageOpenSkill('${n}')">${n}</span>`).join('')}</div></div>`:''}
      ${onlyB.length?`<div><div style="font-size:var(--fs-2xs);color:var(--accent-cool);margin-bottom:4px">เฉพาะ ${diff.agent_b} (${onlyB.length}):</div><div style="display:flex;flex-wrap:wrap;gap:3px">${onlyB.slice(0,15).map(n=>`<span class="skill-tag" style="cursor:pointer;font-size:10px" onclick="coverageOpenSkill('${n}')">${n}</span>`).join('')}</div></div>`:''}
    `;
  }catch(e){out.innerHTML=`<div style="color:var(--accent-danger);font-size:var(--fs-2xs)">❌ ${e.message}</div>`;}
}
async function simulateSkill(name){
// Fetch full skill detail (process_steps may already be in detail view, but refetch to be safe)
try{
const s=await fetch('/api/skills/'+encodeURIComponent(name)).then(r=>r.json());
if(!s||s.error||!(s.process_steps||[]).length){
toast('Skill นี้ไม่มี process_steps สำหรับ simulation','err');return;
}
_simSteps=s.process_steps;_simIdx=-1;_simCurrentName=s.name;
$('sim-title').textContent='🎬 '+s.name;
$('sim-subtitle').textContent=s.th_description?s.th_description.slice(0,100):'';
$('sim-explain').className='empty';$('sim-explain').textContent='กด ▶ เริ่มเพื่อดู '+_simSteps.length+' ขั้นตอน';
$('sim-progress').style.width='0%';
// Render stations
$('sim-stations').innerHTML=_simSteps.map((st,i)=>`
<div class="sim-station" data-i="${i}">
<div class="sim-core">${SIM_ICONS[i%SIM_ICONS.length]}</div>
<div class="sim-num">${String(i+1).padStart(2,'0')}</div>
<div class="sim-label">${st.length>40?st.slice(0,37)+'...':st}</div>
</div>`).join('');
$('sim-backdrop').classList.add('show');
// Show copy-link for single-skill sim too (copies ?skill=<name>).
const copyBtn=$('sim-copy-link');if(copyBtn)copyBtn.style.display='inline-flex';
}catch(e){toast('โหลด skill ไม่ได้: '+e.message,'err');}
}
function simPlay(){
if(_simTimer){clearInterval(_simTimer);_simTimer=null;return;}
if(_simIdx>=_simSteps.length-1)_simIdx=-1; // replay
_simTimer=setInterval(simStep,2200);
simStep();
}
function simStep(){
if(!_simSteps.length)return;
_simIdx++;
if(_simIdx>=_simSteps.length){
if(_simTimer){clearInterval(_simTimer);_simTimer=null;}
$('sim-explain').className='';$('sim-explain').innerHTML='✅ <b>เสร็จสิ้น!</b> ครบ '+_simSteps.length+' ขั้นตอน';
return;
}
// Update stations
document.querySelectorAll('.sim-station').forEach((el,i)=>{
el.classList.toggle('active',i===_simIdx);
el.classList.toggle('done',i<_simIdx);
});
// Progress bar
$('sim-progress').style.width=((_simIdx+1)/_simSteps.length*100)+'%';
// Explanation
$('sim-explain').className='';
$('sim-explain').innerHTML=`<b style="color:var(--accent-brand)">ขั้นที่ ${_simIdx+1}/${_simSteps.length}:</b> ${_simSteps[_simIdx]}`;
}
function simReset(){
if(_simTimer){clearInterval(_simTimer);_simTimer=null;}
_simIdx=-1;
document.querySelectorAll('.sim-station').forEach(el=>{el.classList.remove('active','done');});
$('sim-progress').style.width='0%';
$('sim-explain').className='empty';$('sim-explain').textContent='กด ▶ เริ่มเพื่อดู '+_simSteps.length+' ขั้นตอน';
}
function simClose(e){
if(e&&e.target&&e.target.id!=='sim-backdrop'&&e.type==='click')return;
if(_simTimer){clearInterval(_simTimer);_simTimer=null;}
$('sim-backdrop').classList.remove('show');
// Reset deep-link state.
const copyBtn=$('sim-copy-link');if(copyBtn)copyBtn.style.display='none';
_wfCurrentId=null;_simCurrentName=null;
_wfRestore();
}

// === CHUNK L — Simulation export (SVG + PNG) ===
// Generates a reproducible SVG from step DATA (not DOM capture) so the output
// is clean, re-renderable, and theme-independent.
function _simExportData(){
// Returns {title, subtitle, steps:[{icon,label,num}]} or null if no sim active.
if(_wfCurrentId&&_wfSteps.length){
return{
title:_wfMeta.title_th||_wfCurrentId,
subtitle:_wfMeta.summary_th||'',
steps:_wfSteps.map((st,i)=>({icon:st.icon||'⚙️',label:st.label_th||st.skill||('Step '+(i+1)),num:i+1})),
};
}
if(_simCurrentName&&_simSteps.length){
return{
title:_simCurrentName,
subtitle:'',
steps:_simSteps.map((st,i)=>({icon:'⚙️',label:st.length>50?st.slice(0,47)+'...':st,num:i+1})),
};
}
return null;
}
function _buildSimSVG(d){
const W=1400,padX=40,padY=60,boxW=180,boxH=90,gap=40;
const totalW=d.steps.length*boxW+(d.steps.length-1)*gap;
const svgW=Math.max(W,totalW+padX*2);
const svgH=boxH+padY*2+60;
const startX=padX;
const boxY=padY+50;
let boxes='';
d.steps.forEach((st,i)=>{
const x=startX+i*(boxW+gap);
const cx=x+boxW/2;
const numColor='#5eead4';
const label=st.label.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const icon=st.icon;
boxes+=`<rect x="${x}" y="${boxY}" width="${boxW}" height="${boxH}" rx="10" fill="#14142a" stroke="#26265a" stroke-width="1.5"/>`;
boxes+=`<circle cx="${cx}" cy="${boxY+22}" r="14" fill="#1e1e3a" stroke="${numColor}" stroke-width="1.5"/>`;
boxes+=`<text x="${cx}" y="${boxY+26}" text-anchor="middle" font-family="monospace" font-size="12" fill="${numColor}" font-weight="bold">${st.num}</text>`;
boxes+=`<text x="${cx}" y="${boxY+52}" text-anchor="middle" font-family="sans-serif" font-size="22">${icon}</text>`;
// Wrap label to 2 lines if needed
const maxChars=22;
if(label.length>maxChars){
const cut=label.lastIndexOf(' ',maxChars);
const split=cut>10?cut:maxChars;
const l1=label.slice(0,split);
const l2=label.slice(split).trim().slice(0,maxChars);
boxes+=`<text x="${cx}" y="${boxY+72}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#cbd5e1">${l1}</text>`;
boxes+=`<text x="${cx}" y="${boxY+84}" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#94a3b8">${l2}</text>`;
}else{
boxes+=`<text x="${cx}" y="${boxY+78}" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#cbd5e1">${label}</text>`;
}
});
// Arrows between boxes
let arrows='';
for(let i=0;i<d.steps.length-1;i++){
const x1=startX+i*(boxW+gap)+boxW;
const x2=startX+(i+1)*(boxW+gap);
const y=boxY+boxH/2;
arrows+=`<line x1="${x1}" y1="${y}" x2="${x2-6}" y2="${y}" stroke="#3a3a6a" stroke-width="2"/>`;
arrows+=`<polygon points="${x2-6},${y-5} ${x2},${y} ${x2-6},${y+5}" fill="#3a3a6a"/>`;
}
// Title + subtitle
const titleEsc=d.title.replace(/&/g,'&amp;').replace(/</g,'&lt;');
const subEsc=(d.subtitle||'').replace(/&/g,'&amp;').replace(/</g,'&lt;');
let header=`<text x="${padX}" y="30" font-family="monospace" font-size="18" font-weight="bold" fill="#5eead4">${titleEsc}</text>`;
if(d.subtitle)header+=`<text x="${padX}" y="48" font-family="sans-serif" font-size="12" fill="#94a3b8">${subEsc.slice(0,120)}</text>`;
return `<svg xmlns="http://www.w3.org/2000/svg" width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}"><rect width="100%" height="100%" fill="#06060d"/>${header}${arrows}${boxes}<text x="${svgW-padX}" y="${svgH-15}" text-anchor="end" font-family="sans-serif" font-size="10" fill="#475569">A-Wiki · ${d.steps.length} steps · ${new Date().toISOString().slice(0,10)}</text></svg>`;
}
function simExportSVG(){
const d=_simExportData();
if(!d){toast('ไม่มีขั้นตอนสำหรับ export — เปิด simulation ก่อน','err');return;}
const svg=_buildSimSVG(d);
const blob=new Blob([svg],{type:'image/svg+xml'});
const url=URL.createObjectURL(blob);
const a=document.createElement('a');
a.href=url;a.download=`${d.title.replace(/[^a-z0-9-]/gi,'_')}.svg`;
document.body.appendChild(a);a.click();document.body.removeChild(a);
setTimeout(()=>URL.revokeObjectURL(url),1000);
toast('📥 ดาวน์โหลด SVG แล้ว');
}
function simExportPNG(){
const d=_simExportData();
if(!d){toast('ไม่มีขั้นตอนสำหรับ export — เปิด simulation ก่อน','err');return;}
const svg=_buildSimSVG(d);
const img=new Image();
const svgBlob=new Blob([svg],{type:'image/svg+xml'});
const url=URL.createObjectURL(svgBlob);
img.onload=function(){
const canvas=document.createElement('canvas');
canvas.width=img.width*2;canvas.height=img.height*2; // 2x for crisp output
const ctx=canvas.getContext('2d');
ctx.scale(2,2);
ctx.drawImage(img,0,0);
canvas.toBlob(function(blob){
const dl=URL.createObjectURL(blob);
const a=document.createElement('a');
a.href=dl;a.download=`${d.title.replace(/[^a-z0-9-]/gi,'_')}.png`;
document.body.appendChild(a);a.click();document.body.removeChild(a);
setTimeout(()=>URL.revokeObjectURL(dl),1000);
toast('📥 ดาวน์โหลด PNG แล้ว');
},'image/png');
URL.revokeObjectURL(url);
};
img.onerror=function(){URL.revokeObjectURL(url);toast('❌ ไม่สามารถ render PNG ได้','err');};
img.src=url;
}

// ===== WALKTHROUGHS (multi-skill flows) =====
let _walkthroughsLoaded=false;

// ===== COPY INVOCATION (📋 button on skill card) =====
function copyInvocation(hint,name){
  const text=hint||name||'';
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(()=>toast('📋 คัดลอก: '+text),()=>toast('📋 คัดลอกไม่สำเร็จ','err'));
  }else{
    // Fallback for older browsers / non-secure context.
    const ta=document.createElement('textarea');ta.value=text;ta.style.position='fixed';ta.style.opacity='0';
    document.body.appendChild(ta);ta.select();
    try{document.execCommand('copy');toast('📋 คัดลอก: '+text);}catch(e){toast('📋 คัดลอกไม่สำเร็จ','err');}
    document.body.removeChild(ta);
  }
}

