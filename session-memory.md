# Session Memory

> **Purpose**: เก็บประเด็นค้างคา + decisions สำคัญข้าม session — กันการลืมเรื่องเก่า
> **Auto-load**: ใช่ — CLAUDE.md §📚 Wiki Context Auto-Load อ่านทุก session
> **Size cap**: 500 tokens (~10 sessions rolling) — เก่าสุดถูกตัดเมื่อเกิน
> **Updated by**: SESSION END Protocol (Claude เขียน) + user แก้ได้ตรงๆ

---

## 🔥 Active TODOs (cross-session)

> SessionStart hook reads this block and prints **`- [ ]`** items (unchecked).
> When a task is done, change `[ ]` → `[x]`; the SESSION END Protocol prunes ticked
> items at the next rollover so the list stays slim. Cancelled work → delete the line.
> One bullet = one project; tag with `**[project-slug]**` so future-you knows the scope.

- [x] **[sunday-estate-webapp]** รัน Supabase migrations `0001…0013` ใน Studio (`http://umbrel.local:8000`)
- [x] **[sunday-estate-webapp]** กรอก `prototype/config.js` ใส่ `SUPABASE_URL` + `ANON_KEY` แล้วทดสอบ login จริง
- [x] **[sunday-estate-webapp]** เปิดเว็บ real mode แล้วสร้างบัญชีจริงบัญชีแรก (จะได้ role `admin` อัตโนมัติ)
- [x] **[sunday-estate-webapp]** `docker compose up -d --build fastapi nginx` บน Pi5 + ตั้ง `OPENROUTER_API_KEY`
- [x] **[sunday-estate-webapp]** Settings → AI & OCR Models → กด "Refresh from OpenRouter" ครั้งแรก
- [x] **[sunday-estate-webapp]** Verify production UI ที่ `http://umbrel.local:8090`: login admin → Settings AI model → test AI chat/OCR
- [ ] **[sunday-estate-webapp]** Cloudflare Tunnel: stack compose has `cloudflared` but no `se-cloudflared` container; domain `app.sundayestate.co.th` is DNS `NXDOMAIN`; still needs real Cloudflare zone/tunnel credentials + enable `public` profile
- [x] **[sunday-estate-webapp]** Manual UI verify: hard refresh + verify core runbook UI, OCR PDF editable fields, admin invitations GET route, Portainer stack/env read-only checks (passed 2026-05-18; destructive actions not clicked)
- [x] **[sunday-estate-webapp]** Migration `0016_payment_notifications.sql` + storage bucket `payment-slips` (commit `be5b49d`)
- [x] **[sunday-estate-webapp]** Migration `0017_events.sql` (Calendar NewEventModal) — commit `be5b49d`
- [x] **[sunday-estate-webapp]** Migration `0018_invitations_and_integrations.sql` — commit `be5b49d`
- [x] **[sunday-estate-webapp]** FastAPI `backend/routers/admin.py` → `/api/admin/invite` — commit `be5b49d`
- [x] **[sunday-estate-webapp]** Apply migrations 0016/0017/0018 ใน Supabase Studio (user รันเสร็จ 2026-05-18)
- [x] **[sunday-estate-webapp]** Fix `email-validator` missing in requirements.txt — commit `73860a0` (Claude พบสาเหตุ se-fastapi unhealthy หลัง Portainer Pull-and-redeploy)
- [x] **[sunday-estate-webapp]** Pi5 git pull webapp + Portainer "Pull and redeploy" stack `sunday-estate` ใหม่ (commit `73860a0`) → verify `curl http://umbrel.local:8090/api/health`
- [ ] **[sunday-estate-webapp]** Verify admin invite POST/send end-to-end with logged-in admin (GET `/api/admin/invitations` passed 200; `SUPABASE_SERVICE_KEY` env confirmed in Portainer without exposing value)
- [x] **[hyperframes]** ติดตั้ง `ffmpeg` บนเครื่อง local ก่อน render video pipeline
- [x] **[obsidian]** เปิด Obsidian → enable plugin **Automatic Linker** (v4.3.1)
- [ ] **[wiki-brain]** ทดสอบ `bash scripts/delegate.sh search "test"` บนเครื่องจริง (Mac/PC) — cloud container block outbound ทำให้ทดสอบในนี้ไม่ได้
- [ ] **[wiki-brain]** รัน `bash scripts/update-model-roster.sh` ครั้งแรกบนเครื่องจริง — scout free models จาก OpenRouter (ต้องมี OPENROUTER_API_KEY)
- [x] **[wiki-brain]** รัน `python3 scripts/gen-index.py` — rebuild FTS5 + knowledge graph หลัง wiki เพิ่มหน้าหลายรอบ
- [ ] **[wiki-brain]** เพิ่ม `GEMINI_API_KEY` ใน Project Settings (ปัจจุบันใช้ `GOOGLE_AI_STUDIO_KEY` alias — ใช้งานได้แล้ว แต่ชื่อ canonical ดีกว่า)
- [ ] **[dream]** 🏠 Sunday Estate — ปิด Cloudflare Tunnel ให้ production-ready, domain `app.sundayestate.co.th` ใช้งานได้จริง
- [ ] **[dream]** 🤖 Personal AI Agent — agent ส่วนตัวที่ใช้ wiki นี้เป็นสมอง, ตอบคำถาม+จัดการชีวิตได้ offline
- [ ] **[dream]** 📡 IoT Dashboard — dashboard กลางสำหรับ sensor/device บ้านและที่ทำงาน, real-time + alert
- [ ] **[dream]** 💊 Pharmacy App — แอพจัดการร้านยา Phu Pharmacy: stock, ค้นหายา, order history, LINE notify

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
