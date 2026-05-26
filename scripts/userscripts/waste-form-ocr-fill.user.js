// ==UserScript==
// @name         Waste Form OCR & Fill (gtwoffice trash_add)
// @namespace    a-wiki
// @version      0.1.0
// @description  ถ่ายรูปใบรายงานขยะ → OCR ด้วย Gemini Flash → กรอกฟอร์ม trash_add อัตโนมัติ
// @author       A-Wiki / Asse7en
// @match        https://10779.gtwoffice.com/env/manage/trash_add*
// @match        https://*.gtwoffice.com/env/manage/trash_add*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @connect      generativelanguage.googleapis.com
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  // --- CONFIG ----------------------------------------------------------------
  // Gemini API key: ตั้งครั้งแรกผ่าน prompt → เก็บใน Tampermonkey storage
  const GEMINI_MODEL = 'gemini-2.5-flash';
  const GEMINI_URL = (key) =>
    `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${key}`;

  // Hardcoded constants ตาม wiki/synthesis/waste-form-automation.md
  const SUPPLIES_DEFAULT = 'อบต.อุทัย';
  const RECORDER_DEFAULT = 'Aase7en';

  // Location → form row mapping (label-based)
  // คีย์ของ label ใช้คำสำคัญใน label ของแต่ละแถว (ดูใน screenshot)
  const ROW_LABEL_MAP = {
    OPD: ['ขยะทั่วไป OPD'],
    Ward: ['ขยะทั่วไป Ward'],
    ER: ['ขยะทั่วไป ER'],
    โรงครัว: ['ขยะทั่วไป โรงครัว'],
    เวช: ['ขยะทั่วไป เวช'],
    ฝังเข็ม: ['ขยะทั่วไป ฝังเข็ม'],
    แผนไทย: ['ขยะทั่วไป แพทย์แผนไทย', 'ขยะทั่วไป แผนไทย'],
    บริหาร: ['ขยะทั่วไป บริหาร'],
    ห้องช่าง: ['ขยะทั่วไป ห้องช่าง'],
    ซักฟอก: ['ขยะทั่วไป ซักฟอก'],
    แฟลต: ['ขยะทั่วไป แฟลต'],
  };

  // Compound locations → split equally across rows
  const COMPOUND_LOCATIONS = {
    'OPD+ER': ['OPD', 'ER'],
    'แผนไทย+ฝังเข็ม': ['แผนไทย', 'ฝังเข็ม'],
  };

  // --- SYSTEM PROMPT (ภาษาอังกฤษเพื่อประหยัด token ตาม CLAUDE.md) ---------------
  const SYSTEM_PROMPT = `You extract data from Thai hospital waste-report forms (handwritten).
Return ONLY a JSON array. One object per row. No markdown fences.

Schema per row:
  row_number   integer
  date         "YYYY-MM-DD" (convert Thai Buddhist Era: subtract 543; if cell is "น"/"ง"/dash, copy from row above)
  time         string as written, e.g. "15:00" or "07:35น."  (null if blank)
  weight_kg    number; if cell is "5+5" return the SUM (10). null if blank.
  location     normalize to one of: OPD | Ward | ER | OPD+ER | โรงครัว | เวช | ฝังเข็ม | แผนไทย+ฝังเข็ม | แผนไทย
  recorder     staff name(s) as written (multiple joined with "+"), null if blank

Known confusions to avoid:
  วอร์ด ≠ จอดรถ      (it's Ward)
  เวช  ≠ ลาว        (it's เวชกรรม)
  แผนไทย+ฝังเข็ม ≠ แผนไทย+ฝ่ายแม่

Staff hints (use as confirmation only):
  OPD afternoon → อ้อย+อ้อย ;  Ward → ปลา+เพ็ญ or เพ็ญ+ปลา
  แผนไทย+ฝังเข็ม → หนึ่ง+เพ็ญ ;  ER → กลอยใจ or ณฐอร (เพ็ญ covers night 19:30+)
  โรงครัว → ก

Add a final object {"_meta": {"confidence": 0..1, "unclear": [...]}} if quality is low.
Return ONLY the JSON array.`;

  // --- UTIL ------------------------------------------------------------------
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function log(...args) { console.log('[waste-ocr]', ...args); }
  function warn(...args) { console.warn('[waste-ocr]', ...args); }

  function getApiKey() {
    let key = GM_getValue('GEMINI_API_KEY', '');
    if (!key) {
      key = prompt('ใส่ GEMINI_API_KEY (จะถูกเก็บใน Tampermonkey storage บนเครื่องนี้เท่านั้น):');
      if (key) GM_setValue('GEMINI_API_KEY', key.trim());
    }
    return key && key.trim();
  }

  function clearApiKey() {
    GM_setValue('GEMINI_API_KEY', '');
    alert('ล้าง API key แล้ว — รอบหน้าจะถามใหม่');
  }

  function fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => {
        const s = String(r.result || '');
        const i = s.indexOf(',');
        resolve(i >= 0 ? s.slice(i + 1) : s);
      };
      r.onerror = reject;
      r.readAsDataURL(file);
    });
  }

  function geminiCall(apiKey, base64Data, mimeType) {
    return new Promise((resolve, reject) => {
      const body = {
        system_instruction: { parts: [{ text: SYSTEM_PROMPT }] },
        contents: [{
          role: 'user',
          parts: [
            { inline_data: { mime_type: mimeType, data: base64Data } },
            { text: 'Extract all rows from this hospital waste report.' },
          ],
        }],
        generationConfig: { temperature: 0.1, response_mime_type: 'application/json' },
      };
      GM_xmlhttpRequest({
        method: 'POST',
        url: GEMINI_URL(apiKey),
        headers: { 'Content-Type': 'application/json' },
        data: JSON.stringify(body),
        onload: (resp) => {
          try {
            const j = JSON.parse(resp.responseText);
            if (j.error) return reject(new Error(j.error.message || 'Gemini error'));
            const text = j.candidates?.[0]?.content?.parts?.[0]?.text || '';
            const clean = text.replace(/^```json\s*|\s*```$/g, '').trim();
            resolve(JSON.parse(clean));
          } catch (e) { reject(e); }
        },
        onerror: (e) => reject(new Error('Network error: ' + (e?.error || 'unknown'))),
      });
    });
  }

  // --- AGGREGATION -----------------------------------------------------------
  function aggregateRows(ocrRows, targetDate) {
    // 1. drop _meta entries
    const rows = ocrRows.filter(r => r && r.row_number != null && !r._meta);

    // 2. filter to targetDate if specified
    const filtered = targetDate ? rows.filter(r => r.date === targetDate) : rows;

    // 3. accumulate {location: total_kg}
    const byLocation = {};
    for (const r of filtered) {
      if (r.weight_kg == null || r.location == null) continue;
      const w = Number(r.weight_kg) || 0;
      const locs = COMPOUND_LOCATIONS[r.location];
      if (locs) {
        const split = w / locs.length;
        for (const sub of locs) byLocation[sub] = (byLocation[sub] || 0) + split;
      } else {
        byLocation[r.location] = (byLocation[r.location] || 0) + w;
      }
    }

    // 4. map location → row label keys
    const result = [];
    for (const [loc, kg] of Object.entries(byLocation)) {
      const labels = ROW_LABEL_MAP[loc];
      if (!labels) { warn('unknown location:', loc); continue; }
      result.push({ location: loc, labels, kg: Math.round(kg * 100) / 100 });
    }

    // 5. earliest time + dates seen
    const times = filtered.map(r => r.time).filter(Boolean).sort();
    const dates = [...new Set(filtered.map(r => r.date).filter(Boolean))].sort();
    return { rows: result, earliestTime: times[0] || null, dates, totalRows: filtered.length };
  }

  // --- FORM FILL -------------------------------------------------------------
  function findRowInputByLabel(labelText) {
    // หา <td> ที่ text ตรงกับ labelText (case-insensitive trim) แล้วคืน input ใน row เดียวกัน
    const tds = $$('td, th').filter(td => td.textContent.trim() === labelText);
    for (const td of tds) {
      const row = td.closest('tr');
      if (!row) continue;
      const input = row.querySelector('input[type="text"], input[type="number"], input:not([type])');
      if (input) return input;
    }
    // partial match fallback
    const tdsPartial = $$('td, th').filter(td => td.textContent.trim().includes(labelText));
    for (const td of tdsPartial) {
      const row = td.closest('tr');
      if (!row) continue;
      const input = row.querySelector('input[type="text"], input[type="number"], input:not([type])');
      if (input) return input;
    }
    return null;
  }

  function setInputValue(el, value) {
    if (!el) return false;
    const proto = el.tagName === 'SELECT' ? HTMLSelectElement.prototype : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    if (setter) setter.call(el, value); else el.value = value;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }

  function selectOptionByText(selectEl, textPart) {
    if (!selectEl) return false;
    for (const opt of selectEl.options) {
      if (opt.text.trim() === textPart || opt.text.trim().includes(textPart)) {
        selectEl.value = opt.value;
        selectEl.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
      }
    }
    return false;
  }

  function findHeaderField(labelSubstr) {
    // หา label/td/th ที่มีคำว่า labelSubstr → คืน input/select ใกล้ที่สุด
    const candidates = $$('label, td, th, div').filter(el => el.textContent.trim().startsWith(labelSubstr));
    for (const el of candidates) {
      // ลองดูพี่น้องและ parent's next cell
      const tr = el.closest('tr');
      if (tr) {
        const inp = tr.querySelector('input, select');
        if (inp && !el.contains(inp)) return inp;
      }
      const next = el.nextElementSibling;
      if (next) {
        const inp = next.matches && next.matches('input, select') ? next : next.querySelector?.('input, select');
        if (inp) return inp;
      }
      const parent = el.parentElement;
      if (parent) {
        const inp = parent.querySelector('input, select');
        if (inp) return inp;
      }
    }
    return null;
  }

  function fillForm(plan, options) {
    const report = [];
    // Header: เวลา
    if (plan.earliestTime && options.fillHeader) {
      const timeEl = findHeaderField('เวลา');
      if (timeEl) { setInputValue(timeEl, plan.earliestTime); report.push(`เวลา = ${plan.earliestTime}`); }
      else report.push('⚠ ไม่พบช่องเวลา');
    }
    // Header: Supplies (select)
    if (options.fillHeader) {
      const sup = findHeaderField('Supplies');
      if (sup && sup.tagName === 'SELECT') {
        if (selectOptionByText(sup, SUPPLIES_DEFAULT)) report.push(`Supplies = ${SUPPLIES_DEFAULT}`);
        else report.push(`⚠ Supplies: ไม่พบ option "${SUPPLIES_DEFAULT}"`);
      }
      const rec = findHeaderField('ผู้บันทึก');
      if (rec && rec.tagName === 'SELECT') {
        if (selectOptionByText(rec, RECORDER_DEFAULT)) report.push(`ผู้บันทึก = ${RECORDER_DEFAULT}`);
        else report.push(`⚠ ผู้บันทึก: ไม่พบ option "${RECORDER_DEFAULT}"`);
      }
    }
    // Weight rows
    for (const r of plan.rows) {
      let filled = false;
      for (const lbl of r.labels) {
        const inp = findRowInputByLabel(lbl);
        if (inp) {
          setInputValue(inp, String(r.kg));
          report.push(`✓ "${lbl}" = ${r.kg} kg`);
          filled = true;
          break;
        }
      }
      if (!filled) report.push(`✗ ไม่พบช่องของ ${r.location} (labels tried: ${r.labels.join(' | ')})`);
    }
    return report;
  }

  // --- UI --------------------------------------------------------------------
  const STYLE = `
  #waste-ocr-btn { position: fixed; top: 12px; right: 12px; z-index: 99999;
    background: #6f42c1; color: #fff; border: 0; border-radius: 6px;
    padding: 10px 14px; font-weight: 600; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,.2); }
  #waste-ocr-btn:hover { background: #5a32a3; }
  #waste-ocr-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 100000;
    display: flex; align-items: center; justify-content: center; }
  #waste-ocr-modal { background: #fff; border-radius: 10px; width: min(720px, 92vw); max-height: 90vh;
    overflow: auto; padding: 20px; font-family: -apple-system, sans-serif; }
  #waste-ocr-modal h2 { margin: 0 0 12px; font-size: 18px; }
  #waste-ocr-drop { border: 2px dashed #aaa; padding: 24px; text-align: center; border-radius: 8px;
    color: #666; margin: 8px 0; cursor: pointer; }
  #waste-ocr-drop.drag { background: #f0e6ff; border-color: #6f42c1; }
  #waste-ocr-status { margin: 8px 0; min-height: 20px; color: #444; font-size: 13px; }
  #waste-ocr-preview { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 14px; }
  #waste-ocr-preview th, #waste-ocr-preview td { padding: 6px 8px; border: 1px solid #ddd; text-align: left; }
  #waste-ocr-preview th { background: #f5f0ff; }
  #waste-ocr-preview input { width: 80px; padding: 3px; }
  #waste-ocr-log { background: #f7f7f9; padding: 10px; border-radius: 6px; font-family: monospace;
    font-size: 12px; max-height: 200px; overflow: auto; white-space: pre-wrap; }
  .waste-ocr-row { display: flex; gap: 8px; margin: 10px 0; align-items: center; }
  .waste-ocr-btn { padding: 8px 14px; border: 0; border-radius: 6px; cursor: pointer; font-weight: 600; }
  .waste-ocr-primary { background: #28a745; color: #fff; }
  .waste-ocr-secondary { background: #6c757d; color: #fff; }
  .waste-ocr-danger { background: #dc3545; color: #fff; }
  `;

  function injectStyle() {
    const s = document.createElement('style');
    s.textContent = STYLE;
    document.head.appendChild(s);
  }

  function injectButton() {
    if ($('#waste-ocr-btn')) return;
    const b = document.createElement('button');
    b.id = 'waste-ocr-btn';
    b.textContent = '📷 OCR & Fill';
    b.title = 'อ่านใบรายงานขยะแล้วกรอกฟอร์ม (ดับเบิลคลิกเพื่อล้าง API key)';
    b.addEventListener('click', openModal);
    b.addEventListener('dblclick', clearApiKey);
    document.body.appendChild(b);
  }

  function openModal() {
    const apiKey = getApiKey();
    if (!apiKey) return;

    const overlay = document.createElement('div');
    overlay.id = 'waste-ocr-overlay';
    overlay.innerHTML = `
      <div id="waste-ocr-modal">
        <h2>📷 OCR ใบรายงานขยะ → กรอกฟอร์ม</h2>
        <div id="waste-ocr-drop">ลากรูปวางที่นี่ หรือคลิกเลือกไฟล์ (.jpg / .png)
          <input type="file" accept="image/*" style="display:none" />
        </div>
        <div id="waste-ocr-status">รอรูป…</div>
        <div id="waste-ocr-content"></div>
        <div class="waste-ocr-row" style="justify-content: flex-end">
          <button class="waste-ocr-btn waste-ocr-secondary" data-act="close">ปิด</button>
        </div>
      </div>`;
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
    overlay.querySelector('[data-act="close"]').addEventListener('click', () => overlay.remove());

    const drop = overlay.querySelector('#waste-ocr-drop');
    const fileInput = drop.querySelector('input[type="file"]');
    drop.addEventListener('click', () => fileInput.click());
    drop.addEventListener('dragover', (e) => { e.preventDefault(); drop.classList.add('drag'); });
    drop.addEventListener('dragleave', () => drop.classList.remove('drag'));
    drop.addEventListener('drop', (e) => {
      e.preventDefault(); drop.classList.remove('drag');
      const f = e.dataTransfer.files?.[0];
      if (f) handleFile(f, overlay, apiKey);
    });
    fileInput.addEventListener('change', (e) => {
      const f = e.target.files?.[0];
      if (f) handleFile(f, overlay, apiKey);
    });

    document.body.appendChild(overlay);
  }

  async function handleFile(file, overlay, apiKey) {
    const status = overlay.querySelector('#waste-ocr-status');
    const content = overlay.querySelector('#waste-ocr-content');
    status.textContent = `กำลังส่งไป Gemini (${file.name}, ${(file.size/1024).toFixed(0)} KB)…`;
    content.innerHTML = '';

    try {
      const b64 = await fileToBase64(file);
      const mime = file.type || 'image/jpeg';
      const ocrRaw = await geminiCall(apiKey, b64, mime);
      log('OCR raw:', ocrRaw);

      const arr = Array.isArray(ocrRaw) ? ocrRaw : (ocrRaw.rows || []);
      const meta = arr.find(r => r._meta)?._meta;
      const plan = aggregateRows(arr);

      if (plan.totalRows === 0) {
        status.textContent = '⚠ ไม่พบข้อมูลแถวในรูป — ลองรูปอื่น';
        return;
      }

      // ถ้ามีหลายวันให้เลือก
      let dateChoice = plan.dates[0];
      if (plan.dates.length > 1) {
        dateChoice = prompt(
          `รูปนี้มี ${plan.dates.length} วัน: ${plan.dates.join(', ')}\nจะกรอกของวันที่ไหน? (YYYY-MM-DD)`,
          plan.dates[plan.dates.length - 1]
        );
        if (!dateChoice) { status.textContent = 'ยกเลิก'; return; }
      }
      const dayPlan = aggregateRows(arr, dateChoice);
      renderPreview(content, overlay, dayPlan, meta, dateChoice);
      status.textContent = `อ่านได้ ${plan.totalRows} แถว, วันที่ ${dateChoice} — ตรวจค่า preview ก่อนกรอก`;
    } catch (e) {
      console.error(e);
      status.textContent = '❌ Error: ' + e.message;
    }
  }

  function renderPreview(content, overlay, dayPlan, meta, date) {
    const metaWarn = meta ? `<div style="color:#b54;margin:6px 0">⚠ confidence=${meta.confidence}${meta.unclear?.length ? ', unclear: '+meta.unclear.join(', '):''}</div>` : '';
    const rowsHtml = dayPlan.rows.map((r, i) =>
      `<tr><td>${r.location}</td><td>${r.labels[0]}</td><td><input type="number" step="0.01" data-i="${i}" value="${r.kg}" /></td></tr>`
    ).join('');
    content.innerHTML = `
      ${metaWarn}
      <div style="font-size:13px;color:#555;margin-bottom:6px">วันที่: <b>${date}</b> · เวลาแรก: <b>${dayPlan.earliestTime || '-'}</b> · ${dayPlan.totalRows} entry</div>
      <table id="waste-ocr-preview">
        <thead><tr><th>Location</th><th>Form label</th><th>kg (แก้ได้)</th></tr></thead>
        <tbody>${rowsHtml || '<tr><td colspan="3">— ไม่มี row ที่ match ROW_LABEL_MAP —</td></tr>'}</tbody>
      </table>
      <div class="waste-ocr-row">
        <label><input type="checkbox" id="ocr-fill-header" checked /> กรอก header (เวลา / Supplies / ผู้บันทึก)</label>
      </div>
      <div class="waste-ocr-row">
        <button class="waste-ocr-btn waste-ocr-primary" data-act="fill">✓ Fill Form</button>
        <button class="waste-ocr-btn waste-ocr-secondary" data-act="cancel">Cancel</button>
      </div>
      <div id="waste-ocr-log" style="display:none"></div>`;

    content.querySelector('[data-act="cancel"]').addEventListener('click', () => overlay.remove());
    content.querySelector('[data-act="fill"]').addEventListener('click', () => {
      // อ่านค่าที่ user แก้ใน preview
      content.querySelectorAll('input[data-i]').forEach(inp => {
        const i = +inp.dataset.i;
        dayPlan.rows[i].kg = parseFloat(inp.value) || 0;
      });
      const fillHeader = content.querySelector('#ocr-fill-header').checked;
      const report = fillForm(dayPlan, { fillHeader });
      const logEl = content.querySelector('#waste-ocr-log');
      logEl.style.display = 'block';
      logEl.textContent = report.join('\n');
    });
  }

  // --- BOOT ------------------------------------------------------------------
  injectStyle();
  // form อาจ render หลัง load — ลอง inject ซ้ำได้
  const tryInject = () => { try { injectButton(); } catch (e) { warn(e); } };
  tryInject();
  new MutationObserver(tryInject).observe(document.body, { childList: true, subtree: false });
  log('userscript loaded');
})();
