---
type: source
title: "Freqtrade — Crypto Trading Bot on Raspberry Pi"
slug: freqtrade-pi5
date_ingested: 2026-04-20
original_file: web-search
tags: [freqtrade, trading-bot, raspberry-pi, docker, crypto, telegram]
quality: ⚠️ web-search
---

# Freqtrade — Crypto Trading Bot บน Raspberry Pi

**ประเภท**: open-source software documentation  
**แหล่ง**: freqtrade.io (official docs), wundertrading.com  
**เกี่ยวข้องกับ**: Pi 5, Telegram bot, crypto trading

## ประเด็นหลัก

1. Freqtrade รองรับ ARM64 (Pi 5) ผ่าน Docker image เฉพาะ `*_pi`
2. ต้องใช้ image `freqtradeorg/freqtrade:stable_pi` ไม่ใช่ image ปกติ
3. มี Telegram integration built-in — แจ้งผล trade, สั่ง pause/stop ได้
4. **Dry-run mode**: จำลอง trade โดยไม่ใช้เงินจริง — ต้องทดสอบก่อนเสมอ
5. RAM ที่ใช้: ~200-400MB รันคู่กับ Bitcoin node ได้สบาย

## Docker Setup (Pi 5)

```bash
# สร้าง user data folder
docker run --rm freqtradeorg/freqtrade:stable_pi \
  create-userdir --userdir user_data

# สร้าง config
docker run --rm -v "./user_data:/freqtrade/user_data" \
  freqtradeorg/freqtrade:stable_pi \
  new-config --config user_data/config.json

# Run (dry-run mode ก่อน)
docker compose up -d
```

## docker-compose.yml สำหรับ Pi

```yaml
image: freqtradeorg/freqtrade:stable_pi  # ← ต้องเป็น _pi
```

## Telegram Integration

ใน `config.json`:
```json
"telegram": {
  "enabled": true,
  "token": "YOUR_BOT_TOKEN",
  "chat_id": "YOUR_CHAT_ID"
}
```

คำสั่ง Telegram ที่ใช้ได้: `/start`, `/stop`, `/status`, `/profit`, `/balance`

## ข้อควรระวัง

- ⚠️ เริ่มด้วย **dry-run เสมอ** ก่อนใช้เงินจริง
- ⚠️ API key ต้องตั้งสิทธิ์ **trade only, no withdrawal**
- ⚠️ Backtest กลยุทธ์ก่อน deploy จริงทุกครั้ง
- ⚠️ ตั้ง stop-loss ทุก strategy

## แหล่งอ้างอิง

- [Freqtrade Official Docs](https://www.freqtrade.io/en/stable/installation/)
- [Freqtrade Docker Quickstart](https://www.freqtrade.io/en/stable/docker_quickstart/)
- [freqtrade-pi GitHub](https://github.com/tl-nguyen/freqtrade-pi)

## หน้า Wiki ที่เกี่ยวข้อง

- [[entities/iot/raspberry-pi]]
