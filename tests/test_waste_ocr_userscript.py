import re
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
USERSCRIPT = REPO_ROOT / "scripts" / "userscripts" / "waste-form-ocr-fill.user.js"


def run_userscript_unit(tmp_path: Path, js_expr: str) -> str:
    source = USERSCRIPT.read_text(encoding="utf-8")
    source = re.sub(
        r"\n  // --- BOOT[\s\S]*?\n\}\)\(\);\s*$",
        "\n  globalThis.__wasteOcrTest = { aggregateRows, applyRawRowEdit, buildLearningPrompt, buildSystemPrompt, formatTeachingHistoryForDisplay, recordOcrTeachingHistory, getOcrTeachingHistory };\n})();\n",
        source,
    )
    harness = (
        "globalThis.__gmStore = new Map();\n"
        "globalThis.GM_getValue = (key, fallback) => globalThis.__gmStore.has(key) ? globalThis.__gmStore.get(key) : fallback;\n"
        "globalThis.GM_setValue = (key, value) => globalThis.__gmStore.set(key, value);\n"
        "globalThis.console.warn = () => undefined;\n"
        "globalThis.console.error = () => undefined;\n"
        f"{source}\n"
        f"{js_expr}\n"
    )
    harness_path = tmp_path / "waste_ocr_harness.js"
    harness_path.write_text(harness, encoding="utf-8")
    result = subprocess.run(
        ["node", str(harness_path)],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def test_aggregate_rows_keeps_duplicate_department_entries_as_one_daily_total(tmp_path):
    out = run_userscript_unit(
        tmp_path,
        textwrap.dedent(
            """
            const rows = [
              {row_number: 1, date: '2026-05-10', time: '08:00', weight_kg: 16, location: 'ER', recorder: 'A'},
              {row_number: 2, date: '2026-05-10', time: '09:00', weight_kg: 13, location: 'OPD', recorder: 'B'},
              {row_number: 3, date: '2026-05-10', time: '10:00', weight_kg: 12, location: 'Ward', recorder: 'C'},
              {row_number: 4, date: '2026-05-10', time: '11:00', weight_kg: 5, location: 'ER', recorder: 'D'},
            ];
            const plan = globalThis.__wasteOcrTest.aggregateRows(rows, '2026-05-10');
            const er = plan.rows.find(r => r.location === 'ER');
            console.log(JSON.stringify({erKg: er.kg, totalRows: plan.totalRows, rowCount: plan.rows.length}));
            """
        )
    )
    assert out == '{"erKg":21,"totalRows":4,"rowCount":3}'


def test_aggregate_rows_splits_weight_to_one_secondary_department(tmp_path):
    out = run_userscript_unit(
        tmp_path,
        textwrap.dedent(
            """
            const rows = [
              {row_number: 1, date: '2026-05-11', time: '08:00', weight_kg: 10, location: 'OPD', secondary_location: 'ER', recorder: 'A'},
            ];
            const plan = globalThis.__wasteOcrTest.aggregateRows(rows, '2026-05-11');
            const opd = plan.rows.find(r => r.location === 'OPD');
            const er = plan.rows.find(r => r.location === 'ER');
            console.log(JSON.stringify({opdKg: opd.kg, erKg: er.kg, rowCount: plan.rows.length}));
            """
        )
    )
    assert out == '{"opdKg":5,"erKg":5,"rowCount":2}'


def test_apply_raw_row_edit_recomputes_summary_after_department_and_weight_change(tmp_path):
    out = run_userscript_unit(
        tmp_path,
        textwrap.dedent(
            """
            const rows = [
              {row_number: 1, date: '2026-05-11', time: '08:00', weight_kg: 10, location: 'OPD', secondary_location: null, recorder: 'A'},
              {row_number: 2, date: '2026-05-11', time: '09:00', weight_kg: 5, location: 'ER', secondary_location: null, recorder: 'B'},
            ];
            globalThis.__wasteOcrTest.applyRawRowEdit(rows, 0, 'location', 'เวช');
            globalThis.__wasteOcrTest.applyRawRowEdit(rows, 0, 'secondary_location', 'ฝังเข็ม');
            const plan = globalThis.__wasteOcrTest.applyRawRowEdit(rows, 0, 'weight_kg', '20');
            const byLoc = Object.fromEntries(plan.rows.map(r => [r.location, r.kg]));
            console.log(JSON.stringify({
              opd: byLoc.OPD || 0,
              er: byLoc.ER || 0,
              weich: byLoc['เวช'] || 0,
              acupuncture: byLoc['ฝังเข็ม'] || 0,
              rowCount: plan.rows.length
            }));
            """
        )
    )
    assert out == '{"opd":0,"er":5,"weich":10,"acupuncture":10,"rowCount":3}'


def test_weight_expression_plus_is_calculated_and_preserved_for_teaching(tmp_path):
    out = run_userscript_unit(
        tmp_path,
        textwrap.dedent(
            """
            const rows = [{
              row_number: 24,
              date: '2026-05-13',
              time: '15:00',
              weight_kg: 15,
              _originalKg: 15,
              location: 'ER',
              _originalLocation: 'ER',
              recorder: 'A',
              _originalRecorder: 'A',
            }];
            const plan = globalThis.__wasteOcrTest.applyRawRowEdit(rows, 0, 'weight_kg', '5+5');
            const saved = globalThis.__wasteOcrTest.recordOcrTeachingHistory(rows, {
              dateISO: '2026-05-13',
              fileName: 'sample.jpg',
              note: 'row24 ลายมือเขียน 5+5 ไม่ใช่ 15',
            });
            const history = globalThis.__wasteOcrTest.getOcrTeachingHistory();
            const prompt = globalThis.__wasteOcrTest.buildSystemPrompt();
            console.log(JSON.stringify({
              kg: plan.rows[0].kg,
              rawExpr: rows[0].weight_expr,
              saved,
              field: history[0].field,
              corrected: history[0].corrected,
              computed: history[0].computed,
              promptHasExpr: prompt.includes('corrected to "5+5"'),
              promptHasComputed: prompt.includes('computed 10')
            }));
            """
        )
    )
    assert out == '{"kg":10,"rawExpr":"5+5","saved":1,"field":"weight","corrected":"5+5","computed":10,"promptHasExpr":true,"promptHasComputed":true}'


def test_learning_prompt_records_staff_and_time_corrections_from_raw_table(tmp_path):
    out = run_userscript_unit(
        tmp_path,
        textwrap.dedent(
            """
            const rows = [{
              row_number: 1,
              time: '08:00',
              _originalTime: '07:50',
              weight_kg: 16,
              _originalKg: 16,
              location: 'ER',
              _originalLocation: 'ER',
              recorder: 'สมชาย',
              _originalRecorder: 'สมชย',
            }];
            const text = globalThis.__wasteOcrTest.buildLearningPrompt(rows, {}, '2026-05-10', 'sample.jpg', rows);
            console.log(JSON.stringify({
              hasRecorder: text.includes('recorder'),
              hasTime: text.includes('time'),
              correctionCount: /Corrections\\*\\*: 2/.test(text)
            }));
            """
        )
    )
    assert out == '{"hasRecorder":true,"hasTime":true,"correctionCount":true}'


def test_records_structured_ocr_teaching_history_and_feeds_future_gemini_prompt(tmp_path):
    out = run_userscript_unit(
        tmp_path,
        textwrap.dedent(
            """
            const rows = [{
              row_number: 4,
              time: '11:00',
              _originalTime: '10:50',
              weight_kg: 5,
              _originalKg: 15,
              location: 'ER',
              _originalLocation: 'OPD',
              recorder: 'กลอยใจ',
              _originalRecorder: 'กลอยใ',
            }];
            const saved = globalThis.__wasteOcrTest.recordOcrTeachingHistory(rows, {
              dateISO: '2026-05-10',
              fileName: 'sample.jpg',
            });
            const history = globalThis.__wasteOcrTest.getOcrTeachingHistory();
            const prompt = globalThis.__wasteOcrTest.buildSystemPrompt();
            console.log(JSON.stringify({
              saved,
              fields: history.map(h => h.field).sort(),
              promptHasScope: prompt.includes('WASTE OCR TEACHING HISTORY'),
              promptHasWeight: prompt.includes('weight: read "15" but corrected to "5"'),
              promptHasLocation: prompt.includes('location: read "OPD" but corrected to "ER"'),
              promptHasRecorder: prompt.includes('recorder: read "กลอยใ" but corrected to "กลอยใจ"')
            }));
            """
        )
    )
    assert out == '{"saved":4,"fields":["location","recorder","time","weight"],"promptHasScope":true,"promptHasWeight":true,"promptHasLocation":true,"promptHasRecorder":true}'


def test_records_date_correction_and_free_text_note_in_teaching_history(tmp_path):
    out = run_userscript_unit(
        tmp_path,
        textwrap.dedent(
            """
            const rows = [{
              row_number: 2,
              date: '2026-05-10',
              _originalDate: '2025-05-10',
              time: '09:00',
              _originalTime: '09:00',
              weight_kg: 13,
              _originalKg: 13,
              location: 'OPD',
              _originalLocation: 'OPD',
              recorder: 'A',
              _originalRecorder: 'A',
            }];
            const saved = globalThis.__wasteOcrTest.recordOcrTeachingHistory(rows, {
              dateISO: '2026-05-10',
              fileName: 'sample.jpg',
              note: 'ผู้จดเขียนปีผิด ไม่ใช่ความผิดของ AI',
            });
            const history = globalThis.__wasteOcrTest.getOcrTeachingHistory();
            const prompt = globalThis.__wasteOcrTest.buildSystemPrompt();
            console.log(JSON.stringify({
              saved,
              field: history[0].field,
              original: history[0].original,
              corrected: history[0].corrected,
              note: history[0].note,
              promptHasDate: prompt.includes('date: read "2025-05-10" but corrected to "2026-05-10"'),
              promptHasNote: prompt.includes('Note: ผู้จดเขียนปีผิด ไม่ใช่ความผิดของ AI')
            }));
            """
        )
    )
    assert out == '{"saved":1,"field":"date","original":"2025-05-10","corrected":"2026-05-10","note":"ผู้จดเขียนปีผิด ไม่ใช่ความผิดของ AI","promptHasDate":true,"promptHasNote":true}'


def test_system_prompt_teaches_two_digit_year_resolution_for_current_be_and_ce_years(tmp_path):
    out = run_userscript_unit(
        tmp_path,
        textwrap.dedent(
            """
            const prompt = globalThis.__wasteOcrTest.buildSystemPrompt();
            console.log(JSON.stringify({
              hasBE: prompt.includes('69') && prompt.includes('2569'),
              hasCE: prompt.includes('26') && prompt.includes('2026'),
              hasTwoDigitRule: prompt.includes('two-digit year')
            }));
            """
        )
    )
    assert out == '{"hasBE":true,"hasCE":true,"hasTwoDigitRule":true}'


def test_formats_teaching_history_for_settings_view(tmp_path):
    out = run_userscript_unit(
        tmp_path,
        textwrap.dedent(
            """
            const rows = [{
              row_number: 8,
              date: '2026-05-11',
              _originalDate: '2026-05-11',
              time: '14:25',
              _originalTime: '14:25',
              weight_kg: 3,
              _originalKg: 8,
              location: 'โรงครัว',
              _originalLocation: 'ER',
              recorder: 'N/A',
              _originalRecorder: 'N/A',
            }];
            globalThis.__wasteOcrTest.recordOcrTeachingHistory(rows, {
              dateISO: '2026-05-11',
              fileName: 'sample.jpg',
              note: 'ลายมือแผนกอ่านผิดจาก ER เป็นโรงครัว',
            });
            const html = globalThis.__wasteOcrTest.formatTeachingHistoryForDisplay();
            console.log(JSON.stringify({
              hasTable: html.includes('<table'),
              hasLocation: html.includes('location'),
              hasWeight: html.includes('weight'),
              hasCorrection: html.includes('ER') && html.includes('โรงครัว'),
              hasNote: html.includes('ลายมือแผนกอ่านผิดจาก ER เป็นโรงครัว')
            }));
            """
        )
    )
    assert out == '{"hasTable":true,"hasLocation":true,"hasWeight":true,"hasCorrection":true,"hasNote":true}'
