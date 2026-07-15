---
type: synthesis
tags: [web-app, postgresql, schema, wastewater, env, fastapi, migration, deprecated-design]
sources: [appsheet-env-datadict]
created: 2026-05-04
updated: 2026-07-16
status: legacy-design — schema จริงย้ายไป Supabase ENV_DB, ดูด้านล่าง
---

# PostgreSQL Schema: ระบบบำบัดน้ำเสีย (Wastewater Domain)

> ⚠️ **DEPRECATED สำหรับ schema จริง** (2026-07-16) — เอกสารนี้เป็นดีไซน์ยุคแรก
> (Pi5 self-host era) ที่ออกแบบตาราง `treatment_ponds`/`staff`/
> `water_quality_records` ฯลฯ สำหรับ Docker-on-Pi5 stack แผนนั้นถูกยกเลิก
> (Pi5 ทำงานหนักอยู่แล้ว) แล้วย้ายไป Supabase free tier แทน (ADR-0003)
>
> **Schema จริงใน ENV_DB คือ source of truth** — ดู:
> - `wiki/entities/env/env-webapp-project.md` §Schema source-of-truth
> - `reports/schema-snapshot-p5.md` ใน sibling repo (verified reconciliation)
> - `app/models/` ใน sibling repo (11 ORM models)
>
> **ส่วนที่ยังใช้ได้** (verified P5b.2-local): §Computed Values สูตร,
> §Alert Logic thresholds, แนวคิด "computed ใน Pydantic ไม่เก็บ DB".
> อ่านส่วนอื่นในฐานะ reference ประวัติศาสตร์เท่านั้น.

## คำถามที่ตอบ

"ออกแบบ database schema สำหรับแทน AppSheet ข้อมูลคุณภาพน้ำ โดยให้รองรับ: บันทึกรายวัน, สูตรคำนวณ, PDF report, IoT sensor ในอนาคต"

## สรุป

AppSheet table `ข้อมูลคุณภาพน้ำ` เดิมมี virtual columns และ computed fields จำนวนมาก ใน PostgreSQL แยกออกเป็น:
- **ตารางหลัก** เก็บค่าที่วัดได้จริง (raw measurements)
- **Computed values** คำนวณใน FastAPI (ไม่เก็บซ้ำ เพื่อ single source of truth)
- **ตาราง reference** สำหรับ meter, บุคลากร, บ่อบำบัด

---

## Schema SQL

```sql
-- =============================================
-- DOMAIN: Wastewater Treatment
-- AppSheet source: ข้อมูลน้ำประจำวัน → ข้อมูลคุณภาพน้ำ
-- =============================================

-- บ่อบำบัด (Aeration Pond / Treatment Unit)
CREATE TABLE treatment_ponds (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20) UNIQUE NOT NULL,  -- เช่น 'POND-1', 'AERATOR-A'
    name        VARCHAR(100) NOT NULL,         -- ชื่อบ่อ/จุดวัด
    type        VARCHAR(50),                   -- 'aeration', 'settling', 'chlorination'
    is_active   BOOLEAN DEFAULT TRUE
);

-- บุคลากร (ใช้ร่วมกับทุก domain)
CREATE TABLE staff (
    id          SERIAL PRIMARY KEY,
    employee_id VARCHAR(20) UNIQUE NOT NULL,   -- AppSheet: Employee_id
    full_name   VARCHAR(100) NOT NULL,
    nickname    VARCHAR(50),
    position    VARCHAR(50),                   -- Enum: นักวิชาการ/เจ้าหน้าที่/etc
    phone       VARCHAR(20),
    photo_url   VARCHAR(500),
    status      VARCHAR(20) DEFAULT 'active'   -- Enum: active/inactive
);

-- ค่ามิเตอร์ล่าสุด (AppSheet: last meter)
CREATE TABLE meter_readings (
    id              SERIAL PRIMARY KEY,
    reading_date    DATE NOT NULL,
    meter_kwh       NUMERIC(10,2),             -- ค่ามิเตอร์ไฟฟ้า (kWh)
    recorded_by     INTEGER REFERENCES staff(id),
    note            TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- บันทึกคุณภาพน้ำรายวัน (AppSheet: ข้อมูลคุณภาพน้ำ)
-- เก็บเฉพาะค่าที่วัดได้จริง — computed values คำนวณใน API
CREATE TABLE water_quality_records (
    id              SERIAL PRIMARY KEY,
    record_date     DATE NOT NULL,

    -- DO (Dissolved Oxygen) — 3 จุดวัด
    do_inlet        NUMERIC(5,2),              -- DO บ่อรับน้ำ (mg/L)
    do_aeration_1   NUMERIC(5,2),              -- DO บ่อเติมอากาศ 1
    do_aeration_2   NUMERIC(5,2),              -- DO บ่อเติมอากาศ 2

    -- ค่าเคมีน้ำ
    ph              NUMERIC(4,2),              -- pH (0-14)
    tds             NUMERIC(8,2),              -- Total Dissolved Solids (mg/L)
    free_chlorine   NUMERIC(5,2),              -- Free Chlorine (mg/L)

    -- Sludge Volume (SV30)
    sv30_ml         NUMERIC(6,1),              -- ปริมาณตะกอน 30 นาที (mL/L)

    -- การใช้พลังงาน
    meter_start_kwh NUMERIC(10,2),             -- ค่ามิเตอร์ต้นรอบ
    meter_end_kwh   NUMERIC(10,2),             -- ค่ามิเตอร์สิ้นรอบ
    -- energy_kwh ← COMPUTED: meter_end - meter_start (ใน API)

    -- ปริมาณน้ำ
    flow_rate_m3    NUMERIC(10,2),             -- ปริมาณน้ำเข้า (m3/วัน)

    -- Metadata
    recorded_by     INTEGER REFERENCES staff(id),
    pond_id         INTEGER REFERENCES treatment_ponds(id),
    note            TEXT,
    photo_url       VARCHAR(500),              -- รูปบ่อ/หน้างาน
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),

    -- Unique constraint: 1 record ต่อวัน ต่อบ่อ
    UNIQUE (record_date, pond_id)
);

-- Index สำหรับ query ช่วงวันที่
CREATE INDEX idx_wqr_date ON water_quality_records(record_date DESC);
CREATE INDEX idx_wqr_pond ON water_quality_records(pond_id);

-- PDF Report log (AppSheet: Filter_Water)
CREATE TABLE water_quality_reports (
    id              SERIAL PRIMARY KEY,
    report_month    DATE NOT NULL,             -- เดือน/ปี ของ report
    pdf_url         VARCHAR(500),              -- path ของ PDF ที่ generate แล้ว
    generated_by    INTEGER REFERENCES staff(id),
    generated_at    TIMESTAMP DEFAULT NOW(),
    sent_to_telegram BOOLEAN DEFAULT FALSE
);
```

---

## Computed Values (คำนวณใน FastAPI — ไม่เก็บใน DB)

| Computed Field | สูตร | หน่วย |
|---------------|------|-------|
| `do_average` | `(do_inlet + do_aeration_1 + do_aeration_2) / 3` | mg/L |
| `energy_kwh` | `meter_end_kwh - meter_start_kwh` | kWh |
| `sv30_percent` | `sv30_ml / 1000 * 100` | % |
| `energy_per_m3` | `energy_kwh / flow_rate_m3` | kWh/m3 |
| `date_thai_be` | `record_date.year + 543` | พ.ศ. |

```python
# FastAPI Pydantic Response Model
class WaterQualityResponse(BaseModel):
    # ... raw fields ...
    do_average: float | None = None
    energy_kwh: float | None = None
    sv30_percent: float | None = None
    energy_per_m3: float | None = None
    date_thai_be: int

    @model_validator(mode='after')
    def compute_fields(self):
        if all(v is not None for v in [self.do_inlet, self.do_aeration_1, self.do_aeration_2]):
            self.do_average = round((self.do_inlet + self.do_aeration_1 + self.do_aeration_2) / 3, 2)
        if self.meter_end_kwh and self.meter_start_kwh:
            self.energy_kwh = round(self.meter_end_kwh - self.meter_start_kwh, 2)
        if self.sv30_ml:
            self.sv30_percent = round(self.sv30_ml / 10, 1)
        if self.energy_kwh and self.flow_rate_m3:
            self.energy_per_m3 = round(self.energy_kwh / self.flow_rate_m3, 3)
        if self.record_date:
            self.date_thai_be = self.record_date.year + 543
        return self
```

---

## Alert Logic (AppSheet เดิม: เตือนค่าผิดปกติ)

```python
# ใน POST /water-quality/ endpoint
ALERT_THRESHOLDS = {
    "do_average": {"min": 2.0, "message": "⚠️ DO ต่ำกว่า 2.0 mg/L"},
    "free_chlorine": {"min": 0.5, "message": "⚠️ Chlorine ต่ำกว่า 0.5 mg/L"},
    "ph": {"min": 6.5, "max": 8.5, "message": "⚠️ pH ออกนอกช่วง 6.5-8.5"},
}

async def check_and_alert(record: WaterQualityResponse, telegram_bot):
    alerts = []
    for field, threshold in ALERT_THRESHOLDS.items():
        value = getattr(record, field)
        if value is None:
            continue
        if "min" in threshold and value < threshold["min"]:
            alerts.append(threshold["message"] + f" (ค่าที่วัด: {value})")
        if "max" in threshold and value > threshold["max"]:
            alerts.append(threshold["message"] + f" (ค่าที่วัด: {value})")
    if alerts:
        await telegram_bot.send_message("\n".join(alerts))
```

---

## API Endpoints Plan

```
GET    /api/water-quality/              list (filter: date range, pond)
GET    /api/water-quality/{id}          detail
POST   /api/water-quality/              create (trigger alerts)
PUT    /api/water-quality/{id}          update
DELETE /api/water-quality/{id}          delete (admin only)

GET    /api/water-quality/report/monthly?month=YYYY-MM    monthly summary + PDF
POST   /api/water-quality/report/generate                 generate PDF + Telegram

GET    /api/staff/                      list (shared across domains)
GET    /api/treatment-ponds/            list
```

---

## ลำดับการ Implement

1. **สร้าง Docker stack บน Portainer** (PostgreSQL + FastAPI + Adminer)
2. **Run migration SQL** ด้านบนสร้างตาราง
3. **FastAPI models.py** — SQLAlchemy models + Pydantic schemas
4. **CRUD endpoints** — water_quality_records
5. **Computed fields** — ใน Pydantic response model
6. **Alert logic** — Telegram bot integration
7. **PDF generation** — WeasyPrint monthly report
8. **Frontend** — React form + chart (Recharts)

---

## ความสัมพันธ์

- [[synthesis/appsheet-to-webapp-pi5]] — แผน migration ครบทุก domain
- [[sources/appsheet-env-datadict]] — โครงสร้าง AppSheet ต้นทาง
- [[entities/env/activated-sludge-system]] — ระบบบำบัดน้ำเสียโรงพยาบาล
- [[sources/umbrel-pi5-setup]] — infrastructure Pi5
