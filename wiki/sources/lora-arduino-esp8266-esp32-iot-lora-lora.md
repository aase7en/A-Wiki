---
tags: [lora, arduino, esp8266, esp32, iot]
type: source
title: "#1 LoRa Arduino ESP8266 ESP32 IoT อะไรคือ LoRa ใช้งาน LoRa อย่างไร"
slug: lora-arduino-esp8266-esp32-iot-lora-lora
date_ingested: 2026-05-24
original_file: raw/1 LoRa Arduino ESP8266 ESP32 IoT อะไรคือ LoRa ใช้งาน LoRa อย่างไร.md
---

```yaml
---
title: "#1 LoRa Arduino ESP8266 ESP32 IoT อะไรคือ LoRa ใช้งาน LoRa อย่างไร"
source: "https://www.allnewstep.com/article/136/1-lora-arduino-esp8266-esp32-iot-%E0%B8%AD%E0%B8%B0%E0%B9%84%E0%B8%A3%E0%B8%84%E0%B8%B7%E0%B8%AD-lora-%E0%B9%83%E0%B8%8A%E0%B9%89%E0%B8%87%E0%B8%B2%E0%B8%99-lora-%E0%B8%AD%E0%B8%A2%E0%B9%88%E0%B8%B2%E0%B8%87%E0%B9%84%E0%B8%A3"
author: ""
published: ""
created: "2026-04-18"
description: "#1 LoRa Arduino ESP8266 ESP32 IoT อะไรคือ LoRa แล้วใช้งาน LoRa อย่างไรเราจะมารู้จักกับ LoRa และวิธีใช้งานร่วมกับ Arduino โปรเจกอะไรคือ LoRa ?LoRa คือช..."
tags: ""
---
```

[](https://www.allnewstep.com/)

พิมพ์ค้นหาบทความ หัวข้อกระทู้ และสินค้าในเว็บ AllNewStep ได้ที่นี่

Custom Search

|  | จัดเรียงตาม  Relevance  Date |
| --- | --- |

  
  
เราจะมารู้จักกับ LoRa และวิธีใช้งานร่วมกับ Arduino โปรเจก  
  
**อะไรคือ LoRa?**  
LoRa คือชื่อเรียกของเทคโนโลยี่การมอดูเลชั่น เพื่อเข้ารหัสข้อมูลกับสัญญาณทางไฟฟ้าส่งออกในรูปแบบของคลื่นความถี่วิทยุ โดยวิธีการนี้เป็นลิขสิทธิ์ของบริษัท Semtech และเป็นผู้ผลิตชิฟ สำหรับส่งข้อมูลสื่อสารไร้สายแบบ LoRa  
  
  
คำว่า LoRa ย่อมาจากคำว่า Long Range = LoRa เป็นชื่อที่ใช้เรียกอุปกรณ์ที่มีการสื่อสารแบบ LoRa ซึ่งสามารถสร้างการสื่อสารแบบนี้ได้โดยใช้ชิฟ Semtech LoRa Chip  
  
เทคนิคการมอดูเลชัน LoRa นี้ช่วยให้สามารถสื่อสารข้อมูลในปริมาณน้อยหรือแบนด์วิธต่ำ ได้ในระยะไกล มีความสามารถในการป้องกันสัญญาณรบกวนได้สูง และใช้พลังงานต่ำ  
  
  
ความถี่ของ LoRa  
LoRa ใช้ความถี่ที่ไม่มีลิขสิทธิ์ ซึ่งแต่ละที่จะมีช่องความถี่ที่อนุญาตให้ใช้งาน แตกต่างกันออกไป  
  
- 868 Mhz สำหรับยุโรป
- 915 Mhz สำหรับอเมริกาเหนือ
- 433 Mhz สำหรับเอเชีย

สำหรับในประเทศไทยสามารถใช้ได้ในช่วง 433Mhz และ 915Mhz โดยเอกสารข้อกำหนด IoT ในประเทศไทย [สามารถอ่านได้ที่นี่](http://spectrum.nbtc.go.th/eventreg/iot2017/docs/02_iot_trends_and_spectrum.pdf)  
ล่าสุด กสทช. ได้อนุญาตให้ใช้งาน LoRa ในช่วงความถี่ 920-925Mhz กำลังส่งสูงสุดถึง 4W เอกสารข้อกำหนด [สามารถอ่านได้ที่นี่](http://www.ratchakitcha.soc.go.th/DATA/PDF/2560/E/289/51.PDF)  
  
**LoRa แอพพลิเคชั่น**

LoRa ส่งข้อมูลได้ระยะไกล ใช้พลังงานน้อย ฟีเจอร์นี้เหมาะเป็นอย่างมากสำหรับเซนเซอร์ที่ใช้พลังงานต่ำ เช่น IoT, สมาร์ทฟาร์ม, การสื่อสารระหว่างเครื่องจักร  
  
  
ดังนั้น LoRa จึงเป็นตัวเลือกที่ดีสำหรับ โหนดเซนเซอร์ ทำงานได้เพียงแค่แบตเตอร์รี่ก้อนเล็ก ๆ ก้อนเดียว หรือแม้กระทั้งใช้พลังงานจากโซล่าเซลล์ ก็สามารถส่งข้อมูลข้อมูลเล็ก ๆ ระหว่างอุปกรณ์ได้  
  
  
**LoRa ไม่เหมาะสำหรับโปรเจกที่**

- ต้องการส่งข้อมูลจำนวนมาก
- มีการส่งข้อมูลบ่อย ๆ
- เชื่อมต่อกับเครือข่ายสื่อสารจำนวนมาก
**รูปแบบการใช้งาน LoRa**  
  
สามารถใช้ LoRa ในรูปแบบ  
- สื่อสารแบบ Point to Point
- สื่อสารแบบเครือข่าย LoRa network โดยใช้ LoRaWAN
  
การสื่อสารแบบ Point to Point  
  
การสื่อสารแบบ LoRa สามารถส่งข้อมูลได้ไกลกว่า Wi-Fi หรือ Bluetooth  
  
  
การส่งข้อมูลผ่าน Wi-Fi ได้โดยทั่วไปได้ระยะประมาณ 100-200 เมตร ในขณะที่ LoRa สามารถส่งข้อมูลได้มากกว่า 30 กิโลเมตร  
  
**LoRaWAN**  
เราสามารถสร้างเน็ตเวอร์ค LoRa ได้ โดยใช้ LoRaWNA  
  
โปรโตคอล LoRaWAN เป็นข้อกำหนดด้านเครือข่ายพลังงานต่ำ (LPWAN) ที่ได้จากเทคโนโลยี LoRa ที่ได้รับการรับรองโดย [LoRa Alliance](https://www.lora-alliance.org/technology)  
  
**สถาปัตยกรรม LoRaWAN Network**  
LoRa network ประกอบด้วย 4 ส่วนคือ  
- Device: อุปกณ์/เซนเซอร์ ส่งสัญญาณแบบ LoRa
- gateways: อุปกรณ์รับข้อมูลแบบ LoRa
- Network server: สำหรับส่งข้อมูลขึ้นบน server
- Application: สำหรับประมวลผล/แสดงผลข้อมูล
  
  
**การใช้งาน LoRa กับโปรเจก IoT**  
สมมุติว่าเราต้องการสร้างเครื่องวัดอุณหภูมิ/ความชื้นในฟาร์มนอกบ้าน ซึ่งมีระยะไกลมาก สัญญาณ Wi-Fi ส่งไปไม่ถึง ดังนั้นอุปกรณ์ ESP8266/ESP32 IoT จึ่งส่งข้อมูลมาไม่ได้  
  
วิธีแก้คือ ต่อ LoRa กับอุปกรณ์ IoT เรียกว่า Device  
จากนั้นส่งมายัง อุปกรณ์ ESP8266/ESP32 ที่เป็นตัวรับข้อมูล และต่อในระยะที่ Wi-Fi สัญญาณถึง เรียกส่วนนี้ว่า GATEWAY  
  
เมื่อ GATEWAY ได้รับข้อมูล ก็จะส่งขึ้น Server  
เมื่อเปิดดูในส่วนของ Application โปรแกรมสำหรับประมวลผล/แสดงผล ก็จะเห็นข้อมูลอุณหภูมิ/ความชื่นในฟาร์มนอกบ้าน  
  
  
**ข้อมูลเพิ่มเติม LoRa**  
- [LoRa for IoT (epanorama website)](http://www.epanorama.net/newepa/2017/03/24/lora-for-iot/)
- [LoRa vs LoRaWAN (libelium website)](http://www.libelium.com/development/waspmote/documentation/lora-vs-lorawan/)
- [The Things Network Kickstarter page](https://www.kickstarter.com/projects/419277966/the-things-network)
- [The limits of LoRaWAN (paper)](https://arxiv.org/pdf/1607.08011.pdf)

## อ่านต่อ วิธีใช้งาน LoRa รุ่น Ra-01, Ra-02, SX1278#2 LoRa Arduino ESP8266 ESP32 IoTการใช้งาน LoRa SX1278 Ra-01/Ra-02

  

พูดคุย-สอบถาม
