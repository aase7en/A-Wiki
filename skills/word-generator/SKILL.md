# Skill: Word Generator (ตัวสร้างเอกสาร Word มาตรฐานไทย)

## 🎯 Overview
ความสามารถในการสร้างเอกสาร Microsoft Word (.docx) ที่ถูกต้องตามมาตรฐานงานสารบรรณไทย โดยเน้นการใช้ฟอนต์ **TH SarabunPSK** หรือ **TH Sarabun New** เป็นหลัก

## 🛠️ Tools & Technologies
- **Python (python-docx):** สำหรับสร้างและจัดการโครงสร้างไฟล์ Word
- **Custom Style Mapping:** การกำหนดค่า Style พื้นฐาน (Normal, Heading) ให้เป็นฟอนต์ไทยมาตรฐาน

## 📋 Workflow
1. **Define Content:** รับเนื้อหาที่ต้องการจัดทำเป็นเอกสาร
2. **Set Standard Font:** 
   - กำหนด Font Family: `TH SarabunPSK`
   - กำหนดขนาดตัวอักษร: เนื้อหา (16 pt), หัวข้อ (18 pt Bold)
3. **Format Layout:** ตั้งค่าขอบกระดาษ (Margins) ตามมาตรฐานราชการ (บน 2.5 ซม., ล่าง 2 ซม., ซ้าย 3 ซม., ขวา 2 ซม.)
4. **Generate Artifact:** สร้างไฟล์ `.docx` และส่งมอบให้ผู้ใช้

## 💡 Iron Laws (กฎเหล็ก)
- **Font Consistency:** ต้องบังคับใช้ TH SarabunPSK ทั้งเอกสาร (รวมถึงตารางและ Header/Footer)
- **Line Spacing:** ใช้ระยะบรรทัดแบบ Single หรือ 1.0 ตามความเหมาะสมของเนื้อหา
- **Thai Language Support:** ต้องรองรับการตัดคำภาษาไทยให้สวยงาม (ผ่านการตั้งค่า Alignment แบบ Justify)

## 📂 Code Snippet Example
```python
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
style = doc.styles['Normal']
font = style.font
font.name = 'TH SarabunPSK'
font.size = Pt(16)

p = doc.add_paragraph("ข้อความภาษาไทยมาตรฐาน")
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
```

---
*Created by Poppy Javis for Oh! Shit My Boss*
