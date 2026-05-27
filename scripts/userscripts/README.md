# Waste Form OCR & Auto-Fill — Userscript

> Tampermonkey userscript สำหรับกรอกฟอร์ม `https://10779.gtwoffice.com/env/manage/trash_add`
> อัตโนมัติจากภาพถ่ายใบรายงานขยะ — **ไม่ต้องติดตั้ง Python / Playwright**
>
> See design: [wiki/synthesis/waste-form-automation.md](../../wiki/synthesis/waste-form-automation.md) ·
> OCR prompt source: [wiki/synthesis/garbage-report-ocr.md](../../wiki/synthesis/garbage-report-ocr.md)

---

## ติดตั้ง (ครั้งแรกครั้งเดียว)

1. **ติดตั้ง Tampermonkey** ใน Chrome / Edge / Firefox / Brave
   - Chrome Web Store → ค้น "Tampermonkey" → Add to Chrome
2. **เปิดไฟล์** `waste-form-ocr-fill.user.js` → ลากไปวางใน browser
   - Tampermonkey จะถามว่าจะ install ไหม → กด **Install**
3. **เปิดหน้า** `https://10779.gtwoffice.com/env/manage/trash_add` (login ก่อน)
   - จะเห็นปุ่ม **📷 OCR & Fill** ลอยอยู่มุมขวาบน
4. **คลิกปุ่มครั้งแรก** → จะถาม `GEMINI_API_KEY`
   - เอามาจาก [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (ฟรี)
   - Key จะถูกเก็บใน Tampermonkey storage บนเครื่องนี้เท่านั้น (ไม่ขึ้น git)

---

## วิธีใช้งานประจำวัน

1. ถ่ายรูปใบรายงานขยะให้ชัด (ไม่เอียง ไม่เบลอ)
2. เปิดหน้า trash_add → คลิก **📷 OCR & Fill**
3. ลากรูปวาง / เลือกไฟล์
4. รอ ~3-10 วินาที — Gemini Flash อ่านใบรายงาน
5. ถ้าใบมีหลายวัน → ระบบจะถามให้เลือกวันที่
6. **ตรวจ preview ก่อนกรอก** — แก้ตัวเลขได้ที่ช่อง `kg`
7. กด **✓ Fill Form** → ฟอร์มถูกกรอกอัตโนมัติ (รวมเวลา / Supplies / ผู้บันทึก)
8. **ตรวจฟอร์มเอง** แล้วกด **บันทึกข้อมูล** (ปุ่มเขียวล่างขวาในฟอร์ม) เอง

> ⚠ Script ไม่กด submit เอง — เพื่อให้ user verify ก่อนทุกครั้ง

---

## Cost / Quota

- Gemini 2.5 Flash: ฟรี **1500 req/วัน** — ใบรายงาน 1 ใบ = 1 req
- ใช้ ~30 วินาทีต่อใบ (vs มือเปล่า ~3-5 นาที)

---

## Debug

เปิด DevTools (`F12`) → tab **Console** → จะเห็น log prefix `[waste-ocr]`:
- `userscript loaded` — userscript inject สำเร็จ
- `OCR raw: [...]` — JSON ที่ Gemini ตอบกลับ (ใช้ debug ว่าเลขถูกอ่านเป็นอะไร)
- `unknown location: <xxx>` — มี location ใหม่ที่ไม่อยู่ใน `ROW_LABEL_MAP`

### ปัญหาที่พบบ่อย

| อาการ | แก้ |
|---|---|
| ปุ่ม "📷 OCR & Fill" ไม่ขึ้น | ตรวจว่า Tampermonkey enabled (icon ขวาบน), refresh หน้า |
| `Network error` ตอนกด upload | API key ผิด → **ดับเบิลคลิก**ปุ่มเพื่อล้าง key แล้วใส่ใหม่ |
| OCR อ่านผิด | คลิก preview แล้วแก้เลขเอง ก่อนกด Fill Form |
| Fill แล้ว ✗ ไม่พบช่องของ ER (หรือ location อื่น) | label ในฟอร์มอาจไม่ตรง — ดู [แก้ Row Mapping](#แก้-row-mapping) |
| Header (Supplies/ผู้บันทึก) ไม่กรอก | option text อาจไม่ใช่ "อบต.อุทัย" หรือ "Aase7en" ตรงตัว — แก้ใน script |

---

## แก้ Row Mapping

ถ้าเจอ location ใหม่ (เช่น แผนกใหม่) เปิดไฟล์ `waste-form-ocr-fill.user.js` แล้วแก้ตัวแปร:

```js
const ROW_LABEL_MAP = {
  OPD: ['ขยะทั่วไป OPD'],
  Ward: ['ขยะทั่วไป Ward'],
  // ...
  จิตเวช: ['ขยะทั่วไป จิตเวช'],  // ← เพิ่มแบบนี้
};
```

Key = ค่าที่ OCR คืนมาในฟิลด์ `location` (ดูจาก console log)
Value = array ของ label text ที่จะ match ใน `<td>` ของฟอร์ม (try หลายแบบได้)

หลังแก้ → Tampermonkey dashboard → save → refresh หน้า trash_add

### Compound location (แผนกรวมกัน หาร weight)

```js
const COMPOUND_LOCATIONS = {
  'OPD+ER': ['OPD', 'ER'],
  'แผนไทย+ฝังเข็ม': ['แผนไทย', 'ฝังเข็ม'],
};
```

---

## Backup ไฟล์ & แชร์เพื่อนร่วมงาน

ไฟล์นี้เป็น **เครื่องมือส่วนบุคคล** สำหรับงานที่ทำงาน — ไม่ใช่ทุกคนที่ clone A-Wiki ควรใช้
แนะนำให้สำรองไว้ใน Google Drive และแชร์ผ่าน Drive link:

```bash
# ขั้นตอน 1: ตั้งค่า drive/ symlink (ครั้งแรกครั้งเดียว)
bash scripts/setup-drive-link.sh
# → สร้าง drive/ ชี้ไปที่ Google Drive ของคุณ (L:\My Drive\A-Wiki-Data หรือ Mac path)

# ขั้นตอน 2: สำรองไฟล์
cp scripts/userscripts/waste-form-ocr-fill.user.js drive/personal-tools/userscripts/
cp scripts/userscripts/README.md drive/personal-tools/userscripts/
```

Drive sync อัตโนมัติผ่าน Google Drive Desktop → เพื่อนร่วมงานเข้าถึงได้ทันที

**แชร์ให้เพื่อนร่วมงาน**:
1. ส่ง path Drive (หรือ share link จาก Google Drive)
2. เพื่อนดาวน์โหลดไฟล์ `.user.js` → ลากไปวางใน Chrome + Tampermonkey
3. ใส่ `GEMINI_API_KEY` ของตัวเอง (ฟรี แต่แยก key ต่อคน)

> **หมายเหตุ**: ไฟล์ `drive/` ไม่ถูก commit ไป git — เป็น symlink local เท่านั้น
> OCR corrections/knowledge อยู่ใน `wiki/context/ocr-learning-log.md` (ใน git ทุกคน sync ได้)

---

## Privacy / Security

- ภาพถูกส่งไป **Google Generative Language API** เพื่อ OCR (ดู [Google AI privacy](https://ai.google.dev/gemini-api/terms))
- API key เก็บใน Tampermonkey local storage บนเครื่องนี้เท่านั้น
- ไฟล์ภาพไม่ถูก upload ที่อื่น / ไม่ commit ไป git
- ทุก request เป็น HTTPS

---

## Fallback: Python + Playwright Edition

ถ้า userscript ไม่ work (เช่น OCR accuracy ต่ำ, form selectors แปลก, network proxy) → กลับไปใช้แผนเดิมใน [wiki/synthesis/waste-form-automation.md](../../wiki/synthesis/waste-form-automation.md):

```bash
pip install playwright anthropic
playwright install chromium
python scripts/save-waste-cookie.py    # ยังไม่ได้สร้าง
python scripts/fill-waste-form.py img.jpg --dry-run    # ยังไม่ได้สร้าง
```

(สอง script นี้ยังเป็น TODO — userscript เป็นทางเลือก lightweight ที่ใช้งานได้ก่อน)
