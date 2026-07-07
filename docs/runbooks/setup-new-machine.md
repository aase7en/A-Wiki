# Runbook: Setup A-Wiki บนเครื่องใหม่

> **วัตถุประสงค์**: clone A-Wiki ให้ใช้ได้บน Mac/Windows/Linux โดยเก็บไฟล์หนัก ไฟล์ดิบ และ secrets ไว้ใน cloud data folder นอก git
> **Last updated**: 2026-05-30

---

## Prerequisites

- Git
- Python 3.10+ recommended
- Node.js 18+ optional สำหรับ MCP/GitNexus/agent tooling
- Google Drive Desktop หรือ cloud storage อื่นที่มีโฟลเดอร์ `A-Wiki-Data`

---

## 1. Clone

```bash
git clone https://github.com/aase7en/A-Wiki.git
cd A-Wiki
```

---

## 2. One-command local setup

```bash
bash scripts/setup-local.sh
```

สคริปต์นี้จะทำงานแบบเบาและ cross-platform:

| Step | ทำอะไร | เขียนลง git ไหม |
|---|---|---|
| `setup-cloud-link.sh --auto` | สร้าง `drive/` และ `raw/` link ไป `A-Wiki-Data` | ไม่ |
| `.mcp.json` | สร้าง config ตาม path เครื่องนี้ | ไม่ |
| `import-keys.py` | sync env keys จาก `drive/.secrets` | ไม่ |
| private journal | สร้าง/เชื่อม `log.md` และ `wiki/context/session-memory.md` จาก `drive/personal/journal/` หรือ `.example` | ไม่ |
| `gen-index.py` | rebuild local wiki index | เฉพาะ generated context/index ตามระบบ |
| Codex hooks | link `.codex/hooks` | ไม่ |
| model intel cache | เตรียม `.tmp/model-intel/` | ไม่ |
| `link-agent-configs.sh` | link skills → repo + `.env` → Drive สำหรับทุก agent harness ที่ตรวจพบบนเครื่องนี้ (Claude/Codex/Cline/Hermes/Gemini/ZCode/Antigravity/Windsurf/OpenClaw) | ไม่ |

Mac ส่วนตัวอาจเจอ path ลักษณะนี้:

```text
$HOME/Library/CloudStorage/GoogleDrive-<account>/My Drive/A-Wiki-Data
```

เครื่องที่ทำงานไม่จำเป็นต้อง path ตรงกัน ให้ใช้ตัวตรวจ/ตั้งค่าแทน:

```bash
bash scripts/setup-cloud-link.sh --status
bash scripts/setup-cloud-link.sh --provider google
bash scripts/setup-cloud-link.sh --path "/explicit/cloud/path"
```

---

## 2b. Universal agent-config links (skills + `.env`)

เครื่องใหม่ทุกเครื่อง `setup-local.sh` จะเรียก `scripts/link-agent-configs.sh`
ให้อัตโนมัติ — ไม่ต้องติดตั้ง skill หรือกรอก secret ซ้ำต่อ agent อีก:

```bash
bash scripts/link-agent-configs.sh              # link ทุก harness ที่ตรวจพบ
bash scripts/link-agent-configs.sh --status     # health check
bash scripts/link-agent-configs.sh --agent zcode  # บังคับ agent ที่ยังไม่มี dir
```

- **Skills** (`agent-skills/`, `skills/anthropic-skills/`, `skills/mattpocock/`)
  → symlink จาก repo (git = source of truth, sync ข้ามเครื่องอยู่แล้ว)
- **`.env`** ของ Hermes/ZCode และ repo root → symlink ไป `drive/` (Google Drive
  = source of truth สำหรับ secrets) — ดูรายละเอียดเต็มที่
  `agent-skills/extensibility/symlink-connector/SKILL.md`
- **มือถือ / cloud session (Claude Code on the web ฯลฯ)**: ไม่มี local `~/.claude`
  หรือ Google Drive mount ให้ symlink ใช้ remote environment ของแพลตฟอร์มนั้นแทน
  (repo clone สดในแต่ละ session) — ข้าม step นี้ได้ ไม่ error
- **Windows ไม่มี Developer Mode**: dir link fallback เป็น PowerShell junction
  อัตโนมัติ; ไฟล์เดี่ยว (`.env`) fallback เป็น copy ธรรมดา — แก้ที่ Drive แล้ว
  re-run script เพื่อ sync

---

## 3. Optional installs

| ต้องการ | คำสั่ง |
|---|---|
| Refresh free model roster จาก OpenRouter | `bash scripts/update-model-roster.sh` |
| Refresh current model/agent intel ด้วย Gemini grounding | `bash scripts/update-ai-model-intel.sh --force --print` |
| Rebuild local model router policy | `python3 scripts/model-router-policy.py` |
| Snapshot Microsoft SkillOpt upstream แบบเบา | `bash scripts/refresh-skillopt.sh` |
| Install runnable SkillOpt local-only | `INSTALL_SKILLOPT=1 bash scripts/setup-local.sh` |
| Run deterministic A-Wiki skill evals | `bash scripts/skillopt/run-awiki-evals.sh` |
| Run A-Wiki-owned skill quality report | `python3 scripts/skill-quality-report.py` |
| Check SessionStart TODO hygiene | `python3 scripts/todo-health.py` |
| Verify this machine end-to-end | `python3 scripts/verify-next-machine.py --build-vec` |
| Install react-doctor สำหรับ React project | `INSTALL_REACT_DOCTOR=1 bash scripts/setup-local.sh` |

SkillOpt local install จะอยู่ที่:

```text
.tmp/skillopt-src
.venv-skillopt
```

ทั้งสอง path ถูก ignore เพื่อไม่ทำให้ A-Wiki หนัก

---

## 4. GitHub Actions setup

สำหรับ repo fork หรือ clone ที่จะใช้ GitHub Actions ให้ตั้งค่า repository secret เท่าที่จำเป็น:

| Secret | ใช้ทำอะไร | ถ้าไม่มี |
|---|---|---|
| `OPENROUTER_API_KEY` | ให้ weekly model roster scout ดึงรายชื่อ free model ล่าสุด | workflow ไม่ fail แต่ report จะเป็น `skipped` |

Workflow สำคัญ:

| Workflow | Trigger | หน้าที่ |
|---|---|---|
| `A-Wiki CI` | push ไป `main` + manual | ตรวจ privacy, syntax, tests, readiness smoke |
| `A-Wiki Cross-Platform Smoke` | manual + weekly | ทดสอบ fake external data layer บน Ubuntu/macOS/Windows |
| `A-Wiki Model Roster Refresh` | manual + ทุกวันจันทร์ | เทียบ free model roster ล่าสุดกับ `wiki/context/model-roster.conf`, upload report, เปิด/อัปเดต issue ถ้า roster เปลี่ยน |
| `A-Wiki Weekly Health Digest` | manual + ทุกวันพุธ | สร้าง report สุขภาพ repo/wiki เป็น artifact โดยไม่ auto-commit |

Manual run:

```bash
gh workflow run model-roster-refresh.yml -f create_issue=false
gh workflow run wiki-health-digest.yml
gh run list --workflow model-roster-refresh.yml --limit 1
```

หมายเหตุ: workflow model roster ไม่ auto-commit เพราะการเปลี่ยน model routing กระทบ agent ทั้งระบบ ต้อง review diff ก่อน merge ลง `main`

---

## 5. Verify

```bash
python3 scripts/agent-preflight.py
python3 scripts/verify-awiki-ready.py
python3 scripts/verify-cross-platform.py --build-vec
python3 scripts/verify-next-machine.py --build-vec
bash scripts/setup-cloud-link.sh --status
bash scripts/link-agent-configs.sh --status
python3 -m pytest tests/test_agent_preflight.py tests/test_drive_link_health.py tests/test_link_agent_configs.py -q
```

ควรเห็น:

- branch เป็น `main`
- `drive/` ชี้ไป cloud data folder
- `raw/` ชี้ไป `drive/raw`
- `.secrets` มีอยู่ใน Drive แต่ไม่ print ค่า secret
- `.tmp/model-router-policy.conf` generate ได้
- deterministic skill evals ผ่าน
- skill quality report ไม่มี FAIL

## 6. Cross-device sync

ก่อนสลับเครื่องหรือเปิด Obsidian แก้ไฟล์ ให้ปิด session เก่าก่อน แล้ว sync:

```bash
python3 scripts/sync.py --now
git status --short
```

ถ้าจะใช้ daemon mode ให้เปิดแค่เครื่องเดียว:

```bash
python3 scripts/sync.py --daemon --interval 30 --debounce 10
```

อ่าน workflow แยกสำหรับ mobile/Obsidian ที่ `docs/runbooks/mobile-obsidian-workflow.md`

---

## Rules

- ห้าม commit `raw/`, `drive/`, `.tmp/`, `.venv-skillopt`, `.mcp.json`, `.codex/`, `.claude/`
- ไฟล์หนัก/ดิบ/ส่วนตัว/secrets อยู่ใน `A-Wiki-Data` เท่านั้น
- งานง่ายให้เริ่มจาก local search/graph และ free model roster ก่อนเสมอ
