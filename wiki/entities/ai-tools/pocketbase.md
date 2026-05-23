---
type: entity
category: platform
tags: [pocketbase, backend, sqlite, rest-api, realtime, self-hosted, open-source]
sources: [vibe-pocketbase-gemini-plan]
created: 2026-05-11
updated: 2026-05-11
last_verified: 2026-05-11
verify_tool: training
---

# PocketBase

**ประเภท**: Backend-as-a-Service แบบ self-hosted (single binary)  
**สถานะ**: Active — open source, maintained

## ภาพรวม

PocketBase คือ open-source backend framework ที่รวม SQLite database, REST API, realtime subscriptions, authentication และ Admin UI ไว้ใน **single binary file** ไฟล์เดียว รันได้บนทุก OS (Linux/Mac/Windows) ไม่ต้อง install dependencies

จุดแข็งคือความเรียบง่าย — download binary แล้วรันได้ทันที เหมาะมากสำหรับ vibe coding และ indie projects ที่ต้องการ backend เร็ว

## คุณสมบัติหลัก

- **Single binary**: ไม่ต้อง install Node.js, Python, Database server — รันไฟล์เดียว
- **Admin UI**: GUI สร้าง/จัดการ collection (table) ได้เหมือน Airtable/Excel คลิกได้เลย
- **REST API + Realtime**: สร้าง collection แล้ว API งอกให้อัตโนมัติ — ไม่ต้องเขียน backend code
- **Authentication built-in**: รองรับ email/password, OAuth2 (Google, GitHub ฯลฯ), OTP
- **SQLite storage**: ข้อมูลทั้งหมดอยู่ในไฟล์ `pb_data/data.db` — backup ง่ายมาก
- **JavaScript SDK**: `npm install pocketbase` — ใช้จาก React/Vue/Vanilla JS

## การใช้งานใน Vibe Coding Projects

```bash
# ดาวน์โหลด binary และรัน
./pocketbase serve
# Admin UI: http://127.0.0.1:8090/_/
# REST API:  http://127.0.0.1:8090/api/
```

**Pattern หลัก**:
1. สร้าง collection ผ่าน Admin UI (เหมือน Excel)
2. PocketBase สร้าง REST API ให้อัตโนมัติ
3. Frontend ใช้ PocketBase SDK ยิง API — ไม่ต้องเขียน backend

```javascript
// Frontend SDK usage
import PocketBase from 'pocketbase';
const pb = new PocketBase('http://127.0.0.1:8090');

// Query
const records = await pb.collection('orders').getList();

// Create
await pb.collection('orders').create({ name: 'Test', qty: 5 });

// Auth
await pb.collection('users').authWithPassword(email, password);
```

## Infra + Backup

- **Nginx reverse proxy**: รับ port 80/443 → forward ไป 127.0.0.1:8090
- **Backup**: แค่ zip ไฟล์ `pb_data/data.db` แล้ว push ขึ้น Cloudflare R2 หรือ S3
- **Migrations**: `pb_migrations/` เก็บ schema history ไว้ track ด้วย git ได้

## ข้อเปรียบเทียบกับ Alternatives

| Feature | PocketBase | Supabase | Firebase |
|---------|-----------|---------|---------|
| Self-hosted | ✅ | ✅ (หนักกว่า) | ❌ |
| Single binary | ✅ | ❌ (Docker stack) | ❌ |
| Admin UI | ✅ | ✅ | ✅ |
| Real-time | ✅ | ✅ | ✅ |
| ราคา | ฟรี 100% | Free tier มีขีดจำกัด | Free tier มีขีดจำกัด |
| Complexity | ต่ำมาก | กลาง | กลาง |

## ข้อจำกัด

- ไม่เหมาะกับ scale ใหญ่มาก (millions rows + high concurrency)
- SQLite ไม่รองรับ multi-writer concurrent (ใช้ write lock) — single server เท่านั้น
- ไม่มี built-in horizontal scaling (ต่างจาก PostgreSQL-based solutions)

## ความสัมพันธ์

- ใช้ร่วมกับ: [[concepts/ai-tools/vibe-coding]]
- ใช้ร่วมกับ: [[synthesis/vibe-pocketbase-project]]
- แข่งขันกับ: Supabase, Firebase, Directus, Appwrite
- DB engine: SQLite (ดู [[entities/iot/influxdb]] สำหรับ time-series alternative)

## แหล่งข้อมูล

- [[sources/vibe-pocketbase-gemini-plan]] — แผน project structure จาก Gemini Pro [training]
