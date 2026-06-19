# Plan: KiloCode Config Sync + Agent Brain Unification

## สถานะปัจจุบัน

### Task 1: Config Sync — มีระบบอยู่แล้ว, ต้อง enhance
- **Template**: `A-Wiki-Data/.config/kilo/kilo.jsonc.template` + `scripts/lib/kilo.jsonc.template`
- **Renderer**: `scripts/lib/render_kilo_config.py` — detect Drive, inject secrets, resolve paths
- **Agents symlink**: `~/.config/kilo/agents` → `.kilo/agents/` ✅
- **Commands sync**: renderer copies Drive commands → `~/.config/kilo/command/` ✅

**ช่องว่าง:**
1. `fireworks-ai` provider ไม่อยู่ใน `PROVIDER_SECRET_MAP` หรือ template (แต่ใช้จริง)
2. `FIREWORKS_API_KEY` ไม่มีใน `drive/.secrets` — ต้องเพิ่ม
3. `indexing.gemini.apiKey` hardcoded ใน rendered config, ไม่มีใน template
4. `setup-local.sh` ไม่ได้เรียก `setup-kilo-config.sh` อัตโนมัติ
5. `ANTHROPIC_API_KEY` อยู่ใน PROVIDER_SECRET_MAP แต่ไม่มีใน .secrets (optional, skip)

**Secrets ที่มีอยู่แล้ว:** GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, DEEPSEEK_API_KEY, ZHIPU_API_KEY, PIXELLAB_API_TOKEN

### Task 2: Agent Brain — ยังไม่ได้ทำ
- 7 agents ใน `.kilo/agents/` — มี 3 ตัวที่มี Session Start Protocol
- ไม่มี shared brain fragment
- Template inline prompts ไม่มี Iron Laws / cost-first / swarm references

---

## แผน 8 Phases

### Phase 1: เพิ่ม fireworks-ai ใน portable config system

**`scripts/lib/render_kilo_config.py`** — เพิ่มใน `PROVIDER_SECRET_MAP`:
```python
"fireworks-ai": "FIREWORKS_API_KEY",
```

**`scripts/lib/kilo.jsonc.template`** — เพิ่ม provider block:
```json
"fireworks-ai": {
  "options": {
    "apiKey": "__SECRET_FIREWORKS_API_KEY__"
  }
}
```

**`drive/.secrets`** — เพิ่ม:
```
FIREWORKS_API_KEY=fw_E2xLkk1Xy136j79uNg5Zsc
```

### Phase 2: เพิ่ม indexing section ใน template

**`scripts/lib/kilo.jsonc.template`** — เพิ่ม `indexing` section:
```json
"indexing": {
  "enabled": true,
  "provider": "gemini",
  "model": "gemini-embedding-001",
  "vectorStore": "lancedb",
  "gemini": {
    "apiKey": "__SECRET_GEMINI_API_KEY__"
  }
}
```
(reuse GEMINI_API_KEY ที่มีอยู่แล้ว)

### Phase 3: เพิ่ม step ใน setup-local.sh

**`scripts/setup-local.sh`** — เพิ่ม step หลัง setup drive/ links:
```bash
echo "[X/X] Rendering KiloCode portable config..."
if bash "$REPO_ROOT/scripts/setup-kilo-config.sh" 2>/dev/null; then
  echo "  OK — KiloCode config rendered"
else
  echo "  WARN: KiloCode config render failed (non-fatal)" >&2
fi
```

### Phase 4: สร้าง shared A-Wiki Brain fragment

**สร้างใหม่: `agent-skills/awiki-brain-prompt.md`**

Content สรุปจาก AGENTS.md:
- Iron Laws 9 ข้อ (summary)
- Cost-First Decision Pyramid 6 ระดับ
- Session Start Protocol steps
- Brain Improvement Gate (1-line)
- Core Rules summary (commit to main, kebab-case, confidence markers, 3-layer output)
- Swarm Intelligence (SCOUT → ALLOCATE → VALIDATE)

### Phase 5: อัพเดท agent definitions (7 files)

แต่ละ `.kilo/agents/*.md` จะเพิ่ม **Session Start Protocol** block หลัง YAML frontmatter:

```markdown
## Session Start Protocol
At the start of every session:
1. Run: `/awiki-session-start`
2. Read `AGENTS.md` — Iron Laws, Cost-First Pyramid, Swarm Protocol, Core Rules
3. Read `wiki/context/wiki-overview.md` — wiki structure + stats
4. Read `wiki/context/session-memory.md` — cross-session decisions + TODOs
5. Internalize `agent-skills/awiki-brain-prompt.md` — A-Wiki Brain fragment

You MUST follow the Iron Laws and Cost-First Pyramid defined in AGENTS.md.
Never skip the session start protocol.
```

Agents ที่ต้องอัพเดท:
- `architect.md` — เพิ่ม protocol
- `code-reviewer.md` — เพิ่ม protocol
- `code-simplifier.md` — เพิ่ม protocol
- `code-skeptic.md` — replace existing protocol with enhanced version
- `docs-specialist.md` — เพิ่ม protocol
- `frontend-specialist.md` — replace existing protocol with enhanced version
- `test-engineer.md` — replace existing protocol with enhanced version

### Phase 6: อัพเดท template inline agent prompts

**`scripts/lib/kilo.jsonc.template`** — เพิ่ม Session Start Protocol prefix ในทุก agent prompt:
```
At session start: read AGENTS.md for Iron Laws + Cost-First Pyramid. Read wiki/context/wiki-overview.md and wiki/context/session-memory.md. Follow agent-skills/awiki-brain-prompt.md.\n\n
```
(เพิ่มต้นแต่ละ agent prompt string)

**`drive/.config/kilo/kilo.jsonc.template`** — copy จาก repo template

### Phase 7: อัพเดท /awiki-session-start command

**`.kilo/command/awiki-session-start.md`** — เพิ่ม wiki context loading:
```markdown
## Session Context Loading
After emitting the session start event, read these files:
1. `AGENTS.md` — universal brain config (Iron Laws, Cost-First, Swarm)
2. `wiki/context/wiki-overview.md` — wiki structure
3. `wiki/context/session-memory.md` — cross-session memory
4. `agent-skills/awiki-brain-prompt.md` — brain fragment
```

### Phase 8: ทดสอบ + Sync Drive

```bash
# Verify template renders correctly
bash scripts/setup-kilo-config.sh --check

# Force re-render with new providers
bash scripts/setup-kilo-config.sh --force

# Verify rendered config has fireworks-ai + indexing
cat ~/.config/kilo/kilo.jsonc | python3 -c "import sys,json; d=json.load(sys.stdin); print('Providers:', list(d.get('provider',{}).keys())); print('Indexing:', 'gemini' in str(d.get('indexing',{})))"

# Sync template to Drive
cp scripts/lib/kilo.jsonc.template "drive/.config/kilo/kilo.jsonc.template"
```

---

## ไฟล์ทั้งหมดที่จะแก้ไข (14 files)

| # | File | Action | Phase |
|---|------|--------|-------|
| 1 | `scripts/lib/render_kilo_config.py` | เพิ่ม `fireworks-ai` ใน PROVIDER_SECRET_MAP | 1 |
| 2 | `scripts/lib/kilo.jsonc.template` | เพิ่ม fireworks-ai provider + indexing section + agent prompt prefix | 1,2,6 |
| 3 | `scripts/setup-local.sh` | เพิ่ม step เรียก setup-kilo-config.sh | 3 |
| 4 | `agent-skills/awiki-brain-prompt.md` | **สร้างใหม่** — shared brain fragment | 4 |
| 5 | `.kilo/agents/architect.md` | เพิ่ม Session Start Protocol | 5 |
| 6 | `.kilo/agents/code-reviewer.md` | เพิ่ม Session Start Protocol | 5 |
| 7 | `.kilo/agents/code-simplifier.md` | เพิ่ม Session Start Protocol | 5 |
| 8 | `.kilo/agents/code-skeptic.md` | อัพเดท Session Start Protocol | 5 |
| 9 | `.kilo/agents/docs-specialist.md` | เพิ่ม Session Start Protocol | 5 |
| 10 | `.kilo/agents/frontend-specialist.md` | อัพเดท Session Start Protocol | 5 |
| 11 | `.kilo/agents/test-engineer.md` | อัพเดท Session Start Protocol | 5 |
| 12 | `.kilo/command/awiki-session-start.md` | เพิ่ม wiki context loading | 7 |
| 13 | `drive/.config/kilo/kilo.jsonc.template` | sync จาก repo | 6 |
| 14 | `drive/.secrets` | เพิ่ม FIREWORKS_API_KEY | 1 |

---

## ผลลัพธ์หลังทำเสร็จ

1. **Multi-machine config sync**: เครื่องใหม่แค่รัน `bash scripts/setup-local.sh` → ได้ config ครบ (providers, API keys, agents, commands, skills paths)
2. **All agents have A-Wiki brain**: ทุก agent ทำ Session Start Protocol, รู้ Iron Laws, Cost-First, Swarm
3. **Single source of truth**: แก้ template ที่เดียว → sync ทุกเครื่องผ่าน Google Drive
4. **Secretsปลอดภัย**: API keys อยู่ใน `drive/.secrets` (gitignored), ไม่ hardcode ใน template
