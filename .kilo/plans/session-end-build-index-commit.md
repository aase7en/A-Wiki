# Plan: Build Index + Commit + Session End Protocol

## 1. Build Indexes

### A. A-Wiki Wiki Index (FTS5)
```
python scripts/gen-index.py
```
จะ rebuild FTS5 search index + regenerate `wiki/context/overview-*.md` files

### B. KiloCode Code Index (0/121 → 100%)
จำเป็นต้องเปิด VS Code + KiloCode ไว้เพื่อให้ระบบ index โค้ดอัตโนมัติ
หรือใช้คำสั่ง trigger indexing ผ่าน Kilo CLI หากมี

## 2. Commit Changes

```
git status
git diff --stat
git add -A
git commit -m "feat(kilo): sync config to Drive + agent brain unification"
git push
```

📋 **ไฟล์ที่จะ commit** (ประมาณ 15 ไฟล์):
- `scripts/lib/render_kilo_config.py` — เพิ่ม fireworks-ai resolver
- `scripts/lib/kilo.jsonc.template` — เพิ่ม provider + indexing + agent prompts
- `agent-skills/awiki-brain-prompt.md` — ใหม่ (shared brain fragment)
- `.kilo/agents/*.md` — 7 ไฟล์ (เพิ่ม Session Start Protocol)
- `.kilo/command/awiki-session-start.md` — อัพเดท wiki context loading
- `drive/.secrets` — เพิ่ม FIREWORKS_API_KEY (gitignored! — ไม่ควร commit)
- `drive/.config/kilo/kilo.jsonc.template` — sync template (gitignored!)

⚠️ ไฟล์ใน `drive/` เป็น gitignored — จะ NOT appear ใน `git status`

**ไฟล์ที่จะเห็นใน git diff:**
- `scripts/lib/render_kilo_config.py`
- `scripts/lib/kilo.jsonc.template`
- `agent-skills/awiki-brain-prompt.md` (ใหม่)
- `.kilo/agents/architect.md`
- `.kilo/agents/code-reviewer.md`
- `.kilo/agents/code-simplifier.md`
- `.kilo/agents/code-skeptic.md`
- `.kilo/agents/docs-specialist.md`
- `.kilo/agents/frontend-specialist.md`
- `.kilo/agents/test-engineer.md`
- `.kilo/command/awiki-session-start.md`
- `.kilo/plans/kilo-config-sync-and-agent-unification.md` (plan file)

## 3. Session End Protocol

### Update log.md
```bash
echo "[$(date +%Y-%m-%d)] KiloCode config sync + agent brain unification
- Added fireworks-ai provider to portable config
- Added indexing section with GEMINI_API_KEY
- Created agent-skills/awiki-brain-prompt.md (shared brain fragment)
- Updated all 7 agents with Session Start Protocol
- Updated template inline agent prompts
- Synced template to Drive
- Rendered ~/.config/kilo/kilo.jsonc successfully
- All agents now follow A-Wiki brain workflow (Iron Laws, Cost-First, Swarm)" >> log.md
```

### Update session-memory
```bash
echo "

## 2026-06-19 — KiloCode Config Sync + Agent Unification

### Decisions
- Use template+renderer approach (NOT symlink) for config sync
- Agents reference AGENTS.md + shared fragment instead of embedding full rules
- fireworks-ai provider key stored in drive/.secrets

### Current State
- ~/.config/kilo/kilo.jsonc rendered from Drive template
- All 7 agents have Session Start Protocol
- awiki-brain-prompt.md is single source of truth for brain rules
- Template synced: drive/.config/kilo/kilo.jsonc.template

### Next Session
- Build KiloCode code index (0/121 → 100%)
- Verify session-memory.md.example can be deprecated" >> wiki/context/session-memory.md
```

## Commands to Run ( sequentially )
```bash
# 1. Build wiki index
python scripts/gen-index.py

# 2. Stage + commit
git add scripts/lib/render_kilo_config.py \
      scripts/lib/kilo.jsonc.template \
      agent-skills/awiki-brain-prompt.md \
      .kilo/agents/*.md \
      .kilo/command/awiki-session-start.md

git commit -m "feat(kilo): sync config to Drive + agent brain unification

- Add fireworks-ai provider to PROVIDER_SECRET_MAP + template
- Add indexing section with gemini apiKey placeholder
- Create agent-skills/awiki-brain-prompt.md (shared brain fragment)
- All 7 agents: add Session Start Protocol + AGENTS.md reference
- Template inline prompts: add Session Start Protocol prefix
- Update /awiki-session-start command with wiki context loading
- Sync template to drive/.config/kilo/kilo.jsonc.template
- Add FIREWORKS_API_KEY to drive/.secrets"

# 3. Session end
echo '...' >> log.md
echo '...' >> wiki/context/session-memory.md

# 4. Commit session end
git add log.md wiki/context/session-memory.md
git commit -m "chore: session end 2026-06-19 KiloCode config sync"

# 5. Push
git push
```

## ⚠️ Notes
- `drive/.secrets` และ `drive/.config/kilo/kilo.jsonc.template` อยู่ใน gitignored path — เก็บ sync ผ่าน Google Drive เองอัตโนมัติ ไม่ต้อง commit
- VS Code + KiloCode ต้องเปิดไว้เพื่อให้ code index (0/121) build อัตโนมัติ — ลองเปิด VS Code แล้วเปิด conversation ใหม่ใน Kilo
