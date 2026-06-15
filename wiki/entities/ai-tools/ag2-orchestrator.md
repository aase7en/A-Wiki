---
type: entity
category: tool
tags: [ai-orchestration, swarm, ag2, autogen, multi-agent, cost-first, a-wiki]
sources: []
created: 2026-06-15
updated: 2026-06-15
last_verified: 2026-06-15
verify_tool: training
---

# AG2 Goal Orchestrator

**ประเภท**: Multi-Agent Goal Orchestrator
**สถานะ**: integrated (`scripts/swarm/ag2-goal.py`, `scripts/swarm/goal.sh`)
**License**: Apache-2.0 (ag2ai/ag2, formerly Microsoft AutoGen)

## ภาพรวม

AG2 เป็น **Goal Orchestrator** ของ A-Wiki — รับ goal ระดับสูง แล้วแบ่งเป็น subtask ให้ free model หลายตัวทำงานพร้อมกัน โดย Planner (o3/xhigh) วางแผนและตรวจสอบผล Executors (Gemini/DeepSeek/Qwen via `delegate.sh`) ทำงาน ต่างจาก `delegate.sh` ที่รับ task เดียว AG2 รับ goal ที่ไม่รู้จำนวน subtask ล่วงหน้า

```
User → goal.sh "<goal>"
         │
         ▼
    [Planner] o3/xhigh ──── wiki_search() ──▶ FTS5 (free)
         │  chunks into subtasks               └▶ wiki_get_page()
         ▼
    [delegate.sh] ──▶ Gemini-flash:free  (search/lookup)
                  ──▶ DeepSeek:free       (reason/compare)
                  ──▶ Qwen3-235b:free     (summarize)
                  ──▶ Groq/Llama:free     (scan/fast)
         │  evidence gathered
         ▼
    [Planner validates] ──▶ FINAL_ANSWER
```

## คุณสมบัติหลัก

- **Planner→Executor→Validator loop** — Planner re-plans ถ้า evidence ยังไม่พอ
- **wiki_search() ก่อนเสมอ** — ถ้าคำตอบอยู่ใน A-Wiki แล้ว ไม่เรียก external model
- **Cost-first** — Executors ใช้ free tier ทั้งหมด; Planner เป็นเพียงตัวเดียวที่ paid
- **Parallel subtasks** — delegate.sh รับงานหลาย task พร้อมกัน
- **`--dry-run` mode** — ดู plan โดยไม่เสียเงิน (local wiki only)
- **JSON output** — `--json` flag สำหรับ pipe ต่อ

## Cost-First Position

| Role | Model | Cost |
|------|-------|------|
| Planner | o3 (xhigh) via Codex | Paid — planning + validation เท่านั้น |
| Executor | Gemini/DeepSeek/Qwen/Llama via delegate.sh | Free tier first |
| Local tools | FTS5, sqlite-vec, file reads | ฟรีเสมอ |

## การใช้งาน

```bash
# dry-run (ไม่เสียเงิน)
bash scripts/swarm/goal.sh "Summarize all IoT sensors in A-Wiki" --dry-run

# full loop (ต้องมี .venv-ag2 + OPENAI_API_KEY)
bash scripts/swarm/goal.sh "Find pharmacy entries missing SP data" --json

# plan mode เท่านั้น
python3 scripts/swarm/ag2-goal.py --goal "<goal>" --mode plan --json
```

## ต่างจาก delegate.sh อย่างไร

| | `delegate.sh` | `ag2-goal.py` |
|---|---|---|
| Input | `task_type + prompt` (1 task) | `goal` (multi-step, self-planning) |
| Planning | ไม่มี — caller plans | Planner agent วางแผนเอง |
| Execution | คำสั่งเดียว | หลาย subtask, parallel |
| Re-planning | ไม่มี | มี (ถ้า evidence ไม่พอ) |
| Cost | Free-first | Planner paid + Executors free |

**Rule**: ใช้ `delegate.sh` เมื่อรู้ชัดว่าต้องทำอะไร ใช้ `ag2-goal.py` เมื่อต้องการให้ AI วางแผนเอง

## Setup

```bash
python3.10 -m venv .venv-ag2
source .venv-ag2/bin/activate
pip install -r requirements-ag2.txt

python3 scripts/lib/drive_secrets.py --check
bash scripts/swarm/goal.sh "test goal" --dry-run
```

## Tools ที่ Planner/Executor ใช้ได้

| Tool | Cost | Purpose |
|------|------|---------|
| `wiki_search(query)` | Free | FTS5 search in A-Wiki |
| `wiki_get_page(path)` | Free | อ่านหน้า wiki |
| `wiki_graph_neighbors(node)` | Free | Knowledge graph neighbors |
| `delegate_task(type, prompt)` | Free-first | Route to cheap model |
| `cost_declare(tier, task, reason)` | Free | บันทึก cost-tier declaration |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/ai-tools/ecc]] — swarm skill ecosystem
- ต่อยอดจาก: `scripts/swarm/delegate.sh` — underlying free-model router
- Protocol doc: `docs/protocols/ag2-orchestrator.md`
- Skill: `skills/delegation/ag2-goal/SKILL.md` — usage guide
- Integration: `.codex/config.toml` — Codex planner = o3 + AG2 flow

## แหล่งข้อมูล

- [verified 2026-06-14] ag2ai/ag2 (formerly microsoft/autogen) — Apache-2.0
- `docs/protocols/ag2-orchestrator.md` — A-Wiki protocol + setup guide
- `skills/delegation/ag2-goal/SKILL.md` — usage guide
