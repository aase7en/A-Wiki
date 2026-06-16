# Plan — Cost-First Routing สำหรับ GLM 5.2 + DeepSeek (ดีกว่าคำแนะนำที่ hardcode)

> ตอบคำถาม: ข้อมูลที่ user เอามาน่าเชื่อถือไหม? + ออกแบบระบบให้ "ดีกว่า" ผ่าน Cost-First Pyramid + A-Wiki parallel agent ได้ไหม?
> ขอบเขต (ตามที่ user เลือก): **เดินสายเข้า A-Wiki จริง** + **เปิด Z.AI direct + ใส่ key** + **scout ดึง live benchmark + fallback**.

---

## 0. TL;DR — คำตอบสั้น

- **ความน่าเชื่อถือ: ครึ่งจริง ครึ่งโม้ และส่วนหนึ่งละเมิดกฎ A-Wiki เอง**
  - จริง: GLM 5.2 + Z.AI Codeplan (คุณกำลังคุยกับ `zai-coding-plan/glm-5.2` อยู่ตอนนี้), DeepSeek ถูก, หลัก "ส่ง agent loop ไปโมเดลเหมา" ถูก
  - โม้/ยืนยันไม่ได้: "DeepSeek v4 หลอม Chat+Reasoner", "แชมป์ LiveCodeBench 2026 Hard", "SWE-bench Verified จี้ค่ายปิด" — ไม่มีตัวเลขประกอบ; intel ของ A-Wiki (as_of 2026-06-15) ยังระบุ DeepSeek = V3/R1, swe_bench 50 / terminal_bench 38 (mark `[training]`) ไม่ใช่แชมป์
  - ละเมิดกฎ: คำแนะนำ "ล็อก glm-5.2 ตลอด + hardcode `deepseek-v4` ใน kilo.jsonc" ขัด `AGENTS.md` ("NEVER hardcode model names as policy") + `model-scouter.md` ("Never hardcode model names. Always scout dynamically")
- **ทำได้ไหม / ดีกว่าไหม: ได้ และ A-Wiki มีระบบที่ดีกว่าอยู่แล้ว** — คำแนะนำที่เอามาคือ "เวอร์ชันทำมือ" ของสิ่งที่ Cost-First Pyramid + universal routing + scout + capability scorecard + swarm ทำอัตโนมัติ แผนนี้เชื่อม GLM/DeepSeek เข้าระบบนั้น
- **Insight สำคัญ (แยก 2 เลเยอร์ เพื่อไม่สับสนเรื่อง "ละเมิดกฎ"):**
  - **เลเยอร์ 1 — Interactive surface (Kilo Code ตัวมันเอง = ผม):** การชี้ model ของ editor ไปที่ GLM 5.2 (codeplan ที่จ่ายแล้ว) = ถูกต้องเรื่อง cost (marginal cost 0) ไม่ใช่การ hardcode policy → ทำได้ ไม่ผิดกฎ
  - **เลเยอร์ 2 — Routing/harness policy (swarm, cost-routing.conf, delegate.sh):** ต้อง dynamic + cost-first ห้าม hardcode ชื่อรุ่น → นี่คือสิ่งที่แผนจะเดินสาย

---

## 1. วินิจฉัยความน่าเชื่อถือของข้อมูลที่ user เอามา

| ข้อความในคำแนะนำ | คำตัดสิน | เหตุผล / หลักฐาน |
|---|---|---|
| GLM 5.2 + Z.AI Codeplan $16/เดือน | ✅ จริง | system prompt ระบุ model = `zai-coding-plan/glm-5.2`; providers.json มีค่าย `zai` |
| DeepSeek ถูก + เหมาะ debug | ✅ จริง | cost-routing.conf tier_1 seed = deepseek-chat; providers.json `enabled:true` |
| "DeepSeek v4 หลอม Chat+Reasoner, สลับโหมดคิดในใจอัตโนมัติ" | ⚠️ ยืนยันไม่ได้ | intel A-Wiki ยังเป็น V3/R1 (`deepseek-chat`/`deepseek-reasoner` แยก); ไม่มี v4 ใน providers/scorecard |
| "แชมป์ LiveCodeBench 2026 Hard Tasks" | ⚠️ โม้ | ไม่ให้ตัวเลข; LiveCodeBench เป็น benchmark จริงแต่ "แชมป์" ไม่มี source |
| "SWE-bench Verified จี้ค่ายปิดชั้นนำ" | ❌ ขัดข้อมูลในมือ | scorecard (as_of 2026-06-15): DeepSeek swe_bench=50, terminal_bench=38 — ไม่ใช่ท็อป (mark `[training]` ทั้งคู่ แปลว่ายังไม่ verify) |
| GLM 5.2 "แชมป์ Agentic / Long-Horizon" | ⚠️ โม้ | scorecard: GLM terminal_bench=50, swe_bench=68, reasoning=80 — ดีแต่ไม่ใช่ "แชมป์" และ mark `[training]` |
| baseURL `https://api.z.ai/api/coding/paas/v4` | ⚠️ น่าสงสัย | providers.json + zhipu-glm entity ระบุ endpoint = `https://api.z.ai/api/paas/v4/chat/completions` (เป็น `paas/v4` ไม่มี segment `coding`) — ต้อง verify กับ dashboard จริงก่อนใช้ |
| "ล็อก glm-5.2 ตลอด + hardcode `deepseek-v4` ใน kilo.jsonc" | ❌ ละเมิดกฎ | `AGENTS.md`/`model-switching.md`/`model-scouter.md`: ห้าม hardcode model เป็น policy; ต้อง scout dynamic |
| "Agent ติดหล่ม → สลับไปถาม DeepSeek เอาไอเดีย → สั่ง GLM แก้" | 🔁 แนวคิดถูก แต่ควรเป็น protocol | = Architect(GLM/DeepSeek reason) + Executioner(GLM แก้ไฟล์) ของ swarm; ควรเป็น escalation trigger ไม่ใช่นิสัย manual |

**บทสรุปวินิจฉัย:** setup พื้นฐานใช้ได้ แต่ benchmark claims เป็นการตลาดไม่มีตัวเลข และวิธี "lock + hardcode" สวนทางกับปรัชญา A-Wiki ที่ user ทำระบบไว้แล้ว

---

## 2. การออกแบบที่ "ดีกว่า" (แมปคำแนะนำ naive → ระบบ A-Wiki ที่มี)

| คำแนะนำ naive (ที่ user เอามา) | ระบบ A-Wiki ที่ดีกว่า (ที่จะเดินสาย) | ไฟล์ |
|---|---|---|
| ล็อก GLM 5.2 ใน kilo.jsonc สำหรับ agent loop | **Interactive layer**: ชี้ editor → GLM 5.2 (codeplan) ถูกแล้ว (cost 0); **Routing layer**: GLM เข้า roster เป็น paid-direct ใน cost class ของมัน ไม่แซง free | providers.json, model-roster.conf |
| ใช้ DeepSeek นัดเดียวจอด debug | DeepSeek = cheap-capable paid direct (tier 1 seed) ใน harness; เรียกผ่าน delegate.sh ตาม cost-first | delegate.sh, cost-routing.conf |
| "ติดหล่ม → สลับ DeepSeek เอาไอเดีย" | **Escalation protocol**: 2 รอบ root-cause fail → trigger 4c architect (DeepSeek/GLM reason) → คืน 4b execute (GLM แก้) — เป็น trigger ไม่ใช่นิสัย | docs/protocols/model-switching.md + protocol ใหม่ |
| (ไม่มี) | **Capability scorecard** ดึง live benchmark → rank `(cost_rank, capability)` แบบ paid ไม่แซง free | model-capability-scout.py, model-capability-scores.json |
| (ไม่มี) | **Scout dynamic pricing/availability** ก่อน route เสมอ (anti-stale-model) | model-scout-current.py, cost-routing.conf |
| (ไม่มี) | **Senior Critic = primary agent** validate ทุก output (Iron Law #3) — ไม่มีในคำแนะนำเลย | agile-swarm.md |

หลักการสำคัญที่ทำให้ "ดีกว่า": **cost-first เป็น primary key, capability เป็น secondary** → paid (GLM/DeepSeek) ห้ามแซง free (Gemini/OpenRouter free) ทางคณิตศาสตร์; capability สลับลำดับเฉพาะภายใน cost class เดียวกัน

---

## 3. แผนImplementation (3 track ตามที่ user เลือก)

### Track A — เปิด Z.AI direct + ใส่ key (เลเยอร์ routing/harness)

**เป้า:** GLM วิ่ง direct (coding-plan pricing) ใน swarm แทนผ่าน OpenRouter markup

**ขั้นตอน:**
1. **Reconcile env name inconsistency** ⚠️ (พบระหว่างสำรวจ): providers.json + add-provider.py ใช้ `ZAI_API_KEY` แต่ zhipu-glm entity + delegate.sh env (`ZHIPU_DIRECT_MODEL`, `AWIKI_DISABLE_ZHIPU`) ใช้ `ZHIPU_*` → เลือกชื่อเดียว (แนะ `ZAI_API_KEY` เพราะ providers.json เป็น source of truth และ add-provider.py default) แล้ว alias อีกฝั่ง ก่อนเดินต่อ
2. รัน `python scripts/add-provider.py --provider zai --env-name ZAI_API_KEY --dry-run` ดู preview
3. ใส่ key: `python scripts/add-provider.py --provider zai --env-name ZAI_API_KEY --key-stdin --enable` (key ลง `drive/.secrets` เท่านั้น, repo เก็บแค่ env var name — public-safe, Iron Law #6)
4. ตั้ง `default_model` = `glm-4.6` (confirmed flagship) หรือ `glm-5.2` ถ้า dashboard ยืนยัน model id จริง — **verify id จาก `/models` endpoint ก่อน** (คำแนะนำที่ user เอามาใช้ `glm-5.2` แต่ providers/entity ยังเขียน `glm-4.6`; system prompt ระบุ `glm-5.2` จึงน่าจะจริง แต่ต้อง probe `/models` ยืนยัน string ที่ Z.AI รับ)
5. รีเฟรช catalog: `python scripts/model-scout-current.py --catalog` → GLM ขึ้นเป็น primary (flagship) ของค่าย zai
6. pin roster: `python scripts/apply-model-selection.py` (GLM → TIER2/3_PRIMARY เพราะ paid; free ยังนำหน้า)
7. ตรวจ: `python scripts/batch/route.py --estimate --limit 10` ดูว่า GLM direct ถูกกว่าเส้นทาง OpenRouter จริง

**ไฟล์ที่กระทบ:** `wiki/context/providers.json` (metadata only), `drive/.secrets` (key), `.tmp/model-catalog.json`, `wiki/context/model-roster.conf`

### Track B — รีเฟรช benchmark scorecard (live parser + fallback)

**เป้า:** แทนค่า `[training]`/`[low]` ของ GLM/DeepSeek ด้วยคะแนนจริงจาก leaderboard สาธารณะ

**ข้อจำกัดที่ต้องเขียนตรงไปตรงมา (ยืนยันแล้ว):** ไม่มี leaderboard coding ตัวไหนมี JSON feed แบบ GET ตรง ๆ — `aider.chat/assets/leaderboard.json` = 404; swebench.com เป็น rendered page (มีปุ่ม JSON ใน UI แต่ไม่ใช่ API); tbench.ai เหมือนกัน. ดังนั้น "live" จริง = **dedicated parser** ดึงจากแหล่ง machine-readable แล้ว fallback ค่า committed (เป็น pattern เดิมของ scout อยู่แล้ว — `model-capability-scout.py` เขียนไว้ชัดว่าหน้า rendered "unparseable")

**ขั้นตอน:**
1. **สำรวจแหล่ง machine-readable จริง** (ก่อนเขียน parser): probe ดูว่าอันไหน parse ได้ —
   - SWE-bench: ดู XHR endpoint ที่ปุ่ม "JSON" ใน UI เรียก (น่าจะมี), หรือ HuggingFace dataset `princeton-nlp/SWE-bench_Verified` results
   - Aider Polyglot: raw markdown ใน `github.com/Aider-AI/aider` หรือ `aider.chat/docs/leaderboards/` (HTML table parse ได้)
   - LiveCodeBench: leaderboard repo/JSON
   - Terminal-Bench 2.0: ดูว่ามี raw ใน repo ไหม
2. เพิ่ม source ที่ parse ได้จริงเข้า `SOURCES` ใน `model-capability-scout.py` (dimension mapping: ดู §4)
3. เขียนคะแนนจริงกลับลง `model-capability-scores.json` พร้อม `confidence: "[verified YYYY-MM-DD]"` + `source_urls` + `as_of` (สไตล์ wiki — honest confidence markers)
4. รัน `python scripts/model-capability-scout.py` → `.tmp/model-capability-cache.json` ต้องไม่ crash เมื่อ source fail (offline-first degrade เดิม)
5. อัปเดต `wiki/entities/ai-tools/model-capability-bench.md` แหล่ง leaderboard ตาราง (เพิ่ม Aider Polyglot / LiveCodeBench)

**ไฟล์ที่กระทบ:** `scripts/model-capability-scout.py`, `wiki/context/model-capability-scores.json`, `wiki/entities/ai-tools/model-capability-bench.md`

### Track C — Escalation protocol (แทนนิสัย manual "ติดหล่ม → สลับ DeepSeek")

**เป้า:** เปลี่ยนคำแนะนำ "manual switch" ให้เป็น trigger protocol ที่ทำซ้ำได้ + ตรวจได้

**ขั้นตอน:**
1. เพิ่ม section "Agent-Stuck Escalation" ใน `docs/protocols/model-switching.md`:
   - **Trigger:** Executioner (GLM 4b) แก้บั๊กเดิมซ้ำ 2 รอบ ไม่ผ่าน test → escalate
   - **ขั้น 1 (4c Architect, low/medium):** ขอ root-cause + ทิศทางจาก cheap-capable reasoning route (DeepSeek reasoner หรือ GLM reason ตามที่ scout บอกถูกกว่าในขณะนั้น — **ไม่ hardcode**)
   - **ขั้น 2:** เอา spec/root-cause กลับมาให้ Executioner (4b) แก้ไฟล์ พร้อม failing test (Iron Law #1)
   - **ขั้น 3 (ถ้ายัง):** ขึ้น 4c primary agent (ผม) one-shot architecture → ลดกลับ 4b ทันที
   - **Senior Critic validate** ทุก output (Iron Law #3) — ไม่มีในคำแนะนำเดิม
2. เพิ่ม trigger นี้เข้า `Handoff Note Template` ของ protocol (`escalation_used` field) เพื่อ cross-agent/cross-IDE continuity
3. (optional, หากคุ้ม) เพิ่ม detection: นับ "same-file edit + test ยัง fail" รอบที่ 2 → dashboard event `escalation_suggested` — เป็น hint ไม่ใช่ auto-swap (กัน surprising action)

**ไฟล์ที่กระทบ:** `docs/protocols/model-switching.md` (+ optional `scripts/live-dashboard/server.py`)

---

## 4. Benchmark reference — ที่นิยมวัด + map → task

| Benchmark | URL | วัดอะไร | map → A-Wiki task/dimension |
|---|---|---|---|
| **SWE-bench Verified** | swebench.com | แก้ GitHub issue จริง 500 ข้อ (coding agent) | `swe_bench` → task `code` (gold standard) |
| **Terminal-Bench 2.0** | tbench.ai | agentic / terminal task | `terminal_bench` → task `scan` |
| **Aider Polyglot** | aider.chat/docs/leaderboards | edit/refactor หลายภาษา | (เพิ่มใหม่) → task `code` เสริม swe_bench |
| **LiveCodeBench** | livecodebench.github.io | competitive programming + contamination control | (เพิ่มใหม่) → reasoning + code |
| **NL2RepoBench** | github.com/multimodal-art-projection/NL2RepoBench | NL → repo-scale code | `nl2repobench` → task `repo` |
| reasoning / speed | (สังเคราะห์) | เหตุผลทั่วไป / latency | `reasoning`/`speed` (infer, ไม่ใช่ leaderboard) |

A-Wiki ติดตามอยู่ 3 ตัว (SWE-bench, Terminal-Bench, NL2RepoBench); **แผนเพิ่ม Aider Polyglot + LiveCodeBench** เพราะเป็น 2 ตัวที่คำแนะนำอ้าง และเป็น benchmark ยอดนิยมจริง

หมายเหตุความซื่อสัตย์: HumanEval/MBPP saturated แล้ว (คะแนนเกือบ 100 ทุกรุ่น) จึงไม่คุ้ม track; ARC-AGI/GPQA เป็น reasoning ทั่วไปไม่ใช่ coding — ไม่เพิ่ม

---

## 5. Verification

```bash
# A — provider ใช้ได้ + ราคา direct ถูกกว่า
python scripts/add-provider.py --provider zai --env-name ZAI_API_KEY --dry-run
python scripts/model-scout-current.py --catalog
python scripts/batch/route.py --estimate --limit 10

# B — scout ไม่ crash + score อัปเดต + honest confidence
python scripts/model-capability-scout.py        # best-effort
python scripts/model-capability-scout.py --offline   # committed only, ต้องไม่ fail

# C — protocol trigger ตอบได้ใน probe
bash scripts/verify-model-routing.sh            # CLI platforms ตอบ scout-first + 4a/4b/4c + no hardcode

# กากี่บาน่า overall
python scripts/gen-index.py --check             # wiki structure
python scripts/agent-preflight.py               # safety
```

เกณฑ์ผ่าน: GLM direct ขึ้น roster ใน cost class ที่ถูกต้อง (ไม่แซง free), scorecard มี `[verified YYYY-MM-DD]` อย่างน้อย GLM+DeepSeek, verify-model-routing.sh ผ่าน 2/3 CLI

---

## 6. ไฟล์ที่จะแตะ + ประตูกฎ

**ไฟล์:**
- `wiki/context/providers.json` (metadata อย่างเดียว — public-safe)
- `drive/.secrets` (key value — gitignored)
- `wiki/context/model-roster.conf` + `.tmp/model-catalog.json` (generated)
- `scripts/model-capability-scout.py` (+ SOURCES)
- `wiki/context/model-capability-scores.json` (ค่าจริง + confidence)
- `wiki/entities/ai-tools/model-capability-bench.md` (ตาราง leaderboard)
- `docs/protocols/model-switching.md` (escalation section + handoff template)
- (optional) `scripts/live-dashboard/server.py` (escalation event)

**ประตูกฎที่เกี่ยว:**
- **Iron Law #5** (ห้ามแก้ AGENTS.md/CLAUDE.md โดยไม่ได้รับอนุญาต): แผนนี้ **ไม่แตะ** สองไฟล์นั้น ✅
- **Iron Law #6** (source-of-truth / external-editor): ไม่เกี่ยว
- **Brain Improvement Gate**: ผ่าน — clear gain (scorecard จริง + cost ถูกลง + protocol ทำซ้ำได้), lightweight (config+script+doc ไม่ใช่ heavy always-loaded context), cost-first (ทั้งแผน), cross-platform (key ใน drive/.secrets, env name ใน repo), public-safe (add-provider.py บังคับ)
- **Universal Routing contract**: ไม่ hardcode model ใน policy; "lock GLM 5.2" เฉพาะ interactive surface ของ editor (Level 4 platform-primary) ไม่ใช่ใน cost-routing.conf ✅

**หมายเหตุ kilo.jsonc:** คำแนะนำเดิมให้แก้ kilo.jsonc hardcode `deepseek-v4` — **แนะนำไม่ทำตาม**; ถ้าจะลงทะเบียน provider DeepSeek ใน Kilo Code ให้ใช้ model id จริงที่ `/models` คืน (น่าจะ `deepseek-chat`/`deepseek-reasoner` ไม่ใช่ `deepseek-v4`) และถือว่าเป็นแค่ surface picker ไม่ใช่ policy

---

## 7. ความเสี่ยง / คำถามที่ยังเปิด

- **model id `glm-5.2` vs `glm-4.6`:** system prompt บอก `glm-5.2` (น่าเชื่อ) แต่ providers/entity ยังเขียน `glm-4.6` → ต้อง probe `GET /models` ของ Z.AI ยืนยันก่อนใส่ default_model (กัน 404)
- **endpoint `coding/paas/v4` vs `paas/v4`:** คำแนะนำเอามาใช้ segment `coding` ที่ไม่ตรงกับ providers.json → verify จาก dashboard/เอกสาร Z.AI จริงก่อน
- **env name `ZAI_API_KEY` vs `ZHIPU_API_KEY`:** inconsistency ใน repo ต้อง reconcile ก่อน Track A (ไม่งั้น delegate.sh จะหา key ไม่เจอ)
- **Live parser อาจ parse ไม่ได้ทุก source:** ยอมรับได้ — offline-first fallback เป็นหัวใจของระบบอยู่แล้ว; อย่าโกหกว่า "live ได้หมด"
- **ไม่ auto-swap model เมื่อ escalation:** ต้องเป็น hint/protocol ไม่ใช่ surprising action (Proactiveness balance)
