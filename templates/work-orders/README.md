# Work Orders — หน่วยงานที่ agent ไหนก็หยิบทำต่อได้

ทุก chunk มีไฟล์ WO ของตัวเอง (copy `WO-TEMPLATE.md`) สถานะ:
`open` → `claimed(<agent>)` → (`⏸ paused`) → `done`

**Pause protocol (ใกล้ 5-hr limit / ต้องสลับ agent):**
commit งานค้าง (build ผ่าน → branch ปกติ; ไม่ผ่าน → `wip/<id>`) → append
Checkpoint (commit hash + เหลืออะไร + กับดัก) → Status `⏸ paused` →
อัปเดตตาราง claim ใน `COLLAB.md` → push — **ห้ามทิ้ง uncommitted**

**Resume prompt (user ใช้กับ agent ตัวไหนก็ได้ — Claude/Codex/Cursor/ZCode/Hermes/...):**

```
อ่าน COLLAB.md + docs/work-orders/<id>.md ของ repo นี้
ทำต่อจาก Checkpoint ล่าสุด เฉพาะใน Lane/files ที่ระบุ
เริ่มจาก branch ที่ work order ระบุ; เสร็จแล้ว merge เข้า main + set done
```

Protocol เต็ม + กติกา 8 ข้อ: `COLLAB.md` ใน repo นี้ และ A-Wiki
`docs/protocols/cross-agent-work-orders.md`
