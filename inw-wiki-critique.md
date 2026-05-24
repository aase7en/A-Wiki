# InW-Wiki วิจารณ์ + เปรียบเทียบกับ A-Wiki

> วิเคราะห์ ณ 2026-05-24 โดยเปรียบเทียบกับ [InW-Wiki](/Users/aase7en/Desktop/InW-Wiki) (commit ca. 2026-05-18)  
> และ 14 repo อ้างอิง

---

## 1. จุดเด่นของ InW-Wiki (A-Wiki มีอะไรให้เรียนรู้)

### 1.1 Cost-First Decision Pyramid ⭐⭐⭐⭐⭐

InW-Wiki มี Level -1 ถึง 4 ที่ **บังคับใช้อัตโนมัติ** ทุกครั้งที่ Claude จะทำงาน — นี่คือสิ่งที่ทำให้ InW-Wiki โดดเด่นกว่า A-Wiki ตรง:

| Level | InW-Wiki | A-Wiki | ปัญหา A-Wiki |
|-------|----------|--------|-------------|
| **-1** | FTS5 + query-graph.py ก่อน Grep/Read | มี `search-wiki.py` แต่ `gen-index.py` ไม่ chain regen FTS5 อัตโนมัติ → index ล้าสมัย | dev ไม่ทำ manual regen |
| **0** | Hook 6 ตัวตอน SessionStart | มี hook แต่ไม่ซับซ้อน | A-Wiki ขาด apikey check + binary scan |
| **1** | ask-notebooklm.py (Gemini direct — free) | ยังไม่มี | ต้องพึ่ง Claude token ตลอด |
| **2** | OpenRouter free/cheap models | ยังไม่มี delegate.sh | ขาด free model routing |
| **3** | Subagent Haiku delegation | มี delegate-subagent แต่ไม่ค่อยใช้ | dev ไม่รู้ workflow |
| **4** | Claude writing | A-Wiki มีแล้ว | ok |

**Recommendation**: A-Wiki ควรเพิ่ม:
- `ask-notebooklm.py` — cross-file synthesis via free Gemini API (ตัด Claude token)
- `delegate.sh` — multi-model free tier router (Gemini → DeepSeek → Groq → OpenRouter)
- Cost pyramid enforcement ใน CLAUDE.md

### 1.2 Hook Pipeline ที่ซับซ้อนกว่า ⭐⭐⭐⭐

InW-Wiki มี **hooks 16 ตัว** ใน 5 lifecycle events:

```
SessionStart (6 hooks):  git-pull, wiki-context, binary-scan,
                         show-todos, apikey-check, build-pharmacy-db
PreToolUse   (5 hooks):  staleness-check, claudemd-lock, raw-immutable,
                         destructive-git, no-branch, secret-leak
PostToolUse  (5 hooks):  handoff-auto-export, post-wiki-edit-gen-index,
                         checkpoint-on-todo, checkpoint-on-commit, post-push-todo
Stop         (2 hooks):  agent-switch, auto-commit
PostCompact  (1 hook):   restore wiki context hint
```

A-Wiki มี hooks แต่ **น้อยกว่า + ไม่ครอบคลุม**:
- ขาด `secret-leak` check ก่อน commit
- ขาด `apikey-check` ตอนเริ่ม session
- ขาด `no-branch` enforcement
- ขาด `post-wiki-edit-gen-index` → ต้อง regen overviews manually

### 1.3 Edit Protection (2-layer) ⭐⭐⭐⭐

InW-Wiki มี defense-in-depth 2 ชั้น:
1. **Soft lock** — Claude มีจิตสำนึก หยุดก่อนแก้ CLAUDE.md
2. **Hard lock** — PreToolUse hook ตรวจ env var `WIKI_UNLOCK`

A-Wiki มี lock.txt + lock.example แต่ **ขาด hook enforcement** — Claude สามารถแก้ CLAUDE.md ได้ถ้า dev ไม่ได้บอก

### 1.4 Multi-Device Sync Daemon ⭐⭐⭐⭐

`scripts/sync.py` — 202 บรรทัด Python:
- `--now`: one-shot pull/commit/push
- `--daemon`: background file watcher (debounce 5s, pull remote ทุก 5 min)
- Device name detection via `~/.wiki-device` + hostname fallback
- Conflict resolution with `-Xtheirs`

A-Wiki **ไม่มี** — ใช้ `.github/workflows/wiki-sync.yml` แบบ GitHub Actions pull request workflow แต่ **กฎ repo คือ commit ตรง main ห้าม branch/PR** → workflow ขัดแย้งกับกฎ

### 1.5 Pharmacy Domain ที่ครบวงจร ⭐⭐⭐

InW-Wiki มี pharmacy workflow จริง:
- `scripts/pharmacy_lookup.py` (33.7 KB) — ระบบ query pharmacy database
- `scripts/build_pharmacy_db.py` — build database
- `scripts/compare_delivery.py` (24.9 KB) — เปรียบเทียบการส่งยา
- `scripts/fill-waste-form.py` (16.2 KB) — ฟอร์ม waste management
- `scripts/save-waste-cookie.py` — persistence
- `index-pharmacy.md` (5.2 KB) — 5 domain indexes

A-Wiki มีแค่ `index-pharmacy.md` แบบพื้นฐาน — ขาด automation scripts

### 1.6 OpenRouter Free Model Router ⭐⭐⭐

`scripts/delegate.sh` (384 บรรทัด):
- 7 task types → 3 cost tiers
- 5 engine wrappers (Gemini direct, DeepSeek direct, OpenRouter, Groq, Anthropic)
- **Race mode** — parallel model requests, first response wins
- **Self-healing** — model-not-found → scouter → retry, rate-limit → report, network → retry after 3s
- `update-model-roster.sh` (11.4 KB) — dynamic model discovery

A-Wiki มีแค่ `scripts/swarm/delegate.sh` ที่ใช้ OpenRouter API — ขาด tier system + race mode + chain fallback

---

## 2. จุดที่ A-Wiki เหนือกว่า InW-Wiki

### 2.1 Swarm Intelligence Layer ⭐⭐⭐⭐⭐

A-Wiki มี 3 directory ที่ InW-Wiki ไม่มี:
- `agent-skills/swarm-intelligence/` — model-scouter.md, agile-swarm.md
- `agent-skills/engineering/` — debug-mantra, post-mortem, scrutinize
- `agent-skills/productivity/` — management-talk

### 2.2 Ecosystem Skills (ECC + 9arm) ⭐⭐⭐⭐

A-Wiki มี ecosystem skills เชื่อมโยง 4 repos:
- `skills/claude-thai/` — 14 skills (thai-address, thai-id-validate, thai-pdpa, etc.)
- `skills/ecosystem/` — 100+ skills from everything-claude-code
- `scripts/ecosystem/link-my-skills.sh` — symlink connector

InW-Wiki มีแค่ 4 skills ใน `.claude/skills/` — ขาด ecosystem integration

### 2.3 Knowledge Graph ที่ 5 Edge Types ⭐⭐⭐⭐

A-Wiki: อัปเกรดจาก Phase 2 เป็น 5 typed edges:
- `depends_on`, `implements`, `synthesizes`, `relates`, `deprecated_by`
- `query-graph.py` — สนับสนุน directed queries (`--neighbors`, `--hubs`, `--orphans`, `--deprecated`)

InW-Wiki: graph เดิมก็มี (build-wiki-graph.py 9.1 KB) แต่แนวโน้มการใช้ edges น้อยกว่าแบบ typed — A-Wiki ควรอัปเกรด graph กลับไป InW-Wiki (หรือตั้ง script ให้ InW-Wiki อัปเกรดตาม)

### 2.4 Auto-Generated Domain Indexes ⭐⭐⭐

A-Wiki มี Phase 3: `gen-domain-indexes.py` สร้าง 4 indexes:
- `index-iot.md`, `index-env.md`, `index-ai-tools.md`, `index-pharmacy.md`
- Weighted scoring (`type:entity > type:synthesis > type:concept`)
- สร้างอัตโนมัติทุกครั้งที่รัน `gen-index.py`

InW-Wiki: indexes ถูกสร้างและแก้ manual → ต้อง maintenance

### 2.5 arXiv Integration ⭐⭐⭐

A-Wiki มี Phase 4: `fetch-arxiv.py` — 2-tier pipeline:
- Tier 1: instant title/abstract (4 domains: IoT/cs.NI, env/physics.ao-ph, AI/cs.AI, pharmacy/q-bio.QM)
- Tier 2: full-text on demand
- Auto-dedup by arxiv ID

InW-Wiki ไม่มี — การ capture paper ต้อง manual

---

## 3. วิจารณ์ข้อควรปรับปรุงของ InW-Wiki

### 3.1 Scalability ของ Hook Pipeline

InW-Wiki มี hooks 16 ตัว → **ทุกคำสั่ง Bash ผ่าน 6-8 hooks**:
```
PreToolUse[Edit]: staleness + 2 hooks = 3 checks
PreToolUse[Bash]: 3 hooks = 3 checks
PostToolUse[Edit]: 2 hooks
PostToolUse[Bash]: 2 hooks
```
ใน session ยาวๆ อาจเสีย ~0.5-1.5s ต่อ tool call — เล็กน้อยแต่สะสม

**Recommendation**: รวม hooks ที่เร็วเป็น async check หรือ caching layer

### 3.2 Memory Fragmentation

`.wiki-index.db` (1.4 MB SQLite), `.wiki-graph.json` (163 KB), `logs.md` (84 KB) — **ไม่ unified**:
- FTS5 ต้อง rebuild ทุกครั้งที่ wiki เปลี่ยน
- Graph JSON เก็บใน memory ตอน query
- log.md เป็น append-only → อาจใหญ่เกิน control

**Recommendation**: รวมเป็น single SQLite หรือ RocksDB ที่มีทั้ง FTS5 + graph adjacency + log

### 3.3 Domain Boundaries ที่ตายตัว

InW-Wiki แบ่ง 4 domains (iot, env, ai-tools, pharmacy) → **pain points**:
- Cross-domain entity ต้องเลือกแค่ domain เดียว (เช่น weather station → IoT หรือ Env?)
- synthesis ต้อง manual สร้างหน้าใหม่
- index-{domain}.md ต้อง maintain manual → dev ลืมอัปเดตบ่อย

**Recommendation**: dynamic domain tagging (multi-label) + filter-based query แทน directory boundary

### 3.4 Lock Mechanism ที่ Deterrent-only

Lock เป็น plaintext → deterrent ไม่ใช่ security:
- `.claude/lock.txt` gitignored → dev ลืมตั้งตอน clone
- Hook ใช้ `python3 parse JSON` → fail-open ถ้า python3 ไม่มี
- ไม่มี audit trail — ไม่รู้ว่าใคร unlock เมื่อไหร่

### 3.5 No Automated Quality Check

InW-Wiki: lint manual ผ่าน `@skeptical-reviewer` agent — **ไม่มี automated checker**:
- ตรวจ orphan pages → manual
- ตรวจ broken links → manual
- ตรวจ stale/outdated → manual

A-Wiki Phase 5 (`review-check.py`) แก้ปัญหานี้ — ควร merge กลับไป InW-Wiki

---

## 4. สิ่งที่ A-Wiki ควรปรับปรุงด่วน

จัดลำดับตาม ROI (impact / effort):

### P0 — ต้องทำ (high impact, low effort)

1. **Add InW-Wiki hooks** — copy hooks ที่ขาด:
   - `check-secret-leak.sh`
   - `check-bash-no-branch.sh`
   - `post-wiki-edit-gen-index.sh`
   - **Effort**: ~1 ชม.
   - **Impact**: ป้องกัน accident ที่ serious

2. **Enable FTS5 auto-regen** — แก้ `gen-index.py` chain ให้ regen `search-wiki.py` index ทุกครั้งที่ wiki เปลี่ยน
   - **Effort**: ~30 นาที
   - **Impact**: dev ไม่ต้อง manual regen

3. **Fix GitHub Actions conflict** — ถ้ากฎคือ "commit ตรง main" → ต้องถอด branch/PR workflow ออก
   - **Effort**: ~15 นาที
   - **Impact**: ป้องกัน workflow conflict

### P1 — ควรทำ (high impact, medium effort)

4. **Copy ask-notebooklm.py + delegate.sh** จาก InW-Wiki — cross-file synthesis ฟรี + free model router
   - **Effort**: ~2 ชม. (copy + test)
   - **Impact**: ประหยัด Claude token ~40-60% สำหรับ search/lookup/synthesis

5. **Add Cost Pyramid to CLAUDE.md** — เปลี่ยนให้บังคับใช้ Level -1 ก่อนทำงานทุกครั้ง
   - **Effort**: ~1 ชม.
   - **Impact**: token reduction โดยตรง

6. **Merge review-check.py ไป InW-Wiki** — 6-layer health checker
   - **Effort**: ~30 นาที
   - **Impact**: wiki quality improvement automation

### P2 — อนาคต (high impact, high effort)

7. **Unified storage layer** — SQLite ที่เก็บ FTS5 + graph + logs → single source of truth
   - **Effort**: ~2-3 วัน
   - **Impact**: reliability + query performance

8. **Dynamic domain tagging** — multi-label tags แทน directory-based domains
   - **Effort**: ~3-4 วัน (แก้ templates, gen-index, search, graph)
   - **Impact**: หมดปัญหา cross-domain entity

9. **Sync daemon** — copy `sync.py` + cross-device workflow
   - **Effort**: ~2 ชม.
   - **Impact**: multi-device sync ที่ไม่มี bottleneck GitHub Actions

---

## 5. วิจารณ์ 14 Repos อ้างอิง

### 5.1 Repos ที่ควรศึกษาเพิ่มเติม (high signal)

| Repo | Signal | เหตุผล |
|------|--------|--------|
| **OmegaWiki** (skyllwt) | 🔥🔥🔥🔥🔥 | Wiki ที่ดีที่สุดใน ecosystem — data flow ที่ clean, entity relationship diagram, automatic backlinks |
| **LLM-Wiki-Skilled** (TrueHOOHA) | 🔥🔥🔥🔥 | Skill orchestration layer ที่ overlap กับ A-Wiki's swarm — ควรศึกษาว่าทำ agent routing ยังไง |
| **ai-modules** (theafh) | 🔥🔥🔥🔥 | Knowledge management plugin — modular architecture ที่ A-Wiki ควร adapt |
| **MiroFish** (666ghj) | 🔥🔥🔥 | Git-based knowledge mesh — interesting แต่อาจซับซ้อนเกินไปสำหรับ A-Wiki |
| **GitNexus** (abhigyanpatwari) | 🔥🔥🔥 | Git repository integration — ควรศึกษาการ merge workflow |

### 5.2 Repos ที่ redundancy สูงกับ A-Wiki

| Repo | Redundancy | ข้อสังเกต |
|------|------------|-----------|
| **everything-claude-code** (affaan-m) | 90% | A-Wiki มี ecosystem skills อยู่แล้ว → copy-skips skills ที่มีอยู่ |
| **9arm-skills** (thananon) | 80% | thai skills → A-Wiki มีครบแล้ว (claude-thai/skills) |
| **FrameCode-VibeWork** (Sistema2D) | 70% | overlap กับ productivity layer → skip |
| **synto** (kytmanov) | 60% | synthesis tool — A-Wiki มี ask-notebooklm.py แล้ว |
| **synthadoc** (axoviq-ai) | 55% | similar concept — ศึกษาเพิ่มเติมไม่เร่ง |

### 5.3 Repos ที่มี unique value

| Repo | Unique Value | A-Wiki ควรทำอะไร |
|------|-------------|-----------------|
| **long-term-agent-memory** (eslamgenio) | Episodic + semantic memory layer | ศึกษา + integrate เป็น optional layer |
| **obsidian-llm-wiki-local** (kytmanov) | Obsidian integration best practices | อัปเดต docs/protocols/OBSIDIAN_SKILLS.md |
| **llm-wiki-manager** (sametbrr) | API-first wiki management | ศึกษา API design → อาจ merge API layer |
| **LLM-WIKI-MCP** (Electro-resonance) | MCP server for wiki | MCP integration → A-Wiki ควรรองรับ |
| **LLM-Wiki-Agent-Workflow-Demo** (WayneChou-bot) | Workflow demo | ศึกษา CI/CD pipeline |
| **link** (gowtham0992) | Link management | อาจ merge concept |

---

## 6. สรุป Strategic Recommendations

### Short-term (1-2 sessions)

1. 🔴 **Fix GitHub Actions workflow** — ห้าม branch/PR ถ้ากฎคือ commit ตรง main
2. 🔴 **Add secret-leak + no-branch hooks** — ป้องกัน accident
3. 🟡 **Copy ask-notebooklm.py + delegate.sh** — ประหยัด Claude token
4. 🟡 **Chain FTS5 regen** — dev ไม่ลืม manual regen

### Medium-term (3-5 sessions)

5. 🟢 **Unified storage layer (SQLite)** — FTS5 + graph + logs
6. 🟢 **Merge review-check.py → InW-Wiki** — wiki quality automation
7. 🟢 **Add Cost Pyramid to CLAUDE.md** — token discipline

### Long-term (6-10 sessions)

8. 🔵 **Dynamic domain tagging** — เลิก directory-based domain
9. 🔵 **Sync daemon** — multi-device sync
10. 🔵 **OmegaWiki data flow ศึกษา** — entity relationship diagram, auto-backlinks

---

*วิเคราะห์โดย Cline — 2026-05-24*