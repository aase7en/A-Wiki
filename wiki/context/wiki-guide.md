# Wiki Usage Guide — คู่มือการใช้งาน My-IoT-Wiki

> สำหรับเจ้านาย ~@สุ๑InW และ Claude agent ทุก session
> อ่านไฟล์นี้เมื่อต้องการทราบ keyword, คำสั่ง, และ workflow

---

## ลำดับการโหลด Context (ทำทุก session ใหม่)

```
Step 1 → อ่าน wiki/context/wiki-state.md        (~30 lines, Tier 1)
           ถ้าตอบได้ → หยุด
Step 2 → อ่าน wiki/context/wiki-overview.md     (~200 lines, Tier 2)
           ถ้าตอบได้ → หยุด
Step 3 → อ่าน wiki/context/knowledge-graph.md   (~200 lines, Tier 3)
           ถ้าต้องการ relationships
Step 4 → อ่านหน้าเต็มเฉพาะเมื่อจำเป็น           (Tier 4)
```

---

## คำสั่ง / Keywords ที่ใช้ได้

### Ingest (เพิ่มข้อมูลใหม่)
| พูดว่า | Claude จะทำ |
|--------|-----------|
| `"ingest นี้"` + ส่งข้อความ/URL | สร้าง source page + อัปเดต entities/concepts |
| `"เพิ่มข้อมูล [หัวข้อ]"` | ค้นเว็บ → ingest อัตโนมัติ |
| `"บันทึก [เนื้อหา]"` | สร้าง page ตามที่บอก |

### Query (ถามข้อมูล)
| พูดว่า | Claude จะทำ |
|--------|-----------|
| `"อธิบาย [หัวข้อ]"` | ค้นจาก wiki → ตอบพร้อม citation |
| `"เปรียบเทียบ [A] กับ [B]"` | โหลด knowledge-graph → วิเคราะห์ |
| `"ออกแบบระบบ [use case]"` | โหลด synthesis ก่อน → entities+concepts |

### Synthesis (วิเคราะห์ข้ามหัวข้อ)
| พูดว่า | Claude จะทำ |
|--------|-----------|
| `"วิเคราะห์ [topic]"` | สร้าง synthesis page ถ้าคุ้มค่า |
| `"ออกแบบ [โปรเจ็ค]"` | รวม entities+concepts → synthesis |
| `"สรุป [หัวข้อ]"` | ดึง abstracts → ตอบกระชับ |

### Maintenance
| คำสั่ง | Claude จะทำ |
|--------|-----------|
| `/lint` | ตรวจ orphan pages, contradictions, stubs |
| `"อัปเดต inventory"` | แก้ wiki-state.md + raspberry-pi.md |
| `"push"` | commit + push ทุกไฟล์ที่เปลี่ยน |
| `"สรุป session"` | อัปเดต log.md + push |

---

## Domain Router — บอก Claude ให้โหลดถูกที่

| ถามเรื่อง | บอกว่า | Claude โหลด |
|----------|--------|-----------|
| ESP32, sensor, MQTT | `"IoT:"` | entities/iot/ |
| ขยะ, น้ำเสีย, โรงพยาบาล | `"Env:"` | concepts/env/ |
| Telegram bot, LLM, agent | `"AI:"` | entities/ai-tools/ |
| Pi5, hardware | `"Hardware:"` | raspberry-pi.md |
| ข้ามโดเมน | `"Cross:"` | synthesis/ + knowledge-graph |

**ตัวอย่าง**: `"IoT: ESP32 เชื่อม LoRa ยังไง"` → โหลดแค่ entities/iot/ ไม่ต้องโหลดทั้ง wiki

---

## Session Startup Template (Copy วางได้เลย)

```
สวัสดีครับ เจ้านาย ~@สุ๑InW
โหลด wiki-state แล้ว — session พร้อม

วันนี้จะทำอะไรครับ?
- Ingest source ใหม่?
- ถามข้อมูลจาก wiki?
- ออกแบบ/วิเคราะห์โปรเจ็ค?
```

---

## Workflow สำคัญ

### เพิ่ม Hardware ใหม่
```
1. บอก spec ให้ครบ (ชื่อ, RAM, storage, use case)
2. Claude → อัปเดต wiki-state.md (inventory)
3. Claude → อัปเดต/สร้าง entity page
4. Claude → อัปเดต wiki-overview.md
5. Claude → push
```

### Ingest Source จากมือถือ
```
1. Copy เนื้อหาจาก web/Google Drive → paste ในแชท
2. บอกชื่อไฟล์และ path ที่ต้องการ
3. Claude → สร้าง source page → push
```

### ถามคำถามข้ามโดเมน (IoT × Env × AI)
```
"Cross: ออกแบบระบบตรวจสอบห้องเก็บขยะโรงพยาบาล"
→ Claude โหลด: knowledge-graph → synthesis → entities ที่เกี่ยวข้อง
```

---

## Pi5 Projects — Quick Reference

| Project | Status | Source ใน wiki |
|---------|--------|---------------|
| Bitcoin node (Umbrel) | ✅ running | umbrel-pi5-setup |
| Telegram AI agent | 📐 planned | telegram-ai-agent-setup |
| Freqtrade trading bot | 📐 planned | freqtrade-pi5 |
| Ollama local LLM | 📐 planned | ollama-pi5 |

**แนะนำลำดับทำ**: Telegram AI agent → Ollama → Freqtrade

---

## Source Quality

| สัญลักษณ์ | ความหมาย | ควรทำ |
|----------|---------|-------|
| ✅ verified | fetch จาก PDF/official | เชื่อถือได้ |
| ⚠️ web-search | ได้จาก search results | verify ด้วย PDF |
| 📐 design | วางแผนไว้ ยังไม่ทำ | — |
| 🔴 stub | ยังไม่มีหน้า | สร้างเมื่อมีข้อมูล |

---

*wiki-guide v1.0 — created 2026-04-20 | สำหรับเจ้านาย ~@สุ๑InW*
