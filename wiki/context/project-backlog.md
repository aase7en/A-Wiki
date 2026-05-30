# Project Backlog

> **Purpose**: เก็บงานค้างที่ไม่ควรถูกพิมพ์ทุก SessionStart แต่ยังต้องค้นเจอและทำต่อได้
> **SessionStart rule**: งานที่ต้องเห็นทุกครั้งเท่านั้นอยู่ใน `wiki/context/session-memory.md` §Active TODOs
> **Updated**: 2026-05-30

## Near-Term Project Carry-Over

| Project | Next action | Context |
|---|---|---|
| sunday-estate-webapp | ปิด Cloudflare Tunnel ให้ production-ready; `app.sundayestate.co.th` ยังเป็น DNS `NXDOMAIN`; ต้องมี Cloudflare zone/tunnel credentials + enable `public` profile | Stack compose มี `cloudflared` แต่ยังไม่มี `se-cloudflared` container |
| sunday-estate-webapp | Verify admin invite POST/send end-to-end ด้วย logged-in admin | GET `/api/admin/invitations` ผ่าน 200; `SUPABASE_SERVICE_KEY` env confirmed ใน Portainer โดยไม่เปิดเผยค่า |
| sunday-estate-webapp | Cinematic intro Phase 3 | ต่อจาก 2026-05-30 session ที่ ship Phases 1→2.4 ไป `prototype/`, commits `bb54f64`→`5fc87dc`; plan: `~/.claude/plans/website-graceful-petal.md` |
| sunday-estate-site | Continue M2 | M1 v2 shipped commit `73f335b`; repo private `aase7en/sunday-estate-site`; M2 = i18n TH/EN + Services + 32 Objectives accordion + e-GP detail + Act 5 responsive polish |

## Dream Backlog

| Dream | Outcome |
|---|---|
| Sunday Estate | Production-ready domain + Cloudflare Tunnel |
| Personal AI Agent | Agent ส่วนตัวที่ใช้ A-Wiki เป็นสมอง ตอบคำถามและจัดการชีวิตได้ offline-first |
| IoT Dashboard | Dashboard กลางสำหรับ sensor/device บ้านและที่ทำงาน พร้อม real-time + alert |
| Pharmacy App | แอพจัดการ Phu Pharmacy: stock, ค้นหายา, order history, LINE notify |

## A-Wiki / InW-Wiki Backlog

| Area | Next action |
|---|---|
| Cross-platform | Verify Linux/Windows clone + `pip install -r requirements.txt` + `python scripts/build-vec-index.py` |
| InW-Wiki carry-over | ทดสอบ `ask-notebooklm.py`, `delegate.sh`, `sync.py`, `hooks_runner.py` ที่ merge/copy จาก InW-Wiki |
| Cost Pyramid | เพิ่ม Cost Pyramid enforcement ใน platform docs ที่ยังไม่ครบ โดยไม่แก้ `CLAUDE.md` เว้นแต่ user อนุญาต |
| Pharmacy scripts | Copy/port `pharmacy_lookup.py`, `build_pharmacy_db.py`, `compare_delivery.py` จาก InW-Wiki ถ้ายังใช้จริง |
| Storage | Unified storage layer: SQLite รวม FTS5 + graph + logs เป็น single source of truth |
| Tagging | Dynamic domain tagging: multi-label tags แทน directory-based domains |
| Sync | ทดสอบ `sync.py --daemon` บน multi-device Mac + Work PC |
| Research | ศึกษา OmegaWiki, LLM-Wiki-Skilled, long-term-agent-memory เพื่อออกแบบ entity/memory layer รอบต่อไป |

## External Repo Setup Backlog

| Repo/project | Next action |
|---|---|
| Sunday Estate / Pharmacy / IoT repos | Run `bash scripts/setup-gitnexus.sh` ครั้งเดียวต่อ repo เพื่อได้ code graph |
| GitNexus | Investigate why `scripts/lib/drive_secrets.py` symbol indexing ไม่ครบ; `fetch_secret` queryable as caller แต่ context ไม่เจอ |

## Parking Lot

| Area | Note |
|---|---|
| env-webapp | Telegram Bot future: architecture อยู่ใน `waste-form-automation.md`; implement เมื่อพร้อม Raspberry Pi 5 + Bot token |
| InW-Wiki | Merge `review-check.py` กลับไป InW-Wiki เมื่อ A-Wiki checker นิ่งแล้ว |
