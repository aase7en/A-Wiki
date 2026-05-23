---
title: Sunday Estate Webapp — Frontend QA Batch (2026-05-18)
type: synthesis
domain: cross-domain
related:
  - ai-tools
  - iot
status: deployed-frontend / pending-backend-migrations
created: 2026-05-18
session: 2026-05-18 dev
sources:
  - User QA report 2026-05-18 (4 bugs from production UI testing)
  - Plan file ~/.claude/plans/webapp-snoopy-lobster.md (in-session, local-only)
  - Webapp commit aase7en/sunday-estate-webapp@1e8147c
  - Webapp repo: /Users/aase7en/Desktop/sunday-estate-webapp/
---

# Sunday Estate Frontend QA Batch — 2026-05-18

> **Purpose**: handoff doc สำหรับ AI agent ตัวถัดไปที่จะมาทำงานต่อกับ webapp นี้
> หลัง Claude Sonnet 4.6 ติด rate limit หรือ session หมด
> ดู synthesis หลัก: [[sunday-estate-webapp]]

> **Status**: Frontend commit `1e8147c` push สำเร็จขึ้น `origin/main` แล้ว
> รอ user redeploy Pi5 + verify + ส่งงาน backend migrations ให้ session ถัดไป

---

## 🎯 Context (ทำไมงานนี้ถึงเกิด)

User test production UI ที่ `http://umbrel.local:8090` หลัง deploy เสร็จ (commit b0d1d09) แล้วแจ้ง **4 ปัญหา** ใน 1 message:

1. OCR เอกสาร > ทะเบียนบ้าน > input box "ผู้อยู่อาศัย" อ่านออกมาเป็น raw JSON
2. ปุ่ม "บันทึกใหม่" บน Dashboard (admin) ไม่ทำงาน
3. ปุ่มผีทั่ว frontend (21 ปุ่ม) — user ต้องการให้ "ทุกปุ่มทำงานได้จริง ไม่ใช่ปุ่มผีว่างๆ"
4. ตาราง ปล่อยกู้/ขายฝาก ไม่มี select-all + bulk Edit/Delete

User decisions (จาก AskUserQuestion):
- Dashboard btn → **Quick-Create menu** (สัญญาใหม่ / ที่ดินใหม่)
- Bulk Edit → **Bulk patch field** (status/type หลาย row พร้อมกัน)
- Ghost btns → **Wire ทุกปุ่ม scope ขยาย** (ไม่ใช่ "Coming soon" toast)

---

## ✅ สิ่งที่ทำเสร็จแล้ว (commit `1e8147c`, 1,210 บรรทัด, 7 ไฟล์)

### T1 — OCR `_flattenOcrRows` fix
- **Root cause**: `prototype/src/misc.jsx:199` มี `&& !Array.isArray(v)` ทำให้ array-of-objects ตกลง `_ocrValueToText` แล้วโดน `JSON.stringify`
- **Fix**: เอา `&& !Array.isArray(v)` ออก → array recurse เป็น rows แยก
- **ผล**: `residents: [{name:"A"},{name:"B"}]` → flatten เป็น `residents.name` (section #1), `residents.name` (section #2)

### T4 — Bulk select + edit + delete (ปล่อยกู้/ขายฝาก)
- **Files**: `loans.jsx` (state + UI + `BulkEditLoansModal`) + `data.jsx` (`bulkUpdateLoans` + `bulkDeleteLoans`)
- **Features**:
  - Header checkbox indeterminate (`-`) เมื่อเลือกบางส่วน
  - Bulk action bar: "N รายการที่เลือก" + ปุ่ม Bulk edit / Delete / Clear
  - Bulk Delete: confirm + Supabase `.in()` filter (RLS admin-only)
  - Bulk Edit modal: pick field (status/type/scope) + new value (dropdown ตามชนิด)
- **Note**: ขายฝากไม่ใช่หน้าแยก — เป็น `type` filter ในตารางเดียวกัน → bulk ทำงานครอบคลุมทั้งสอง

### T2 — Dashboard Quick-Create menu
- **Files**: `dashboard.jsx` (dropdown UI) + `app.jsx` (pendingAction routing) + `loans.jsx`/`lands.jsx` (consume pendingAction)
- **Flow**: กด "บันทึกใหม่" → menu เด้ง → เลือก "สัญญาใหม่"/"ที่ดินใหม่" → setPage + setPendingAction("new") → list page useEffect เห็น pendingAction → setFormOpen(true)
- **Click-outside**: useEffect listener บน `document.mousedown`

### T3 — Ghost button audit (21 buttons wired)

| # | Location | Action |
|---|----------|--------|
| 3a | `dashboard.jsx:145` CashFlow 12M/6M/3M | Slice data array ตาม period state |
| 3b | `loans.jsx:127` ตัวกรอง | Dropdown panel: type checkboxes + due-within radio + counter badge |
| 3c | `loans.jsx:210` Pagination | Client-side 20/page + page selector buttons |
| 3d | `lands.jsx:40` รายงาน | Modal: Export CSV (BOM+UTF-8) / Print (Cmd+P → Save as PDF) |
| 3e | `borrower.jsx:36` ติดต่อเจ้าหน้าที่ | ContactOfficerModal: tel/LINE/mailto links |
| 3f | `borrower.jsx:37,130` แจ้งการชำระ | PaymentNotifyModal: slip upload + amount + date → insert `payment_notifications` |
| 3g | `borrower.jsx:106` เชื่อมต่อ/จัดการ | NotificationPrefsModal stub |
| 3h | `borrower.jsx:187` download icon | `window.open(doc.url, "_blank")` + fallback alert |
| 3i | `misc.jsx:42` Export iCal | Generate `.ics` blob from `LOANS.due` → download |
| 3j | `misc.jsx:43` เพิ่มนัดหมาย | NewEventModal: title + date + time + note → insert `events` |
| 3k | `misc.jsx:58-60` Month/Week/Agenda | View state → conditional render 3 layouts |
| 3l | `misc.jsx:528` ตั้งค่าแจ้งเตือน | AlertSettingsModal: per-type toggles + lead-days + quiet hours → upsert `app_settings.alert_preferences` |
| 3m | `misc.jsx:564` alert action btn | `handleAlertAction(a)` switch (dismiss/snooze/view) |
| 3n | `misc.jsx:730` เชิญผู้ใช้ | InviteUserModal: POST `/api/admin/invite` → fallback `pending_invitations` insert |
| 3o | `misc.jsx:758` edit pencil | EditUserModal: update `profiles.role` + `display_name` |
| 3p | `misc.jsx:783` Add integration | IntegrationManageModal: insert `integrations` |
| 3q | `misc.jsx:798` Manage/Connect | Same modal in edit mode |

---

## 🔴 ที่ค้างอยู่ — Backend migrations + FastAPI routes

### ตารางใหม่ที่ frontend modals คาดว่าจะมี (graceful fallback ตอนนี้ — alert "บันทึกแล้ว" แต่ data ไม่ persist)

#### 1. `payment_notifications` (สำหรับ PaymentNotifyModal)
```sql
create table public.payment_notifications (
  id           uuid primary key default gen_random_uuid(),
  loan_id      text references public.loans(id) on delete cascade,
  user_id      uuid references auth.users(id),
  amount       numeric not null,
  paid_at      date not null,
  slip_url     text,
  note         text,
  status       text not null default 'pending' check (status in ('pending','verified','rejected')),
  created_at   timestamptz not null default now(),
  verified_at  timestamptz,
  verified_by  uuid references auth.users(id)
);
alter table public.payment_notifications enable row level security;
-- RLS: borrower เห็นเฉพาะ row ของตัวเอง; admin/super เห็นทุก row
```
+ Storage bucket `payment-slips` (10MB, private, path `<loan_id>/<timestamp>-<name>`)

#### 2. `events` (สำหรับ NewEventModal + Calendar)
```sql
create table public.events (
  id            uuid primary key default gen_random_uuid(),
  title         text not null,
  scheduled_at  timestamptz not null,
  description   text,
  loan_id       text references public.loans(id) on delete set null,
  land_id       text references public.lands(id) on delete set null,
  created_by    uuid references auth.users(id),
  created_at    timestamptz not null default now()
);
alter table public.events enable row level security;
```

#### 3. `pending_invitations` + FastAPI `/api/admin/invite`
```sql
create table public.pending_invitations (
  id          uuid primary key default gen_random_uuid(),
  email       citext unique not null,
  role        text not null check (role in ('admin','super','user')),
  invited_by  uuid references auth.users(id),
  status      text not null default 'pending' check (status in ('pending','accepted','expired','revoked')),
  token       text unique,
  created_at  timestamptz not null default now(),
  expires_at  timestamptz default (now() + interval '7 days')
);
```
+ FastAPI route `backend/routers/admin.py`:
```python
@router.post("/invite")
async def invite(req: InviteReq, current = Depends(require_admin)):
    # 1) Use SERVICE_ROLE to call supabase.auth.admin.invite_user_by_email
    # 2) Insert pending_invitations row with token returned
    # 3) Return {ok: true, expires_at}
```

#### 4. `integrations` (สำหรับ IntegrationManageModal)
```sql
create table public.integrations (
  id          uuid primary key default gen_random_uuid(),
  name        text unique not null,           -- e.g. "LINE Notify", "Telegram Bot"
  kind        text not null,                  -- 'notify' | 'storage' | 'ai'
  config      jsonb not null default '{}',    -- token, webhook URL, etc.
  enabled     boolean not null default true,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
alter table public.integrations enable row level security;
-- RLS: admin-only
```

#### 5. `alert_preferences` (ใน app_settings)
ไม่ต้องสร้างตารางใหม่ — frontend upsert ลง `app_settings` ด้วย key `alert_preferences` (มี table อยู่แล้วใน migration 0009)

---

## 🧪 Verification (User ต้องทำ)

1. **Pi5 redeploy**: Portainer → stack `sunday-estate` → **Re-pull image and redeploy** (~2 min)
2. **Hard refresh**: Cmd+Shift+R ที่ `http://umbrel.local:8090`
3. **Test matrix**:

| Test | Expected |
|------|----------|
| Upload ทะเบียนบ้าน (มีหลายผู้อาศัย) → Review page | Field "residents.*" แสดงเป็น input ปกติ ไม่ใช่ JSON block |
| Dashboard admin → "บันทึกใหม่" | Menu เด้ง: "สัญญาใหม่" / "ที่ดินใหม่" → navigate + form เปิด |
| ปล่อยกู้ → ติ๊ก 3 row | Bar "3 รายการที่เลือก" + ปุ่ม Bulk edit/Delete |
| ปล่อยกู้ → header checkbox | Indeterminate (`-`) เมื่อบางส่วน, ✓ ครบเมื่อทั้งหมด |
| Bulk Delete | Confirm → row หาย หลัง reload |
| Bulk Edit → status=ไถ่ถอนแล้ว | Confirm → row ที่เลือกเปลี่ยนสถานะพร้อมกัน |
| Loans Filter dropdown | เลือก type "ขายฝาก" + due "ภายใน 7 วัน" → ตารางกรอง + badge "2" |
| Loans pagination | >20 rows → page 2 + ← → ทำงาน |
| Dashboard CashFlow chips | 6M → กราฟยุบเหลือ 6 bars |
| Calendar Export iCal | Download `.ics` → import Google Calendar เห็น events |
| Calendar Week toggle | Layout เปลี่ยนเป็น 7-day strip |
| Lands รายงาน → CSV | Download `lands-YYYY-MM-DD.csv` |
| Borrower contact officer | Modal มี tel/LINE/email links คลิกได้ |
| Settings เชิญผู้ใช้ | Modal: email + role → submit → alert (จะ persist เมื่อ backend ทำ) |

---

## 📝 Instructions for Next AI Agent

### ถ้าคุณมารับงานต่อจาก session นี้:

1. **Read first**:
   - ไฟล์นี้ (เห็นภาพรวมงานที่ทำไป)
   - [[sunday-estate-webapp]] (synthesis หลัก)
   - `git log --oneline -10` ใน `/Users/aase7en/Desktop/sunday-estate-webapp/` (เห็น commit history)

2. **Confirm with user first**:
   - User redeploy + verify หรือยัง? ถ้ายัง — ขอ feedback ก่อนทำ migration
   - มี bug ใหม่ที่เจอจาก QA หรือไม่?

3. **Next-priority work** (ตามลำดับ):
   1. รอ user feedback จาก verify → ถ้ามี bug ใหม่ใน 14 ปุ่มที่ wire → fix ก่อน
   2. **Migration 0014** (`payment_notifications` + storage bucket `payment-slips`)
   3. **Migration 0015** (`events`)
   4. **Migration 0016** (`pending_invitations` + `integrations`)
   5. FastAPI route `backend/routers/admin.py` (`/api/admin/invite` ใช้ service_role)
   6. (Optional) Cloudflare Tunnel public access — ยังค้างจาก session เก่า

4. **กฎเหล็ก**:
   - **ห้าม push ตรงๆ ไม่ขอผู้ใช้** — push main เท่านั้น ไม่มี branch/PR
   - **ห้ามแตะ** Umbrel/Bitcoin/supabasepi5 stack
   - **Pi5 deploy** ใช้ Portainer (`http://umbrel.local:9000`) stack `sunday-estate` → Re-pull + Redeploy
   - Frontend prototype ใช้ Babel-in-browser — แก้ .jsx แล้ว push commit ได้เลย (image rebuild ใน Docker)
   - Backend ARM64 wheels (`cryptography`, `httpx`) compile ช้า — ใช้ pre-built image จาก ghcr.io/aase7en/sunday-estate-api

5. **Files mental model**:
   ```
   prototype/src/
   ├── app.jsx          ← Top-level routing, App state (page, scope, lang)
   ├── shell.jsx        ← Sidebar + Topbar + nav structure
   ├── dashboard.jsx    ← Drag-drop widgets + Quick-Create menu (T2)
   ├── loans.jsx        ← Loans table + bulk select (T4) + filter/pagination (T3b,c)
   ├── lands.jsx        ← Lands grid/list + Report modal (T3d)
   ├── borrower.jsx     ← Borrower portal (T3e-h modals)
   ├── misc.jsx         ← Calendar + OCR + Alerts + Settings (T1, T3i-q)
   ├── data.jsx         ← window.SE_DATA exports + Supabase calls
   ├── sbclient.jsx     ← window.sb client init
   ├── ui.jsx           ← Reusable: Icon, Tag, Donut, BarsChart
   ├── ai.jsx           ← AIPanel + AIInlinePage
   └── login.jsx        ← LoginPage
   ```

6. **กลไก pendingAction** (T2 → list pages):
   - App.jsx มี `pendingAction` state + `triggerQuickCreate(entity)` ฟังก์ชัน
   - Dashboard accept `onQuickCreate(entity)` prop → call function
   - LoansList/LandsList accept `pendingAction` + `onPendingActionConsumed` props
   - List pages useEffect: ถ้า `pendingAction === "new"` && canWrite → `setFormOpen(true)` + consume
   - Pattern นี้ขยาย "edit:<id>", "scroll-to:<id>" ได้ในอนาคต

---

## 🔗 Related artifacts

- **Plan file (local-only)**: `~/.claude/plans/webapp-snoopy-lobster.md` (เครื่อง Claude นี้เท่านั้น)
- **Webapp commit**: `aase7en/sunday-estate-webapp@1e8147c` (GitHub: https://github.com/aase7en/sunday-estate-webapp)
- **Pi5 stack**: Portainer → `sunday-estate` (nginx :8090 + fastapi :8000 internal)
- **Last working production URL**: `http://umbrel.local:8090`
- **Previous session log**: [[../../log#2026-05-17 sunday-estate-production-verified]]
- **Main synthesis**: [[sunday-estate-webapp]]
