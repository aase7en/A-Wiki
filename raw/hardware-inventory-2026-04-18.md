# Hardware Inventory — My IoT Lab
Date: 2026-04-18
Source: ถ่ายรูปอุปกรณ์จริง (10 รูป)

## Microcontrollers
- ESP32 DevKit V1 + Terminal Breakout Board × 1
- ESP32-S3-N16R8 WROOM + Terminal Breakout (green PCB) × 1
- Arduino Uno R3 (CH340) × 1

## Communication Modules
- DX-LR02-900T22D LoRa 900MHz × 2 (พร้อมเสาอากาศ SMA)

## Power
- 18650 Battery Shield V3 (5V/4A output, 3V/1A output, USB-A output, Micro-USB input) × 1
- Vapcell INR18650 M35 3500mAh 3.7V (Max continuous discharge: 10A, Max pulse: 25A/5s) × 2

## Adapters
- DX-SMART DX-PJ15-V1.1 USB Type-C to TTL (TX/RX/NC/GND/5V/3V3/GND) × 2

## Starter Kit Contents (Arduino R3 CH340 Starter Kit)
- DHT11 Temperature & Humidity Sensor × 1
- HC-SR501 PIR Motion Sensor × 1
- 0.96" OLED × 1
- IIC LCD 1602 × 1
- SG90 Servo × 1
- 1-Way Relay Module × 1
- HC-SR04 Ultrasonic Module × 1
- 8×8 Red Dot Matrix Screen × 1
- Joystick Module × 1
- TTP223B Touch Sensor × 1
- Soil Humidity Sensor × 1
- Obstacle Avoidance Module × 1
- BreadBoard 4.5×3.5cm × 2
- DuPont Cable F-M × 20
- DuPont Cable M-M × 40
- Resistors: 220R/1k/10k × 10 each (30 pcs)
- LEDs: Green/Blue/Yellow/Red × 5 each (20 pcs)
- USB Cable × 1

## โปรเจ็คเป้าหมาย
ระบบ monitor อุณหภูมิในห้อง ส่งข้อมูลผ่านมือถือ
(Line / Telegram / Dashboard กราฟย้อนหลัง)

## หมายเหตุจากรูป
- ESP32 DevKit V1 ติดอยู่บน terminal breakout board พร้อมสาย power (แดง/ดำ)
- DX-LR02 ×2 ต่ออยู่กับ ESP32 ผ่าน UART (MO/M1/RXD/TXD/AUX/VCC/GND) ดูเหมือนกำลัง test LoRa link
- 18650 Battery Shield V3 รองรับ 5V 4A (boost converter) และ 3V 1A สำหรับ MCU โดยตรง
- USB-C to TTL ยี่ห้อ DX-SMART ใช้สำหรับ flash firmware หรือ debug serial
