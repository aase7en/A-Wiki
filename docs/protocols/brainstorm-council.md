# Brainstorm Council Protocol

> Module: `scripts/lib/council_room.py` (offline-orchestration only — no synthesis model call)
> CLI: `scripts/swarm/council.py` (thin wrapper — `ask` / `synthesize` / `show` / `list`)
> Wired: on-demand tool, driven by the moderator — **no SessionStart hook**
> Tests: `pytest tests/test_council_room.py -v`

## ปัญหาที่แก้

เวลาต้องการ brainstorm หรือตัดสินใจที่มีหลายมุมมอง การถามโมเดล primary (top-tier, แพง) รอบเดียวมักได้คำตอบเดียว — ไม่มีความหลากหลายให้เทียบ ในขณะที่ยิงคำถามเดียวกันไปหลายโมเดล **ฟรี/ถูก** พร้อมกันแล้วเอามาเทียบ ก็ได้มุมมองที่กว้างกว่าในต้นทุนที่ต่ำกว่ามาก — ตรงกับ Cost-First Decision Pyramid (`CLAUDE.md`) ที่บอกให้เริ่มจาก level ต่ำสุดเสมอ

Brainstorm Council แก้ปัญหานี้แบบแบ่งงานชัดเจน:

- **ส่วนถูก (this module)**: fan คำถามเดียวออกไป K โมเดลฟรี/ถูกพร้อมกัน ผ่าน `scripts/swarm/delegate.sh` ตัวเดิมที่มีอยู่แล้ว (ไม่แก้ delegate.sh เลย) เก็บคำตอบเป็น transcript JSON แล้ว emit dashboard event
- **ส่วนแพง (moderator = primary agent ที่กำลังคุยอยู่ตอนนี้)**: อ่าน transcript แล้วสังเคราะห์ (synthesize) เอง — โมดูลนี้**ไม่เคย**เรียกโมเดล paid เพื่อสรุปให้ synthesis text ถูกเขียนกลับมาโดย moderator ผ่าน `add_synthesis()` / `council.py synthesize` เท่านั้น

## สถาปัตยกรรม

```
primary agent (moderator, in-session)
        │  1. ask a question
        ▼
scripts/swarm/council.py ask "question"
        │  2. convene() — cost-first, parallel
        ▼
scripts/lib/council_room.py
        │  3. fan-out (ThreadPoolExecutor, one thread per engine)
        ├──► delegate.sh (env: only GEMINI enabled)   → answer / fail
        ├──► delegate.sh (env: only OPENROUTER enabled) → answer / fail
        └──► delegate.sh (env: only GROQ enabled)      → answer / fail
        │  4. write .tmp/council/<id>.json  +  emit council_start/council_answer
        ▼
primary agent reads transcript, synthesizes
        │  5. council.py synthesize <id> --text "..."
        ▼
scripts/lib/council_room.py::add_synthesis()  → rewrites transcript + emit council_synthesis
```

## วิธีทำงาน

1. **`plan_participants(n, env)`** — เลือก engine cost-first จาก `FREE_FIRST_ORDER = (GEMINI, OPENROUTER, GROQ, ZHIPU, DEEPSEEK, ANTHROPIC)` (ฟรี → subscription → pay-as-you-go) ข้าม engine ที่ `AWIKI_DISABLE_<ID>=1` หรือไม่มี API key ที่ต้องใช้ (`ENGINE_KEY_ENV`) คืนสูงสุด `n` ตัว — น้อยกว่าหรือว่างเปล่าได้ ไม่ raise
2. **`force_engine_env(engine, base_env)`** — บังคับ engine เดียวให้ `delegate.sh` เลือก **โดยไม่แก้ delegate.sh เลยแม้แต่บรรทัดเดียว**: ตั้ง `AWIKI_DISABLE_<ID>=1` ให้ 5 engine ที่ไม่ใช่ engine เป้าหมาย และเอา disable var ของ engine เป้าหมายออก (`_provider_enabled` ใน delegate.sh อ่าน var นี้อยู่แล้ว) — คืน env ใหม่เสมอ ไม่แตะ `base_env` เดิม และปล่อย namespace อื่น (เช่น `AWIKI_DISABLE_DASHBOARD_AUTOSTART`) ผ่านไปโดยไม่แตะต้อง
3. **`convene(question, ...)`** — วางแผน participants แล้วรันพร้อมกันด้วย `ThreadPoolExecutor` (หนึ่ง thread ต่อ engine) แต่ละ participant ล้มได้โดยไม่ทำให้รอบทั้งหมดล้ม (`_run_one` ครอบ exception ไว้) เขียน transcript ลง `.tmp/council/<id>.json` **เสมอ** — แม้ไม่มี participant เลย (`status: "no-participants"`) หรือ participant ทุกตัวล้ม (`status: "all-failed"`) emit `council_start` (question ตัดที่ 120 ตัวอักษร, n) แล้ว `council_answer` ต่อ participant หนึ่งครั้ง
4. **`add_synthesis(council_id, text, ...)`** — moderator เท่านั้นที่เรียก validate `council_id` ด้วย `COUNCIL_ID_RE` ก่อนแตะ filesystem เสมอ (กัน path traversal เช่น `../evil`) โหลด transcript เดิม เขียน `synthesis: {text, author, added_at}` กลับ แล้ว emit `council_synthesis`
5. **`load_council(id)` / `list_councils()`** — อ่านกลับสำหรับ `council.py show` / `council.py list`; `list_councils()` เรียงใหม่สุดก่อน พร้อมสรุป `participants_ok` / `participants_total` / `has_synthesis`

## Engine Model (ใช้ delegate.sh ตัวเดิม 100%)

delegate.sh มี 6 engine คุมด้วย `_provider_enabled <ID>` ที่อ่าน `AWIKI_DISABLE_<ID>`:

| Engine ID | API key env var | delegate.sh wrapper |
|-----------|------------------|----------------------|
| `GEMINI` | `GEMINI_API_KEY` | `try_gemini_direct` |
| `OPENROUTER` | `OPENROUTER_API_KEY` | `try_openrouter_model` |
| `GROQ` | `GROQ_API_KEY` | `try_groq_model` |
| `ZHIPU` | `ZHIPU_API_KEY` | `try_zhipu_direct` |
| `DEEPSEEK` | `DEEPSEEK_API_KEY` | `try_deepseek_direct` |
| `ANTHROPIC` | `ANTHROPIC_API_KEY` | `try_anthropic_haiku` |

Council ไม่เพิ่ม engine ใหม่ ไม่เปลี่ยน routing logic ใน delegate.sh — แค่ควบคุมว่า *engine ไหนถูกเปิดใช้ต่อการเรียกหนึ่งครั้ง* ผ่าน env ที่ delegate.sh อ่านอยู่แล้ว

## CLI

```bash
# 1) ยิงคำถามไป council (default 3 participants, task_type=reason, timeout=90s)
python scripts/swarm/council.py ask "ควรใช้ SQLite FTS5 หรือ sqlite-vec สำหรับ wiki search?"
#   [GEMINI] ok (2.1s)
#   ...
#   transcript: .tmp/council/council-20260712-143000-a1b2.json
#   → moderator: python scripts/swarm/council.py synthesize council-20260712-143000-a1b2 --text "..."

# 2) moderator (primary agent) อ่าน transcript แล้วสังเคราะห์เอง — ไม่มีโมเดล paid ถูกเรียกจากขั้นนี้
python scripts/swarm/council.py synthesize council-20260712-143000-a1b2 --text "สรุป: ..."
# หรือ --file path/to/synthesis.md

# 3) อ่านย้อนหลัง
python scripts/swarm/council.py show council-20260712-143000-a1b2
python scripts/swarm/council.py list
```

`ask` exit code: `0` ถ้ามี participant สำเร็จอย่างน้อย 1, `1` ถ้าไม่มี participant เลย หรือทุกตัวล้ม (ต่างจาก SessionStart module อย่าง `vendor_watch`/`skill_learning` ที่ต้อง degrade เงียบเสมอ — council เป็น on-demand tool ที่ moderator เรียกตรง ๆ ควรรู้ทันทีว่ารอบล้ม)

## Transcript Schema (`.tmp/council/<id>.json`, gitignored)

```json
{
  "id": "council-20260712-143000-a1b2",
  "question": "...",
  "task_type": "reason",
  "created_at": "2026-07-12T14:30:00+00:00",
  "participants": [
    {"engine": "GEMINI", "status": "ok", "answer": "...", "latency_s": 2.1},
    {"engine": "OPENROUTER", "status": "fail", "answer": "timeout after 90s", "latency_s": 90.0}
  ],
  "synthesis": null,
  "status": "ok"
}
```

`id` matches `COUNCIL_ID_RE`: `council-YYYYMMDD-HHMMSS-xxxx` (4 hex chars, `uuid4().hex[:4]`) — ทุกฟังก์ชันที่รับ `council_id` (`add_synthesis`, `load_council`) validate กับ regex นี้ก่อนแตะ filesystem เสมอ

## Fail-Soft Guarantees (ต่าง participant vs. ต่าง round)

| ระดับ | พฤติกรรม |
|-------|----------|
| Participant เดียวล้ม (timeout, key ผิด, network) | `_run_one()` จับ exception ไว้เอง → participant นั้น `status: "fail"`, ตัวอื่นเดินต่อปกติ — **ไม่มีทางล้มทั้งรอบ** |
| ไม่มี participant เลย (ไม่มี key / ปิดหมด) | `convene()` ยังเขียน transcript (`status: "no-participants"`) และคืนค่าปกติ — ไม่ raise |
| Participant ทุกตัวล้ม | transcript เขียนเสร็จ (`status: "all-failed"`) — **CLI exit 1** (ต่างจาก SessionStart modules ที่ต้อง exit เงียบเสมอ) |
| `add_synthesis`/`load_council` ได้ id ผิดรูปแบบหรือ traversal (`../evil`) | raise `ValueError` ก่อนแตะไฟล์ใด ๆ — CLI จับแล้ว exit 1 พร้อมข้อความ |
| `add_synthesis`/`load_council` หา council ไม่เจอ | raise `ValueError` — CLI exit 1 |
| dashboard ไม่ทำงาน (`event_logger.py` ยิงไม่ถึง) | `default_emit()` ครอบ `try/except: pass` ทั้งหมด — ไม่มีทางทำให้ round ล้ม |

## ทดสอบ

```bash
pytest tests/test_council_room.py -v          # plan/force-env/convene/synthesis/load-list/runner/CLI — 28 tests, all offline
pytest tests/test_hooks_subprocess_encoding.py -v   # regression — encoding= lint pattern (hooks dir only; council_room follows the same rule manually)
bash -n scripts/swarm/delegate.sh              # regression — delegate.sh must stay byte-for-byte unchanged

python scripts/swarm/council.py list           # demo อ่านจริงจาก .tmp/council/ (ว่างถ้ายังไม่เคย ask)
```

ทุก test offline 100% — มี fake `runner`/`emit` injected เสมอ ไม่มี test ไหนเรียก `delegate.sh` จริง ไม่มี network call ไม่มีการเขียนไฟล์นอก `tmp_path`

## ข้อจำกัดที่ตั้งใจ (by design)

- **ไม่มี capability ranking** — delegate.sh มี `_run_ranked` (capability-ranked ภายใน cost class เดียวกัน) แต่ council แค่เลือก engine ตาม `FREE_FIRST_ORDER` ตรง ๆ ไม่พยายาม rank ความฉลาดของแต่ละ engine — ถ้าต้องการ ranking ต้องเป็น layer เพิ่มเติมทีหลัง ไม่ใช่ตอนนี้
- **ไม่มี SessionStart hook** — นี่คือ on-demand tool ที่ moderator เรียกเองเมื่อต้องการ ไม่ใช่ passive check ทุก session (ต่างจาก `vendor_watch`/`skill_learning`)
- **synthesis ไม่ auto-generate** — โมดูลนี้ปฏิเสธเรียกโมเดล paid โดยเจตนา ถ้า agent อยากได้ synthesis ต้องอ่าน transcript เองแล้วเขียนกลับผ่าน `add_synthesis()` — ไม่มี mode ไหนให้ auto-synthesize
- **`.tmp/council/` เป็น local scratch, gitignored** — เหมือน `.tmp/` อื่น ๆ ในระบบ (`.tmp/skill-suggestions.json`, `.tmp/vendor-check-cache.json`) ไม่ sync ข้ามเครื่อง ไม่ commit
- **timeout ต่อ participant คงที่ทั้งรอบ** — `convene(timeout=...)` ใช้ค่าเดียวกันกับทุก engine ไม่มี per-engine timeout override ในเวอร์ชันนี้

## ข้อจำกัดที่พบจาก live demo (2026-07-12 — จดไว้ ยังไม่แก้)

- **Key visibility**: `plan_participants()` เห็นเฉพาะ key ใน process env — key ที่อยู่แค่ใน drive `.secrets` (delegate.sh โหลดเองผ่าน `load-drive-keys.sh`) ทำให้ engine นั้น "ล่องหน" จาก council ทั้งที่ delegate ใช้ได้จริง (demo: GEMINI มี key ใน drive แต่ไม่ถูกเลือก) — workaround: export key เข้า env ก่อน หรือใช้ engine ที่ env มองเห็น; root fix ในอนาคต = ถาม `drive_secrets.py --check` แบบ on-demand
- **task_type ↔ engine roster**: การ force engine เดียวทำให้ candidate models เหลือเฉพาะของ engine นั้นใน tier ของ task_type — engine ที่ไม่มี model ใน tier นั้นจะ fail ทั้งที่ engine ปกติดี (demo: GROQ + `reason` (tier-2) → "All 0 model(s) failed" แต่ GROQ + `summarize` (tier-1) ตอบปกติ) — เลือก `--task-type` ให้เข้ากับ participants หรือปล่อย fail-soft แล้วให้ moderator ตัดสิน
