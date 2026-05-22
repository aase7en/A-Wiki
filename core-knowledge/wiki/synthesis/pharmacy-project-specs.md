# Project Specs: Pharmacy Order Checker

## 1. เป้าหมาย (Goal)
สร้างระบบ AI Assistant ที่ช่วยให้คุณศุภศิษฎิ์ (เจ้าของร้านภูฟาร์มาซี) สามารถตรวจสอบรายการสั่งยาที่ลูกน้องส่งมาทาง Line ได้อย่างรวดเร็วและแม่นยำ 100% โดยลดเวลาในการเปิด Catalog กระดาษหรือค้นหาไฟล์ PDF

## 2. ขอบเขตงาน (Scope)
- **Input**: ข้อความ Text จาก Line (ที่สะกดผิด/ใช้ชื่อเล่น) หรือรูปภาพลายมือรายการยา
- **Processing**: ใช้ Claude API (Vision + Text) ในการทำ OCR และ Fuzzy Matching กับฐานข้อมูลยาหลัก
- **Database**: อ้างอิงไฟล์ `raw/pharmacy/sp_drugs_full_3760.json` และ `wiki/concepts/pharmacy/drug-aliases.md`
- **Output**: ตารางที่ระบุ ชื่อยาที่ถูกต้อง, ขนาด (Strength), หน่วยสั่งซื้อ (Unit), และจำนวน (Qty) เพื่อเตรียมส่งสั่งซื้อกับ Supplier (เอสพีดรักสโตร์)

## 3. มาตรฐานความสำเร็จ (Success Criteria - Tip #10)
- AI ต้องสามารถ Match ชื่อยาที่เป็น "ชื่อเล่น" (เช่น อม็อก, พารา) ได้ถูกต้อง > 95%
- ระบบต้องระบุ "หน่วยสั่งซื้อ" (กล่อง/ขวด/กระปุก) ได้ตรงตามระบบของร้านภูฟาร์มาซี
- มี Form สำหรับให้เจ้าของร้านตรวจสอบและแก้ไขข้อมูลก่อน Export

## 4. แผนการดำเนินงาน (Phases)
(อ้างอิงจาก [[wiki/synthesis/pharmacy-order-checker]])
- Phase 1: Data Preparation (Done)
- Phase 2: Simple Web Validation (Current)
- Phase 3: OCR Integration
- Phase 4: Export System

## 5. เอกสารอ้างอิง
- [[wiki/concepts/pharmacy/pharmacy-context]]
- [[wiki/concepts/pharmacy/drug-aliases]]
- [[wiki/synthesis/pharmacy-order-checker]]
