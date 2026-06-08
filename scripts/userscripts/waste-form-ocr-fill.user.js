// ==UserScript==
// @name         Waste Form OCR & Fill (gtwoffice trash_add)
// @namespace    a-wiki
// @version      1.1.2
// @description  ถ่ายรูปใบรายงานขยะ → OCR ด้วย Gemini Flash → กรอกฟอร์ม + บันทึกอัตโนมัติ + เปิดฟอร์มถัดไป
// @author       A-Wiki contributors
// @match        https://10779.gtwoffice.com/env/manage/trash_add*
// @match        https://*.gtwoffice.com/env/manage/trash_add*
// @match        https://10779.gtwoffice.com/env/manage/trash
// @match        https://*.gtwoffice.com/env/manage/trash
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
    บ่อบำบัด: 5,   // ขยะทั่วไปบ่อบำบัด [verified 2026-06-08 gtwoffice row 5]
  };

  // Compound locations → split equally across rows
  const COMPOUND_LOCATIONS = {
    'OPD+ER': ['OPD', 'ER'],
    'แผนไทย+ฝังเข็ม': ['แผนไทย', 'ฝังเข็ม'],
  };

  // Post-OCR weight range hints (ใช้ตรวจสอบหลัง Gemini ตอบ — ไม่ block fill แค่แสดง ⚠)
  const WEIGHT_RANGE_HINTS = {
    OPD:       { min: 5,  max: 40,  label: 'OPD ปกติ 10–39' },
    Ward:      { min: 2,  max: 22,  label: 'Ward ปกติ 3–20' },
    ER:        { min: 1,  max: 20,  label: 'ER ปกติ' },
    โรงครัว:  { min: 10, max: 80,  label: 'โรงครัว' },
    บ่อบำบัด: { min: 0.5,max: 20,  label: 'บ่อบำบัด' },
  };

  function getWeightWarning(location, kg) {
    if (kg == null || kg === '') return null;
    const num = typeof kg === 'number' ? kg : Number(kg);
    if (!Number.isFinite(num)) return null;
    const hint = WEIGHT_RANGE_HINTS[location];
    if (!hint) return null;
    if (num > hint.max) return `⚠ ${num} ดูสูงเกิน (${hint.label})`;
    if (num < hint.min) return `⚠ ${num} ดูต่ำเกิน (${hint.label})`;
    return null;
  }

  // --- USER SETTINGS (persisted) --------------------------------------------
  function getSettings() {
    return GM_getValue('ocr_settings', { suppliesValue: '', recorderValue: '', customHints: '', autoHints: [] });
  }
  function saveSettings(s) { GM_setValue('ocr_settings', s); }
  const OCR_TEACHING_HISTORY_KEY = 'ocr_teaching_history';
  const OCR_TEACHING_HISTORY_MAX = 120;
  const OCR_TEACHING_PROMPT_MAX = 15;

  function getOcrTeachingHistory() {
    const history = GM_getValue(OCR_TEACHING_HISTORY_KEY, []);
    return Array.isArray(history) ? history : [];
  }

  function saveOcrTeachingHistory(history) {
    GM_setValue(OCR_TEACHING_HISTORY_KEY, history.slice(0, OCR_TEACHING_HISTORY_MAX));
  }

  function clearOcrTeachingHistory() {
    GM_setValue(OCR_TEACHING_HISTORY_KEY, []);
  }

  function escHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function makeTeachingEntry(field, original, corrected, row, context, extra = {}) {
    return {
      ts: new Date().toISOString(),
      date: context.dateISO || row.date || null,
      file: context.fileName || null,
      row_number: row.row_number || null,
      location: row.location || row._originalLocation || null,
      field,
      original: original == null || original === '' ? '-' : String(original),
      corrected: corrected == null || corrected === '' ? '-' : String(corrected),
      note: (context.note || '').trim() || null,
      ...extra,
    };
  }

  function correctionEntriesFromRows(rawRows, context = {}) {
    const entries = [];
    rawRows.forEach(r => {
      const originalDate = Object.prototype.hasOwnProperty.call(r, '_originalDate') ? r._originalDate : r.date;
      const originalLocation = Object.prototype.hasOwnProperty.call(r, '_originalLocation') ? r._originalLocation : r.location;
      const originalSecondary = Object.prototype.hasOwnProperty.call(r, '_originalSecondaryLocation') ? r._originalSecondaryLocation : (r.secondary_location || '');
      const originalTime = Object.prototype.hasOwnProperty.call(r, '_originalTime') ? r._originalTime : r.time;
      const originalRecorder = Object.prototype.hasOwnProperty.call(r, '_originalRecorder') ? r._originalRecorder : r.recorder;
      const originalWeightExpr = Object.prototype.hasOwnProperty.call(r, '_originalWeightExpr') ? r._originalWeightExpr : (r.weight_expr || '');
      const correctedWeight = r.weight_expr || r.weight_kg;

      if ((r.date || '') !== (originalDate || '')) {
        entries.push(makeTeachingEntry('date', originalDate, r.date, r, context));
      }
      if (r.location !== originalLocation) {
        entries.push(makeTeachingEntry('location', originalLocation, r.location, r, context));
      }
      if ((r.secondary_location || '') !== (originalSecondary || '')) {
        entries.push(makeTeachingEntry('secondary_location', originalSecondary, r.secondary_location, r, context));
      }
      if (r._originalKg != null && (Math.abs((r.weight_kg || 0) - (r._originalKg || 0)) > 0.001 || (r.weight_expr || '') !== (originalWeightExpr || ''))) {
        entries.push(makeTeachingEntry('weight', r._originalKg, correctedWeight, r, context, r.weight_expr ? { computed: r.weight_kg } : {}));
      }
      if ((r.time || '') !== (originalTime || '')) {
        entries.push(makeTeachingEntry('time', originalTime, r.time, r, context));
      }
      if ((r.recorder || '') !== (originalRecorder || '')) {
        entries.push(makeTeachingEntry('recorder', originalRecorder, r.recorder, r, context));
      }
    });
    return entries;
  }

  function recordOcrTeachingHistory(rawRows, context = {}) {
    const entries = correctionEntriesFromRows(rawRows, context);
    if (!entries.length) return 0;
    const history = [...entries, ...getOcrTeachingHistory()];
    saveOcrTeachingHistory(history);
    return entries.length;
  }

  function formatTeachingHistoryForPrompt() {
    const history = getOcrTeachingHistory().slice(0, OCR_TEACHING_PROMPT_MAX);
    if (!history.length) return '';
    return history.map(h => {
      const bits = [
        h.date ? `date ${h.date}` : null,
        h.row_number ? `raw row ${h.row_number}` : null,
        h.location ? `location ${h.location}` : null,
      ].filter(Boolean).join(', ');
      const computed = h.computed != null ? ` (computed ${h.computed})` : '';
      return `- ${h.field}: read "${h.original}" but corrected to "${h.corrected}"${computed}${bits ? ` (${bits})` : ''}.${h.note ? ` Note: ${h.note}` : ''}`;
    }).join('\n');
  }

  function buildConsolidatedRules() {
    const history = getOcrTeachingHistory();
    const counter = {};
    for (const h of history) {
      const key = `${h.field}|${h.original}→${h.corrected}`;
      if (!counter[key]) counter[key] = { count: 0, sample: h };
      counter[key].count++;
    }
    const confirmed = [], suspected = [];
    for (const { count, sample } of Object.values(counter)) {
      const loc = sample.location ? ` (especially at ${sample.location})` : '';
      const line = `- ${sample.field}: when written "${sample.original}" always read as "${sample.corrected}"${loc}`;
      if (count >= 3) confirmed.push(line);
      else if (count >= 2) suspected.push(line);
    }
    return { confirmed, suspected };
  }

  function exportTeachingHistoryAsWikiMarkdown() {
    const { confirmed, suspected } = buildConsolidatedRules();
    const history = getOcrTeachingHistory();
    const today = new Date().toISOString().slice(0, 10);

    const confirmedMd = confirmed.length
      ? confirmed.map(l => `| ${today} | (consolidated ≥3×) | ${l} |`).join('\n')
      : '_(ยังไม่มี confirmed rules — ต้องการ correction เดิมซ้ำ ≥ 3 ครั้ง)_';

    const rawRows = history.slice(0, 50).map(h => {
      const loc = h.location || '-';
      const ctx = [h.date || '', `row ${h.row_number || '?'}`, loc, h.file || ''].filter(Boolean).join(', ');
      return `| ${(h.ts || '').slice(0, 10)} | ${h.field} | ${h.original} | ${h.corrected} | ${ctx} |`;
    }).join('\n');

    return `## Corrections Log (exported ${today} — paste into wiki/context/ocr-learning-log.md)

### Confirmed Rules (≥ 3 corrections same pattern)

${confirmedMd}

### Suspected Rules (2 corrections same pattern)

${suspected.length ? suspected.map(l => l).join('\n') : '_(ยังไม่มี)_'}

### Raw Corrections (top 50 most recent)

| วันที่ | Field | OCR อ่านว่า | ค่าจริง | บริบท |
|---|---|---|---|---|
${rawRows || '_(ไม่มี history)_'}
`;
  }

  function formatTeachingHistoryForDisplay(limit = 30) {
    const history = getOcrTeachingHistory().slice(0, limit);
    if (!history.length) {
      return '<div style="font-size:12px;color:#666;padding:8px;background:#fafafa;border:1px solid #eee;border-radius:6px">ยังไม่มี OCR teaching history — เมื่อแก้ข้อมูลในตาราง 1 แล้วกด Fill ระบบจะบันทึกบทเรียนไว้ตรงนี้</div>';
    }
    const rows = history.map(h => `<tr>
      <td style="padding:4px 6px;border:1px solid #ddd;white-space:nowrap">${escHtml((h.ts || '').slice(0, 10))}</td>
      <td style="padding:4px 6px;border:1px solid #ddd">${escHtml(h.field)}</td>
      <td style="padding:4px 6px;border:1px solid #ddd">${escHtml(h.original)}</td>
      <td style="padding:4px 6px;border:1px solid #ddd">${escHtml(h.corrected)}${h.computed != null ? ` <span style="color:#666">(= ${escHtml(h.computed)})</span>` : ''}</td>
      <td style="padding:4px 6px;border:1px solid #ddd">${escHtml(h.location || '-')}</td>
      <td style="padding:4px 6px;border:1px solid #ddd">${escHtml(h.note || '')}</td>
    </tr>`).join('');
    return `<div style="font-size:12px;color:#444;margin:6px 0">ล่าสุด ${history.length} จากทั้งหมด ${getOcrTeachingHistory().length} รายการ</div>
      <div style="max-height:220px;overflow:auto;border:1px solid #ddd;border-radius:6px">
        <table style="width:100%;border-collapse:collapse;font-size:12px">
          <thead style="position:sticky;top:0;background:#f7f7f9">
            <tr>
              <th style="padding:4px 6px;border:1px solid #ddd;text-align:left">Date</th>
              <th style="padding:4px 6px;border:1px solid #ddd;text-align:left">Field</th>
              <th style="padding:4px 6px;border:1px solid #ddd;text-align:left">AI read</th>
              <th style="padding:4px 6px;border:1px solid #ddd;text-align:left">Corrected</th>
              <th style="padding:4px 6px;border:1px solid #ddd;text-align:left">Location</th>
              <th style="padding:4px 6px;border:1px solid #ddd;text-align:left">Note</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  function buildTwoDigitYearHint() {
    const currentCE = new Date().getFullYear();
    const currentBE = currentCE + 543;
    const ce2 = String(currentCE).slice(-2);
    const be2 = String(currentBE).slice(-2);
    return `DATE YEAR RULE: Resolve ambiguous two-digit year using the current year context. Current CE year is ${currentCE}; current Thai Buddhist Era year is ${currentBE}. If handwritten year is "${be2}", interpret it as BE ${currentBE} and convert output date to CE ${currentCE}. If handwritten year is "${ce2}", consider that the recorder may be using CE ${currentCE}.`;
  }

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
  date         "YYYY-MM-DD" (convert Thai Buddhist Era: subtract 543; if cell is '"', '-', 'น', 'ง', or dash, copy from row above)
  time         string as written, e.g. "15:00" or "07:35น."  (null if blank)
  weight_kg    number; if cell is "5+5" return the SUM (10). Double check digits 2↔9, 6↔5, 1↔4, 8↔9, 4↔3, 2↔1 in tens place. OPD weight is usually 10-39, rarely 40+. null if blank.
  weight_expr  optional string; if the handwritten weight is an addition expression like "5+5", keep that expression here while weight_kg is the computed numeric sum.
  location     normalize to one of: OPD | Ward | ER | OPD+ER | โรงครัว | เวช | ฝังเข็ม | แผนไทย+ฝังเข็ม | แผนไทย | บ่อบำบัด
  secondary_location optional; null unless one handwritten row clearly combines exactly two departments under one weight. Use one of: OPD | Ward | ER | โรงครัว | เวช | ฝังเข็ม | แผนไทย
  recorder     staff name(s) as written (multiple joined with "+"), null if blank

Known confusions to avoid:
  วอร์ด ≠ จอดรถ      (it's Ward) Note: if recorder is อ้อย but weight <=10 in the evening, it might be Ward, cross-check!
  เวช  ≠ ลาว        (it's เวชกรรม)
  แผนไทย+ฝังเข็ม ≠ แผนไทย+ฝ่ายแม่

Staff hints (use as confirmation only):
  OPD afternoon → อ้อย+อ้อย (Recorder อ้อย is usually OPD) ;  Ward → ปลา+เพ็ญ or เพ็ญ+ปลา
  แผนไทย+ฝังเข็ม → หนึ่ง+เพ็ญ ;  ER → กลอยใจ or ณฐอร (เพ็ญ covers night 19:30+)
  โรงครัว → ก

Add a final object {"_meta": {"confidence": 0..1, "unclear": [...]}} if quality is low.
Return ONLY the JSON array.`;

  function buildSystemPrompt() {
    const s = getSettings();
    const hints = (s.customHints || '').trim();
    const { confirmed, suspected } = buildConsolidatedRules();

    let prompt = SYSTEM_PROMPT;

    // Confirmed rules (≥3 occurrences) — high-priority, placed right after base prompt
    if (confirmed.length > 0) {
      prompt += `\n\nCONFIRMED CORRECTION RULES (learned from ≥3 repeated human corrections — treat as hard rules):\n${confirmed.join('\n')}`;
    }

    prompt += `\n\n${buildTwoDigitYearHint()}`;

    if (hints) {
      prompt += `\n\nADDITIONAL USER CORRECTIONS (apply these — they override defaults):\n${hints}`;
    }
    if (s.autoHints && s.autoHints.length > 0) {
      prompt += `\n\nAUTO-LEARNED PAST CORRECTIONS (Avoid repeating these mistakes):\n` + s.autoHints.map(h => `- ${h}`).join('\n');
    }

    // Suspected rules (2 occurrences)
    if (suspected.length > 0) {
      prompt += `\n\nSUSPECTED PATTERNS (seen twice — apply with caution):\n${suspected.join('\n')}`;
    }

    const teachingHistory = formatTeachingHistoryForPrompt();
    if (teachingHistory) {
      prompt += `\n\nWASTE OCR TEACHING HISTORY (domain-specific corrections from past human edits; apply these patterns when reading future Thai hospital waste weight forms):\n${teachingHistory}`;
    }
    return prompt;
  }

  // --- UTIL ------------------------------------------------------------------
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function log(...args) { console.log('[waste-ocr]', ...args); }
  function warn(...args) { console.warn('[waste-ocr]', ...args); }

  function parseWeightInput(value) {
    if (value == null || value === '') return { value: null, expr: null };
    if (typeof value === 'number') return Number.isFinite(value) ? { value, expr: null } : { value: null, expr: null };

    const text = String(value).trim();
    if (!text) return { value: null, expr: null };

    const normalized = text.replace(/\s+/g, '');
    if (normalized.includes('+')) {
      const parts = normalized.split('+');
      if (parts.length > 1 && parts.every(p => /^\d+(?:\.\d+)?$/.test(p))) {
        const sum = parts.reduce((total, p) => total + Number(p), 0);
        return { value: Math.round(sum * 100) / 100, expr: normalized };
      }
      return { value: null, expr: normalized };
    }

    const numberValue = Number(normalized);
    return Number.isFinite(numberValue) ? { value: numberValue, expr: null } : { value: null, expr: null };
  }

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

  function clickSaveButton() {
    const btn = Array.from(document.querySelectorAll('button, input[type="submit"]'))
      .find(el => !el.closest('#waste-ocr-overlay') &&
                  (el.textContent?.includes('บันทึก') || el.value?.includes('บันทึก')));
    if (btn) { btn.click(); return true; }
    return false;
  }
  function cacheAgeText(ts) {
    const min = Math.floor((Date.now() - ts) / 60000);
    if (min < 1) return 'เมื่อสักครู่';
    if (min < 60) return `${min} นาทีก่อน`;
    const hr = Math.floor(min / 60);
    return `${hr} ชม.${min % 60 ? ' '+(min%60)+' นาที' : ''}ก่อน`;
  }

  // --- LEARNING PROMPT (สำหรับส่งให้ A-Wiki AI Agent) -----------------------
  // เปรียบเทียบค่า OCR-original กับค่าที่ user แก้ → สร้าง prompt markdown
  // user copy แล้ว paste เข้า Claude Code → agent อัปเดต wiki/context/ocr-learning-log.md
  function buildLearningPrompt(rawRows, meta, dateISO, fileName, originalOcrRaw) {
    const nowIso = new Date().toISOString().slice(0, 16).replace('T', ' ');
    const diffs = [];

    const rowsTable = rawRows.map((r, i) => {
      const locChanged = r.location !== r._originalLocation;
      const secondaryLocChanged = (r.secondary_location || '') !== (r._originalSecondaryLocation || '');
      const dateChanged = (r.date || '') !== (r._originalDate || '');
      const originalWeightExpr = Object.prototype.hasOwnProperty.call(r, '_originalWeightExpr') ? r._originalWeightExpr : (r.weight_expr || '');
      const kgDisplay = r.weight_expr ? `${r.weight_expr} (= ${r.weight_kg || 0})` : (r.weight_kg || 0);
      const kgChanged = Math.abs((r.weight_kg || 0) - (r._originalKg || 0)) > 0.001 || (r.weight_expr || '') !== (originalWeightExpr || '');
      const timeChanged = (r.time || '') !== (r._originalTime || '');
      const recorderChanged = (r.recorder || '') !== (r._originalRecorder || '');
      const change = [
        dateChanged ? `date: ${r._originalDate || '-'}→${r.date || '-'}` : null,
        locChanged ? `location: ${r._originalLocation}→${r.location}` : null,
        secondaryLocChanged ? `secondary_location: ${r._originalSecondaryLocation || '-'}→${r.secondary_location || '-'}` : null,
        kgChanged ? `kg: ${r._originalKg}→${kgDisplay}` : null,
        timeChanged ? `time: ${r._originalTime || '-'}→${r.time || '-'}` : null,
        recorderChanged ? `recorder: ${r._originalRecorder || '-'}→${r.recorder || '-'}` : null,
      ].filter(Boolean).join('; ') || '—';
      if (dateChanged || locChanged || secondaryLocChanged || kgChanged || timeChanged || recorderChanged) {
        diffs.push({ i, r, dateChanged, locChanged, secondaryLocChanged, kgChanged, timeChanged, recorderChanged });
      }
      return `| ${r.row_number || i + 1} | ${r.time || '-'} | ${r.location} | ${r.secondary_location || '-'} | ${r.recorder || '-'} | ${kgDisplay} | ${r._originalLocation} | ${r._originalSecondaryLocation || '-'} | ${r._originalRecorder || '-'} | ${r._originalKg || 0} | ${change} |`;
    }).join('\n');

    const logEntries = diffs.flatMap(d => {
      const lines = [];
      if (d.dateChanged) lines.push(`| ${dateISO} | date | ${d.r._originalDate || '-'} | ${d.r.date || '-'} | raw row ${d.r.row_number || '?'} = ${d.r.location} (${fileName}) |`);
      if (d.locChanged) lines.push(`| ${dateISO} | location | ${d.r._originalLocation} | ${d.r.location} | raw row ${d.r.row_number || '?'} (${fileName}) |`);
      if (d.secondaryLocChanged) lines.push(`| ${dateISO} | secondary_location | ${d.r._originalSecondaryLocation || '-'} | ${d.r.secondary_location || '-'} | raw row ${d.r.row_number || '?'} = ${d.r.location} (${fileName}) |`);
      if (d.kgChanged) lines.push(`| ${dateISO} | weight | ${d.r._originalKg} | ${d.r.weight_expr ? `${d.r.weight_expr} (= ${d.r.weight_kg || 0})` : d.r.weight_kg} | raw row ${d.r.row_number || '?'} = ${d.r.location} (${fileName}) |`);
      if (d.timeChanged) lines.push(`| ${dateISO} | time | ${d.r._originalTime || '-'} | ${d.r.time || '-'} | raw row ${d.r.row_number || '?'} = ${d.r.location} (${fileName}) |`);
      if (d.recorderChanged) lines.push(`| ${dateISO} | recorder | ${d.r._originalRecorder || '-'} | ${d.r.recorder || '-'} | raw row ${d.r.row_number || '?'} = ${d.r.location} (${fileName}) |`);
      return lines;
    }).join('\n') || '_(ไม่มี correction — OCR ถูกต้องทั้งใบ)_';
    const correctionCount = diffs.reduce((total, d) =>
      total + [d.dateChanged, d.locChanged, d.secondaryLocChanged, d.kgChanged, d.timeChanged, d.recorderChanged].filter(Boolean).length, 0);

    const confLine = meta && meta.confidence != null ? `**OCR confidence**: ${meta.confidence}\n` : '';
    const unclearLine = meta && meta.unclear && meta.unclear.length ? `**OCR unclear notes**: ${meta.unclear.join('; ')}\n` : '';

    return `# Waste OCR Correction Feedback — ${nowIso}

**Image**: ${fileName || '(unknown)'}
**Target date**: ${dateISO}
${confLine}${unclearLine}**Corrections**: ${correctionCount}

## Per-row comparison (user-final vs OCR)

| Row | Time | Location (final) | Secondary Location | Recorder (final) | kg (final) | OCR Location | OCR Secondary | OCR Recorder | OCR kg | Change |
|---|---|---|---|---|---|---|---|---|---|---|
${rowsTable}

## Action requested

อัปเดต \`wiki/context/ocr-learning-log.md\` → Corrections Log โดยเพิ่มแถว:

${logEntries}

ถ้าผิดซ้ำๆ → พิจารณาอัปเดต SYSTEM_PROMPT vocabulary ใน \`scripts/userscripts/waste-form-ocr-fill.user.js\`
(หรือเพิ่ม Custom OCR hints ผ่านปุ่ม ⚙ Settings ของ userscript)

## Raw OCR (debug)

\`\`\`json
${JSON.stringify(originalOcrRaw, null, 2)}
\`\`\`
`;
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
      if ((r.weight_kg == null && !r.weight_expr) || r.location == null) continue;
      const w = parseWeightInput(r.weight_expr || r.weight_kg).value || 0;
      const locs = [...(COMPOUND_LOCATIONS[r.location] || [r.location])];
      if (r.secondary_location && !locs.includes(r.secondary_location)) locs.push(r.secondary_location);
      const split = w / locs.length;
      for (const sub of locs) byLocation[sub] = (byLocation[sub] || 0) + split;
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

  function applyRawRowEdit(rawRows, rowIndex, field, value) {
    const row = rawRows[rowIndex];
    if (!row) return aggregateRows(rawRows, null);
    if (field === 'weight_kg') {
      const parsed = parseWeightInput(value);
      row.weight_kg = parsed.value;
      if (parsed.expr) row.weight_expr = parsed.expr;
      else delete row.weight_expr;
    } else if (field === 'secondary_location') {
      row.secondary_location = value || null;
    } else {
      row[field] = value;
    }
    return aggregateRows(rawRows, null);
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
  #waste-ocr-preview select { padding: 3px 6px; }
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

    // Delayed check (ค่า value อยู่ในรูปแบบ CE — display เป็น BE)
    await sleep(100);
    log(`  [after 100ms] el.value=${el.value}`);
    await sleep(900);
    log(`  [after 1000ms] el.value=${el.value}`);

    // ตรวจ display element ที่แสดง BE (text node ใน Vue-rendered display)
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

    const valueOK = el.value === valueCE || el.value.includes(valueCE.split('/').slice(0,2).join('/'));
    log(`  value check: el.value="${el.value}" matches CE? ${valueOK}`);
    log(`  display check: BE "${valueBE}" appears in text nodes? ${displayOK}`);

    if (valueOK) {
      log('=== datepicker done, success: true (CE format) ===');
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

        <div style="margin:10px 0;padding:10px;background:#fff;border:1px solid #ddd;border-radius:8px">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:6px">
            <div style="font-weight:600;font-size:13px">OCR teaching history (ดูว่า AI ถูกสอนอะไรไปแล้ว)</div>
            <div style="display:flex;gap:4px">
              <button class="waste-ocr-btn waste-ocr-secondary" data-act="export-wiki" style="padding:3px 8px;font-size:11px">📤 Export to Wiki</button>
              <button class="waste-ocr-btn waste-ocr-danger" data-act="clear-teaching-history" style="padding:3px 8px;font-size:11px">ล้าง history</button>
            </div>
          </div>
          <div id="ocr-export-area" style="display:none;margin-bottom:8px">
            <div style="font-size:11px;color:#555;margin-bottom:4px">Copy → paste ต่อท้าย <code>wiki/context/ocr-learning-log.md</code> → git commit:</div>
            <textarea id="ocr-export-text" rows="10" readonly style="width:100%;box-sizing:border-box;font-family:monospace;font-size:11px;padding:6px;border:1px solid #ccc;border-radius:4px;background:#f9f9f9"></textarea>
          </div>
          <div id="ocr-teaching-history-view">${formatTeachingHistoryForDisplay()}</div>
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
        autoHints: settings.autoHints || [],
      });
      const msg = panel.querySelector('#set-saved-msg');
      msg.style.display = 'inline';
      setTimeout(() => { msg.style.display = 'none'; }, 2000);
    });
    panel.querySelector('[data-act="clear-overrides"]')?.addEventListener('click', () => {
      saveRowOverrides({});
      renderSettingsPanel(panel);
    });
    panel.querySelector('[data-act="clear-teaching-history"]')?.addEventListener('click', () => {
      if (!confirm('ล้าง OCR teaching history ทั้งหมด? Gemini จะไม่ได้ใช้บทเรียนเก่าเหล่านี้ใน prompt รอบถัดไป')) return;
      clearOcrTeachingHistory();
      renderSettingsPanel(panel);
    });
    panel.querySelector('[data-act="export-wiki"]')?.addEventListener('click', () => {
      const exportArea = panel.querySelector('#ocr-export-area');
      const exportText = panel.querySelector('#ocr-export-text');
      const md = exportTeachingHistoryAsWikiMarkdown();
      exportText.value = md;
      exportArea.style.display = exportArea.style.display === 'none' ? 'block' : 'none';
      if (exportArea.style.display === 'block') exportText.select();
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
    const locationKeys = Object.keys(LOCATION_TO_ROW);

    const filledCount = dates.filter(d => filled[d]).length;
    const optionsHtml = dates.map(d => {
      const isFilled = filled[d];
      return `<option value="${d}" ${isFilled ? 'style="color:#888"' : ''}>${isFilled ? '✅' : '⬜'} ${thaiDateBE(d)}${isFilled ? ' (กรอกแล้ว)' : ''}</option>`;
    }).join('');

    const metaWarn = meta ? `<div style="color:#b54;margin:6px 0">⚠ confidence=${meta.confidence}${meta.unclear?.length ? ', unclear: '+meta.unclear.join(', '):''}</div>` : '';

    status.textContent = `📦 ${fileName} · ${dates.length} วัน (กรอกแล้ว ${filledCount}/${dates.length}) — เลือกวันแล้วกด Fill`;
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
        <label><input type="checkbox" id="ocr-auto-continue" checked /> บันทึกอัตโนมัติ &amp; เปิดฟอร์มถัดไป</label>
      </div>
      <div class="waste-ocr-row">
        <button class="waste-ocr-btn waste-ocr-primary" data-act="fill">✓ Fill Form</button>
        <button class="waste-ocr-btn waste-ocr-secondary" data-act="debug">🔍 Debug DOM</button>
        <button class="waste-ocr-btn waste-ocr-secondary" data-act="reupload">⟳ Re-upload</button>
      </div>
      <div id="waste-ocr-log" style="display:none"></div>
      <div id="waste-ocr-learning" style="display:none;margin-top:12px;border-top:1px solid #ddd;padding-top:10px"></div>`;

    const sel = content.querySelector('#ocr-day-select');
    const previewEl = content.querySelector('#ocr-day-preview');
    const learnDiv = content.querySelector('#waste-ocr-learning');

    // --- NEW: Two-table UI (v0.9.2) ---
    // Table 1: Raw OCR rows (editable per-line)
    // Table 2: Aggregated summary (auto-calculated, read-only except Row#)
    function renderDay(dateISO) {
      // Get raw OCR rows for this date (before aggregation)
      const rawRows = arr.filter(r => r && r.row_number != null && !r._meta && r.date === dateISO);
      // Deep-clone so user edits don't mutate the original arr
      const clonedRawRows = JSON.parse(JSON.stringify(rawRows));

      // Snapshot OCR-original values for learning
      clonedRawRows.forEach(r => {
        r._originalDate = r.date;
        r._originalLocation = r.location;
        r._originalSecondaryLocation = r.secondary_location || '';
        r._originalKg = r.weight_kg;
        r._originalWeightExpr = r.weight_expr || '';
        r._originalTime = r.time;
        r._originalRecorder = r.recorder;
      });
      let correctedDateISO = dateISO;

      function syncRawRowsFromDom() {
        const dateEl = previewEl.querySelector('#ocr-record-date');
        const parsedDate = parseAnyDate(dateEl?.value || correctedDateISO);
        if (parsedDate) {
          correctedDateISO = parsedDate;
          clonedRawRows.forEach(r => { r.date = correctedDateISO; });
        }
        clonedRawRows.forEach((_, i) => {
          const kgEl = previewEl.querySelector(`.ocr-raw-kg[data-i="${i}"]`);
          const locEl = previewEl.querySelector(`.ocr-raw-loc[data-i="${i}"]`);
          const secEl = previewEl.querySelector(`.ocr-raw-secondary-loc[data-i="${i}"]`);
          const timeEl = previewEl.querySelector(`.ocr-raw-time[data-i="${i}"]`);
          const recEl = previewEl.querySelector(`.ocr-raw-rec[data-i="${i}"]`);
          if (kgEl) applyRawRowEdit(clonedRawRows, i, 'weight_kg', kgEl.value);
          if (locEl) applyRawRowEdit(clonedRawRows, i, 'location', locEl.value);
          if (secEl) applyRawRowEdit(clonedRawRows, i, 'secondary_location', secEl.value);
          if (timeEl) applyRawRowEdit(clonedRawRows, i, 'time', timeEl.value);
          if (recEl) applyRawRowEdit(clonedRawRows, i, 'recorder', recEl.value);
        });
      }

      // --- Aggregated table updater ---
      function rebuildAggTable() {
        // Re-aggregate from the current visible raw table values.
        syncRawRowsFromDom();
        const plan = aggregateRows(clonedRawRows, null);
        const aggTbody = content.querySelector('#waste-ocr-agg-tbody');
        if (!aggTbody) return plan;
        const aggHtml = plan.rows.map(r => `<tr style="border-bottom:1px solid #d4edda">
          <td style="padding:5px 8px">${r.location}</td>
          <td style="padding:5px 4px"><input type="number" min="1" max="25" class="ocr-agg-row" data-loc="${r.location}" value="${r.rowIdx}" style="width:50px;padding:2px;border:1px solid #ccc;border-radius:3px" /></td>
          <td style="padding:5px 8px;font-weight:bold;color:#28a745">${r.kg.toFixed(2)}</td>
        </tr>`).join('');
        aggTbody.innerHTML = aggHtml || '<tr><td colspan="3" style="text-align:center;color:#999">— ไม่มี row ที่ match —</td></tr>';

        // Bind Row# override in agg table
        content.querySelectorAll('.ocr-agg-row').forEach(inp => {
          inp.addEventListener('change', (e) => {
            const loc = e.target.dataset.loc;
            const overrides = getRowOverrides();
            overrides[loc] = parseInt(e.target.value, 10);
            saveRowOverrides(overrides);
          });
        });
        return plan;
      }

      const filledNote = filled[dateISO] ? `<span style="color:#28a745">✓ กรอกแล้วเมื่อ ${cacheAgeText(filled[dateISO])}</span>` : '';

      // --- Build Raw Table HTML ---
      const rawHtml = clonedRawRows.map((r, i) => {
        const opts = locationKeys.map(k =>
          `<option value="${k}"${k === r.location ? ' selected' : ''}>${k}</option>`
        ).join('');
        const secondaryOpts = [''].concat(locationKeys).map(k =>
          `<option value="${k}"${k === (r.secondary_location || '') ? ' selected' : ''}>${k || '-'}</option>`
        ).join('');
        const warn = getWeightWarning(r.location, r.weight_kg);
        const warnHtml = warn ? `<div class="ocr-weight-warn" data-i="${i}" style="font-size:10px;color:#c0392b;margin-top:1px">${escHtml(warn)}</div>` : `<div class="ocr-weight-warn" data-i="${i}" style="font-size:10px;color:#c0392b;margin-top:1px"></div>`;
        return `<tr style="border-bottom:1px solid #e8ddf5">
          <td style="text-align:center;padding:4px;color:#6f42c1;font-weight:600">${r.row_number || i + 1}</td>
          <td style="padding:4px"><input type="text" class="ocr-raw-time" data-i="${i}" value="${r.time || ''}" style="width:52px;padding:2px 4px;border:1px solid #ccc;border-radius:3px;font-size:12px" /></td>
          <td style="padding:4px">
            <input type="text" inputmode="decimal" class="ocr-raw-kg" data-i="${i}" value="${r.weight_expr || (r.weight_kg != null ? r.weight_kg : '')}" style="width:52px;padding:2px 4px;border:1px solid #ccc;border-radius:3px;font-size:12px" />
            ${warnHtml}
          </td>
          <td style="padding:4px"><select class="ocr-raw-loc" data-i="${i}" style="width:92px;padding:2px;border:1px solid #ccc;border-radius:3px;font-size:12px">${opts}</select></td>
          <td style="padding:4px"><select class="ocr-raw-secondary-loc" data-i="${i}" style="width:92px;padding:2px;border:1px solid #ccc;border-radius:3px;font-size:12px">${secondaryOpts}</select></td>
          <td style="padding:4px"><input type="text" class="ocr-raw-rec" data-i="${i}" value="${r.recorder || ''}" style="width:65px;padding:2px 4px;border:1px solid #ccc;border-radius:3px;font-size:12px" /></td>
        </tr>`;
      }).join('');

      previewEl.innerHTML = `
        <div style="font-size:13px;color:#555;margin:6px 0">
          วันที่: <b>${thaiDateBE(dateISO)}</b> (CE ${dateISO}) · ${clonedRawRows.length} entry · ${filledNote}
        </div>
        <div class="waste-ocr-row" style="background:#fff8e1;padding:8px;border:1px solid #f1d27a;border-radius:6px;align-items:flex-start">
          <label style="font-weight:600;min-width:90px;margin-top:5px">วันที่บันทึก:</label>
          <input type="date" id="ocr-record-date" value="${dateISO}" style="padding:5px 8px;border:1px solid #ccc;border-radius:4px" />
          <div style="font-size:11px;color:#7a5a00;line-height:1.35">แก้วันที่ตรงนี้ถ้า OCR/ผู้จดเขียนวันที่ผิด ระบบจะใช้วันที่นี้กรอก header และบันทึกเป็น OCR teaching history</div>
        </div>
        <div style="margin:6px 0 10px">
          <label style="font-weight:600;font-size:13px;display:block;margin-bottom:3px">หมายเหตุสอน AI / บริบทข้อผิดพลาด:</label>
          <textarea id="ocr-teaching-note" rows="2" placeholder="เช่น ผู้จดเขียนปีผิด ไม่ใช่ความผิดของ AI, เลข 69 หมายถึง พ.ศ.2569, ลายมือทำให้ 5 ดูเหมือน 15" style="width:100%;box-sizing:border-box;padding:6px 8px;border:1px solid #ccc;border-radius:5px;font-size:12px"></textarea>
        </div>

        <div style="font-weight:600;margin-top:8px;font-size:14px;color:#6f42c1">📝 1. ข้อมูลที่ AI อ่านได้ (แก้ไขได้ทีละบรรทัด)</div>
        <div style="max-height:220px;overflow-y:auto;margin:4px 0 10px;border:1px solid #d0c0ee;border-radius:6px">
          <table id="waste-ocr-raw-table" style="width:100%;border-collapse:collapse;font-size:13px">
            <thead style="position:sticky;top:0;background:#f5f0ff;box-shadow:0 1px 0 #ccc;z-index:1">
              <tr>
                <th style="padding:5px 4px;width:35px">Row</th>
                <th style="padding:5px 4px;width:60px">เวลา</th>
                <th style="padding:5px 4px;width:55px">kg</th>
                <th style="padding:5px 4px;width:95px">แผนก</th>
                <th style="padding:5px 4px;width:95px">แผนกเสริม</th>
                <th style="padding:5px 4px;width:70px">ผู้จด</th>
              </tr>
            </thead>
            <tbody>${rawHtml || '<tr><td colspan="5" style="text-align:center;color:#999;padding:12px">— ไม่มีข้อมูล —</td></tr>'}</tbody>
          </table>
        </div>
        <div style="font-size:11px;color:#888;margin-top:-6px;margin-bottom:8px">แก้ค่าด้านบน → ตารางสรุปด้านล่างจะอัปเดตอัตโนมัติทันที</div>

        <div style="font-weight:600;margin-top:10px;font-size:14px;color:#28a745">📊 2. สรุปรวม แผนก/วัน (พร้อมกรอก)</div>
        <table id="waste-ocr-agg-table" style="width:100%;border-collapse:collapse;font-size:13px;margin:4px 0;border:1px solid #b6dab6;border-radius:6px;overflow:hidden">
          <thead style="background:#e7f5e7">
            <tr>
              <th style="text-align:left;padding:5px 8px">Location</th>
              <th style="text-align:left;padding:5px 4px;width:65px">Form Row #</th>
              <th style="text-align:left;padding:5px 8px;width:80px">Total kg</th>
            </tr>
          </thead>
          <tbody id="waste-ocr-agg-tbody"></tbody>
        </table>
        <div style="font-size:11px;color:#888;margin-top:-2px">ข้อมูลนี้จะถูกใช้กรอกลงฟอร์มเมื่อกด Fill · แก้ Form Row # ได้เพื่อ override</div>
      `;

      // Reset learning prompt เมื่อเปลี่ยนวัน
      learnDiv.style.display = 'none';
      learnDiv.innerHTML = '';

      const dateInput = previewEl.querySelector('#ocr-record-date');
      dateInput.addEventListener('input', (e) => {
        const parsed = parseAnyDate(e.target.value);
        if (!parsed) return;
        correctedDateISO = parsed;
        clonedRawRows.forEach(r => { r.date = correctedDateISO; });
        rebuildAggTable();
      });

      const rawTableEl = previewEl.querySelector('#waste-ocr-raw-table');
      const rawEditSelector = '.ocr-raw-kg, .ocr-raw-loc, .ocr-raw-secondary-loc, .ocr-raw-time, .ocr-raw-rec';
      ['input', 'change', 'blur'].forEach(type => {
        rawTableEl.addEventListener(type, (e) => {
          if (e.target?.matches?.(rawEditSelector)) rebuildAggTable();
        });
      });

      function refreshWeightWarning(i) {
        const r = clonedRawRows[i];
        const warnEl = previewEl.querySelector(`.ocr-weight-warn[data-i="${i}"]`);
        if (!warnEl) return;
        const w = getWeightWarning(r.location, r.weight_kg);
        warnEl.textContent = w || '';
      }

      // --- Bind raw table edits → auto-update agg table ---
      previewEl.querySelectorAll('.ocr-raw-kg').forEach(inp => {
        inp.addEventListener('input', (e) => {
          const i = +e.target.dataset.i;
          applyRawRowEdit(clonedRawRows, i, 'weight_kg', e.target.value);
          refreshWeightWarning(i);
          rebuildAggTable();
        });
      });
      previewEl.querySelectorAll('.ocr-raw-loc').forEach(sel => {
        sel.addEventListener('change', (e) => {
          const i = +e.target.dataset.i;
          clonedRawRows[i].location = e.target.value;
          refreshWeightWarning(i);
          rebuildAggTable();
        });
      });
      previewEl.querySelectorAll('.ocr-raw-secondary-loc').forEach(sel => {
        sel.addEventListener('change', (e) => {
          const i = +e.target.dataset.i;
          clonedRawRows[i].secondary_location = e.target.value || null;
          rebuildAggTable();
        });
      });
      previewEl.querySelectorAll('.ocr-raw-time').forEach(inp => {
        inp.addEventListener('input', (e) => {
          clonedRawRows[+e.target.dataset.i].time = e.target.value;
        });
      });
      previewEl.querySelectorAll('.ocr-raw-rec').forEach(inp => {
        inp.addEventListener('input', (e) => {
          clonedRawRows[+e.target.dataset.i].recorder = e.target.value;
        });
      });

      // Initial render of agg table
      rebuildAggTable();

      // Return accessors (instead of raw dayPlan) so fill handler can read latest state
      return {
        getRawRows: () => { syncRawRowsFromDom(); return clonedRawRows; },
        getDayPlan: () => { syncRawRowsFromDom(); return aggregateRows(clonedRawRows, null); },
        getDateISO: () => correctedDateISO,
        getTeachingNote: () => (previewEl.querySelector('#ocr-teaching-note')?.value || '').trim(),
      };
    }

    let currentDayResult = renderDay(sel.value);
    sel.addEventListener('change', () => { currentDayResult = renderDay(sel.value); });

    content.querySelector('[data-act="debug"]').addEventListener('click', () => {
      const logEl = content.querySelector('#waste-ocr-log');
      logEl.style.display = 'block';
      logEl.textContent = debugDumpForm();
    });
    content.querySelector('[data-act="reupload"]').addEventListener('click', () => {
      content.innerHTML = '';
      status.textContent = 'ลากรูปใหม่วางด้านบน';
    });
    content.querySelector('[data-act="fill"]').addEventListener('click', async () => {
      // Read current state from the two-table UI
      const rawRows = currentDayResult.getRawRows();
      const dayPlan = currentDayResult.getDayPlan();
      const correctedDateISO = currentDayResult.getDateISO() || sel.value;
      const teachingNote = currentDayResult.getTeachingNote();

      // Save any Row# overrides from agg table
      const overrides = getRowOverrides();
      let savedOverride = false;
      content.querySelectorAll('.ocr-agg-row').forEach(inp => {
        const loc = inp.dataset.loc;
        const newIdx = parseInt(inp.value, 10);
        if (!newIdx) return;
        const existingIdx = resolveRowIdx(loc);
        if (newIdx !== existingIdx) {
          overrides[loc] = newIdx;
          savedOverride = true;
        }
      });
      if (savedOverride) saveRowOverrides(overrides);
      // Re-resolve row indices after saving overrides
      if (savedOverride) {
        dayPlan.rows.forEach(r => {
          r.rowIdx = resolveRowIdx(r.location);
        });
      }

      const fillHeader = content.querySelector('#ocr-fill-header').checked;
      const dateISO = correctedDateISO;
      const savedTeachingCount = recordOcrTeachingHistory(rawRows, { dateISO, fileName, note: teachingNote });
      const fillBtn = content.querySelector('[data-act="fill"]');
      fillBtn.disabled = true; fillBtn.textContent = '⏳ กำลังกรอก…';
      const report = await fillForm(dayPlan, { fillHeader, dateISO });
      fillBtn.disabled = false; fillBtn.textContent = '✓ Fill Form';
      if (savedOverride) report.unshift('💾 บันทึก row override แล้ว — รอบหน้าใช้ค่าใหม่');
      if (savedTeachingCount) report.unshift(`🧠 บันทึก OCR teaching history ${savedTeachingCount} รายการ — Gemini จะใช้เป็นบทเรียนรอบถัดไป`);

      const autoContinue = content.querySelector('#ocr-auto-continue')?.checked;
      if (autoContinue) {
        markFilled(dateISO); // บันทึก filled ก่อน navigate — ให้หน้าถัดไปเห็น ✓
        GM_setValue('ocr_auto_open_add', true);
        report.push('⏳ กำลังบันทึก...');
        const logEl2 = content.querySelector('#waste-ocr-log');
        logEl2.style.display = 'block';
        logEl2.textContent = report.join('\n');
        await sleep(300);
        const saved = clickSaveButton();
        if (!saved) {
          report.push('⚠ ไม่พบปุ่มบันทึก — กรุณากดบันทึกเอง');
          GM_setValue('ocr_auto_open_add', false);
          logEl2.textContent = report.join('\n');
        }
        return;
      }

      const logEl = content.querySelector('#waste-ocr-log');
      logEl.style.display = 'block';
      logEl.textContent = report.join('\n');
      markFilled(dateISO);
      const opt = sel.querySelector(`option[value="${dateISO}"]`) || sel.options[sel.selectedIndex];
      if (opt && !opt.textContent.includes('✓')) opt.textContent = `${thaiDateBE(dateISO)} ✓ (กรอกแล้ว)`;

      // --- LEARNING PROMPT (สำหรับส่งให้ A-Wiki AI Agent) ---
      const learnText = buildLearningPrompt(rawRows, meta, dateISO, fileName, arr);
      learnDiv.innerHTML = `
        <h3 style="margin:0 0 6px;font-size:14px">📚 Learning Prompt — สำหรับส่งให้ A-Wiki AI Agent</h3>
        <div style="font-size:11px;color:#666;margin-bottom:6px">🧠 OCR teaching history ถูกบันทึกอัตโนมัติแล้ว ${savedTeachingCount} รายการ และจะถูกส่งให้ Gemini ในรอบ OCR ถัดไป</div>
        <textarea id="ocr-learning-text" style="width:100%;height:200px;font-family:monospace;font-size:11px;box-sizing:border-box" readonly></textarea>
        <div class="waste-ocr-row">
          <button class="waste-ocr-btn waste-ocr-primary" data-act="copy-learn">📋 Copy</button>
          <button class="waste-ocr-btn waste-ocr-secondary" data-act="download-learn">⬇ Download .md</button>
        </div>`;
      const ta = learnDiv.querySelector('#ocr-learning-text');
      ta.value = learnText;
      learnDiv.style.display = 'block';

      learnDiv.querySelector('[data-act="copy-learn"]').onclick = () => {
        ta.removeAttribute('readonly');
        ta.select();
        try { document.execCommand('copy'); } catch (e) { warn(e); }
        ta.setAttribute('readonly', 'true');
        if (navigator.clipboard) navigator.clipboard.writeText(ta.value).catch(() => {});
      };
      learnDiv.querySelector('[data-act="download-learn"]').onclick = () => {
        const blob = new Blob([learnText], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ocr-correction-${dateISO}-${Date.now()}.md`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      };
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

  // หน้า list (trash) — ตรวจ flag แล้วคลิก เพิ่มข้อมูล อัตโนมัติ
  if (/\/env\/manage\/trash$/.test(location.pathname)) {
    if (GM_getValue('ocr_auto_open_add', false)) {
      GM_setValue('ocr_auto_open_add', false);
      GM_setValue('ocr_auto_open_overlay', true); // สั่งให้ trash_add หน้าถัดไปเปิด overlay อัตโนมัติ
      sleep(700).then(() => {
        const addBtn = Array.from(document.querySelectorAll('a, button'))
          .find(el => el.textContent?.trim().includes('เพิ่มข้อมูล'));
        if (addBtn) { addBtn.click(); log('auto-continue: clicked เพิ่มข้อมูล'); }
        else warn('auto-continue: เพิ่มข้อมูล button not found');
      });
    }
    log('userscript loaded (list page — no overlay)');
  } else {
    // หน้า trash_add — inject overlay ตามปกติ
    injectStyle();
    const tryInject = () => { try { injectButton(); } catch (e) { warn(e); } };
    tryInject();
    new MutationObserver(tryInject).observe(document.body, { childList: true, subtree: false });

    // auto-open overlay ถ้ามาจาก auto-continue flow
    if (GM_getValue('ocr_auto_open_overlay', false)) {
      GM_setValue('ocr_auto_open_overlay', false);
      sleep(400).then(() => {
        const ocrBtn = document.querySelector('#waste-ocr-btn');
        if (ocrBtn) { ocrBtn.click(); log('auto-continue: opened OCR overlay'); }
        else warn('auto-continue: #waste-ocr-btn not found');
      });
    }

    log('userscript loaded');
  }
})();
