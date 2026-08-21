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


## ค้นหา / กราฟ (ใช้แทนการเปิดไฟล์ไล่ทีละอัน)
```bash
python -m conductor search --query "esp32 lora" --json        # ความรู้ (hybrid FTS+vec)
python -m conductor related --page wiki/entities/iot/esp32.md --json  # เพื่อนบ้านในกราฟ
python -m conductor hubs --json                               # hub สำคัญ (553 โหนด)
```

## Programmatic (agent ที่รัน script ได้)
```bash
python -m conductor status|gate|plan|verify|recall|claim|models --json
```
(gate = GO/NO-GO ก่อนเริ่ม topic · verify = รัน gates · claim = จองงานใน COLLAB)

## SSoT Map (หนึ่ง role = หนึ่งไฟล์ — ห้ามสร้างซ้ำ)
| ต้องการ | ไปที่ (มีอยู่แล้ว อย่าสร้างใหม่) |
|---|---|
| สถานะงาน/claims/PR | `COLLAB.md` · สดๆ รัน `python -m conductor status --json` |
| แผน/roadmap/checklist | `docs/migration/awiki-vnext-plan.md` (+ phase work orders ข้างๆ) |
| ใบสั่งงาน | `docs/work-orders/` · migration phases อยู่ `docs/migration/phase-N-*.md` |
| ความจำ/บทเรียน (ledger) | `python -m conductor recall --query ...` (JSONL ที่ .tmp — ห้ามแก้ ให้เติม) |
| กติกาข้าม agent | `docs/protocols/cross-agent-work-orders.md` + `agent-continuity-gate.md` + `cross-agent-plan-handoff.md` |
| STATE สด (PR เปิด/ขั้นถัดไป) | `python -m conductor status --json` = generated STATE — ไม่มีไฟล์ hand-edit ค้างสมัย |
