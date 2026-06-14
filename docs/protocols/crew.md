# Straw Hat Wiki Crew Protocol

> **อัปเดต**: 2026-06-15 | **วัตถุประสงค์**: capability-role dispatch สำหรับ A-Wiki โดยไม่ hardcode model names

---

## ลูกเรือ (Crewmates)

| ชื่อ | Role | Cost lane | ความถนัด |
|------|------|-----------|-----------|
| 🧠 Vegapunk | Primary advisor / validator | `platform-primary` | วางแผน, synthesize, validate, final judgment |
| 🗺️ Nami | Search / lookup lane | `free-current` | ข้อมูลล่าสุด, URL summary, fact lookup |
| 📚 Robin | Reason / compare lane | `cheap-capable` หรือ `free-current` | reasoning, compare, synthesis ย่อย |
| ⚡ Luffy | Scan / lint lane | `platform-low-scout` หรือ `free-current` | file scan, lint, fast evidence gathering |
| 🔧 Franky | Universal fallback lane | runtime router | fallback / race / bridge ผ่าน `delegate.sh` |
| 🍳 Sanji | Dispatch shim | local | แปลง task → `delegate.sh` และเก็บ backward compatibility |

---

## Task Routing Table

| `task_type` | Crew role | Routed by |
|-----------|-----------|-----------|
| `search` / `lookup` | Nami | `scripts/swarm/delegate.sh search` |
| `summarize` | Nami / Robin | `scripts/swarm/delegate.sh summarize` |
| `reason` / `compare` | Robin | `scripts/swarm/delegate.sh reason|compare` |
| `scan` | Luffy | `scripts/swarm/delegate.sh scan` |
| `race` | Franky | `scripts/swarm/delegate.sh race` |

**Fallback chain**: ใช้ runtime roster จาก `delegate.sh` เสมอ; อย่า bind provider/model name ใน protocol นี้

---

## วิธีใช้ (Vegapunk สั่ง Sanji)

### Single task
```bash
python3 scripts/crew-dispatch.py --task "search:best MQTT broker 2026"
```

### Parallel dispatch (หลาย task พร้อมกัน)
ใช้ shell parallel หรือ AG2 orchestrator แทน เพราะ shim นี้ intentionally รับทีละ task:

```bash
bash scripts/swarm/delegate.sh search "latest ESP32-S3 specs" &
bash scripts/swarm/delegate.sh compare "ESP32 vs ESP32-S3 for TinyML" &
bash scripts/swarm/delegate.sh scan "summarize wiki/entities/iot/esp32.md" &
wait
```

### Goal-level orchestration
เมื่อโจทย์เป็น goal หลาย step ให้ใช้ AG2:

```bash
bash scripts/swarm/goal.sh "Audit all AI-tool wiki entries for staleness" --dry-run
```

---

## Cost Pyramid Integration

```
คำถามมาถึง Vegapunk
  ↓
"ค้น wiki ก่อนได้ไหม?"  → scripts/search-wiki.py (Level -1, ฟรี 100%)
"ไม่พบ → ต้องออก net?"  → Nami lane ผ่าน `delegate.sh` (Level 1, ฟรีก่อน)
"ต้อง reasoning?"        → Robin lane ผ่าน `delegate.sh` (Level 2, cheap/free)
"scan ไฟล์เยอะ?"         → Luffy lane ผ่าน `delegate.sh` (Level 3, low-scout/free)
"เขียน wiki/สรุป?"       → Vegapunk / platform-primary (Level 4)
```

---

## ข้อจำกัดที่ต้องรู้

- Crew นี้เป็น **role map** ไม่ใช่ provider map; provider/model จริงเลือกที่ runtime โดย `delegate.sh`
- ถ้า free-model keys ไม่มี → route จะล้มไปที่ platform-primary หรือ fail ตาม exit code ของ `delegate.sh`
- ถ้าต้อง self-planning / multi-round loop ให้ใช้ AG2 (`goal.sh`) ไม่ใช่ `crew-dispatch.py`
- Primary agent ยังต้อง validate output ของทุก lane ตาม Iron Law III

---

## Env Keys Setup

```bash
# preferred: store in drive/.secrets and let delegate.sh / goal.sh load on demand
export OPENROUTER_API_KEY="..."      # recommended universal free-first unlock
export GOOGLE_AI_STUDIO_KEY="..."    # Gemini alias
export GROQ_API_KEY="..."            # fast scan fallback
export DEEPSEEK_API_KEY="..."        # direct provider fallback
```

---

*Protocol version 2.0 — 2026-06-15*
