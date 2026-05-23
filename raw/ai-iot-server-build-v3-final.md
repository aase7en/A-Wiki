# Personal AI & IoT Server Build List (v3)

> Source: `AI_IoT_Server_Build_v3_Final.pdf` (ผู้ใช้ส่งจาก Downloads/ — สร้างโดย AI Assistant)
> วันที่อ้างอิง: พฤษภาคม 2026
> วันที่ ingest: 2026-05-05

สเปกคอมพิวเตอร์ระดับสูงสำหรับการทำงาน 24/7 รองรับ:
- Local LLM (70B+)
- IoT Monitoring
- AI Agent
- Web Server
- 4K Entertainment

## Build List

| อุปกรณ์ | รุ่นที่แนะนำ | ราคาโดยประมาณ (บาท) |
|---|---|---|
| CPU | AMD Ryzen 7 9700X (Eco Mode 65W) | 12,000 |
| Mainboard | ASRock B860M Pro RS (4x RAM Slots) | 5,500 |
| RAM | 128GB (32GB x 4) Kingston FURY Beast DDR5 5600MHz | 20,000 |
| GPU | NVIDIA RTX 4070 Ti Super (16GB VRAM) *ความยาว < 270mm | 34,000 |
| SSD (OS/AI) | 2TB NVMe PCIe Gen 4.0 (Samsung 990 Pro) | 5,000 |
| HDD (Data/IoT) | 8TB WD Red Plus / Seagate IronWolf (NAS Grade 24/7) | 8,500 |
| Case | Jonsbo TK-1 v2 (ตู้ปลาจิ๋ว กระจกโค้ง 270 องศา) | 5,000 |
| PSU | Cooler Master V750 SFX Gold (SFX Form Factor) | 5,000 |
| Cooler | Noctua NH-L9x65 (Silent Profile) | 3,500 |

**รวมงบประมาณโดยประมาณ: 98,500 บาท**

## Technician & Shop Checklist (สิ่งที่ต้องกำชับช่าง)

1. **การตรวจสอบแรม (Critical)**: รบกวนทำการทดสอบ Memtest86 อย่างน้อย 4 ชั่วโมง (ใส่เต็ม 4 แถว) เพื่อให้มั่นใจว่าระบบเสถียรสำหรับการเปิดรัน AI และ IoT ทิ้งไว้ตลอด 24/7
2. **การตั้งค่า BIOS**: ช่วยอัปเดต BIOS เป็นรุ่นล่าสุด และตั้งค่า AMD Eco Mode (65W TDP) เพื่อความเย็นและประหยัดไฟสูงสุด รวมถึงตั้ง XMP/EXPO ที่ 5200-5600MHz
3. **การเลือกการ์ดจอ**: เคส TK-1 v2 มีพื้นที่จำกัด รบกวนเลือกตัวการ์ดที่มี **ความยาวไม่เกิน 270-280mm** (แนะนำรุ่น 2 พัดลม)
4. **การจัดเก็บข้อมูล**: รบกวนใช้ HDD Grade NAS (24/7) เท่านั้นสำหรับลูก 8TB เพื่อรองรับการเขียนข้อมูล Data Monitor ของ IoT ตลอดเวลา
5. **การจัดสายไฟ**: เคสมีกระจกใสโชว์รอบด้าน รบกวนจัดสายไฟ (Cable Management) ให้สวยงามและไม่บังทางลมระบายอากาศ
6. **ความเงียบ (Silent Operation)**: ปรับแต่ง Fan Curve ให้พัดลมหมุนเบาที่สุดในสภาวะปกติ เพื่อไม่ให้รบกวนเวลาพักผ่อนในบ้าน

---

*สร้างโดย AI Assistant เพื่อเป็นแนวทางประกอบคอมพิวเตอร์ระดับสูงประจำเดือน พฤษภาคม 2026*
