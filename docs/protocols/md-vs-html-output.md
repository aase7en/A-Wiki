# Protocol: Output Format — Durability Stratification + Render-Don't-Dump

> เจตนา: ให้ทุก agent (Claude/Codex/Gemini/Cursor) เลือก format ของ output อย่างสม่ำเสมอ
> เพื่อดึง human-in-the-loop กลับมา review จริง โดยไม่เพิ่ม read-token ใน context window
>
> อ้างอิง: Thariq Shihipar (ทีม Claude Code, Anthropic) — "HTML is the new Markdown" (พ.ค. 2026).

## TL;DR

- **Layer 1 (Durable):** เอกสารถาวร → **Markdown** เสมอ (git, diff, อ่านซ้ำ)
- **Layer 2 (Machine↔machine):** ข้อมูลที่ agent re-ingest → **CSV/JSONL/JSON** (กระชับสุด, ห้าม HTML)
- **Layer 3 (Human review):** รายงาน/ตาราง verbose สำหรับคน → compact JSON → `render.py` → leaf HTML ใน `exports/html/` (gitignored, agent ไม่อ่านกลับ)
- **Render, don't dump:** ห้าม paste รายงาน/ตารางยาวลง chat — emit JSON → render → ตอบแค่ path + 1–3 บรรทัดสรุป

---

## The 3-Layer Output Model

| Layer | อายุ / ผู้อ่าน | Format | อยู่ที่ไหน |
|---|---|---|---|
| **1. Durable knowledge** | เดือน–ปี · คน+agent อ่านซ้ำ · ต้อง diff | **Markdown** | CLAUDE.md, AGENTS.md, `wiki/`, ADRs, `docs/` |
| **2. Machine↔machine** | ชั่วคราว · agent re-ingest เองหรือส่งต่อ tool | **CSV/TSV > JSONL > JSON** (ห้าม HTML, ห้าม MD table ยาว) | stdin/stdout, temp `*.json`/`*.csv` |
| **3. Human review leaf** | ชม.–วัน · ครั้งเดียว · คนดูในเบราว์เซอร์ · **agent ไม่อ่านกลับ** | compact JSON → `render.py` → leaf HTML | `exports/html/` (gitignored) |

---

## ทำไม HTML ไม่ประหยัด Token สำหรับ Agent

HTML **กินโทเคนมากที่สุด** เมื่อ agent ต้อง "อ่าน" มัน — เพราะ tag overhead บวม text จริง:

| Format (เนื้อหาเดียวกัน 6 records × 4 fields) | chars | ~tokens (char/4) | เทียบ Markdown |
|---|---|---|---|
| **CSV** | 152 | **~38** | **0.69× ถูกสุด** |
| **Markdown table** | 220 | **~55** | 1.00× baseline |
| **JSONL** | 272 | ~68 | 1.24× |
| **JSON** | 288 | ~72 | 1.31× |
| **HTML table** | 460 | **~115** | **2.09× แพงสุด** |

> Prose: Markdown ~39 tok, HTML ~56 tok (1.44×). วัดด้วย char/4 proxy (ทิศทางเชื่อถือได้; ตัวเลขจริงขึ้นอยู่กับ BPE tokenizer)
>
> ตรวจสอบด้วย: `python3 scripts/format-cost.py --demo`

**ดังนั้น HTML ประหยัด token ได้ "เฉพาะกลไกเดียวเท่านั้น"**: agent ถือแค่ compact JSON, `render.py` ขยาย JSON→HTML ด้วย **0 โทเคน agent**, HTML ถูก gitignore, **agent ไม่เคยอ่านกลับ**. การประหยัดคือ "ผลัก presentation ออกนอก context window" — ไม่ใช่ "HTML กระชับ". HTML ที่ agent ต้องอ่าน = ต้นทุนสูงสุด.

---

## Decision Thresholds (กฏใช้ตัดสินใจ)

### ตาราง / Tabular data

| เงื่อนไข | Format ที่ถูกต้อง | เหตุผล |
|---|---|---|
| ≤5 rows, ไม่มี severity/sort/diff/pick | **Markdown table inline** | เพียงพอ, render เปลืองขั้นตอน |
| Agent ต้อง re-ingest / ส่งต่อ tool | **CSV/TSV** (prefer) หรือ **JSONL** | กระชับที่สุด, Layer 2 |
| ≥12 rows **หรือ** sort/filter/severity/diff/graph/ให้คนเลือก | **render-html** (`audit` / `report` surface) | human review, ห้าม dump ลง chat |

### รายงาน / Reports

| เงื่อนไข | Format |
|---|---|
| รายงาน multi-section ที่คนต้อง review (post-mortem, code-review, health digest) | **render-html เสมอ** |
| บันทึกสั้น / คำสั่ง / decision log ≤5 bullet | **Markdown** |

### Hard Prohibitions

- ห้ามเขียน `.html` ลง `wiki/`, `raw/`, `docs/`, `CLAUDE.md`, `AGENTS.md` — เหล่านี้คือ **source-of-truth ที่ต้อง diff ใน git**
- ห้ามเขียน `.html` นอก `exports/html/` หรือ `skills/render-html/templates/`
- ห้าม commit HTML artifact — `exports/html/` ถูก gitignore ตลอด
- ห้าม paste HTML ทั้งก้อนกลับเข้า chat — ใช้ **Copy-as-JSON** เท่านั้น (paste HTML กลับ = กินโทเคน 2.1× MD)
- ห้าม agent อ่าน `exports/html/*.html` กลับเข้า context window

*บังคับใช้บน file-write โดย `scripts/hooks/check_output_format.py` (PreToolUse). Chat output เป็นวินัย — ไม่มี output-event hook.*

---

## "Render, Don't Dump" Mandate

**รูปแบบที่ถูก:**
```
1. สร้างข้อมูลเป็น JSON     →  data = {"findings": [...]}
2. เขียนลง temp file        →  data.json
3. render                   →  python3 skills/render-html/scripts/render.py report --in data.json
4. ตอบกลับ agent/user       →  "Rendered: exports/html/report-20260605-141023.html (12 findings)"
```

**รูปแบบที่ผิด:**
```
# ❌ ห้าม: dump ตารางยาว/รายงาน verbose ลง chat หรือ wiki
agent ตอบ: "| File | Severity | Line | Issue |\n|---|---| ... (50 rows)"
```

---

## กฏเดิม (คงไว้)

1. **Source-of-truth = Markdown เสมอ.** HTML เป็น layer ทับ data เดิม ไม่ใช่แทนที่. ห้ามเขียน HTML ลง `wiki/`, `raw/`, หรือ `CLAUDE.md`.
2. **เลือก HTML เมื่อ output มีอย่างน้อยหนึ่งอย่าง:** ตารางที่อยากให้ sort/filter, diff ที่ควรไฮไลต์สี, ความรุนแรงหลายระดับ (severity), กราฟ/ความสัมพันธ์, หรือผู้ใช้ต้องเลือก/ปรับค่าแล้วส่งกลับ.
3. **เลือก Markdown เมื่อ** เป็นเอกสารสั้น/คำสั่ง/บันทึก ที่เน้นอ่านเป็นข้อความและต้อง review ใน commit.
4. **HTML ต้อง self-contained + gitignored** — ออกที่ `exports/html/` (ephemeral), zero external dependency.
5. **ใส่ทางกลับเสมอ** — artifact ทุกชิ้นมีปุ่ม Copy-as-JSON เพื่อ round-trip ค่าที่ผู้ใช้เลือกกลับเข้า agent.

---

## วิธีทำ (render-html)

```bash
# render surface ที่มีอยู่ (11 surfaces: scouter, report, health, graph, plan, pharmacy,
#   delivery, audit, skills, agents, status)
python3 skills/render-html/scripts/render.py <surface> --in data.json

# วัด token cost ของแต่ละ format (brain-gate verify command)
python3 scripts/format-cost.py --demo
python3 scripts/format-cost.py --in data.json
```

---

## Verify

```bash
# render-html tests
python3 -m pytest skills/render-html/tests/test_render_html.py -v

# hook tests (ครอบคลุม check_output_format)
python3 -m pytest tests/test_check_output_format.py -v

# format-cost measurement + ordering check
python3 -m pytest tests/test_format_cost.py -v
python3 scripts/format-cost.py --demo

# smoke-test hook blocking (.html → wiki/)
echo '{"tool_name":"Write","tool_input":{"file_path":"wiki/x.html","content":"<x>"}}' \
  | python scripts/hooks_runner.py check-output-format
# คาด: exit 2 + stderr BLOCKED
```

---

## หมายเหตุการบังคับใช้

| กลไก | สิ่งที่คุมได้ | สิ่งที่คุมไม่ได้ |
|---|---|---|
| `check_output_format.py` (PreToolUse hook) | การเขียนไฟล์ (Edit/Write/MultiEdit) | chat reply ของ agent |
| `check_output_format.py` advisory (c) | ตักเตือนเมื่อ .md มีตารางใหญ่+keyword | ไม่บล็อก (false-positive กัน) |
| AGENTS.md rule #7 + brand files | กฏสำหรับทุก AI brand | ขึ้นกับ agent เชื่อฟัง |
| `render-html` skill | ให้เครื่องมือ render ชัดเจน | ไม่บังคับ agent ใช้ |

ไม่มี output-event hook ใน Claude Code หรือ Codex ณ ปัจจุบัน — chat output format เป็น **วินัย** ที่อาศัย rule #7 + protocol นี้.
