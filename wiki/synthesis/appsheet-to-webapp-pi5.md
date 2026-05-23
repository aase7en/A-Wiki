---
type: synthesis
tags: [web-app, raspberry-pi, self-hosted, appsheet-migration, env, iot, fullstack]
sources: [appsheet-activated-sludge-app, appsheet-epidem-app, appsheet-env-datadict]
created: 2026-04-22
updated: 2026-05-04
progress: Phase 1 RESET — containers wiped by Umbrel update, must redeploy via Portainer
---

# แผน: ย้าย AppSheet → Self-hosted Web App บน Raspberry Pi 5

## คำถามที่ตอบ

"จะสร้าง web application ทดแทน AppSheet (ActivatedSludge + Epidem) บน Pi5 ที่บ้าน ได้อย่างไร?"

## สรุป

AppSheet ช้าเกินไปสำหรับการใช้งานรายวัน + ไม่สามารถ integrate กับ IoT sensors ได้ตรงๆ  
การสร้าง self-hosted web app บน Pi5 ให้: ความเร็ว, IoT integration, ควบคุมข้อมูลเอง, ขยายได้ในอนาคต

---

## ข้อมูล AppSheet ที่มีอยู่

### App 1: ActivatedSludge-29279640 (งาน ENV)
| โมดูล | ตาราง | จำนวนข้อมูล |
|-------|-------|-------------|
| คุณภาพน้ำรายวัน | ข้อมูลบ่อบำบัดประจำวัน | 80+ ฟิลด์ |
| น้ำประปา | tap water, coliform | หลายตาราง |
| ถังดับเพลิง | fire_extinguisher | พร้อม PDF report |
| ไฟฉุกเฉิน | ข้อมูลตรวจไฟฉุกเฉิน | พร้อม PDF report |
| บุคลากร | ข้อมูลผู้ปฏิบัติงาน | รูปถ่าย + ข้อมูล |
| เครื่องมือ | tool_maintainance | - |

### App 2: Epidem-29279640 (งานควบคุมโรค)
| โมดูล | ตาราง | จำนวนข้อมูล |
|-------|-------|-------------|
| ผู้ถูกสัตว์กัด (Rabies PEP) | patient information | 80+ ฟิลด์ |
| SQL backup | sql_export1-4 | สำรองข้อมูล |

### ข้อมูลร่วม (Shared)
- ระบบน้ำประปา, ถังดับเพลิง, บุคลากร — มีอยู่ในทั้งสองแอป

---

## สถาปัตยกรรม Web App ที่แนะนำ

```
┌─────────────────────────────────────────────────────────┐
│                   Raspberry Pi 5 (8/16GB)                │
│                                                          │
│  ┌──────────┐   ┌──────────┐   ┌───────────────────┐   │
│  │  Nginx   │   │ FastAPI  │   │   PostgreSQL       │   │
│  │ (reverse │──▶│ Backend  │──▶│   (main database)  │   │
│  │  proxy)  │   │ :8000    │   │   :5432            │   │
│  └──────────┘   └──────────┘   └───────────────────┘   │
│       │                │                                  │
│  ┌──────────┐   ┌──────────┐   ┌───────────────────┐   │
│  │  React/  │   │Mosquitto │   │   InfluxDB         │   │
│  │  Vite    │   │  MQTT    │   │   (time-series)    │   │
│  │ Frontend │   │ :1883    │   │   IoT sensor data  │   │
│  └──────────┘   └──────────┘   └───────────────────┘   │
│                       │                                   │
└───────────────────────│───────────────────────────────── ┘
                        │ MQTT
              ┌─────────┴─────────┐
              │   ESP32 Sensors   │
              │   (future IoT)    │
              │  DO, pH, TDS,     │
              │  Temp, Chlorine   │
              └───────────────────┘
```

### Tech Stack

| Layer | เทคโนโลยี | เหตุผล |
|-------|-----------|--------|
| **Frontend** | React 18 + Vite + Tailwind CSS | เร็ว, component-based, mobile-friendly |
| **Backend** | FastAPI (Python) | Python ecosystem รองรับ IoT ดี, async |
| **Database** | PostgreSQL | เชื่อถือได้, relational ✔ ทุก module |
| **Time-series** | InfluxDB | เมื่อเพิ่ม IoT sensors จริง |
| **MQTT** | Mosquitto | ส่งข้อมูล sensor → server (ใช้ wiki รู้อยู่แล้ว) |
| **Reverse Proxy** | Nginx | SSL termination, static files |
| **Container** | Docker Compose | จัดการทุก service ง่าย |
| **PDF** | WeasyPrint | สร้าง ทส.1/ทส.2 และรายงานระบาดวิทยา |
| **Auth** | JWT + bcrypt | session-based login |
| **Access** | Tailscale / Cloudflare Tunnel | เข้าจากโรงพยาบาลหรือมือถือได้ |

---

## โมดูลที่ต้องสร้าง (เรียงลำดับความสำคัญ)

### Phase 1 — Core (MVP) ⭐⭐⭐
- [ ] **Auth** — Login, Role (admin/user/viewer)
- [ ] **Water Quality** — บันทึกคุณภาพน้ำรายวัน (แทน module หลักของ ActivatedSludge)
- [ ] **Rabies PEP** — บันทึกผู้ถูกสัตว์กัด, ตารางวัคซีน 5 เข็ม
- [ ] **PDF Generator** — ส่งออก ทส.1/ทส.2, รายงานผู้ป่วย

### Phase 2 — Operations ⭐⭐
- [ ] **Fire Safety** — ตรวจสอบถังดับเพลิง + ไฟฉุกเฉิน
- [ ] **Water Supply** — ระบบน้ำประปา, coliform
- [ ] **Personnel** — ข้อมูลบุคลากร + รูปถ่าย
- [ ] **Equipment** — บันทึกซ่อมบำรุงเครื่องมือ

### Phase 3 — IoT Integration ⭐
- [ ] **ESP32 → MQTT → API** — sensor คุณภาพน้ำ real-time
- [ ] **Dashboard** — Grafana หรือ React charts
- [ ] **Alert** — LINE Notify / Telegram เมื่อค่าผิดปกติ
- [ ] **InfluxDB** — เก็บ time-series sensor data

---

## ข้อมูล Migration

### ข้อมูลเดิมที่ต้อง migrate
1. **Recovery Data** (JSON) → PostgreSQL (script Python)
2. **รูปถ่าย** (~2,900 ไฟล์) → เก็บใน `/data/uploads/` บน Pi5
3. **PDF templates** (DOCX → WeasyPrint template)
4. **Google Sheets** → PostgreSQL import

### การเข้าถึงจากโรงพยาบาล
```
Option A: Tailscale VPN (แนะนำ) — ง่าย, ปลอดภัย, ฟรีสำหรับ personal use
Option B: Cloudflare Tunnel — ไม่ต้อง public IP, ฟรี
Option C: Dynamic DNS + Router port forward — เสี่ยงกว่า
```

---

## เปรียบเทียบ: AppSheet vs Web App ใหม่

| หัวข้อ | AppSheet | Web App (Pi5) |
|--------|---------|---------------|
| ความเร็ว | ช้า | เร็ว (local) |
| ค่าใช้จ่าย | $50/เดือน (Business) | ~0 (Pi5 ซื้อครั้งเดียว) |
| IoT Integration | ไม่มี | MQTT + InfluxDB เลย |
| Custom PDF | จำกัด | เต็มที่ (WeasyPrint) |
| ออฟไลน์ | ไม่ได้ | ได้ (local server) |
| บำรุงรักษา | ไม่ต้องทำ | ต้องดูแลเอง |
| Backup | Google Drive อัตโนมัติ | ต้องตั้ง cron |

---

## สิ่งที่ Wiki รู้อยู่แล้วที่ใช้ได้เลย

- **[[entities/iot/esp32]]** → sensor node สำหรับ DO, pH, TDS
- **[[concepts/iot/mqtt-protocol]]** → ส่งข้อมูล sensor → Pi5
- **[[entities/iot/raspberry-pi]]** → server hardware
- **[[synthesis/pi4-lora-gateway-server]]** → สถาปัตยกรรม Pi server ที่เคยวางไว้
- **[[synthesis/temperature-monitor-project]]** → ตัวอย่าง sensor → dashboard
- **Claude Code** → ใช้ช่วย generate code (ดู `wiki/concepts/ai-tools/openrouter-claude-code.md`)

---

## สถานะปัจจุบัน

### Session 1 (2026-04-22) ✅ — Infrastructure เดิม (ถูกลบแล้ว)
- Infrastructure ผ่าน SSH บน Pi5: PostgreSQL 16, FastAPI :8000, Adminer :8181
- Schema 5 ตาราง: `users`, `water_quality_records`, `patients`, `rabies_cases`, `vaccination_schedule`
- Water Quality API: GET/POST/DELETE + auto-alert DO<2.0 / Cl<0.5
- ⚠️ **Umbrel OS update ล้าง custom Docker containers ทั้งหมด** → ต้อง redeploy ใหม่

### Session 2 (2026-05-04) — Storage cleanup + YAML analysis
- **Pi5 storage**: เดิม 91% (1.6T/1.8T) → ลบ Time Machine 690GB → เหลือ 51% (848GB free)
- **Bitcoin full node**: ยังอยู่ที่ 871GB — ปล่อยไว้ตามแผน
- **Portainer**: เข้าได้ปกติ (admin) — ใช้ deploy stack ใหม่แทน SSH
- **YAML analysis**: วิเคราะห์ AppSheet data dictionary ครบ 81 tables, 1,639 columns, 155 actions
- ⚠️ raw YAML file (`raw/manual-input-appsheet-env-2026-05-04.md`) บันทึกได้แค่ 2 chunks — ยังไม่ครบ

### 📋 ถัดไป (Session 3+)
- [ ] **Redeploy FastAPI + PostgreSQL ผ่าน Portainer** (สร้าง stack ถาวรที่รอดข้าม Umbrel update)
- [ ] ออกแบบ PostgreSQL schema ใหม่ครบทุก domain (เริ่ม wastewater)
- [ ] React frontend (เริ่มหลัง API พร้อม)
- [ ] Feature implementation: OCR, PDF, QR, Telegram

---

## โครงสร้าง AppSheet ENV — 6 Domain Groups (จาก YAML analysis 2026-05-04)

> App ID: ActivatedSludge-29279640 | 81 tables | 1,639 columns | 155 actions | 128 views

### Domain 1: ระบบบำบัดน้ำเสีย (Wastewater Treatment) ⭐ ซับซ้อนที่สุด
| AppSheet Table | คำอธิบาย | Google Sheet |
|---------------|---------|-------------|
| ข้อมูลคุณภาพน้ำ | บันทึกรายวัน: TDS, pH, DO-1/2/3, SV30, Free Chlorine, meter readings, energy calc | ข้อมูลน้ำประจำวัน |
| Filter_Water | สร้าง PDF report สรุปคุณภาพน้ำ | ข้อมูลน้ำประจำวัน |
| last meter | ค่ามิเตอร์ล่าสุด (คำนวณพลังงาน) | ข้อมูลน้ำประจำวัน |

### Domain 2: ระบบประปา (Water Supply)
| AppSheet Table | คำอธิบาย | Google Sheet |
|---------------|---------|-------------|
| น้ำประปา | บันทึกคุณภาพน้ำประปา | ข้อมูลคุณภาพน้ำประปา |
| tap water_Filter | PDF report น้ำประปา | ข้อมูลคุณภาพน้ำประปา |
| Menu ประปา | เมนูนำทาง (virtual) | — |

### Domain 3: สุขาภิบาลอาหาร (Food Sanitation)
| AppSheet Table | คำอธิบาย | Google Sheet |
|---------------|---------|-------------|
| coliform bac. | ผลตรวจโคลิฟอร์มน้ำ | สุขาภิบาลอาหารและน้ำ2 |
| coliform bac._Water | โคลิฟอร์มน้ำดื่ม | สุขาภิบาลอาหารและน้ำ2 |
| coliform bac. Food. | โคลิฟอร์มอาหาร | สุขาภิบาลอาหารและน้ำ2 |
| coliform bac. Employee | โคลิฟอร์มผู้สัมผัสอาหาร | สุขาภิบาลอาหารและน้ำ2 |

### Domain 4: ความปลอดภัย (Safety)
| AppSheet Table | คำอธิบาย | Google Sheet |
|---------------|---------|-------------|
| Emergency light | รายการไฟฉุกเฉิน | Items |
| Check | ตรวจสอบไฟฉุกเฉิน (scan QR) | Items |
| ถังดับเพลิง | รายการถังดับเพลิง | fire_extinguisher |
| ตรวจสอบถัง | ตรวจสอบถังดับเพลิง (scan QR) | fire_extinguisher |
| Filter_Firer | PDF report ถังดับเพลิง | fire_extinguisher |
| Filter_Light | PDF report ไฟฉุกเฉิน | Items |

### Domain 5: ระบาดวิทยา (Epidemiology / Rabies PEP)
| AppSheet Table | คำอธิบาย | Google Sheet |
|---------------|---------|-------------|
| patient information | ผู้ถูกสัตว์กัด: HN, ชื่อ-ที่อยู่-อายุ, วัคซีน 5 เข็ม | Patients / ข้อมูลหมากัด |
| แบบสอบสวนโรค | รายงานระบาดวิทยา | ข้อมูลหมากัด |
| sql_export 1–5 | lookup คนไข้จาก HN (OCR input) → ชื่อ/ที่อยู่/อายุ | (read-only mirror) |

### Domain 6: Admin / Shared
| AppSheet Table | คำอธิบาย | Google Sheet |
|---------------|---------|-------------|
| address | auto-complete ที่อยู่ (TambonID → อำเภอ/จังหวัด/รหัสไปรษณีย์) | — |
| ข้อมูลผู้ปฏิบัติงาน | บุคลากร + รูปถ่าย | ข้อมูลน้ำประจำวัน |
| location_area | จุดตรวจ QR สำหรับ job check-in | งานสวน |
| job | GPS geolocation check-in (คำนวณระยะห่างจากโรงพยาบาล) | งานสวน |

---

## Feature-to-Implementation Mapping

| AppSheet Feature | Implementation ใน Web App |
|-----------------|--------------------------|
| Virtual columns + สูตรคำนวณ (DO avg, energy, SV30%) | PostgreSQL computed columns + Python ใน FastAPI |
| Auto-complete ที่อยู่ (address table) | Import address table → PostgreSQL → API endpoint |
| OCR HN → ดึงข้อมูลคนไข้ (sql_export) | Claude API (vision) → extract HN → query patient table |
| PDF report (Filter_Water, Filter_Firer, Filter_Light) | WeasyPrint templates (HTML/CSS → PDF) |
| Telegram notification + PDF attach | python-telegram-bot → ส่งหลัง POST สำเร็จ |
| QR scan (ถังดับเพลิง, ไฟฉุกเฉิน, job) | React QR reader library → lookup location_area / equipment |
| GPS check-in (job) | Browser Geolocation API → FastAPI distance calc (Haversine) |
| Thai Buddhist date (พ.ศ.) | Python: `year + 543` conversion ใน API response |
| Enum dropdowns | PostgreSQL ENUM types หรือ lookup tables |

---

## ข้อมูล Infrastructure สำคัญ

```
Pi5 Home Server:
  OS: Umbrel (rugpi — system partition ไม่ persistent ข้าม update!)
  ⚠️ Deploy ผ่าน Portainer Stack เท่านั้น (ไม่ใช่ SSH manual) เพื่อให้รอดข้าม update

Target Ports:
  :8000  FastAPI backend
  :5432  PostgreSQL
  :8181  Adminer (DB UI)
  :9000  Portainer

Access:
  Local:     umbrel.local / 192.168.1.165
  Tailscale: 100.x.y.z

DB credentials (เดิม — ยังไม่ deploy ใหม่):
  user: webapp / pass: webapp1234 / db: webapp
```

## แผนการทำงาน (ปรับปรุง)

```
Session 1 (2026-04-22): Infrastructure SSH + DB schema + Water Quality API ✅ (ถูกลบแล้ว)
Session 2 (2026-05-04): Storage cleanup + AppSheet YAML analysis ✅
Session 3: Redeploy ผ่าน Portainer + ออกแบบ schema ครบทุก domain
Session 4: Water Quality + Rabies PEP API endpoints
Session 5: Auth (JWT login)
Session 6: React frontend (mobile-first)
Session 7: PDF generation (WeasyPrint)
Session 8: Feature: OCR, QR, GPS, Telegram
Session 9: Data migration จาก AppSheet JSON/Google Sheets
Session 10+: IoT sensor integration
```

## แหล่งข้อมูลที่ใช้

- [[entities/env/activated-sludge-system]] — schema ระบบบำบัดน้ำเสีย
- [[entities/env/rabies-pep-surveillance]] — schema ระบาดวิทยา
- AppSheet ActivatedSludge-29279640 — โครงสร้างข้อมูลเดิม
- AppSheet Epidem-29279640 — โครงสร้างข้อมูลเดิม
