# Skill: Assessment Generator (แบบประเมินสมรรถภาพมืออาชีพ)

## 🎯 Overview
ความสามารถในการสร้างแบบประเมินสมรรถภาพการทำงาน (Competency Assessment) ที่ครอบคลุมทั้งเกณฑ์การให้คะแนน (Rubrics), น้ำหนักคะแนน (Weighting) และแบบฟอร์มประเมินที่พร้อมใช้งานในรูปแบบ Excel และ PDF โดยเน้นการวิเคราะห์ตามบริบทจริงของงาน

## 🛠️ Tools & Technologies
- **Python (openpyxl):** สำหรับสร้างไฟล์ Excel ที่มีสูตรคำนวณอัตโนมัติ (บังคับใช้ฟอนต์ **TH Sarabun New**)
- **Markdown:** สำหรับร่างโครงสร้างเกณฑ์และเนื้อหา
- **manus-md-to-pdf:** สำหรับแปลงร่างเป็นเอกสาร PDF พร้อมพิมพ์

## 📋 Workflow
1. **Analyze Context:** วิเคราะห์บทบาทหน้าที่ของผู้รับการประเมิน (เช่น งานบ่อบำบัด, งานสวน, งานธุรการ)
2. **Define Weighting:** กำหนดน้ำหนักความสำคัญ (%) ตามความเสี่ยงและผลกระทบของงาน (Risk-Based Weighting)
3. **Draft Rubrics:** สร้างเกณฑ์คะแนน 1-5 ที่มีนิยามชัดเจน (Measurable Rubrics) เพื่อลดความลำเอียง
4. **Generate Artifacts:** 
   - สร้างไฟล์ Excel ที่มี Tab เกณฑ์คะแนน และ Tab แบบประเมิน
   - สร้างไฟล์ PDF ที่รวมเนื้อหาทั้งหมดไว้ในฉบับเดียว

## 💡 Iron Laws (กฎเหล็ก)
- **Data Integrity:** ต้องมีเกณฑ์ป้องกันการปลอมแปลงข้อมูล (Make Data)
- **Professional Layout:** ใช้โทนสี Teal หรือสีที่เหมาะสมกับองค์กรสาธารณสุข
- **User-Centric:** แบบฟอร์มต้องกรอกง่าย ไม่ซับซ้อน และคำนวณคะแนนให้อัตโนมัติ

## 📂 Example Structure
- `Criteria Tab`: น้ำหนักคะแนน 40/25/20/15
- `Assessment Tab`: หัวข้อประเมินรายข้อ + สูตร SUM คะแนน
- `PDF Export`: รวมคำอธิบายเกณฑ์และแบบฟอร์มไว้ในไฟล์เดียว

---
*Created by Poppy Javis for Oh! Shit My Boss*
