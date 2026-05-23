---
type: concept
tags: [tinyml, edge-ai, machine-learning, esp32, tensorflow-lite, anomaly-detection]
sources: [tinyml-esp32-applications, tinyml-esp32-tutorial, vaccine-cae-anomaly-detection]
created: 2026-04-18
updated: 2026-04-18
---

# TinyML (Edge AI)

## นิยาม

TinyML คือการรัน Machine Learning model บน microcontroller หรืออุปกรณ์ขนาดเล็ก (RAM < 1MB, power < 1mW) ทำให้อุปกรณ์ IoT ตัดสินใจได้เอง โดยไม่ต้องส่งข้อมูลไปประมวลผลที่ cloud

## ทำไมถึงสำคัญใน IoT

- **Latency ต่ำ**: ตัดสินใจ ms แทนที่จะรอ round-trip ไป cloud
- **Privacy**: ข้อมูล sensor ไม่ออกนอกอุปกรณ์
- **Offline**: ทำงานได้แม้ไม่มี internet
- **ประหยัดพลังงาน**: ไม่ต้องส่ง raw data ตลอดเวลา

## วิธีการทำงาน

```
[Training บน PC/Cloud]              [Inference บน ESP32]
TensorFlow → Train model            model.tflite → C array
           → Quantize (int8)    →   TFLite Micro → MicroInterpreter
           → Export .tflite         sensor data  → predict()
```

**Workflow ด้วย Edge Impulse:**
1. เก็บ sensor data → อัปโหลดขึ้น Edge Impulse
2. ออกแบบ signal processing pipeline
3. Train model (Neural Network / Anomaly Detection)
4. Export เป็น Arduino library
5. Flash ลง ESP32

## ตัวอย่าง Use Cases

| Use Case | Input Sensor | Model Type |
|----------|-------------|-----------|
| Anomaly detection ตู้แช่วัคซีน | DS18B20 / PT100 | Convolutional Autoencoder |
| ตรวจจับท่าทาง (gesture) | Accelerometer | Dense Neural Network |
| Electronic nose | MQ gas sensors | Classification |
| ตรวจจับไฟป่า | Temp + smoke + optical | Multi-input NN |
| Predictive maintenance | Vibration + temp | Anomaly detection |
| Voice control | Microphone | Keyword spotting |

## Performance บน ESP32

จากงานวิจัย vaccine cold chain (Frontiers AI 2024):
- Model: Convolutional Autoencoder, ~9,500 parameters
- Memory: 1.2 MB
- Inference time: 200ms ± 15ms
- Power: 50mW ± 5mW
- Accuracy: 92%

## Tools & Frameworks

| Tool | หน้าที่ |
|------|--------|
| **Edge Impulse** | end-to-end platform (เก็บ data → train → deploy) |
| **TensorFlow Lite Micro** | inference framework บน MCU |
| **Arduino TensorFlowLite.h** | library สำหรับ Arduino/ESP32 |
| **PlatformIO** | IDE ที่แนะนำสำหรับ TinyML project |

## ข้อจำกัด

- RAM จำกัด: ต้อง quantize model เป็น int8 (ลด accuracy เล็กน้อย)
- Training ยังต้องใช้ PC/Cloud — แค่ inference เท่านั้นที่ on-device
- Model ซับซ้อนมากไม่ได้ — ESP32 S3 (8MB PSRAM) รับได้มากกว่า ESP32 classic
- ต้องมี training data เพียงพอ

## ความสัมพันธ์

- Hardware ML workload สูง: [[entities/iot/esp32-s3]] (16MB Flash + 8MB PSRAM)
- Hardware gateway + Edge AI เบา: [[entities/iot/esp32-c6]] (WiFi 6 + Thread/Zigbee)
- IDE: [[entities/iot/platformio]]
- Use case: [[concepts/iot/cold-chain-monitoring]], Smart Farm (soil + LoRa + C6)

## แหล่งข้อมูล

- [[sources/tinyml-esp32-applications]] — 6 use cases บน ESP32
- [[sources/vaccine-cae-anomaly-detection]] — real research deployment
