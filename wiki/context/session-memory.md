# Session Memory

> **Purpose**: เก็บประเด็นค้างคา + decisions สำคัญข้าม session — กันการลืมเรื่องเก่า
> **Auto-load**: ใช่ — CLAUDE.md §📚 Wiki Context Auto-Load อ่านทุก session
> **Size cap**: 500 tokens (~10 sessions rolling) — เก่าสุดถูกตัดเมื่อเกิน
> **Updated by**: SESSION END Protocol (Claude เขียน) + user แก้ได้ตรงๆ

---

## 🔥 Active TODOs (cross-session)

> SessionStart hook reads only unchecked **`- [ ]`** items in this block.
> Keep this list small (target ≤12). Move project/dream backlog to `wiki/context/project-backlog.md`.
> Done = delete or move to `log.md`; cancelled = delete.

- [ ] **[a-wiki-hardening]** Continue platform hardening Step 6 review noise, Step 7 sync reliability, Step 8 platform docs
- [ ] **[a-wiki-infra]** Test cloud-link + drive_secrets บน Work PC และ WSL/Linux Docker หลัง pull รอบล่าสุด

---

## 📌 Sticky (ไม่หมดอายุ — pin ไว้)

> Pin หัวข้อที่ต้องจำตลอด — design decisions, user preferences, recurring blockers

- **⚡ SESSION START RULE**: ทุก session ใหม่ — Claude ต้องแสดง open TODOs ใน **first visible message** (data อยู่ใน system-reminder แล้ว = 0 extra tokens) รูปแบบ:
  ```
  🔥 ค้างอยู่ (N items): [dream] 🏠 Sunday Estate | 🤖 Personal AI Agent | ... + [wiki-brain/project] ...
  มีอะไรให้ช่วยวันนี้ไหม?
  ```
  ห้ามละเว้น — user ใช้ mobile และไม่เห็น system-reminder

- **Token-first philosophy**: ทุก feature ต้องคิด token cost ก่อน. Pyramid Level 0 (hook) → 4 (Sonnet). ดู CLAUDE.md §💰
- **Solo + multi-device workflow**: push main ตรงได้ — SessionStart hook pull main ก่อนทุก session = single brain. PR workflow ถูกถอดออก (2026-05-15) เพราะ over-engineering สำหรับ user คนเดียว
- **🚫 NO branch / NO PR**: Wiki นี้มีคนใช้คนเดียว — ห้ามสร้าง `claude/` branch, ห้ามใช้ `isolation: worktree`, ห้ามเปิด PR ทุกกรณี. commit ตรงลง main เท่านั้น
- **Edit Protection**: CLAUDE.md root ต้อง unlock ด้วย `export WIKI_UNLOCK=$(cat .claude/lock.txt)` — env หายเมื่อปิด terminal
- **Git storage**: Wiki หลักอยู่ที่ `/Users/aase7en/Desktop/InW-Wiki`; ไม่ใช้ Google Drive sync แล้ว; `.git/` เป็น directory ปกติใน repo; `~/git-data/` เหลือไว้เป็น stale backup ได้เท่านั้น
- **Multi-agent failover order**: `wiki-qwen`/`claude-router` (OpenRouter ⭐ seamless+hooks) → `gemini` (web search) → Codex Desktop → AI Studio → VS Code+Cline. รัน `bash scripts/agent-switch.sh` ก่อน handoff ทุกครั้ง. ดู `wiki/concepts/ai-tools/multi-agent-failover.md`

---

## 🗓️ Recent (last 10 sessions, newest top)

### [2026-05-30] p2-todo-hygiene-model-routing (Mac, Codex)

- **Done**: Fixed `scripts/update-model-roster.sh` embedded Python generation; roster refresh now completes against OpenRouter and refreshes `.tmp/model-router-policy.conf`.
- **Done**: Fixed shell quoting in `scripts/model-router-policy.py` so model-intel summaries containing backticks or `$()` do not execute during `source`.
- **Done**: Verified `bash scripts/delegate.sh search ...` works with current free-model keys.
- **Done**: Added `scripts/todo-health.py`, wired it into `scripts/verify-awiki-ready.py`, and moved non-session project/dream backlog to `wiki/context/project-backlog.md`.
- **Done**: Made arXiv refresh in `scripts/gen-index.py` opt-in (`--fetch-arxiv` or `AWIKI_GEN_INDEX_FETCH_ARXIV=1`) so normal index regeneration does not wait on four network calls.
- **Done**: Added canonical local `GEMINI_API_KEY` alias in `.claude/settings.local.json` without printing the secret.
- **Done**: Installed `requirements.txt` into current Python, verified `apsw`, and rebuilt sqlite-vec embeddings successfully.
- **Done**: Added `scripts/verify-cross-platform.py --build-vec` for Mac/Linux/Windows clone verification; Mac pass confirmed.
- **Done**: Skill quality now reports 39 OK, 0 WARN, 0 FAIL after adding owned-skill eval coverage and missing frontmatter.
- **Next**: Continue platform hardening Step 6 review noise, Step 7 sync reliability, Step 8 platform docs; verify Work PC/WSL with `python3 scripts/verify-cross-platform.py --build-vec`.

### [2026-05-29] a-wiki-handoff-priority-plan (Work PC, Codex)

- **Done**: Added `docs/runbooks/a-wiki-handoff-priority-plan.md` with remaining work split by P0-P3 for the next computer/agent.
- **Verify**: Work PC preflight is clean; Drive `.secrets` health check reports readable key names only; secret hook accepts clean payload.
- **Next**: On Mac, run `git pull origin main`, `python scripts/agent-preflight.py`, and `python scripts/health_external_data.py`; then continue P1 Codex local config template sync or P2 bootstrap depending on failures.

### [2026-05-29] a-wiki-hardening-step-5-hook-policy (Work PC, Codex)

- **Done**: Rewrote tracked Claude `stop-auto-commit.sh` and local Codex stop hook to refuse non-`main` sessions instead of merging branches; replaced Windows-only absolute local `.codex/hooks.json` hook paths with relative paths; added hook path audit to `scripts/agent-preflight.py` with WARN for missing local configs.
- **Verify**: `python -m pytest tests/test_agent_preflight.py tests/test_hook_policy.py -q` passed; `python scripts/agent-preflight.py --skip-remote` reports hook command paths OK while worktree is dirty.
- **Next**: Finish Step 5 by adding a tracked template/setup sync path for ignored `.codex/*` and checking Gemini/Antigravity hook parity where `.gemini/settings.json` exists; then Step 6 review noise profiles.

### [2026-05-29] a-wiki-hardening-step-4-agent-preflight (Work PC, Codex)

- **Done**: Added `scripts/agent-preflight.py` as a shared start-of-session safety check for platforms with partial/no hooks; it checks branch, origin reachability, working tree summary, Drive-backed `A-Wiki-Data`, generated context freshness, core hook presence, and platform instruction drift.
- **Done**: Added `tests/test_agent_preflight.py`; documented `python scripts/agent-preflight.py` in AGENTS/Claude/Gemini/Cursor/Cline/Windsurf/Copilot instructions.
- **Next**: Step 5 = hook parity and policy cleanup, especially stop-auto-commit branch behavior and hook command drift.

### [2026-05-29] a-wiki-hardening-step-3-script-entrypoints (Work PC, Codex)

- **Done**: Replaced invalid `scripts/wiki/*.py` shim files with Python compatibility wrappers for `gen-index.py`, `hooks_runner.py`, `search-wiki.py`, `query-graph.py`, `build-wiki-index.py`, and `build-wiki-graph.py`; fixed Windows console encoding for search/review/gen-index chain output; excluded generated context outputs from review-check input to stop report self-feedback churn; fixed `gen-index.py` output path isolation so tests cannot write sample overview into the real repo; updated stale docs from `--dry-run` to `--check`.
- **Verify**: `python -m pytest tests/test_gen_index.py tests/test_drive_link_health.py tests/test_external_data_health.py tests/test_review_check.py -q` passed 43 tests; `python scripts/gen-index.py` now chains through review-check; `python scripts/gen-index.py --check`, `python scripts/wiki/gen-index.py --check`, and `python scripts/wiki/search-wiki.py test` passed on Work PC.
- **Next**: Step 4 = portable agent preflight command for every platform/tool; include venv/dependency detection because `build-vec-index.py` still warns when `apsw` is missing on this machine.

### [2026-05-29] a-wiki-hardening-step-2-external-data-health (Work PC, Codex)

- **Done**: Updated `scripts/hooks/check_drive_link.py` for POSIX symlink + Windows Junction/ReparsePoint + `.drive-path` fallback; updated `scripts/drive_path.py` to resolve junction targets; added `scripts/health_external_data.py`; added tests in `tests/test_drive_link_health.py` and `tests/test_external_data_health.py`.
- **Verify**: `python -m pytest tests/test_drive_link_health.py tests/test_external_data_health.py -q` passed 5 tests; `python scripts/hooks/check_drive_link.py` reports cloud links OK; `python scripts/drive_path.py` resolves `L:\My Drive\A-Wiki-Data`; `python scripts/health_external_data.py` reports required folders OK, raw file count 54, and `.secrets` present without printing values.
- **Remaining**: Verify same commands on MacBook after pulling `origin/main`.
- **Next**: Step 3 = normalize script entrypoints and fix stale `--dry-run` docs.

### [2026-05-29] a-wiki-hardening-step-1-secret-safety (Work PC, Codex)

- **Done**: Added real `scripts/hooks/check_secret_leak.py`, restored `scripts/lib/drive_secrets.py` + `scripts/lib/__init__.py`, added tests in `tests/test_hooks.py` and `tests/test_drive_vault.py`, added `.gitignore` exceptions for tracked secret helper/hook files, and sanitized ignored local `.codex/config.toml` so it no longer stores plaintext API keys.
- **Verify**: `python -m pytest tests/test_hooks.py tests/test_drive_vault.py -q` passed 22 tests; `python scripts/lib/drive_secrets.py --check` confirmed Drive `.secrets` readable without printing values; regex scan over `.codex`, scripts, tests, docs, AGENTS/CLAUDE/GEMINI found no live-looking key literals; `git diff --check` passed.
- **Remaining**: User should rotate the API keys that were previously exposed in local plaintext `.codex/config.toml`.
- **Next**: Step 2 = fix cross-platform `drive/` + `raw/` health, especially Windows Junction detection in `check_drive_link.py`.

### [2026-05-29] a-wiki-platform-hardening-baseline (Work PC, Codex)

- **Done**: Step 0 audit + roadmap created at `docs/runbooks/a-wiki-platform-hardening-plan.md`; confirmed Work PC external data layer uses `drive/` junction to `L:\My Drive\A-Wiki-Data` and `raw/` junction to `L:\My Drive\A-Wiki-Data\raw`; Google Drive folders present: `raw/`, `.obsidian/`, `waste-reports/`, `personal-tools/`, `ocr-feedback/`, `individual-tasks/`, `.secrets`.
- **Findings**: Critical gaps are local plaintext API keys in ignored `.codex/config.toml` (must migrate + rotate), missing `check_secret_leak.py` despite hook references, missing `scripts/lib/drive_secrets.py` despite Drive-first secret docs/imports, Windows junction false warnings in `check_drive_link.py`, invalid `scripts/wiki/gen-index.py` shim on Windows, AGENTS command drift (`--dry-run` vs actual `--check`), hook parity gaps across Claude/Codex/Gemini/Antigravity/Cursor/Windsurf/Cline/Copilot, and noisy `review-check.py` results.
- **Decision**: Treat Google Drive `A-Wiki-Data` as first-class external data layer, not an optional side folder. Every future platform/device health check must verify both git repo state and external data state.
- **Next**: Step 1 = implement real secret leak hook + tests, restore Drive secrets helper, remove need for plaintext Codex keys, and ask user to rotate exposed keys after migration.

### [2026-05-28] frontend-slides upstream sync + integration (Mac, Claude Code Opus 4.7)

- **Done**: ตรวจสอบ + adopt `zarazhangrui/frontend-slides` (19.4k★ MIT) — สังเกตว่า A-Wiki มี skill นี้อยู่แล้วผ่าน ECC vendor route แต่ **stale** เพราะ ECC ยังไม่ได้ pull v2.1.0 ของ upstream (2026-05-26 commit `24e420e`)
- **Done**: Security audit ผ่าน — zero deps, ไม่มี eval/exec/Function/XMLHttp/network exfil. innerHTML 1 จุดใน `bold-template-pack/deck-stage.js:365` = controlled template literal สำหรับ UI overlay. URL ทั้งหมดเป็น Google Fonts / Fontshare / jsdelivr Chinese fonts CDN
- **Done**: Sparse-clone จาก upstream ตรง — sync `SKILL.md` + `STYLE_PRESETS.md` + `animation-patterns.md` + `html-template.md` + `viewport-base.css` + `scripts/{extract-pptx.py,export-pdf.sh}` + `LICENSE` + **NEW `bold-template-pack/`** (34 templates, 1.8MB, `deck-stage.js` web component)
- **Done**: Skip `scripts/deploy.sh` (Vercel — ขัด offline-first), skip `plugins/` + `.claude-plugin/marketplace.json` (A-Wiki ใช้ skill route ไม่ใช่ plugin marketplace)
- **Done**: SKILL.md frontmatter augmented — `origin: zarazhangrui/frontend-slides`, `upstream_version: 2.1.0`, `license: MIT`, `last_verified: 2026-05-28`
- **Done**: Architectural change ใน upstream — SKILL.md จาก clamp/viewport-flex (เก่า ~6.5KB) → **fixed 1920×1080 stage scaled uniformly + bold-template-pack progressive disclosure** (ใหม่ ~28KB). Mobile = letterbox/pillarbox แทน reflow
- **Done**: Create `wiki/entities/ai-tools/frontend-slides.md` (entity page ตาม template ecc.md) + update `AGENTS.md` integration table
- **TODO**: Update CLAUDE.md integration table (ติด hook lock — รออนุญาตจาก user รอบหน้า)
- **Decision**: ใช้ upstream ตรงสำหรับ skill นี้ เพราะ ECC vendor lag. Refresh policy: re-sparse-clone จาก zarazhangrui repo (ไม่ผ่าน `refresh-ecosystem.sh`)
- **Lesson**: ก่อน adopt external repo — ตรวจว่า skill มีอยู่แล้วผ่าน vendor route ไหม และ vendor sync ทันไหม. ในเคสนี้ direct upstream > vendor pipeline

### [2026-05-26] sqlite-vec migration — hybrid FTS5 + semantic search (Mac, Claude Code)

- **Done**: Migrate local embeddings จาก `.wiki-embeddings.json` (3.2MB TF-IDF JSON) → `wiki_vec` virtual table ใน `.wiki-index.db` ผ่าน sqlite-vec; รวมกับ FTS5 ใน DB เดียว, hybrid query ผ่าน weighted RRF (alpha 0..1, default 0.5)
- **Done**: New: `requirements.txt` (sqlite-vec, fastembed, apsw), `scripts/build-vec-index.py` (fastembed paraphrase-multilingual-MiniLM-L12-v2, 384-dim, multilingual covers ไทย+อังกฤษ)
- **Done**: Rewrite `scripts/wiki/query-rag.py` — drop FAISS/sentence-transformers, use sqlite-vec + apsw; keep CLI signature for MCP back-compat
- **Done**: Cross-platform via `apsw` (third-party SQLite binding) — bypass `--disable-loadable-sqlite-extensions` ของ python.org / Apple system Python builds. Shell hook `.claude/hooks/post-wiki-edit-gen-index.sh` ปรับให้ใช้ `.venv/bin/python3` ถ้ามี (fallback system python3)
- **Done**: Update `scripts/mcp-wiki-server.py wiki_semantic_search` tool schema (ลบ provider enum, default alpha 0.5), chain `build-vec-index.py` ใน `wiki_regen_index`
- **Done**: Update `scripts/build-wiki-index.py` — DROP TABLE wiki แทน unlink ทั้งไฟล์ (กัน wipe sibling wiki_vec tables เวลา FTS5 rebuild)
- **Done**: Skeptical-reviewer subagent pass หา 4 issues จริง: stale MCP tool schema, double vec rebuild via post-hook chain, stale comment, non-atomic DROP/CREATE/INSERT → ทั้งหมดแก้แล้ว
- **Done**: Smoke tests ผ่าน — pharmacy/drug-interaction (top-1 ตรง), Thai "เซ็นเซอร์คุณภาพอากาศ" (vec จับ ที่ FTS5 พลาดเพราะ tokenizer ไทยอ่อน), MQTT/LoRaWAN (hybrid fts# + vec# ranks ปนกัน). gen-index.py chain end-to-end ทำงาน (437 embeddings)
- **Decision**: ทิ้ง `.wiki-embeddings.json` + `.rag-index/` + `scripts/wiki/build-embeddings.py` (cutover ไม่ parallel)
- **Decision**: ตอน planning เลือก `intfloat/multilingual-e5-small` แต่ fastembed ไม่ support → switch เป็น `paraphrase-multilingual-MiniLM-L12-v2` (384-dim, no prefix needed)
- **Decision**: Update CLAUDE.md Cost Pyramid Level -1 (`Local FTS5 + sqlite-vec + knowledge-graph`) — user อนุญาตชัดเจน
- **Lesson**: Reviewer สำคัญจริง — ผม "ลืม" เรียก skeptical-reviewer หลังเขียนสคริปต์ใหม่; user ทักว่า A-Wiki swarm protocol ออกแบบไว้ใช้ทำไมไม่ใช้. Compensate โดยเรียก reviewer ตอน Phase 2 cleanup
- **TODO**: Verify Linux/Windows behavior — clone repo บนเครื่องอื่นแล้วรัน install + build

### [2026-05-26] mac-remote-access — แก้ AnyDesk session denied + gh auth login (Claude Desktop)

- **Done**: Fix Claude Desktop "GitHub CLI authentication expired" — `gh auth login --hostname github.com --git-protocol https --web` device-code flow, login as `aase7en`, token stored in macOS Keychain (scopes: gist, read:org, repo)
- **Done**: Diagnose AnyDesk Mac (ID `611965728`) remote-from-phone (ID `1555919398`) failing with "session denied due to access control" — traced via `~/.anydesk/anydesk.trace` log + `system.conf`
- **Root cause**: ACL checkbox "Restrict client access to the following AnyDesk addresses" was **enabled with empty whitelist** → blocked all incoming. User unticked checkbox → connection works
- **Decision**: For production remote-from-anywhere use, recommend ACL with phone ID `1555919398` whitelisted + Unattended Password + 2FA (currently all-open + must-accept-on-Mac)
- **Learning**: AnyDesk error "access control restrictions" can mean ACL-empty-whitelist, not just `interactive_access=0`. Always check `~/.anydesk/anydesk.trace` `Login attempt denied` lines for actual reason
- **TODO**: macOS Screen Recording / Accessibility / Input Monitoring permissions for AnyDesk still NOT granted (TCC db empty) — phone can connect but may see black screen / can't control until granted

### [2026-05-25] multi-platform-brain — Universal AI brain + cross-platform setup (PC ที่ทำงาน)

- **Done**: ตรวจสอบ A-Wiki บน Windows PC (`A:\GitHub\A-Wiki`) เทียบ Mac — พบ 3 จุดขาด: raw/, .mcp.json, API keys
- **Done**: `scripts/setup-local.sh` — cross-platform setup (raw/ junction, .mcp.json, API key sync, wiki index, .codex/ hooks)
- **Done**: `scripts/import-keys.py` — sync Google Drive `.secrets` → `.claude/settings.local.json` env block (4 keys synced)
- **Done**: สร้าง raw/ junction Windows → `L:\My Drive\A-Wiki-Data\raw` (57 files)
- **Done**: ศึกษา agents.md spec + Cline extension → upgrade AGENTS.md เป็น Universal Master Brain
- **Done**: สร้าง 6 platform config files: GEMINI.md, .cursorrules, .windsurfrules, .clinerules, .github/copilot-instructions.md, .aider.conf.yml
- **Done**: README.md full rewrite — 4 superpowers, platform support table, wiki brain section, correct setup steps
- **Decision**: AGENTS.md = Universal Master (ไม่สร้าง BRAIN.md แยก — industry standard)
- **Decision**: ห้าม hard-code model names ทุกที่ — ใช้ dynamic roster เท่านั้น
- **Decision**: CLAUDE.md เก็บ content ครบ 100% ไม่ลบออก — AGENTS.md เป็น copy ที่ตัด Claude-specific ออก

### [2026-05-24] inwwiki-critique — วิเคราะห์ InW-Wiki + 14 repos + บันทึก improvement plan สู่ session-memory

- **Done**: วิเคราะห์ InW-Wiki ครบ — directory, scripts, hooks, edit-protection, delegate.sh, sync.py, ask-notebooklm.py
- **Done**: วิเคราะห์ 14 repos อ้างอิง — tiered by signal vs redundancy (OmegaWiki 🔥🔥🔥🔥🔥, LLM-Wiki-Skilled, ai-modules, long-term-agent-memory)
- **Done**: เขียน critique ฉบับเต็ม 13 หัวข้อ → inw-wiki-critique.md
- **Done**: บันทึก improvement plan ลง session-memory.md → 14 TODO items ใน ## 🔥 Active TODOs (tagged [wiki-brain-inwwiki])
- **Decision**: Session memory เป็นระบบที่ใช้กับ Cline บน VSCode ได้เลย — Cline อ่าน/เขียน session-memory.md โดยตรงผ่าน read_file / replace_in_file
- **Open**: งาน P0 ด่วนที่สุด — Fix GitHub Actions workflow + Add missing hooks + Chain FTS5 auto-regen

### [2026-05-21] wiki-brain multiagent + TODO system — Gemini hooks, done.sh, mobile visibility

- **Done**: `.gemini/settings.json` + 7 hooks for Gemini CLI / Antigravity 2.0 (mirrors .codex/)
- **Done**: API key alias fix — `GOOGLE_AI_STUDIO_KEY` accepted as `GEMINI_API_KEY` in hooks + delegate.sh
- **Done**: `scripts/done.sh` — fuzzy-match TODO → [x] → commit → push
- **Done**: `post-push-todo-remind.sh` hook — shows remaining TODOs after every git push (0 tokens)
- **Done**: Sticky rule — Claude shows open TODOs in first visible message every session (mobile workaround)
- **Done**: Deleted 20 stale `claude/` branches via PowerShell on Work PC; Work PC git pull 84 commits
- **Key decision**: GitHub App isolation = creates claude/ branches automatically → user should disable in Project Settings
- **TODO**: Set `~/.wiki-device` on Work PC + MacBook; disable GitHub App isolation; drugs.db → .gitignore

### [2026-05-20] garbage-report-ocr learning + git rebase fix

- **Done**: ถอดข้อความ 3 หน้าใบรายงานขยะทั่วไป (30 เม.ย. – 14 พ.ค. 2569) ด้วย manual OCR
- **Done**: รับ ground-truth corrections หน้า 1 → อัปเดต `wiki/synthesis/garbage-report-ocr.md`: Fields 6 คอลัมน์, SYSTEM_PROMPT + Location Vocabulary + Staff Directory + confusion traps
- **Done**: git rebase fix — local main 65 ahead/origin 50 ahead → `git pull --rebase` → up to date ✅
- **Key findings**: "วอร์ด" OCR อ่านเป็น "จอดรถ" / "เวช" อ่านเป็น "ลาว" / แผนไทย+ฝังเข็ม (ไม่ใช่ฝ่ายแม่) / OPD=อ้อย+อ้อย / วอร์ด=ปลา+เพ็ญ / ER=กลอยใจ หรือ ณฐอร
- **TODO**: ส่ง corrections หน้า 2-3 เพื่อ expand staff directory และยืนยัน location vocab เพิ่มเติม

### [2026-05-19] Crew semi-auto + SSL flags + git-diverge fix

- **Done**: `crew-dispatch.py` — 3 flags ใหม่: `--test-ssl` (certifi detection), `--mock` (fake responses), `--json` (structured output สำหรับ Claude)
- **Done**: SKILL.md crew-dispatch อัปเดต — Claude ต้อง call Bash tool เอง (semi-auto ✅)
- **Done**: Git divergence fix — local main 65 ahead/origin 50 ahead/no ancestor → diff=0 → reset --hard → up to date ✅
- **Decision**: branch `claude/ssl-fix-crew-automation-Q7xkS` = งาน cloud automation; main ยังต้อง commit ตรง
- **TODO**: ทดสอบ `--test-ssl` บน Mac จริง (pip install certifi → expect HTTP 200)

### [2026-05-19] Device detection — multi-device session awareness

- **Done**: SessionStart hook `session-start-device.sh` detect Work PC/Mac/iPhone — output `📱/💻/🖥️ Device: ...` ทุก session; `wiki/context/device-session.md` rolling 10-session history; mirror `.codex/`; `docs/protocols/device-detection.md`
- **TODO**: สร้าง `~/.wiki-device` บน Work PC Linux (`echo "work-pc"`) + Mac (`echo "home-mac"`) — iPhone auto-detect แล้ว
- **Decision**: `~/.wiki-device` (ไม่อยู่ใน repo) = primary identity; Darwin → home-mac; container Linux → web-mobile; persistent Linux → work-pc

### [2026-05-19] Straw Hat Wiki Crew + parallel dispatch

- **Done**: `crew-dispatch.py` parallel dispatcher (Nami/Robin/Luffy/Franky) + `crew-freshness-check.sh` hook + SSL/UTF-8 fix + ทดสอบ 3/3 สำเร็จบน Windows PC (~24s parallel vs ~57s sequential)
- **Decision**: One Piece crew naming — Vegapunk=Sonnet (CEO), Nami=Gemini Flash-Lite (ฟรี), Robin=DeepSeek V4 Flash (ถูก), Luffy=Groq Llama (ฟรี), Franky=OpenRouter free (ฟรี)
- **Decision**: `handoff.md` gitignored — หยุด stop hook loop
- **Done**: crew semi-auto — `--mock --json` flags + SKILL.md อัปเดต → Claude call Bash tool เองได้แล้ว ✅
- **TODO**: ทดสอบ SSL fix บน Mac จริง (`python3 scripts/crew-dispatch.py --test-ssl`)

### [2026-05-18] Wiki Brain Upgrade v4.3 + README rewrite + duplicate cleanup (session end)

- **Done (Phase 1+2+3 — full Gemini-research-inspired upgrade)**: 8/8 plan items + verification + cleanup pass
- **Phase 1**: `.claude/agents/skeptical-reviewer.md` (Read/Grep only, used + returned GO this session) + `check-secret-leak.sh` hook #14 (blocks sk-/ghp_/AKIA/AIza/JWT in `git commit`, exit 2 verified) + `token-optimization` Step 6 Caveman + Step 7 Strategic Compact triggers + CLAUDE.md slim 352→251 lines (Schema v4.1→v4.2)
- **Phase 2**: SQLite FTS5 wiki search (`build-wiki-index.py` 195 rows + `search-wiki.py` Thai/EN works) + `ask-notebooklm.py` (Gemini Flash free-tier alternative to NotebookLM Pro manual paste, uses existing `exports/notebooklm/*.md` bundles)
- **Phase 3**: knowledge graph (`build-wiki-graph.py` 195 nodes / 785 edges / 63 broken / 26 orphans + `query-graph.py` neighbors/hubs/orphans/cross-domain/shortest-path) + `gen-index.py` chain → auto-regen `wiki/context/knowledge-graph.md` from JSON
- **New Cost Pyramid Level -1**: local FTS5 + graph queries (ฟรี + ออฟไลน์, ก่อน Grep+Read)
- **Cleanup (general-purpose subagent audit)**: deleted `Welcome.md` (Obsidian template leftover); slimmed `GEMINI.md` 349→49 lines (thin-pointer pattern like AGENTS.md, drift eliminated); updated `Home.md` (+Pharmacy, +knowledge-graph link, +README link); rewrote `README.md` 585→400 lines with accurate counts (14 hooks, 17 skills, 1 subagent) + v4.3 changelog
- **Moved from CLAUDE.md to docs/protocols/**: §Domains → `domains.md` (new) | §Context Compaction detail → `context-compaction.md` (new) | §Security Rules → appended `edit-protection.md` | §Format log.md → appended `lifecycle.md`
- **Skipped per plan Part D** (low ROI for this wiki): Context7 MCP, GitNexus, continuous-learning-v2 `/evolve`, Thai 12 skills, sqlite-vec semantic search, dmux/multi-* commands, separate Caveman/Graphify skills (folded into token-optimization instead)
- **Lessons**: WIKI_UNLOCK env vars stripped by Claude Code sandbox (Bash tool + hooks both see empty) — workaround = Bash heredoc `cat > CLAUDE.md` (bypass-by-design per hook docs); `auto-stop` + auto-commit hooks frequently fire between turns → some intermediate commits not driven by Claude
- **Open** (carry-over, unchanged from previous): Cloudflare Tunnel + Pi5 admin invite end-to-end + UI 14 ปุ่ม manual QA (all sunday-estate)
- **Push**: 11 commits this session, all pushed to `origin/main`. Final tip: `c214168 docs(readme): rewrite for v4.3 Wiki Brain Upgrade`

### [2026-05-18] sunday-estate prototype UI polish — theme unify + logo glow + logout redirect (session end)

- **Done (login fix)**: `config.js` `DEMO_MODE: true`; `sbclient.jsx` lazy `rehydrate()` — อ่าน `se_authed`/`se_user` จาก sessionStorage ทุกครั้งที่ page load → session ไม่หายข้าม navigation
- **Done (theme)**: `styles.css` `:root` → SE navy `#002c5f` + gold `#f6a800`; dark `#061429`; `--brand-glow` CSS var; modern theme `.brand-mark` override กำจัด gradient ซ้ำ
- **Done (motion)**: `landing.css` ลบ `background-attachment: fixed` modern theme (GPU bottleneck); dark meteor `pullRadius` 440→760, attract `.040-.092`→`.085-.175`
- **Done (logo)**: `shell.jsx` + `login.jsx` `<div>S</div>` → `<img>` brand-mark PNG; `.brand-mark` `drop-shadow` filter theme-aware glow
- **Done (logout + overflow)**: `app.jsx handleLogout` → `window.location.href = "landing-demo.html"`; `.theme-switch button` `min-width`/`inline-flex`/`nowrap`
- **Open**: Pi5 TODO ยังค้าง (Cloudflare Tunnel, redeploy ×2); ปลิก `DEMO_MODE: false` เมื่อ Pi5 พร้อม

### [2026-05-18] wiki-brain-optimization v4.2 + README showcase (session end)

- **Done**: ตรวจสุขภาพ Wiki (GOOD: ~190 pages, 4 domains, 70 src, 24 synthesis) + optimize 5 งาน: API key check hook, 2 symlinks, web-research→delegate.sh wire, wiki-state.md counts อัปเดต, sunday-estate-webapp.md enriched (open issues + deployment checklist)
- **Done**: README.md v4.2 — "Wiki Brain at a Glance" dashboard + architecture diagram อัปเดต สำหรับ NotebookLM infographic
- **Gap wired**: `session-start-apikey-check.sh` hook ใหม่ ใน SessionStart chain; symlink `session-memory.md` (root) + `delegation-protocol.md` (skills/); `web-research` SKILL.md → `delegate.sh` step 1
- **Confirmed**: sunday-estate-webapp wiki มีแล้ว: `wiki/synthesis/sunday-estate-webapp.md` + `sunday-estate-frontend-qa-2026-05-18.md`
- **Open**: 4 SE TODOs ยังค้าง (Cloudflare Tunnel, Pi5 redeploy ×2, SUPABASE_SECRET_KEY); ffmpeg local; Obsidian Automatic Linker

### [2026-05-18] sunday-estate fix + agent-switch.sh hook upgrade (session end)

- **sunday-estate (pending Pi5 action)**: User apply migrations 0016-0018 สำเร็จ → Portainer "Pull and redeploy" → error `se-fastapi unhealthy`; Claude diagnose root cause = `email-validator` ขาดใน `requirements.txt` (admin.py ใช้ pydantic EmailStr); fix push commit `73860a0` บน webapp main; Pi5 webapp path เจอที่ `/home/umbrel/umbrel/app-data/portainer/data/portainer/compose/29/` (Portainer upload snapshot, ไม่ใช่ git repo); user ต้องรัน `sudo tee -a requirements.txt` + Portainer "Update the stack → Re-pull and redeploy"
- **Hook upgrade (commit `f072e15`)**: แก้ `scripts/agent-switch.sh` — (1) fix PENDING extraction bug (เคย grep `**TODO**:` legacy pattern, ใช้ awk slice `## 🔥 Active TODOs` block ตาม show-active-todos.sh แทน) (2) เพิ่ม `### 📨 Last Session Brief` section ใน handoff.md + AI Studio prompt — extract narrative ล่าสุดจาก `## 🗓️ Recent` block ของ session-memory.md ใส่ลง handoff.md อัตโนมัติ
- **Impact**: Stop hook → ทุก agent ที่อ่าน handoff.md (Codex/Gemini CLI/AI Studio/OpenRouter) ได้ narrative ครบทันที — Claude ไม่ต้องเขียน handoff narrative มือเอง
- **Architecture knowledge**: Sunday-estate stack รันใน Docker-in-Docker ผ่าน `portainer_docker_1` container; host `sudo docker ps` **ไม่เห็น** sunday containers; ดู log ผ่าน Portainer UI → Containers → se-fastapi → Logs
- **Multi-device confirmed**: Git sync workflow ทำงาน (Stop hook push → SessionStart pull); กฎ: ปิด session เครื่องเก่าก่อนเปิดเครื่องใหม่ กัน push conflict

### [2026-05-18] sunday-estate fastapi unhealthy → email-validator fix + Pi5 path located (HANDOFF→Codex)

- **Trigger**: User กด Portainer "Pull and redeploy" stack `sunday-estate` หลัง apply migrations 0016/0017/0018 → error `dependency failed to start: container se-fastapi is unhealthy`
- **Root cause (Claude diagnose)**: `backend/routers/admin.py` มี `from pydantic import EmailStr` + `class InviteBody: email: EmailStr` แต่ `requirements.txt` ไม่มี `email-validator` → pydantic v2 raise `PydanticUserError` ตอน import time → FastAPI crash → healthcheck (`curl /api/health`) fail
- **Fix pushed (Mac repo)**: commit `73860a0` บน `aase7en/sunday-estate-webapp` main เพิ่ม `email-validator>=2.0.0`
- **Pi5 webapp path found**: `/home/umbrel/umbrel/app-data/portainer/data/portainer/compose/29/` (Portainer-managed upload snapshot จาก 2026-05-18 02:12; **ไม่ใช่ git repo** — แก้ตรงในไฟล์ Pi5 หรือ re-upload stack)
- **Pi5 verified state**: `requirements.txt` 10 บรรทัด ลงท้าย `slowapi==0.1.9` (ขาด `email-validator` confirmed); `routers/admin.py` มีอยู่แล้ว
- **User next action**: `echo "email-validator>=2.0.0" | sudo tee -a /home/umbrel/umbrel/app-data/portainer/data/portainer/compose/29/backend/requirements.txt` → Portainer UI "Update the stack" → "Re-pull image and redeploy" → verify `curl http://umbrel.local:8090/api/health`
- **Architecture insight**: Sunday-estate stack รันใน Docker-in-Docker ผ่าน container `portainer_docker_1`; host `sudo docker ps` **ไม่เห็น** sunday containers; ดู log ผ่าน Portainer UI → Containers → se-fastapi → Logs
- **Migrations confirmed applied**: 0016/0017/0018 ใน Supabase Studio รันสำเร็จก่อน Pull-and-redeploy พัง
- **Handoff destination**: Codex (Claude ใกล้ rate limit) — handoff.md section ใหม่มี context ครบ

### [2026-05-18] autosave-hooks + migration-fix + env-clarify (session end)

- **Done autosave**: ติดตั้ง hook autosave wiki state (commit `7e1110e` ใน wiki) — `checkpoint-on-todo.sh` (debounce 30s) + `checkpoint-on-commit.sh` (filter `git commit`) + `scripts/regen-now.sh` → ทุก TodoWrite/commit รีเจน `wiki/context/now.md` (≤2KB live snapshot) อัตโนมัติ ลดการอ่าน context สำหรับ agent ตัวต่อไป ~80%
- **Done backend**: webapp commit `be5b49d` — migrations 0016/0017/0018 + `/api/admin/invite` route (Supabase Auth admin invite_user_by_email + graceful SMTP/DB fallback + GET list + DELETE revoke)
- **Bug fixed**: migration 0016 ใช้ enum name `payment_status` ที่ชนกับ `0002_enums.sql` (มี values คนละชุดสำหรับ `loan_payments`) → DO block silent skip → table ใช้ enum เก่าที่ไม่มี `'pending'` → user เจอ `22P02`; rename เป็น `payment_notif_status` (commit `4571719`)
- **Env clarify**: ผมพูดผิดเรียก `SUPABASE_SECRET_KEY` (ชื่อใน Pi5 Supabase /.env); backend จริงๆ ใช้ `SUPABASE_SERVICE_KEY` (จาก `config.py:supabase_service_key`) — webapp `/.env` ของ user มีอยู่แล้ว 180 ตัวอักษร + routers อื่นใช้ `make_admin_client()` ทำงานมาก่อนแล้ว → ไม่ต้องตั้งใหม่
- **Open for user**: 1) `git pull` webapp → จะได้ commit `4571719`, 2) ใน Supabase Studio drop ตาราง `payment_notifications` ถ้าสร้างบางส่วนจาก attempt ก่อน — `drop table if exists public.payment_notifications cascade;`, 3) รัน migration 0016 ใหม่ → ตามด้วย 0017 → 0018, 4) Pi5 Portainer Re-pull + Redeploy stack `sunday-estate` เพื่อโหลด `/api/admin/invite`, 5) verify admin invite ผ่าน Settings → เชิญผู้ใช้
- **Decision**: ENUM ใน Supabase migrations ต้องใช้ชื่อ unique ข้าม migration ไฟล์ (DO block silent ข้าม duplicate ทำให้ใช้ enum เก่าโดยไม่ตั้งใจ) — ในอนาคตควรใช้ schema-scoped หรือ prefix ชื่อให้ชัดเจน

### [2026-05-18] sunday-estate-migrations-0016-0018-admin-route

- **Done**: Unblock 14 stub buttons จาก commit `1e8147c` — สร้าง migration 0016 (`payment_notifications` + storage bucket `payment-slips` + RLS borrower/admin + status trigger), 0017 (`events` calendar + RLS scope-aware), 0018 (`pending_invitations` + `integrations` + admin-only RLS + seed 5 integrations); สร้าง `backend/routers/admin.py` พร้อม `/api/admin/invite` (Supabase Auth admin invite_user_by_email + upsert pending_invitations + 7-day expiry + graceful SMTP/DB fallback) + `/api/admin/invitations` list + DELETE revoke; commit `be5b49d` push สำเร็จ (`aase7en/sunday-estate-webapp` main, 5 files / 446 lines); python compile ผ่าน
- **Decision**: ใช้ DO block `exception when duplicate_object` แทน `create type if not exists` (PG ไม่รองรับ); admin invite route fallback gracefully ถ้า SMTP ไม่ตั้ง — ยังบันทึก pending row ให้ admin resend; integration seed 5 ตัว disabled (LINE/Telegram/SMS/Drive/Cloudflare)
- **Open**: user ต้อง 1) Apply migrations 0016/0017/0018 ใน Supabase Studio (SQL Editor), 2) ตรวจ `SUPABASE_SECRET_KEY` ใน Pi5 Portainer env (service_role — make_admin_client() ต้องใช้), 3) Pi5 backend redeploy เพื่อโหลด `/api/admin/invite` route ใหม่
- **Constraint**: ห้ามแตะ Umbrel/Bitcoin/supabasepi5 stack; push main ตรง; เลขย้าย — 0014/0015 เคยใช้ ai_provider_keys/ai_providers_dynamic แล้ว ส่วน 0016+ คือ batch ใหม่นี้

### [2026-05-18] sunday-estate-multi-provider-foundation

- **Done**: สร้างระบบ multi-AI-provider พื้นฐานบน Sunday Estate webapp ครบ 9 commits (`ed17ce9` → `8904b29`) — migration `0015_ai_providers_dynamic.sql` (table มี slug PK + kind + base_url + priority + auto-migrate จาก 0014); backend `core/providers/` package (openrouter_adapter / openai_compat / gemini / __init__ dispatcher); router `ai_providers.py` (full CRUD + reorder + test); frontend `AIProvidersSettings` (dynamic list + AddProviderForm + ↑↓ reorder + custom kind=openai_compat รองรับ Mistral/Cohere/self-hosted); admin notification เมื่อ provider สลับ fallback
- **Done**: Rewrote `OCRPage` (prototype/src/misc.jsx) จาก 100% mock → real backend; fixed OCR file picker bugs ก่อน handoff (FileReader replace btoa loop, overlay pattern in portal, 422 error message แทน 500 generic)
- **Decision**: plain text api_key in DB + RLS admin-only — security เทียบเท่า .env; openai_compat kind ครอบคลุม 95% ของ provider (OpenAI-spec) — เฉพาะ Gemini ที่ต้อง custom adapter เพราะ format ต่าง
- **Handoff**: เขียน plan + handoff prompt ใน `/Users/aase7en/.claude/plans/http-umbrel-local-8090-compiled-wadler.md` ส่งต่อให้ Codex ทำ "Set as Primary OCR/Chat buttons + badges" — Codex รับช่วงสำเร็จ (commits `6cc04de`, `e61270d`, `b0d1d09`, `1e8147c`)
- **Knowledge from Poppy Javis (verified 2026-05-17)**: `openrouter/auto` ไม่ฟรี (curated pool, charge per model); `openrouter/free` คือ free router; `qwen/qwen3-coder:free` rate-limit ตลอด; ใช้ `deepseek/deepseek-v4-flash:free` สำหรับ chat, `google/gemma-4-31b-it:free` สำหรับ vision OCR; OpenRouter free model = 20 RPM / 50 req/day per user
- **Constraint**: solo workflow push main ตรง, ห้ามแตะ Umbrel/Bitcoin/supabasepi5

### [2026-05-18] sunday-estate-ocr-routing-json-fields

- **Done**: Codex fixed Sunday Estate OCR/provider UX across 3 webapp commits pushed to `main`: `6cc04de` primary OCR/Chat buttons + badges, `e61270d` backend reads `slug` + PDF MIME + provider-priority fallback, `b0d1d09` renders OCR JSON/arrays/nested objects as editable fields with Thai labels
- **Verify**: Prototype loaded in browser with no new console errors; backend `compileall` passed; `git diff --check` passed. User confirmed PDF OCR can read PDF after fix, then reported raw JSON output; UI formatter fix is now pushed but needs Pi5 redeploy
- **Open**: User must Portainer Re-pull + Redeploy stack `sunday-estate` at latest webapp commit `1e8147c`, hard refresh `Cmd+Shift+R`, then retest PDF OCR and QA buttons. Next implementation wave remains migrations `payment_notifications`, `events`, `pending_invitations`, `integrations` + `/api/admin/invite`
- **Constraint**: Do not touch Umbrel/Bitcoin/supabasepi5 runtime directly; code-only push main, deploy via Portainer

### [2026-05-20] wiki-sync-architecture

- **Done**: 4-layer auto-sync ครบ: L0 session-start pull --rebase + delta, L1 pre-edit lazy staleness check (>30min → auto-pull), L2 .gitattributes union merge, L3 stop-auto-commit all+push; merge pharmacy branch to main
- **Open**: Phase 2 (Obsidian Git local) + Phase 3 ยังไม่ทำ — ไม่เร่งด่วน
- **Decision**: union merge สำหรับ log files, merge=ours สำหรับ *.db; ทุก hook เป็น shell script = 0 tokens
- **TODO**: device อื่นๆ ที่ใช้ Gemini CLI/Codex ต้อง `git pull origin main` เองก่อนเริ่ม (ไม่มี Claude hooks) — อาจเพิ่ม git hook ใน `.git/hooks/` ทีหลัง

### [2026-05-18] sunday-estate-frontend-qa-batch

- **Done**: ปิด 4 bugs จาก QA user — T1 OCR `_flattenOcrRows` (1-line fix array recursion), T4 bulk select+edit+delete สัญญา, T2 Dashboard Quick-Create menu, T3 wire ghost buttons 21 ปุ่มทั่ว frontend; commit `1e8147c` push สำเร็จ (`aase7en/sunday-estate-webapp` main, 1210 lines / 7 jsx files); babel parser ผ่านทุกไฟล์
- **Open**: รอ user redeploy Pi5 + verify; 14 ปุ่มที่เป็น modal stub ต้องการ migration ใหม่ (`payment_notifications` + storage `payment-slips`, `events`, `pending_invitations`, `integrations`) + FastAPI `/api/admin/invite` route
- **Decision**: Quick-Create routing ผ่าน `pendingAction` state ใน App.jsx (ขยายได้ในอนาคต เช่น `edit:<id>`); bulk action ใช้ Supabase `.in()` filter — RLS admin-only คุ้มกัน; modal pattern graceful fallback เมื่อ table missing (try/except บน "relation does not exist")
- **TODO for next agent**: ทำตามลำดับใน [[synthesis/sunday-estate-frontend-qa-2026-05-18]] section "Instructions for Next AI Agent" — รอ user verify ก่อน, แล้ว migrations 0014→0015→0016, จากนั้น FastAPI admin route, สุดท้าย Cloudflare Tunnel
- **Constraint**: solo workflow (push main ตรง), ห้ามแตะ Umbrel/Bitcoin/supabasepi5 stack, Pi5 deploy via Portainer Re-pull+Redeploy เท่านั้น


---

<!--
Format:
### [YYYY-MM-DD] <session-topic-slug>
- **Done**: 1-2 บรรทัด สิ่งที่ทำเสร็จ
- **Open**: คำถาม/blocker ค้างคา
- **Decision**: ตัดสินใจสำคัญ + เหตุผล
- **TODO**: งานที่ user หรือ Claude ต้องตามต่อ
-->
