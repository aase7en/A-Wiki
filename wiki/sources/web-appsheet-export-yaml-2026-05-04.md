---
type: source
title: "web appsheet export yaml 2026 05 04"
slug: web-appsheet-export-yaml-2026-05-04
date_ingested: 2026-05-24
original_file: raw/web-appsheet-export-yaml-2026-05-04.md
---

```yaml
---
---
```

# วิธี Export AppSheet App Definition เป็น YAML / JSON

> ⚠️ PENDING REVIEW — เนื้อหานี้สรุปจากข้อมูลปี 2026 เพื่อใช้ในการวิเคราะห์โครงสร้างแอป

จากการค้นหาข้อมูล วิธีที่จะดึง "App Definition" (โครงสร้างตาราง, Virtual Columns และ Formulas) ออกมาในครั้งเดียวเพื่อให้อ่านง่าย (เช่น ในรูปแบบ YAML) มีแนวทางดังนี้:

## 1. วิธี Export ผ่านเมนู Manage (แบบทางการ)
แม้ AppSheet จะยังไม่มีปุ่ม "Export to YAML" โดยตรงใน Editor ปกติ แต่คุณสามารถทำได้ผ่านเมนูนี้:
*   **เมนู**: `Manage` -> `Author` -> `Export App`
*   **ผลลัพธ์**: คุณจะได้ไฟล์ `.json` ซึ่งบรรจุโครงสร้างทั้งหมดของแอป (App Spec)
*   **การแปลงเป็น YAML**: นำไฟล์ JSON ที่ได้ไปวางใน Online Converter (เช่น json2yaml.com) หรือส่งให้ AI (Gemini/Claude) แปลงเป็น YAML เพื่อให้อ่านง่ายขึ้น

## 2. วิธีดึงโครงสร้างแบบ "App Documentation" (แนะนำสำหรับมนุษย์อ่าน)
หากต้องการอ่าน Table + Virtual Columns + Formulas ได้ครบในหน้าเดียวโดยไม่ต้องแปลงไฟล์:
*   **เมนู**: `Settings` -> `Information` -> `App Documentation`
*   **ขั้นตอน**:
    1. คลิกที่ลิงก์ **"The documentation page for this app is available HERE"**
    2. หน้าเว็บจะแสดงโครงสร้างแอปทั้งหมดแบบละเอียด
    3. **Tip**: คุณสามารถ "Print to PDF" หรือ "Select All -> Copy" ข้อความทั้งหมดมาเก็บเป็นไฟล์ Text/YAML ได้ทันที

## 3. วิธีใช้ AppSheet Toolbox (Chrome Extension)
นี่เป็นวิธีที่นิยมที่สุดในหมู่ Developer:
*   ติดตั้ง Extension **AppSheet Toolbox**
*   ในหน้า Editor จะมีแถบเครื่องมือเพิ่มขึ้นมา
*   ไปที่แถบ **"Spec"** หรือ **"Documentation"** ใน Toolbox
*   คุณสามารถ Copy โครงสร้างที่เป็น JSON/YAML ของแต่ละตารางหรือทั้งแอปได้ง่ายกว่าเมนูมาตรฐาน

## 4. การดึงผ่าน Browser Console (Advanced)
หากต้องการ App Definition แบบ Real-time:
1. เปิด AppSheet Editor
2. กด `F12` เข้า Console
3. พิมพ์ `window.currentApp` (หรือตรวจสอบใน Network Tab หาคำว่า `GetAppDefinition`)
4. Copy JSON ที่ได้ไปแปลงเป็น YAML

### ข้อสังเกตสำหรับ Claude
- การใช้ YAML จะช่วยประหยัด Token ได้มากกว่า JSON เมื่อต้องส่งโครงสร้างแอปให้ AI วิเคราะห์
- ในไฟล์ Export จะไม่มี "ข้อมูล (Data)" ในตาราง มีเพียง "โครงสร้าง (Metadata)" เท่านั้น
- สูตร (Formulas) ใน Virtual Columns จะอยู่ในฟิลด์ `formula` หรือ `appFormula` ในไฟล์ JSON/YAML
