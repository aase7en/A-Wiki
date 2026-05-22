---
type: source
title: "ESP32 E-Paper Weather Display — Low Power, OpenWeatherMap"
slug: esp32-weather-epd
date_ingested: 2026-04-18
original_file: https://github.com/lmarzen/esp32-weather-epd
tags: [esp32, weather, e-paper, openweathermap, deep-sleep, low-power, bme280]
---

# ESP32 E-Paper Weather Display

**ประเภท**: GitHub project (open source)  
**ผู้เขียน**: lmarzen  
**Hardware**: FireBeetle 2 ESP32-E + 7.5" E-Paper

## ประเด็นหลัก

1. **Ultra low power**: ~14µA deep sleep, ~83mA ขณะ refresh — battery 5000mAh อยู่ได้ **6-12 เดือน**
2. **OpenWeatherMap API**: ต้องสมัคร API key ฟรี (One Call API 3.0 + Air Pollution API)
3. **E-Paper 7.5"**: แสดง current weather, hourly graph, precipitation probability, indoor sensor
4. **Update ทุก 30 นาที**: deep sleep ระหว่างนั้น
5. **Indoor sensor**: BME280 วัด Temp/Humidity ภายในห้อง แสดงคู่กับ outdoor data

## Hardware

| Component | รายละเอียด | ราคาประมาณ |
|-----------|-----------|-----------|
| ESP32 | FireBeetle 2 ESP32-E | ~$8 |
| Display | Waveshare 7.5" E-Paper (B/W) | ~$25 |
| Adapter | DESPI-C02 | ~$5 |
| Sensor | BME280 | ~$3 |
| Battery | 3.7V LiPo 5000mAh | ~$15 |

**รวม ~$56** (ประหยัดกว่า commercial weather station)

## Power Strategy

```
refresh (15s, 83mA) → deep sleep (30min, 14µA) → wake → refresh → ...
Battery life = 5000mAh ÷ avg_current ≈ 6-12 เดือน
```

## หน้า Wiki ที่ได้รับการอัปเดต

- สร้างหน้านี้เป็น source สำหรับ weather monitoring use case
