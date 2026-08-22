# ADR: A-Conductor DECISION_REQUIRED 3 ข้อ — คำตอบ 2026-08-22

- **สถานะ**: DECIDED (default-conservative; user ยังเปลี่ยนได้ทุกเมื่อ)
- **บริบท**: 3 ประตูที่ A-Conductor รอคำตอบ (docs ฝั่งนั้น: second-brain-phase1 §backlog, one-app-orchestration-design §approaches, WO-P1-023 DR-P1-003)
- **ที่มาของคำตอบ**: ถาม user แล้วไม่มีคำตอบภายใน session → ใช้ตัวเลือกอนุรักษ์นิยมที่สุดตาม best judgment ของ executor + ตรงสถานะปัจจุบันของระบบทั้งสามประตู

## ข้อ 1 — MCP gateway enforcement (Second Brain Phase 2)

**ตัดสิน: เลื่อนต่อ + ใช้ hooks ที่มีอยู่** (ตาม ADR-0001 ฝั่ง Conductor)

- เหตุผล: gateway เป็น MCP proxy subsystem ใหม่ (session state, namespace collisions) — เสี่ยง "second orchestration universe" ผิดกฎ reuse-before-build ของ integration contract §4-5 ขณะที่ฝั่งสมองมี enforcement ที่พิสูจน์แล้ว (hooks 29 ตัว วิ่งจริง 4 providers — ดู E2E journey harness)
- ผลต่อระบบ: Phase 2 ของ Second Brain ใช้ prompt-injection + กฎสั้น (quote rule before write) + hooks ระดับ agent ที่รองรับ — ได้ enforcement บางส่วนโดยไม่เพิ่ม subsystem; agent ที่ไม่มี hooks (บาง surface) ยังเป็น "สอนไม่ใช่กั้น"
- เงื่อนไขเปิดใหม่: เมื่อมีหลักฐานว่า agent ข้ามกฎบ่อยจนจับได้จริง (เก็บ evidence จาก self_audit)

## ข้อ 2 — Code signing ลบ SmartScreen

**ตัดสิน: ไม่ sign + สอนวิธีกดผ่าน** ("More info → Run anyway" ครั้งแรกครั้งเดียวต่อเครื่อง)

- เหตุผล: ใช้เอง/ทีมเล็กที่เชื่อแหล่งโหลด — ค่า cert รายปี (OV ~$70-200 / EV ~$300+ ต้อง hardware token) ยังไม่คุ้ม; self-signed แก้ได้เฉพาะเครื่องตัวเองจึงไม่แก้อะไรถ้าใช้หลายเครื่อง
- ผลต่อระบบ: friction เล็กๆ ตอนเปิด exe ครั้งแรก — จัดการด้วยคู่มือ (ใส่ใน USER-GUIDE ฝั่ง Conductor เมื่อถึงจุดนั้น)
- เงื่อนไขเปิดใหม่: เมื่อแจกจ่ายสาธารณะจริงจัง

## ข้อ 3 — DR-P1-003 tunnel transport (Worker 3 live test)

**ตัดสิน: ระงับต่อ + ใช้ dummy/local integration** (คงสถานะปัจจุบัน)

- เหตุผล: gate นี้เขียนไว้เพื่อกันสองอย่างโดยเฉพาะ — (1) กลืน tunnel binding ของ worker ที่กำลัง live (2) provisioning ภายนอกอัตโนมัติที่แตะ credential ภายนอก; งานอื่นทั้งหมดไม่ได้ถูกบล็อกอยู่แล้ว จึงไม่มีเหตุจำเป็นต้องเปิดตอนนี้
- ผลต่อระบบ: Worker 3 live start/restart/stop ยังไม่ถูก validate จริง — ความเสี่ยงจำกัดอยู่ที่ worker นั้นตัวเดียว; ทุกอย่างอื่น (control center, UI, dummy runtime, process manager) validate ได้ปกติ
- เงื่อนไขเปิดใหม่: เมื่อจำเป็นต้อง validate Worker 3 จริง — ทางที่ตรง gate ที่สุดคือ **user provision binding เองแบบ disposable** แล้วส่ง config ให้ (ไม่ใช่ auto-provision)

## การนำไปใช้

ADR นี้อยู่ฝั่งสมอง (authority ของ policy) — ฝั่ง A-Conductor อ้างถึงได้จาก work order / ADR-0001 ของมัน; ไม่มี code change ใดๆ จากการตัดสินทั้งสามข้อนี้ (ทั้งหมดคือการคงสถานะปัจจุบันอย่างเป็นทางการ)
