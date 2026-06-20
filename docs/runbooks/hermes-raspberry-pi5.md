# Hermes Agent on Raspberry Pi 5 — A-Wiki Brain Integration

**วันที่**: 2026-06-20 | **สถานะ**: ✅ Verified

## ภาพรวม

Hermes Agent บน Raspberry Pi 5 (ARM64) ทำหน้าที่เป็น **AI orchestrator ที่ขับเคลื่อนด้วย A-Wiki brain** — รองรับทั้ง:
- **Lifecycle skills** (DEFINE→PLAN→BUILD→VERIFY→REVIEW→SHIP) — 20 skills
- **4 specialist personas** — code-reviewer, test-engineer, security-auditor, web-performance-auditor
- **Telegram gateway** — รับคำสั่ง → ค้น A-Wiki FTS5 → ตอบกลับ
- **A-Wiki Live Dashboard** — real-time event monitoring
- **Cron automation** — benchmark scan, cost audit, health check
- **IoT/MQTT control** — ESP32, sensors via Telegram

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Raspberry Pi 5 | 8GB RAM | 16GB RAM |
| Storage | 64GB microSD | 256GB NVMe SSD (via HAT) |
| OS | Raspberry Pi OS (64-bit) | Ubuntu Server 24.04 ARM64 |
| Python | 3.11+ | 3.12 |
| Network | WiFi 5 / Ethernet | Ethernet (stable for Telegram/API) |

## One-Shot Setup (Preferred)

```bash
# 1. Install Hermes Agent
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc

# 2. Setup Hermes (model, API key)
hermes model

# 3. Sync A-Wiki brain → Hermes (one command)
bash scripts/hermes/awiki-init-pi5.sh

# 4. Optional: Telegram + Dashboard
bash scripts/hermes/awiki-init-pi5.sh --full
```

Script `awiki-init-pi5.sh` does ALL of this automatically:
| Step | What |
|------|------|
| 1 | Clone/pull A-Wiki repo |
| 2 | Link 20 lifecycle skills → `~/.hermes/skills/lifecycle/` |
| 3 | Link meta-skill (awiki-lifecycle-router) → `~/.hermes/skills/awiki/` |
| 4 | Link 4 A-Wiki native skills (debug-mantra, scrutinize, grill-me, post-mortem) |
| 5 | Link 4 agent personas → `~/.hermes/agents/` |
| 6 | Register lifecycle config → `~/.hermes/config.d/awiki-lifecycle.json` |
| 7 | Install session start hook → `~/.hermes/hooks/awiki-session-start.sh` |
| 8 | Set `A_WIKI_DIR`, skill paths in Hermes `.env` |
| 9 | Verify all links and configs |

## Manual Setup (Step by Step)

If you prefer to do it manually or troubleshoot:

### 1. Clone A-Wiki
```bash
git clone https://github.com/aase7en/A-Wiki.git ~/A-Wiki
cd ~/A-Wiki
bash scripts/setup-local.sh
```

### 2. Link Skills to Hermes
```bash
# Lifecycle skills (20 skills)
ln -s ~/A-Wiki/skills/engineering-lifecycle/*/ ~/.hermes/skills/lifecycle/

# Meta-skill (router)
ln -s ~/A-Wiki/skills/engineering-lifecycle/awiki-lifecycle-router/ ~/.hermes/skills/awiki/lifecycle-router/

# A-Wiki native skills (debug-mantra, scrutinize, grill-me, post-mortem)
ln -s ~/A-Wiki/skills/engineering/*/ ~/.hermes/skills/awiki/native/
```

### 3. Register Personas
```bash
mkdir -p ~/.hermes/agents
ln -s ~/A-Wiki/agents/code-reviewer.md ~/.hermes/agents/code-reviewer.md
ln -s ~/A-Wiki/agents/test-engineer.md ~/.hermes/agents/test-engineer.md
ln -s ~/A-Wiki/agents/security-auditor.md ~/.hermes/agents/security-auditor.md
ln -s ~/A-Wiki/agents/web-performance-auditor.md ~/.hermes/agents/web-performance-auditor.md
```

### 4. Register Lifecycle Config
```bash
mkdir -p ~/.hermes/config.d
cp ~/A-Wiki/scripts/hermes/lifecycle-config.json ~/.hermes/config.d/awiki-lifecycle.json
```

### 5. Install Session Hook
```bash
mkdir -p ~/.hermes/hooks
cp ~/A-Wiki/hooks/lifecycle-session-start.sh ~/.hermes/hooks/awiki-session-start.sh
chmod +x ~/.hermes/hooks/awiki-session-start.sh

# Register in hooks.json
echo '{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"bash ~/.hermes/hooks/awiki-session-start.sh"}]}]}}' > ~/.hermes/hooks.json
```

### 6. Set Environment
```bash
echo "export A_WIKI_DIR=$HOME/A-Wiki" >> ~/.hermes/.env
echo "export A_WIKI_LIFECYCLE_SKILLS=$HOME/.hermes/skills/lifecycle" >> ~/.hermes/.env
echo "export HERMES_AGENTS_DIR=$HOME/.hermes/agents" >> ~/.hermes/.env
```

## How Hermes Uses A-Wiki Brain

### Skill Discovery Flow
```
User: "สร้าง API task management"
  → Hermes reads lifecycle-config.json
  → Phase: DEFINE → skill: spec-driven-development
  → Agent writes spec, user approves
  → Phase: PLAN → skill: planning-and-task-breakdown
  → Phase: BUILD → skill: incremental-implementation + TDD
  → Phase: REVIEW → parallel fan-out:
      ├── code-reviewer (Staff Engineer)
      ├── security-auditor (OWASP check)
      └── test-engineer (coverage review)
  → Phase: SHIP → skill: shipping-and-launch
```

### Slash Commands in Hermes Chat
| Command | Maps To | Behavior |
|---------|---------|----------|
| `/spec` | `spec-driven-development` | Define requirements before code |
| `/plan` | `planning-and-task-breakdown` | Break into verifiable tasks |
| `/build` | `incremental-implementation` + TDD | Build slice by slice |
| `/test` | `debug-mantra` + TDD | Debug + fix with tests |
| `/review` | `scrutinize` + `code-simplification` + `security-and-hardening` | Quality gates |
| `/code-simplify` | `code-simplification` | Reduce complexity |
| `/ship` | `shipping-and-launch` + parallel fan-out | Pre-launch checklist + persona review |

### Telegram Bot Integration
```
User (Telegram): "ค้นหา esp32 temperature sensor ใน wiki"
  → Hermes gateway receive
  → A-Wiki FTS5 search (python3 scripts/wiki/search-wiki.py)
  → Summarize from wiki entities/concepts
  → Reply via Telegram

User (Telegram): "ช่วย review โค้ดไฟล์นี้"
  → Hermes spawns code-reviewer persona
  → Reads file via agent tool
  → Returns five-axis review (correctness, readability, architecture, security, performance)
```

## Lifecycle Phases (20 Skills)

| Phase | Skills | What Hermes Does |
|-------|--------|------------------|
| **DEFINE** | `spec-driven-development`, `idea-refine`, `grill-me` | Write spec → human reviews → proceed |
| **PLAN** | `planning-and-task-breakdown` | Decompose → verify acceptance criteria |
| **BUILD** | `incremental-implementation`, `test-driven-development`, `doubt-driven-development`, `source-driven-development`, `frontend-ui-engineering`, `api-and-interface-design`, `context-engineering` | Implement slice by slice, test first |
| **VERIFY** | `browser-testing-with-devtools`, `debug-mantra` | Reproduce → fix → guard |
| **REVIEW** | `code-simplification`, `security-and-hardening`, `performance-optimization`, `scrutinize` | Five-axis review, OWASP, security audit |
| **SHIP** | `git-workflow-and-versioning`, `ci-cd-and-automation`, `deprecation-and-migration`, `documentation-and-adrs`, `observability-and-instrumentation`, `shipping-and-launch`, `post-mortem` | Pre-launch checklist, staged rollout, rollback plan |

### Agent Personas (4 Specialists)

| Persona | Role | When Hermes Spawns It |
|---------|------|-----------------------|
| `code-reviewer` | Senior Staff Engineer, five-axis review | On `/review`, `/ship`, or explicit request |
| `test-engineer` | QA Specialist, coverage analysis | On `/test`, `/ship`, or explicit request |
| `security-auditor` | Security Engineer, OWASP audit | On `/review`, `/ship`, or auth-sensitive code |
| `web-performance-auditor` | Web Perf Engineer, Core Web Vitals | On `/webperf` or performance concern |

Orchestration rule: **Personas do NOT invoke other personas.** Only Hermes (as orchestrator) performs parallel fan-out.

## Docker Compose (Alternative)

```yaml
version: '3.8'
services:
  hermes:
    image: ghcr.io/nousresearch/hermes-agent:latest
    platform: linux/arm64
    volumes:
      - ~/.hermes:/root/.hermes
      - ~/A-Wiki:/A-Wiki:ro
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - A_WIKI_DIR=/A-Wiki
      - HERMES_AGENTS_DIR=/root/.hermes/agents
    restart: unless-stopped

  dashboard:
    image: python:3.11-slim
    platform: linux/arm64
    working_dir: /A-Wiki
    volumes:
      - ~/A-Wiki:/A-Wiki
    command: python3 scripts/live-dashboard/server.py
    ports:
      - "7790:7790"
    restart: unless-stopped
```

## Performance Notes

| Metric | RPi 5 8GB | RPi 5 16GB |
|--------|-----------|------------|
| Hermes idle RAM | ~200MB | ~200MB |
| Lifecycle skills loaded | ~50MB (SKILL.md cached) | ~50MB |
| Dashboard server | ~50MB | ~50MB |
| Telegram gateway | ~30MB | ~30MB |
| **Usable for other services** | ~6GB | ~14GB |

- **ไม่แนะนำ local LLM** → ใช้ API-based (DeepSeek V4 Flash, Gemini Flash, Qwen)
- Telegram gateway ใช้ RAM น้อยมาก (~30MB)
- Lifecycle skills เป็น plain text ขนาดเล็ก (~2,200 บรรทัดรวมทั้งหมด)
- Memory จริงที่ Hermes ใช้ขึ้นกับ model context window และจำนวน session

## Verifying the Integration

```bash
# Check skills are linked
hermes skills list
# Should show 20+ skills in lifecycle/

# Check personas
ls ~/.hermes/agents/

# Check config loaded
cat ~/.hermes/config.d/awiki-lifecycle.json

# Test A-Wiki brain
hermes chat -q "แนะนำ lifecycle workflow สำหรับสร้าง REST API"
# Hermes should route through: spec → plan → build → review → ship

# Test persona spawn
hermes chat -q "/review โค้ดของฉัน"

# Verify wiki search works (if Telegram gateway is set up)
hermes chat -q "ค้นหา: mqtt broker ใน wiki"
```

## Troubleshooting

| ปัญหา | วิธีแก้ |
|-------|--------|
| Skills not found | `hermes skills check` + verify symlinks in `~/.hermes/skills/lifecycle/` |
| Personas not spawning | Check `HERMES_AGENTS_DIR` path, verify `.md` files exist |
| Lifecycle config not loaded | Verify `~/.hermes/config.d/awiki-lifecycle.json` exists and is valid JSON |
| Telegram timeout | ใช้ Ethernet แทน WiFi, check bot token |
| Hook not firing | Check `~/.hermes/hooks.json` syntax, verify hook script path |
| Dashboard 404 | `cd ~/A-Wiki && python3 scripts/live-dashboard/server.py` |
| Memory high | `hermes cron pause` + reduce `max_turns` in config |
| `Illegal instruction` | ติดตั้ง Python 3.11 ARM64 binary (not 3.13 pre-release) |
| `hermes skills install` fails offline | Use `ln -s` method above — Hermes reads symlinked dirs |

## References

| File | Purpose |
|------|---------|
| `scripts/hermes/awiki-init-pi5.sh` | One-shot brain sync script |
| `scripts/hermes/lifecycle-config.json` | Hermes phase routing config |
| `hooks/lifecycle-session-start.sh` | Session start hook for lifecycle router |
| `skills/engineering-lifecycle/awiki-lifecycle-router/SKILL.md` | Meta-skill: intent→skill mapping |
| `agents/*.md` | 4 specialist personas |
| `commands/*.md` | 7 slash commands |
| `docs/runbooks/rpi5-docker-audit.md` | Docker compatibility audit |
