# Local-only Sources Manifest

ไฟล์เหล่านี้อยู่บน **local-only/manual backup** — ไม่อยู่ใน git (gitignored)
Claude อ่านได้จาก path ปกติใน `raw/` เพื่อให้ Obsidian links, `/ingest`, และ source metadata ยังเสถียร

> ถ้าไฟล์ไม่มีบน machine นี้ → restore/copy จาก local backup หรือเครื่องหลักก่อน ingest/query

| ไฟล์ (ใน raw/) | Domain | ขนาด | วันที่ ingest | หมายเหตุ |
|---------------|--------|------|-------------|---------|
| `UthaiHospital/บัญชีราคามาตรฐานครุภัณฑ์.pdf` | env/pharmacy | ~1 MB | unknown | บัญชีราคามาตรฐานครุภัณฑ์โรงพยาบาลอุทัย |
| `pharmacy/sp_drugs_full_3760.json` | pharmacy | ~3 MB | unknown | ฐานข้อมูลยาหลัก SP Drugstore 2020 (3,760 SKU) |
| `pharmacy/sp_drugs_medications_2895.json` | pharmacy | ~2 MB | unknown | subset เฉพาะยา 2,895 รายการ |

---

## กฎการอัปเดต manifest นี้

เมื่อ ingest source ที่เป็น **binary หรือ data ขนาดใหญ่** (PDF / รูปภาพ / CSV / JSON):
1. เพิ่ม entry ในตารางด้านบน (วัน + ขนาด + domain)
2. commit เฉพาะ `wiki/context/local-sources.md` + wiki pages + `log.md`
3. **ไม่ commit ตัวไฟล์จริง** — gitignored โดยอัตโนมัติ
4. **คง logical path ใต้ `raw/`** — อย่าย้าย `raw/` ทั้งก้อนออกจาก vault เพราะ Obsidian links และ `/ingest` อ้าง path นี้
