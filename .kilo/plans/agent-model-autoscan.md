# Plan — Agent Model Auto-Scan + Source-of-Truth Consolidation

> ตอบคำถาม: ประมวลคำแนะนำจาก Gemini + ของจริงใน repo → ทำอะไรต่อ?
> ผู้ใช้ตัดสินใจแล้ว: (1) auto-apply ในกรอบปลอด (2) ย้าย model เข้า .md frontmatter + symlink (3) GHA รายสัปดาห์

---

## 0. TL;DR

**สิ่งที่ Gemini เสนอ:** สร้าง 12 ไฟล์ `.md` ใน `~/.config/kilo/agents/` พร้อม `model:` frontmatter + สคริปต์สแกน benchmark รายสัปดาห์ที่แก้ `model:` อัตโนมัติ

**ความจริงใน repo:**
- คุณมี **12 agent ครบ** อยู่แล้ว (7 `.md` ใน `.kilo/agents/` + 12 entries ใน `~/.config/kilo/kilo.jsonc`)
- **Fireworks $6 credit ถูกแปลงเป็นการผูกโมเดลไปแล้ว** (code/code-skeptic/frontend/test-engineer วิ่ง Fireworks ทั้งชุด)
- ชื่อโมเดลที่ Gemini เขียน (`claude-sonnet-4.6`, `deepseek-v4-pro`, `minimax/m3`) = **ไม่มีอยู่จริง** (ส่วน `qwen3p7-plus`/`deepseek-v4-flash` มีจริง)
- **Infrastructure scout มีพร้อม** (`model-scout-current.py`, `model-capability-scout.py`, `batch/scout.py`, `model-roster.conf`, `cost-routing.conf`, `providers.json`, `model-capability-scores.json`)

**สิ่งที่ "ใหม่จริง" มี 2 อย่าง:**
1. ย้ายการผูก `model:` จาก `kilo.jsonc` มาไว้ใน `.md` frontmatter (เพื่อพกติดตัว/แชร์)
2. สคริปต์สแกน benchmark รายสัปดาห์ + auto-apply ในกรอบปลอด

**แผนนี้ทำ:** รวม 2 อย่างเข้าระบบ A-Wiki ที่มีอยู่แล้ว โดยไม่ทำลายของเดิม + เคารพกฎ cost-first + Iron Laws

---

## 1. สถาปัตยกรรมที่จะสร้าง

### 1.1 แหล่งความจริง (Source of Truth)

| Agent | ประเภท | แหล่งความจริงของ model | GHA จัดการ? |
|-------|--------|----------------------|-------------|
| architect, code-reviewer, code-simplifier, code-skeptic, docs-specialist, frontend-specialist, test-engineer | Custom (มี .md) | `.kilo/agents/<name>.md` frontmatter (`model:` + `variant:`) | ✅ auto-apply ปลอดภัย |
| plan, ask, code, debug, orchestrator | Built-in overrides | `~/.config/kilo/kilo.jsonc` `agent.{name}.{model,variant}` (machine-local) | ❌ เสนอใน issue เท่านั้น |

**เหตุผลที่แยก:**
- Custom agents (7): มี prompt+permission ใน .md อยู่แล้ว → เพิ่ม `model:` ใน frontmatter = single source of truth, symlink global → repo ได้
- Built-in overrides (5): ถ้าสร้าง .md จะ **wipe built-in prompt** (Kilo docs ยืนยัน: .md body = prompt). วิธีเดียวที่ pin model+variant โดยไม่แตะ prompt คือ `kilo.jsonc` `agent.{name}.{model}` (docs ตัวอย่างนี้โดยตรง)
- GHA รันบน repo → แก้ได้แค่ไฟล์ใน repo → 5 built-ins จึงเป็น propose-only

### 1.2 Symlink strategy

```
~/.config/kilo/agents  →  $REPO_ROOT/.kilo/agents
```

- `~/.config/kilo/agents/` ปัจจุบันไม่มี → สร้าง symlink ได้เลย
- ทำให้ 7 custom agents ใช้ได้ทุกโปรเจกต์ในเครื่อง (global agents, precedence level 4)
- สำหรับ A-Wiki: project .md (level 5) ใช้โดยตรง

### 1.3 Cost-class boundaries (กรอบปลอด)

| Cost class | Rank | ตัวอย่างโมเดล | Auto-apply? |
|------------|------|---------------|-------------|
| `free` | 0 | gemini-flash, llama (groq), qwen (groq/fireworks), kimi (fireworks credit), deepseek-v4-flash (fireworks) | ✅ same class |
| `cheap-paid` | 1 | deepseek-chat, zai direct | ✅ same class |
| `premium-paid` | 2 | claude-opus (openrouter) | ✅ same class |
| `subscription` | -1 | zai-coding-plan (GLM 5.2 codeplan) | ไม่เปลี่ยน (paid subscription, model id ไม่เปลี่ยน) |

**กฎ:**
- Same cost class + capability gain ≥ min_gain → **auto-apply** (แก้ .md frontmatter)
- Tier up (rank เพิ่ม) → **propose only** (เปิด issue)
- Tier down (rank ลด, ถูกกว่า) → **auto-apply** (cost-first)
- Unmanaged agent → **propose only**

### 1.4 Weekly scan flow

```
GHA cron (Mon 02:41 UTC)
  ↓
checkout repo
  ↓
python scripts/agents/agent_model_scan.py --apply
  ↓
load policy + scorecard (committed, offline-first)
  ↓
best-effort refresh scorecard from leaderboards (reuse model-capability-scout)
  ↓
for each managed agent:
  - match current model → family → capability score
  - find best candidate in same cost class from allowed families
  - if gain ≥ min_gain → auto-apply (rewrite .md frontmatter)
  - if tier-up → propose (add to report)
  ↓
git diff --quiet? → exit
  ↓
if changed:
  - git commit (safe swaps only)
  - git push
  - create/update issue with tier-up proposals + summary
```

---

## 2. Implementation Tracks

### Track A — Consolidate agent source of truth

**ไฟล์ที่จะแก้:**

| ไฟล์ | การกระทำ |
|------|---------|
| `.kilo/agents/architect.md` | เพิ่ม `model: openrouter/anthropic/claude-opus-4.8` + `variant: max` ใน frontmatter |
| `.kilo/agents/code-reviewer.md` | เพิ่ม `model: google/gemini-3.5-flash` |
| `.kilo/agents/code-simplifier.md` | เพิ่ม `model: groq/qwen/qwen3-32b` |
| `.kilo/agents/code-skeptic.md` | เพิ่ม `model: fireworks-ai/accounts/fireworks/models/kimi-k2p7-code` |
| `.kilo/agents/docs-specialist.md` | เพิ่ม `model: google/gemini-3.5-flash` |
| `.kilo/agents/frontend-specialist.md` | เพิ่ม `model: fireworks-ai/accounts/fireworks/models/qwen3p7-plus` |
| `.kilo/agents/test-engineer.md` | เพิ่ม `model: fireworks-ai/accounts/fireworks/models/kimi-k2p7-code` |
| `~/.config/kilo/kilo.jsonc` | Backup → `~/.config/kilo/kilo.jsonc.pre-agents-md.bak` → ลบ 7 custom agent entries (architect, code-reviewer, code-simplifier, code-skeptic, docs-specialist, frontend-specialist, test-engineer) จาก `agent` object, เก็บ 5 built-in overrides (plan, ask, code, debug, orchestrator) + top-level fields |
| `~/.config/kilo/agents` | สร้าง symlink → `$REPO_ROOT/.kilo/agents` |

**Precedence verification:**
- Kilo docs ยืนยัน: project `.md` (level 5) > global `kilo.jsonc` (level 2)
- ดังนั้น .md model: จะ override ได้ทันที
- Symlink ทำให้ global agents (level 4) = project agents (level 5) = ไฟล์เดียวกัน

### Track B — Policy + scorecard

**ไฟล์ที่จะสร้าง/แก้:**

| ไฟล์ | การกระทำ |
|------|---------|
| `wiki/context/agent-model-policy.json` | **สร้างใหม่** — cost classes, agents (12 ตัว), apply policy, candidate families |
| `wiki/context/model-capability-scores.json` | เพิ่ม `kimi` family (kimi-k2p7-code ใช้ใน 2 agents, ยังไม่มีใน scorecard) |

**Schema ของ policy:**
```json
{
  "schema_version": 1,
  "cost_classes": { "free": {"rank": 0}, "cheap-paid": {"rank": 1}, "premium-paid": {"rank": 2} },
  "apply_policy": {
    "auto_apply_within_same_cost_class": true,
    "tier_up_requires_confirmation": true,
    "min_capability_gain": 5,
    "revert_log": "wiki/context/agent-model-scan-log.jsonl"
  },
  "agents": {
    "<name>": {
      "file": ".kilo/agents/<name>.md",
      "current_model": "provider/model-id",
      "role_dimension": "swe_bench|reasoning|speed",
      "cost_class": "free|cheap-paid|premium-paid",
      "candidate_families": ["gemini-flash", "llama", ...],
      "managed": true
    }
  }
}
```

### Track C — Scanner script + tests (TDD)

**ไฟล์ที่จะสร้าง:**

| ไฟล์ | การกระทำ |
|------|---------|
| `tests/test_agent_model_scan.py` | **เขียนแล้ว** — 18 tests ครอบคลุม cost-class, safe-swap, frontmatter rewrite, candidate pick, dry-run/apply/revert |
| `scripts/agents/agent_model_scan.py` | **สร้างใหม่** — scanner + safe-apply + revert |

**Functions ที่ต้อง implement:**
- `cost_rank(policy, class_name) -> int`
- `is_safe_swap(policy, current_class, candidate_class) -> bool`
- `capability_for_model(scorecard, model_id, dimension) -> int`
- `decide_agent(agent_cfg, scorecard, policy) -> dict` (action: apply|propose|none)
- `rewrite_frontmatter_model(text, new_model) -> str` (line-based, no PyYAML dep)
- `run_scan(policy, scorecard, apply_changes, repo_root) -> dict`
- `revert_last(policy, repo_root)`
- `main()` CLI: `--dry-run` (default), `--apply`, `--revert`, `--offline`

**Reuse จาก `model-capability-scout.py`:**
- `load_scorecard()` → โหลด scorecard ที่ commit แล้ว
- `build_cache()` → refresh live จาก leaderboards (best-effort)
- `_match_family()` → map model id → family key

### Track D — GHA workflow + docs

**ไฟล์ที่จะสร้าง:**

| ไฟล์ | การกระทำ |
|------|---------|
| `.github/workflows/agent-model-scan.yml` | **สร้างใหม่** — weekly cron (Mon 02:41 UTC), checkout, run scan, commit safe swaps, create issue for tier-ups |
| `docs/protocols/agent-model-autoscan.md` | **สร้างใหม่** — protocol doc อธิบายระบบ, cost classes, safe bounds, revert process |

**GHA workflow structure (ตามสไตล์ `model-roster-refresh.yml`):**
```yaml
name: A-Wiki Agent Model Scan
on:
  schedule:
    - cron: "41 2 * * 1"
  workflow_dispatch:
permissions:
  contents: write
  issues: write
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup python
      - run scan --apply
      - if changed: commit + push
      - if tier-up proposals: create/update issue
```

---

## 3. Files to touch (summary)

| ไฟล์ | Track | Action |
|------|-------|--------|
| `.kilo/agents/architect.md` | A | edit (add model+variant) |
| `.kilo/agents/code-reviewer.md` | A | edit (add model) |
| `.kilo/agents/code-simplifier.md` | A | edit (add model) |
| `.kilo/agents/code-skeptic.md` | A | edit (add model) |
| `.kilo/agents/docs-specialist.md` | A | edit (add model) |
| `.kilo/agents/frontend-specialist.md` | A | edit (add model) |
| `.kilo/agents/test-engineer.md` | A | edit (add model) |
| `~/.config/kilo/kilo.jsonc` | A | backup + edit (remove 7 custom agents) |
| `~/.config/kilo/agents` | A | create symlink |
| `wiki/context/agent-model-policy.json` | B | create |
| `wiki/context/model-capability-scores.json` | B | edit (add kimi) |
| `tests/test_agent_model_scan.py` | C | **created** |
| `scripts/agents/agent_model_scan.py` | C | create |
| `.github/workflows/agent-model-scan.yml` | D | create |
| `docs/protocols/agent-model-autoscan.md` | D | create |

---

## 4. Verification

```bash
# A — agent .md files valid
for f in .kilo/agents/*.md; do head -1 "$f" | grep -q '^---' && echo "OK: $f"; done
# symlink works
ls -la ~/.config/kilo/agents
# global kilo.jsonc valid JSON
python3 -c "import json; json.load(open('$HOME/.config/kilo/kilo.jsonc'))"

# B — policy valid
python3 -c "import json; json.load(open('wiki/context/agent-model-policy.json'))"

# C — tests pass
python -m pytest tests/test_agent_model_scan.py -v
# dry-run scan
python scripts/agents/agent_model_scan.py --dry-run

# D — GHA valid
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/agent-model-scan.yml'))"

# overall
python scripts/gen-index.py --check
python scripts/agent-preflight.py
```

---

## 5. Risks / open questions

| ความเสี่ยง | Mitigation |
|-----------|-----------|
| แก้ global `kilo.jsonc` ผิด → agent loop พัง | Backup ก่อนแก้ (`kilo.jsonc.pre-agents-md.bak`); ถ้าพัง restore จาก backup |
| Symlink แตก → global agents หาย | Symlink เป็น relative path (`ln -s /absolute/path`) หรือ absolute; ถ้าแตก ลบ symlink แล้วสร้างใหม่ |
| Scorecard `[training]` → scan เสนอโมเดลแย่ | `min_capability_gain: 5` + offline-first (committed scores); live refresh เป็น best-effort |
| GHA commit ตรง → user ไม่รู้ | GHA เปิด issue summary ทุกครั้งที่เปลี่ยน; user review ได้ก่อน merge (ถ้าตั้ง branch protection) |
| Frontmatter rewrite พัง .md | Line-based (ไม่ใช่ YAML parser); preserve body + other keys; revert log สำหรับ undo |
| Built-in overrides ไม่ถูก auto-manage | Documented limitation; user สามารถย้ายเข้า repo `.kilo/kilo.jsonc` ภายหลังได้ |

---

## 6. Gate checks

- **Iron Law #1 (test first):** ✅ `tests/test_agent_model_scan.py` เขียนก่อน script
- **Iron Law #5 (no edit AGENTS.md/CLAUDE.md):** ✅ แผนนี้ไม่แตะ 2 ไฟล์นั้น
- **Brain Improvement Gate:** ✅ clear gain (single source of truth + auto-scan), lightweight (script+config+doc), cost-first (ทั้งแผน), cross-platform (key ใน drive/.secrets, symlink), public-safe (policy ไม่มี secret)
- **Universal Routing contract:** ✅ ไม่ hardcode model เป็น policy; auto-scan เคารพ cost-first (free นำหน้า paid)

---

## 7. Next steps (after plan approved)

1. Run `pytest tests/test_agent_model_scan.py` → confirm 18 tests fail (ImportError, module not found)
2. Implement `scripts/agents/agent_model_scan.py` → tests pass
3. Edit 7 `.md` files (add model+variant)
4. Backup + edit global `kilo.jsonc` (remove 7 custom agents)
5. Create symlink `~/.config/kilo/agents` → repo `.kilo/agents`
6. Create `wiki/context/agent-model-policy.json`
7. Add kimi to `model-capability-scores.json`
8. Create `.github/workflows/agent-model-scan.yml`
9. Create `docs/protocols/agent-model-autoscan.md`
10. Run full verification + dry-run scan
