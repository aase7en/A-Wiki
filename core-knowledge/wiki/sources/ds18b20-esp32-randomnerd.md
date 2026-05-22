---
type: source
title: "ESP32 DS18B20 Temperature Sensor — Single, Multiple, Web Server"
slug: ds18b20-esp32-randomnerd
date_ingested: 2026-04-18
original_file: https://randomnerdtutorials.com/esp32-ds18b20-temperature-arduino-ide/
tags: [esp32, ds18b20, temperature, one-wire, multiple-sensors, arduino]
---

# ESP32 DS18B20 Temperature Sensor Guide

**ประเภท**: tutorial  
**แหล่ง**: Random Nerd Tutorials

## ประเด็นหลัก

1. **One-Wire protocol**: DS18B20 ใช้สายข้อมูลเพียง 1 เส้น + 4.7kΩ pull-up ระหว่าง DATA กับ VCC
2. **Multiple sensors**: สาย bus เดียว ต่อ sensor หลายตัวได้ แต่ละตัวมี 64-bit unique address
3. **Libraries**: OneWire (Paul Stoffregen) + DallasTemperature (Miles Burton)
4. **GPIO**: ใช้ GPIO 4 ในตัวอย่าง (ใช้ GPIO อื่นได้)
5. **Specs**: -55°C ถึง +125°C, ±0.5°C ที่ -10°C ถึง +85°C

## Wiring

```
DS18B20 VCC  → 3.3V
DS18B20 GND  → GND
DS18B20 DATA → GPIO 4 ──┬── 4.7kΩ ── 3.3V
                         (pull-up resistor บังคับ)
```

## Code หลัก

```cpp
sensors.requestTemperatures();
float tempC = sensors.getTempCByIndex(0);  // sensor แรก
float tempC2 = sensors.getTempCByIndex(1); // sensor ที่สอง
```

## Parasite Mode

DS18B20 สามารถดึงไฟจาก DATA line โดยไม่ต้องต่อ VCC แยก (ประหยัดสาย) แต่ไม่แนะนำสำหรับ multi-sensor หรือ long wire

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/ds18b20]] — สร้างใหม่
