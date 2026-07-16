// ===== CHUNK XX — Usage Analytics Dashboard (Chart.js) =====
const HEALTH_SNAPSHOTS_KEY='awiki-health-snapshots';
const HEALTH_SNAPSHOTS_MAX=90;
let _analyticsCharts={};  // canvasId → Chart instance (destroy before re-render)
function _destroyChart(id){if(_analyticsCharts[id]){try{_analyticsCharts[id].destroy();}catch(_){}delete _analyticsCharts[id];}}
// Persist a daily health snapshot (once per day) for the trend chart.
function _maybeSnapshotHealth(dist){
  try{
    const today=new Date().toISOString().slice(0,10);
    const snaps=_lsGet(HEALTH_SNAPSHOTS_KEY,[]);
    if(snaps.length&&snaps[snaps.length-1].date===today){
      snaps[snaps.length-1]={date:today,dist:dist};
    }else{
      const avg=Math.round((dist.good*85+dist.ok*72+dist.weak*45+dist.critical*15)/Math.max(1,dist.good+dist.ok+dist.weak+dist.critical));
      snaps.push({date:today,dist:dist,avg:avg});
      while(snaps.length>HEALTH_SNAPSHOTS_MAX)snaps.shift();
    }
    _lsSet(HEALTH_SNAPSHOTS_KEY,snaps);
    return snaps;
  }catch(_){return _lsGet(HEALTH_SNAPSHOTS_KEY,[]);}
}
// CHUNK A10: lazy-load chart.js from CDN on first analytics tab open.
// Avoids preloading ~200KB of chart library on dashboard boot.
let _chartJsPromise=null;
function loadChartJs(){
  if(typeof Chart!=='undefined')return Promise.resolve();
  if(_chartJsPromise)return _chartJsPromise;
  _chartJsPromise=new Promise((resolve)=>{
    const s=document.createElement('script');
    s.src='https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js';
    s.onload=()=>resolve();
    s.onerror=()=>{console.warn('chart.js CDN failed to load');resolve();};
    document.head.appendChild(s);
  });
  return _chartJsPromise;
}
async function analyticsLoad(){
  const unavail=$('analytics-unavailable');
  // CHUNK A10: lazy-load chart.js — wait for it before rendering charts.
  await loadChartJs();
  if(typeof Chart==='undefined'){if(unavail)unavail.style.display='block';return;}
  if(unavail)unavail.style.display='none';
  const opens=_lsGet(OPENS_KEY,[]);
  const sub=$('analytics-subtitle');
  if(sub)sub.textContent=`${opens.length} opens บันทึกในเครื่องนี้ · ข้อมูลเฉพาะที่ (ไม่ sync)`;
  // Chart 1: top opened (30d) — reuse trendingSkills.
  const top=trendingSkills(30,10);
  _destroyChart('chart-top-opened');
  _analyticsCharts['chart-top-opened']=new Chart($('chart-top-opened'),{
    type:'bar',
    data:{labels:top.map(t=>t.name),datasets:[{label:'opens',data:top.map(t=>t.count),backgroundColor:'rgba(94,234,212,.6)',borderColor:'rgba(94,234,212,1)',borderWidth:1}]},
    options:{indexAxis:'y',plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,ticks:{color:'#888'}},y:{ticks:{color:'#aaa',font:{size:10}}}}}
  });
  // Chart 2: co-occurrence pairs.
  const co=_mineCoOccurrence();
  const coEdges=co?(co.edges||[]):[];
  coEdges.sort((a,b)=>(b.weight||0)-(a.weight||0));
  const topCo=coEdges.slice(0,10);
  _destroyChart('chart-cooccur');
  _analyticsCharts['chart-cooccur']=new Chart($('chart-cooccur'),{
    type:'bar',
    data:{labels:topCo.map(e=>e.from+' ↔ '+e.to),datasets:[{label:'weight',data:topCo.map(e=>e.weight),backgroundColor:'rgba(167,139,250,.6)',borderColor:'rgba(167,139,250,1)',borderWidth:1}]},
    options:{indexAxis:'y',plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,ticks:{color:'#888'}},y:{ticks:{color:'#aaa',font:{size:9}}}}}
  });
  // Chart 3: opens daily (14d).
  const cutoff=Date.now()-14*24*60*60*1000;
  const dayBuckets={};
  for(let i=13;i>=0;i--){const d=new Date(Date.now()-i*24*60*60*1000).toISOString().slice(0,10);dayBuckets[d]=0;}
  opens.forEach(o=>{if(o.ts>=cutoff){const d=new Date(o.ts).toISOString().slice(0,10);if(d in dayBuckets)dayBuckets[d]++;}});
  const dayLabels=Object.keys(dayBuckets);
  _destroyChart('chart-opens-daily');
  _analyticsCharts['chart-opens-daily']=new Chart($('chart-opens-daily'),{
    type:'line',
    data:{labels:dayLabels.map(d=>d.slice(5)),datasets:[{label:'opens/day',data:dayLabels.map(d=>dayBuckets[d]),borderColor:'rgba(94,234,212,1)',backgroundColor:'rgba(94,234,212,.15)',fill:true,tension:.3}]},
    options:{plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#888',font:{size:9}}},y:{beginAtZero:true,ticks:{color:'#888'}}}}
  });
  // Chart 4a: health distribution (doughnut) — needs skills data.
  let skills=_skillsCache;
  if(!skills.length){
    try{const r=await fetch('/api/skills?limit=500').then(r=>r.json());skills=r.skills||[];}catch(_){}
  }
  const dist={critical:0,weak:0,ok:0,good:0};
  skills.forEach(s=>{if(s.health&&s.health.level)dist[s.health.level]++;});
  const snaps=_maybeSnapshotHealth(dist);
  _destroyChart('chart-health-dist');
  _analyticsCharts['chart-health-dist']=new Chart($('chart-health-dist'),{
    type:'doughnut',
    data:{labels:['critical','weak','ok','good'],datasets:[{data:[dist.critical,dist.weak,dist.ok,dist.good],backgroundColor:['#f87171','#fbbf24','#86efac','#34d399']}]},
    options:{plugins:{legend:{position:'right',labels:{color:'#aaa',font:{size:10}}}}}
  });
  // Chart 4b: health trend (avg over time).
  _destroyChart('chart-health-trend');
  _analyticsCharts['chart-health-trend']=new Chart($('chart-health-trend'),{
    type:'line',
    data:{labels:snaps.map(s=>s.date.slice(5)),datasets:[{label:'avg health',data:snaps.map(s=>s.avg||0),borderColor:'rgba(52,211,153,1)',backgroundColor:'rgba(52,211,153,.15)',fill:true,tension:.3}]},
    options:{plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#888',font:{size:9}}},y:{min:0,max:100,ticks:{color:'#888'}}}}
  });
}

// === EVAL HISTORY PANE — pass@k time series (R3) ===
let _evalChart=null;
async function evalHistoryLoad(){
  const empty=$('eval-empty'),chartEl=$('eval-history-chart'),reg=$('eval-regressions'),sub=$('eval-subtitle');
  if(!chartEl)return;
  if(empty){empty.style.display='block';empty.innerHTML='⏳ กำลังโหลด...';}
  if(reg)reg.style.display='none';
  // CHUNK A10: ensure chart.js is available (lazy-loaded on demand).
  await loadChartJs();
  try{
    const d=await fetch('/api/eval/history').then(r=>r.json());
    if(empty)empty.style.display='none';
    if(sub)sub.textContent=`${d.run_count||0} run(s) · ${d.suite_model_count||0} suite/model line(s)`;
    // Build regression date→pairs index for point styling.
    const regByDate={};
    (d.regressions||[]).forEach(r=>{
      const k=r.date_tag;
      (regByDate[k]=regByDate[k]||[]).push(r.suite+' / '+r.model);
    });
    // Regression banner
    if(reg&&(d.regressions||[]).length){
      const worst=d.regressions.slice(0,5).map(r=>`${r.suite}/${r.model} ${r.prev_pass_at_k}→${r.new_pass_at_k} (Δ${r.delta})`).join(' · ');
      reg.innerHTML='🚨 <b>'+(d.regressions.length)+' regression point(s)</b> — worst: '+worst+((d.regressions.length>5)?' …':'');
      reg.style.display='block';
    }
    const labels=(d.series&&d.series.labels)||[];
    const datasets=((d.series&&d.series.datasets)||[]).map(ds=>{
      // Color: cycle through a palette so lines are distinguishable.
      const palette=['rgba(94,234,212,1)','rgba(129,140,248,1)','rgba(251,191,36,1)','rgba(248,113,113,1)','rgba(52,211,153,1)','rgba(244,114,182,1)','rgba(167,243,208,1)','rgba(253,224,71,1)'];
      const c=palette[Math.abs(hashCode(ds.label))%palette.length];
      return {
        label:ds.label,
        data:ds.data,
        borderColor:c,
        backgroundColor:c.replace('1)','.12)'),
        fill:false,
        tension:.3,
        // Highlight regression points with red rotated-rect markers.
        pointRadius:ds.data.map((v,i)=>{const dt=labels[i];return(dt&&regByDate[dt]&&regByDate[dt].includes(ds.label))?5:3;}),
        pointBackgroundColor:ds.data.map((v,i)=>{const dt=labels[i];return(dt&&regByDate[dt]&&regByDate[dt].includes(ds.label))?'#f87171':c;}),
        pointStyle:ds.data.map((v,i)=>{const dt=labels[i];return(dt&&regByDate[dt]&&regByDate[dt].includes(ds.label))?'rectRot':'circle';}),
        spanGaps:true,
      };
    });
    if(_evalChart){try{_evalChart.destroy();}catch(_){}_evalChart=null;}
    if(!labels.length){
      if(empty){empty.style.display='block';empty.innerHTML='ยังไม่มี eval results — รัน <code>bash scripts/eval/trigger_ci.sh</code> เพื่อเริ่ม collect baseline pass@k';}
      return;
    }
    _evalChart=new Chart(chartEl,{
      type:'line',
      data:{labels:labels.map(l=>l.slice(4)),datasets},  // trim year for compactness
      options:{
        responsive:true,maintainAspectRatio:false,
        plugins:{legend:{position:'bottom',labels:{color:'var(--text-secondary)',font:{size:10},boxWidth:12}}},
        scales:{
          x:{ticks:{color:'#888',font:{size:9},maxRotation:45,minRotation:45}},
          y:{min:0,max:1,ticks:{color:'#888',callback:v=>(v*100).toFixed(0)+'%'}}
        },
        interaction:{mode:'nearest',intersect:false},
      }
    });
  }catch(e){
    if(empty){empty.style.display='block';empty.innerHTML='⚠️ โหลดไม่สำเร็จ: '+String(e);}
  }
}
function hashCode(s){let h=0;for(let i=0;i<s.length;i++){h=((h<<5)-h)+s.charCodeAt(i);h|=0;}return h;}

// === COST HISTORY PANE — USD estimate per run (S6) ===
let _costLineChart=null,_costBarChart=null;
async function costHistoryLoad(){
  const empty=$('cost-empty'),lineEl=$('cost-line-chart'),barEl=$('cost-bar-chart'),sub=$('cost-subtitle'),totalEl=$('cost-total');
  if(!lineEl)return;
  if(empty){empty.style.display='block';empty.innerHTML='⏳ กำลังโหลด...';}
  // CHUNK A10: ensure chart.js is available (lazy-loaded on demand).
  await loadChartJs();
  try{
    const d=await fetch('/api/eval/cost').then(r=>r.json());
    if(empty)empty.style.display='none';
    const runCount=d.run_count||0;
    const totalUsd=(d.total_usd||0).toFixed(4);
    if(sub)sub.textContent=`${runCount} run(s) · ${totalUsd} USD รวม (estimate)`;
    if(totalEl)totalEl.textContent='💰 รวมทุก run: $'+totalUsd;
    const labels=(d.series&&d.series.labels)||[];
    const datasets=((d.series&&d.series.datasets)||[]).map(ds=>{
      const palette=['rgba(251,191,36,1)','rgba(248,113,113,1)','rgba(94,234,212,1)','rgba(129,140,248,1)','rgba(52,211,153,1)','rgba(244,114,182,1)'];
      const c=palette[Math.abs(hashCode(ds.label))%palette.length];
      return {label:ds.label,data:ds.data,borderColor:c,backgroundColor:c.replace('1)','.15)'),fill:true,tension:.3,spanGaps:true};
    });
    if(_costLineChart){try{_costLineChart.destroy();}catch(_){}_costLineChart=null;}
    if(_costBarChart){try{_costBarChart.destroy();}catch(_){}_costBarChart=null;}
    if(!labels.length){
      if(empty){empty.style.display='block';empty.innerHTML='ยังไม่มี eval results พร้อม token counts — รัน CI eval (S6.0+ record tokens) เพื่อเริ่มเก็บ cost data';}
      return;
    }
    // Line chart: USD per run per suite/model
    _costLineChart=new Chart(lineEl,{
      type:'line',
      data:{labels:labels.map(l=>l.slice(4)),datasets},
      options:{responsive:true,maintainAspectRatio:false,
        plugins:{legend:{position:'bottom',labels:{color:'var(--text-secondary)',font:{size:10},boxWidth:12}},tooltip:{callbacks:{label:c=>c.dataset.label+': $'+(c.parsed.y||0).toFixed(4)}}},
        scales:{x:{ticks:{color:'#888',font:{size:9},maxRotation:45,minRotation:45}},y:{min:0,ticks:{color:'#888',callback:v=>'$'+v.toFixed(3)}}}
      }
    });
    // Bar chart: total USD per model (who's most expensive?)
    const summary=d.summary||[];
    if(summary.length&&barEl){
      const sorted=summary.slice(0,10);  // top 10 most expensive
      _costBarChart=new Chart(barEl,{
        type:'bar',
        data:{labels:sorted.map(s=>s.model),datasets:[{label:'total USD',data:sorted.map(s=>s.total_usd),backgroundColor:'rgba(251,191,36,.7)',borderColor:'rgba(251,191,36,1)'}]},
        options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
          plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>'$'+(c.parsed.x||0).toFixed(4)}}},
          scales:{x:{min:0,ticks:{color:'#888',callback:v=>'$'+v.toFixed(3)}},y:{ticks:{color:'#888',font:{size:10}}}}
        }
      });
    }
    // T6: load cost optimization recommendations alongside cost charts
    costOptimizeLoad();
  }catch(e){
    if(empty){empty.style.display='block';empty.innerHTML='⚠️ โหลดไม่สำเร็จ: '+String(e);}
  }
}

// === COST OPTIMIZATION — recommend cheaper good-enough models (T6) ===
async function costOptimizeLoad(){
  const tbl=$('cost-optimize-table'),empty=$('cost-optimize-empty');
  if(!tbl)return;
  try{
    const d=await fetch('/api/eval/cost-optimize').then(r=>r.json());
    const recs=d.recommendations||[];
    if(!recs.length){
      if(empty){empty.style.display='block';empty.innerHTML='ยังไม่มี recommendations — ต้องการ eval results (pass@k) + cost data (tokens)';}
      tbl.style.display='none';
      return;
    }
    if(empty)empty.style.display='none';
    tbl.style.display='block';
    // Render table
    let html='<table style="width:100%;border-collapse:collapse;font-size:var(--fs-2xs)">';
    html+='<tr style="border-bottom:1px solid var(--border2);color:var(--text-tertiary)"><th style="text-align:left;padding:4px">suite</th><th>current</th><th>recommended</th><th>save $</th><th>save %</th><th>status</th></tr>';
    recs.forEach(r=>{
      const isRec=r.status==='recommend';
      const rowStyle=isRec?'background:rgba(52,211,153,.08)':'';
      const statusBadge=isRec?'<span style="color:#34d399">⚡ recommend</span>':('<span style="color:var(--text-tertiary)">'+r.status+'</span>');
      html+=`<tr style="border-bottom:1px solid var(--border2);${rowStyle}">`;
      html+=`<td style="padding:4px">${r.suite||'?'}</td>`;
      html+=`<td style="text-align:center">${r.current_model||'?'}</td>`;
      html+=`<td style="text-align:center">${r.recommended_model||'?'}</td>`;
      html+=`<td style="text-align:center">${(r.savings_usd||0).toFixed(4)}</td>`;
      html+=`<td style="text-align:center">${((r.savings_pct||0)*100).toFixed(1)}%</td>`;
      html+=`<td style="text-align:center">${statusBadge}</td>`;
      html+='</tr>';
    });
    html+='</table>';
    html+='<div style="margin-top:8px;font-size:var(--fs-3xs);color:var(--text-tertiary)">apply ผ่าน CLI: <code>python scripts/eval/apply_cost_optimizer.py --apply</code></div>';
    tbl.innerHTML=html;
  }catch(e){
    if(empty){empty.style.display='block';empty.innerHTML='⚠️ โหลดไม่สำเร็จ: '+String(e);}
  }
  // V3: load cost-optimize audit log alongside recommendations
  costLogLoad();
}

// === COST OPTIMIZE AUDIT LOG — applied swaps history (V3) ===
async function costLogLoad(){
  const tbl=$('cost-log-table'),empty=$('cost-log-empty');
  if(!tbl)return;
  try{
    const d=await fetch('/api/eval/cost-optimize-log').then(r=>r.json());
    const entries=d.entries||[];
    if(!entries.length){
      if(empty){empty.style.display='block';empty.innerHTML='ยังไม่มี cost optimization swaps (ยังไม่ได้ apply หรือไม่มี recommendations)';}
      tbl.style.display='none';
      return;
    }
    if(empty)empty.style.display='none';
    tbl.style.display='block';
    let html='<table style="width:100%;border-collapse:collapse;font-size:var(--fs-3xs)">';
    html+='<tr style="border-bottom:1px solid var(--border2);color:var(--text-tertiary);position:sticky;top:0;background:var(--elev-1)"><th style="text-align:left;padding:3px">date</th><th>suite</th><th>from → to</th><th>save $</th><th>save %</th></tr>';
    entries.forEach(e=>{
      const dt=e.ts?new Date(e.ts*1000).toISOString().slice(0,16):'?';
      html+='<tr style="border-bottom:1px solid var(--border2)">';
      html+=`<td style="padding:3px">${dt}</td>`;
      html+=`<td style="text-align:center">${e.suite||e.subagent||'?'}</td>`;
      html+=`<td style="text-align:center">${e.from||'?'} → <b>${e.to||'?'}</b></td>`;
      html+=`<td style="text-align:center">${(e.savings_usd||0).toFixed(4)}</td>`;
      html+=`<td style="text-align:center">${((e.savings_pct||0)*100).toFixed(1)}%</td>`;
      html+='</tr>';
    });
    html+='</table>';
    tbl.innerHTML=html;
  }catch(e){
    if(empty){empty.style.display='block';empty.innerHTML='⚠️ โหลดไม่สำเร็จ: '+String(e);}
  }
}

// === PIPELINE DAG VISUALIZER — vis-network render (T5) ===
let _pipelineNet=null,_pipelineSuitesLoaded=false;
async function pipelineGraphLoad(){
  const sel=$('pipeline-suite-select'),vis=$('pipeline-graph-vis'),empty=$('pipeline-graph-empty');
  if(!sel)return;
  // Populate dropdown on first load
  if(!_pipelineSuitesLoaded){
    try{
      const d=await fetch('/api/eval/pipeline-graph').then(r=>r.json());
      (d.pipelines||[]).forEach(p=>{
        const o=document.createElement('option');o.value=p;o.textContent=p;sel.appendChild(o);
      });
      _pipelineSuitesLoaded=true;
    }catch(e){}
  }
  const suite=sel.value;
  if(_pipelineNet){try{_pipelineNet.destroy();}catch(_){}_pipelineNet=null;}
  if(!suite){
    if(vis)vis.style.display='none';
    if(empty){empty.style.display='block';empty.innerHTML='เลือก pipeline suite เพื่อดู DAG';}
    return;
  }
  if(empty)empty.style.display='none';
  if(vis)vis.style.display='block';
  try{
    const d=await fetch('/api/eval/pipeline-graph?suite='+encodeURIComponent(suite)).then(r=>r.json());
    if(d.error||(d.nodes||[]).length===0){
      if(vis)vis.style.display='none';
      if(empty){empty.style.display='block';empty.innerHTML='⚠️ '+(d.error||'ไม่มีข้อมูล');}
      return;
    }
    // Node colors by group
    const groupColors={sequential:{bg:'rgba(94,234,212,.8)',border:'rgba(94,234,212,1)'},
                       parallel:{bg:'rgba(251,191,36,.8)',border:'rgba(251,191,36,1)'},
                       merge:{bg:'rgba(248,113,113,.8)',border:'rgba(248,113,113,1)'}};
    const nodes=(d.nodes||[]).map(n=>{
      const c=groupColors[n.group]||groupColors.sequential;
      return {id:n.id,label:n.label,title:n.title,group:n.group,color:{background:c.bg,border:c.border},font:{color:'#fff',size:12}};
    });
    const edges=(d.edges||[]).map(e=>({from:e.from,to:e.to,arrows:{to:{enabled:true}},color:{color:'rgba(150,150,180,.6)'},smooth:{type:'curvedCW'}}));
    // Check vis-network availability (CDN)
    if(typeof vis==='undefined'||!vis.Network){
      if(vis)vis.style.display='none';
      if(empty){empty.style.display='block';empty.innerHTML='🔗 vis-network ไม่พร้อม (offline?)';}
      return;
    }
    _pipelineNet=new vis.Network(vis,{nodes:new vis.DataSet(nodes),edges:new vis.DataSet(edges)},
      {layout:{hierarchical:{enabled:true,direction:'LR',sortMethod:'directed',levelSeparation:120}},
       nodes:{shape:'box',margin:10,borderWidth:2},
       edges:{width:1.5},
       physics:{enabled:false},
       interaction:{hover:true,tooltipDelay:100}});
  }catch(e){
    if(vis)vis.style.display='none';
    if(empty){empty.style.display='block';empty.innerHTML='⚠️ โหลดไม่สำเร็จ: '+String(e);}
  }
}

// === RACE RESULTS — best model per suite (U3) ===
async function raceResultsLoad(){
  const tbl=$('race-table'),empty=$('race-empty'),sub=$('race-subtitle');
  if(!tbl)return;
  if(empty){empty.style.display='block';empty.innerHTML='⏳ กำลังโหลด...';}
  tbl.style.display='none';
  try{
    const d=await fetch('/api/eval/race-results').then(r=>r.json());
    const suites=d.suites||[];
    if(!suites.length){
      if(empty){empty.style.display='block';empty.innerHTML='ยังไม่มี race results — รัน CI eval (T4 race step) ก่อน<br><span style="font-size:var(--fs-xs)">ข้อมูลมาจาก <code>.tmp/subagent-eval/races/*.json</code></span>';}
      return;
    }
    if(empty)empty.style.display='none';
    if(sub)sub.textContent=`${suites.length} suite(s) · best model per suite`;
    tbl.style.display='block';
    // Collect all model names for column headers
    const allModels=[...new Set(suites.flatMap(s=>Object.keys(s.models||{})))].sort();
    let html='<table style="width:100%;border-collapse:collapse;font-size:var(--fs-2xs)">';
    html+='<tr style="border-bottom:1px solid var(--border2);color:var(--text-tertiary)"><th style="text-align:left;padding:4px">suite</th><th>🏆 best</th>';
    allModels.forEach(m=>{html+=`<th>${m}</th>`;});
    html+='</tr>';
    suites.forEach(s=>{
      html+='<tr style="border-bottom:1px solid var(--border2)">';
      html+=`<td style="padding:4px">${s.suite}</td>`;
      html+=`<td style="text-align:center;color:#34d399;font-weight:600">${s.best} (${(s.best_pass_at_k*100).toFixed(0)}%)</td>`;
      allModels.forEach(m=>{
        const info=(s.models||{})[m];
        if(info){
          const isBest=m===s.best;
          const rate=(info.mean_pass_at_k*100).toFixed(0);
          html+=`<td style="text-align:center;${isBest?'background:rgba(52,211,153,.12);font-weight:600':''}">${rate}%${info.wins?` <span style="color:var(--text-tertiary)">(${info.wins}🏆)</span>`:''}</td>`;
        }else{
          html+='<td style="text-align:center;color:var(--text-disabled)">—</td>';
        }
      });
      html+='</tr>';
    });
    html+='</table>';
    tbl.innerHTML=html;
  }catch(e){
    if(empty){empty.style.display='block';empty.innerHTML='⚠️ โหลดไม่สำเร็จ: '+String(e);}
  }
  // V2: load race history trend alongside current results
  raceHistoryLoad();
}

// === RACE HISTORY TREND — best model over time (V2) ===
async function raceHistoryLoad(){
  const tbl=$('race-history-table'),empty=$('race-history-empty');
  if(!tbl)return;
  try{
    const d=await fetch('/api/eval/race-history').then(r=>r.json());
    const dates=d.dates||[];
    const series=d.series||{};
    if(!dates.length||!Object.keys(series).length){
      if(empty){empty.style.display='block';empty.innerHTML='ยังไม่มี race history — race results snapshot จะสะสมใน <code>evals/subagents/races/</code> ทุก CI run';}
      tbl.style.display='none';
      return;
    }
    if(empty)empty.style.display='none';
    tbl.style.display='block';
    let html='<table style="width:100%;border-collapse:collapse;font-size:var(--fs-3xs)">';
    html+='<tr style="border-bottom:1px solid var(--border2);color:var(--text-tertiary)"><th style="text-align:left;padding:3px">suite</th>';
    dates.forEach(dt=>{html+=`<th>${dt.slice(4)}</th>`;});
    html+='</tr>';
    Object.entries(series).forEach(([suite,s])=>{
      html+='<tr style="border-bottom:1px solid var(--border2)">';
      html+=`<td style="padding:3px">${suite}</td>`;
      s.best_models.forEach((bm,i)=>{
        const isChange=i>0&&s.best_models[i-1]!==bm;
        html+=`<td style="text-align:center;${isChange?'background:rgba(251,191,36,.15)':''}">${bm||'—'}${isChange?' ⚡':''}</td>`;
      });
      html+='</tr>';
    });
    html+='</table>';
    html+='<div style="margin-top:6px;font-size:var(--fs-3xs);color:var(--text-tertiary)">⚡ = best model เปลี่ยนจาก run ก่อน</div>';
    tbl.innerHTML=html;
  }catch(e){
    if(empty){empty.style.display='block';empty.innerHTML='⚠️ โหลดไม่สำเร็จ: '+String(e);}
  }
}

// === SUITE EDITOR — form-based suite creation (X2) ===
let _seMeta={subagents:[],suites:[]},_seMetaLoaded=false;
async function suiteEditorInit(){
  if(_seMetaLoaded)return;
  try{
    _seMeta=await fetch('/api/eval/suite-meta').then(r=>r.json());
    _seMetaLoaded=true;
    // populate load dropdown
    const sel=$('se-load-select');
    if(sel)(_seMeta.suites||[]).forEach(s=>{const o=document.createElement('option');o.value=s;o.textContent=s;sel.appendChild(o);});
  }catch(e){console.warn('suite meta load failed',e);}
}
function suiteEditorAddCase(c){
  const wrap=$('se-cases');if(!wrap)return;
  const row=document.createElement('div');
  row.style.cssText='display:grid;grid-template-columns:100px 140px 1fr 120px 120px 30px;gap:6px;align-items:start;padding:6px;border:1px solid var(--border2);border-radius:var(--r-md)';
  const cased=c||{id:'',subagent:'',prompt:'',required:'',forbidden:''};
  const saopts=(_seMeta.subagents||[]).map(n=>`<option value="${n}"${n===cased.subagent?' selected':''}>${n}</option>`).join('');
  row.innerHTML=`
    <input class="se-id" placeholder="id" value="${cased.id||''}" style="padding:4px;font-size:var(--fs-3xs;border:1px solid var(--border2);border-radius:4px;background:var(--elev-2);color:var(--text-primary)">
    <select class="se-subagent" style="padding:4px;font-size:var(--fs-3xs);border:1px solid var(--border2);border-radius:4px;background:var(--elev-2);color:var(--text-primary)"><option value="">subagent…</option>${saopts}</select>
    <textarea class="se-prompt" placeholder="prompt" style="padding:4px;font-size:var(--fs-3xs);border:1px solid var(--border2);border-radius:4px;background:var(--elev-2);color:var(--text-primary);min-height:32px;resize:vertical">${cased.prompt||''}</textarea>
    <input class="se-required" placeholder="required (comma)" value="${(cased.required||[]).join(', ')}" style="padding:4px;font-size:var(--fs-3xs);border:1px solid var(--border2);border-radius:4px;background:var(--elev-2);color:var(--text-primary)">
    <input class="se-forbidden" placeholder="forbidden (comma)" value="${(cased.forbidden||[]).join(', ')}" style="padding:4px;font-size:var(--fs-3xs);border:1px solid var(--border2);border-radius:4px;background:var(--elev-2);color:var(--text-primary)">
    <button onclick="this.parentElement.remove()" style="padding:4px;cursor:pointer;border:1px solid var(--border2);border-radius:4px;background:var(--elev-2);color:var(--text-secondary)">🗑️</button>`;
  wrap.appendChild(row);
}
function suiteEditorCollect(){
  const name=$('se-suite-name')?.value?.trim()||'';
  const desc=$('se-description')?.value||'';
  const rows=[...document.querySelectorAll('#se-cases > div')];
  const cases=rows.map(r=>{
    const parseCS=t=>(t||'').split(',').map(s=>s.trim()).filter(s=>s);
    return{id:r.querySelector('.se-id').value.trim(),subagent:r.querySelector('.se-subagent').value,prompt:r.querySelector('.se-prompt').value,required:parseCS(r.querySelector('.se-required').value),forbidden:parseCS(r.querySelector('.se-forbidden').value)};
  }).filter(c=>c.id&&c.prompt);
  return{suite:name,description:desc,cases};
}
async function suiteEditorSave(){
  const data=suiteEditorCollect();
  const st=$('se-status');
  if(st)st.textContent='💾 saving...';
  try{
    const r=await fetch('/api/eval/suite',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    const j=await r.json();
    if(r.ok){
      if(st)st.innerHTML=`✅ Saved: <code>${j.path}</code> (${data.cases.length} cases)`;
      toast('✅ Suite saved: '+data.suite);
    }else{
      if(st)st.innerHTML=`❌ ${j.error||'save failed'}`;
    }
  }catch(e){if(st)st.innerHTML='❌ '+String(e);}
}
async function suiteEditorLoad(){
  const name=$('se-load-select')?.value;if(!name)return;
  try{
    const d=await fetch('/api/eval/suite?name='+encodeURIComponent(name)).then(r=>r.json());
    if(d.error){if($('se-status'))$('se-status').innerHTML='❌ '+d.error;return;}
    $('se-suite-name').value=d.suite||name;
    $('se-description').value=d.description||'';
    $('se-cases').innerHTML='';
    (d.cases||[]).forEach(c=>suiteEditorAddCase(c));
    if($('se-status'))$('se-status').textContent=`📂 Loaded "${name}" (${(d.cases||[]).length} cases)`;
  }catch(e){if($('se-status'))$('se-status').innerHTML='❌ '+String(e);}
}

function clearAnalyticsData(){
  if(!confirm('ล้าง opens log + health snapshots ทั้งหมด? (ไม่สามารถย้อนกลับได้)'))return;
  _lsSet(OPENS_KEY,[]);
  _lsSet(HEALTH_SNAPSHOTS_KEY,[]);
  _lsSet(RECENT_KEY,[]);
  toast('🗑️ ล้างข้อมูล usage แล้ว');
  analyticsLoad();
}

// ===== CHUNK TT — Smart Default Agent (auto-detect from env) =====
// On boot, if the URL has no ?agent= param, ask the server which agent is
// calling (detected from env fingerprints). If detected, auto-apply the
// Skills-tab agent filter + show an info banner. Skipped silently if the
// server returns null (no fingerprint found — e.g. opened from a browser).
async function autoDetectAgent(){
  try{
    const url=new URL(window.location.href);
    if(url.searchParams.get('agent'))return;  // explicit ?agent= wins
    const r=await fetch('/api/detect-agent').then(r=>r.json());
    if(!r||!r.agent)return;
    // Apply to the agent filter once Skills tab is visited (lazy — dropdown
    // populates on first skillsLoad). We stash the detected name and apply
    // it inside applyUrlParams/skillsLoad.
    window._autoDetectedAgent=r.agent;
    window._autoDetectedSource=r.source||'env';
    // If Skills tab is already active, apply now; otherwise it applies on visit.
    if(currentView==='skills')_applyAutoDetectedAgent();
  }catch(_){}
}
function _applyAutoDetectedAgent(){
  if(!window._autoDetectedAgent)return;
  const sel=$('skills-agent-filter');if(!sel)return;
  const a=window._autoDetectedAgent;
  // Only apply if the option exists (dropdown populated) or value is 'all'.
  let found=false;
  for(const opt of sel.options){if(opt.value.toLowerCase()===a.toLowerCase()){sel.value=opt.value;found=true;break;}}
  if(!found){
    // Dropdown not yet populated — retry once after skillsLoad fills it.
    setTimeout(_applyAutoDetectedAgent,300);
    return;
  }
  // Show info banner (distinct from the explicit ?agent= banner).
  let banner=$('skills-autodetect-banner');
  if(!banner){
    banner=document.createElement('div');banner.id='skills-autodetect-banner';
    banner.style.cssText='padding:6px 10px;background:rgba(94,234,212,.10);border:1px solid var(--accent-success);border-radius:var(--r-md);font-size:var(--fs-2xs);color:var(--text-secondary);margin-bottom:6px;flex-shrink:0';
    const tb=$('skills-toolbar');if(tb)tb.parentNode.insertBefore(banner,tb.nextSibling);
  }
  banner.innerHTML='🤖 <b style="color:var(--accent-success)">auto-detected: '+a+'</b> (จาก env) · <a href="#" onclick="clearAutoDetect();return false" style="color:var(--text-tertiary);text-decoration:underline">ดูทั้งหมด</a>';
  skillsLoad();
}
function clearAutoDetect(){
  window._autoDetectedAgent=null;
  const banner=$('skills-autodetect-banner');if(banner)banner.remove();
  const sel=$('skills-agent-filter');if(sel)sel.value='all';
  skillsLoad();syncUrlState();
}

// ===== URL PARAMS (?agent=, ?skill=, ?flow=) =====
// Deep-link support: open the dashboard with ?agent=zcode&skill=tdd or
// ?flow=debug-production-issue to jump straight to a skill detail or
// auto-play a walkthrough. Called once on page load (Skills view).
function applyAgentParam(){return applyUrlParams();}
function applyUrlParams(){
  const url=new URL(window.location.href);
  const agent=url.searchParams.get('agent');
  const skill=url.searchParams.get('skill');
  const flow=url.searchParams.get('flow');
  // Agent filter first.
  if(agent){
    const sel=$('skills-agent-filter');
    if(sel){
      for(const opt of sel.options){
        if(opt.value.toLowerCase()===agent.toLowerCase()){sel.value=opt.value;break;}
      }
      let banner=$('skills-agent-banner');
      if(!banner){
        banner=document.createElement('div');
        banner.id='skills-agent-banner';
        banner.style.cssText='padding:6px 10px;background:var(--accent-brand-soft,rgba(120,170,255,.12));border:1px solid var(--accent-brand,rgba(120,170,255,.4));border-radius:var(--r-md);font-size:var(--fs-2xs);color:var(--text-secondary);margin-bottom:6px;flex-shrink:0';
        const tb=$('skills-toolbar');if(tb)tb.parentNode.insertBefore(banner,tb.nextSibling);
      }
      banner.innerHTML='👁 กำลังดู skills ของ <b style="color:var(--accent-brand)">'+agent+'</b> · <a href="#" onclick="clearAgentParam();return false" style="color:var(--text-tertiary);text-decoration:underline">ดูทั้งหมด</a>';
      skillsLoad();
    }
  }
  // ?skill=<name> → open detail drawer (after skills list loads).
  if(skill){
    // Wait for skills list to populate, then open detail.
    setTimeout(()=>{try{skillsOpenDetail(decodeURIComponent(skill));}catch(e){console.warn('skill deep-link fail',e);}},500);
  }
  // ?flow=<id> → auto-play walkthrough simulation.
  if(flow){
    setTimeout(()=>{
      try{
        if(!_walkthroughsLoaded)loadWalkthroughs();
        simWalkthrough(decodeURIComponent(flow));
      }catch(e){console.warn('flow deep-link fail',e);}
    },600);
  }
}
// === CHUNK PP — Dashboard URL State Sync ===
// Build a query string representing the CURRENT dashboard state: active view + all
// Skills-tab filters + sort. Used by syncUrlState() to keep the URL shareable and by
// the popstate handler to restore state on browser back/forward.
let _urlSyncSuspend=false;  // guard: while applying URL-driven state, don't re-sync
function _buildStateQs(){
  const qs=new URLSearchParams();
  if(currentView&&currentView!=='summary')qs.set('view',currentView);
  // Skills-tab filters (only meaningful when skills DOM exists)
  const sel=$('skills-agent-filter');if(sel&&sel.value&&sel.value!=='all')qs.set('agent',sel.value);
  const dom=$('skills-domain-filter');if(dom&&dom.value)qs.set('domain',dom.value);
  const srch=$('skills-search');if(srch){const q=srch.value.trim();if(q)qs.set('q',q);}
  const srt=$('skills-sort');if(srt&&srt.value)qs.set('sort',srt.value);
  if(_skillsInv&&_skillsInv!=='all')qs.set('invocation',_skillsInv);
  if(_skillsCat)qs.set('category',_skillsCat);
  const inst=$('skills-installed-only');if(inst&&inst.checked)qs.set('installed','1');
  return qs.toString();
}
// Reflect current state into the URL (replaceState — no extra history entry per change).
function syncUrlState(){
  if(_urlSyncSuspend)return;
  try{
    const qs=_buildStateQs();
    const newSearch=qs?('?'+qs):'';
    const cur=window.location.search;
    if(cur!==newSearch){
      const nu=window.location.pathname+newSearch+window.location.hash;
      window.history.replaceState({},'',nu);
    }
  }catch(_){}
}
// Copy the current URL (with full state) to clipboard for sharing.
async function copyShareUrl(){
  try{
    syncUrlState();  // ensure URL reflects latest state first
    const url=window.location.href;
    if(navigator.clipboard&&navigator.clipboard.writeText){
      await navigator.clipboard.writeText(url);
    }else{
      // Fallback: transient textarea select.
      const ta=document.createElement('textarea');ta.value=url;document.body.appendChild(ta);ta.select();
      document.execCommand('copy');ta.remove();
    }
    toast('🔗 คัดลอก URL แล้ว — วางที่เครื่องอื่นได้เลย');
  }catch(e){toast('คัดลอก URL ไม่สำเร็จ: '+e.message,true);}
}
// Restore dashboard state from the URL on load / back / forward.
// Called from setView boot AND from popstate. Guarded so applying state does not
// recursively push history entries.
function applyFullStateFromUrl(){
  _urlSyncSuspend=true;
  try{
    const url=new URL(window.location.href);
    const view=url.searchParams.get('view');
    if(view){try{setView(view);}catch(_){}}
    // Skills-tab filters
    const dom=url.searchParams.get('domain');
    if(dom){const el=$('skills-domain-filter');if(el){el.value=dom;}}
    const q=url.searchParams.get('q');
    if(q){const el=$('skills-search');if(el){el.value=q;}}
    const sort=url.searchParams.get('sort');
    if(sort){const el=$('skills-sort');if(el){el.value=sort;}}
    const inv=url.searchParams.get('invocation');
    if(inv){try{skillsSetInv(inv);}catch(_){}}
    const cat=url.searchParams.get('category');
    if(cat){try{skillsSetCat(cat);}catch(_){}}
    const inst=url.searchParams.get('installed');
    if(inst==='1'){const el=$('skills-installed-only');if(el)el.checked=true;}
    // agent/skill/flow handled by existing applyUrlParams below (kept for compat).
  }finally{
    _urlSyncSuspend=false;
  }
}
// Browser back/forward → re-apply URL state. Idempotent.
window.addEventListener('popstate',function(){
  try{applyFullStateFromUrl();}catch(_){}
});
function clearAgentParam(){
  const url=new URL(window.location.href);
  url.searchParams.delete('agent');
  window.history.replaceState({},'',url);
  const banner=$('skills-agent-banner');if(banner)banner.remove();
  $('skills-agent-filter').value='all';
  skillsLoad();
}
async function loadWalkthroughs(){
  if(_walkthroughsLoaded)return;
  try{
    const r=await fetch('/api/walkthroughs');
    const j=await r.json();
    const list=$('walkthroughs-list');
    const count=$('walkthroughs-count');
    count.textContent=`(${j.total} กระแส)`;
    list.innerHTML=j.flows.map(f=>{
      const d=f.difficulty||{};
      const diffColor=d.level==='ขั้นสูง'?'var(--accent-danger)':d.level==='ปานกลาง'?'var(--accent-warn)':'var(--accent-green)';
      const diffBadge=d.score!==undefined?`<span style="color:${diffColor};font-weight:600;margin-left:4px" title="auto-score: ${d.score}/100">${d.level||''} ${d.score}</span>`:'';
      const manualBadge=f.level_th&&d.level&&f.level_th!==d.level?`<span style="color:var(--text-tertiary)" title="manual level">${f.level_th}</span>`:'';
      return `
      <button class="chat-quick-btn" style="padding:5px 11px;font-size:var(--fs-2xs);background:var(--elev-2);border:1px solid var(--border2);color:var(--text-primary)" onclick="simWalkthrough('${f.id}')">
        ${f.title_th} <span style="color:var(--text-tertiary)">· ${f.step_count} ขั้น</span>${manualBadge?' / '+manualBadge:''}${diffBadge}
      </button>`;
    }).join('');
    _walkthroughsLoaded=true;
  }catch(e){console.warn('walkthroughs load fail',e);}
}
function toggleWalkthroughsBar(){
  const list=$('walkthroughs-list'),ar=$('walkthroughs-arrow');
  const open=list.style.display!=='none';
  list.style.display=open?'flex':'none';
  ar.textContent=open?'▾':'▸';
  if(!open && !_walkthroughsLoaded)loadWalkthroughs();
}
let _wfSteps=[],_wfIdx=-1,_wfTimer=null,_wfMeta={},_wfCurrentId=null;
async function simWalkthrough(id){
  try{
    const r=await fetch('/api/walkthroughs/'+encodeURIComponent(id));
    if(!r.ok){toast('ไม่พบ flow: '+id,'err');return;}
    const j=await r.json();
    _wfSteps=j.steps;_wfIdx=-1;_wfMeta=j;_wfCurrentId=id;
    // Reuse the same sim modal — render stations from walkthrough steps.
    $('sim-title').textContent='🎬 '+j.title_th;
    $('sim-stations').innerHTML=_wfSteps.map((st,i)=>`
<div class="sim-station" data-i="${i}">
  <div class="sim-core">${st.icon||'🔧'}</div>
  <div class="sim-station-label">${st.label_th}</div>
  <div style="font-size:var(--fs-2xs);color:var(--text-tertiary);margin-top:2px">${st.skill}</div>
</div>`).join('');
    $('sim-progress').style.width='0%';
    $('sim-explain').className='';$('sim-explain').innerHTML=`<div style="color:var(--text-secondary);font-size:var(--fs-xs);margin-bottom:6px">${j.summary_th}</div><div style="font-size:var(--fs-2xs);color:var(--text-tertiary)">${j.level_th} · ${j.duration_th} · ${_wfSteps.length} ขั้น · กด ▶ เริ่ม</div>`;
    $('sim-backdrop').classList.add('show');
    // Show the copy-link button (walkthrough context only).
    const copyBtn=$('sim-copy-link');if(copyBtn)copyBtn.style.display='inline-flex';
    // Override play/step behavior for this walkthrough run.
    _wfBindControls();
  }catch(e){toast('โหลด flow ไม่ได้: '+e,'err');}
}
function simCopyLink(){
  if(_wfCurrentId){copyFlowLink(_wfCurrentId);return;}
  // Single-skill simulation — copy ?skill=<name>.
  // _simCurrentName is set by simulateSkill() below.
  if(typeof _simCurrentName!=='undefined'&&_simCurrentName){copySkillLink(_simCurrentName);}
}
function _wfBindControls(){
  // The existing sim modal has buttons calling simPlay/simStep/simReset.
  // We temporarily override those globals for the walkthrough run.
  window._wfSavedPlay=window.simPlay;window._wfSavedStep=window.simStep;
  window.simPlay=_wfPlay;window.simStep=_wfStep;
}
function _wfRestore(){
  if(window._wfSavedPlay){window.simPlay=window._wfSavedPlay;window.simStep=window._wfSavedStep;}
}
function _wfPlay(){
  if(_wfTimer){clearInterval(_wfTimer);_wfTimer=null;return;}
  if(_wfIdx>=_wfSteps.length-1)_wfIdx=-1;
  _wfTimer=setInterval(_wfStep,2400);  // slower than single-skill (more context per step)
  _wfStep();
}
function _wfStep(){
  if(!_wfSteps.length)return;
  _wfIdx++;
  if(_wfIdx>=_wfSteps.length){
    if(_wfTimer){clearInterval(_wfTimer);_wfTimer=null;}
    $('sim-explain').className='';$('sim-explain').innerHTML=`✅ <b>เสร็จสิ้น flow!</b> ครบ ${_wfSteps.length} ขั้น — ${_wfMeta.title_th}`;
    return;
  }
  document.querySelectorAll('.sim-station').forEach(el=>{el.classList.remove('active','done');});
  for(let i=0;i<_wfIdx;i++)document.querySelector(`.sim-station[data-i="${i}"]`)?.classList.add('done');
  document.querySelector(`.sim-station[data-i="${_wfIdx}"]`)?.classList.add('active');
  $('sim-progress').style.width=((_wfIdx+1)/_wfSteps.length*100)+'%';
  const st=_wfSteps[_wfIdx];
  $('sim-explain').innerHTML=`<b style="color:var(--accent-brand)">ขั้นที่ ${_wfIdx+1}/${_wfSteps.length}:</b> ${st.label_th}<div style="margin-top:5px;font-size:var(--fs-2xs);color:var(--text-secondary)">${st.skill_th_description||st.skill}</div>`;
}
// Hook into simClose to restore controls when modal closes.
const _origSimClose=simClose;
simClose=function(e){
  if(e&&e.target&&e.target.id!=='sim-backdrop'&&e.type==='click')return;
  if(_wfTimer){clearInterval(_wfTimer);_wfTimer=null;}
  if(_wfSteps.length){_wfSteps=[];_wfIdx=-1;_wfRestore();}
  $('sim-backdrop').classList.remove('show');
};

setView('summary');
// CHUNK PP: if URL carries state (?view=, filters), apply it after initial paint.
try{applyFullStateFromUrl();}catch(_){}
// CHUNK TT: auto-detect agent from env (only if no explicit ?agent= in URL).
try{autoDetectAgent();}catch(_){}
// CHUNK UU: auto-restore last workspace if user opted in.
try{maybeAutoRestoreWorkspace();}catch(_){}
_stageRO.observe(flowStage);
window.addEventListener('resize',layoutFlow);
connect();loadRecommendations();loadModelStationsConfig();layoutFlow();renderLanes();

// === CHUNK CC — PWA Offline Mode (progressive enhancement) ===
if('serviceWorker' in navigator){
  navigator.serviceWorker.register('/sw.js').then(function(reg){
    console.log('📱 A-Wiki SW registered (offline-ready)');
  }).catch(function(e){
    console.warn('SW registration failed (non-fatal):', e);
  });
}

