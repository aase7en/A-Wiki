# AG2 Goal Orchestrator — A-Wiki Protocol

> **Status**: Active [verified 2026-06-14]
> **Requires**: Python ≥3.10 in `.venv-ag2` + `requirements-ag2.txt`
> **Entry points**: `bash scripts/swarm/goal.sh` | `python3 scripts/swarm/ag2-goal.py`

---

## ภาพรวม

AG2 (ag2ai/ag2, formerly AutoGen) เป็น **Goal Orchestrator** ของ A-Wiki — ใช้เมื่อต้องการสั่งงานด้วย goal ระดับสูง แทนการสั่ง subtask ทีละอัน

```
User → goal.sh "<goal>"
         │
         ▼
    [Planner] o3/xhigh ──── wiki_search() ──▶ FTS5 (free)
         │                                      └▶ wiki_get_page()
         │  chunks into subtasks
         ▼
    [delegate.sh] ──────────▶ Gemini-flash:free  (search/lookup)
                  ──────────▶ DeepSeek:free       (reason/compare)
                  ──────────▶ Qwen3-235b:free     (summarize)
                  ──────────▶ Groq/Llama:free     (scan/fast)
         │
         ▼  evidence gathered
    [Planner validates] ──▶ FINAL_ANSWER
```

---

## Cost-First Position

| Who | Model | Cost |
|-----|-------|------|
| Planner | o3 (xhigh) — Codex platform | Paid, used only for planning + validation |
| Executor | Gemini/DeepSeek/Qwen via delegate.sh | Free tier first |
| Local tools | FTS5, sqlite-vec, file reads | Zero cost |

**Rule**: Planner calls `wiki_search()` first. ถ้าคำตอบอยู่ใน wiki แล้ว ไม่ต้องเรียก external model เลย.

---

## Quick Start

```bash
# ดู plan ก่อนโดยไม่เสียเงิน (dry-run, local wiki only)
bash scripts/swarm/goal.sh "Summarize all IoT sensors in A-Wiki" --dry-run

# รัน full AG2 loop (ต้องมี .venv-ag2 + OPENAI_API_KEY)
bash scripts/swarm/goal.sh "Find all pharmacy entries missing SP data" --json

# Mode แบบ plan เท่านั้น
python3 scripts/swarm/ag2-goal.py --goal "<goal>" --mode plan --json
```

---

## Setup

```bash
# 1. สร้าง venv สำหรับ AG2 (ต้องการ Python ≥3.10)
python3.10 -m venv .venv-ag2
source .venv-ag2/bin/activate
pip install -r requirements-ag2.txt

# 2. ตรวจสอบ keys (Planner ต้องการ OPENAI_API_KEY, Executors ต้องการ free-model keys)
python3 scripts/lib/drive_secrets.py --check

# 3. ทดสอบ dry-run
bash scripts/swarm/goal.sh "test goal" --dry-run
```

---

## AG2 ต่างจาก delegate.sh อย่างไร?

| | `delegate.sh` | `ag2-goal.py` |
|---|---|---|
| Input | `task_type + prompt` (one task) | `goal` (multi-step, self-planning) |
| Planning | ไม่มี — caller plans | Planner agent วางแผนเอง |
| Execution | คำสั่งเดียว | หลาย subtask, parallel |
| Loops | ไม่มี | มี (re-plan ถ้าหลักฐานไม่พอ) |
| Cost | Free-first (delegate tier) | Planner paid + Executors free |

ใช้ `delegate.sh` เมื่อรู้ชัดว่าจะทำอะไร. ใช้ `ag2-goal.py` เมื่อต้องการให้ AI วางแผนเอง.

---

## Tools ที่ Planner/Executor ใช้ได้

| Tool | Cost | Purpose |
|------|------|---------|
| `wiki_search(query)` | Free | FTS5 search in A-Wiki |
| `wiki_get_page(path)` | Free | Read specific wiki page |
| `wiki_graph_neighbors(node)` | Free | Knowledge graph neighbors |
| `delegate_task(type, prompt)` | Free-first | Route to cheap model |
| `cost_declare(tier, task, reason)` | Free | Write cost-tier declaration |

---

## Integration กับ Codex

ใน `.codex/config.toml` (persistent_instructions) มีการอ้าง AG2 goal flow แล้ว:
- Codex Planner = o3 + xhigh reasoning
- Executors = delegate.sh → free models
- Validation = Planner reviews evidence ก่อน commit

---

## Backward Compatibility

`scripts/crew-dispatch.py` แปลง old crew-dispatch format ไปเป็น `delegate.sh` calls:

```bash
# Old format (crew name)
python3 scripts/crew-dispatch.py --task "search:query" --crew nami

# New format (task_type prefix)
python3 scripts/crew-dispatch.py --task "search:query"

# Both route to: bash scripts/swarm/delegate.sh search "query"
```

Crew alias map: `nami→search`, `robin→reason`, `luffy→scan`, `franky→race`, `zoro→compare`
