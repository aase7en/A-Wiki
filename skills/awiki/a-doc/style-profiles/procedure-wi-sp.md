# Style Profile: WI/SP/WP Procedure (คู่มือมาตรฐาน QA)

> Quality Assurance document — Work Instruction / Standard Procedure / Work Procedure
> Pattern จาก `WI-EOH-001-00`, `SP-EOH-002-00`, `WP-ENV-001` (ไฟล์จริงใน `_uThaiHos`)
> ใช้กับ: types/procedure/
> Verified: 2026-07-16

## Code convention

- **WI** = Work Instruction (คำสำคัญ: วิธีปฏิบัติงาน)
- **SP** = Standard Procedure (คำสำคัญ: มาตรฐาน/แนวทาง)
- **WP** = Work Procedure (คำสำคัญ: กระบวนการทำงาน)
- Format: `WI-<DEPT>-<NNN>-<REV>` เช่น `WI-EOH-001-00`
  - EOH = Environmental & Occupational Health
  - ENV = Environmental
  - NNN = running number
  - REV = revision (00 = first)

## Page Setup

เหมือน gov-letter-standard (A4, L3cm/R2cm) แต่เพิ่ม:
- **Header**: โลโก้ รพ. + ชื่อเอกสาร + document code
- **Footer**: เลขหน้า + revision date

## Font

เหมือน hospital-announce.md (TH SarabunIT๙ หรือ SarabunPSK)
- Heading 1 (หัวข้อหลัก): 16pt bold
- Heading 2 (1.0, 2.0): 14pt bold
- Heading 3 (1.1, 1.2): 14pt bold
- Normal: 14pt

## Document structure (QA standard — 6 sections บังคับ)

```
[โลโก้ + ตราครุฑ]
คู่มือ/วิธีปฏิบัติงาน...
รหัสเอกสาร: WI-EOH-001-00          ฉบับที่: 00
หน้า 1/XX                          วันที่บังคับใช้: X ม.ค. 2569

1. วัตถุประสงค์ (Purpose)
   <1-2 ย่อหน้า — ทำไมต้องมีคู่มือนี้>

2. ขอบเขต (Scope)
   <ใช้กับหน่วยงาน/บุคคลใดบ้าง>

3. นิยามและตัวย่อ (Definitions)
   3.1 <คำศัพท์> หมายถึง ...
   3.2 ...

4. ขั้นตอนการปฏิบัติงาน (Procedure)
   4.1 <ขั้นตอนที่ 1>
       - <รายละเอียด>
       - <flowchart ถ้ามี>
   4.2 <ขั้นตอนที่ 2>
   ...

5. เอกสารอ้างอิง (References)
   5.1 <กฎหมาย/ระเบียบ>
   5.2 <คู่มืออื่น>

6. บันทึก (Records)
   6.1 <แบบฟอร์ม> รหัส <XXX-NNN>
   6.2 ...

[ตาราง revision history ท้ายเอกสาร]
| ฉบับที่ | วันที่ | รายละเอียดการแก้ไข | ผู้แก้ |
|---|---|---|---|
| 00 | DD/MM/BBBB | เอกสารใหม่ | ชื่อ |
```

## docx-js structure

```javascript
const doc = new Document({
  styles: {/* same as hospital-announce */},
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 1134, bottom: 1134, left: 1701, right: 1134,
                  header: 567, footer: 567 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "WI-EOH-001-00 ฉบับที่ 00", size: 20 })]
          })
        ]
      })
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ text: "หน้า ", size: 20 }),
              new PageNumber(),
              new TextRun({ text: " วันที่บังคับใช้: ", size: 20 }),
              // thai-date-format
            ]
          })
        ]
      })
    },
    children: [
      // 6 sections above
    ]
  }]
});
```

## Examples จากไฟล์จริง

| Code | หัวข้อ | ที่มา |
|---|---|---|
| WI-EOH-001-00 | ระบบบำบัดน้ำเสียใน รพ.อุทัย | `_uThaiHos/05_Finance_Admin_07_Policies_/_QA/` |
| SP-EOH-002-00 | การดูแลจัดเก็บและขนย้ายมูลฝอย | same |
| WP-ENV-001 | วิธีปฏิบัติงานมูลฝอย | `_uThaiHos/05_Finance_Admin_07_Policies_/_คู่มือปฏิบัติงาน/` |
| WP-ENV-002 | วิธีปฏิบัติงานระบบบำบัดน้ำเสีย | same |

## Notes

- QA document ต้องผ่าน approval (ผอ. + ผู้เชี่ยวชาญ) — ระบุใน SKILL ว่าต้องมีช่องลายเซ็นอนุมัติ
- Revision tracking บังคับ — ทุกครั้งที่แก้ ต้องบันทึกใน revision history table
- ใช้กับ HA Standard (Healthcare Accreditation) audit — ต้องตรง format ตัวอักษร
