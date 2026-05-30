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
| `gen-index.py` | rebuild local wiki index | เฉพาะ generated context/index ตามระบบ |
| Codex hooks | link `.codex/hooks` | ไม่ |
| model intel cache | เตรียม `.tmp/model-intel/` | ไม่ |

Mac ส่วนตัวอาจเจอ path แบบนี้:

```text
/Users/aase7en/Library/CloudStorage/GoogleDrive-aase7en@sunday-estate.com/My Drive/A-Wiki-Data
```

เครื่องที่ทำงานไม่จำเป็นต้อง path ตรงกัน ให้ใช้ตัวตรวจ/ตั้งค่าแทน:

```bash
bash scripts/setup-cloud-link.sh --status
bash scripts/setup-cloud-link.sh --provider google
bash scripts/setup-cloud-link.sh --path "/explicit/cloud/path"
```

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
| Install react-doctor สำหรับ React project | `INSTALL_REACT_DOCTOR=1 bash scripts/setup-local.sh` |

SkillOpt local install จะอยู่ที่:

```text
.tmp/skillopt-src
.venv-skillopt
```

ทั้งสอง path ถูก ignore เพื่อไม่ทำให้ A-Wiki หนัก

---

## 4. Verify

```bash
python3 scripts/agent-preflight.py
python3 scripts/verify-awiki-ready.py
bash scripts/setup-cloud-link.sh --status
python3 -m pytest tests/test_agent_preflight.py tests/test_drive_link_health.py -q
```

ควรเห็น:

- branch เป็น `main`
- `drive/` ชี้ไป cloud data folder
- `raw/` ชี้ไป `drive/raw`
- `.secrets` มีอยู่ใน Drive แต่ไม่ print ค่า secret
- `.tmp/model-router-policy.conf` generate ได้
- deterministic skill evals ผ่าน
- skill quality report ไม่มี FAIL

---

## Rules

- ห้าม commit `raw/`, `drive/`, `.tmp/`, `.venv-skillopt`, `.mcp.json`, `.codex/`, `.claude/`
- ไฟล์หนัก/ดิบ/ส่วนตัว/secrets อยู่ใน `A-Wiki-Data` เท่านั้น
- งานง่ายให้เริ่มจาก local search/graph และ free model roster ก่อนเสมอ
