---
name: a-doc-announce
description: "ประกาศโรงพยาบาล / ประกาศนโยบาย — CANONICAL สมบูรณ์. Source: ประกาศนโยบายจริง (de-identified) (Poppy Javis analysis). Font TH SarabunIT๙, A4, margins L3cm/R2cm, ตราครุฑกลาง, ลำดับเลข 1./1.1. Trigger: 'ประกาศ', 'นโยบาย', 'policy', 'ประกาศนโยบาย'"
version: 1.0.0
author: A-Wiki (จากไฟล์ประกาศจริง (de-identified))
domain: [document, thai]
lifecycle_phase: build
category: pipeline
agents: [all]
invocation: manual
# 2026-07-23: both → manual — subskill เรียกจาก parent a-doc เท่านั้น ไม่ควร auto-load (ประหยัด ~1.3k tokens)
---

# A-Doc Type: Announce (ประกาศ)

ประกาศโรงพยาบาล — เอกสารที่ใช้ประกาศนโยบาย/แนวทาง มีลำดับเลขอย่างเป็นทางการ

## เมื่อไหร่ใช้

✅ Trigger: "ประกาศ", "นโยบาย", "policy", "ประกาศนโยบาย"
- ประกาศนโยบาย (พลังงาน, ความปลอดภัย, สิ่งแวดล้อม)
- ประกาศแนวทางปฏิบัติ

❌ ไม่ใช่ announce:
- คำสั่งแต่งตั้งคณะกรรมการ → `types/order/`
- บันทึกข้อความ → `types/memo/`

## ไฟล์ตัวอย่างใน `<WORK_DIR>`

| ไฟล์ | pattern |
|---|---|
| `20240711_นโยบายสิ่งแวดล้อม.pdf` | ประกาศนโยบาย |
| `20260306_นโยบายความปลอดภัยและสิ่งแวดล้อม.pdf` | ประกาศนโยบายรวม |
| ประกาศนโยบายจริง (de-identified) (analyzed) | canonical |

## Style profile

✅ ใช้ `style-profiles/hospital-announce.md` (default)
- Font: TH SarabunIT๙ (H1=16pt bold, H2=14pt bold+u, Body=14pt, Quote=12pt)
- Paper: A4, Margins L3cm/R2cm/Top1.75cm/Bottom2.54cm
- ตัวเลข: ไทย [๑๒๓]
- วันที่: พ.ศ.

## Structure (โครงเอกสาร)

```
[ตราครุฑ — กึ่งกลางหน้า บนสุด]

[หัวข้อประกาศ — H1 center bold 16pt]
"ประกาศนโยบาย..."

[บล็อกเปิด — Quote center 12pt]
"<HOSPITAL_NAME> ได้ตระหนักถึงความสำคัญของ..."

[เนื้อหา — Normal left 14pt]
[หัวข้อรอง — H2 bold+u 14pt]
"มาตรการ..."

[รายการข้อ — H4 indent 14pt]
1. ...
   1.1 ...
   1.1.1 ...

2. ...

[บล็อกปิด — Normal]
"จึงประกาศมาเพื่อโปรดทราบและปฏิบัติต่อไป"

[วันที่ + ลงนาม — center]
ประกาศ ณ วันที่ X เดือน X พ.ศ. XXXX

           (ลายเซ็น)
           (นาย X)
           ผู้อำนวยการ <HOSPITAL_NAME>
```

## docx-js skeleton

```javascript
const { Document, Packer, Paragraph, TextRun, ImageRun,
        AlignmentType, HeadingLevel } = require('docx');
const fs = require('fs');

const doc = new Document({
  styles: {
    default: { document: { run: { font: "TH SarabunIT๙", size: 28 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, font: "TH SarabunIT๙" },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 240, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, underline: {}, font: "TH SarabunIT๙" },
        paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1 } },
      { id: "Quote", name: "Quote", basedOn: "Normal", next: "Normal",
        run: { size: 24, font: "TH SarabunIT๙" },
        paragraph: { alignment: AlignmentType.CENTER } }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 992, bottom: 1440, left: 1701, right: 1134 }
      }
    },
    children: [
      // ตราครุฑ
      // new Paragraph({ alignment: AlignmentType.CENTER, children: [
      //   new ImageRun({ data: fs.readFileSync('garuda.png'), transformation: { width: 150, height: 150 } })
      // ]}),

      // หัวข้อประกาศ
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun({ text: "ประกาศนโยบาย...", bold: true })]
      }),

      // บล็อกเปิด
      new Paragraph({
        style: "Quote",
        children: [new TextRun({ text: "<HOSPITAL_NAME> ได้ตระหนักถึง..." })]
      }),

      // เนื้อหา
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: "มาตรการ", bold: true, underline: {} })]
      }),
      new Paragraph({
        children: [new TextRun({ text: "1. ..." })]
      }),

      // ลงนาม
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "ประกาศ ณ วันที่ ... พ.ศ. ..." })]
      })
    ]
  }]
});

Packer.toBuffer(doc).then(buffer =>
  fs.writeFileSync("announce.docx", buffer)
);
```

## Numbering (decimal hierarchy)

```javascript
numbering: {
  config: [
    { reference: "dec",
      levels: [
        { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
        { level: 1, format: LevelFormat.DECIMAL, text: "%1.%2.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1440, hanging: 360 } } } },
        { level: 2, format: LevelFormat.DECIMAL, text: "%1.%2.%3.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 2160, hanging: 360 } } } }
      ]
    }
  ]
}
```

## Checklist ก่อนส่งมอบ

- [ ] ตราครุฑ (กลางหน้า บนสุด)
- [ ] หัวข้อประกาศ H1 bold center
- [ ] วันที่ พ.ศ. (thai-date-format)
- [ ] ตัวเลขไทย [๑๒๓]
- [ ] ลำดับข้อ 1./1.1./1.1.1.
- [ ] ลายเซ็น + ชื่อ + ตำแหน่ง ผอ.
- [ ] validate docx ผ่าน
