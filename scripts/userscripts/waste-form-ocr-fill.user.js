// ==UserScript==
// @name         Waste Form OCR & Fill (gtwoffice trash_add)
// @namespace    a-wiki
// @version      0.2.0
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
  const RECORDER_DEFAULT = 'ศุภศิษฎิ์ คงสุวรรณ';

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

  // --- FORM SCAN -------------------------------------------------------------
  // Scan form once, return { locKey: { rowNumber, label } } + inputRows array.
  // rowNumber = 1-based index across all <tr> in the table that hold an editable input.
  function scanFormForRowIndices() {
    const map = {};
    let table = null;
    let inputRows = [];

    for (const loc of Object.keys(ROW_LABEL_MAP)) {
      for (const lbl of ROW_LABEL_MAP[loc]) {
        const exact = $$('td, th').find(t => t.textContent.trim() === lbl);
        const partial = exact || $$('td, th').find(t => t.textContent.trim().includes(lbl));
        if (!partial) continue;
        const tr = partial.closest('tr');
        if (!tr) continue;
        if (!table) {
          table = tr.closest('table');
          if (table) {
            inputRows = Array.from(table.querySelectorAll('tr')).filter(r =>
              r.querySelector('input[type="text"], input[type="number"], input:not([type])'));
          }
        }
        const idx = inputRows.indexOf(tr);
        if (idx >= 0) { map[loc] = { rowNumber: idx + 1, label: lbl }; break; }
      }
    }
    return { map, table, inputRows };
  }

  function fillInputRow(inputRows, rowNumber, value) {
    const tr = inputRows && inputRows[rowNumber - 1];
    if (!tr) return false;
    const input = tr.querySelector('input[type="text"], input[type="number"], input:not([type])');
    if (!input) return false;
    return setInputValue(input, value);
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
    // Weight rows — prefer rowNumber-based fill (user-correctable), fallback to label
    const inputRows = options.inputRows || [];
    for (const r of plan.rows) {
      let filled = false;
      if (r.rowNumber && inputRows.length) {
        if (fillInputRow(inputRows, r.rowNumber, String(r.kg))) {
          report.push(`✓ Row ${r.rowNumber} (${r.location}) = ${r.kg} kg`);
          filled = true;
        }
      }
      if (!filled) {
        const labels = r.labels || ROW_LABEL_MAP[r.location] || [];
        for (const lbl of labels) {
          const inp = findRowInputByLabel(lbl);
          if (inp) {
            setInputValue(inp, String(r.kg));
            report.push(`✓ "${lbl}" = ${r.kg} kg (label fallback)`);
            filled = true;
            break;
          }
        }
      }
      if (!filled) report.push(`✗ ไม่พบช่องของ ${r.location} (row#=${r.rowNumber || '?'})`);
    }
    return report;
  }

  // --- LEARNING PROMPT -------------------------------------------------------
  // Build a Markdown prompt describing OCR vs user-corrected values.
  // Designed to be pasted into Claude Code / A-Wiki to update wiki/context/ocr-learning-log.md.
  function buildLearningPrompt(dayPlan, meta, date, fileName, originalOcrRaw) {
    const nowIso = new Date().toISOString().slice(0, 16).replace('T', ' ');
    const diffs = [];

    const rowsTable = dayPlan.rows.map((r, i) => {
      const locChanged = r.location !== r._originalLocation;
      const kgChanged = Math.abs((r.kg || 0) - (r._originalKg || 0)) > 0.001;
      const rowChanged = r.rowNumber !== r._originalRowNumber;
      const change = [
        locChanged ? `location: ${r._originalLocation}→${r.location}` : null,
        kgChanged ? `kg: ${r._originalKg}→${r.kg}` : null,
        rowChanged ? `row#: ${r._originalRowNumber}→${r.rowNumber}` : null,
      ].filter(Boolean).join('; ') || '—';
      if (locChanged || kgChanged || rowChanged) {
        diffs.push({ i, r, locChanged, kgChanged, rowChanged });
      }
      return `| ${i + 1} | ${r.location} | ${r.rowNumber ?? '?'} | ${r.kg} | ${r._originalLocation} | ${r._originalKg} | ${change} |`;
    }).join('\n');

    const logEntries = diffs.flatMap(d => {
      const lines = [];
      if (d.locChanged) lines.push(`| ${date} | location | ${d.r._originalLocation} | ${d.r.location} | row ${d.r.rowNumber} (${fileName}) |`);
      if (d.kgChanged) lines.push(`| ${date} | weight | ${d.r._originalKg} | ${d.r.kg} | row ${d.r.rowNumber} = ${d.r.location} (${fileName}) |`);
      if (d.rowChanged) lines.push(`| ${date} | row-mapping | ${d.r._originalLocation}→row${d.r._originalRowNumber} | ${d.r.location}→row${d.r.rowNumber} | user manual override |`);
      return lines;
    }).join('\n') || '_(ไม่มี correction — OCR ถูกต้องทั้งใบ)_';

    const confLine = meta && meta.confidence != null ? `**OCR confidence**: ${meta.confidence}\n` : '';
    const unclearLine = meta && meta.unclear && meta.unclear.length ? `**OCR unclear notes**: ${meta.unclear.join('; ')}\n` : '';

    return `# Waste OCR Correction Feedback — ${nowIso}

**Image**: ${fileName || '(unknown)'}
**Target date**: ${date}
${confLine}${unclearLine}**Corrections**: ${diffs.length}

## Per-row comparison (user-final vs OCR)

| # | Location (final) | Row # | kg (final) | OCR Location | OCR kg | Change |
|---|---|---|---|---|---|---|
${rowsTable}

## Action requested

อัปเดต \`wiki/context/ocr-learning-log.md\` → Corrections Log โดยเพิ่มแถว:

${logEntries}

ถ้า location/weight ที่ผิดซ้ำๆ → พิจารณาอัปเดต SYSTEM_PROMPT vocabulary ใน
\`wiki/synthesis/garbage-report-ocr.md\` และ \`scripts/userscripts/waste-form-ocr-fill.user.js\`

## Raw OCR (debug)

\`\`\`json
${JSON.stringify(originalOcrRaw, null, 2)}
\`\`\`
`;
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
      renderPreview(content, overlay, dayPlan, meta, dateChoice, arr, file.name);
      status.textContent = `อ่านได้ ${plan.totalRows} แถว, วันที่ ${dateChoice} — ตรวจค่า preview ก่อนกรอก`;
    } catch (e) {
      console.error(e);
      status.textContent = '❌ Error: ' + e.message;
    }
  }

  function renderPreview(content, overlay, dayPlan, meta, date, originalOcrRaw, fileName) {
    // Scan form once: map location → rowNumber; cache input rows for fill + override
    const { map: locRowMap, inputRows } = scanFormForRowIndices();

    // Snapshot OCR-original values per row + compute initial rowNumber from form
    dayPlan.rows.forEach(r => {
      r.rowNumber = locRowMap[r.location]?.rowNumber ?? null;
      r._originalLocation = r.location;
      r._originalKg = r.kg;
      r._originalRowNumber = r.rowNumber;
    });

    const allLocationKeys = Object.keys(ROW_LABEL_MAP);
    const metaWarn = meta ? `<div style="color:#b54;margin:6px 0">⚠ confidence=${meta.confidence}${meta.unclear?.length ? ', unclear: '+meta.unclear.join(', '):''}</div>` : '';

    const rowsHtml = dayPlan.rows.map((r, i) => {
      const opts = allLocationKeys.map(k =>
        `<option value="${k}"${k === r.location ? ' selected' : ''}>${k}</option>`
      ).join('');
      const rowVal = r.rowNumber ?? '';
      return `<tr>
        <td><select class="ocr-loc" data-i="${i}" style="width:120px">${opts}</select></td>
        <td><input type="number" class="ocr-row" data-i="${i}" value="${rowVal}" min="1" style="width:60px" /></td>
        <td><input type="number" step="0.01" class="ocr-kg" data-i="${i}" value="${r.kg}" /></td>
      </tr>`;
    }).join('');

    content.innerHTML = `
      ${metaWarn}
      <div style="font-size:13px;color:#555;margin-bottom:6px">วันที่: <b>${date}</b> · เวลาแรก: <b>${dayPlan.earliestTime || '-'}</b> · ${dayPlan.totalRows} entry</div>
      <table id="waste-ocr-preview">
        <thead><tr><th>Location</th><th>Row #</th><th>kg (แก้ได้)</th></tr></thead>
        <tbody>${rowsHtml || '<tr><td colspan="3">— ไม่มี row ที่ match ROW_LABEL_MAP —</td></tr>'}</tbody>
      </table>
      <div style="font-size:11px;color:#888;margin-top:-4px">เปลี่ยน Location → Row # คำนวณใหม่อัตโนมัติ · แก้ Row # เองได้เพื่อ override</div>
      <div class="waste-ocr-row">
        <label><input type="checkbox" id="ocr-fill-header" checked /> กรอก header (เวลา / Supplies / ผู้บันทึก)</label>
      </div>
      <div class="waste-ocr-row">
        <button class="waste-ocr-btn waste-ocr-primary" data-act="fill">✓ Fill Form</button>
        <button class="waste-ocr-btn waste-ocr-secondary" data-act="cancel">Cancel</button>
      </div>
      <div id="waste-ocr-log" style="display:none"></div>
      <div id="waste-ocr-learning" style="display:none;margin-top:12px;border-top:1px solid #ddd;padding-top:10px">
        <h3 style="margin:0 0 6px;font-size:14px">📚 Learning Prompt — สำหรับส่งให้ A-Wiki AI Agent</h3>
        <div style="font-size:11px;color:#666;margin-bottom:6px">Copy แล้ว paste เข้า Claude Code (cwd ใน A-Wiki) เพื่อให้ Agent อัปเดต <code>wiki/context/ocr-learning-log.md</code></div>
        <textarea id="ocr-learning-text" style="width:100%;height:200px;font-family:monospace;font-size:11px;box-sizing:border-box" readonly></textarea>
        <div class="waste-ocr-row">
          <button class="waste-ocr-btn waste-ocr-primary" data-act="copy-learning">📋 Copy</button>
          <button class="waste-ocr-btn waste-ocr-secondary" data-act="download-learning">⬇ Download .md</button>
        </div>
      </div>`;

    // Location dropdown → auto-update Row # via locRowMap
    content.querySelectorAll('.ocr-loc').forEach(sel => {
      sel.addEventListener('change', (e) => {
        const i = +e.target.dataset.i;
        const newLoc = e.target.value;
        dayPlan.rows[i].location = newLoc;
        const auto = locRowMap[newLoc]?.rowNumber;
        const rowInput = content.querySelector(`.ocr-row[data-i="${i}"]`);
        if (rowInput) {
          rowInput.value = auto ?? '';
          dayPlan.rows[i].rowNumber = auto ?? null;
        }
      });
    });

    // Manual Row # override
    content.querySelectorAll('.ocr-row').forEach(inp => {
      inp.addEventListener('input', (e) => {
        const i = +e.target.dataset.i;
        const v = parseInt(e.target.value, 10);
        dayPlan.rows[i].rowNumber = Number.isFinite(v) && v > 0 ? v : null;
      });
    });

    content.querySelector('[data-act="cancel"]').addEventListener('click', () => overlay.remove());
    content.querySelector('[data-act="fill"]').addEventListener('click', () => {
      // Pull latest values from all inputs (in case input event missed)
      content.querySelectorAll('.ocr-kg').forEach(inp => {
        const i = +inp.dataset.i;
        dayPlan.rows[i].kg = parseFloat(inp.value) || 0;
      });
      content.querySelectorAll('.ocr-loc').forEach(sel => {
        const i = +sel.dataset.i;
        dayPlan.rows[i].location = sel.value;
      });
      content.querySelectorAll('.ocr-row').forEach(inp => {
        const i = +inp.dataset.i;
        const v = parseInt(inp.value, 10);
        dayPlan.rows[i].rowNumber = Number.isFinite(v) && v > 0 ? v : null;
      });

      const fillHeader = content.querySelector('#ocr-fill-header').checked;
      const report = fillForm(dayPlan, { fillHeader, inputRows });
      const logEl = content.querySelector('#waste-ocr-log');
      logEl.style.display = 'block';
      logEl.textContent = report.join('\n');

      // Always build learning prompt — even when no edits (low-conf or just to confirm OCR was correct)
      const learnText = buildLearningPrompt(dayPlan, meta, date, fileName, originalOcrRaw);
      const learnDiv = content.querySelector('#waste-ocr-learning');
      const ta = content.querySelector('#ocr-learning-text');
      ta.value = learnText;
      learnDiv.style.display = 'block';

      content.querySelector('[data-act="copy-learning"]').onclick = () => {
        ta.removeAttribute('readonly');
        ta.select();
        try { document.execCommand('copy'); } catch (e) { warn(e); }
        ta.setAttribute('readonly', 'true');
        if (navigator.clipboard) navigator.clipboard.writeText(ta.value).catch(() => {});
      };
      content.querySelector('[data-act="download-learning"]').onclick = () => {
        const blob = new Blob([learnText], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ocr-correction-${date}-${Date.now()}.md`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      };
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
