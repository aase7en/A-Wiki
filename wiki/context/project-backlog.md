# Project Backlog

> **Purpose**: เก็บงานค้างที่ไม่ควรถูกพิมพ์ทุก SessionStart แต่ยังต้องค้นเจอและทำต่อได้
> **SessionStart rule**: งานที่ต้องเห็นทุกครั้งเท่านั้นอยู่ใน `wiki/context/session-memory.md` §Active TODOs
> **Updated**: 2026-05-30

## Near-Term Project Carry-Over

| Project | Next action | Context |
|---|---|---|
| private-webapp | ปิด Cloudflare Tunnel ให้ production-ready; domain ยังเป็น DNS `NXDOMAIN`; ต้องมี Cloudflare zone/tunnel credentials + enable `public` profile | รายละเอียดจริงอยู่ใน private journal/Drive |
| private-webapp | Verify admin invite POST/send end-to-end ด้วย logged-in admin | ตรวจ flow โดยไม่เปิดเผย service key |
| private-webapp | Cinematic intro Phase 3 | รายละเอียด repo/commit/plan อยู่ใน private journal/Drive |
| private-site | Continue M2 | รายละเอียด repo/commit/objectives อยู่ใน private journal/Drive |

## Dream Backlog

| Dream | Outcome |
|---|---|
| Private business site | Production-ready domain + Cloudflare Tunnel |
| Personal AI Agent | Agent ส่วนตัวที่ใช้ A-Wiki เป็นสมอง ตอบคำถามและจัดการชีวิตได้ offline-first |
| IoT Dashboard | Dashboard กลางสำหรับ sensor/device บ้านและที่ทำงาน พร้อม real-time + alert |
| Pharmacy App | แอพจัดการ Phu Pharmacy: stock, ค้นหายา, order history, LINE notify |

## A-Wiki / InW-Wiki Backlog

| Area | Next action |
|---|---|
| Cross-platform | Repo-side verifier done: run `python3 scripts/verify-next-machine.py --build-vec` after pull on each machine |
| Legacy wiki carry-over | Core scripts/evals/hooks verified; pharmacy scripts ported; remaining carry-over only when a real use case appears |
| Storage | Future architecture: unified SQLite รวม FTS5 + graph + logs เป็น single source of truth |
| Tagging | Future architecture: dynamic domain tagging / multi-label tags แทน directory-only domains |
| Research | ศึกษา OmegaWiki, LLM-Wiki-Skilled, long-term-agent-memory เพื่อออกแบบ entity/memory layer รอบต่อไป |

## External Repo Setup Backlog

| Repo/project | Next action |
|---|---|
| Private business / Pharmacy / IoT repos | Use `AWIKI_DREAM_REPOS="/path/a:/path/b" bash scripts/setup-dream-gitnexus.sh` |
| GitNexus | Investigate why `scripts/lib/drive_secrets.py` symbol indexing ไม่ครบ; `fetch_secret` queryable as caller แต่ context ไม่เจอ |

## Parking Lot

| Area | Note |
|---|---|
| env-webapp | Telegram Bot future: architecture อยู่ใน `waste-form-automation.md`; implement เมื่อพร้อม Raspberry Pi 5 + Bot token |
| Legacy wiki | Merge `review-check.py` กลับไป legacy wiki เมื่อ A-Wiki checker นิ่งแล้ว |
