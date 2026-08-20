# ADR: A-Wiki Conductor — Inspired-By, Not Fork (MIT confirmed)

- **Date:** 2026-08-21
- **Status:** Accepted (user decision, night session)
- **Context:** ต้องการสร้าง A-Wiki Conductor (orchestrator เฉพาะของเรา) โดย
  ศึกษาจาก Serena; ผู้ใช้ยืนยัน Serena เป็น MIT ("แค่ให้เครดิตพอ")
- **Decision:** ** Inspired-by implementation** — ยืมแนวคิดการออกแบบ
  (layered config, contexts, modes, per-project settings, fail-closed
  validation) แต่เขียน code เองทั้งหมดบน primitives ที่ A-Wiki มีอยู่แล้ว
  (COLLAB claims, hook registry, task-board, gates) — ไม่ copy codebase
  ของ Serena มา maintain diff
- **Rationale:** Conductor ต้องการ orchestration layer บนสมอง A-Wiki
  ไม่ใช่ execution hand ของ Serena; copy ทั้งตัว = ภาระ maintain สูง
- **Consequences:** เครดิตใน `conductor/NOTICE` + README; ถ้าอนาคตต้อง
  ยืม code จริง ค่อย evaluate ต่อทีละส่วนตาม MIT
