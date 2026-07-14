"""Thai skill guide content for the Live Dashboard Skills view.

Single source of truth for v2 fields:
  - th_description   (Thai, 2-3 sentences)
  - when_to_use      (Thai trigger phrases)
  - examples         ([{scenario, how}, ...]) 1-2 concrete cases
  - process_steps    ([str, ...]) for simulation animation
  - invocation       ("auto"|"manual"|"both") overrides the "manual" default
                     set by the v1→v2 migration when a skill is hook-loaded.

Apply via:
    python scripts/skills_registry/apply_thai_guide.py

The apply script is idempotent: re-running only updates skills listed here and
never removes fields from skills that are not in THAI_GUIDE.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Core ~50 skills — grouped by function for readability.
# Keep entries concise; the dashboard truncates long descriptions.
# ---------------------------------------------------------------------------

THAI_GUIDE: dict[str, dict] = {
    # ── Lifecycle (define → ship) ──────────────────────────────────────────
    "spec-driven-development": {
        "invocation": "manual",
        "th_description": "เขียนสเปก/requirements ให้ชัดก่อนเริ่มเขียนโค้ด เพื่อให้ทุกคน (และ AI) เข้าใจตรงกันว่าต้องทำอะไร ถึงเงื่อนไขไหนถือว่าเสร็จ",
        "when_to_use": "เริ่มฟีเจอร์ใหม่, แก้ bug ใหญ่, หรือทำงานที่ซับซ้อนเกิน 1 ไฟล์",
        "examples": [
            {"scenario": "จะทำระบบ login OAuth", "how": "เขียนสเปกก่อน: flow, error cases, acceptance criteria แล้วค่อยโค้ด"},
            {"scenario": "ลูกค้าขอฟีเจอร์ export PDF", "how": "ระบุ field, layout, ขนาดก่อนเขียน 1 บรรทัด"},
        ],
        "process_steps": ["ระบุปัญหา", "เขียน acceptance criteria", "แยกหน้า concern", "เอาสเปกมาทำ TDD"],
    },
    "brainstorm-before-build": {
        "invocation": "manual",
        "th_description": "บังคับให้ถาม user 3 คำถาม (scope/constraint/success) ก่อนเริ่มสร้างสิ่งใหม่ ป้องกันการเขียนผิดทิศทาง",
        "when_to_use": "ก่อนสร้าง skill/hook/script/feature ใหม่ หรือ refactor ที่กระทบ >3 ไฟล์",
        "examples": [
            {"scenario": "user ขอ 'ทำสกิล superpowers'", "how": "ถามก่อน: ติดเต็มหรือ cherry-pick? เน้น coding หรือ wiki?"},
        ],
        "process_steps": ["ถาม clarify (≤3 คำถาม)", "เสนอ 2-3 approach", "รอ user เลือก", "เขียน plan"],
    },
    "planning-and-task-breakdown": {
        "invocation": "manual",
        "th_description": "แยกงานใหญ่ให้เป็น task เล็กๆ ที่ทำได้ทีละชิ้น พร้อม dependency และลำดับ",
        "when_to_use": "งานมีหลายขั้นตอน, ต้องประเมินเวลา, หรือแบ่งงานให้หลายคน/หลาย agent",
        "examples": [
            {"scenario": "ย้ายระบบจาก REST เป็น GraphQL", "how": "แตกเป็น: schema → resolver → migration → test → cutover"},
        ],
    },
    "incremental-implementation": {
        "invocation": "manual",
        "th_description": "ทำทีละส่วนเล็ก ทดสอบแต่ละส่วนให้ผ่านก่อนไปต่อ ไม่รวบยอดเขียนทีเดียว",
        "when_to_use": "implement ฟีเจอร์ที่มีหลายขั้นตอน หรือกลัวเขียนเยอะแล้ว debug ยาก",
        "examples": [
            {"scenario": "เขียน API endpoint ใหม่", "how": "ทำ route → logic → test ทีละ chunk, commit ทุก chunk"},
        ],
        "_note": "Skill exists in skills/engineering-lifecycle/build/ but not yet in registry — entry kept for when it is registered",
    },
    "tdd": {
        "invocation": "manual",
        "th_description": "เขียน test ก่อนโค้ด (Red-Green-Refactor) เพื่อให้แน่ใจว่าโค้ดทำงานถูกและกัน regression",
        "when_to_use": "เขียนฟังก์ชันใหม่, แก้ bug (เขียน test สำหรับ bug ก่อน), หรือ refactor",
        "examples": [
            {"scenario": "เขียนฟังก์ชันคำนวณส่วนลด", "how": "เขียน test ว่า input X ต้องได้ Y ก่อน, รันให้ fail, แล้วเขียนโค้ด"},
        ],
        "process_steps": ["เขียน test (Red)", "เขียนโค้ดให้ผ่าน (Green)", "ปรับให้สะอาด (Refactor)"],
    },
    "code-simplification": {
        "invocation": "manual",
        "th_description": "ลดความซับซ้อนของโค้ด โดยไม่เปลี่ยนพฤติกรรม — ทำให้อ่านง่ายขึ้น ลดซ้ำ ตัดส่วนที่ไม่จำเป็น",
        "when_to_use": "โค้ดอ่านยาก, มี duplicate, ฟังก์ชันยาวเกินไป หรือหลัง implement เสร็จ",
        "examples": [
            {"scenario": "ฟังก์ชัน 200 บรรทัด", "how": "แยกเป็น 3-4 ฟังก์ชันเล็ก ตั้งชื่อให้อธิบายตัวเอง"},
        ],
    },
    "shipping-and-launch": {
        "invocation": "manual",
        "th_description": "เช็คลิสต์ก่อน release: test, docs, migration, rollback plan, monitoring — ให้มั่นใจว่า launch ปลอดภัย",
        "when_to_use": "ก่อน deploy ขึ้น production, release ฟีเจอร์ใหญ่, หรือส่งมอบงาน",
        "examples": [
            {"scenario": "deploy ฟีเจอร์ checkout ใหม่", "how": "เช็ค: test ผ่าน, migration dry-run, rollback script พร้อม, alert ตั้ง"},
        ],
    },

    # ── Lifecycle / patterns (language & framework) ───────────────────────
    "backend-patterns": {
        "invocation": "manual",
        "th_description": "design pattern ฝั่ง backend — API design, database optimization, server-side best practice สำหรับ service ที่ scale",
        "when_to_use": "ออกแบบ backend ใหม่, ปรับ API/database, หรือเตรียมรองรับโหลดสูง",
        "examples": [
            {"scenario": "API ช้า", "how": "/backend-patterns ตรวจ N+1 query, caching, indexing"},
        ],
    },
    "django-patterns": {
        "invocation": "manual",
        "th_description": "design pattern Django — architecture, DRF REST API, ORM best practice, caching, signals, middleware",
        "when_to_use": "ใช้ Django/DRF แล้วอยากทำตามมาตรฐาน, ปรับ ORM/API ให้เร็วและสะอาด",
        "examples": [
            {"scenario": "Django API ช้า", "how": "/django-patterns select_related + caching + pagination"},
        ],
    },
    "django-tdd": {
        "invocation": "manual",
        "th_description": "กลยุทธ์ test Django ด้วย pytest-django + factory_boy + mocking + coverage — TDD แบบ Django",
        "when_to_use": "เขียน Django แล้วอยากมี test ที่ทน ไม่ซับซ้อนเกิน",
        "examples": [
            {"scenario": "test model + view", "how": "/django-tdd factory + pytest + coverage ≥ 80%"},
        ],
    },
    "django-security": {
        "invocation": "manual",
        "th_description": "security ของ Django — auth, authorization, CSRF, SQL injection, ป้องกันช่องโหว่ทั่วไป",
        "when_to_use": "Django app ขึ้น production, audit ความปลอดภัย, เพิ่ม auth ที่แข็งแรง",
        "examples": [
            {"scenario": "ตั้ง auth ใหม่", "how": "/django-security session, CSRF, password policy"},
        ],
    },
    "react-testing": {
        "invocation": "manual",
        "th_description": "test React component ด้วย React Testing Library + Vitest/Jest + MSW mock network + accessibility check",
        "when_to_use": "เขียน React แล้วต้องการ test ที่เชื่อถือได้ ไม่ fragile",
        "examples": [
            {"scenario": "test form submit", "how": "/react-testing RTL + MSW mock API + assert"},
        ],
    },
    "react-performance": {
        "invocation": "manual",
        "th_description": "optimize React/Next.js — memo, code-splitting, lazy loading, render budget ตามแนวทาง Vercel engineering",
        "when_to_use": "React app ช้า, re-render เยอะ, bundle ใหญ่, Lighthouse คะแนนต่ำ",
        "examples": [
            {"scenario": "list 1000 แถวกระตุก", "how": "/react-performance memo + virtualization"},
        ],
    },
    "rust-testing": {
        "invocation": "manual",
        "th_description": "กลยุทธ์ test Rust — unit, integration, async test, property-based test, doctest",
        "when_to_use": "เขียน Rust แล้วอยากมี test ครอบคลุม รวม async/property",
        "examples": [
            {"scenario": "test async fn", "how": "/rust-testing tokio::test + property-based"},
        ],
    },
    "kotlin-coroutines-flows": {
        "invocation": "manual",
        "th_description": "coroutine + Flow ของ Kotlin สำหรับ Android/KMP — structured concurrency, Flow operator, state/cold/hot flow",
        "when_to_use": "เขียน Android/KMP แล้วใช้ async/Flow ไม่คล่อง หรือเจอ bug สาย concurrency",
        "examples": [
            {"scenario": "รวมหลาย Flow", "how": "/kotlin-coroutines-flows combine + flatMapMerge"},
        ],
    },
    "springboot-patterns": {
        "invocation": "manual",
        "th_description": "design pattern Spring Boot — REST API, layered services, data access, caching, async processing",
        "when_to_use": "สร้าง/ปรับ service Spring Boot, อยากทำตาม pattern ที่คนทั่วไปใช้",
        "examples": [
            {"scenario": "REST API ของ service", "how": "/springboot-patterns controller-service-repository"},
        ],
    },
    "swiftui-patterns": {
        "invocation": "manual",
        "th_description": "pattern SwiftUI — state ด้วย @Observable, view composition, navigation, performance",
        "when_to_use": "เขียน SwiftUI แล้วอยากมีโครงสะอาด, view ซับซ้อน, หรือกระตุกเรื่อง state",
        "examples": [
            {"scenario": "state กระจาย", "how": "/swiftui-patterns ใช้ @Observable + environment"},
        ],
    },
    "golang-patterns": {
        "invocation": "manual",
        "th_description": "แนวทางเขียนโค้ดภาษา Go ที่ใช้กันทั่วไป — concurrency ด้วย goroutine และ channel, การจัดการ error, โครงสร้างแพ็กเกจ, interface แบบ implicit รวมถึงการทำ context",
        "when_to_use": "เขียนเซอร์วิสด้วย Go, อยากทำตามฉันทามติของชุมชน, หรือเริ่มโปรเจกต์ใหม่",
        "examples": [
            {"scenario": "เซอร์วิส HTTP ใน Go", "how": "/golang-patterns แนะนำโครงและ best practice"},
        ],
    },
    "kotlin-patterns": {
        "invocation": "manual",
        "th_description": "แนวทางเขียนโค้ดภาษา Kotlin ที่นิยม — coroutine, scope function, data class, sealed class, null safety และการขยายความสามารถด้วย extension function",
        "when_to_use": "เขียนแอป Android หรือเซอร์วิสด้วย Kotlin, อยากเขียนให้กระชับและปลอดภัยกว่า Java",
        "examples": [
            {"scenario": "โมเดลข้อมูล + API", "how": "/kotlin-patterns แนะ data class + coroutine"},
        ],
    },

    # ── Iron Law / Engineering ─────────────────────────────────────────────
    "debug-mantra": {
        "invocation": "manual",
        "th_description": "วินัย 4 ข้อสำหรับ debug: (1) reproduce ให้ได้ก่อน (2) รู้ fail path (3) ตั้งข้อสงสัยแล้วหาที่หักล้าง (4) เก็บ breadcrumb ทุกครั้ง. บังคับ Iron Law #2",
        "when_to_use": "ทุกครั้งที่เจอ bug — ห้ามแก้โดยไม่หา root cause ก่อน",
        "examples": [
            {"scenario": "แอป crash บางครั้ง", "how": "reproduce ให้ได้ก่อน, trace stack, ตั้งสมมติฐาน แล้วหา evidence หักล้าง"},
            {"scenario": "production error ไม่ชัด", "how": "ดู log ทุก layer, cross-reference, ห้าม patch ลอยๆ"},
        ],
        "process_steps": ["Reproduce ให้ได้", "Trace fail path", "ตั้งและหักล้างสมมติฐาน", "Cross-reference breadcrumbs"],
    },
    "scrutinize": {
        "invocation": "manual",
        "th_description": "รีวิวแบบเข้ม — ตั้งคำถามทุก assumption, หา edge case, เช็ค security/perf. ใช้คู่กับ code-review",
        "when_to_use": "รีวิวงานก่อน merge, audit ระบบเก่า, หรือตรวจงานที่ risky",
        "examples": [
            {"scenario": "PR ใหญ่ก่อน merge", "how": "scrutinize ทุกไฟล์: logic, test, security, perf"},
        ],
    },
    "post-mortem": {
        "invocation": "manual",
        "th_description": "เขียนบทเรียนหลัง incident: เกิดอะไรขึ้น, root cause, impact, แก้อย่างไร, ป้องกันยังไงคราวหน้า",
        "when_to_use": "หลัง production incident, outage, หรือ bug รุนแรง",
        "examples": [
            {"scenario": "DB down 2 ชม.", "how": "เขียน post-mortem: timeline, root cause, action items"},
        ],
        "process_steps": ["สรุปเหตุการณ์", "หา root cause", "ประเมิน impact", "กำหนด action items"],
    },
    "root-cause-first": {
        "invocation": "manual",
        "th_description": "หา root cause ก่อนแก้ — ไม่ใช่แก้ symptom. ใช้ 5-Whys หรือ fishbone",
        "when_to_use": "bug ซ้ำ, ปัญหาเรื้อรัง, หรือก่อนแก้ production issue",
        "examples": [
            {"scenario": "แอปช้าเป็นบางครั้ง", "how": "ถาม why 5 ครั้งจนถึง root: query N+1? cache miss? DB lock?"},
        ],
    },
    "verify-before-done": {
        "invocation": "manual",
        "th_description": "บังคับตรวจสอบก่อนบอกว่า 'เสร็จแล้ว' — รัน test, ตรวจ output, ยืนยันจริงไม่ใช่แค่คิดว่าเสร็จ",
        "when_to_use": "ก่อนบอก user ว่าทำเสร็จ, ก่อน commit, หรือหลัง refactor",
        "examples": [
            {"scenario": "แก้ bug เสร็จ", "how": "รัน test, reproduce bug อีกครั้งให้แน่ใจหาย, แล้วค่อยบอกเสร็จ"},
        ],
    },
    "safety-guard": {
        "invocation": "manual",
        "th_description": "ตรวจสอบความปลอดภัยก่อนทำการที่เสียหายได้ยาก — delete, force push, ส่งข้อมูลออก, เปลี่ยน production",
        "when_to_use": "ก่อนลบไฟล์, force push, ส่ง request ออก outside, หรือแก้ production config",
        "examples": [
            {"scenario": "จะ git push --force", "how": "safety-guard บังคับยืนยันก่อน, เช็ค branch"},
        ],
    },

    # ── Wiki ops ───────────────────────────────────────────────────────────
    "ingest-source": {
        "invocation": "manual",
        "th_description": "เอา source ใหม่ (URL, PDF, text) เข้า wiki — บันทึก raw ก่อน, สร้าง source summary, อัปเดต index",
        "when_to_use": "user ส่ง URL/PDF/file ให้เก็บเป็นความรู้ใน wiki",
        "examples": [
            {"scenario": "user ส่งลิงก์บทความ MQTT", "how": "save raw → harness route → wiki/sources/mqtt.md → gen-index"},
        ],
        "process_steps": ["save ลง raw/", "ผ่าน harness route", "สร้าง wiki/sources/", "regen index"],
    },
    "lint-wiki": {
        "invocation": "manual",
        "th_description": "ตรวจสุขภาพ wiki: broken links, missing frontmatter, ชื่อไฟล์ผิด format, confidence markers",
        "when_to_use": "หลังแก้ wiki เยอะ, หรือเป็น routine health check",
        "examples": [
            {"scenario": "เพิ่มหน้า wiki 10 หน้า", "how": "/lint-wiki ตรวจ link + frontmatter ให้ครบ"},
        ],
    },
    "wiki-search-local": {
        "invocation": "manual",
        "th_description": "ค้น wiki แบบ offline ผ่าน FTS5 — เร็ว, ฟรี, ไม่ต้องเรียก LLM",
        "when_to_use": "อยากค้นความรู้ใน wiki, หาหน้าที่เกี่ยวข้อง, ก่อนเขียนหน้าใหม่เพื่อกันซ้ำ",
        "examples": [
            {"scenario": "อยากรู้เรื่อง DS18B20", "how": "search 'DS18B20' ก่อนเขียนหน้าใหม่"},
        ],
    },
    "ask-notebooklm": {
        "invocation": "manual",
        "th_description": "สังเคราะห์คำตอบข้ามหลายไฟล์ใน wiki โดยใช้ Gemini API — เหมาะกับคำถามที่ต้องรวมข้อมูลหลายแหล่ง",
        "when_to_use": "คำถามที่คำตอบอยู่กระจายในหลายหน้า wiki, ต้องการ synthesis ไม่ใช่แค่ search",
        "examples": [
            {"scenario": "'ระบบ IoT มีอะไรบ้าง'", "how": "ask-notebooklm รวมข้อมูลจากทุกหน้า iot/"},
        ],
    },
    "connections-optimizer": {
        "invocation": "manual",
        "th_description": "วิเคราะห์และเสนอ [[wikilinks]] ระหว่างหน้า เพื่อให้ knowledge graph แน่นขึ้น",
        "when_to_use": "หลังเพิ่มหน้าใหม่, หรือเป็น periodic maintenance",
        "examples": [
            {"scenario": "เพิ่มหน้า ESP32", "how": "optimizer เสนอลิงก์ไป MQTT, OTA, pinout ที่เกี่ยวข้อง"},
        ],
    },

    # ── Swarm / Cost ───────────────────────────────────────────────────────
    "model-cost-switching": {
        "invocation": "manual",
        "th_description": "จัดลำดับ model ตามต้นทุน — ใช้ model ถูกก่อน แพงทีหลัง. บังคับ cost-first decision pyramid",
        "when_to_use": "ก่อนเริ่มงาน multi-step หรือ task มีต้นทุนสูง — classify ก่อนเลือก tier",
        "examples": [
            {"scenario": "ต้อง scan 50 ไฟล์", "how": "ใช้ tier ถูก (free/cheap) ก่อน ไม่ใช่ primary model"},
        ],
    },
    "delegate-subagent": {
        "invocation": "manual",
        "th_description": "มอบหมายงานย่อยให้ subagent/worker model — เพื่อประหยัด context ของ primary agent",
        "when_to_use": "งานซ้ำๆ (scan, lint, gather), หรือเมื่อ primary agent เริ่มเต็ม context",
        "examples": [
            {"scenario": "ค้นหา symbol ใน codebase ใหญ่", "how": "delegate ให้ Explore agent"},
        ],
    },
    "cost-tracking": {
        "invocation": "manual",
        "th_description": "ติดตามต้นทุนการใช้ model/token — รู้ว่างานไหนแพง และหาทางลด",
        "when_to_use": "งาน multi-step, หรืออยากรู้ว่าใช้ token เยอะเพราะอะไร",
        "examples": [
            {"scenario": "session ใช้เงินเยอะ", "how": "/cost-tracking ดูว่า task ไหนแพง ปรับ tier"},
        ],
    },
    "context-budget": {
        "invocation": "manual",
        "th_description": "จัดการ context window — โหลดเฉพาะข้อมูลที่จำเป็น, compact เมื่อใกล้เต็ม",
        "when_to_use": "งานยาว, หรือเริ่มรู้สึกว่า agent 'ลืม' เพราะ context เต็ม",
        "examples": [
            {"scenario": "session ยาว 50+ turn", "how": "compact: เก็บ summary สละ detail"},
        ],
    },
    "token-optimization": {
        "invocation": "manual",
        "th_description": "ลดการใช้ token — ใช้ Markdown แทน HTML, compact JSON, ตัด verbose output",
        "when_to_use": "เมื่อต้องการประหยัดค่าใช้จ่าย หรือ context เริ่มเต็ม",
        "examples": [
            {"scenario": "report ยาว 5000 token", "how": "แปลงเป็น compact JSON + render-html แทน"},
        ],
    },

    # ── Process / Meta ─────────────────────────────────────────────────────
    "awiki-lifecycle-router": {
        "invocation": "auto",
        "th_description": "ตัวกลางที่ map 'intent ของ user' → 'skill ที่เหมาะสม' ตาม lifecycle (define→ship). โหลดอัตโนมัติตอน session start",
        "when_to_use": "อัตโนมัติทุก session — เป็นตัวตัดสินใจว่าจะใช้ skill ไหน",
        "examples": [
            {"scenario": "user พิมพ์ 'bug นี้'", "how": "router → debug-mantra"},
            {"scenario": "user พิมพ์ 'deploy'", "how": "router → shipping-and-launch"},
        ],
        "process_steps": ["define", "plan", "build", "verify", "review", "ship"],
    },
    "handoff": {
        "invocation": "manual",
        "th_description": "สร้าง handoff doc สั้นสำหรับส่งต่องานระหว่าง agent — สถานะปัจจุบัน, ทำอะไรต่อ, ไฟล์สำคัญ",
        "when_to_use": "switch agent, ปิด session กลางคัน, หรือส่งต่อให้คนอื่น",
        "examples": [
            {"scenario": "switch Claude → Codex", "how": "เขียน handoff.md แล้ว push"},
        ],
        "_note": "cross-agent-plan-handoff protocol lives in docs/protocols/ but the skill itself is registered as 'handoff'",
    },
    "continuous-learning-v2": {
        "invocation": "auto",
        "th_description": "เรียนรู้จาก pattern ที่เกิดซ้ำ — ถ้าทำงานแบบเดิมบ่อย แนะนำให้สร้าง skill/hook",
        "when_to_use": "อัตโนมัติทุก session — detect recurring patterns",
        "examples": [
            {"scenario": "ทำ git workflow ซ้ำๆ", "how": "เสนอสร้าง skill git-workflow"},
        ],
    },

    # ── Quality ────────────────────────────────────────────────────────────
    "two-axis-code-review": {
        "invocation": "manual",
        "th_description": "รีวิวโค้ดแบบ 2 แกน: (1) correctness/logic (2) style/maintainability",
        "when_to_use": "ก่อน merge PR, หลัง implement เสร็จ, หรือ audit โค้ดเก่า",
        "examples": [
            {"scenario": "เพื่อนส่ง PR", "how": "/two-axis-code-review ดูทั้ง logic และ style"},
        ],
    },
    "security-and-hardening": {
        "invocation": "manual",
        "th_description": "ตรวจช่องโหว่ความปลอดภัย: injection, auth, secret leak, input validation",
        "when_to_use": "รีวิว security, ก่อน deploy, หรือรับงานที่ sensitive",
        "examples": [
            {"scenario": "API มี input จาก user", "how": "ตรวจ SQL injection, XSS, auth"},
        ],
    },
    "performance-optimization": {
        "invocation": "manual",
        "th_description": "หาและแก้ bottleneck — profile ก่อน, แก้ที่จุดที่ช้าจริง ไม่ใช่เดา",
        "when_to_use": "แอป/API ช้า, ใช้ CPU/DB เยอะ, หรือ user ร้องเรียนความเร็ว",
        "examples": [
            {"scenario": "API ตอบช้า 2 วิ", "how": "profile → พบ N+1 query → แก้ → วัดใหม่"},
        ],
    },
    "agent-eval": {
        "invocation": "manual",
        "th_description": "ประเมินคุณภาพของ agent/prompt — วัด accuracy, cost, latency และหาจุดปรับปรุง",
        "when_to_use": "สร้าง agent ใหม่, แก้ prompt, หรือเปรียบเทียบ model",
        "examples": [
            {"scenario": "เปลี่ยน prompt", "how": "eval ก่อน/หลัง เพื่อดูว่าดีขึ้นจริง"},
        ],
    },
    "production-audit": {
        "invocation": "manual",
        "th_description": "ตรวจสุขภาพระบบ production: logs, monitoring, alerting, runbook, SLO",
        "when_to_use": "เข้ามาดูแลระบบใหม่, หลัง incident, หรือ periodic audit",
        "examples": [
            {"scenario": "รับลูกค้าใหม่", "how": "audit: monitoring ครบไหม, alert ทำงานไหม"},
        ],
    },

    # ── Document / Git ─────────────────────────────────────────────────────
    "documentation-and-adrs": {
        "invocation": "manual",
        "th_description": "เขียน doc และ ADR (Architecture Decision Record) — บันทึกทำไมถึงตัดสินใจแบบนี้",
        "when_to_use": "ตัดสินใจ architecture, เปลี่ยนเทคโนโลยี, หรือ doc สำคัญ",
        "examples": [
            {"scenario": "เลือก Postgres แทน MySQL", "how": "เขียน ADR: context, options, decision, consequences"},
        ],
    },
    "git-workflow-and-versioning": {
        "invocation": "manual",
        "th_description": "มาตรฐาน git: commit message format, branching, versioning, tagging",
        "when_to_use": "เริ่ม project, ตั้ง convention, หรือก่อน release",
        "examples": [
            {"scenario": "ทำ semantic versioning", "how": "ตั้งกฎ: feat→minor, fix→patch, break→major"},
        ],
    },
    "ci-cd-and-automation": {
        "invocation": "manual",
        "th_description": "ตั้ง CI/CD pipeline — auto test, lint, build, deploy เพื่อลดมนุษย์ผิดพลาด",
        "when_to_use": "project ใหม่, หรืออยาก automate งานที่ทำซ้ำ",
        "examples": [
            {"scenario": "ทุก push ต้อง test", "how": "CI: run pytest + lint ก่อน merge"},
        ],
    },
    "deprecation-and-migration": {
        "invocation": "manual",
        "th_description": "เลิกใช้/ย้ายระบบเก่าอย่างปลอดภัย — มี migration path, sunset timeline, fallback",
        "when_to_use": "ย้าย API, เปลี่ยน library, หรือปิดฟีเจอร์เก่า",
        "examples": [
            {"scenario": "เลิก API v1", "how": "deprecate → แจ้ง → ให้เวลา → migrate → sunset"},
        ],
    },

    # ── Productivity ───────────────────────────────────────────────────────
    "management-talk": {
        "invocation": "manual",
        "th_description": "สื่อสารแบบผู้นำ — สรุปงาน, วาง OKR, ให้ feedback, ประชุมมีประสิทธิภาพ",
        "when_to_use": "เขียน status update, นำทีม, หรือสื่อสารกับ stakeholder",
        "examples": [
            {"scenario": "สรุปงานสัปดาห์", "how": "/management-talk สรุป progress, blocker, next"},
        ],
    },
    "internal-comms": {
        "invocation": "manual",
        "th_description": "เขียนสื่อสารภายในองค์กร — memo, announcement, changelog",
        "when_to_use": "ประกาศ policy, release note, หรือสื่อสารข้ามทีม",
        "examples": [
            {"scenario": "ประกาศเปลี่ยน policy WFH", "how": "internal-comms เขียน memo ชัดเจน"},
        ],
    },
    "article-writing": {
        "invocation": "manual",
        "th_description": "เขียนบทความ/บล็อก — มีโครง, hook, สาระ, ปิดท้าย",
        "when_to_use": "เขียน blog, tutorial, หรือ content marketing",
        "examples": [
            {"scenario": "สอนใช้ MQTT", "how": "/article-writing โครง intro → concept → example → summary"},
        ],
    },
    "render-html": {
        "invocation": "manual",
        "th_description": "render JSON/report เป็น HTML สวยๆ สำหรับดู — ประหยัด token เพราะ HTML ไม่กลับเข้า context",
        "when_to_use": "ต้องการดู report/ตารางแบบสวย แต่ไม่อยากเปลือง context window",
        "examples": [
            {"scenario": "report 1000 บรรทัด", "how": "emit JSON → render-html → ได้ไฟล์ดู ไม่เปลือง token"},
        ],
    },
    "grill-me": {
        "invocation": "manual",
        "th_description": "สัมภาษณ์ยืดเยื้อเพื่อลับแผนหรือดีไซน์ — ถามทีละคำถาม เสนอคำตอบให้คุณปฏิเสธ บังคับให้คิดลึกก่อนสร้าง",
        "when_to_use": "มีแผนหรือไอเดียแต่ยังไม่ชัด อยากถูกท้าทายก่อน commit ลงไป",
        "examples": [
            {"scenario": "จะทำฟีเจอร์ใหม่", "how": "/grill-me ถามจนกว่าจะเจาะจงได้ว่าทำเพราะอะไร"},
        ],
        "process_steps": ["ตั้งคำถามใหญ่", "เสนอคำตอบให้ปฏิเสธ", "ขุดลึกแต่ละจุด", "สรุปแผนที่ผ่านการท้าทาย"],
    },
    "grilling": {
        "invocation": "manual",
        "th_description": "สอบสวนแบบไม่ยอมแพ้ — ทีละคำถาม เสนอแนะคำตอบ ใช้ซ้ำเมื่อไอเดียยังหลวมๆ",
        "when_to_use": "อยากฝืนเยอะกว่า grill-me, มีเวลา, หรือเดิมพันสูง",
        "examples": [
            {"scenario": "เลือก architecture", "how": "/grilling ไล่แต่ละ option จนเหลือตัวเดียว"},
        ],
    },
    "grill-with-docs": {
        "invocation": "manual",
        "th_description": "เหมือน grilling แต่ผลพลอยได้คือเอกสาร — ADR + glossary เกิดตามมาจากการสอบสวน",
        "when_to_use": "ต้องการทั้งลับแผนและได้เอกสาร ADR/glossary ในรอบเดียว",
        "examples": [
            {"scenario": "วาง schema ใหม่", "how": "/grill-with-docs ได้ทั้ง decision + ADR บันทึก"},
        ],
        "process_steps": ["สัมภาษณ์แผน", "บันทึก glossary", "สร้าง ADR", "สรุป decision"],
    },
    "triage": {
        "invocation": "manual",
        "th_description": "ขับ issue/PR ผ่าน state machine ของการตัดสินใจ — categorise, verify, grill, write-up, merge",
        "when_to_use": "มี issue/PR ค้างเยอะ, อยากไล่อย่างเป็นระบบไม่ปล่อยค้าง",
        "examples": [
            {"scenario": "PR ค้าง 20 รายการ", "how": "/triage แยกหมวด → verify → grill → ตัดสินใจ"},
        ],
        "process_steps": ["categorise", "verify repro", "grill design", "write-up", "merge/close"],
    },
    "to-issues": {
        "invocation": "manual",
        "th_description": "แตก plan/spec/PRD เป็น issue แบบ tracer-bullet slice — แต่ละ issue ทำได้ทีละอันอิสระ",
        "when_to_use": "มีแผนใหญ่ ต้องการแบ่งเป็น issue ที่คว้าทำได้ทันที",
        "examples": [
            {"scenario": "สเปกระบบ login", "how": "/to-issues แตกเป็น issue 5 อัน แต่ละอันครบ vertical slice"},
        ],
    },

    # ── Thai ───────────────────────────────────────────────────────────────
    "thai-translate": {
        "invocation": "manual",
        "th_description": "แปลไทย-อังกฤษ คำศัพท์เทคนิค — รักษา context, ใช้คำเทคนิคที่คนไทยคุ้น",
        "when_to_use": "แปล doc, สื่อสารกับคนไทย, หรือทำ content สองภาษา",
        "examples": [
            {"scenario": "แปล README อังกฤษ", "how": "/thai-translate รักษาคำเทคนิค (deploy, API) แปลที่เหลือ"},
        ],
    },
    "thai-text-processing": {
        "invocation": "manual",
        "th_description": "ตัดคำ/normalize ข้อความไทย — จัดการกับ tokenization ที่ไทยไม่มีวรรคตอน",
        "when_to_use": "ประมวลผล text ไทย, search, หรือ NLP",
        "examples": [
            {"scenario": "สร้าง search ภาษาไทย", "how": "ใช้ word segmentation ก่อน index"},
        ],
    },
    "thai-pdpa": {
        "invocation": "manual",
        "th_description": "ตรวจสอบการปฏิบัติตาม พ.ร.บ. PDPA — การเก็บ/ใช้/เปิดเผยข้อมูลส่วนบุคคล",
        "when_to_use": "แอปเก็บข้อมูล user, หรือต้อง compliance ไทย",
        "examples": [
            {"scenario": "ฟอร์มเก็บ email", "how": "ตรวจ consent, purpose, สิทธิ์ user"},
        ],
    },
    "thai-date-format": {
        "invocation": "manual",
        "th_description": "จัดรูปวันที่แบบไทย (พ.ศ., ปี ค.ศ. → พ.ศ.) — กันสับสน",
        "when_to_use": "แสดงวันที่ให้ user ไทย, หรือออกเอกสาร",
        "examples": [
            {"scenario": "วันที่ 2026-07-13", "how": "แปลงเป็น 13 กรกฎาคม 2569"},
        ],
    },

    # ── Specialized ────────────────────────────────────────────────────────
    "mcp-builder": {
        "invocation": "manual",
        "th_description": "สร้าง MCP server — expose tool/resource ให้ agent เรียกใช้ผ่าน Model Context Protocol",
        "when_to_use": "อยากให้ agent เรียก API/DB/tool ของตัวเองได้",
        "examples": [
            {"scenario": "อยากให้ agent ค้น DB ได้", "how": "/mcp-builder สร้าง MCP server query DB"},
        ],
    },
    "api-design": {
        "invocation": "manual",
        "th_description": "ออกแบบ REST/GraphQL API — endpoint, schema, versioning, error format",
        "when_to_use": "สร้าง API ใหม่, หรือปรับ API เก่า",
        "examples": [
            {"scenario": "API สั่งซื้อ", "how": "ออกแบบ /orders, /orders/{id}, error code"},
        ],
    },
    "frontend-design": {
        "invocation": "manual",
        "th_description": "ออกแบบ UI/UX หน้าเว็บ — layout, color, typography, component",
        "when_to_use": "สร้างหน้าเว็บใหม่, ปรับ design หรือทำ prototype",
        "examples": [
            {"scenario": "หน้า dashboard", "how": "/frontend-design layout + color + chart"},
        ],
    },
    "obsidian": {
        "invocation": "manual",
        "th_description": "จัดการ notes ใน Obsidian — wikilinks, tags, template, graph view",
        "when_to_use": "ใช้ Obsidian เป็น knowledge base ส่วนตัว",
        "examples": [
            {"scenario": "สร้าง note ใหม่", "how": "ใช้ template, tag, ลิงก์ไป note ที่เกี่ยวข้อง"},
        ],
    },
    "agent-architecture-audit": {
        "invocation": "manual",
        "th_description": "ตรวจสอบสถาปัตยกรรมของ agent system — skill ทำงานร่วมกันไหม, มี loop ไหม, ซ้ำซ้อนไหม",
        "when_to_use": "agent system ซับซ้อนแล้ว, อยากปรับ architecture",
        "examples": [
            {"scenario": "มี 50 skills แล้ว", "how": "audit: ซ้ำไหม, conflict ไหม, ขาดอะไร"},
        ],
    },
    "mcp-server-patterns": {
        "invocation": "manual",
        "th_description": "สร้าง MCP server ด้วย Node/TypeScript SDK — tools, resources, prompts, Zod validation, stdio vs streamable HTTP transport",
        "when_to_use": "อยากสร้าง MCP server ใหม่ให้ agent เรียกใช้ tool/resource",
        "examples": [
            {"scenario": "สร้าง MCP server query DB", "how": "/mcp-server-patterns เลือก transport + define tool"},
        ],
        "process_steps": ["เลือก transport", "define tools/resources", "Zod validate", "wire handler", "test stdio"],
    },
    "agent-harness-construction": {
        "invocation": "manual",
        "th_description": "ออกแบบ action space, tool definitions, observation formatting สำหรับ agent harness — ให้ agent ตัดสินใจได้แม่นขึ้น",
        "when_to_use": "สร้างหรือปรับ agent harness, agent ตัดสินใจผิดบ่อย, อยากเพิ่ม success rate",
        "examples": [
            {"scenario": "agent เลือก tool ผิดบ่อย", "how": "/agent-harness-construction ปรับ description + schema"},
        ],
    },
    "agent-introspection-debugging": {
        "invocation": "manual",
        "th_description": "debug agent failure แบบมีโครง — capture, diagnosis, contained recovery, prevention — ไม่ใช่แค่ลองใหม่",
        "when_to_use": "agent ล้มเหลวซ้ำๆ, ไม่รู้ว่าผิดตรงไหน, อยากแก้ที่สาเหตุ",
        "examples": [
            {"scenario": "agent loop ไม่จบ", "how": "/agent-introspection-debugging capture state → diagnose → fix"},
        ],
        "process_steps": ["capture failure", "diagnose root cause", "contained recovery", "prevent regression"],
    },
    "plan-orchestrate": {
        "invocation": "manual",
        "th_description": "อ่าน plan document แตกเป็น step แล้วออกแบบ agent chain ต่อ step จาก catalog — สั่ง execution แบบมีระเบียบ",
        "when_to_use": "มี plan ยาว, ต้องการ orchestrate หลาย skill/agent ตามลำดับ",
        "examples": [
            {"scenario": "deploy หลาย service", "how": "/plan-orchestrate อ่าน plan → แตก chain → execute"},
        ],
        "process_steps": ["อ่าน plan", "decompose steps", "design agent chain", "execute + monitor"],
    },
    "agent-sort": {
        "invocation": "manual",
        "th_description": "เรียง skills/commands/rules/hooks สำหรับ repo หนึ่งๆ เป็น install plan โดยอ้างหลักฐาน — ไม่เดา",
        "when_to_use": "เริ่ม repo ใหม่หรืออยากทำความสะอาด skill catalog ที่ล้น",
        "examples": [
            {"scenario": "repo ใหม่ ไม่รู้จะใส่ skill ไหน", "how": "/agent-sort ได้ลำดับ install พร้อมเหตุผล"},
        ],
    },
    "ag2-goal": {
        "invocation": "manual",
        "th_description": "orchestrate multi-step goal ด้วย AG2 — planner แตกเป้า, free executor รัน, planner ตรวจ",
        "when_to_use": "เป้าซับซ้อนเกิน one-shot, ต้องการ planner+executor แยกบทบาท",
        "examples": [
            {"scenario": "research และสรุป 10 paper", "how": "/ag2-goal planner แตกงาน → executor ทำ → รวม"},
        ],
    },
    "workspace-surface-audit": {
        "invocation": "manual",
        "th_description": "ตรวจ repo, MCP servers, plugins, connectors, env surfaces, harness setup แล้วแนะนำของที่ขาด/เกิน",
        "when_to_use": "repo รกแล้ว อยากรู้ว่ามีอะไรบ้าง และอะไรควรเสีย",
        "examples": [
            {"scenario": "เข้า repo ใหม่", "how": "/workspace-surface-audit สรุป surface ทั้งหมด"},
        ],
    },
    "skill-comply": {
        "invocation": "manual",
        "th_description": "ตรวจว่า skills/rules/agent definitions ถูก follow จริงไหม — สร้าง scenario test อัตโนมัติ",
        "when_to_use": "อยากวัดว่า Iron Law หรือ rule ที่ตั้งไว้ถูกปฏิบัติจริง",
        "examples": [
            {"scenario": "ตั้ง rule 'test ก่อนโค้ด'", "how": "/skill-comply สร้าง scenario ทดสอบการ follow"},
        ],
    },
    "hexagonal-architecture": {
        "invocation": "manual",
        "th_description": "ออกแบบ/ปรับ ports & adapters ให้ domain boundary ชัด — แยก core logic จาก external (DB, API, UI)",
        "when_to_use": "โค้ดเก่าผสม domain กับ infra ไว้ด้วยกัน, test ยาก, swap DB/API ไม่ได้",
        "examples": [
            {"scenario": "จะ swap MySQL เป็น Postgres", "how": "/hexagonal-architecture แยก port ก่อนแก้"},
        ],
        "process_steps": ["identify domain core", "define ports", "isolate adapters", "test domain in isolation"],
    },
    "documentation-lookup": {
        "invocation": "auto",
        "th_description": "ดึง docs ล่าสุดของ lib/framework ผ่าน context7 MCP แทนการใช้ข้อมูลในโมเดล — กันใช้ API เก่า",
        "when_to_use": "ใช้ lib ที่ API เปลี่ยนเร็ว (React, Next.js, FastAPI) หรือเกรงว่าโมเดลจำผิด",
        "examples": [
            {"scenario": "ใช้ Next.js App Router", "how": "auto-load context7 → ดึง official docs ปัจจุบัน"},
        ],
    },
    "browser-testing-with-devtools": {
        "invocation": "manual",
        "th_description": "ใช้ Chrome DevTools MCP ดึงข้อมูล runtime จริง — DOM inspection, console logs, network traces, performance",
        "when_to_use": "debug frontend, ตรวจ layout, วัด performance, หา error ใน console",
        "examples": [
            {"scenario": "หน้าโหลดช้า", "how": "/browser-testing-with-devtools trace network + measure"},
        ],
        "process_steps": ["inspect DOM", "read console", "trace network", "profile performance", "report"],
    },
    "setup-pre-commit": {
        "invocation": "manual",
        "th_description": "ติดตั้ง Husky pre-commit hooks กับ lint-staged (prettier), type check, test — กัน commit โค้ดเสีย",
        "when_to_use": "repo ใหม่, หรืออยากให้ทีม commit สะอาดขึ้นอัตโนมัติ",
        "examples": [
            {"scenario": "ทีม commit โค้ดไม่ format", "how": "/setup-pre-commit ติด Husky + lint-staged"},
        ],
    },
    "symlink-connector": {
        "invocation": "manual",
        "th_description": "linker สากล — symlink skills ของ harness ทุกตัวไปยัง A-Wiki repo, .env ไป Google Drive",
        "when_to_use": "อยากใช้ skill/config ร่วมกันข้าม Claude/Codex/Cline/Hermes/Gemini/ZCode",
        "examples": [
            {"scenario": "เพิ่ม skill ใหม่ใช้ทุก agent", "how": "/symlink-connector ลิงก์ครั้งเดียวครบทุก harness"},
        ],
    },
    "frontend-design-direction": {
        "invocation": "manual",
        "th_description": "ตั้ง design direction เฉพาะของ ECC สำหรับ production UI — เลือก style, color, motion ให้เข้ากับงาน",
        "when_to_use": "เริ่ม production UI ใหม่, อยากให้ design ชัดและสม่ำเสมอ",
        "examples": [
            {"scenario": "ทำ SaaS dashboard", "how": "/frontend-design-direction เลือก direction ก่อนเขียน"},
        ],
    },
    "liquid-glass-design": {
        "invocation": "manual",
        "th_description": "ระบบ design แบบ Liquid Glass ของ iOS 26 — glass material ที่มี blur, reflection, motion โต้ตอบ",
        "when_to_use": "ทำ iOS app, อยากใช้ material ใหม่ของ iOS 26 อย่างถูกวิธี",
        "examples": [
            {"scenario": "ออกแบบ iOS widget", "how": "/liquid-glass-design ใช้ dynamic glass material"},
        ],
    },
    "web-artifacts-builder": {
        "invocation": "manual",
        "th_description": "สร้าง HTML artifact หลาย component บน claude.ai ด้วย modern frontend — ดีไซน์สวย, โต้ตอบได้",
        "when_to_use": "อยากได้หน้า HTML สวยให้ user ดู, หรือ prototype UI ใน artifact",
        "examples": [
            {"scenario": "prototype landing page", "how": "/web-artifacts-builder สร้าง multi-component HTML"},
        ],
    },
    "research": {
        "invocation": "manual",
        "th_description": "สืบค้นคำถามกับแหล่งขั้นต้นที่เชื่อถือได้ แล้วบันทึกผลเป็น markdown — cite, synthesize ไม่เอาจาก memory",
        "when_to_use": "ต้องการคำตอบที่ verify ได้, งานวิจัย, due diligence",
        "examples": [
            {"scenario": "เทรนด์ LLM ปีนี้", "how": "/research สืบจาก primary sources → สรุป cite ครบ"},
        ],
        "process_steps": ["ตั้งคำถาม", "หา primary source", "verify credibility", "synthesize + cite"],
    },

    # ── A-Wiki core commands ──────────────────────────────────────────────
    "a-wiki-commands": {
        "invocation": "manual",
        "th_description": "คำสั่งหลักของ A-Wiki — /today, /lint, /ingest, /search และอื่นๆ",
        "when_to_use": "อยากรู้คำสั่ง A-Wiki ที่มี, หรือหาคำสั่งที่เหมาะกับงาน",
        "examples": [
            {"scenario": "อยาก ingest URL", "how": "/ingest <URL>"},
        ],
    },

    # ── Aliases (alias → canonical mapping) ───────────────────────────────
    # Each alias gets a standalone th_description that points at its canonical
    # skill, so the dashboard shows what each alias is for instead of a blank
    # card. The alias entries stay lightweight — detail lives on the canonical.
    "hipaa-compliance": {
        "invocation": "manual",
        "th_description": "Alias ของ healthcare-phi-compliance — มาตรฐานคุ้มครองข้อมูลสุขภาพ (PHI/HIPAA) สำหรับระบบ medical/healthcare",
        "when_to_use": "ทำระบบ healthcare ที่ต้องจัดการ PHI หรือ comply HIPAA",
        "examples": [
            {"scenario": "เก็บข้อมูลคนไข้", "how": "ดู healthcare-phi-compliance สำหรับแนวทางครบ"},
        ],
    },
    "laravel-verification": {
        "invocation": "manual",
        "th_description": "Alias ของ django-verification — นำ pattern ตรวจสอบ Laravel จาก django-verification มาใช้ (แนวทาง cross-framework เดียวกัน)",
        "when_to_use": "verify งาน Laravel ผ่านแนวทางเดียวกับ django-verification",
        "examples": [
            {"scenario": "ตรวจ Laravel service", "how": "เปิด django-verification แล้ว map ไป Laravel"},
        ],
    },
    "quarkus-verification": {
        "invocation": "manual",
        "th_description": "Alias ของ django-verification — นำ pattern ตรวจสอบ Quarkus จาก django-verification มาใช้",
        "when_to_use": "verify งาน Quarkus ผ่านแนวทางเดียวกับ django-verification",
        "examples": [
            {"scenario": "ตรวจ Quarkus service", "how": "เปิด django-verification แล้ว map ไป Quarkus"},
        ],
    },
    "springboot-verification": {
        "invocation": "manual",
        "th_description": "Alias ของ django-verification — นำ pattern ตรวจสอบ Spring Boot จาก django-verification มาใช้",
        "when_to_use": "verify งาน Spring Boot ผ่านแนวทางเดียวกับ django-verification",
        "examples": [
            {"scenario": "ตรวจ Spring Boot app", "how": "เปิด django-verification แล้ว map ไป Spring"},
        ],
    },
    "token-budget-advisor": {
        "invocation": "manual",
        "th_description": "Alias ของ context-budget — คำนวณและแนะนำ token budget ต่อ task/context เพื่อใช้ model budget อย่างคุ้มค่า",
        "when_to_use": "ทำ multi-step task ที่กลัว token บาน หรือต้องการ budget estimate",
        "examples": [
            {"scenario": "ทำ long ingest", "how": "ดู context-budget ก่อนเริ่ม"},
        ],
    },

    # ── Game / media pipeline ─────────────────────────────────────────────
    "game-phaser-pipeline": {
        "invocation": "manual",
        "th_description": "Pipeline เกมสำหรับโปรเจก game ของ A-Wiki (PWQ) — Phaser + Vite + TypeScript + PixelLab ครบ: route, asset naming/manifest, ขั้นตอน verify, และ safety gate สำหรับ client (visualization-only)",
        "when_to_use": "เริ่ม/ปรับโปรเจก game Phaser ของ A-Wiki หรือเพิ่ม asset/mechanic ใหม่",
        "examples": [
            {"scenario": "เพิ่ม sprite ตัวละครใหม่", "how": "ตั้งชื่อตาม manifest convention → import → verify route"},
            {"scenario": "ตั้ง client ใหม่", "how": "ทำตาม visualization-only safety gate ห้าม signed request/execution"},
        ],
        "process_steps": ["ตั้งชื่อ asset", "อัปเดต manifest", "wire route Phaser", "verify ในเกม", "เช็ค safety gate"],
    },

    # ── Quant / simulation (was missing `invocation` field — fix here) ────
    "monte-carlo-quant-analysis": {
        "invocation": "manual",
        "th_description": "Monte Carlo simulation + synthetic data + quant risk (VaR/CVaR/Sharpe/drawdown/RRR) สำหรับ portfolio/trading PREDICTION — paper/simulation-only ไม่ใช่คำแนะนำการลงทุน",
        "when_to_use": "forecast ผลลัพธ์ผ่าน repeated random sampling, สร้าง synthetic scenarios, คำนวณ risk เป็น distribution",
        "examples": [
            {"scenario": "ประเมิน portfolio VaR", "how": "วิ่ง simulation N ครั้ง → distribution → percentile"},
        ],
    },
}


__all__ = ["THAI_GUIDE"]
