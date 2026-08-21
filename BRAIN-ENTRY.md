# BRAIN-ENTRY — จุดเข้าสมองสำหรับ agent ภายนอก (ถูกปลุกโดย A-Conductor)

> ไฟล์นี้คือ **index เบาตัวเดียว** ที่ system_prompt ของ connector ควรชี้มา
> (Index+Pull: อ่านเฉพาะนี่ก่อน — ดึงรายละเอียดเมื่อจำเป็นเท่านั้น ประหยัด token)

## กฎ 3 ข้อ (ทำตามก่อนแตะอะไร)
1. **งานร่วม/ไฟล์ shared → อ่าน `COLLAB.md` ก่อน** (claims/lanes — กันชนกับ agent อื่น)
2. **ก่อน write/execute → อ้างกฎที่ทำตาม** (Iron Laws ใน `AGENTS.md` §Iron Laws)
3. **ไม่รู้จะวางไฟล์ไหน → อย่าสร้างใหม่** — ดู map ก่อน (repo: `AGENTS.md` §Storage · drive: `LAYOUT.md`)

## ลำดับอ่านต่อ (Pull เมื่อเกี่ยวข้องเท่านั้น)
| ต้องการ | ไฟล์ |
|---|---|
| ภาพรวมความรู้ | `wiki/context/wiki-overview.md` (สั้น) |
| ความจำข้าม session | `wiki/context/session-memory.md` (เครื่องนี้มี; เครื่องสดไม่มี = ข้ามได้ ไม่ error) |
| เส้นทาง skill | `wiki/A-ROUTER.md` + `wiki/SKILL-INDEX.md` |
| กติกาละเอียด | `AGENTS.md` (ใหญ่ — อ่านเฉพาะเมื่อทำงานใน repo นี้) · `docs/protocols/` |

## Programmatic (agent ที่รัน script ได้)
```bash
python -m conductor status|gate|plan|verify|recall|claim|models --json
```
(gate = GO/NO-GO ก่อนเริ่ม topic · verify = รัน gates · claim = จองงานใน COLLAB)
