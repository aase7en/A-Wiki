---
type: source
title: "LoRaWAN® FUOTA on RAK3172 (RUI3 v5) with ChirpStackOS"
slug: lorawan-fuota-rak3172
date_ingested: 2026-04-18
original_file: raw/LoRaWAN® FUOTA on RAK3172 (RUI3 v5) with ChirpStackOS – Full Step-by-Step Demo.md
tags: [lorawan, fuota, rak3172, chirpstack, ota, firmware-update, advanced]
---

# LoRaWAN® FUOTA on RAK3172 with ChirpStackOS

**ประเภท**: video tutorial (YouTube — RAKwireless)
**วันที่**: 2026-03-03
**ผู้เผยแพร่**: RAKwireless

## ประเด็นหลัก

1. **FUOTA**: Firmware Update Over-the-Air ผ่าน LoRaWAN — อัปเดต firmware โดยไม่ต้อง connect สาย
2. **ChirpStack**: self-hosted LoRaWAN Network Server (LNS) — ทางเลือก open-source แทน TTN
3. **Class C mode**: device ต้องเปลี่ยน Class C ระหว่าง FUOTA เพื่อรับ downlink ตลอดเวลา
4. **Multicast**: ส่ง firmware fragment ไปหลาย device พร้อมกันผ่าน multicast group
5. **ยังเป็น beta**: ณ วันที่ publish ยังไม่ production-ready

## Workflow ของ FUOTA

```
ChirpStackOS → FUOTA session → Upload firmware → Start session
    ↓
Device receives multicast fragments (Class C)
    ↓
Verify firmware → Reboot with new firmware
```

## เกี่ยวข้องกับโปรเจ็คนี้แค่ไหน

**ระดับ Advanced** — ไม่เกี่ยวกับโปรเจ็คปัจจุบัน แต่มีประโยชน์มากหากโปรเจ็คขยายเป็น production LoRaWAN ที่ต้องการ OTA update

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/lorawan]] — เพิ่ม FUOTA mention
