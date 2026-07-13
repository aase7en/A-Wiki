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

    # ── A-Wiki core commands ──────────────────────────────────────────────
    "a-wiki-commands": {
        "invocation": "manual",
        "th_description": "คำสั่งหลักของ A-Wiki — /today, /lint, /ingest, /search และอื่นๆ",
        "when_to_use": "อยากรู้คำสั่ง A-Wiki ที่มี, หรือหาคำสั่งที่เหมาะกับงาน",
        "examples": [
            {"scenario": "อยาก ingest URL", "how": "/ingest <URL>"},
        ],
    },
}


__all__ = ["THAI_GUIDE"]
