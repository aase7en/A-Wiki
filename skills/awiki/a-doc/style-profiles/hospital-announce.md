# Style Profile: Hospital Announce (ประกาศโรงพยาบาล)

> Source: ประกาศนโยบายจริง (de-identified) (analyzed via python-docx by Poppy Javis)
> Verified: 2026-07-16
> ใช้กับ: types/announce/, types/order/, types/policy/

## Page Setup

| Property | Value | DXA (twentieths of point) |
|---|---|---|
| Paper size | A4 | width 11906, height 16838 |
| Top margin | 1.75 cm | 992 |
| Bottom margin | 2.54 cm | 1440 |
| Left margin | 3.00 cm | 1701 |
| Right margin | 2.00 cm | 1134 |

> **หมายเหตุ**: L3cm/R2cm = มาตรฐานราชการไทย (เย็บซ้าย)

## Font

| Element | Font | Size (pt) | Style |
|---|---|---|---|
| Heading 1 (หัวข้อประกาศ) | TH SarabunIT๙ | 16 | Bold |
| Heading 2 (หัวข้อรอง) | TH SarabunIT๙ | 14 | Bold + Underline |
| Heading 3 (หัวข้อย่อย) | TH SarabunIT๙ | 14 | Bold |
| Heading 4 (รายการข้อ) | TH SarabunIT๙ | 14 | Regular |
| Normal (เนื้อหาทั่วไป) | TH SarabunIT๙ | 14 | Regular |
| Quote (ข้อความลงท้าย) | TH SarabunIT๙ | 12 | Regular |

## DXA quick reference (docx-js)

```javascript
// Page size
size: { width: 11906, height: 16838 }  // A4

// Margins
margin: {
  top: 992,      // 1.75 cm
  bottom: 1440,  // 2.54 cm
  left: 1701,    // 3.00 cm
  right: 1134    // 2.00 cm
}
```

## docx-js styles config

```javascript
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "TH SarabunIT๙", size: 28 } }  // 14pt = 28 half-points
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, font: "TH SarabunIT๙" },  // 16pt
        paragraph: {
          alignment: AlignmentType.CENTER,
          spacing: { before: 240, after: 240 },
          outlineLevel: 0
        }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, underline: {}, font: "TH SarabunIT๙" },  // 14pt bold+u
        paragraph: {
          alignment: AlignmentType.LEFT,
          spacing: { before: 180, after: 180 },
          outlineLevel: 1
        }
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, font: "TH SarabunIT๙" },
        paragraph: { spacing: { before: 120, after: 120 }, outlineLevel: 2 }
      },
      {
        id: "Heading4", name: "Heading 4", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 28, font: "TH SarabunIT๙" },
        paragraph: { indent: { left: 720 }, outlineLevel: 3 }  // 36pt = 720 twips
      },
      {
        id: "Quote", name: "Quote", basedOn: "Normal", next: "Normal",
        run: { size: 24, font: "TH SarabunIT๙" },  // 12pt
        paragraph: { alignment: AlignmentType.CENTER }
      }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },
        margin: { top: 992, bottom: 1440, left: 1701, right: 1134 }
      }
    },
    children: [/* content */]
  }]
});
```

## Layout structure (เรียงบน→ล่าง)

```
[ตราครุฑ — กึ่งกลางหน้า]                      ← image center
                                                ← blank line
[หัวข้อประกาศ — Heading1 center bold 16pt]   ← "ประกาศนโยบาย..."
                                                ← blank line
[วันที่ — Quote center 12pt]                  ← "ประกาศ ณ วันที่ X  mechanismคก.."
                                                ← blank line
[เนื้อหา — Normal left 14pt]
  [หัวข้อรอง — Heading2 bold+u 14pt]
  [รายการข้อ — Heading4 indent 14pt]
    1. ...
    1.1 ...
    1.1.1 ...
                                                ← blank line
[ลงนาม — center]
  (ลายเซ็น)
  นาย X
  ผู้อำนวยการ <HOSPITAL_NAME>
```

## Numbering

- ลำดับเลข: **1./1.1./1.1.1.** (decimal hierarchy)
- ตัวเลขในเนื้อหา: **ไทย** [๑๒๓] ตามมาตรฐานราชการ
- ปี: **พ.ศ.** (Buddhist Era = CE + 543)

## Garuda emblem (ตราครุฑ)

- กึ่งกลางหน้า บนสุด
- ใช้ซ้ำเมื่อขึ้นหัวข้อใหญ่ใหม่ (เช่น หน้า 2)
- image path: ดูใน `<WORK_DIR>/06_Projects_Training_03_Logos_โลโก้/`

## Notes

- Line spacing: Single หรือ Multiple 1.15 (อ่านง่าย)
- Space after paragraph: 6pt (normal), 12pt (แยกหัวข้อใหญ่)
- ไม่ใช้ bullet unicode (•) — ใช้ LevelFormat.BULLET ใน docx-js
