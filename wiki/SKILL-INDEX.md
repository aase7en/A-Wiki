# 🧠 SKILL-INDEX — A-Wiki Central Skill Brain

> **AUTO-GENERATED** by `scripts/skills_registry/generators/gen_skill_index.py`
> from `skills-registry.json`. **Do not edit by hand** (Iron Law #9).
> Run `python scripts/regen-skill-surfaces.py` to refresh.
>
> This is the central skill brain. **Every agent reads this at session
> start** (USA-1 §6) so all agents see the same canonical skill set.

**Total canonical skills**: 229 · **Aliases/deprecated**: 5

## 📊 Domain Summary

| Domain | Thai | Skills |
|--------|------|--------|
| `code` | เขียนโค้ด / ภาษาโปรแกรม | 88 |
| `debug` | ดีบัก / หาสาเหตุปัญหา | 7 |
| `design` | ดีไซน์ระบบ / สถาปัตยกรรม | 22 |
| `ux-ui` | UX/UI / Frontend / a11y | 7 |
| `engineering` | วิศวกร / Architect / Agent harness | 46 |
| `trader` | เทรด / DeFi / ตลาด | 11 |
| `medical` | การแพทย์ / ร้านยา / HIPAA | 4 |
| `business` | ธุรกิจ / การเงิน / CRM | 7 |
| `data` | Data Visualization / DB / Query | 7 |
| `security` | ความปลอดภัย / Hardening | 9 |
| `ai-ops` | AI ops / LLM / Cost | 21 |
| `productivity` | Productivity / Management | 13 |
| `wiki` | Wiki / Knowledge ops | 9 |
| `pharmacy` | ร้านยา / สต็อกยา | 2 |
| `thai` | ภาษาไทย / เอกสารไทย | 14 |
| `media` | สื่อ / วิดีโอ / รูปภาพ | 15 |
| `document` | เอกสาร / docx/pdf/pptx/xlsx | 9 |
| `sre` | SRE / Observability / Deploy | 2 |

## 🎯 Skills by Domain

### Goal #5 primary domains

### `code` — เขียนโค้ด / ภาษาโปรแกรม

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-debug` | verify | pipeline | Debug loop ครบวงจร — บังคับ failing test ก่อน fix + root cause ก่อน. รองรับ subagent fan-out สำหร... |
| `a-web` | meta | pipeline | งานเว็บ/frontend ครบ chain — ออกแบบ, สร้าง, ทดสอบ, a11y, performance |
| `a-wiki-commands` | none | uncategorized | คำสั่งหลักของ A-Wiki — /today, /lint, /ingest, /search และอื่นๆ |
| `a-wiki-telegram` | none | uncategorized | เชื่อมต่อ A-Wiki กับ Telegram bot เพื่อให้ค้นหาข้อมูล wiki, สั่ง lifecycle commands และทำ backup ... |
| `ag2-goal` | none | delegation | orchestrate multi-step goal ด้วย AG2 — planner แตกเป้า, free executor รัน, planner ตรวจ |
| `api-design` | none | ecosystem | ออกแบบ REST/GraphQL API — endpoint, schema, versioning, error format |
| `audit-reference-originality` | review | vendor-mengto | ตรวจสอบ originality ของเว็บ vs ข้อมูลอ้างอิง หา plagiarism risk พร้อม evidence + แนวแก้ |
| `autoglm-browser-agent` | none | uncategorized | ทักษะนี้ช่วยให้ AI Agent สามารถควบคุมเบราว์เซอร์เพื่อทำงานอัตโนมัติ เช่น การนำทาง การกรอกฟอร์ม แล... |
| `awiki-brain-improvement-gate` | none | wiki | ใช้ก่อนแก้ไขความสามารถของ A-Wiki brain, agent instructions, skills, hooks, plugins, scripts, sync... |
| `awiki-creator-layer` | none | wiki | เปลี่ยนบันทึก A-Wiki, หน้า wiki, สรุป source code และไฟล์เสียงส่วนตัว ให้เป็นโพสต์สาธารณะที่ปลอดภ... |
| `awiki-lifecycle-router` | meta | engineering-lifecycle | ตัวกลางที่ map 'intent ของ user' → 'skill ที่เหมาะสม' ตาม lifecycle (define→ship). โหลดอัตโนมัติต... |
| `brainstorm-before-build` | none | wiki | บังคับให้ถาม user 3 คำถาม (scope/constraint/success) ก่อนเริ่มสร้างสิ่งใหม่ ป้องกันการเขียนผิดทิศทาง |
| `browser-qa` | none | ecosystem | ใช้ทักษะนี้เพื่อทดสอบ UI อัตโนมัติและตรวจสอบการทำงานของหน้าเว็บหลัง deploy ฟีเจอร์ โดยจำลองการคลิ... |
| `browser-testing-with-devtools` | verify | engineering-lifecycle | ใช้ Chrome DevTools MCP ดึงข้อมูล runtime จริง — DOM inspection, console logs, network traces, pe... |
| `ci-cd-and-automation` | ship | engineering-lifecycle | ตั้ง CI/CD pipeline — auto test, lint, build, deploy เพื่อลดมนุษย์ผิดพลาด |
| `claude-api` | none | uncategorized | ทักษะนี้ช่วยให้คุณเรียกใช้ Claude API โดยตรงจากเทอร์มินัล รองรับการส่งข้อความและรับคำตอบจากโมเดล ... |
| `code-reviewer` | review | persona | บุคลิก Senior Staff Engineer สำหรับ review โค้ด — architecture, idioms, debt, coupling, missing t... |
| `code-simplification` | review | engineering-lifecycle | ลดความซับซ้อนของโค้ด โดยไม่เปลี่ยนพฤติกรรม — ทำให้อ่านง่ายขึ้น ลดซ้ำ ตัดส่วนที่ไม่จำเป็น |
| `content-engine` | none | ecosystem | สร้างระบบเนื้อหาที่ปรับให้เข้ากับแต่ละแพลตฟอร์ม เช่น X, LinkedIn, TikTok, YouTube และจดหมายข่าว พ... |
| `council` | none | ecosystem | เรียกประชุมสภาสี่เสียงเพื่อช่วยตัดสินใจในสถานการณ์ที่คลุมเครือ มีหลายทางเลือก หรือต้องประเมินข้อด... |
| `cpp-testing` | none | ecosystem | ใช้เมื่อเขียนหรือแก้ไข C++ tests, ตั้งค่า GoogleTest/CTest, วินิจฉัย test ที่ล้มเหลวหรือ flaky, ห... |
| `crew-dispatch` | none | wiki | แยกคำถาม A-Wiki ที่ซับซ้อนหลายมิติออกเป็น subtasks ย่อยแบบขนาน โดยให้ primary agent ตรวจสอบและควบ... |
| `cross-agent-work-orders` | plan | wiki | มาตรฐานบังคับให้ทุก agent ทำงานร่วมกันใน repo เดียว: work orders + ตาราง claim + เลนไฟล์ + pause/... |
| `crosspost` | none | ecosystem | แจกจ่ายเนื้อหาไปยังหลายแพลตฟอร์มพร้อมกัน เช่น X, LinkedIn, Threads และ Bluesky โดยปรับรูปแบบเนื้อ... |
| `csharp-testing` | none | ecosystem | ทักษะนี้ครอบคลุมการเขียนเทสต์ในภาษา C# และ .NET โดยใช้ xUnit, FluentAssertions, การจำลอง (mocking... |
| `deep-research` | none | ecosystem | ค้นหาข้อมูลเชิงลึกจากหลายแหล่งผ่าน firecrawl และ exa MCPs สังเคราะห์ผลลัพธ์และสร้างรายงานพร้อมการ... |
| `deprecation-and-migration` | ship | engineering-lifecycle | เลิกใช้/ย้ายระบบเก่าอย่างปลอดภัย — มี migration path, sunset timeline, fallback |
| `django-patterns` | none | ecosystem | design pattern Django — architecture, DRF REST API, ORM best practice, caching, signals, middleware |
| `django-verification` | none | ecosystem | ตรวจสอบความพร้อมของโปรเจกต์ Django ก่อน release หรือ PR ครอบคลุม migrations, linting, tests พร้อม... |
| `documentation-and-adrs` | ship | engineering-lifecycle | เขียน doc และ ADR (Architecture Decision Record) — บันทึกทำไมถึงตัดสินใจแบบนี้ |
| `e2e-testing` | none | ecosystem | ทักษะสำหรับการเขียนและจัดการ E2E test ด้วย Playwright ครอบคลุม Page Object Model, การตั้งค่า conf... |
| `everything-claude-code` | none | uncategorized | ทักษะนี้กำหนดรูปแบบและแนวปฏิบัติสำหรับการพัฒนาโปรเจกต์ JavaScript โดยใช้ conventional commits เพื... |
| `frontend-patterns` | none | ecosystem | รวบรวมแนวทางการพัฒนา frontend สำหรับ React, Next.js, การจัดการ state, การเพิ่มประสิทธิภาพ และ UI ... |
| `fsharp-testing` | none | ecosystem | ทักษะสำหรับการเขียนเทสต์ใน F# โดยใช้ xUnit, FsUnit, Unquote และ FsCheck สำหรับ property-based tes... |
| `game-phaser-pipeline` | build | game | Pipeline เกมสำหรับโปรเจก game ของ A-Wiki (PWQ) — Phaser + Vite + TypeScript + PixelLab ครบ: route... |
| `git-workflow-and-versioning` | ship | engineering-lifecycle | มาตรฐาน git: commit message format, branching, versioning, tagging |
| `golang-testing` | none | ecosystem | ทักษะการทดสอบ Go ที่ครอบคลุม table-driven tests, subtests, benchmarks, fuzzing และ test coverage ... |
| `hook-suggest` | none | wiki | แนะนำ hook ที่เหมาะสมสำหรับการทำงานต่าง ๆ ในโปรเจกต์ เช่น pre-commit, pre-push หรือ post-checkout... |
| `implement` | build | mattpocock | ใช้ทักษะนี้เพื่อ implement ฟีเจอร์หรือแก้ไขโค้ดตาม PRD หรือ issues ที่กำหนด โดยเน้น TDD เพื่อให้โ... |
| `internet-skill-finder` | none | uncategorized | ค้นหาและแนะนำ Agent Skills จาก GitHub repositories ที่ผ่านการตรวจสอบแล้ว ใช้เมื่อผู้ใช้ต้องการค้น... |
| `iterative-retrieval` | none | ecosystem | รูปแบบการดึงข้อมูลแบบวนซ้ำเพื่อปรับปรุงบริบทที่เกี่ยวข้องให้ดีขึ้นเรื่อย ๆ แก้ปัญหาที่ subagent ม... |
| `kotlin-testing` | none | ecosystem | ทักษะการทดสอบ Kotlin ด้วย Kotest, MockK, การทดสอบ coroutine, property-based testing และ Kover cov... |
| `laravel-patterns` | none | ecosystem | อธิบายรูปแบบสถาปัตยกรรม Laravel สำหรับแอปพลิเคชันระดับ production ครอบคลุมการจัดโครงสร้าง routing... |
| `motion-patterns` | none | ecosystem | รวมแพทเทิร์น animation สำหรับ React / Next.js ที่พร้อมใช้งานจริง ครอบคลุมปุ่มกด, modal, toast, st... |
| `nextjs-turbopack` | none | ecosystem | อธิบายการใช้งาน Next.js 16+ ร่วมกับ Turbopack ซึ่งเป็น incremental bundler ที่ช่วยเพิ่มความเร็วใน... |
| `observability-and-instrumentation` | ship | engineering-lifecycle | เพิ่ม structured logging, RED metrics, OpenTelemetry tracing และ symptom-based alerting ระหว่างกา... |
| `openai-docs` | none | uncategorized | ใช้ค้นหาหรืออ้างอิงเอกสารทางการของ OpenAI สำหรับการสร้างแอปพลิเคชันด้วย API, Codex, หรือผลิตภัณฑ์... |
| `optimize-web-animations` | review | vendor-mengto | Profile + optimize performance ของ animation — CSS, canvas/WebGL, GSAP/Three/Matter, memory leaks... |
| `parallel-execution-optimizer` | none | uncategorized | ใช้เมื่อต้องการให้งานเสร็จเร็วขึ้นด้วยการทำงานแบบ parallel, concurrent agents, batched tool calls... |
| `pdf` | none | uncategorized | ใช้เมื่อต้องการทำงานกับไฟล์ PDF เช่น อ่านหรือดึงข้อความ/ตารางจาก PDF รวมหรือรวมหลายไฟล์ PDF เข้าด... |
| `performance-optimization` | review | engineering-lifecycle | หาและแก้ bottleneck — profile ก่อน, แก้ที่จุดที่ช้าจริง ไม่ใช่เดา |
| `perl-testing` | none | ecosystem | ทักษะสำหรับการทดสอบ Perl โดยใช้ Test2::V0, Test::More, prove runner, การ mock, การวัด coverage ด้... |
| `phaser-arcade-physics` | build | game | Phaser 3 Arcade Physics reference (colliders, overlap, velocity/gravity tuning) — vendored from g... |
| `phaser-core` | build | game | Phaser 3 core engine reference (scenes, game config, loader, sprites) — vendored from gamedev-ski... |
| `pixijs-rendering` | build | game | PixiJS rendering reference (containers, sprites, filters, render pipeline) — vendored from gamede... |
| `planning-and-task-breakdown` | plan | engineering-lifecycle | แยกงานใหญ่ให้เป็น task เล็กๆ ที่ทำได้ทีละชิ้น พร้อม dependency และลำดับ |
| `platform-ingest` | meta | pipeline | Platform ingestion layer — อ่านโพสต์จาก Reddit/YouTube/Bilibili/URL ทั่วไป โดยใช้ endpoint ที่ ve... |
| `plugin-creator` | none | uncategorized | สร้างและจัดโครงสร้าง plugin สำหรับ Codex โดยสร้างโฟลเดอร์ .codex-plugin/ พร้อมไฟล์ plugin.json ที... |
| `project-flow-ops` | none | ecosystem | จัดการการทำงานระหว่าง GitHub และ Linear โดยการจัดลำดับความสำคัญของ issues และ pull requests, เชื่... |
| `project-guidelines-example` | none | uncategorized | ทักษะนี้ให้ตัวอย่างแนวทางปฏิบัติสำหรับโปรเจกต์ เช่น การตั้งชื่อไฟล์ โครงสร้างโฟลเดอร์ และรูปแบบกา... |
| `prototype` | build | mattpocock | สร้าง prototype แบบเร็วเพื่อตอบคำถามด้านการออกแบบหรือทดสอบแนวคิด โดยไม่ต้องกังวลเรื่องคุณภาพโค้ดห... |
| `python-testing` | none | ecosystem | ทักษะนี้ครอบคลุมกลยุทธ์การทดสอบ Python ด้วย pytest รวมถึง TDD, fixtures, mocking, parametrization... |
| `react-patterns` | none | uncategorized | รวบรวมแพทเทิร์น React 18/19 ที่จำเป็น เช่น การใช้ hooks อย่างมีวินัย, การแบ่งขอบเขต Server/Client... |
| `react-performance` | none | uncategorized | optimize React/Next.js — memo, code-splitting, lazy loading, render budget ตามแนวทาง Vercel engin... |
| `react-testing` | none | uncategorized | test React component ด้วย React Testing Library + Vitest/Jest + MSW mock network + accessibility ... |
| `recursive-decision-ledger` | none | uncategorized | ใช้เมื่อต้องการติดตามการตัดสินใจแบบวนซ้ำในกระบวนการค้นหาหรือปรับแต่งหลายขั้นตอน เช่น การสุ่มสำรวจ... |
| `resolving-merge-conflicts` | none | mattpocock | ช่วยแก้ไข conflict ที่เกิดขึ้นระหว่างการ merge หรือ rebase โดยวิเคราะห์ความตั้งใจของแต่ละ hunk แท... |
| `rust-testing` | none | ecosystem | กลยุทธ์ test Rust — unit, integration, async test, property-based test, doctest |
| `scrape-web` | none | uncategorized | ส่ง URL ไปยัง scraper ที่เหมาะสมที่สุด โดยไล่ระดับจาก curl → Scrapling → Crawl4AI → Firecrawl → B... |
| `search-first` | none | ecosystem | ค้นหาเครื่องมือ ไลบรารี และแพทเทิร์นที่มีอยู่ก่อนเริ่มเขียนโค้ดใหม่ เพื่อลดงานซ้ำซ้อนและใช้ทรัพยา... |
| `security-and-hardening` | review | engineering-lifecycle | ตรวจช่องโหว่ความปลอดภัย: injection, auth, secret leak, input validation |
| `shipping-and-launch` | ship | engineering-lifecycle | เช็คลิสต์ก่อน release: test, docs, migration, rollback plan, monitoring — ให้มั่นใจว่า launch ปลอ... |
| `skill-creator` | none | uncategorized | สร้างทักษะใหม่ ปรับปรุงทักษะที่มีอยู่ และวัดประสิทธิภาพของทักษะ ช่วยให้คุณออกแบบและปรับแต่งทักษะต... |
| `skill-installer` | none | uncategorized | ติดตั้งสกิล Codex จากรายการที่คัดสรรหรือจาก GitHub repo ลงใน $CODEX_HOME/skills ใช้เมื่อผู้ใช้ต้อ... |
| `skill-scout` | none | ecosystem | ค้นหาสกิลที่มีอยู่แล้วจากแหล่งต่างๆ ทั้งในเครื่อง, marketplace, GitHub และเว็บ ก่อนที่จะสร้างสกิล... |
| `social-publisher` | none | uncategorized | ช่วยกำหนดเวลาและเผยแพร่โพสต์โซเชียลมีเดียไปยัง 13 แพลตฟอร์มผ่าน SocialClaw เช่น X, LinkedIn, Inst... |
| `spec-driven-development` | define | engineering-lifecycle | เขียนสเปก/requirements ให้ชัดก่อนเริ่มเขียนโค้ด เพื่อให้ทุกคน (และ AI) เข้าใจตรงกันว่าต้องทำอะไร ... |
| `tdd` | build | mattpocock | เขียน test ก่อนโค้ด (Red-Green-Refactor) เพื่อให้แน่ใจว่าโค้ดทำงานถูกและกัน regression |
| `test-engineer` | verify | persona | บุคลิก QA Specialist — edge cases, integration gaps, failure modes, test coverage |
| `threejs-gltf-loading` | build | game | three.js glTF model loading reference — vendored from gamedev-skills/awesome-gamedev-agent-skills. |
| `threejs-materials-lighting` | build | game | three.js materials + lighting reference — vendored from gamedev-skills/awesome-gamedev-agent-skills. |
| `threejs-scene-setup` | build | game | three.js scene/camera/renderer setup reference — vendored from gamedev-skills/awesome-gamedev-age... |
| `two-axis-code-review` | review | mattpocock | รีวิวโค้ดแบบ 2 แกน: (1) correctness/logic (2) style/maintainability |
| `vite-patterns` | none | ecosystem | รวบรวมแพทเทิร์นการใช้งาน Vite ตั้งแต่การตั้งค่า config, plugin, HMR, env variables, proxy, SSR, l... |
| `web-artifacts-builder` | none | uncategorized | สร้าง HTML artifact หลาย component บน claude.ai ด้วย modern frontend — ดีไซน์สวย, โต้ตอบได้ |
| `web-research` | none | wiki | ค้นหาข้อมูลจากเว็บโดยอัตโนมัติ เช่น ตรวจสอบราคา ดาต้าชีท หาตัวเลือก หรือยืนยันข้อเท็จจริง รองรับห... |
| `webapp-testing` | none | uncategorized | ชุดเครื่องมือสำหรับทดสอบและโต้ตอบกับเว็บแอปพลิเคชันที่รันในเครื่อง โดยใช้ Playwright เพื่อตรวจสอบ... |
| `windows-desktop-e2e` | none | ecosystem | สกิลสำหรับเขียน E2E test สำหรับแอปพลิเคชัน Windows desktop (WPF, WinForms, Win32/MFC, Qt) โดยใช้ ... |

### `debug` — ดีบัก / หาสาเหตุปัญหา

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-debug` | verify | pipeline | Debug loop ครบวงจร — บังคับ failing test ก่อน fix + root cause ก่อน. รองรับ subagent fan-out สำหร... |
| `agent-introspection-debugging` | none | ecosystem | debug agent failure แบบมีโครง — capture, diagnosis, contained recovery, prevention — ไม่ใช่แค่ลอง... |
| `browser-qa` | none | ecosystem | ใช้ทักษะนี้เพื่อทดสอบ UI อัตโนมัติและตรวจสอบการทำงานของหน้าเว็บหลัง deploy ฟีเจอร์ โดยจำลองการคลิ... |
| `debug-mantra` | none | uncategorized | [Iron Law #2] debug-mantra 4 ขั้น — reproduce → hypothesize → test-fix → verify — ไม่ใช่ try-and-see |
| `scrutinize` | none | uncategorized | รีวิวแบบเข้ม — ตั้งคำถามทุก assumption, หา edge case, เช็ค security/perf. ใช้คู่กับ code-review |
| `triage` | verify | mattpocock | ขับ issue/PR ผ่าน state machine ของการตัดสินใจ — categorise, verify, grill, write-up, merge |
| `verify-before-done` | none | wiki | บังคับตรวจสอบก่อนบอกว่า 'เสร็จแล้ว' — รัน test, ตรวจ output, ยืนยันจริงไม่ใช่แค่คิดว่าเสร็จ |

### `design` — ดีไซน์ระบบ / สถาปัตยกรรม

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-plan` | define | pipeline | ออกแบบ UX/UI, database, architecture — บังคับถาม grill-with-docs ≥3 questions ก่อนเริ่ม implement |
| `add-shader-cursor-trail` | build | vendor-mengto | เอฟเฟกต์ cursor trail บน WebGPU — halftone twinkling, chromatic ripples, film grain พร้อม fallbacks |
| `audit-reference-originality` | review | vendor-mengto | ตรวจสอบ originality ของเว็บ vs ข้อมูลอ้างอิง หา plagiarism risk พร้อม evidence + แนวแก้ |
| `brand-guidelines` | none | uncategorized | ใช้สีและฟอนต์ของแบรนด์ Anthropic กับ artifact ใดๆ เพื่อให้มีลุคและฟีลแบบทางการของ Anthropic |
| `brand-voice` | none | ecosystem | สร้างโปรไฟล์สไตล์การเขียนจากเนื้อหาจริง เช่น โพสต์ บทความ เอกสาร หรือเว็บไซต์ จากนั้นนำโปรไฟล์นั้... |
| `canvas-design` | none | uncategorized | สร้างงานศิลปะภาพและเอกสาร .png และ .pdf ที่สวยงาม โดยใช้หลักการออกแบบและปรัชญาศิลปะ เหมาะสำหรับทำ... |
| `cinematic-gsap-lenis-motion-system` | build | vendor-mengto | Motion system ระดับพรีเมียมด้วย GSAP + ScrollTrigger + Lenis — luxury editorial, Awwwards, scroll... |
| `codebase-design` | build | mattpocock | ชุดคำศัพท์และแนวคิดสำหรับออกแบบโมดูลที่ลึก (deep modules) โดยเน้นการหาโอกาสในการขยาย (deepening o... |
| `design-first-ui-prompting` | define | vendor-mengto | เทมเพลต prompt แบบ design-first: goal -> format -> layout -> type -> color -> constraints + varia... |
| `design-system` | none | ecosystem | ใช้สร้างหรือตรวจสอบ design system ตรวจสอบความสม่ำเสมอทางภาพ และรีวิว PR ที่เกี่ยวข้องกับสไตล์ |
| `domain-modeling` | define | mattpocock | ออกแบบและปรับปรุง domain model ของโปรเจกต์ — กำหนดคำศัพท์เฉพาะ, สร้าง ubiquitous language, และบัน... |
| `frontend-design` | none | uncategorized | ออกแบบ UI/UX หน้าเว็บ — layout, color, typography, component |
| `gsap` | build | vendor-mengto | GSAP animations — timelines, ScrollTrigger, stagger, transforms สำหรับ HTML/CSS/JS/React เติมช่อง... |
| `gsap-scrolltrigger-storytelling` | build | vendor-mengto | Storytelling แบบ sticky scroll ด้วย GSAP ScrollTrigger — progressive reveals, scroll-synced anima... |
| `optimize-web-animations` | review | vendor-mengto | Profile + optimize performance ของ animation — CSS, canvas/WebGL, GSAP/Three/Matter, memory leaks... |
| `shaders-cursor-ripples` | build | vendor-mengto | เอฟเฟกต์น้ำเกร่อน (water ripple) ตามเมาส์บนรูปด้วย WebGPU + Shaders library |
| `taste-skill` | build | design | Anti-slop frontend taste layer (Leonxlnx/taste-skill, MIT, 59.4k star) — infers design intent for... |
| `theme-factory` | none | uncategorized | ชุดเครื่องมือสำหรับปรับแต่งสไตล์ของ artifacts เช่น สไลด์ เอกสาร รายงาน หรือหน้า HTML Landing Page... |
| `threejs` | build | vendor-mengto | Three.js สำหรับเว็บ — scene/camera/renderer, lights, GLTF, controls, performance (เน้น designer p... |
| `transitions-dev` | build | design | 18 production-ready CSS transitions + reveal/review/apply audit workflow (Jakubantalik/transition... |
| `ui-ux-pro-max` | build | design | Searchable local design-intelligence database (nextlevelbuilder/ui-ux-pro-max-skill, MIT) — 161 p... |
| `webgl-3d-object` | build | vendor-mengto | วัตถุ 3D บนเว็บด้วย WebGL — mesh depth, PBR material, แสงจริง, perspective camera, subtle rotatio... |

### `ux-ui` — UX/UI / Frontend / a11y

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-plan` | define | pipeline | ออกแบบ UX/UI, database, architecture — บังคับถาม grill-with-docs ≥3 questions ก่อนเริ่ม implement |
| `a-web` | meta | pipeline | งานเว็บ/frontend ครบ chain — ออกแบบ, สร้าง, ทดสอบ, a11y, performance |
| `accessibility` | none | ecosystem | ออกแบบ พัฒนา และตรวจสอบความสามารถในการเข้าถึงของผลิตภัณฑ์ดิจิทัลให้สอดคล้องกับมาตรฐาน WCAG 2.2 ระ... |
| `frontend-a11y` | none | uncategorized | ทักษะนี้ช่วยตรวจสอบและปรับปรุงการเข้าถึง (accessibility) ของส่วนติดต่อผู้ใช้ (UI) โดยวิเคราะห์โคร... |
| `taste-skill` | build | design | Anti-slop frontend taste layer (Leonxlnx/taste-skill, MIT, 59.4k star) — infers design intent for... |
| `transitions-dev` | build | design | 18 production-ready CSS transitions + reveal/review/apply audit workflow (Jakubantalik/transition... |
| `ui-ux-pro-max` | build | design | Searchable local design-intelligence database (nextlevelbuilder/ui-ux-pro-max-skill, MIT) — 161 p... |

### `engineering` — วิศวกร / Architect / Agent harness

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-claim` | meta | pipeline | ระบบจองงานข้าม agent — ประกาศ scope+goal+phase ก่อนเริ่ม, เห็นว่า agent อื่นทำอะไรอยู่, hook bloc... |
| `a-council` | review | pipeline | Persistent multi-persona council: code-reviewer/test-engineer/security-auditor post findings to a... |
| `a-escalate` | meta | pipeline | แพ็คปัญหาที่ติดเป็น prompt พร้อมบริบทครบ ส่งให้โมเดลเก่งกว่าคิดต่อ — ผู้ใช้ก๊อปไปวางเอง ไม่มีการส... |
| `a-loop` | meta | pipeline | Autonomous goal loop: decompose → execute → verify → distill → improve. A- suite aggregator that ... |
| `a-plan` | define | pipeline | ออกแบบ UX/UI, database, architecture — บังคับถาม grill-with-docs ≥3 questions ก่อนเริ่ม implement |
| `a-research` | meta | pipeline | งานค้นคว้าและวิเคราะห์ — รวมวิจัย วิเคราะห์ และตรวจสอบแหล่งข้อมูลไว้ที่เดียว |
| `a-router` | meta | pipeline | ตัวจ่ายงานของ A-Suite — รับ request แล้วบอกว่าควรใช้ skill ไหน phase ไหน ผ่าน trigger table ที่ g... |
| `a-think` | meta | pipeline | Loop คิดวิเคราะห์ 7 ขั้น — รันก่อนตอบ non-trivial request. รวม fable-method + fable5-standards. F... |
| `a-web` | meta | pipeline | งานเว็บ/frontend ครบ chain — ออกแบบ, สร้าง, ทดสอบ, a11y, performance |
| `architecture-decision-records` | none | uncategorized | บันทึกการตัดสินใจทางสถาปัตยกรรมที่เกิดขึ้นระหว่าง Claude Code sessions ในรูปแบบ ADR ที่มีโครงสร้า... |
| `ask-matt` | none | mattpocock | ใช้ถามว่าควรใช้ skill หรือ flow ไหนสำหรับสถานการณ์ของคุณ โดยทำหน้าที่เป็น router วนดู skills ทั้ง... |
| `awiki-lifecycle-router` | meta | engineering-lifecycle | ตัวกลางที่ map 'intent ของ user' → 'skill ที่เหมาะสม' ตาม lifecycle (define→ship). โหลดอัตโนมัติต... |
| `browser-testing-with-devtools` | verify | engineering-lifecycle | ใช้ Chrome DevTools MCP ดึงข้อมูล runtime จริง — DOM inspection, console logs, network traces, pe... |
| `ci-cd-and-automation` | ship | engineering-lifecycle | ตั้ง CI/CD pipeline — auto test, lint, build, deploy เพื่อลดมนุษย์ผิดพลาด |
| `code-simplification` | review | engineering-lifecycle | ลดความซับซ้อนของโค้ด โดยไม่เปลี่ยนพฤติกรรม — ทำให้อ่านง่ายขึ้น ลดซ้ำ ตัดส่วนที่ไม่จำเป็น |
| `codebase-design` | build | mattpocock | ชุดคำศัพท์และแนวคิดสำหรับออกแบบโมดูลที่ลึก (deep modules) โดยเน้นการหาโอกาสในการขยาย (deepening o... |
| `deprecation-and-migration` | ship | engineering-lifecycle | เลิกใช้/ย้ายระบบเก่าอย่างปลอดภัย — มี migration path, sunset timeline, fallback |
| `documentation-and-adrs` | ship | engineering-lifecycle | เขียน doc และ ADR (Architecture Decision Record) — บันทึกทำไมถึงตัดสินใจแบบนี้ |
| `domain-modeling` | define | mattpocock | ออกแบบและปรับปรุง domain model ของโปรเจกต์ — กำหนดคำศัพท์เฉพาะ, สร้าง ubiquitous language, และบัน... |
| `git-guardrails-claude-code` | none | mattpocock | ตั้งค่า hook ใน Claude Code เพื่อบล็อกคำสั่ง git ที่อันตราย เช่น push, reset --hard, clean, branc... |
| `git-workflow-and-versioning` | ship | engineering-lifecycle | มาตรฐาน git: commit message format, branching, versioning, tagging |
| `grill-with-docs` | define | mattpocock | เหมือน grilling แต่ผลพลอยได้คือเอกสาร — ADR + glossary เกิดตามมาจากการสอบสวน |
| `implement` | build | mattpocock | ใช้ทักษะนี้เพื่อ implement ฟีเจอร์หรือแก้ไขโค้ดตาม PRD หรือ issues ที่กำหนด โดยเน้น TDD เพื่อให้โ... |
| `improve-codebase-architecture` | review | mattpocock | สแกนโค้ดเบสเพื่อหาโอกาสในการปรับปรุงสถาปัตยกรรม สร้างรายงาน HTML แบบภาพ จากนั้นเจาะลึกประเด็นที่เ... |
| `latency-critical-systems` | none | uncategorized | ใช้สำหรับระบบที่ไวต่อ latency เช่น realtime dashboard, market data, streaming agent, execution ga... |
| `migrate-to-shoehorn` | none | mattpocock | แปลงไฟล์ทดสอบ TypeScript ที่ใช้ type assertion แบบ `as` ให้ใช้ `@total-typescript/shoehorn` แทน เ... |
| `observability-and-instrumentation` | ship | engineering-lifecycle | เพิ่ม structured logging, RED metrics, OpenTelemetry tracing และ symptom-based alerting ระหว่างกา... |
| `performance-optimization` | review | engineering-lifecycle | หาและแก้ bottleneck — profile ก่อน, แก้ที่จุดที่ช้าจริง ไม่ใช่เดา |
| `planning-and-task-breakdown` | plan | engineering-lifecycle | แยกงานใหญ่ให้เป็น task เล็กๆ ที่ทำได้ทีละชิ้น พร้อม dependency และลำดับ |
| `platform-ingest` | meta | pipeline | Platform ingestion layer — อ่านโพสต์จาก Reddit/YouTube/Bilibili/URL ทั่วไป โดยใช้ endpoint ที่ ve... |
| `prototype` | build | mattpocock | สร้าง prototype แบบเร็วเพื่อตอบคำถามด้านการออกแบบหรือทดสอบแนวคิด โดยไม่ต้องกังวลเรื่องคุณภาพโค้ดห... |
| `research` | define | mattpocock | สืบค้นคำถามกับแหล่งขั้นต้นที่เชื่อถือได้ แล้วบันทึกผลเป็น markdown — cite, synthesize ไม่เอาจาก m... |
| `resolving-merge-conflicts` | none | mattpocock | ช่วยแก้ไข conflict ที่เกิดขึ้นระหว่างการ merge หรือ rebase โดยวิเคราะห์ความตั้งใจของแต่ละ hunk แท... |
| `scaffold-exercises` | build | mattpocock | สร้างโครงสร้างไดเรกทอรีสำหรับแบบฝึกหัดที่มีส่วนของหัวข้อ โจทย์ เฉลย และคำอธิบาย ซึ่งผ่านการตรวจสอ... |
| `security-and-hardening` | review | engineering-lifecycle | ตรวจช่องโหว่ความปลอดภัย: injection, auth, secret leak, input validation |
| `setup-matt-pocock-skills` | none | mattpocock | ตั้งค่า repository สำหรับทักษะทางวิศวกรรมของ Matt Pocock รวมถึง issue tracker, labels สำหรับ tria... |
| `setup-pre-commit` | none | mattpocock | ติดตั้ง Husky pre-commit hooks กับ lint-staged (prettier), type check, test — กัน commit โค้ดเสีย |
| `shipping-and-launch` | ship | engineering-lifecycle | เช็คลิสต์ก่อน release: test, docs, migration, rollback plan, monitoring — ให้มั่นใจว่า launch ปลอ... |
| `spec-driven-development` | define | engineering-lifecycle | เขียนสเปก/requirements ให้ชัดก่อนเริ่มเขียนโค้ด เพื่อให้ทุกคน (และ AI) เข้าใจตรงกันว่าต้องทำอะไร ... |
| `symlink-connector` | ship | extensibility | linker สากล — symlink skills ของ harness ทุกตัวไปยัง A-Wiki repo, .env ไป secrets/global.env บน G... |
| `tdd` | build | mattpocock | เขียน test ก่อนโค้ด (Red-Green-Refactor) เพื่อให้แน่ใจว่าโค้ดทำงานถูกและกัน regression |
| `to-issues` | plan | mattpocock | แตก plan/spec/PRD เป็น issue แบบ tracer-bullet slice — แต่ละ issue ทำได้ทีละอันอิสระ |
| `to-prd` | define | mattpocock | สังเคราะห์บทสนทนาปัจจุบันให้เป็น PRD (Product Requirements Document) และเผยแพร่ออกมา โดยไม่ต้องสั... |
| `triage` | verify | mattpocock | ขับ issue/PR ผ่าน state machine ของการตัดสินใจ — categorise, verify, grill, write-up, merge |
| `two-axis-code-review` | review | mattpocock | รีวิวโค้ดแบบ 2 แกน: (1) correctness/logic (2) style/maintainability |
| `web-performance-auditor` | review | persona | บุคลิก Web Performance Engineer — Core Web Vitals, bundle size, jank, animation cost |

### `trader` — เทรด / DeFi / ตลาด

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-invest` | meta | pipeline | งานวิเคราะห์การลงทุน — พอร์ต, ความเสี่ยง, quant simulation, market intelligence |
| `defi-amm-security` | none | ecosystem | รายการตรวจสอบความปลอดภัยสำหรับสัญญา AMM บน Solidity ครอบคลุมการป้องกัน reentrancy, การเรียงลำดับ ... |
| `finance-pipeline` | meta | pipeline | ไปป์ไลน์วิเคราะห์การลงทุนแบบครบวงจร — ดึงข้อมูล -> วิเคราะห์ (เทคนิค+พื้นฐาน+ความรู้สึกตลาด) -> โ... |
| `ito-basket-compare` | none | uncategorized | เปรียบเทียบตะกร้า Itô prediction-market กับฐานความรู้ บันทึกพอร์ต บริบทการเงิน รายการเฝ้าดู หรือว... |
| `ito-data-atlas-agent` | none | uncategorized | ออกแบบ Data Atlas agent สำหรับการวิจัยตะกร้า Itô, การค้นพบตลาด, การร่างพารามิเตอร์, และการแก้ไขแบ... |
| `ito-market-intelligence` | none | uncategorized | ใช้สำหรับค้นหาข้อมูลเกี่ยวกับ prediction market เช่น อีเวนต์ เวนิว underlier สภาพคล่อง และข่าวสาร... |
| `ito-trade-planner` | none | uncategorized | สร้างเวิร์กชีตวางแผนการซื้อขายสำหรับตลาดทำนายแบบ Itô หรือ venue workflows โดยไม่ให้คำแนะนำทางการเ... |
| `llm-trading-agent-security` | none | ecosystem | รูปแบบความปลอดภัยสำหรับเอเจนต์เทรดดิ้งอัตโนมัติที่มีสิทธิ์เข้าถึงกระเป๋าเงินหรือทำธุรกรรม ครอบคลุ... |
| `monte-carlo-quant-analysis` | none | awiki | Monte Carlo simulation + synthetic data + quant risk (VaR/CVaR/Sharpe/drawdown/RRR) สำหรับ portfo... |
| `prediction-market-oracle-research` | none | uncategorized | ค้นคว้าข้อมูลจาก prediction market เพื่อใช้เป็น oracle signal หรือ data source สำหรับผลิตภัณฑ์, A... |
| `prediction-market-risk-review` | none | uncategorized | ตรวจสอบเวิร์กโฟลว์ของ prediction market, basket, oracle และ trading agent ด้าน compliance, ความปล... |

### `medical` — การแพทย์ / ร้านยา / HIPAA

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `healthcare-phi-compliance` | none | ecosystem | รูปแบบการปฏิบัติตามข้อกำหนดด้านข้อมูลสุขภาพที่ได้รับการคุ้มครอง (PHI) และข้อมูลส่วนบุคคลที่สามารถ... |
| `medical-pipeline` | meta | pipeline | ไปป์ไลน์คำถามคลินิกแบบ evidence-based — สืบค้นหลักฐาน -> วินิจฉัยแยกโรค/แนวทางรักษา -> ตรวจสอบควา... |
| `openmed` | none | uncategorized | ใช้ OpenMed สำหรับการสกัดข้อมูลทางการแพทย์ (medical entity extraction), การตรวจจับข้อมูลส่วนบุคคล... |
| `pharmacy-order-lookup` | none | wiki | ค้นหาข้อมูลใบสั่งยาจากร้านขายยา โดยใช้หมายเลขใบสั่งยา (Order ID) หรือชื่อผู้ป่วย เพื่อดึงรายละเอี... |

### `business` — ธุรกิจ / การเงิน / CRM

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-content` | meta | pipeline | งานเขียนคอนเทนต์และการตลาด — บทความ, brand voice, SEO, campaign, โพสต์โซเชียล |
| `a-invest` | meta | pipeline | งานวิเคราะห์การลงทุน — พอร์ต, ความเสี่ยง, quant simulation, market intelligence |
| `a-med-order` | build | pipeline | สั่งซื้อยาครบวง: ตรวจคำผิดชื่อยา (จำคำพ้องที่ยืนยันแล้วอัตโนมัติ) → ใบสั่งซื้อ Excel/Sheet → กรอก... |
| `internal-comms` | none | uncategorized | เขียนสื่อสารภายในองค์กร — memo, announcement, changelog |
| `market-research` | none | ecosystem | ค้นคว้าข้อมูลตลาด วิเคราะห์คู่แข่ง ตรวจสอบสถานะนักลงทุน และรวบรวมข่าวสารอุตสาหกรรม พร้อมระบุแหล่ง... |
| `marketing-campaign` | none | uncategorized | วางแผนและดำเนินการแคมเปญการตลาดแบบครบวงจร ตั้งแต่การวิจัยกลุ่มเป้าหมาย การกำหนดตำแหน่งทางการตลาด ... |
| `seo` | none | ecosystem | วิเคราะห์และปรับปรุง SEO ทั้งด้านเทคนิค การปรับแต่งหน้าเว็บ ข้อมูลโครงสร้าง (Structured Data) Cor... |

### `data` — Data Visualization / DB / Query

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-research` | meta | pipeline | งานค้นคว้าและวิเคราะห์ — รวมวิจัย วิเคราะห์ และตรวจสอบแหล่งข้อมูลไว้ที่เดียว |
| `data-throughput-accelerator` | none | uncategorized | ใช้เมื่อต้องการเร่งความเร็วการนำเข้าข้อมูลขนาดใหญ่ การ backfill การส่งออก ETL การโหลดคลังข้อมูล ก... |
| `finance-pipeline` | meta | pipeline | ไปป์ไลน์วิเคราะห์การลงทุนแบบครบวงจร — ดึงข้อมูล -> วิเคราะห์ (เทคนิค+พื้นฐาน+ความรู้สึกตลาด) -> โ... |
| `literature-review` | none | ecosystem | ทักษะนี้ช่วยวางแผนการค้นหา คัดกรองแหล่งข้อมูล สังเคราะห์ และจัดการอ้างอิงสำหรับงานทบทวนวรรณกรรมอย... |
| `monte-carlo-quant-analysis` | none | awiki | Monte Carlo simulation + synthetic data + quant risk (VaR/CVaR/Sharpe/drawdown/RRR) สำหรับ portfo... |
| `research-pipeline` | meta | pipeline | ไปป์ไลน์วิจัยแบบ 3 stage สำหรับทุก domain — รวบรวม -> สังเคราะห์ -> วิพากษ์วิจารณ์. ใช้ subagent ... |
| `scholar-evaluation` | none | ecosystem | ประเมินผลงานวิชาการอย่างมีโครงสร้าง ไม่ว่าจะเป็นบทความ ข้อเสนอการวิจัย การทบทวนวรรณกรรม ส่วนวิธีก... |

### A-Wiki extension domains

### `security` — ความปลอดภัย / Hardening

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `defi-amm-security` | none | ecosystem | รายการตรวจสอบความปลอดภัยสำหรับสัญญา AMM บน Solidity ครอบคลุมการป้องกัน reentrancy, การเรียงลำดับ ... |
| `gateguard` | none | ecosystem | เกทที่บังคับให้ผู้ใช้ตรวจสอบข้อเท็จจริงก่อนดำเนินการแก้ไข เขียน หรือรัน Bash โดยจะบล็อกคำสั่ง Edi... |
| `git-guardrails-claude-code` | none | mattpocock | ตั้งค่า hook ใน Claude Code เพื่อบล็อกคำสั่ง git ที่อันตราย เช่น push, reset --hard, clean, branc... |
| `llm-trading-agent-security` | none | ecosystem | รูปแบบความปลอดภัยสำหรับเอเจนต์เทรดดิ้งอัตโนมัติที่มีสิทธิ์เข้าถึงกระเป๋าเงินหรือทำธุรกรรม ครอบคลุ... |
| `safety-guard` | none | ecosystem | ตรวจสอบความปลอดภัยก่อนทำการที่เสียหายได้ยาก — delete, force push, ส่งข้อมูลออก, เปลี่ยน production |
| `security-and-hardening` | review | engineering-lifecycle | ตรวจช่องโหว่ความปลอดภัย: injection, auth, secret leak, input validation |
| `security-auditor` | review | persona | บุคลิก Security Engineer — auth, secrets, injection, OWASP, threat model |
| `security-review` | none | uncategorized | ใช้เมื่อเพิ่มระบบ authentication, จัดการ user input, ทำงานกับ secrets, สร้าง API endpoints หรือ i... |
| `security-scan` | none | ecosystem | สแกนการตั้งค่า Claude Code ในโฟลเดอร์ .claude/ เพื่อหาช่องโหว่ด้านความปลอดภัย การตั้งค่าที่ผิดพลา... |

### `ai-ops` — AI ops / LLM / Cost

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-claim` | meta | pipeline | ระบบจองงานข้าม agent — ประกาศ scope+goal+phase ก่อนเริ่ม, เห็นว่า agent อื่นทำอะไรอยู่, hook bloc... |
| `agent-eval` | none | ecosystem | ประเมินคุณภาพของ agent/prompt — วัด accuracy, cost, latency และหาจุดปรับปรุง |
| `agent-introspection-debugging` | none | ecosystem | debug agent failure แบบมีโครง — capture, diagnosis, contained recovery, prevention — ไม่ใช่แค่ลอง... |
| `agent-sort` | none | ecosystem | เรียง skills/commands/rules/hooks สำหรับ repo หนึ่งๆ เป็น install plan โดยอ้างหลักฐาน — ไม่เดา |
| `benchmark-optimization-loop` | none | uncategorized | ใช้เมื่อต้องการปรับปรุงประสิทธิภาพของโค้ดหรือระบบ โดยลองหลายรูปแบบ วัด latency/throughput/cost แล... |
| `build` | build | awiki | สกิลนี้ใช้คำสั่ง /build เพื่อแยกงานออกจากข้อความ ส่งต่อไปยัง telegram-command-router และ persona-... |
| `context-budget` | none | ecosystem | จัดการ context window — โหลดเฉพาะข้อมูลที่จำเป็น, compact เมื่อใกล้เต็ม |
| `continuous-agent-loop` | none | ecosystem | รูปแบบและสถาปัตยกรรม canonical สำหรับ autonomous agent loop — รองรับหลาย agent (Claude Code / Gem... |
| `continuous-learning` | none | uncategorized | สกิลนี้เป็นเวอร์ชันเก่าที่ถูกแทนที่ด้วย continuous-learning-v2 แล้ว ใช้สำหรับดึงข้อมูลจาก stop-ho... |
| `delegate-subagent` | none | wiki | มอบหมายงานย่อยให้ subagent/worker model — เพื่อประหยัด context ของ primary agent |
| `eval-harness` | none | ecosystem | กรอบงานประเมินผลแบบเป็นทางการสำหรับ Claude Code sessions ที่ใช้หลักการ eval-driven development (E... |
| `handoff` | meta | mattpocock | สร้าง handoff doc สั้นสำหรับส่งต่องานระหว่าง agent — สถานะปัจจุบัน, ทำอะไรต่อ, ไฟล์สำคัญ |
| `hermes-fan-out` | meta | swarm | รัน persona หลายตัวตามลำดับสำหรับ Hermes (ไม่มี concurrency ดั้งเดิม) — code-reviewer, test-engin... |
| `mcp-builder` | none | uncategorized | สร้าง MCP server — expose tool/resource ให้ agent เรียกใช้ผ่าน Model Context Protocol |
| `model-cost-switching` | none | ai-ops | จัดลำดับ model ตามต้นทุน — ใช้ model ถูกก่อน แพงทีหลัง. บังคับ cost-first decision pyramid |
| `plan` | plan | awiki | สกิลนี้ใช้รับคำสั่ง /plan จาก Telegram เพื่อแยกงานที่ซับซ้อนออกเป็นงานย่อยที่ตรวจสอบได้ โดยเรียกใ... |
| `review` | review | awiki | สกิลนี้ทำงานผ่านคำสั่ง /review ใน Telegram เพื่อดึงงานที่ต้องการตรวจสอบ จากนั้นเรียกใช้ telegram-... |
| `ship` | ship | awiki | สกิลนี้ใช้คำสั่ง /ship เพื่อดึงข้อมูล task จาก Telegram แล้วส่งต่อไปยัง telegram-command-router แ... |
| `strategic-compact` | none | ecosystem | แนะนำให้บีบอัดบริบทด้วยตนเองในช่วงเวลาที่เหมาะสมของงาน เพื่อรักษาบริบทที่สำคัญระหว่างขั้นตอนต่างๆ... |
| `token-optimization` | none | wiki | ลดการใช้ token — ใช้ Markdown แทน HTML, compact JSON, ตัด verbose output |
| `writing-great-skills` | meta | mattpocock | เอกสารอ้างอิงสำหรับการเขียนและแก้ไข skills ให้มีคุณภาพดี — ครอบคลุมหลักการและคำศัพท์ที่ทำให้ skil... |

### `productivity` — Productivity / Management

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `article-writing` | none | ecosystem | เขียนบทความ/บล็อก — มีโครง, hook, สาระ, ปิดท้าย |
| `blueprint` | none | ecosystem | สกิลนี้ช่วยให้คุณสร้าง blueprint หรือพิมพ์เขียวสำหรับโปรเจกต์ใหม่ได้อย่างรวดเร็ว โดยกำหนดโครงสร้า... |
| `doc-coauthoring` | none | uncategorized | แนะนำขั้นตอนการทำงานร่วมกันในการเขียนเอกสาร เช่น คู่มือ ข้อเสนอ สเปกเทคนิค หรือเอกสารตัดสินใจ โดย... |
| `handoff` | meta | mattpocock | สร้าง handoff doc สั้นสำหรับส่งต่องานระหว่าง agent — สถานะปัจจุบัน, ทำอะไรต่อ, ไฟล์สำคัญ |
| `management-talk` | none | uncategorized | สื่อสารแบบผู้นำ — สรุปงาน, วาง OKR, ให้ feedback, ประชุมมีประสิทธิภาพ |
| `plan-orchestrate` | none | ecosystem | อ่าน plan document แตกเป็น step แล้วออกแบบ agent chain ต่อ step จาก catalog — สั่ง execution แบบม... |
| `planning-and-task-breakdown` | plan | engineering-lifecycle | แยกงานใหญ่ให้เป็น task เล็กๆ ที่ทำได้ทีละชิ้น พร้อม dependency และลำดับ |
| `post-mortem` | none | uncategorized | เขียนบทเรียนหลัง incident: เกิดอะไรขึ้น, root cause, impact, แก้อย่างไร, ป้องกันยังไงคราวหน้า |
| `research-pipeline` | meta | pipeline | ไปป์ไลน์วิจัยแบบ 3 stage สำหรับทุก domain — รวบรวม -> สังเคราะห์ -> วิพากษ์วิจารณ์. ใช้ subagent ... |
| `teach` | none | mattpocock | สอนทักษะหรือแนวคิดใหม่ให้กับผู้ใช้ภายใน workspace นี้ โดยสามารถดำเนินการต่อเนื่องข้ามหลาย session... |
| `to-issues` | plan | mattpocock | แตก plan/spec/PRD เป็น issue แบบ tracer-bullet slice — แต่ละ issue ทำได้ทีละอันอิสระ |
| `to-prd` | define | mattpocock | สังเคราะห์บทสนทนาปัจจุบันให้เป็น PRD (Product Requirements Document) และเผยแพร่ออกมา โดยไม่ต้องสั... |
| `writing-great-skills` | meta | mattpocock | เอกสารอ้างอิงสำหรับการเขียนและแก้ไข skills ให้มีคุณภาพดี — ครอบคลุมหลักการและคำศัพท์ที่ทำให้ skil... |

### `wiki` — Wiki / Knowledge ops

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `ask-notebooklm` | none | wiki | สังเคราะห์คำตอบข้ามหลายไฟล์ใน wiki โดยใช้ Gemini API — เหมาะกับคำถามที่ต้องรวมข้อมูลหลายแหล่ง |
| `export-notebooklm` | none | wiki | สร้างหรือรีเฟรช snapshot ของ wiki เพื่อส่งออกไปยัง NotebookLM โดยเฉพาะเมื่อผู้ใช้พิมพ์ /snapshot-... |
| `ingest-source` | none | wiki | เอา source ใหม่ (URL, PDF, text) เข้า wiki — บันทึก raw ก่อน, สร้าง source summary, อัปเดต index |
| `lint-wiki` | none | wiki | ตรวจสุขภาพ wiki: broken links, missing frontmatter, ชื่อไฟล์ผิด format, confidence markers |
| `obsidian` | none | wiki | จัดการ notes ใน Obsidian — wikilinks, tags, template, graph view |
| `render-html` | none | uncategorized | render JSON/report เป็น HTML สวยๆ สำหรับดู — ประหยัด token เพราะ HTML ไม่กลับเข้า context |
| `search` | none | awiki | ค้นหาข้อมูลในวิกิด้วยคำสั่ง /search ซึ่งเป็น alias ของ /wiki ใช้ FTS5 ในการค้นหาแบบเต็มข้อความ ส่... |
| `wiki` | none | awiki | ค้นหาข้อมูลจาก Wikipedia ผ่านคำสั่ง /wiki โดยส่งคำค้นหาไปยัง Telegram-command-router แล้วเรียกใช้... |
| `wiki-search-local` | none | wiki | ค้น wiki แบบ offline ผ่าน FTS5 — เร็ว, ฟรี, ไม่ต้องเรียก LLM |

### `pharmacy` — ร้านยา / สต็อกยา

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-med-order` | build | pipeline | สั่งซื้อยาครบวง: ตรวจคำผิดชื่อยา (จำคำพ้องที่ยืนยันแล้วอัตโนมัติ) → ใบสั่งซื้อ Excel/Sheet → กรอก... |
| `pharmacy-order-lookup` | none | wiki | ค้นหาข้อมูลใบสั่งยาจากร้านขายยา โดยใช้หมายเลขใบสั่งยา (Order ID) หรือชื่อผู้ป่วย เพื่อดึงรายละเอี... |

### `thai` — ภาษาไทย / เอกสารไทย

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-doc` | build | pipeline | เอกสารราชการไทย/โรงพยาบาล — router ไป 8 ประเภท พร้อม grill format ทุกครั้ง. รองรับการเรียนรู้จากไ... |
| `a-doc-announce` | build | pipeline | ประกาศโรงพยาบาล — template canonical สมบูรณ์จากไฟล์จริง <HOSPITAL> |
| `thai-address` | none | thai | ใช้สำหรับแยกวิเคราะห์ ตรวจสอบ และจัดรูปแบบที่อยู่ของไทย รวมถึงการค้นหารหัสไปรษณีย์และจังหวัด รองร... |
| `thai-customer-service` | none | thai | ใช้สำหรับสร้างข้อความบริการลูกค้าภาษาไทย เช่น การตอบกลับ การขอโทษ การแจ้งสถานะคำสั่งซื้อ สคริปต์ค... |
| `thai-date-format` | none | thai | จัดรูปวันที่แบบไทย (พ.ศ., ปี ค.ศ. → พ.ศ.) — กันสับสน |
| `thai-festival-card` | none | thai | ใช้สร้างข้อความอวยพรหรือแสดงความเสียใจในโอกาสต่าง ๆ ของไทย เช่น วันสงกรานต์ วันลอยกระทง งานแต่งงา... |
| `thai-government-form` | none | thai | ใช้สำหรับสร้างเอกสารราชการไทย เช่น หนังสือราชการ หนังสือมอบอำนาจ หนังสือลา หนังสือร้องเรียน หรือแ... |
| `thai-id-validate` | none | thai | ใช้สำหรับตรวจสอบความถูกต้องของเลขบัตรประจำตัวประชาชนไทย เลขประจำตัวผู้เสียภาษี เบอร์โทรศัพท์ และ ... |
| `thai-invoice` | none | thai | ใช้สำหรับงานที่เกี่ยวข้องกับเอกสารภาษีไทย เช่น ใบกำกับภาษี ใบเสร็จรับเงิน ใบเสนอราคา และหนังสือรั... |
| `thai-pdpa` | none | thai | ตรวจสอบการปฏิบัติตาม พ.ร.บ. PDPA — การเก็บ/ใช้/เปิดเผยข้อมูลส่วนบุคคล |
| `thai-resume` | none | thai | ใช้สำหรับงานที่เกี่ยวข้องกับเรซูเม่และ CV ภาษาไทยหรือสองภาษา (ไทย/อังกฤษ) ช่วยร่าง เขียน หรือปรับ... |
| `thai-social-caption` | none | thai | ใช้สำหรับเขียนแคปชั่นภาษาไทยสำหรับโซเชียลมีเดีย โพสต์ หรือข้อความสั้น ๆ เหมาะกับงานที่ต้องการเนื้... |
| `thai-text-processing` | none | thai | ตัดคำ/normalize ข้อความไทย — จัดการกับ tokenization ที่ไทยไม่มีวรรคตอน |
| `thai-translate` | none | thai | แปลไทย-อังกฤษ คำศัพท์เทคนิค — รักษา context, ใช้คำเทคนิคที่คนไทยคุ้น |

### `media` — สื่อ / วิดีโอ / รูปภาพ

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-content` | meta | pipeline | งานเขียนคอนเทนต์และการตลาด — บทความ, brand voice, SEO, campaign, โพสต์โซเชียล |
| `algorithmic-art` | none | uncategorized | สร้างงานศิลปะเชิงอัลกอริทึมด้วย p5.js โดยใช้ seeded randomness เพื่อให้ผลลัพธ์ reproducible และให... |
| `game-phaser-pipeline` | build | game | Pipeline เกมสำหรับโปรเจก game ของ A-Wiki (PWQ) — Phaser + Vite + TypeScript + PixelLab ครบ: route... |
| `imagegen` | none | uncategorized | สร้างหรือแก้ไขภาพบิตแมปเมื่อต้องการภาพถ่าย ภาพประกอบ พื้นผิว สไปรต์ หรือภาพโปร่งใสที่ AI สร้างขึ้... |
| `motion-advanced` | none | ecosystem | ทักษะนี้รวบรวมเทคนิค motion ขั้นสูงสำหรับ React และ Next.js ครอบคลุม drag & drop, gesture, text a... |
| `motion-foundations` | none | ecosystem | จัดการ motion tokens, spring presets, และกฎ performance สำหรับ React/Next.js ด้วย motion/react คร... |
| `motion-patterns` | none | ecosystem | รวมแพทเทิร์น animation สำหรับ React / Next.js ที่พร้อมใช้งานจริง ครอบคลุมปุ่มกด, modal, toast, st... |
| `motion-ui` | none | uncategorized | ระบบ motion สำหรับ UI ที่พร้อมใช้งานจริงใน React/Next.js ใช้สำหรับเพิ่ม animation, transition และ... |
| `phaser-arcade-physics` | build | game | Phaser 3 Arcade Physics reference (colliders, overlap, velocity/gravity tuning) — vendored from g... |
| `phaser-core` | build | game | Phaser 3 core engine reference (scenes, game config, loader, sprites) — vendored from gamedev-ski... |
| `pixijs-rendering` | build | game | PixiJS rendering reference (containers, sprites, filters, render pipeline) — vendored from gamede... |
| `slack-gif-creator` | none | uncategorized | ความรู้และเครื่องมือสำหรับสร้าง GIF แบบเคลื่อนไหวที่เหมาะกับ Slack โดยเฉพาะ มีข้อจำกัดด้านขนาดและ... |
| `threejs-gltf-loading` | build | game | three.js glTF model loading reference — vendored from gamedev-skills/awesome-gamedev-agent-skills. |
| `threejs-materials-lighting` | build | game | three.js materials + lighting reference — vendored from gamedev-skills/awesome-gamedev-agent-skills. |
| `threejs-scene-setup` | build | game | three.js scene/camera/renderer setup reference — vendored from gamedev-skills/awesome-gamedev-age... |

### `document` — เอกสาร / docx/pdf/pptx/xlsx

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `a-doc` | build | pipeline | เอกสารราชการไทย/โรงพยาบาล — router ไป 8 ประเภท พร้อม grill format ทุกครั้ง. รองรับการเรียนรู้จากไ... |
| `a-doc-announce` | build | pipeline | ประกาศโรงพยาบาล — template canonical สมบูรณ์จากไฟล์จริง <HOSPITAL> |
| `assessment-generator` | none | uncategorized | สร้างข้อสอบหรือแบบประเมินจากเนื้อหาที่กำหนด โดยสามารถปรับระดับความยากและรูปแบบคำถามได้ เหมาะสำหรั... |
| `docx` | none | uncategorized | ใช้สร้าง อ่าน แก้ไข หรือจัดการไฟล์ Word (.docx) โดยตรง รองรับการเพิ่มข้อความ ตาราง รูปภาพ และจัดร... |
| `excel-generator` | none | wiki | สร้างสเปรดชีต Excel ระดับมืออาชีพที่เน้นความสวยงามและการวิเคราะห์ข้อมูล ใช้สำหรับจัดระเบียบ วิเคร... |
| `frontend-slides` | none | ecosystem | สร้างสไลด์นำเสนอ HTML ที่สวยงามและมีอนิเมชั่นตั้งแต่เริ่มต้น หรือแปลงจากไฟล์ PowerPoint เหมาะสำหร... |
| `pptx` | none | uncategorized | ใช้เมื่อต้องทำงานกับไฟล์ .pptx ไม่ว่าจะเป็นการสร้างสไลด์เด็ค พิตช์เด็ค หรือพรีเซนเทชันใหม่ อ่านแล... |
| `word-generator` | none | uncategorized | สร้างคำศัพท์หรือข้อความแบบสุ่มตามพารามิเตอร์ที่กำหนด เช่น จำนวนคำ ประเภทของคำ หรือรูปแบบที่ต้องกา... |
| `xlsx` | none | uncategorized | ใช้เมื่อไฟล์สเปรดชีต (.xlsx) เป็นอินพุตหรือเอาต์พุตหลัก เช่น เปิด อ่าน แก้ไข หรือซ่อมแซมไฟล์ Exce... |

### `sre` — SRE / Observability / Deploy

| Skill | Lifecycle | Category | Description |
|-------|-----------|----------|-------------|
| `ci-cd-and-automation` | ship | engineering-lifecycle | ตั้ง CI/CD pipeline — auto test, lint, build, deploy เพื่อลดมนุษย์ผิดพลาด |
| `observability-and-instrumentation` | ship | engineering-lifecycle | เพิ่ม structured logging, RED metrics, OpenTelemetry tracing และ symptom-based alerting ระหว่างกา... |

## 🔄 Lifecycle-Phase Map

Skills that participate in the engineering lifecycle (DEFINE→PLAN→BUILD→VERIFY→REVIEW→SHIP):

- **DEFINE**: `a-plan`, `design-first-ui-prompting`, `domain-modeling`, `grill-with-docs`, `research`, `spec-driven-development`, `to-prd`
- **PLAN**: `cross-agent-work-orders`, `plan`, `planning-and-task-breakdown`, `to-issues`
- **BUILD**: `a-doc`, `a-doc-announce`, `a-med-order`, `add-shader-cursor-trail`, `build`, `cinematic-gsap-lenis-motion-system`, `codebase-design`, `game-phaser-pipeline`, `gsap`, `gsap-scrolltrigger-storytelling`, `implement`, `phaser-arcade-physics`, `phaser-core`, `pixijs-rendering`, `prototype`, `scaffold-exercises`, `shaders-cursor-ripples`, `taste-skill`, `tdd`, `threejs`, `threejs-gltf-loading`, `threejs-materials-lighting`, `threejs-scene-setup`, `transitions-dev`, `ui-ux-pro-max`, `webgl-3d-object`
- **VERIFY**: `a-debug`, `browser-testing-with-devtools`, `test-engineer`, `triage`
- **REVIEW**: `a-council`, `audit-reference-originality`, `code-reviewer`, `code-simplification`, `improve-codebase-architecture`, `optimize-web-animations`, `performance-optimization`, `review`, `security-and-hardening`, `security-auditor`, `two-axis-code-review`, `web-performance-auditor`
- **SHIP**: `ci-cd-and-automation`, `deprecation-and-migration`, `documentation-and-adrs`, `git-workflow-and-versioning`, `observability-and-instrumentation`, `ship`, `shipping-and-launch`, `symlink-connector`
- **META**: `a-claim`, `a-content`, `a-escalate`, `a-invest`, `a-loop`, `a-research`, `a-router`, `a-think`, `a-web`, `awiki-lifecycle-router`, `finance-pipeline`, `handoff`, `hermes-fan-out`, `medical-pipeline`, `platform-ingest`, `research-pipeline`, `writing-great-skills`

## 🔁 Alias → Canonical Resolution

Deprecated/alias skills and their canonical replacement. Agents invoking the
alias name auto-resolve to the canonical (USA-1 §7.2).

| Alias / Deprecated | → Canonical | Note |
|--------------------|-------------|------|
| `hipaa-compliance` | `healthcare-phi-compliance` |  |
| `laravel-verification` | `django-verification` |  |
| `quarkus-verification` | `django-verification` |  |
| `springboot-verification` | `django-verification` |  |
| `token-budget-advisor` | `context-budget` |  |

## ⚡ Quick-Pick — what to use when

| Intent | Skill(s) |
|--------|----------|
| Refine a vague idea before building | `brainstorm-before-build` |
| Write a spec before coding | `spec-driven-development` |
| Break a spec into verifiable tasks | `planning-and-task-breakdown` |
| Implement code (thin slices) | `incremental-implementation` |
| Write the failing test first | `test-driven-development` · `tdd` · `tdd-workflow` |
| Something is broken — find root cause | `debug-mantra` · `root-cause-first` |
| Review code | `scrutinize` · `code-simplification` |
| Security review | `security-and-hardening` · `hipaa-compliance` · `thai-pdpa` |
| Performance optimization | `performance-optimization` · `react-performance` |
| Ship / deploy / release | `shipping-and-launch` · `git-workflow-and-versioning` |
| Write an ADR / doc | `documentation-and-adrs` |
| Ingest a source into the wiki | `ingest-source` |
| Search the wiki locally (free) | `wiki-search-local` |
| Cross-file synthesis | `ask-notebooklm` |
| Find existing skills before creating | `skill-scout` |
| Delegate to a free model | `delegate-subagent` |

---

*USA-1 §6 — A-Wiki v1.2 · Central Skill Brain · auto-generated*
