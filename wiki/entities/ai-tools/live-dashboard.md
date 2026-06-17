---
type: entity
category: [project, tool]
tags: [dashboard, monitoring, realtime, websocket, swarm, model-routing, awiki-core]
sources: []
created: 2026-06-18
updated: 2026-06-18
last_verified: 2026-06-18
verify_tool: training
---

# Live Dashboard — A-Wiki Real-time Monitor

**ประเภท**: internal tool / monitoring server
**สถานะ**: ✅ ใช้งานจริง — auto-start ทุก session ที่ port `:7790`

## ภาพรวม
Live Dashboard เป็น HTTP + WebSocket server (Python stdlib, zero-dep) ที่ให้ภาพ real-time ของการทำงานใน A-Wiki — event feed, knowledge-graph delta, swarm/agent activity, และ model-routing config. เริ่มอัตโนมัติโดย SessionStart hook (`session_start.py` → `dashboard-ensure.sh` → `server.py --daemonize`, PID-guarded) เปิด browser ครั้งแรกที่ `localhost:7790`. ปิด autostart ได้ด้วย `AWIKI_DISABLE_DASHBOARD_AUTOSTART=1`. [training]

## คุณสมบัติหลัก
- **Event feed** — tail log ของ tool calls / hooks / agent actions ผ่าน WebSocket broadcast
- **Graph panel** — knowledge-graph snapshot + delta (`_graph_snapshot`, `_process_graph_event`)
- **Model config UI** ⚙️ — อ่าน/เขียน roster + key status (`/api/models`, `/api/keys`); เขียน key ลง `drive/.secrets` เท่านั้น
- **Idle watchdog** — `idle_watchdog()` ปิดตัวเองเมื่อ idle เพื่อไม่กิน resource
- **PID-guard** — `is_already_running()` + `_is_port_free()` กันเปิดซ้อน

## การใช้งานใน A-Wiki
- โค้ดอยู่ที่ `scripts/live-dashboard/` (`server.py`, `event_logger.py`, `live-dashboard.html`)
- ใช้เลือก/เปลี่ยน model ของ swarm (เช่น GLM ดู [[zai-glm]]) ผ่าน ⚙️ panel
- ตรวจสถานะ: `lsof -i :7790` หรือ `curl http://localhost:7790`

## ความสัมพันธ์
- ใช้ร่วมกับ: [[zai-glm]] · [[model-capability-bench]] — แสดง/สลับ model routing
- เกี่ยวข้องกับ: SessionStart hook (`session_start.py`), `docs/protocols/model-switching.md`

## แหล่งข้อมูล
- `scripts/live-dashboard/README.md` — สถาปัตยกรรม server + event schema
