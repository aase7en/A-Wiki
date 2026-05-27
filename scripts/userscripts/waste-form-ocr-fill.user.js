// ==UserScript==
// @name         Waste Form OCR & Fill (gtwoffice trash_add)
// @namespace    a-wiki
// @version      0.8.1
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

  // Explicit form field IDs [verified 2026-05-26 via DOM dump]
  const FIELD_IDS = {
    date: 'TRASH_DATE',      // datepicker (BE format DD/MM/YYYY+543)
    time: 'TRASH_TIME',      // masked time input
    year: 'TRASH_YEAR',      // select (BE year)
    supplies: 'TRASH_SUP',   // Select2: js-example-basic-s
    recorder: 'TRASH_USER',  // Select2: js-example-basic-s
  };

  // Location → row index (1-25, the Nth TRASH_SUB_QTY[] input)
  // Reference: wiki/synthesis/waste-form-automation.md
  const LOCATION_TO_ROW = {
    OPD: 12,        // ขยะทั่วไป OPD
    Ward: 14,       // ขยะทั่วไป Ward
    ER: 8,          // ขยะทั่วไป ER
    โรงครัว: 9,     // ขยะทั่วไป โรงครัว
    บริหาร: 10,     // ขยะทั่วไป บริหาร
    ฝังเข็ม: 11,    // ขยะทั่วไป ฝังเข็ม
    เวช: 13,        // ขยะทั่วไป เวชฯ
    ห้องช่าง: 15,
    ซักฟอก: 16,
    แฟลต: 17,
    แผนไทย: 18,     // ขยะทั่วไป แพทย์แผนไทย
  };

  // Compound locations → split equally across rows
  const COMPOUND_LOCATIONS = {
    'OPD+ER': ['OPD', 'ER'],
    'แผนไทย+ฝังเข็ม': ['แผนไทย', 'ฝังเข็ม'],
  };

  // --- USER SETTINGS (persisted) --------------------------------------------
  function getSettings() {
    return GM_getValue('ocr_settings', { suppliesValue: '', recorderValue: '', customHints: '' });
  }
  function saveSettings(s) { GM_setValue('ocr_settings', s); }
  function getRowOverrides() {
    return GM_getValue('ocr_row_overrides', {}); // {location: rowIdx}
  }
  function saveRowOverrides(o) { GM_setValue('ocr_row_overrides', o); }
  function resolveRowIdx(location) {
    const overrides = getRowOverrides();
    return overrides[location] ?? LOCATION_TO_ROW[location];
  }

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

  function buildSystemPrompt() {
    const hints = (getSettings().customHints || '').trim();
    if (!hints) return SYSTEM_PROMPT;
    return SYSTEM_PROMPT + `\n\nADDITIONAL USER CORRECTIONS (apply these — they override defaults):\n${hints}`;
  }

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

  // --- CACHE (last OCR result, 24h TTL) -------------------------------------
  const CACHE_KEY = 'last_ocr_cache';
  const CACHE_TTL_MS = 24 * 60 * 60 * 1000;

  function saveCache(arr, fileName) {
    GM_setValue(CACHE_KEY, {
      ts: Date.now(),
      fileName: fileName || 'unknown',
      rows: arr,
      filled: {}, // {dateISO: timestamp} — track which days have been filled this session
    });
  }
  function loadCache() {
    const entry = GM_getValue(CACHE_KEY, null);
    if (!entry || !entry.rows) return null;
    if (Date.now() - entry.ts > CACHE_TTL_MS) return null;
    return entry;
  }
  function markFilled(dateISO) {
    const entry = loadCache();
    if (!entry) return;
    entry.filled = entry.filled || {};
    entry.filled[dateISO] = Date.now();
    GM_setValue(CACHE_KEY, entry);
  }
  function clearCache() {
    GM_setValue(CACHE_KEY, null);
  }
  function cacheAgeText(ts) {
    const min = Math.floor((Date.now() - ts) / 60000);
    if (min < 1) return 'เมื่อสักครู่';
    if (min < 60) return `${min} นาทีก่อน`;
    const hr = Math.floor(min / 60);
    return `${hr} ชม.${min % 60 ? ' '+(min%60)+' นาที' : ''}ก่อน`;
  }

  // --- DATE HELPERS (Thai BE ↔ ISO CE) --------------------------------------
  function thaiDateBE(iso) {
    // "2026-04-30" → "30/04/2569"
    if (!iso) return '';
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
    if (!m) return iso;
    const [, y, mo, d] = m;
    return `${d}/${mo}/${+y + 543}`;
  }
  function thaiDateCE(iso) {
    // "2026-04-30" → "30/04/2026" (dd/mm/yyyy CE — format ที่ picker เก็บภายใน)
    if (!iso) return '';
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
    if (!m) return iso;
    const [, y, mo, d] = m;
    return `${d}/${mo}/${y}`;
  }
  function parseAnyDate(s) {
    // accept "2026-04-30" or "30/04/2569" or "30/04/2026"
    if (!s) return null;
    s = s.trim();
    let m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
    if (m) return s;
    m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(s);
    if (m) {
      let [, d, mo, y] = m;
      y = +y;
      if (y > 2400) y -= 543; // BE → CE
      return `${y}-${String(+mo).padStart(2,'0')}-${String(+d).padStart(2,'0')}`;
    }
    return null;
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
        system_instruction: { parts: [{ text: buildSystemPrompt() }] },
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
        timeout: 60000,
        headers: { 'Content-Type': 'application/json' },
        data: JSON.stringify(body),
        onload: (resp) => {
          try {
            if (resp.status < 200 || resp.status >= 300) {
              return reject(new Error(`HTTP ${resp.status}: ${resp.responseText?.slice(0, 200)}`));
            }
            const j = JSON.parse(resp.responseText);
            if (j.error) return reject(new Error(j.error.message || 'Gemini error'));
            const text = j.candidates?.[0]?.content?.parts?.[0]?.text || '';
            const clean = text.replace(/^```json\s*|\s*```$/g, '').trim();
            if (!clean) return reject(new Error('Empty response from Gemini'));
            resolve(JSON.parse(clean));
          } catch (e) { reject(new Error('Parse error: ' + e.message)); }
        },
        onerror: (e) => reject(new Error('Network error: ' + (e?.error || 'unknown'))),
        ontimeout: () => reject(new Error('Timeout after 60s')),
      });
    });
  }

  async function geminiCallRetry(apiKey, base64Data, mimeType, maxRetry = 2) {
    let lastErr;
    for (let i = 0; i <= maxRetry; i++) {
      try { return await geminiCall(apiKey, base64Data, mimeType); }
      catch (e) {
        lastErr = e;
        warn(`Gemini attempt ${i+1}/${maxRetry+1} failed:`, e.message);
        if (i < maxRetry) await new Promise(r => setTimeout(r, 1500 * (i + 1)));
      }
    }
    throw lastErr;
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

    // 4. map location → row index (1-25)
    const result = [];
    for (const [loc, kg] of Object.entries(byLocation)) {
      const rowIdx = resolveRowIdx(loc);
      if (!rowIdx) { warn('unknown location:', loc); continue; }
      result.push({ location: loc, rowIdx, kg: Math.round(kg * 100) / 100 });
    }
    result.sort((a, b) => a.rowIdx - b.rowIdx);

    // 5. earliest time + dates seen
    const times = filtered.map(r => r.time).filter(Boolean).sort();
    const dates = [...new Set(filtered.map(r => r.date).filter(Boolean))].sort();
    return { rows: result, earliestTime: times[0] || null, dates, totalRows: filtered.length };
  }

  // --- FORM FILL -------------------------------------------------------------
  const INPUT_SEL = 'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="checkbox"]):not([type="radio"]), textarea, [contenteditable="true"]';

  function normalizeText(s) {
    return (s || '').replace(/\s+/g, ' ').trim();
  }
  function fuzzyEq(a, b) {
    return normalizeText(a).replace(/[\s:*]/g, '') === normalizeText(b).replace(/[\s:*]/g, '');
  }
  function fuzzyIncludes(haystack, needle) {
    return normalizeText(haystack).replace(/\s/g, '').includes(normalizeText(needle).replace(/\s/g, ''));
  }
  function isInOurOverlay(el) {
    return !!el.closest?.('#waste-ocr-overlay');
  }

  // ROW MATCH (v0.5): นับ TRASH_SUB_QTY[] เป็น index 1-25 ตามลำดับ DOM
  function findRowQtyInputByIdx(idx) {
    if (!idx) return null;
    const qtyInputs = $$('input[name="TRASH_SUB_QTY[]"]').filter(i => !isInOurOverlay(i));
    return qtyInputs[idx - 1] || null;
  }

  // (legacy — kept for debug only)
  function findRowInputByLabel(labelText) {
    const trs = $$('tr').filter(tr => !isInOurOverlay(tr));
    // 1) Primary: หา input.fo13 ที่ value match
    let matches = [];
    for (const tr of trs) {
      const labelInput = tr.querySelector('input.fo13, input[class*="fo13"]');
      if (!labelInput) continue;
      const v = labelInput.value || '';
      if (fuzzyEq(v, labelText)) matches.push({ tr, score: 3 });
      else if (fuzzyIncludes(v, labelText)) matches.push({ tr, score: 2 });
    }
    // 2) Fallback: any first text-input in row with value match
    if (matches.length === 0) {
      for (const tr of trs) {
        const firstInput = tr.querySelector('input[type="text"], input:not([type])');
        if (!firstInput) continue;
        const v = firstInput.value || '';
        if (fuzzyEq(v, labelText)) matches.push({ tr, score: 1 });
        else if (fuzzyIncludes(v, labelText)) matches.push({ tr, score: 0.5 });
      }
    }
    // 3) Fallback: td.textContent (เผื่อบาง row ใช้ plain text)
    if (matches.length === 0) {
      for (const tr of trs) {
        const tds = Array.from(tr.querySelectorAll('td, th'));
        if (tds.some(td => fuzzyIncludes(td.textContent, labelText))) {
          matches.push({ tr, score: 0.3 });
        }
      }
    }
    if (matches.length === 0) return null;
    matches.sort((a, b) => b.score - a.score);
    const tr = matches[0].tr;
    // Return qty input (TRASH_SUB_QTY[]) — fallback ไปอีก input ที่ไม่ใช่ label
    return tr.querySelector('input[name="TRASH_SUB_QTY[]"]')
      || tr.querySelector('input[name*="QTY"]')
      || tr.querySelector('input.text-center')
      || Array.from(tr.querySelectorAll(INPUT_SEL)).find(i => !i.classList.contains('fo13'))
      || null;
  }

  function isSelect2(el) {
    return el && (el.classList?.contains('js-example-basic-s') || el.classList?.contains('select2-hidden-accessible'));
  }

  function setInputValue(el, value) {
    if (!el) return false;
    value = String(value);
    const $jq = window.jQuery || window.$;
    // Special: Select2 widget — must use jQuery API
    if (el.tagName === 'SELECT' && isSelect2(el) && $jq) {
      try { $jq(el).val(value).trigger('change'); return true; } catch {}
    }
    try { el.focus?.(); } catch {}
    // Native setter (React-safe)
    const proto = el.tagName === 'SELECT' ? HTMLSelectElement.prototype
                : el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype
                : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    try { if (setter) setter.call(el, value); else el.value = value; } catch { el.value = value; }
    // Event sequence
    const fire = (type, EventCls = Event, init = { bubbles: true }) => {
      try { el.dispatchEvent(new EventCls(type, init)); } catch {}
    };
    fire('keydown', KeyboardEvent);
    fire('input');
    fire('keyup', KeyboardEvent);
    fire('change');
    if ($jq) {
      try { $jq(el).val(value).trigger('input').trigger('change').trigger('keyup'); } catch {}
    }
    // Avoid blur for datepicker (may reset value)
    if (!el.classList?.contains('datepicker')) {
      try { el.blur?.(); } catch {}
    }
    return true;
  }

  function selectOptionByText(selectEl, textPart) {
    if (!selectEl) return false;
    let found = null;
    for (const opt of selectEl.options) {
      const t = normalizeText(opt.text);
      const tgt = normalizeText(textPart);
      if (t === tgt) { found = opt; break; }
      if (!found && t.includes(tgt)) found = opt;
    }
    if (!found) return false;
    return setInputValue(selectEl, found.value);
  }
  function selectOptionByValue(selectEl, value) {
    if (!selectEl || value == null || value === '') return false;
    return setInputValue(selectEl, String(value));
  }

  function findHeaderField(labelSubstr) {
    const target = normalizeText(labelSubstr).replace(/[:*]/g, '').trim();

    // 1) <label for="X"> → find #X
    const labels = $$('label').filter(l => !isInOurOverlay(l));
    for (const lab of labels) {
      const txt = normalizeText(lab.textContent).replace(/[:*]/g, '').trim();
      if (!txt.startsWith(target) && !txt.includes(target)) continue;
      const forAttr = lab.getAttribute('for');
      if (forAttr) {
        const el = document.getElementById(forAttr);
        if (el && !isInOurOverlay(el)) return el;
      }
      // No 'for' — look at siblings / parent's children
      let sib = lab.nextElementSibling;
      while (sib) {
        if (sib.matches?.('input, select, textarea') && !isInOurOverlay(sib)) return sib;
        const inner = sib.querySelector?.('input:not([type="hidden"]), select, textarea');
        if (inner && !isInOurOverlay(inner)) return inner;
        sib = sib.nextElementSibling;
      }
      // parent group
      let cur = lab.parentElement;
      for (let d = 0; d < 3 && cur; d++) {
        const inp = cur.querySelector?.('input:not([type="hidden"]), select, textarea');
        if (inp && !lab.contains(inp) && !isInOurOverlay(inp)) return inp;
        cur = cur.parentElement;
      }
    }

    // 2) Any text leaf (th/td/div/span/p/strong/b) containing label text → walk up parents
    const all = $$('th, td, div, span, p, strong, b, dt')
      .filter(el => !isInOurOverlay(el))
      .filter(el => {
        const txt = normalizeText(el.textContent).replace(/[:*]/g, '').trim();
        // ใช้ "starts with" เพื่อหลีกเลี่ยง match container ใหญ่
        return txt.startsWith(target) && txt.length < target.length + 15;
      });
    for (const el of all) {
      let cur = el;
      for (let d = 0; d < 5 && cur; d++) {
        const inp = cur.parentElement?.querySelector?.('input:not([type="hidden"]), select, textarea');
        if (inp && !el.contains(inp) && !isInOurOverlay(inp)) return inp;
        cur = cur.parentElement;
      }
    }
    return null;
  }

  async function fillForm(plan, options) {
    const report = [];
    const settings = getSettings();

    if (options.fillHeader) {
      // วันที่บันทึก (datepicker เก็บ value เป็น dd/mm/yyyy CE — แสดง BE)
      if (options.dateISO) {
        const dateBE = thaiDateBE(options.dateISO);
        const dateCE = thaiDateCE(options.dateISO);
        const dateEl = document.getElementById(FIELD_IDS.date);
        if (dateEl) {
          const ok = await setDatepickerValue(dateEl, dateCE, dateBE);
          if (ok) report.push(`✓ วันที่บันทึก = ${dateBE} (เก็บภายในเป็น ${dateCE})`);
          else report.push(`⚠ วันที่บันทึก ไม่ติด (ค่าตอนนี้ "${dateEl.value}") — โปรดคลิกช่องแล้วเลือก ${dateBE} เอง`);
        } else report.push(`✗ ไม่พบ #${FIELD_IDS.date}`);
        // ปี (BE select)
        const yearEl = document.getElementById(FIELD_IDS.year);
        const yBE = String(parseInt(options.dateISO.slice(0, 4), 10) + 543);
        if (yearEl) {
          if (yearEl.tagName === 'SELECT' ? selectOptionByText(yearEl, yBE) : setInputValue(yearEl, yBE)) {
            report.push(`✓ ปี = ${yBE}`);
          } else report.push(`⚠ ปี: ไม่พบ option ${yBE}`);
        }
      }
      // เวลา (masked input)
      if (plan.earliestTime) {
        const timeEl = document.getElementById(FIELD_IDS.time);
        if (timeEl) { setInputValue(timeEl, plan.earliestTime); report.push(`✓ เวลา = ${plan.earliestTime}`); }
        else report.push(`✗ ไม่พบ #${FIELD_IDS.time}`);
      }
      // Supplies (Select2 — ใช้ value จาก settings)
      const supEl = document.getElementById(FIELD_IDS.supplies);
      if (supEl) {
        if (settings.suppliesValue && selectOptionByValue(supEl, settings.suppliesValue)) {
          const txt = supEl.options[supEl.selectedIndex]?.text;
          report.push(`✓ Supplies = ${txt}`);
        } else {
          report.push(`⚠ Supplies: ไม่ได้ตั้งค่าใน Settings (ใช้ค่าฟอร์มเดิม)`);
        }
      }
      // ผู้บันทึก (Select2 — ใช้ value จาก settings)
      const recEl = document.getElementById(FIELD_IDS.recorder);
      if (recEl) {
        if (settings.recorderValue && selectOptionByValue(recEl, settings.recorderValue)) {
          const txt = recEl.options[recEl.selectedIndex]?.text;
          report.push(`✓ ผู้บันทึก = ${txt}`);
        } else {
          report.push(`⚠ ผู้บันทึก: ไม่ได้ตั้งค่าใน Settings`);
        }
      }
    }

    // Weight rows — ใช้ row index (1-25)
    for (const r of plan.rows) {
      const inp = findRowQtyInputByIdx(r.rowIdx);
      if (inp) {
        setInputValue(inp, String(r.kg));
        report.push(`✓ row ${r.rowIdx} (${r.location}) = ${r.kg} kg`);
      } else {
        report.push(`✗ ไม่พบ qty input ของ row ${r.rowIdx} (${r.location})`);
      }
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
        <h2>📷 OCR ใบรายงานขยะ → กรอกฟอร์ม
          <button class="waste-ocr-btn waste-ocr-secondary" data-act="toggle-settings" style="float:right;padding:4px 10px;font-size:12px">⚙ Settings</button>
        </h2>
        <div id="waste-ocr-settings" style="display:none"></div>
        <div id="waste-ocr-cache-banner"></div>
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
    overlay.querySelector('[data-act="toggle-settings"]').addEventListener('click', () => {
      const panel = overlay.querySelector('#waste-ocr-settings');
      if (panel.style.display === 'none') {
        renderSettingsPanel(panel);
        panel.style.display = 'block';
      } else {
        panel.style.display = 'none';
      }
    });

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

    // เช็ค cache → ถ้ามี แสดง banner + auto-load
    const cache = loadCache();
    if (cache) {
      const dates = [...new Set(cache.rows.filter(r => r && !r._meta).map(r => r.date).filter(Boolean))].sort();
      const banner = overlay.querySelector('#waste-ocr-cache-banner');
      banner.innerHTML = `
        <div style="background:#e7f5e7;border:1px solid #b6dab6;padding:10px;border-radius:6px;margin-bottom:8px">
          <b>💾 พบ OCR ล่าสุด</b> · ${cache.fileName} · ${cacheAgeText(cache.ts)} · ${dates.length} วัน
          <div class="waste-ocr-row" style="margin-top:6px">
            <button class="waste-ocr-btn waste-ocr-primary" data-act="use-cache">ใช้ของเดิม</button>
            <button class="waste-ocr-btn waste-ocr-danger" data-act="clear-cache">ล้าง cache</button>
            <span style="font-size:12px;color:#666">หรืออัปโหลดรูปใหม่ด้านล่าง (จะแทน cache)</span>
          </div>
        </div>`;
      banner.querySelector('[data-act="use-cache"]').addEventListener('click', () => {
        showDayPicker(overlay, cache.rows, cache.fileName);
      });
      banner.querySelector('[data-act="clear-cache"]').addEventListener('click', () => {
        clearCache();
        banner.innerHTML = '';
      });
    }
  }

  // --- Searchable dropdown (พิมพ์ค้นหาได้) ---
  // options: [{value, text}], onChange(newValue)
  function makeSearchableDropdown(host, options, initialValue, onChange) {
    const initial = options.find(o => String(o.value) === String(initialValue));
    let selectedValue = initialValue;
    host.innerHTML = `
      <div class="sd-wrap" style="position:relative">
        <input class="sd-input" type="text" value="${(initial?.text||'').replace(/"/g,'&quot;')}"
               placeholder="พิมพ์ค้นหา ชื่อ/นามสกุล…" autocomplete="off"
               style="width:100%;padding:6px 8px;border:1px solid #ccc;border-radius:4px;box-sizing:border-box" />
        <div class="sd-list" style="display:none;position:absolute;top:100%;left:0;right:0;background:#fff;
                                    border:1px solid #ccc;max-height:240px;overflow-y:auto;z-index:100001;
                                    border-radius:4px;box-shadow:0 4px 12px rgba(0,0,0,.15)"></div>
      </div>`;
    const input = host.querySelector('.sd-input');
    const list = host.querySelector('.sd-list');
    let activeIdx = -1, currentFiltered = [];

    function renderList(filter = '') {
      const f = normalizeText(filter).toLowerCase();
      currentFiltered = !f
        ? options.slice(0, 100)
        : options.filter(o => normalizeText(o.text).toLowerCase().includes(f)).slice(0, 100);
      list.innerHTML = currentFiltered.length
        ? currentFiltered.map((o, i) => {
            const isSel = String(o.value) === String(selectedValue);
            return `<div class="sd-item" data-i="${i}"
                style="padding:6px 10px;cursor:pointer;${isSel?'background:#e7e0f5;font-weight:600':''}">${o.text}</div>`;
          }).join('')
        : '<div style="padding:8px;color:#999">ไม่พบ</div>';
      list.querySelectorAll('.sd-item').forEach(el => {
        el.addEventListener('mousedown', (e) => { e.preventDefault(); pickIdx(+el.dataset.i); });
        el.addEventListener('mouseenter', () => {
          list.querySelectorAll('.sd-item').forEach(x => x.style.background = '');
          el.style.background = '#f0e6ff';
        });
      });
      activeIdx = -1;
    }
    function pickIdx(i) {
      const o = currentFiltered[i];
      if (!o) return;
      selectedValue = o.value;
      input.value = o.text;
      list.style.display = 'none';
      onChange?.(selectedValue);
    }
    input.addEventListener('focus', () => { renderList(input.value); list.style.display = 'block'; });
    input.addEventListener('input', () => { renderList(input.value); list.style.display = 'block'; });
    input.addEventListener('blur', () => { setTimeout(() => { list.style.display = 'none'; }, 200); });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown') { e.preventDefault(); activeIdx = Math.min(activeIdx + 1, currentFiltered.length - 1); highlightActive(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); activeIdx = Math.max(activeIdx - 1, 0); highlightActive(); }
      else if (e.key === 'Enter') { e.preventDefault(); if (activeIdx >= 0) pickIdx(activeIdx); }
      else if (e.key === 'Escape') { list.style.display = 'none'; }
    });
    function highlightActive() {
      list.querySelectorAll('.sd-item').forEach((el, i) => {
        el.style.background = i === activeIdx ? '#f0e6ff' : (String(currentFiltered[i].value) === String(selectedValue) ? '#e7e0f5' : '');
        if (i === activeIdx) el.scrollIntoView({ block: 'nearest' });
      });
    }
    renderList();
    return { getValue: () => selectedValue };
  }

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  function findVueInstance(el) {
    // Vue 2 attaches __vue__ to root DOM of each component
    let cur = el;
    while (cur) {
      if (cur.__vue__) return { vue: cur.__vue__, version: 2 };
      if (cur.__vueParentComponent) return { vue: cur.__vueParentComponent, version: 3 };
      cur = cur.parentElement;
    }
    return null;
  }

  function nativeSet(el, value) {
    const proto = el.tagName === 'SELECT' ? HTMLSelectElement.prototype
                : el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype
                : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    if (setter) setter.call(el, value); else el.value = value;
  }

  // --- Datepicker (เก็บ value เป็น dd/mm/yyyy CE — Vue convert เป็น BE สำหรับ display) ---
  async function setDatepickerValue(el, valueCE, valueBE) {
    if (!el) return false;
    log('=== datepicker debug ===');
    log('  target id:', el.id, '| current:', el.value, '| want CE:', valueCE, '| display BE:', valueBE);

    const wasReadonly = el.hasAttribute('readonly') || el.readOnly;
    log('  readonly?', wasReadonly, '| data-date-format:', el.getAttribute('data-date-format'));

    if (wasReadonly) { el.removeAttribute('readonly'); el.readOnly = false; }
    nativeSet(el, valueCE);
    el.dispatchEvent(new InputEvent('input', { bubbles: true, cancelable: true, data: valueCE }));
    el.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
    log(`  [CE set] after input event → el.value=${el.value}`);

    const found = findVueInstance(el);
    if (found) {
      log(`  Vue ${found.version} instance found, keys:`, Object.keys(found.vue).slice(0, 15));
      const v = found.vue;
      for (const prop of ['value', 'date', 'inputValue', 'selectedDate', 'modelValue', 'localValue']) {
        if (prop in v && v[prop] !== undefined) {
          try {
            log(`  trying vue.${prop} = '${valueCE}' (was '${v[prop]}')`);
            v[prop] = valueCE;
          } catch (e) { warn(`  vue.${prop} set threw:`, e.message); }
        }
      }
      try { v.$emit?.('input', valueCE); v.$emit?.('change', valueCE); } catch {}
    } else {
      log('  no Vue instance found on el or ancestors');
    }

    await sleep(100);
    log(`  [after 100ms] el.value=${el.value}`);

    // กระตุ้น picker re-render (CE → BE display) ผ่าน focus+blur
    log('  triggering picker re-render via focus+blur');
    try { el.focus(); } catch {}
    await sleep(80);
    try { el.blur(); } catch {}
    await sleep(100);
    log(`  [after focus+blur] el.value=${el.value}`);

    // ถ้า display ยังไม่เป็น BE → ลอง open+close picker
    let valueIsBE = (el.value === valueBE);
    if (!valueIsBE) {
      log('  display still CE — trying open picker + Escape to close');
      try { el.click(); } catch {}
      await sleep(250);
      // ส่ง Escape เพื่อปิด picker (ต้องส่งหลายที่เพราะ key handler อาจอยู่ที่ document)
      for (const target of [el, document, document.body]) {
        try {
          target.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', keyCode: 27, which: 27, bubbles: true }));
        } catch {}
      }
      // ถ้า picker ไม่ปิดจาก Esc — คลิกข้างนอก
      await sleep(150);
      try { document.body.click(); } catch {}
      await sleep(200);
      log(`  [after open+close] el.value=${el.value}`);
      valueIsBE = (el.value === valueBE);
    }

    // ตรวจ display element ที่แสดง BE (text node)
    let displayOK = false;
    const dateRegex = /\b\d{2}\/\d{2}\/25\d{2}\b/;
    const textNodes = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(n) {
        if (!n.nodeValue || !dateRegex.test(n.nodeValue)) return NodeFilter.FILTER_REJECT;
        if (n.parentElement?.closest('#waste-ocr-overlay')) return NodeFilter.FILTER_REJECT;
        const tag = n.parentElement?.tagName;
        if (tag === 'SCRIPT' || tag === 'STYLE') return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    let tn;
    while ((tn = walker.nextNode())) textNodes.push(tn);
    if (textNodes.length > 0) {
      log(`  ${textNodes.length} text node(s) with BE date:`);
      textNodes.forEach((n, i) => {
        const matched = (n.nodeValue.match(dateRegex)||[])[0];
        log(`    text[${i}] "${matched}" in <${n.parentElement?.tagName?.toLowerCase()}> class="${(n.parentElement?.className||'').slice(0,40)}"`);
        if (matched === valueBE) displayOK = true;
      });
    }

    const valueOK = el.value === valueCE || el.value === valueBE
                  || el.value.includes(valueCE.split('/').slice(0,2).join('/'));
    log(`  value check: el.value="${el.value}" matches CE/BE? ${valueOK}`);
    log(`  display check: BE "${valueBE}" appears? ${displayOK || valueIsBE}`);

    if (valueOK || valueIsBE || displayOK) {
      log('=== datepicker done, success: true ===');
      if (wasReadonly) el.setAttribute('readonly', '');
      return true;
    }

    // Fallback: ลองส่ง BE ดู (เผื่อ picker บางตัวรับ BE)
    log('  CE didn\'t stick — trying BE format as fallback');
    nativeSet(el, valueBE);
    el.dispatchEvent(new InputEvent('input', { bubbles: true, cancelable: true, data: valueBE }));
    el.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
    await sleep(500);
    log(`  [BE attempt after 500ms] el.value=${el.value}`);
    if (el.value === valueBE || el.value === valueCE) {
      log('=== datepicker done, success: true (BE fallback) ===');
      if (wasReadonly) el.setAttribute('readonly', '');
      return true;
    }

    // C) คลิกเปิด picker → คลิกวันที่
    log('  trying picker UI click fallback');
    if (wasReadonly) el.setAttribute('readonly', '');
    const ok = await clickPickerSelectDate(el, valueBE);
    log('=== datepicker done, success:', ok, ', final el.value:', el.value, '===');
    return ok;
  }

  // Click strategy: เปิด picker → หา « » buttons → คลิก day cell
  async function clickPickerSelectDate(inputEl, valueBE) {
    const m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(valueBE);
    if (!m) return false;
    const [, dStr, moStr, yBEStr] = m;
    const day = +dStr, month = +moStr, beYear = +yBEStr;
    const monthNames = ['มกราคม','กุมภาพันธ์','มีนาคม','เมษายน','พฤษภาคม','มิถุนายน',
                        'กรกฎาคม','สิงหาคม','กันยายน','ตุลาคม','พฤศจิกายน','ธันวาคม'];
    const targetMonthName = monthNames[month - 1];

    // เปิด picker
    inputEl.click();
    inputEl.focus();
    await sleep(250);

    // หา picker DOM — ค้นหา element ที่มีเดือนไทย + ปี BE และ visible
    let picker = null;
    const allDivs = $$('div, table, section').filter(el => !isInOurOverlay(el) && el.offsetParent !== null);
    for (const d of allDivs) {
      const txt = normalizeText(d.textContent);
      if (monthNames.some(mn => txt.includes(mn)) && /256\d|257\d/.test(txt) && txt.length < 800) {
        picker = d;
        log('  picker candidate found, classList:', d.className, 'tag:', d.tagName);
        break;
      }
    }
    if (!picker) { warn('  picker not found after click — date field may not be a popover picker'); return false; }

    // Navigate to target month/year
    for (let step = 0; step < 80; step++) {
      const headerEl = picker.querySelector('.picker-switch, .datepicker-switch, [class*="switch"], th.dow ~ th, thead th, .header, .title')
                    || Array.from(picker.querySelectorAll('*')).find(e => monthNames.some(mn => e.textContent.trim().startsWith(mn)));
      const headerText = headerEl?.textContent?.trim() || '';
      if (headerText.includes(targetMonthName) && headerText.includes(String(beYear))) {
        log(`  reached month: ${headerText}`);
        break;
      }
      const headerYear = parseInt(headerText.match(/256\d|257\d/)?.[0] || '0', 10);
      const headerMonthIdx = monthNames.findIndex(mn => headerText.includes(mn));
      const curOrdinal = headerYear * 12 + (headerMonthIdx + 1);
      const tgtOrdinal = beYear * 12 + month;
      const nextBtn = picker.querySelector('.next, [class*="next"], button[aria-label*="next" i], .fa-chevron-right, .fa-angle-right')?.closest('button, a, td, th, span, div');
      const prevBtn = picker.querySelector('.prev, [class*="prev"], button[aria-label*="prev" i], .fa-chevron-left, .fa-angle-left')?.closest('button, a, td, th, span, div');
      const btn = tgtOrdinal > curOrdinal ? nextBtn : prevBtn;
      if (!btn) { warn('  nav buttons not found in picker'); return false; }
      btn.click();
      await sleep(60);
    }

    // คลิก day cell
    const dayCells = $$('td, .day, [class*="day"], button', picker).filter(c =>
      c.textContent.trim() === String(day) &&
      !c.classList.contains('old') && !c.classList.contains('new') &&
      !c.classList.contains('disabled') && !c.classList.contains('off')
    );
    if (dayCells.length === 0) { warn('  day cell', day, 'not found'); return false; }
    dayCells[0].click();
    await sleep(150);
    log('  clicked day', day, 'final el.value:', inputEl.value);
    return inputEl.value === valueBE || inputEl.value.startsWith(String(day).padStart(2, '0'));
  }

  function renderSettingsPanel(panel) {
    const settings = getSettings();
    const supEl = document.getElementById(FIELD_IDS.supplies);
    const recEl = document.getElementById(FIELD_IDS.recorder);
    const overrides = getRowOverrides();
    const overrideText = Object.keys(overrides).length
      ? Object.entries(overrides).map(([loc, idx]) => `${loc}→${idx}`).join(', ')
      : '(ไม่มี — ใช้ค่า default)';

    const readOptions = (selectEl) => selectEl
      ? Array.from(selectEl.options).filter(o => o.value !== '').map(o => ({ value: o.value, text: o.text }))
      : [];
    const supOptions = readOptions(supEl);
    const recOptions = readOptions(recEl);

    panel.innerHTML = `
      <div style="background:#f5f0ff;border:1px solid #d0c0ee;padding:12px;border-radius:8px;margin-bottom:10px">
        <div style="font-weight:600;margin-bottom:8px">⚙ Settings (เก็บใน Tampermonkey storage)</div>

        <div style="margin-bottom:10px">
          <label style="display:block;font-size:13px;margin-bottom:3px">Supplies (อบต. / หน่วยงาน):</label>
          <div id="set-supplies-host"></div>
        </div>

        <div style="margin-bottom:10px">
          <label style="display:block;font-size:13px;margin-bottom:3px">ผู้บันทึก (พิมพ์ค้นหา ชื่อ/นามสกุล):</label>
          <div id="set-recorder-host"></div>
        </div>

        <div style="margin-bottom:8px">
          <label style="display:block;font-size:13px;margin-bottom:3px">
            🧠 Custom OCR hints (สอน Gemini ให้แม่นขึ้น — ต่อท้าย system prompt):
          </label>
          <textarea id="set-hints" rows="5" placeholder="ตัวอย่าง:&#10;- ลายมือ 'อ้อย' มักอ่านเป็น 'บอย' — ให้อ่านเป็น 'อ้อย'&#10;- น้ำหนัก 12 บางครั้งอ่านเป็น 17 — ตรวจซ้ำเลข 1-2-7&#10;- location 'จิตเวช' → ใช้คำว่า 'เวช'"
            style="width:100%;padding:6px;font-family:monospace;font-size:12px;box-sizing:border-box">${(settings.customHints || '').replace(/</g,'&lt;')}</textarea>
        </div>

        <div style="margin-bottom:8px;font-size:12px;color:#666">
          Row overrides (ปุ่ม Fill จะเซฟอัตโนมัติเมื่อแก้ Row # ใน preview): <code>${overrideText}</code>
          ${Object.keys(overrides).length ? '<button class="waste-ocr-btn waste-ocr-danger" data-act="clear-overrides" style="padding:3px 8px;font-size:11px;margin-left:6px">ล้าง</button>' : ''}
        </div>

        <div class="waste-ocr-row">
          <button class="waste-ocr-btn waste-ocr-primary" data-act="save-settings">💾 บันทึก settings</button>
          <span id="set-saved-msg" style="color:#28a745;font-size:12px;display:none">✓ บันทึกแล้ว</span>
        </div>
      </div>`;

    const supDD = makeSearchableDropdown(panel.querySelector('#set-supplies-host'), supOptions, settings.suppliesValue);
    const recDD = makeSearchableDropdown(panel.querySelector('#set-recorder-host'), recOptions, settings.recorderValue);

    panel.querySelector('[data-act="save-settings"]').addEventListener('click', () => {
      saveSettings({
        suppliesValue: supDD.getValue(),
        recorderValue: recDD.getValue(),
        customHints: panel.querySelector('#set-hints').value,
      });
      const msg = panel.querySelector('#set-saved-msg');
      msg.style.display = 'inline';
      setTimeout(() => { msg.style.display = 'none'; }, 2000);
    });
    panel.querySelector('[data-act="clear-overrides"]')?.addEventListener('click', () => {
      saveRowOverrides({});
      renderSettingsPanel(panel);
    });
  }

  async function handleFile(file, overlay, apiKey) {
    const status = overlay.querySelector('#waste-ocr-status');
    const content = overlay.querySelector('#waste-ocr-content');
    const banner = overlay.querySelector('#waste-ocr-cache-banner');
    status.textContent = `กำลังส่งไป Gemini (${file.name}, ${(file.size/1024).toFixed(0)} KB)…`;
    content.innerHTML = '';
    if (banner) banner.innerHTML = '';

    try {
      const b64 = await fileToBase64(file);
      const mime = file.type || 'image/jpeg';
      const ocrRaw = await geminiCallRetry(apiKey, b64, mime);
      log('OCR raw:', ocrRaw);

      const arr = Array.isArray(ocrRaw) ? ocrRaw : (ocrRaw.rows || []);
      const plan = aggregateRows(arr);

      if (plan.totalRows === 0) {
        status.textContent = '⚠ ไม่พบข้อมูลแถวในรูป — ลองรูปอื่น';
        return;
      }

      // เก็บ cache → ใช้ซ้ำได้หลายวันโดยไม่ต้อง OCR ใหม่
      saveCache(arr, file.name);
      log('cached', plan.dates.length, 'days');

      showDayPicker(overlay, arr, file.name);
    } catch (e) {
      console.error(e);
      status.textContent = '❌ Error: ' + e.message;
    }
  }

  function showDayPicker(overlay, arr, fileName) {
    const status = overlay.querySelector('#waste-ocr-status');
    const content = overlay.querySelector('#waste-ocr-content');
    const meta = arr.find(r => r._meta)?._meta;
    const dates = [...new Set(arr.filter(r => r && !r._meta).map(r => r.date).filter(Boolean))].sort();

    if (dates.length === 0) {
      status.textContent = '⚠ ไม่มีวันที่ใน OCR result';
      return;
    }

    const cache = loadCache() || { filled: {} };
    const filled = cache.filled || {};

    const optionsHtml = dates.map(d => {
      const isFilled = filled[d] ? ' ✓ (กรอกแล้ว)' : '';
      return `<option value="${d}">${thaiDateBE(d)}${isFilled}</option>`;
    }).join('');

    const metaWarn = meta ? `<div style="color:#b54;margin:6px 0">⚠ confidence=${meta.confidence}${meta.unclear?.length ? ', unclear: '+meta.unclear.join(', '):''}</div>` : '';

    status.textContent = `📦 ${fileName} · ${dates.length} วันใน cache — เลือกวันแล้วกด Fill`;
    content.innerHTML = `
      ${metaWarn}
      <div class="waste-ocr-row" style="background:#f5f0ff;padding:10px;border-radius:6px">
        <label style="font-weight:600">เลือกวัน:</label>
        <select id="ocr-day-select" style="padding:6px 10px;font-size:14px;flex:1">
          ${optionsHtml}
        </select>
      </div>
      <div id="ocr-day-preview"></div>
      <div class="waste-ocr-row">
        <label><input type="checkbox" id="ocr-fill-header" checked /> กรอก header (วันที่ / ปี / เวลา / Supplies / ผู้บันทึก)</label>
      </div>
      <div class="waste-ocr-row">
        <button class="waste-ocr-btn waste-ocr-primary" data-act="fill">✓ Fill Form</button>
        <button class="waste-ocr-btn waste-ocr-secondary" data-act="debug">🔍 Debug DOM</button>
        <button class="waste-ocr-btn waste-ocr-secondary" data-act="reupload">⟳ Re-upload</button>
      </div>
      <div id="waste-ocr-log" style="display:none"></div>`;

    const sel = content.querySelector('#ocr-day-select');
    const previewEl = content.querySelector('#ocr-day-preview');

    function renderDay(dateISO) {
      const dayPlan = aggregateRows(arr, dateISO);
      const rowsHtml = dayPlan.rows.map((r, i) =>
        `<tr><td>${r.location}</td><td><input type="number" min="1" max="25" data-row="${i}" value="${r.rowIdx}" style="width:50px" /></td><td><input type="number" step="0.01" data-i="${i}" value="${r.kg}" /></td></tr>`
      ).join('');
      const filledNote = filled[dateISO] ? `<span style="color:#28a745">✓ กรอกแล้วเมื่อ ${cacheAgeText(filled[dateISO])}</span>` : '';
      previewEl.innerHTML = `
        <div style="font-size:13px;color:#555;margin:6px 0">
          วันที่: <b>${thaiDateBE(dateISO)}</b> (CE ${dateISO}) · เวลาแรก: <b>${dayPlan.earliestTime || '-'}</b> · ${dayPlan.totalRows} entry · ${filledNote}
        </div>
        <table id="waste-ocr-preview">
          <thead><tr><th>Location</th><th>Row #</th><th>kg (แก้ได้)</th></tr></thead>
          <tbody>${rowsHtml || '<tr><td colspan="3">— ไม่มี row ที่ match LOCATION_TO_ROW —</td></tr>'}</tbody>
        </table>`;
      return dayPlan;
    }

    let currentDayPlan = renderDay(sel.value);
    sel.addEventListener('change', () => { currentDayPlan = renderDay(sel.value); });

    content.querySelector('[data-act="debug"]').addEventListener('click', () => {
      const logEl = content.querySelector('#waste-ocr-log');
      logEl.style.display = 'block';
      logEl.textContent = debugDumpForm();
    });
    content.querySelector('[data-act="reupload"]').addEventListener('click', () => {
      // เคลียร์ content + ให้ user ลากรูปใหม่
      content.innerHTML = '';
      status.textContent = 'ลากรูปใหม่วางด้านบน';
    });
    content.querySelector('[data-act="fill"]').addEventListener('click', async () => {
      // อ่าน kg + rowIdx ที่ user แก้ใน preview
      content.querySelectorAll('input[data-i]').forEach(inp => {
        const i = +inp.dataset.i;
        currentDayPlan.rows[i].kg = parseFloat(inp.value) || 0;
      });
      const overrides = getRowOverrides();
      let savedOverride = false;
      content.querySelectorAll('input[data-row]').forEach(inp => {
        const i = +inp.dataset.row;
        const newIdx = parseInt(inp.value, 10);
        if (!newIdx) return;
        if (newIdx !== currentDayPlan.rows[i].rowIdx) {
          overrides[currentDayPlan.rows[i].location] = newIdx;
          currentDayPlan.rows[i].rowIdx = newIdx;
          savedOverride = true;
        }
      });
      if (savedOverride) saveRowOverrides(overrides);
      const fillHeader = content.querySelector('#ocr-fill-header').checked;
      const dateISO = sel.value;
      const fillBtn = content.querySelector('[data-act="fill"]');
      fillBtn.disabled = true; fillBtn.textContent = '⏳ กำลังกรอก…';
      const report = await fillForm(currentDayPlan, { fillHeader, dateISO });
      fillBtn.disabled = false; fillBtn.textContent = '✓ Fill Form';
      if (savedOverride) report.unshift('💾 บันทึก row override แล้ว — รอบหน้าใช้ค่าใหม่');
      const logEl = content.querySelector('#waste-ocr-log');
      logEl.style.display = 'block';
      logEl.textContent = report.join('\n');
      markFilled(dateISO);
      // อัปเดต dropdown แสดง ✓
      const opt = sel.querySelector(`option[value="${dateISO}"]`);
      if (opt && !opt.textContent.includes('✓')) opt.textContent = `${thaiDateBE(dateISO)} ✓ (กรอกแล้ว)`;
      // re-render preview เพื่ออัปเดต filled note
      currentDayPlan = renderDay(dateISO);
    });
  }

  function debugDumpForm() {
    const lines = ['=== Form DOM Dump ==='];
    // --- Table rows (label inputs + qty inputs) ---
    const rows = $$('tr').filter(tr => !isInOurOverlay(tr));
    lines.push(`Total <tr> (excl. overlay): ${rows.length}`);
    rows.forEach((tr, i) => {
      const labelInput = tr.querySelector('input.fo13, input[class*="fo13"]')
        || tr.querySelector('input[type="text"], input:not([type])');
      const labelVal = labelInput?.value || '';
      const qty = tr.querySelector('input[name="TRASH_SUB_QTY[]"]') || tr.querySelector('input[name*="QTY"]');
      if (labelVal || qty) {
        lines.push(`tr[${i}] label="${labelVal.slice(0,40)}" qty.name="${qty?.name||'-'}" qty.id="${qty?.id||'-'}"`);
      }
    });
    // --- Header fields (outside <tr>) ---
    lines.push('');
    lines.push('=== Top-level form fields (header) ===');
    const fields = $$('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), select, textarea')
      .filter(el => !isInOurOverlay(el) && el.offsetParent !== null && !el.closest('table'));
    fields.forEach((el, i) => {
      const lab = inferLabel(el);
      lines.push(`field[${i}] <${el.tagName.toLowerCase()}> name="${el.name||''}" id="${el.id||''}" class="${(el.className||'').slice(0,40)}" value="${(el.value||'').slice(0,40)}" label="${lab.slice(0,40)}"`);
    });
    return lines.join('\n');
  }

  function inferLabel(el) {
    if (el.id) {
      const lab = document.querySelector(`label[for="${el.id}"]`);
      if (lab) return normalizeText(lab.textContent);
    }
    let cur = el;
    for (let d = 0; d < 5 && cur; d++) {
      cur = cur.parentElement;
      if (!cur) break;
      const lab = cur.querySelector?.('label, .control-label, dt, th');
      if (lab && !lab.contains(el)) return normalizeText(lab.textContent);
    }
    // try previous sibling text
    let sib = el.previousElementSibling;
    while (sib) {
      const t = normalizeText(sib.textContent);
      if (t) return t;
      sib = sib.previousElementSibling;
    }
    return '';
  }

  // --- BOOT ------------------------------------------------------------------
  injectStyle();
  // form อาจ render หลัง load — ลอง inject ซ้ำได้
  const tryInject = () => { try { injectButton(); } catch (e) { warn(e); } };
  tryInject();
  new MutationObserver(tryInject).observe(document.body, { childList: true, subtree: false });
  log('userscript loaded');
})();
