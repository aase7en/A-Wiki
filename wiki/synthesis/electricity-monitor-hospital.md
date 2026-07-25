---
type: synthesis
tags: [energy, sct-013, esp32, supabase, ingest-sensor, carbon-footprint, hospital, non-invasive]
sources: [energy-power-monitoring, pzem-004t-guide-2025]
created: 2026-07-24
updated: 2026-07-24
---

# ระบบมอนิเตอร์ไฟฟ้าแอร์ใน <HOSPITAL> → env-wastewater-webapp

> **คำถามที่ตอบ**: จะบันทึกการใช้ไฟฟ้าแอร์ทุกตัวใน <HOSPITAL> แบบ realtime + ส่งเข้า web app + คำนวณ carbon footprint ได้อย่างไร โดยมีข้อจำกัด non-invasive + < 1,000 บาท/หน่วย + มี WiFi?

## สรุป

ใช้ **[[entities/iot/sct-013]] (non-invasive CT clamp)** + **[[entities/iot/esp32]]** วัดกระแสแต่ละแอร์ → ESP32 คำนวณ kWh สะสม → POST ผ่าน thin proxy → **env-wastewater-webapp `ingest-sensor` Edge Function** (มีอยู่แล้ว) → frontend Realtime → ต่อยอดเป็น carbon footprint ผ่าน `EMISSION_FACTOR_KGCO2E_PER_KWH` ที่มีอยู่แล้ว

> เลือก SCT-013 + ESP32 แทน PZEM-004T เพราะ PZEM เป็น invasive (ต้องดับไฟต่อ series สาย live) → เสี่ยงใน <HOSPITAL> production. ดู [[synthesis/energy-power-monitoring]] สำหรับ PZEM version ที่เหมาะกับบ้าน/โรงงานเล็กที่ดับไฟได้

## Data Flow

```
[แอร์ <HOSPITAL> ห้อง X]                   [แอร์ ห้อง Y]   ...   [แอร์ ห้อง N]
        │ (สาย live เดียว ไม่ตัด)                │                   │
        ▼                                       ▼                   ▼
  ┌──────────────┐                        ┌──────────────┐    ┌──────────────┐
  │ SCT-013 +    │                        │ SCT-013 +    │    │ SCT-013 +    │
  │ ESP32        │                        │ ESP32        │    │ ESP32        │
  │ P=V·I·PF,∫Wh│                        │              │    │              │
  └──────┬───────┘                        └──────┬───────┘    └──────┬───────┘
         │ HTTPS POST (batch 5 min, JSON)        │                   │
         ▼                                       ▼                   ▼
         └────────────────┬──────────────────────┘                   │
                          ▼                                          │
                 ┌────────────────────────┐                          │
                 │ Thin proxy (Cloudflare │ ◄────── same endpoint ◄──┘
                 │ Worker / Supabase EF)  │   (proxy injects
                 │ + service_role key     │    service_role bearer)
                 └────────────┬───────────┘
                              │ POST https://<project>.functions.supabase.co/ingest-sensor
                              ▼
                 ┌────────────────────────────────────┐
                 │ ingest-sensor EF (existing, untouched)│
                 │ → wastewater.sensor_reading INSERT  │
                 └────────────┬───────────────────────┘
                              │ Realtime INSERT event
                              ▼
                 use-sensor-feed.ts hook → /sensors page (P20d.2, TBD)
                              │
                              ▼
                 Monthly kWh × EMISSION_FACTOR_KGCO2E_PER_KWH (0.4999)
                 = tCO₂e per AC unit per month
```

## BOM ต่อหน่วยวัด (1 แอร์)

| Component | ราคา (บาท) | ที่มา / Confidence |
|-----------|-----------|-----|
| [[entities/iot/esp32]] DevKit V1 | 0 (มีใน Lab ×1) / ~350–450 ⚠️ VERIFY (สั่งเพิ่ม) | wiki esp32.md |
| [[entities/iot/sct-013]]-000 | ~200 ⚠️ VERIFY | ต้อง scout จริงตอนสั่ง |
| 2× 10kΩ resistor + 10Ω burden + cap | ~10 | — |
| กล่อง + สาย + USB power adapter | ~100 | — |
| **รวมต่อหน่วย** | **~650–750 บาท** ✅ < 1,000 | |

## เปรียบเทียบ MCU (ตัดสินใจใน ADR)

| MCU | ราคา (บาท) | WiFi built-in | TLS to Supabase | Firmware ชุดเดียว? | เหมาะกับงานนี้? |
|---|---|---|---|---|---|
| [[entities/iot/arduino-uno-r3]] clone | 270 (verify) | ❌ (ต้อง +ESP-01 = 65) | ⚠️ ESP-01 ทำ TLS ยาก | ❌ (ต้องเขียน 2 ชุด) | ❌ |
| [[entities/iot/esp32]] DevKit V1 | 0 (Lab) / ~350–450 (verify) | ✅ | ✅ native | ✅ | ✅ ⭐ **เลือก** |
| ESP8266 NodeMCU v3 | 180 (verify) | ✅ | ⚠️ flash จำกัด | ✅ | ⚠️ (ต้องซื้อใหม่, TLS ลำบาก) |

→ รายละเอียดเหตุผล 4 ข้อ ใน ADR-0011 ของ env-wastewater-webapp

## Payload JSON (เข้า ingest-sensor contract เดิม ไม่ต้องแก้ EF)

ESP32 batch ทุก 5 นาที:
```json
[
  {
    "sensor_code": "PWR-AC-<ROOM>-01",
    "taken_at": "2026-07-24T10:05:00Z",
    "value": 1.234,
    "raw": { "v_assumed": 220, "i_rms": 5.6, "pf": 0.85, "w_inst": 1047, "uptime_s": 300 }
  }
]
```

- `value` = kWh **สะสม** ตั้งแต่เริ่มวัน → frontend ทำ delta = kWh ในช่วงเวลา
- `sensor_code` = `PWR-AC-<ROOM>-NN` (placeholder, Iron Law #6 — ห้ามชื่อห้องจริง)
- `parameter_code='kwh'`, `unit='kWh'` ใน `wastewater.sensor` master table

## การคำนวณ carbon footprint (ต่อยอด layer ที่มี)

```ts
// frontend/src/lib/carbon.ts (existing constant — reused, not duplicated)
const EMISSION_FACTOR_KGCO2E_PER_KWH = 0.4999;  // TGO Thailand grid 2023

// monthly aggregate per AC unit:
//   kWh_month = sum of delta(value) over month
//   tCO2e_month = kWh_month × 0.4999 / 1000
```

## ข้อดีของ approach นี้

1. **Non-invasive 100%** — ไม่ตัดสาย ไม่ดับไฟ เหมาะติดตั้งจริงใน <HOSPITAL> ที่กำลังทำงาน
2. **BOM < 1,000 บาท/หน่วย** — ขยายได้ทุกแอร์
3. **ใช้ ingest-sensor EF เดิม** — ไม่ต้องเขียน backend ใหม่
4. **ต่อยอด carbon layer เดิม** — ใช้ emission factor ที่ seed ไว้แล้วใน DB
5. **Realtime** — ผ่าน Supabase Realtime publication ที่ migration P20d ต่อไว้แล้ว

## ข้อจำกัด / ข้อควรระวัง

1. **PF เป็นค่าประมาณ** → ความคลาดเคลื่อน kWh ราว ±10–15% vs มิเตอร์จริง. ถ้าต้องการแม่นยำกว่านี้ ต้องเปลี่ยนเป็น PZEM-004T (invasive) หรือแยกตัววัด PF
2. **WiFi coverage** — ESP32 ต้องถึง WiFi ของ <HOSPITAL>. ถ้าห้องไหนสัญญาณไม่ถึง ต้องพิจารณา LoRa (ดู [[synthesis/iot-lora-architecture]]) หรือ WiFi extender
3. **service_role key ต้องไม่อยู่ใน firmware** — บังคับผ่าน proxy (NFR3)
4. **ต้อง calibration ตอนติดตั้ง** — เทียบค่ากระแสที่อ่านได้กับ clamp meter อิสระก่อนใช้งานจริง

## Roadmap

| Phase | Scope | เป้า |
|---|---|---|
| P0 | Prototype ESP32 + SCT-013 บนโต๊ะ (calibrate กับ hair dryer / heater) | ความแม่นยำ ±10% |
| P1 | ติดตั้งจริง 1 แอร์ที่ <HOSPITAL> 7 วัน เทียบ kWh มิเตอร์ | AC1 |
| P2 | ขยายทุกแอร์ + หน้า /sensors UI (P20d.2) | FR3 |
| P3 | Dashboard peak/downtime/รายเดือน + carbon | FR4, FR5 |

## ความสัมพันธ์

- Variant ของ: [[synthesis/energy-power-monitoring]] (PZEM-based — สำหรับที่ดับไฟได้)
- ใช้ฮาร์ดแวร์: [[entities/iot/esp32]], [[entities/iot/sct-013]]
- ส่งข้อมูลเข้า: env-wastewater-webapp `ingest-sensor` EF + `wastewater.sensor_reading`
- ต่อยอด carbon: `EMISSION_FACTOR_KGCO2E_PER_KWH` ใน `frontend/src/lib/carbon.ts`
- Pattern: [[concepts/iot/data-logger]], [[concepts/iot/dashboard-design]]

## แหล่งข้อมูล

- [[sources/espem-energy-monitor]] — pattern ต้นแบบ (PZEM version)
- [[sources/pzem-004t-guide-2025]] — reference การอ่านค่าพลังงาน
- env-wastewater-webapp `docs/adr/0011-ac-power-monitor-esp32-sct013.md` — decision record
- OpenEnergyMonitor "Building Blocks" — วิธี calibration CT clamp (public reference, verify version)
