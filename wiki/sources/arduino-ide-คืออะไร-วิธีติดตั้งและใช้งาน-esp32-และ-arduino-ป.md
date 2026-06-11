---
type: source
title: "**Arduino IDE** (Integrated Development Environment) คือโปรแกรมสำหรับเขียนโค้ดแล"
slug: arduino-ide-คืออะไร-วิธีติดตั้งและใช้งาน-esp32-และ-arduino-ป
date_ingested: 2026-05-24
original_file: raw/Arduino IDE คืออะไร วิธีติดตั้งและใช้งาน ESP32 และ Arduino ปี2025.md
tags: [iot, esp32, arduino]
---

---
title: "Arduino IDE คืออะไร วิธีติดตั้งและใช้งาน ESP32 และ Arduino ปี2025"
source: "https://devadiy.com/arduino-ide-guide/"
author:
  - "deva_diy"
published: 2025-08-12
created: 2026-04-18
description: "สอนใช้งาน Arduino IDE สำหรับมือใหม่ ตั้งแต่การติดตั้ง การตั้งค่า และการอัปโหลดโค้ดไปยังบอร์ด ESP32 และ Arduino พร้อมเทคนิคพื้นฐานที่ควรรู้"
tags:
  - "clippings"
---
## Arduino IDE คืออะไร

**Arduino IDE** (Integrated Development Environment) คือโปรแกรมสำหรับเขียนโค้ดและอัปโหลดไปยังบอร์ดไมโครคอนโทรลเลอร์ เช่น Arduino UNO, ESP32, ESP8266 และบอร์ดอื่น ๆ ที่รองรับ โดยตัวโปรแกรมจะรวมฟังก์ชันสำคัญที่ Maker และนักพัฒนาต้องใช้ไว้ในที่เดียว ได้แก่

- ตัวแก้ไขโค้ด (Code Editor) – สำหรับพิมพ์โค้ดภาษา C/C++
- ปุ่มคอมไพล์ (Verify) – ตรวจสอบโค้ดว่าถูกต้องหรือไม่
- ปุ่มอัปโหลด (Upload) – ส่งโค้ดไปยังบอร์ดผ่านสาย USB หรือการเชื่อมต่ออื่น ๆ
- Serial Monitor / Plotter – ใช้ดูข้อมูลที่บอร์ดส่งกลับมาหรือแสดงกราฟแบบเรียลไทม์
- ระบบจัดการบอร์ดและไลบรารี (Board Manager / Library Manager) – เพิ่มความสามารถใหม่ให้กับโปรเจกต์ เช่น รองรับบอร์ดใหม่หรือใช้งานเซ็นเซอร์เสริม

**Arduino IDE** ได้รับความนิยมเพราะใช้งานง่าย รองรับหลายแพลตฟอร์ม (Windows, macOS, Linux) และมีคอมมูนิตี้ใหญ่ที่แบ่งปันโค้ดและตัวอย่างมากมาย ทำให้เหมาะทั้งกับมือใหม่และผู้พัฒนา IoT ระดับมืออาชีพ

![arduino-ide-guide-board](https://devadiy.com/wp-content/uploads/elementor/thumbs/arduino-ide-guide-board-ra3kx4d83gutc4sd2takzltpvw6keg2q927f5poxo0.webp "arduino-ide-guide-board")

### 1\. บอร์ดตระกูล Arduino

เช่น

- Arduino UNO / UNO R4
- Arduino Nano / Nano Every / Nano 33 IoT
- Arduino Mega 2560
- Arduino Leonardo
- Arduino MKR Series

ข้อดีคือ ติดตั้งเสร็จแล้วใช้งานได้ทันที ไม่ต้องเพิ่มบอร์ดเสริม (เพราะ Arduino IDE มีแพ็กเกจติดมาให้แล้ว)

### 2\. ESP32

บอร์ดยอดนิยมสำหรับงาน IoT เพราะมี WiFi และ Bluetooth ในตัว พร้อมสเปกแรงกว่า Arduino UNO หลายเท่า  
ตัวอย่างบอร์ดยอดนิยม เช่น

- ESP32 DevKit V1 (DOIT)
- ESP32 WROOM / WROVER
- ESP32-S3 / ESP32-C3 (รุ่นใหม่ รองรับ AI และ USB ในตัว)

การใช้งานต้องติดตั้ง ESP32 Board Manager เพิ่ม โดยสามารถติดตั้งได้จาก Preferences → Additional Board Manager URLs แล้วเพิ่มลิงก์:

https://espressif.github.io/arduino-esp32/package\_esp32\_index.json

### 3\. ESP8266 (รุ่นเล็กของ ESP32)

- NodeMCU v2/v3
- Wemos D1 Mini  
	เหมาะสำหรับงาน IoT ขนาดเล็ก ราคาประหยัด

### 4\. บอร์ดอื่น ๆ

เช่น STM32, Teensy, Raspberry Pi Pico (RP2040) และบอร์ดตระกูลอื่นที่มีแพ็กเกจสำหรับ Arduino IDE.

![](https://devadiy.com/wp-content/uploads/2025/08/arduino-ide-guide-download.webp)
![](https://www.youtube.com/watch?v=wcEJk1ui0UA)

### 1\. ดาวน์โหลด Arduino IDE

1. เปิดเว็บทางการ: [https://www.arduino.cc/en/software](https://www.arduino.cc/en/software)
2. เลือกเวอร์ชันที่ต้องการ (แนะนำ Arduino IDE 2.x รุ่นใหม่ ใช้งานง่ายและเร็วกว่าเวอร์ชัน 1.x)
3. เลือกระบบปฏิบัติการของคุณ:
- - Windows – เลือก Windows Installer (.exe) หรือ Portable Zip
		- macOS – ดาวน์โหลดไฟล์.zip หรือ.dmg
		- Linux – เลือกแพ็กเกจ.AppImage,.tar.xz หรือใช้คำสั่งติดตั้งผ่าน Terminal

### 2\. ติดตั้งบน Windows

1. ดับเบิลคลิกไฟล์ Arduino-IDE-Installer.exe
2. กด I Agree และเลือก Next ไปจนจบ
3. หลังติดตั้งเสร็จ สามารถเปิดโปรแกรมจาก Start Menu

### 3\. ติดตั้งบน macOS

1. แตกไฟล์.zip หรือเปิดไฟล์.dmg
2. ลากไอคอน Arduino IDE ไปไว้ใน Applications
3. เปิดโปรแกรมครั้งแรก อาจต้องอนุญาตการรัน (System Preferences → Security & Privacy)

### 4\. ติดตั้งบน Linux

1. ดาวน์โหลดไฟล์.AppImage หรือ.tar.xz
2. ถ้าเป็น.AppImage ให้ตั้งค่า Permission → Allow Executable แล้วดับเบิลคลิกเพื่อรัน
3. ถ้าเป็น.tar.xz ให้แตกไฟล์ และรันสคริปต์ install.sh ผ่าน Terminal

### 5\. ตรวจสอบการทำงาน

- เปิด Arduino IDE → ไปที่ File → Examples → 01.Basics → Blink
- เลือกบอร์ดและพอร์ต → กด Upload → ถ้าไฟกระพริบบนบอร์ด แสดงว่าพร้อมใช้งาน

![ขั้นตอนเพิ่ม URL และติดตั้ง ESP32 Board Manager ใน Arduino IDE พร้อมภาพหน้าจอ Preferences และ Board Manager](https://devadiy.com/wp-content/uploads/2025/08/arduino-ide-guide-install-board-manager.webp)

### 1\. เปิด Arduino IDE

ใช้ได้ทั้ง Arduino IDE 1.x และ 2.x แต่แนะนำ 2.x เพราะใช้งานง่ายกว่า

### 2\. เพิ่ม URL สำหรับ ESP32 Board Manager

1. ไปที่เมนู File → Preferences (Windows/Linux) หรือ Arduino IDE → Preferences (macOS)
2. ในช่อง Additional Board Manager URLs ให้ใส่ลิงก์นี้:  
	https://espressif.github.io/arduino-esp32/package\_esp32\_index.json
3. ถ้ามี URL อื่นอยู่แล้ว ให้กดปุ่ม ไอคอนรูปหน้า (หรือปุ่มลูกศร) เพื่อใส่หลายบรรทัด

### 3\. ติดตั้ง ESP32 Board Package

1. ไปที่ Tools → Board → Board Manager
2. ค้นหา esp32
3. กด Install ที่แพ็กเกจ “esp32 by Espressif Systems”
4. รอให้ติดตั้งเสร็จ (อาจใช้เวลาสักครู่)

### 4\. เลือกบอร์ด ESP32 ที่ต้องการใช้งาน

- ไปที่ Tools → Board แล้วเลือกบอร์ด เช่น
	- ESP32 Dev Module
		- ESP32-WROOM-DA Module
		- ESP32-S3 Dev Module

![](https://devadiy.com/wp-content/uploads/2025/08/arduino-ide-guide-structure.webp)

### 1\. setup()

- ใช้สำหรับตั้งค่าเริ่มต้น เช่น
	- กำหนดโหมดของขา GPIO (INPUT/OUTPUT)
		- เริ่มการสื่อสาร Serial
		- เชื่อมต่อ WiFi หรือเริ่มทำงานเซนเซอร์
- จะรันเพียง ครั้งเดียว หลังจากเปิดเครื่องหรือรีเซ็ต

ตัวอย่าง:

void setup() {  
pinMode(2, OUTPUT); // ตั้งค่า GPIO2 เป็น OUTPUT  
Serial.begin(115200); // เริ่ม Serial Monitor  
Serial.println(“Start!”);  
}

### 2\. loop()

- ใช้สำหรับคำสั่งที่ต้องทำงานซ้ำ เช่น
	- อ่านค่าจากเซนเซอร์ทุก 1 วินาที
		- กระพริบไฟ LED
		- ตรวจสอบสถานะปุ่มกด
- จะรันซ้ำไปเรื่อย ๆ จนกว่าบอร์ดจะหยุดทำงาน

ตัวอย่าง:

void loop() {  
digitalWrite(2, HIGH); // เปิด LED  
delay(1000); // รอ 1 วินาที  
digitalWrite(2, LOW); // ปิด LED  
delay(1000); // รอ 1 วินาที  
}

### 1\. อุปกรณ์ที่ใช้

- บอร์ด Arduino UNO หรือ ESP32
- สาย USB สำหรับเชื่อมต่อกับคอมพิวเตอร์
- (ถ้าใช้ LED แยก) หลอด LED + ตัวต้านทาน 220Ω

> หมายเหตุ: บอร์ด Arduino UNO ใช้ LED ในตัวที่ขา 13, ส่วน ESP32 DevKit V1 ใช้ LED ในตัวที่ขา GPIO 2

### 2\. เขียนโค้ด Blink LED

void setup() {  
pinMode(2, OUTPUT); // กำหนด GPIO 2 เป็น OUTPUT  
}

void loop() {  
digitalWrite(2, HIGH); // เปิด LED  
delay(1000); // รอ 1 วินาที  
digitalWrite(2, LOW); // ปิด LED  
delay(1000); // รอ 1 วินาที  
}

- pinMode(2, OUTPUT); → กำหนดให้ขา 2 เป็นเอาต์พุต
- digitalWrite(2, HIGH); → เปิดไฟ LED
- delay(1000); → หน่วงเวลา 1 วินาที (1000 ms)

### 1\. เชื่อมต่อบอร์ดกับคอมพิวเตอร์

- ใช้สาย USB (เช่น USB Type-A to Micro-USB หรือ Type-C ตามรุ่นบอร์ด)
- ตรวจสอบว่าไฟบนบอร์ดติด แสดงว่ามีไฟเลี้ยงแล้ว

### 2\. เลือกบอร์ด (Board)

- ไปที่ Tools → Board
- เลือกรุ่นบอร์ดที่ใช้ เช่น
	- Arduino UNO
		- ESP32 Dev Module
		- ESP32-S3 Dev Module

### 3\. เลือกพอร์ต (Port)

- ไปที่ Tools → Port
- เลือกพอร์ตที่มีชื่อบอร์ดแสดง เช่น COM3 (Arduino UNO) หรือ /dev/ttyUSB0 บน Linux/Mac
- ถ้าไม่เจอพอร์ต ให้ติดตั้งไดรเวอร์ (เช่น CH340, CP2102)

### 5\. ทดสอบการทำงาน

- ถ้าเป็นโค้ด Blink LED → ดูว่าไฟกระพริบตามที่ตั้งค่าไว้
- ถ้าเป็นโค้ดอ่านเซนเซอร์ → เปิด Serial Monitor เพื่อตรวจสอบค่า

### 1\. การเปิด Serial Monitor

1. อัปโหลดโค้ดลงบอร์ดให้เรียบร้อย
2. ไปที่เมนู Tools → Serial Monitor หรือกดปุ่ม แว่นขยาย ที่มุมขวาบนของ Arduino IDE
3. เลือก Baud Rate ให้ตรงกับที่ตั้งไว้ในโค้ด เช่น 9600 หรือ 115200

### 2\. การตั้งค่าในโค้ด

ก่อนใช้งาน Serial Monitor ต้องเริ่มการสื่อสารอนุกรมในฟังก์ชัน setup() ด้วยคำสั่ง

Serial.begin(115200); // เริ่มสื่อสารที่ความเร็ว 115200 bps

จากนั้นใช้คำสั่ง

- Serial.print(“ข้อความ”); → แสดงข้อความต่อเนื่อง
- Serial.println(“ข้อความ”); → แสดงข้อความแล้วขึ้นบรรทัดใหม่

### 3\. ตัวอย่างโค้ดทดสอบ

void setup() {  
Serial.begin(115200); // เริ่ม Serial Monitor  
Serial.println(“เริ่มต้นการทำงาน…”);  
}

void loop() {  
int sensorValue = analogRead(34); // อ่านค่าจากขา ADC 34  
Serial.print(“Sensor Value: “);  
Serial.println(sensorValue);  
delay(1000); // รอ 1 วินาที  
}

**คำอธิบาย:**

- เมื่อเปิด Serial Monitor จะเห็นข้อความ “เริ่มต้นการทำงาน…”
- จากนั้นจะแสดงค่าจากเซนเซอร์ทุก 1 วินาที

### 4\. การใช้งานร่วมกับ Serial Plotter

นอกจากดูเป็นข้อความแล้ว ยังใช้ Serial Plotter เพื่อแสดงค่าเป็นกราฟแบบเรียลไทม์ได้ที่ Tools → Serial Plotter

**💡 Tip:**

- ถ้าเปิด Serial Monitor ไม่เจอข้อมูล ให้ตรวจสอบว่า Baud Rate ในโปรแกรมและในโค้ดตรงกัน
- ใช้ Serial.print() และ Serial.println() อย่างพอดี ไม่ควรส่งข้อมูลถี่เกินไปเพราะจะทำให้บอร์ดหน่วง

![หน้าต่าง Library Manager ของ Arduino IDE แสดงขั้นตอนค้นหาและติดตั้งไลบรารี DHT sensor พร้อมปุ่ม Install](https://devadiy.com/wp-content/uploads/2025/08/arduino-ide-guide-install-library.webp)

### 1\. การติดตั้งจาก Library Manager (แนะนำ)

1. เปิด Arduino IDE
2. ไปที่ Sketch → Include Library → Manage Libraries…
3. ในช่องค้นหา พิมพ์ชื่อไลบรารีที่ต้องการ เช่น DHT sensor หรือ ESPAsyncWebServer
4. เลือกเวอร์ชันล่าสุด แล้วกด Install
5. รอจนขึ้น “Installed” แล้วใช้งานได้ทันที

### 2\. การติดตั้งจากไฟล์ ZIP

ใช้ในกรณีที่ดาวน์โหลดไลบรารีจาก GitHub หรือเว็บไซต์อื่น

1. ดาวน์โหลดไฟล์.zip ของไลบรารี
2. ใน Arduino IDE ไปที่ Sketch → Include Library → Add.ZIP Library…
3. เลือกไฟล์.zip ที่ดาวน์โหลดมา
4. ไลบรารีจะถูกเพิ่มเข้ามาอัตโนมัติ

### 3\. การลบหรืออัปเดตไลบรารี

1. เปิด Library Manager
2. ค้นหาไลบรารีที่ต้องการลบ → คลิก Remove
3. ถ้าต้องการอัปเดต → เลือกเวอร์ชันใหม่แล้วกด Update

#### 4\. ตัวอย่างการใช้งานไลบรารี DHT

#include “DHT.h”

#define DHTPIN 4 // ขา DATA ต่อ GPIO4  
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

void setup() {  
Serial.begin(115200);  
dht.begin();  
}

void loop() {  
float t = dht.readTemperature();  
float h = dht.readHumidity();

Serial.print(“Temp: “);  
Serial.print(t);  
Serial.print(“°C Humidity: “);  
Serial.print(h);  
Serial.println(“%”);  
delay(2000);  
}

**💡 Tip:**

- เลือกไลบรารีจากผู้พัฒนาที่เชื่อถือได้ (เช่นของ Adafruit, Espressif)
- ควรอัปเดตไลบรารีสม่ำเสมอเพื่อแก้บั๊กและเพิ่มฟีเจอร์ใหม่

**Q2: Arduino IDE รองรับบอร์ดอะไรบ้าง?**  
A: รองรับบอร์ด Arduino ทุกตระกูล และบอร์ดจากผู้ผลิตอื่น เช่น ESP32, ESP8266, STM32, Raspberry Pi Pico

**Q3: Arduino IDE ใช้ภาษาอะไรเขียนโปรแกรม?**  
A: ใช้ภาษา C/C++ เป็นหลัก แต่มีฟังก์ชันของ Arduino Framework ช่วยให้เขียนง่ายขึ้น

**Q4: Arduino IDE 1.x กับ 2.x ต่างกันอย่างไร?**  
A: เวอร์ชัน 2.x ใช้ UI แบบใหม่, เร็วกว่า, มีระบบ Auto-complete และการจัดการไฟล์โปรเจกต์ที่ดีกว่า

**Q5: ต้องติดตั้งอะไรเพิ่มเพื่อใช้กับ ESP32?**  
A: ต้องเพิ่ม URL ใน Board Manager และติดตั้งแพ็กเกจ “esp32 by Espressif Systems”

**Q7: Arduino IDE ใช้กับมือถือได้ไหม?**  
A: ได้ ถ้าใช้แอป ArduinoDroid (Android) หรือ Arduino Cloud แต่จะไม่สะดวกเท่าเวอร์ชัน PC

**Q8: อัปโหลดโค้ดแล้วขึ้น Error ต้องทำอย่างไร?**  
A: ตรวจสอบสาย USB, พอร์ตที่เลือก, ไดรเวอร์ และกดปุ่ม BOOT บน ESP32 ตอนเริ่มอัปโหลด

**Q9: ติดตั้งไลบรารีจาก GitHub ยังไง?**  
A: ดาวน์โหลดไฟล์.zip → Sketch → Include Library → Add.ZIP Library…
