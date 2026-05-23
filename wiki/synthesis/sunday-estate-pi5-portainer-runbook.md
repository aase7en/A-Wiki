---
title: Sunday Estate Pi5 Portainer Runbook
type: synthesis
domain: cross-domain
related:
  - sunday-estate-webapp
  - iot
  - ai-tools
status: active-runbook
created: 2026-05-18
updated: 2026-05-18
sources:
  - wiki/synthesis/sunday-estate-webapp.md
  - wiki/synthesis/sunday-estate-frontend-qa-2026-05-18.md
  - wiki/context/session-memory.md
---

# Sunday Estate Pi5 Portainer Runbook

## คำถามที่ตอบ

จะ redeploy / verify / debug stack `sunday-estate` บน Pi5 ผ่าน Portainer อย่างไร โดยไม่แตะ Umbrel, Bitcoin node, หรือ Supabase stack ที่ไม่เกี่ยวข้อง

## สรุปเร็ว

| Priority | งาน | ทำที่ไหน | สถานะที่ต้องได้ |
|---|---|---|---|
| P0 | Verify backend health | Mac หรือ Pi5 terminal | `/api/health` ตอบ `{"status":"ok","service":"sunday-estate-api"}` |
| P0 | Verify admin routes are deployed | Mac หรือ Pi5 terminal | `/api/admin/invitations` ตอบ `401 Missing bearer token` เมื่อยังไม่ login |
| P1 | Portainer redeploy stack | Portainer UI | stack `sunday-estate` ขึ้น running/healthy |
| P1 | Verify env/service role | Portainer UI stack env | backend มี `SUPABASE_SERVICE_KEY` หรือ service_role key ที่ถูกต้อง |
| P2 | Manual UI QA | Browser logged-in admin | 14 ปุ่ม + OCR PDF editable fields ผ่าน |
| P3 | Cloudflare Tunnel | Pi5/Portainer + Cloudflare account | public hostname ชี้เข้า nginx เท่านั้น |

> ห้ามใส่ `service_role` หรือ secret key ใด ๆ ใน `prototype/config.js` เพราะ browser code ต้องมีแค่ anon key

---

## 1. Preflight จาก Mac

ใช้ตรวจจากเครื่อง Mac ก่อนเข้า Portainer:

```bash
curl -sS http://umbrel.local:8090/api/health
```

Expected:

```json
{"status":"ok","service":"sunday-estate-api"}
```

ตรวจว่า admin route deploy แล้ว:

```bash
curl -i -sS http://umbrel.local:8090/api/admin/invitations | sed -n '1,20p'
```

Expected แบบยังไม่ login:

```text
HTTP/1.1 401 Unauthorized
{"detail":"Missing bearer token"}
```

ถ้าได้ `404 Not Found` แปลว่า backend ยังไม่ได้โหลด route ใหม่ หรือ stack ยังไม่ redeploy เป็น version ล่าสุด

---

## 2. Portainer Redeploy Checklist

ทำใน Portainer UI:

1. เปิด `http://umbrel.local:9000`
2. เข้า **Stacks**
3. เลือก stack `sunday-estate`
4. กด **Pull and redeploy** หรือ **Update the stack**
5. เปิด option ประมาณ **Re-pull image and redeploy** ถ้ามี
6. รอจน containers กลับมา running/healthy
7. กลับมารัน health check:

```bash
curl -sS http://umbrel.local:8090/api/health
```

Expected:

```json
{"status":"ok","service":"sunday-estate-api"}
```

ถ้า Portainer แจ้ง `se-fastapi is unhealthy` ให้ไปดูข้อ 4

---

## 3. Environment Variables ที่ต้องตรวจ

ตรวจใน Portainer stack `sunday-estate` เท่านั้น ห้ามแก้ stack Umbrel/Bitcoin/supabasepi5

| Variable | ใช้ที่ไหน | ต้องเป็นอะไร |
|---|---|---|
| `SUPABASE_URL` | FastAPI backend | URL Supabase/Kong ของ Pi5 |
| `SUPABASE_ANON_KEY` | frontend/backend | anon JWT เท่านั้น |
| `SUPABASE_SERVICE_KEY` | FastAPI backend เท่านั้น | service_role key สำหรับ admin ops |
| `OPENROUTER_API_KEY` | FastAPI backend | ใช้ AI chat/OCR/model sync |
| `NGINX_PORT` | docker compose/nginx | ปัจจุบันควรเป็น `8090` |

ตรวจใน browser-facing config:

```bash
curl -sS http://umbrel.local:8090/config.js
```

ต้องเห็น `DEMO_MODE: false` และต้องไม่เห็น `SUPABASE_SERVICE_KEY`

---

## 4. ถ้า FastAPI Unhealthy

จากประวัติล่าสุด root cause เคยเป็น `email-validator` ขาดใน `backend/requirements.txt`

ถ้าเข้าถึง Pi5 terminal ได้ ให้ตรวจ path Portainer-managed compose snapshot:

```bash
sudo grep -n "email-validator" \
  /home/umbrel/umbrel/app-data/portainer/data/portainer/compose/29/backend/requirements.txt
```

ถ้าไม่เจอ ให้เพิ่มชั่วคราว:

```bash
echo "email-validator>=2.0.0" | sudo tee -a \
  /home/umbrel/umbrel/app-data/portainer/data/portainer/compose/29/backend/requirements.txt
```

แล้วกลับไป Portainer:

1. stack `sunday-estate`
2. **Update the stack**
3. เปิด **Re-pull image and redeploy**
4. รอ container healthy
5. verify:

```bash
curl -sS http://umbrel.local:8090/api/health
```

หมายเหตุ: Sunday Estate stack รันผ่าน Docker-in-Docker ของ Portainer; `sudo docker ps` บน host อาจไม่เห็น `se-fastapi` โดยตรง ให้ดู logs ผ่าน Portainer UI เป็นหลัก

---

## 5. Manual UI QA หลัง Redeploy

เปิด browser:

```text
http://umbrel.local:8090
```

ทำ `Cmd+Shift+R` เพื่อ hard refresh แล้ว login admin

| Test | Expected |
|---|---|
| Dashboard > "บันทึกใหม่" | menu เด้ง: สัญญาใหม่ / ที่ดินใหม่ |
| เลือก "สัญญาใหม่" | ไปหน้า loans และ form เปิดเอง |
| เลือก "ที่ดินใหม่" | ไปหน้า lands และ form เปิดเอง |
| Loans > checkbox header | select all / indeterminate ทำงาน |
| Loans > เลือกหลาย row | bulk action bar โผล่ |
| Bulk edit | update field หลายรายการได้ |
| Bulk delete | confirm แล้ว row หาย |
| Loans filter | type/due filter ทำงานและ badge เปลี่ยน |
| Pagination | เปลี่ยนหน้าได้เมื่อรายการเกิน page size |
| Calendar month/week/agenda | layout เปลี่ยนตามปุ่ม |
| Export iCal | download `.ics` |
| Lands report CSV | download CSV |
| Borrower contact officer | tel/LINE/email link เปิดได้ |
| Settings > invite user | modal submit ได้; verify backend end-to-end |
| OCR PDF | output แปลงเป็น editable fields ไม่ใช่ raw JSON block |

ถ้า OCR ยังเห็น raw JSON ใน field array เช่น `residents` ให้ hard refresh อีกครั้ง และตรวจว่า `src/misc.jsx` บน Pi5 มี `_flattenOcrRows` แบบ recurse array-of-objects

---

## 6. Admin Invite End-to-End

ตรวจ route แบบไม่ login ก่อน:

```bash
curl -i -sS http://umbrel.local:8090/api/admin/invitations | sed -n '1,20p'
```

Expected:

```text
HTTP/1.1 401 Unauthorized
{"detail":"Missing bearer token"}
```

จาก UI:

1. login ด้วย admin
2. Settings
3. Team / เชิญผู้ใช้
4. ใส่ email test ที่ควบคุมได้
5. เลือก role
6. Submit

Expected:

| ผล | ความหมาย |
|---|---|
| เชิญสำเร็จ / pending row ถูกสร้าง | backend service role ใช้งานได้ |
| SMTP warning แต่มี pending invitation | database fallback ทำงาน; SMTP ยังไม่ตั้ง |
| 401/403 | token/role admin ไม่ถูก หรือ session หมด |
| 500 service key/config | ตรวจ `SUPABASE_SERVICE_KEY` ใน Portainer env |

---

## 7. Cloudflare Tunnel Checklist

งานนี้ต้องมี Cloudflare credential และทำบน Pi5/Portainer environment ไม่ใช่ Mac เครื่องนี้

Preflight บน Pi5:

```bash
cloudflared --version
```

ถ้ายังไม่มี:

```bash
# เลือกวิธีติดตั้งตาม OS/Pi image ที่ใช้อยู่
# หลังติดตั้งแล้ว login ด้วย Cloudflare account
cloudflared tunnel login
```

สร้าง tunnel:

```bash
cloudflared tunnel create sunday-estate
cloudflared tunnel list
```

ผูก DNS/hostname:

```bash
cloudflared tunnel route dns sunday-estate <your-domain-or-subdomain>
```

ตั้ง config ให้ public service วิ่งเข้า nginx เท่านั้น:

```yaml
tunnel: sunday-estate
credentials-file: /etc/cloudflared/<tunnel-id>.json

ingress:
  - hostname: <your-domain-or-subdomain>
    service: http://nginx:80
  - service: http_status:404
```

ขึ้น service ผ่าน compose profile:

```bash
docker compose --profile public up -d cloudflared
```

Verify:

```bash
curl -I https://<your-domain-or-subdomain>
```

Security rule:

| ต้อง public | ต้อง LAN-only |
|---|---|
| Sunday Estate nginx/webapp | Supabase Studio `:8000` |
| `/api/*` ผ่าน nginx proxy | Portainer `:9000` |
| static frontend | Postgres/pooler ports |
| | Bitcoin/Umbrel ports |

---

## 8. ถ้าต้องส่งต่อให้ AI Agent ตัวถัดไป

บอก agent ว่า:

```text
Read [[sunday-estate-pi5-portainer-runbook]], [[sunday-estate-webapp]], and [[sunday-estate-frontend-qa-2026-05-18]].
Do not touch Umbrel/Bitcoin/supabasepi5 stack.
Only verify or update stack sunday-estate via Portainer.
Current open tasks: Cloudflare Tunnel, manual UI/OCR QA, admin invite end-to-end.
```

## แหล่งข้อมูลที่ใช้

- [[sunday-estate-webapp]]
- [[sunday-estate-frontend-qa-2026-05-18]]
- [[../context/session-memory]]
