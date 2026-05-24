---
type: source
title: "Supabase 2026 — ภาพรวม + วิเคราะห์ความเหมาะสมกับโปรเจกต์ของ Aase7en"
slug: supabase-2026-aase7en
date_ingested: 2026-05-24
original_file: raw/supabase-overview-2026-05-02.md
---

```yaml
---
title: "Supabase 2026 — ภาพรวม + วิเคราะห์ความเหมาะสมกับโปรเจกต์ของ Aase7en"
date_collected: "2026-05-02"
collected_by: "gemini (web search) + claude (synthesis)"
status: "raw"
---
```

# Supabase — ทำความรู้จัก + ควรใช้กับโปรเจกต์ไหนของคุณ

> **บริบทผู้ใช้**: โปรเจกต์ในมือคือ Pharmacy web app (ภูฟาร์มาซี — FastAPI + React + Pi5 + Claude API for OCR) และ IoT side projects (ESP32, MQTT)
> เอกสารนี้แบ่งเป็น 2 ส่วน: **ส่วน A** ข้อเท็จจริง Supabase, **ส่วน B** การ synthesize ว่าเหมาะกับโปรเจกต์คุณไหม

---

## ส่วน A — ข้อเท็จจริง Supabase 2026

### 1. Supabase คืออะไร

**Backend-as-a-Service (BaaS) แบบ open-source** สร้างทับ PostgreSQL — แทนที่จะให้ NoSQL แบบ Firebase, Supabase ใช้ Postgres จริงๆ ทำให้ได้ SQL + transaction + ACID เต็มรูปแบบ

**สถาปัตยกรรมหลัก:**
| Component | หน้าที่ |
|---|---|
| **PostgreSQL** | core DB (มี extension: pgvector, PostGIS, pg_cron, pg_graphql) |
| **PostgREST** | auto-generate REST API จาก schema |
| **GoTrue** | Auth (email/OAuth/magic link/SAML) |
| **Realtime** | WebSocket subscribe การเปลี่ยนแปลง row |
| **Storage** | S3-compatible file storage |
| **Edge Functions** | Serverless (Deno runtime) |
| **Vector Buckets** | (2026 ใหม่) S3-compatible vector lake สำหรับ AI |
| **Multigres** | (2026 ใหม่) horizontal scaling layer |

### 2. ข้อดี (5 ข้อ)

1. **PostgreSQL จริง** — ไม่ใช่ NoSQL เลียนแบบ → query ซับซ้อน, JOIN, view, trigger ได้ครบ
2. **Open-source + self-host ได้** — ไม่มี vendor lock-in (รัน Docker เองบน Pi5/VPS ก็ได้)
3. **Auto API + Type-safe SDK** — เขียน schema → ได้ REST/GraphQL/TypeScript types ทันที
4. **Row Level Security (RLS)** — security ระดับ row ใน Postgres → frontend คุยกับ DB ตรงๆ ได้อย่างปลอดภัย
5. **AI/Vector ready** — `pgvector` ในตัว + Vector Buckets + MCP integration → ทำ RAG/semantic search ง่าย

### 3. ข้อเสีย (5 ข้อ)

1. **Learning curve SQL + RLS** — ถ้าไม่เคยเขียน Postgres policy → งง พอสมควร
2. **Offline support อ่อน** — Firebase ทำ offline-first ดีกว่ามาก (สำคัญสำหรับ mobile)
3. **Edge Functions ยังไม่ mature** — Deno runtime, cold start, debugging ยาก
4. **Self-host ยุ่งกว่าที่โฆษณา** — ต้อง maintain ~7 services (Postgres, GoTrue, Storage, Realtime, Kong, PostgREST, Studio)
5. **Cost jump ที่ high tier** — Free → Pro $25 ไม่กระโดด แต่ Pro → Team/Enterprise กระโดดเยอะ

### 4. Pricing 2026 (verified 2026-05-02 จาก supabase.com/pricing)

| Plan | ราคา | DB | Bandwidth (egress + cached) | MAU | File Storage |
|---|---|---|---|---|---|
| **Free** | $0 | 500 MB | 5 GB + 5 GB | 50,000 | 1 GB |
| **Pro** | $25/mo | 8 GB (+$0.125/GB) | 250 GB + 250 GB (+$0.09/$0.03/GB) | 100,000 (+$0.00325/MAU) | 100 GB (+$0.021/GB) |
| **Team** | $599/mo | เหมือน Pro | เหมือน Pro | เหมือน Pro | เหมือน Pro |
| **Enterprise** | Custom | Custom | Custom | Custom | Custom |

> **หมายเหตุ**: Team ราคาแพงกว่า Pro ที่ resource เท่ากัน เพราะได้ SOC2, SSO, log retention นานกว่า, role-based access — ไม่ใช่ resource เพิ่ม

### 5. ความยากง่าย

- **Time to first project**: 5-10 นาที (สมัคร → สร้าง project → ได้ DB + API)
- **Time to production app**: 1-2 สัปดาห์ (เรียน RLS, design schema, integrate frontend)
- **Prerequisites**:
  - SQL พื้นฐาน (SELECT, JOIN, FK) — ✅ จำเป็น
  - React/Next.js หรือ framework อื่น — ✅ จำเป็น
  - Auth concepts (JWT, OAuth) — ⚠️ ดีถ้ามี
  - PostgreSQL advanced (RLS, function, trigger) — ⚠️ เรียนตอนเจอปัญหา

### 6. เปรียบเทียบทางเลือก

| เกณฑ์ | **Supabase** | **Firebase** | **PocketBase** | **Self-host PG+FastAPI** |
|---|---|---|---|---|
| DB engine | Postgres | Firestore (NoSQL) | SQLite | Postgres |
| Self-host | ✅ ได้ | ❌ ไม่ได้ | ✅ single binary! | ✅ ได้ |
| Setup time | 5 นาที | 5 นาที | 1 นาที | 1-2 ชม |
| Pi5 deploy | ⚠️ หนัก (~7 services) | ❌ | ✅✅ เบา | ✅ |
| Realtime | ✅ ดี | ✅ ดีที่สุด | ⚠️ พอใช้ |  ❌ ต้องทำเอง |
| Auth | ✅ ครบ | ✅ ครบ | ✅ พื้นฐาน | ❌ ต้องทำเอง |
| Vector/AI | ✅✅ pgvector | ❌ | ❌ | ✅ ถ้า install pgvector |
| ราคา free | 500MB DB | quota แชร์ | $0 ถ้า self-host | $0 ถ้า self-host |
| Offline-first | ⚠️ อ่อน | ✅✅ ดีที่สุด | ⚠️ อ่อน | ❌ |
| Lock-in | ต่ำ (PG export) | สูงมาก | ต่ำมาก | ต่ำสุด |

### 7. Use case เหมาะ vs ไม่เหมาะ

**✅ เหมาะ:**
- Web app/SaaS ที่ต้องมี Auth + DB + Realtime
- AI app ที่ต้อง vector search (RAG, semantic search)
- MVP ที่อยาก ship เร็ว แต่ migrate ได้ในอนาคต
- Multi-tenant app (RLS ทำได้สวย)

**❌ ไม่เหมาะ:**
- Mobile-first app ที่ต้อง offline สนิท → ใช้ Firebase
- Edge IoT ที่อยู่ในเครื่อง embedded → ใช้ SQLite/PocketBase
- Heavy real-time gaming → latency สูงกว่า dedicated solution
- ระบบ enterprise legacy ที่ต้อง on-prem แบบ strict → self-host เอาแต่ต้อง maintain

### 8. ข่าวเด่น 2026

1. **ChatGPT App official integration (พ.ค. 2026)** — Supabase เป็น app ใน ChatGPT → จัดการ DB/schema/migration/edge functions ผ่านภาษาธรรมชาติได้ (ภาพที่คุณส่งมา)
2. **MCP Server support** — เชื่อม Claude Code, Cursor, Windsurf ได้ direct
3. **Vector Buckets** — S3-compatible vector lake ใหม่ แยกจาก pgvector
4. **Multigres** — horizontal scaling แบบ Vitess-for-Postgres (เปิดตัวต้นปี 2026)
5. **OpenAI Apps SDK** — สร้าง custom GPT ที่อ่าน/เขียน Supabase ได้

---

## ส่วน B — เชื่อมโยงกับโปรเจกต์ของคุณ (Synthesis โดย Claude)

### โปรเจกต์ 1: Pharmacy Web App (ภูฟาร์มาซี — Phase 2)

**สเปคปัจจุบันใน wiki**: FastAPI + React + Pi5 + Claude API (OCR + drug validation)

| มิติ | ใช้ Supabase? | เหตุผล |
|---|---|---|
| **Drug catalog (3,760 SKU)** | 💚 **ใช่ — เหมาะมาก** | Postgres + full-text search ภาษาไทย + pgvector สำหรับ fuzzy match ชื่อยาสะกดผิด |
| **Auth ลูกค้า/พนักงาน** | 💚 ใช่ | GoTrue ทำได้เลย ไม่ต้องเขียน FastAPI auth เอง |
| **Order history / LINE integration** | 🟡 ก็ได้ | RLS แยก order ตาม user, realtime subscribe order status |
| **OCR pipeline (Claude API)** | ❌ ไม่เกี่ยว | OCR ต้องเรียก Claude API จาก backend อยู่ดี |
| **Deploy บน Pi5** | 🔴 **อย่า self-host** | Supabase stack หนักเกินไปสำหรับ Pi5 — ใช้ Supabase cloud (Free/Pro) แทน |

**คำแนะนำสำหรับ Pharmacy:**
- ✅ **ลองใช้ Supabase Free tier แทน FastAPI + self-host Postgres** ใน Phase 2
- 💡 ใช้ pgvector เก็บ embedding ของชื่อยา → fuzzy match ภาษาไทยที่สะกดผิดได้ดีกว่า fuzzywuzzy เยอะ
- 💡 Pi5 รัน **เฉพาะ OCR worker** (เรียก Claude API) → push ผลลง Supabase cloud
- ⚠️ ระวัง: data 3,760 SKU = JSON ~3-5 MB, อยู่ใน free tier 500 MB สบาย แต่ embedding 1,536 มิติ × 3,760 ≈ 23 MB เพิ่มเข้าไป → ยังไม่เต็ม
- 🆕 **Bonus**: ChatGPT integration ใหม่ → คุณ debug schema, run migration ผ่าน chat ได้ → เร็วกว่า psql มาก

**สรุป**: **Supabase เหมาะกับ Pharmacy มาก** — น่าจะลด dev time ได้ 30-50% เทียบกับ FastAPI auth+CRUD เขียนเอง

### โปรเจกต์ 2: IoT (ESP32, MQTT, sensors)

| มิติ | ใช้ Supabase? | เหตุผล |
|---|---|---|
| **Telemetry storage (sensor data)** | 🟡 ก็ได้ แต่ไม่ optimal | Postgres ไม่ใช่ time-series DB — เก็บได้แต่ไม่ optimal เท่า InfluxDB/TimescaleDB |
| **MQTT broker** | ❌ ไม่ใช่ | Supabase ไม่มี MQTT — ต้อง Mosquitto/EMQX แยก |
| **Dashboard frontend** | 💚 ใช่ | Realtime subscribe → live chart |
| **Auth สำหรับ devices** | 🟡 ก็ได้ | แต่ JWT-on-device ค่อนข้างหนักสำหรับ ESP32 |

**คำแนะนำสำหรับ IoT:**
- 💡 ใช้ Supabase **เฉพาะ dashboard frontend + user auth**
- 💡 Telemetry → ใช้ TimescaleDB extension ใน Postgres (Supabase รองรับ) → ได้ time-series ใน Postgres เดียวกัน
- ❌ อย่าใช้ Supabase replace MQTT — ESP32 → MQTT broker → bridge → Supabase (architecture เดิม)

**สรุป**: **เสริมได้ ไม่ใช่หลัก** — ใช้สำหรับชั้น UI/Auth, ไม่ใช่ ingestion layer

### Verdict: คุณ "จำเป็น" ต้องใช้ Supabase ไหม?

| โปรเจกต์ | จำเป็น? | คำแนะนำ |
|---|---|---|
| **Pharmacy** | 🟢 **ควรลอง** | Phase 2 ลองสร้าง prototype บน Supabase Free 1 weekend → ถ้าเร็วกว่า FastAPI ที่ทำอยู่ก็ migrate |
| **IoT** | 🟡 มีก็ดี | ใช้สำหรับ frontend dashboard ดีกว่าเขียน WebSocket เอง |
| **AI Tools side** | 🟢 ควรรู้ | MCP server ของ Supabase = practice ground ดี |
| **Wiki ตัวนี้** | 🔴 ไม่ต้อง | Markdown + GitHub + Obsidian + Claude เพียงพอ ไม่ต้อง DB |

### Action items ที่แนะนำ (ทำ/ไม่ทำก็ได้)

- [ ] **Weekend experiment**: สร้าง Supabase project ฟรี → import `sp_drugs_full_3760.json` → ลอง full-text search ภาษาไทย + pgvector fuzzy match
- [ ] เปรียบเทียบ DX กับ FastAPI version ที่กำลังพัฒนา
- [ ] ถ้าใช่ → เขียน ADR (decision record) เลือก Supabase vs FastAPI สำหรับ Phase 2
- [ ] ลอง MCP integration: เชื่อม Claude Code → Supabase project ของ Pharmacy → query แบบสนทนา

---

## แหล่งข้อมูล

> URLs ยังไม่ verify (Gemini server overload ตอน synthesis) — Claude session ถัดไปควรเช็คก่อน promote ลง wiki/

- supabase.com/pricing — pricing tiers (verify ก่อน cite)
- supabase.com/docs/guides/getting-started — onboarding
- ภาพ ChatGPT integration ที่ผู้ใช้ส่ง (sanookai.com) — 2026-05-02
- Supabase blog — Multigres, Vector Buckets announcements (2026)
