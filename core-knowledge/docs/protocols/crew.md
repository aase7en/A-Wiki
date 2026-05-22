# Straw Hat Wiki Crew Protocol

> **อัปเดต**: 2026-05-18 | **วัตถุประสงค์**: routing rules สำหรับ parallel multi-agent dispatch

---

## ลูกเรือ (Crewmates)

| ชื่อ | Model | Cost | Env Key | ความถนัด |
|------|-------|------|---------|---------|
| 🧠 Vegapunk | Claude Sonnet | ปกติ | `ANTHROPIC_API_KEY` | CEO: วางแผน, synthesize, เขียน wiki |
| 🗺️ Nami | Gemini 2.5 Flash-Lite | **ฟรี** (1K req/day) | `GOOGLE_AI_STUDIO_KEY` | หาของ: search, lookup, URL summary |
| 📚 Robin | DeepSeek V4 Flash | $0.14/M input | `DEEPSEEK_API_KEY` | ขุดประวัติ: reasoning, compare, analysis |
| ⚡ Luffy | Groq Llama 3.3 70B | **ฟรี** (14.4K req/day) | `GROQ_API_KEY` | กำลัง: scan ไฟล์, lint, fast execute |
| 🔧 Franky | OpenRouter free router | **ฟรี** (200 req/day) | `OPENROUTER_API_KEY` | ช่าง: code, build, universal fallback |
| 🍳 Sanji | `crew-dispatch.py` | ฟรี (local) | — | เชฟ: orchestrate parallel dispatch |

---

## Task Routing Table

| task_type | ไปที่ | เหตุผล |
|-----------|-------|--------|
| `search` | Nami | Gemini ดี web-grounded, ฟรี |
| `lookup` | Nami | same |
| `summary` | Nami | same |
| `url` | Nami | URL fetch + summary |
| `analyze` | Robin | DeepSeek reasoning ดี, ถูก |
| `compare` | Robin | same |
| `reason` | Robin | same |
| `scan` | Luffy | Groq เร็วสุด, ฟรี, ดีสำหรับ file scan |
| `lint` | Luffy | same |
| `execute` | Luffy | same |
| `code` | Franky | OpenRouter free picks best code model |
| `build` | Franky | same |
| `refactor` | Franky | same |

**Fallback chain**: ถ้า crewmate หลักไม่มี API key → Franky (OpenRouter) → Luffy (Groq)

---

## วิธีใช้ (Vegapunk สั่ง Sanji)

### Single task
```bash
python3 scripts/crew-dispatch.py --task "search:best MQTT broker 2026"
```

### Parallel dispatch (หลาย task พร้อมกัน)
```bash
python3 scripts/crew-dispatch.py \
  --task "search:latest ESP32-S3 specs" \
  --task "analyze:compare ESP32 vs ESP32-S3 for TinyML" \
  --task "scan:summarize wiki/entities/iot/esp32.md"
```

### Plan file (Vegapunk เขียน JSON plan แล้วให้ Sanji dispatch)
```bash
# สร้าง /tmp/plan.json:
# [{"type": "search", "prompt": "..."}, {"type": "analyze", "prompt": "..."}]
python3 scripts/crew-dispatch.py --plan /tmp/plan.json
```

### ดูสถานะลูกเรือ
```bash
python3 scripts/crew-dispatch.py --list-crew
```

### Demo (ทดสอบระบบ)
```bash
python3 scripts/crew-dispatch.py --demo
```

---

## Cost Pyramid Integration

```
คำถามมาถึง Vegapunk
  ↓
"ค้น wiki ก่อนได้ไหม?"  → scripts/search-wiki.py (Level -1, ฟรี 100%)
"ไม่พบ → ต้องออก net?"  → Nami: Gemini Flash-Lite (Level 1, ฟรี)
"ต้อง reasoning?"        → Robin: DeepSeek (Level 2, ถูกมาก)
"scan ไฟล์เยอะ?"         → Luffy: Groq (Level 3, ฟรี)
"เขียน wiki/สรุป?"       → Vegapunk: Claude Sonnet (Level 4, ปกติ)
```

---

## ข้อจำกัดที่ต้องรู้

- **Nami (Gemini)**: Google ลด rate limit 50-80% ในธ.ค. 2025 — ระวัง 1K req/day หมดถ้าใช้บ่อย
- **Luffy (Groq)**: 6K TPM — ไม่เหมาะงาน long-context (>4K tokens ต่อ call)
- **Franky (OpenRouter free)**: catalog เปลี่ยนตลอด — ใช้ `openrouter/free` router ให้ auto-pick
- **Robin (DeepSeek)**: V4 Pro ลด 75% ถึง 31 พ.ค. 2026 — ถ้าต้อง reasoning หนัก upgrade ได้ถูก
- **ทุกคน**: ถ้าไม่มี API key → fall through ไป Franky → ถ้า Franky ก็ไม่มี → Claude native

---

## Env Keys Setup

```bash
# ใส่ใน ~/.zshrc หรือ ~/.bashrc
export GOOGLE_AI_STUDIO_KEY="..."   # Nami — https://aistudio.google.com/apikey
export DEEPSEEK_API_KEY="..."       # Robin — https://platform.deepseek.com
export GROQ_API_KEY="..."           # Luffy — https://console.groq.com
export OPENROUTER_API_KEY="..."     # Franky — https://openrouter.ai/keys
```

---

*Protocol version 1.0 — 2026-05-18*
