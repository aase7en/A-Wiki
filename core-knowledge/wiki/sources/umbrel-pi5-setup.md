---
type: source
title: "Umbrel OS บน Raspberry Pi 5 — Setup และ Custom Apps"
slug: umbrel-pi5-setup
date_ingested: 2026-04-20
original_file: web-search
tags: [umbrel, raspberry-pi, bitcoin, docker, self-hosted]
quality: ⚠️ web-search
---

# Umbrel OS บน Raspberry Pi 5

**ประเภท**: official documentation + community  
**แหล่ง**: github.com/getumbrel, umbrel.com, community.umbrel.com  
**เกี่ยวข้องกับ**: Pi 5, Bitcoin node, Docker

## ประเด็นหลัก

1. Umbrel OS ติดตั้งบน NVMe โดยตรง (ต้องใช้ v1.2.0+)
2. Bitcoin node รันเป็น Docker container ผ่าน App Store
3. รองรับ **pruned node** — ลด storage จาก ~700GB เหลือ ~10-50GB
4. เพิ่ม custom Docker app ผ่าน **Portainer** ที่ติดตั้งได้จาก App Store
5. มี App Store 300+ apps: Bitcoin, Lightning, Nextcloud, Home Assistant ฯลฯ

## การติดตั้ง Pi 5

```
1. Download umbrelOS image → flash ด้วย Balena Etcher
2. Flash ลง NVMe (ไม่ใช่ microSD — write cycle จำกัด)
3. เสียบ ethernet, เปิดเครื่อง
4. เข้า http://umbrel.local
```

> ⚠️ Pi 5 รุ่นเก่าอาจต้องอัปเดต bootloader ก่อน

## Bitcoin Pruned Node (ประหยัด Storage)

ใน Bitcoin Node settings ใน Umbrel:
```
prune=10000   # เก็บแค่ 10GB ล่าสุด (~10,000 blocks)
```

| Mode | Storage | ความสามารถ |
|------|---------|-----------|
| Full node (default) | ~700GB+ | ตรวจสอบทุก block ตั้งแต่ genesis |
| Pruned node | ~10-50GB | ตรวจสอบ block ปัจจุบัน, ไม่มี historical |

> เจ้านายรัน full node อยู่แล้ว → **ไม่จำเป็นต้อง prune** เพราะมี 2TB NVMe

## เพิ่ม Custom Docker App (Freqtrade, Ollama, Bot)

1. ติดตั้ง **Portainer** จาก Umbrel App Store
2. เปิด Portainer → Add Stack → ใส่ docker-compose.yml
3. หรือใช้ SSH: `ssh umbrel@umbrel.local`

## แหล่งอ้างอิง

- [Umbrel GitHub Wiki — Pi 5](https://github.com/getumbrel/umbrel/wiki/Install-umbrelOS-on-a-Raspberry-Pi-5)
- [Bitcoin Pruned Node — Umbrel Community](https://community.umbrel.com/t/bitcoin-pruned-node-and-lightning-node/22459)
- [Umbrel App Store](https://apps.umbrel.com)

## หน้า Wiki ที่เกี่ยวข้อง

- [[entities/iot/raspberry-pi]]

---

## อัปเดต 2026-04-22 — สำรวจ Docker containers

### Containers ที่รันอยู่บน Pi5

| Container | Port | สถานะ |
|-----------|------|-------|
| `webapp_backend` | 8000 | FastAPI ✅ Up 6h |
| `webapp_db` | 5432 | PostgreSQL ✅ |
| `webapp_adminer` | 8181 | DB Admin UI ✅ |
| `portainer` | 9000 | ✅ Up 11h |
| `bitcoin_app_1` | 8332-8333 | ✅ Up 24h |
| `lightning_lnd_1` | 9735 | ✅ Up 25h |
| `nextcloud` | 8081 | ✅ Up 24h |
| `cloudflared` | — | ✅ ติดตั้งแล้วแต่ยังไม่ config tunnel |
| `tailscale` | — | ✅ IP = 100.111.37.13 |
| `pi-hole` | — | ✅ ติดตั้งแต่ยังไม่ได้ใช้ |

### FastAPI — Hospital ENV & Epidem API v1.0.0

Swagger UI: `http://umbrel.local:8000/docs`

Endpoints ที่มีแล้ว:
- `GET/POST /water-quality/`
- `GET/DELETE /water-quality/{record_id}`
- `GET /health`

### PostgreSQL DB (webapp/webapp1234)

Tables ที่มี: `patients`, `rabies_cases`, `users`, `vaccination_schedule`, `water_quality_records`

`water_quality_records` — fields ครอบคลุมระบบบำบัดน้ำเสียโรงพยาบาลครบ:
DO, pH, TDS, SV30, Free Chlorine, Temp, pump/aerator/chlorinator status, รูปภาพ, alerts

### Tailscale
เข้าถึงจากนอกบ้านได้ผ่าน `100.111.37.13` — ต้อง login Tailscale account เดียวกันบนอุปกรณ์ที่ใช้

### งานที่ยังค้างอยู่
- [ ] Cloudflare Tunnel ยังไม่ได้ config (ต้องสมัคร Cloudflare account + domain)
- [ ] ดู code FastAPI ว่า endpoint ครบไหม
- [ ] เพิ่ม endpoint สำหรับ rabies_cases, vaccination_schedule
- [ ] ทำ frontend แทน Swagger UI
