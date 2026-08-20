# A-Wiki Conductor — Serena Fork Foundation Notes

> **สถานะ:** design notes ช่วงต้น (night shift 2026-08-20) — ยังไม่ใช่ spec
> เต็ม ไม่มี implementation ใดๆ ในเอกสารนี้
> **เจตนา:** อนาคตจะ fork/copy Serena มาพัฒนาต่อเป็น **A-Wiki Conductor**
> (โปรแกรมเฉพาะของเรา) — อ่าน Serena configuration docs ละเอียดแล้ว บันทึก
> สิ่งที่ควรยืม / ไม่ควรยืม / คำถามที่ต้องตอบก่อนลงมือ

## สิ่งที่อ่านมา (source)

`https://oraios.github.io/serena/02-usage/050_configuration.html` — ระบบ
configuration ของ Serena: layered config, contexts, modes, projects, prompt
templates, language-server settings

## 🚨 คำถามบล็อกแรก — LICENSE (ต้องเช็คก่อน fork จริง)

หน้า configuration **ไม่พูดถึง license เลย** — ก่อน fork/copy ต้องอ่าน
LICENSE ของ repo Serena จริง (oraios/serena) และตัดสิน:
- ถ้า permissive (MIT/Apache) → fork ได้ + ระบุ attribution
- ถ้า copyleft → พิจารณา "ใช้เป็น dependency" แทน "fork"
- จดไว้ใน ADR ก่อนเขียนโค้ด Conductor บรรทัดแรก

## สิ่งที่ควรยืมจาก Serena (แบบ design ไม่ใช่ copy code)

| แนวคิด Serena | ปรับใช้ใน Conductor |
|---|---|
| **Layered config** (global `serena_config.yml` → project `project.yml` + `.local.yml` → CLI override) | ตรงกับ A-Wiki pattern อยู่แล้ว (`config/awiki.yaml` + `.awiki/project.yaml` Phase 4) — Conductor ใช้สามชั้นนี้ต่อไป |
| **Contexts** (claude-code/codex/ide/agent...) ตายตัวต่อ session + `single_project` lock | = provider adapters ของเรา (Phase 6) — ยืมไอเดีย "context กำหนด tool subset ที่เห็นได้" มาทำ per-agent surface |
| **Modes** = union(base + default + added) | เหมาะกับ A-Wiki phases: base=safety เสมอ, default=ตาม phase work order, added=ต่อ session |
| **`SERENA_HOME` + per-project dir + trusted projects** | = `AWIKI_DATA_DIR`/drive root + `.awiki/` + fail-closed validate — อยู่แล้ว ยืมโครง trusted-project list |
| **Jinja2 prompt templates + `embed_memory()`** | น่าสนใจสำหรับ context injection ที่ควบคุมได้ (แทน ad-hoc stdout) |
| **`ls_specific_settings`** (ls_path/ls_args/initializationOptions) | สำหรับ Phase 10 Graft/code-context — เก็บไว้เป็นแนวทาง |

## สิ่งที่ "ไม่ควร" ยืม / ต้องระวัง

- **Anonymous usage reporting** (opt-out ผ่าน env) — Conductor ของเรา
  **ไม่เก็บ telemetry ใดๆ** (Iron Law #6 / public-safe ตั้งแต่วันแรก)
- Modes ที่ incompatible กันไม่ถูก block อัตโนมัติ — Conductor ต้อง
  validate mode combinations ตั้งแต่ config-load (fail-closed เหมือน
  Phase 4 validator)
- Config ที่แก้ผ่าน dashboard/editor หลายทาง → drift — Conductor ใช้
  regen + `--check` pattern เดียวกับ skill-surfaces/scanner ที่เรามี

## หน้าที่จริงของ Conductor (ตามเป้าหมายเรา)

Serena = execution hand; **Conductor = orchestration manager** (ตาม
routing protocol: A-Conductor = manager/orchestration):
- รับ objective → แตก work orders → กระจายให้ agents ตาม lane/claim
- ติดตาม 5-hr limits → มอบหมายสลับมือ (pause/resume)
- บังคับ Agent Continuity Gate ก่อนทุก session
- อ่าน/เขียน A-Wiki เป็น memory + governance

→ งั้นสิ่งที่จะ "ยืม" จาก Serena จริงๆ อาจไม่ใช่ทั้งตัว แต่เป็น
**ชั้น configuration + project-management UX** ของมัน

## คำถามที่ค้างไว้ถาม user ตอนตื่น (grill-with-docs แทนการเดา)

1. **ขอบเขต:** Conductor = orchestrator ล้วน หรือ รวม execution tools
   แบบ Serena ด้วย? (mvp ไหนก่อน)
2. **Fork vs dependency vs inspired-by:** อยาก maintain upstream diff ไหม?
3. **ภาษา/runtime:** Serena เป็น Python+MCP — Conductor ใช้ Python
   ต่อเลยไหม (ทีมงานเราคุ้น)

## แผนถัดไป (ยังไม่ได้เริ่ม)

- [ ] อ่าน LICENSE จริงของ oraios/serena + จด ADR fork-decision
- [ ] ถ้า fork ได้: spike branch `conductor/spike-config-map` แผลง
      Serena config keys → A-Wiki equivalents
- [ ] เขียน spec เต็มผ่าน /A-Plan chain (a-think → grill → spec)
