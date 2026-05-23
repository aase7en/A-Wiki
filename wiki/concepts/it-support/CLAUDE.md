> **Cost-First**: ก่อนให้ Claude ทำงานใดๆ ใน domain นี้ → ดู [Cost-First Pyramid](/CLAUDE.md#cost-first-decision-pyramid)
> Hook → Free API → Cheap paid (DeepSeek/Qwen) → Subagent Haiku → Claude Sonnet
> **Prompt ส่งออกนอก: ใช้ภาษาอังกฤษเสมอ** (ประหยัด token ~30%)

---

# IT Support — Domain Rules

Domain สำหรับ troubleshooting, device setup, hardware/software issues ในที่ทำงาน

## กฎสำหรับ Claude

- หน้า IT Support → `wiki/concepts/it-support/<slug>.md`
- Entity ถ้ามี (เช่น specific device) → `wiki/entities/it-support/<slug>.md`
- IP/MAC ของอุปกรณ์ส่วนตัว → ใช้ placeholder `<device-ip>` ไม่ hardcode ใน wiki
- PowerShell / bash commands → ตรวจสอบก่อน paste เสมอ
- Solutions ที่ environment-specific → ระบุ OS version, driver version ให้ชัด

## Index

→ [[/index-it]]
