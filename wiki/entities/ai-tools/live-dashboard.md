---
type: entity
category: [project, tool]
tags: [dashboard, monitoring, realtime, sse, swarm, model-routing, awiki-core, light-theme, 3-zone]
sources: []
created: 2026-06-18
updated: 2026-06-19
last_verified: 2026-06-19
verify_tool: training
---

# Live Dashboard — A-Wiki Real-time Monitor

**ประเภท**: internal tool / monitoring server (v2.2 "Cyber-Clean")
**สถานะ**: ✅ ใช้งานจริง — auto-start ทุก session ที่ port `:7790`

## ภาพรวม
Live Dashboard เป็น HTTP + SSE server (Python stdlib, zero-dep) ที่ให้ภาพ real-time ของการทำงานใน A-Wiki — event feed, knowledge-graph delta, swarm/agent activity, และ model-routing config. รุ่น v2.2 เพิ่ม 3-zone layout, light-first theme + dark toggle, และ client-derived metrics (throughput, latency P50/P99). <code>scripts/live-dashboard/live-dashboard.html</code> เป็น single-file < 60KB. [training]

## คุณสมบัติหลัก
- **3-zone layout**: Z1 metrics bar, Z2 orchestrator + subagents grid/flow/timeline/graph, Z3 resource monitor. Event log sidebar right, settings slide-over overlay
- **Light/Dark theme**: light default (`#f5f7f6`, mint accent) + dark toggle (`[data-theme="dark"]`), persisted in `localStorage`, respects `prefers-color-scheme`
- **Client-derived metrics**: throughput (events/s), P50/P99 latency (from `delegate_done.duration_ms` rolling window), session uptime, total requests — all computed from SSE event stream, zero server changes
- **Subagents grid**: agent cards with real-time status (RUNNING/QUEUED/DONE/FAILED), duration count, delegation count, utilization bar
- **Event feed** — tail log ของ tool calls / hooks / agent actions ผ่าน SSE broadcast
- **4 views in Z2-center**: Grid (default agent cards), Flow (origin→station pipes + particles), Timeline (branching lanes), Graph (vis-network knowledge graph)
- **Resource monitor**: per-model delegation share bars + infra footer ("LOCAL: MAC MINI M4 · N PROVIDERS · COST-FIRST ROUTING")
- **Model config UI** ⚙️ — อ่าน/เขียน roster + key status (`/api/models`, `/api/keys`); เขียน key ลง `drive/.secrets` เท่านั้น
- **Contract test suite**: 17 tests guarding tokens, size (<60KB), SSE contracts, animations, theme toggle, zone IDs, fake-data absence, and latency window
- **Idle watchdog** — `idle_watchdog()` ปิดตัวเองเมื่อ idle เพื่อไม่กิน resource
- **PID-guard** — `is_already_running()` + `_is_port_free()` กันเปิดซ้อน

## การใช้งานใน A-Wiki
- โค้ดอยู่ที่ `scripts/live-dashboard/` (`server.py`, `live-dashboard.html`) — server เป็น DOM-agnostic, ใช้ fallback path `exports/html/live-dashboard.html`
- ใช้เลือก/เปลี่ยน model ของ swarm (เช่น GLM ดู [[zai-glm]]) ผ่าน ⚙️ panel
- ตรวจสถานะ: `lsof -i :7790` หรือ `curl http://localhost:7790`

## ความสัมพันธ์
- ใช้ร่วมกับ: [[zai-glm]] · [[model-capability-bench]] — แสดง/สลับ model routing
- เกี่ยวข้องกับ: SessionStart hook (`session_start.py`), `docs/protocols/model-switching.md` · `docs/design/dashboard-design-system.md`
- Design tokens: `docs/design/dashboard-design-system.md` v2.2-light

## แหล่งข้อมูล
- `scripts/live-dashboard/README.md` — สถาปัตยกรรม server + event schema + 3-zone layout
- `docs/design/dashboard-design-system.md` — design tokens + component architecture
- `tests/test_live_dashboard_html.py` — 17 contract tests
