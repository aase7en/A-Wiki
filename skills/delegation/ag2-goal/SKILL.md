---
name: ag2-goal
description: Orchestrate multi-step goals using AG2 agents — Planner decomposes, free Executors execute, Planner validates.
version: "1.0"
requires: [python>=3.10, .venv-ag2, requirements-ag2.txt]
cost_tier: L4 (Planner) + L1 (Executors via free models)
---

# Skill: AG2 Goal Orchestrator

> ใช้เมื่อต้องการ accomplish goal ที่ซับซ้อน แบบ self-planning — แทนการสั่ง subtask ทีละอัน

## เมื่อไหร่ใช้

✅ Goal ที่ไม่รู้ล่วงหน้าว่า subtask จะมีกี่อัน เช่น:
- "Audit all wiki entries that reference AI tools and check for staleness"
- "Find all pharmacy records missing price data and generate a summary"
- "Synthesize what A-Wiki knows about IoT sensors vs what's been updated recently"

✅ งานที่ต้องการ evidence gathering ก่อน planning (wiki search → plan → execute)
✅ Multi-round loop: Planner decides done / needs more evidence

❌ ข้าม: งาน 1 subtask → ใช้ `delegate.sh` โดยตรง
❌ ข้าม: งานที่ต้องการ human approval ทุก step

---

## ขั้นตอน

### 1. Dry-run ก่อนเสมอ

```bash
bash scripts/swarm/goal.sh "<goal>" --dry-run
```

ดูว่า Planner จะแตก subtasks อะไรบ้าง และ wiki มีข้อมูลที่เกี่ยวข้องไหม

### 2. Full run (ถ้า dry-run สมเหตุสมผล)

```bash
# ต้องมี OPENAI_API_KEY (Planner) + free-model keys (Executors)
bash scripts/swarm/goal.sh "<goal>"

# หรือ JSON output สำหรับ pipeline
bash scripts/swarm/goal.sh "<goal>" --json
```

### 3. ใช้ Python API โดยตรง

```python
import subprocess, json

result = subprocess.run(
    ["python3", "scripts/swarm/ag2-goal.py",
     "--goal", "your goal here", "--json"],
    capture_output=True, text=True
)
data = json.loads(result.stdout)
print(data["final_answer"])
```

---

## Cost Control

| Step | Cost |
|------|------|
| wiki_search() | Free — FTS5 local |
| delegate_task() | Free — OpenRouter/Gemini/Groq free tier |
| Planner (o3) | Paid — 1 call per subtask chunk + 1 final validation |

**ลด cost**: ถ้า wiki_search พบคำตอบ → Planner ไม่ต้อง delegate เลย (L1 → L4 only for synthesis)

---

## Tools Available

```python
wiki_search(query, limit=5)           # FTS5 search
wiki_get_page(path)                   # read wiki page
wiki_graph_neighbors(node, limit=10)  # knowledge graph
delegate_task(task_type, prompt)      # free model via delegate.sh
cost_declare(tier, task, reason)      # write cost declaration
```

---

## ดูเพิ่มเติม

- `docs/protocols/ag2-orchestrator.md` — full protocol
- `scripts/swarm/ag2-goal.py` — implementation
- `scripts/swarm/ag2_tools.py` — tool wrappers
- `scripts/swarm/delegate.sh` — cost-tiered model router
