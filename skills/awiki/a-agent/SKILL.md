---
name: a-agent
description: "สร้าง/วิเคราะห์/debug AI agent — bind agent-harness-construction, mcp-builder, mcp-server-patterns, eval-harness, continuous-agent-loop, prompt-optimizer, token-optimization, delegate-subagent. Dispatcher ล้วน ไม่มีเทคนิคของตัวเอง. Trigger: 'agent', 'MCP', 'harness', 'eval agent', 'prompt eng', 'token optimize'."
version: 1.0.0
author: A-Wiki
domain: [ai-ops, engineering]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/A-Agent"
a_phase: any
---

# A-Agent — งาน AI/Agent engineering

> **Dispatcher ล้วน** — ไม่มีเทคนิคเป็นของตัวเอง หน้าที่เดียวคือผูก 7-phase spine
> เข้ากับ canonical skill ที่มีอยู่แล้ว ถ้าต้อง *อธิบายวิธีทำ* แปลว่ามันควรเป็น
> canonical skill ไม่ใช่ pack

## เมื่อไหร่ใช้

✅ ใช้:
- สร้าง agent harness / autonomous loop ใหม่
- สร้าง MCP server / tool
- วัดผล agent (eval harness)
- optimize prompt / token
- กระจายงานให้ subagent

❌ ข้าม:
- แค่เขียน prompt อย่างเดียวไม่ได้สร้างระบบ → `prompt-optimizer` ตรงๆ
- งาน LLM app ทั่วไปไม่ใช่ agent → `a-backend`

## Iron Law

> **`focus_set` ก่อนเริ่มเสมอ** — pack ครอบทั้ง chain

```
focus_set({"skill": "a-agent", "goal": "<done criteria>", "phase": "ask"})
```

## Phase → skill

| Phase | ใช้ | ทำอะไร |
|-------|-----|--------|
| ASK | `a-think` · `grill-with-docs` | นิยาม "agent" ให้ชัด: autonomous? tool-use? eval criteria? |
| DESIGN | `agent-harness-construction` · `mcp-server-patterns` · `agent-architecture-audit` · (agent UI/chat/dashboard? → `/A-Design` ใช้ grammar consumer-service) | วาง harness shape + tool surface + audit boundary + UI เมื่อ agent มีหน้าจอ |
| PLAN | `a-plan` | แตกเป็น slice (harness → tool → eval) |
| IMPLEMENT | `mcp-builder` · `continuous-agent-loop` · `delegate-subagent` | สร้างจริง |
| REVIEW | `a-council` · `eval-harness` · `agent-eval` | รีวิว + วัดผล |
| DEBUG | `a-debug` · `agent-introspection-debugging` | repro → introspect → root cause |
| TEST | `eval-harness` · `ai-regression-testing` | eval + regression |

> เดิน phase ด้วย `focus_advance` · จบงาน `focus_clear`

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "ใช้ ECC skill ตรงๆ ก็ได้" | ได้ — แต่ยังต้อง `focus_set` ไม่งั้นไม่มีใครรู้ว่าอยู่ phase ไหน |
| "pack นี้ควรมีเทคนิคของตัวเอง" | ไม่ — ถ้าต้องอธิบายวิธีทำ ให้ไปสร้าง canonical skill แล้ว bind มาแทน |

## Invocation

```
/A-Agent "<งาน>"
```
