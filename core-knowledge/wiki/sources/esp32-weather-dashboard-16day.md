---
type: source
title: "ESP32 Weather Dashboard — Satellite Maps + 16-Day Forecast (Free APIs)"
slug: esp32-weather-dashboard-16day
date_ingested: 2026-04-18
original_file: https://www.hackster.io/mircemk/esp32-weather-dashboard-with-satellite-maps-and-16-day-forec-7ee044
tags: [esp32-s3, weather, dashboard, open-meteo, openweathermap, lcd, touch, 16-day-forecast]
---

# ESP32 Weather Dashboard with Satellite Maps + 16-Day Forecast

**ประเภท**: Hackster.io project  
**Hardware**: CrowPanel 7.0 HMI (ESP32-S3, 800×480 touch LCD)  
**ราคา**: ~$30 USD พร้อม acrylic case (ไม่ต้องบัดกรี)

## ประเด็นหลัก

1. **ใช้ API ฟรีทั้งหมด**: Open-Meteo (forecast), OpenWeatherMap (map tiles), RainViewer (radar), NTP (time)
2. **16-day forecast**: เด่นกว่า weather station ทั่วไป
3. **Interactive satellite map**: zoom 3 ระดับ, เลือก overlay (radar/cloud/precipitation)
4. **8 graphs**: pressure, precipitation, cloud cover, humidity, wind, UV, solar radiation
5. **ESP32-S3**: ใช้ CrowPanel ที่มี display ในตัว — ง่ายที่สุด ไม่ต้อง wire อะไรเพิ่ม

## APIs ที่ใช้ (ทั้งหมดฟรี)

| API | ข้อมูล | ลงทะเบียน |
|-----|--------|----------|
| Open-Meteo | 16-day forecast | ไม่ต้อง |
| OpenWeatherMap | Map tiles | ต้อง (ฟรี) |
| RainViewer | Radar tiles | ไม่ต้อง |
| NTP | Time sync | ไม่ต้อง |

## เปรียบเทียบกับ ESP32 E-Paper (lmarzen)

| | E-Paper (lmarzen) | LCD Touch (mircemk) |
|-|------------------|-------------------|
| Display | 7.5" E-Paper B/W | 7" LCD 800×480 |
| Power | ~14µA sleep, battery | ต้องต่อไฟ |
| Forecast | ไม่ระบุ | 16 วัน |
| Maps | ไม่มี | satellite + radar |
| ราคา | ~$56 | ~$30 |
| เหมาะกับ | portable, battery | ติดผนัง, plugged |

## หน้า Wiki ที่ได้รับการอัปเดต

- สร้างหน้านี้เป็น source สำหรับ weather monitoring use case
