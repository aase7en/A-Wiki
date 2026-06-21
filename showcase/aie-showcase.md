# [Thai ไอ้A Plus Spot.] — AI อัตโนมัติบน Raspberry Pi 5

![](https://aase7en.github.io/A-Wiki/awiki-live.html)

---

## TL;DR — มันคืออะไร

ไอ้A คือ AI Agent ที่รันอยู่บน Raspberry Pi 5 ในห้องนอน —

- คุยกับคุณผ่าน Telegram ตลอด 24 ชม.
- รายงานข่าวให้คุณทุกเช้า 7 โมง
- เขียนโค้ด แก้บั๊ก push ขึ้น GitHub ได้เอง
- มีสมองเป็น A-Wiki — ระบบความรู้ที่มันอ่าน เขียน และค้นหาได้
- ใช้ AI 19 โมเดลฟรีจาก 8 เจ้า — สลับอัตโนมัติเมื่อตัวไหนล่ม

ไม่มี server รายเดือน ไม่มีค่า cloud — ทุกอย่างรันบน Pi ตัวเดียว

---

## 🧠 Architecture

```
                          ┌─────────────────────┐
                          │    [Telegram / Web]   │  ← คุณคุยกับไอ้A ทางนี้
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  Cloudflare Tunnel   │  ← เข้ารหัส QUIC ทะลุเน็ต
                          └──────────┬──────────┘
                                     │
┌────────────────────────────────────▼───────────────────────────────────┐
│                         Raspberry Pi 5 · umbrelOS                        │
│                                                                          │
│  ┌──────────────────────────────┐    ┌──────────────────────────────┐   │
│  │       Hermes Agent            │    │        A-Wiki Brain           │   │
│  │                              │    │                              │   │
│  │  Gateway · Tools · Cron      │◄──►│  Wiki · Knowledge Graph      │   │
│  │  Skills · Memory · Kanban    │    │  FTS5 Search · Cost Pyramid  │   │
│  │  Batch Workers (3 parallel)  │    │  Iron Laws · Swarm Protocol  │   │
│  └──────────────┬───────────────┘    └──────────────────────────────┘   │
│                 │                                                        │
│  ┌──────────────▼───────────────────────────────────────────────────┐   │
│  │                   Model Pool — Auto Switch                         │   │
│  │                                                                    │   │
│  │  DeepSeek V4 Pro  │  Gemini Flash  │  Z.AI GLM  │  OpenRouter      │   │
│  │  Groq · Fireworks  │  HuggingFace   │  xAI Grok  │  +2 more        │   │
│  │                                                                    │   │
│  │  19 models · 8 providers · 429 → auto-failover 60s cooldown      │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ ทำอะไรได้บ้าง

### 📰 ระบบอัตโนมัติรายวัน

| เวลา | ทำอะไร |
|------|--------|
| 07:00 น. | รายงานข่าวเช้า — ค้นหา + สรุปไทย + ส่ง Telegram |
| ทุก 5 นาที | ตรวจสอบ Cloudflare Tunnel — ถ้าตาย restart ทันที |
| ทุก 15 นาที | อัปเดต URL Tunnel ในเว็บ A-Wiki Live |
| ทุก 6 ชม. | สแกนหาโมเดลฟรีใหม่จากทุก provider |

### 💬 คุยโต้ตอบ

- ตอบคำถามทั่วไป — ค้นเว็บ + วิเคราะห์
- ภาษาไทยเป็นหลัก — บุคลิก "ไอ้A" เงียบ ลุ่มลึก มุกแห้ง
- จำได้ว่าคุณเป็นใคร — persistent memory ข้าม session
- รองรับรูป — Gemini Flash อ่านรูปให้

### 💻 เขียนโค้ด + จัดการระบบ

- อ่าน/เขียน/แก้ไขไฟล์ในเครื่อง
- รัน shell command + Python
- Git push ขึ้น GitHub โดยตรง (SSH key ใน container)
- แก้ config Hermes เองได้ — เปลี่ยนโมเดล เปิดปิดฟีเจอร์

### 🎨 Creative

- สร้างรูป AI ด้วย FAL
- แปลงข้อความเป็นเสียง (Edge TTS)
- เปลี่ยน persona ได้ 15+ แบบ

---

## 🚀 โปรเจกต์ในท่อ (Backlog)

### 🎮 เกมภายใต้ Sunday Estate

| โปรเจกต์ | Stack | สถานะ |
|----------|-------|--------|
| **Sunday Invest Moon** | Phaser + React + Zustand | 🟡 Dev — 679 tests green |
| **Tide & Tally** | เรือโจรสลัดเทรดบอท | 🟡 Dev |

### 🏥 IoT โรงพยาบาล

| โปรเจกต์ | Hardware |
|----------|----------|
| วัดไฟฟ้า | PZEM-004T + ESP32 |
| ชั่งขยะ | Load Cell + HX711 |
| PM2.5 | PMS5003 + LoRa |
| Cold Chain | DS18B20 + TinyML |

### 💻 Web App + AI

| โปรเจกต์ | Stack |
|----------|-------|
| Pharmacy Order Checker | FastAPI + React |
| ระบบบำบัดน้ำเสีย | FastAPI + PostgreSQL |
| Trading Bot | Freqtrade + Pi 5 |
| Mac Mini AI Server | Ollama + LiteLLM |

> ทั้งหมด 15+ โปรเจกต์ใน roadmap — รันบน Pi 5 + Mac Mini เป็นหลัก

---

## 💰 ต้นทุน

| รายการ | ราคา/เดือน |
|--------|-----------|
| Raspberry Pi 5 ไฟฟ้า | ~30 บาท |
| DeepSeek V4 Pro (API) | ตาม usage |
| โมเดลฟรี 19 ตัว | 0 บาท |
| Cloudflare Tunnel | 0 บาท |
| GitHub Pages | 0 บาท |
| **รวม** | **~30 บาท + API usage** |

---

## 🔧 Technical Stack

- **Hardware:** Raspberry Pi 5 · 8GB RAM · ARM64
- **OS:** umbrelOS · Docker container
- **Agent:** Hermes Agent (Nous Research) · DeepSeek V4 Pro
- **Brain:** A-Wiki — markdown wiki · FTS5 search · knowledge graph
- **Network:** Cloudflare Tunnel (QUIC) · Telegram API · GitHub API
- **CI/CD:** GitHub Actions — auto-scout · deploy to Pages · wiki health
- **Orchestration:** Kanban board · Cron scheduler · Batch delegation

---

## 📂 Open Source

ทุกอย่างอยู่บน GitHub — [github.com/aase7en/A-Wiki](https://github.com/aase7en/A-Wiki)

```
scripts/hermes/model-pool/     ← Free model pool + auto-failover
.github/workflows/             ← GitHub Actions
agent-skills/                  ← Iron Laws + Swarm
wiki/                          ← ฐานความรู้
```

---

## 🎯 What Makes It Different

1. **รันบน Pi จริงๆ** — ไม่ใช่ VM บน cloud ไม่ใช่ demo — ไฟเสียบตลอด ทำงานตลอด

2. **ฟรีเป็นหลัก** — 19 โมเดลฟรีใช้ก่อน ติด limit ค่อยสลับ จนหมด pool ค่อยใช้ของเสียเงิน

3. **Iron Laws** — กฎที่ AI ต้องทำตาม ห้ามโกง ห้ามข้ามขั้นตอน ห้ามแก้ไข raw data

4. **เรียนเองได้** — เจอปัญหา → แก้ → บันทึกเป็น skill → ครั้งต่อไปรู้เลย

5. **หนึ่งคนสร้าง** — ไม่มีทีม ไม่มี budget ไม่มี investor — แค่คนที่อยากรู้ว่าถ้าให้ AI อยู่ในกล่องเล็กๆ แล้วปล่อยมันทำงาน มันจะไปได้ไกลแค่ไหน

---

──✦ [Thai ไอ้A Plus Spot.] · A-Wiki Brain + Hermes Agent · 2026 ✦──
