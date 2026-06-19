# Hermes Agent on Raspberry Pi 5 — A-Wiki Integration Guide

**วันที่**: 2026-06-20 | **สถานะ**: ✅ Verified

## ภาพรวม

Hermes Agent สามารถรันบน Raspberry Pi 5 (ARM64) เพื่อทำหน้าที่เป็น AI agent gateway ที่:
- ต่อ Telegram bot → รับคำสั่ง/ถาม-ตอบจาก A-Wiki
- ดู A-Wiki Live Dashboard แบบ real-time
- รัน cron jobs (health check, benchmark scan, cost audit)
- ควบคุม IoT devices ผ่าน MQTT (ESP32, sensors)

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Raspberry Pi 5 | 8GB RAM | 16GB RAM |
| Storage | 64GB microSD | 256GB NVMe SSD (via HAT) |
| OS | Raspberry Pi OS (64-bit) | Ubuntu Server 24.04 ARM64 |
| Python | 3.11+ | 3.12 |
| Network | WiFi 5 / Ethernet | Ethernet (stable for Telegram) |

## Installation

```bash
# 1. Install Hermes Agent (one-liner)
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc

# 2. Setup
hermes setup              # interactive wizard
hermes model              # add API key + choose model (DeepSeek V4 / Gemini Flash)

# 3. Clone A-Wiki
git clone <a-wiki-repo-url> ~/A-Wiki
cd ~/A-Wiki
bash scripts/setup-local.sh

# 4. Telegram gateway
hermes gateway setup      # choose Telegram → enter bot token
hermes gateway start      # start background service

# 5. Link A-Wiki skills to Hermes
ln -s ~/A-Wiki/agent-skills/ ~/.hermes/skills/awiki/
```

## Docker Compose (Alternative)

```yaml
# docker-compose.yml
version: '3.8'
services:
  hermes:
    image: ghcr.io/nousresearch/hermes-agent:latest
    platform: linux/arm64
    volumes:
      - ~/.hermes:/root/.hermes
      - ~/A-Wiki:/A-Wiki:ro
    environment:
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - A_WIKI_DRIVE_PATH=/A-Wiki/drive
    restart: unless-stopped

  dashboard:
    image: python:3.11-slim
    platform: linux/arm64
    working_dir: /A-Wiki
    volumes:
      - ~/A-Wiki:/A-Wiki
    command: python3 scripts/live-dashboard/server.py
    ports:
      - "7790:7790"
    restart: unless-stopped
```

## Performance Notes

| Metric | RPi 5 8GB | RPi 5 16GB |
|--------|-----------|------------|
| Hermes idle RAM | ~200MB | ~200MB |
| Python LLM overhead | ~500MB | ~500MB |
| Dashboard server | ~50MB | ~50MB |
| **Usable for other services** | ~6GB | ~14GB |

- **ไม่แนะนำให้รัน local LLM บน Pi 5** — ใช้ API-based models (DeepSeek, Gemini) แทน
- Telegram gateway ใช้ RAM น้อยมาก (~30MB)
- Dashboard SSE ใช้ไฟล์-based log → CPU ต่ำ

## Integration with A-Wiki Live

1. Dashboard รันบน Pi 5 port 7790 → ดูใน browser ได้
2. Hermes cron jobs รันอัตโนมัติบน Pi 5 (ไม่ต้องเปิด Mac ทิ้งไว้)
3. Telegram bot → ถามคำถาม → Hermes → ค้น A-Wiki FTS5 → ตอบกลับ
4. IoT devices → MQTT broker (Mosquitto บน Pi) → Hermes skill → ควบคุมผ่าน Telegram

## Troubleshooting

| ปัญหา | วิธีแก้ |
|-------|--------|
| `Illegal instruction` | ติดตั้ง Python 3.11 ARM64 binary |
| Telegram timeout | ใช้ Ethernet แทน WiFi |
| Dashboard 404 | เช็ค `exports/html/` หรือ `scripts/live-dashboard/` |
| Memory full | ลด `max_turns` ใน config.yaml เหลือ 30 |
