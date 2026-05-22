# Journal — บันทึกประจำวัน

> **TL;DR:** เขียนทุกวัน 1-3 ย่อหน้า สิ่งที่ทำ คิด รู้สึก ตัดสินใจ → AI อนาคตจะเลียนวิธีคิดจากนี่ได้

---

## ทำไมต้องเขียน

Wiki เก็บ **WHAT we know** (knowledge)
Journal เก็บ **HOW we think** (reasoning patterns)

สำหรับ Digital Legacy AI ที่จะ "เป็นเรา" หลังเราจากไป — ต้องการทั้งสองอย่าง

ดู context ใหญ่ที่: [[wiki/synthesis/digital-legacy-ai-architecture]]

---

## รูปแบบไฟล์

```
journal/
├── README.md           ← ไฟล์นี้
├── _template.md        ← copy ไปใช้
├── 2026/
│   ├── 2026-04-30.md
│   ├── 2026-05-01.md
│   └── ...
└── 2027/
    └── ...
```

ชื่อไฟล์: `YYYY-MM-DD.md` (ภาษาอังกฤษ ISO format)

---

## Workflow

### วิธีที่ 1 — Manual
```bash
cd ~/Code/wiki-clean
mkdir -p journal/$(date +%Y)
cp journal/_template.md journal/$(date +%Y)/$(date +%Y-%m-%d).md
code journal/$(date +%Y)/$(date +%Y-%m-%d).md
```

### วิธีที่ 2 — Alias ใน ~/.zshrc (แนะนำ)
```bash
journal() {
  local f="$HOME/Code/wiki-clean/journal/$(date +%Y)/$(date +%Y-%m-%d).md"
  mkdir -p "$(dirname "$f")"
  [ -f "$f" ] || cp "$HOME/Code/wiki-clean/journal/_template.md" "$f"
  ${EDITOR:-code} "$f"
}
```
จะใช้แค่พิมพ์ `journal` → เปิดไฟล์ของวันนี้

### วิธีที่ 3 — บอก Claude
```
"เปิด journal วันนี้" / "บันทึกวันนี้: [เนื้อหา]"
```

---

## เคล็ดลับเขียนให้ AI ใช้ได้

1. **เขียนเหตุผล ไม่ใช่แค่เหตุการณ์** — "ตัดสินใจ X เพราะ Y" ดีกว่า "ทำ X"
2. **บันทึกสิ่งที่ลังเล** — "คิดอยู่ว่า A หรือ B แต่เลือก A เพราะ..."
3. **เขียนความรู้สึกตรงๆ** — AI จะจับ tone ได้
4. **ภาษาธรรมดา** — เหมือนเล่าให้ตัวเองฟัง ไม่ต้อง formal
5. **ลิงก์ wiki page** — ถ้าวันนั้นทำงานเรื่องไหน `[[wiki/...]]`

---

## ความเป็นส่วนตัว

⚠️ Journal มีข้อมูลส่วนตัว — ถ้าจะ public ให้แยก private branch

ตัวเลือก:
- **A.** Push ทุกอย่างขึ้น GitHub private repo (ปัจจุบัน Aase7en-InW-Wiki น่าจะ private — เช็คก่อน)
- **B.** เก็บ journal/ ใน .gitignore + sync ผ่าน Drive แทน
- **C.** Encrypt ก่อน commit (`git-crypt` หรือ `age`)

ค่า default ตอนนี้ = A (commit ปกติ)
