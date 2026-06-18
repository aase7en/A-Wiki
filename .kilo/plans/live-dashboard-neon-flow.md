# Plan — A-Wiki Live Dashboard: Deep-Space Neon Flow

> เปลี่ยนวิวหลักของ `scripts/live-dashboard/live-dashboard.html` ให้เป็น **animated pipeline flow chart** (ข้อมูลไหลตามท่อ neon ไปยังแต่ละ model) พร้อม **ข้อความความคิดลอยวาปเข้า-เลือนหาย** ผูกกับ event จริง + ambient และ **animated counter** แบบพรีเมียม สไตล์ deep-space neon AI

**สรุปการตัดสินใจ (ยืนยันกับผู้ใช้แล้ว):**
- สไตล์: **Deep-space neon AI** (พื้นดำลึก + ท่อ neon glow + อนุภาคข้อมูล)
- Flow chart: **แทนที่เป็นวิวหลัก** เก็บ Graph (vis-network) กับ Branching Timeline เป็นวิวสลับรอง
- ข้อความลอย: **ผูก event จริง + ambient** ตอน idle

**ขอบเขต:** แก้ไฟล์เดียว — `scripts/live-dashboard/live-dashboard.html` (frontend เท่านั้น)  
**ไม่ต้องแก้** server.py / API / event schema เพราะข้อมูลที่จำเป็นมาจาก SSE + `/api/graph` + `/api/models` ครบแล้ว

---

## 1. ข้อมูลป้อนเข้าที่ใช้ได้ (ไม่ต้องเพิ่มในฝั่ง server)

| แหล่ง | ใช้ทำอะไร |
|------|----------|
| SSE `delegate_start {model, task}` | เปิดท่อ + ปล่อยอนุภาคไหล origin→model + ข้อความลอย |
| SSE `delegate_done {model, duration_ms}` | ปิดท่อ + อนุภาคกลับ model→origin + thought "done · Xs" |
| SSE `delegate_fail {model, reason}` | ท่อแดงพร่าว + thought "failed" |
| SSE `cost_declare {tier, task}` | ข้อความลอย "tier L4 · task" + อัปเดต tier bar |
| SSE `hook_check {hook, tool, result, tier}` | hook badge + thought เมื่อ block/warn |
| SSE `graph_update {nodes, edges, parallel_count}` | parallel counter + สถานะ agent |
| SSE `session_start` | thought "session started" + pulse origin |
| `/api/models` (GET ตอน boot) | วาง **model stations** เริ่มต้น |
| `/api/capabilities` | capability badge ใน settings (เดิม) |

---

## 2. สถาปัตยกรรมวิวใหม่

### 2.1 Layout (โครงเดิม, เปลี่ยนเนื้อหากลาง)
```
┌─ Header (neon brand · workflow tabs · animated counters · ⚙️ 🗑) ─┐
├─ Glow divider · cost-tier bar (shimmer) ─────────────────────────┤
│ #net-panel (left, flex)              │ #sidebar (event log, เดิม) │
│  ┌─ hook-strip (เดิม) ──────────────┐ │                           │
│  │ view toggle: [🌊 Flow] [🔗 Graph] [🏊 Timeline]                 │
│  │ ============ FLOW (DEFAULT) ============                       │
│  │  #flow-stage (rel)                                              │
│  │   ├─ #flow-bg   (nebula/starfield, เบา)                         │
│  │   ├─ #flow-svg  (ท่อ + อนุภาค + model stations)                 │
│  │   ├─ #flow-html-overlay (origin orb + model chips + counters)   │
│  │   └─ #thoughts-layer (ข้อความลอยวาป-เลือน)                       │
│  │ ============ GRAPH / TIMELINE (เดิม, ซ่อน) ============         │
├─ Glow divider · rec-strip (typed rotator, เดิม) ─────────────────┤
│  Settings slide-over (เดิม, ไม่แตะ)                                │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Flow Chart ส่วนประกอบ

**A. Origin node (ซ้ายกลาง)** — วงโคจร/ลูกแก้วสมอง "Senior Critic"
- Glowing orb + pulse ring เมื่อมีงาน พร้อม `fade-cycle` status (เดิม: watching/validating/delegating)
- เป็นจุดกำเนิดของทุกท่อ

**B. Model stations (ขวา, fan out)** — โหลดจาก `/api/models` บูตครั้งแรก; เพิ่มอันใหม่ทันทีเมื่อเจอ model ใน delegate event (เหมือน `_lanes` ปัจจุบัน)
- แต่ละ station: chip/hexagon กระจกฝ้า + ไอคอน + ชื่อ model + **micro animated counter** (นับ task ที่ทำเสร็จของ model นั้น)
- สถานะ: idle (หรี่) · active (pulse ring + glow) · done-flash (เขียวพร่าว) · fail-flash (แดง)

**C. Pipes (เส้นท่อ SVG)** — เส้นโค้งเชื่อม origin→แต่ละ station
- idle: เส้นบางหรี่ + gradient stroke + glow น้อย
- active: **neon glow สว่าง + animated dash flow** (`stroke-dasharray` + `stroke-dashoffset` rAF) + **อนุภาค** (dot เคลื่อนตาม path ด้วย `getPointAtLength`)
- done: ส่งอนุภาค "return burst" จาก station→origin แล้วค่อย ๆ หรี่

**D. Particle engine (JS, rAF)**
- object pool จำกัด (cap ~40 อนุภาคทั้งระบบ) กัน CPU
- particle = {path, t (0..1), speed, color, size, dir}
- loop เดียวอัปเดตตำแหน่งทุกอนุภาคตาม path แล้ววาดใน SVG
- `delegate_start` → ปล่อยอนุภาคต่อเนื่อง origin→model จนกว่าจะ done/fail
- `delegate_done`/`fail` → หยุดปล่อย + ส่ง burst กลับ

### 2.3 Thoughts layer (ข้อความลอยวาป-เลือน)
- `#thoughts-layer` = div absolute full-overlay เหนือ flow-stage, pointer-events:none
- `spawnThought(text, anchor, {tone, drift})`:
  1. สร้าง element ใกล้ anchor (origin หรือ station หรือจุดสุ่ม)
  2. **warp in**: scale .3→1 + opacity 0→1 + blur→sharp + glow ring (~400ms ease-out)
  3. **hold + drift up** (~1.8–2.6s, translate ย ขึ้นเล็กน้อย)
  4. **fade out** (~700ms) แล้ว remove
- ผูก event: delegate_start/done/fail · cost_declare · hook(block/warn) · session_start
- **Ambient** (idle > 5s): ปล่อยข้อความจาก pool เบา ๆ ที่ตำแหน่งสุ่ม ช้ากว่า เพื่อให้หน้า "มีชีวิต" ตลอด (pool: 'monitoring swarm…','cost-first routing','Iron Laws enforced','free models preferred','senior critic validates')
- cap element (≤ 14 อันบนจอ) กัน congest

---

## 3. การขัดเกลาสไตล์ "Deep-Space Neon" (ทั้งหน้า)

- **`:root` variables**: ปรับ palette deep-space — `--bg-0:#04040c`, เพิ่ม `--neon-cyan`, `--neon-violet`, `--neon-gold` + glow shadow tokens; เก็บ role/model colors เดิม
- **Background**: เลเยอร์ radial-gradient nebula (เคลื่อนช้ามาก) + starfield จาง (CSS หรือ canvas เล็ก ๆ, capping) หลังทุกอย่าง
- **Header**: brand gradient neon เข้มขึ้น, ใส่ subtle scanline/grid overlay, live-pulse เป็น neon dot
- **Animated counters** (header `s-hooks/s-models/s-events/s-par`): ขยาย + ตัวเลข gradient neon + glow นุ่ม + tabular-nums; คงฟังก์ชัน `animateCounter` (cubic ease เดิม) แต่เพิ่ม "tick glow" ตอนนับ
- **Glass cards** (settings): เพิ่ม inner highlight border + glow edge ให้ดูพรีเมียมขึ้น
- **prefers-reduced-motion**: ปิด nebula/particle/thought-warp ทั้งหมด (โชว์สถานะ static) — ขยาย block ที่มีอยู่

---

## 4. การรักษาฟังก์ชันเดิม (ห้ามพัง)

- ✅ SSE connect/retry, event dispatch, hook-strip, event-log sidebar, settings (models/keys/help), cost-tier bar, typed rotator rec-strip — **คงเดิมทั้งหมด**
- ✅ `doClear()` / `doClearLocal()` — เพิ่ม reset flow (หยุดอนุภาค/เคลียร์ thoughts/ทุก station กลับ idle)
- ✅ View toggle — เดิมมี Timeline/Graph → เปลี่ยนเป็น **Flow / Graph / Timeline** (Flow = default)
- ✅ Graph view (vis-network) + Branching Timeline (`_lanes`) — คง logic ไว้ใช้เมื่อสลับวิว
- ✅ ทุก `data-counter` id คงไว้; `bumpCounter()` API ไม่เปลี่ยน
- ✅ Model name resolution (`modelShort`/`modelKey`/`laneColor`) — นำกลับมาใช้กับ stations/particles ด้วย

---

## 5. ขั้นตอนดำเนินงาน (chunks, เอาไว้สรุปส่งมอบ)

1. **chunk(f1): base theme + background** — ปรับ `:root` palette deep-space, เพิ่ม nebula/starfield layer, ขัด header + counters + glass cards
2. **chunk(f2): flow stage skeleton** — โครง `#flow-stage`/`#flow-bg`/`#flow-svg`/overlay/thoughts-layer, view toggle 3 ตัว, โหลด model stations จาก `/api/models`
3. **chunk(f3): pipe + particle engine** — วาดท่อ origin→stations, particle pool rAF, เดินสายเข้ากับ `delegate_start/done/fail`
4. **chunk(f4): thoughts layer** — `spawnThought` (warp-in/drift/fade) ผูกทุก event + ambient idle
5. **chunk(f5): polish + reduced-motion + reset** — ขัด timing/glow, ปิดอนิเมชันตาม `prefers-reduced-motion`, ผูก `doClearLocal` reset flow

---

## 6. การทดสอบ/ตรวจสอบ

ไฟล์เป้าหมายเป็น **single-file static HTML ภาพเคลื่อนไหม** — ไม่มี unit test อัตโนมัติที่เหมาะ (dashboard ปัจจุบันก็ไม่มี test) จึงตรวจด้วย manual/runtime:

1. รัน `python3 scripts/live-dashboard/server.py` (หรือ `bash scripts/dashboard-ensure.sh`) → เปิด `localhost:7790`
2. **โหลดได้ ไม่ error**: เปิด DevTools Console ดูว่าไม่มี JS error; network `/events` SSE เชื่อมได้
3. **จำลอง event** (ทดสอบ animation จริง):
   - `python3 scripts/live-dashboard/event_logger.py delegate_start model=deepseek-v3 task=search`
   - `python3 scripts/live-dashboard/event_logger.py delegate_done model=deepseek-v3 duration_ms=1200`
   - `python3 scripts/live-dashboard/event_logger.py cost_declare tier=L2 task=scan`
   - `python3 scripts/live-dashboard/event_logger.py hook_check hook=check_cost_tier tool=Edit result=pass tier=L2`
   → ดูว่า: ท่อ deepseek สว่าง + อนุภาคไหล → หยุด + burst กลับ · tier bar ขยับ · hook badge ขึ้น · thought วาปเข้า-เลือน
4. **ขนาน**: ยิง `delegate_start` หลาย model พร้อมกัน → เห็นหลายท่อ active + counter parallel ขึ้น
5. **Idle ambient**: รอ >5s ไม่มี event → มีข้อความ ambient ลอย
6. **reduced-motion**: เปิด OS "reduce motion" → หน้า static ไม่มีอนิเมชันหนัก
7. **clear**: กด 🗑 → flow reset, อนุภาค/ท่อ/thoughts หาย
8. **settings/event-log/tier-bar/typed-rotator** ยังทำงานปกติ (regression check)

> หมายเหตุ Iron Law #1: กฎ "test ก่อนโค้ด" มุ่งไปที่โค้ด production logic; สำหรับ single-file HTML ภาพเคลื่อนไหม การตรวจคือ runtime/manual smoke ตามข้างต้น (ความสามารถของสายตาไม่สามารถ assert ใน unit test ได้)

---

## 7. ข้อควรระวัง / ความเสี่ยง

- **Performance**: particle/thought pool ต้อง cap; ใช้ rAF เดียว; หลีกเลี่ยง layout thrash (ใช้ `transform`/`opacity` เท่านั้น)
- **ไม่ใช้ library เพิ่ม**: เก็บ zero-dep + vis-network เดิม (ท่อ/อนุภาค/thoughts เขียน SVG + JS ธรรมดา)
- **ไม่กระทบ privacy**: ข้อความลอยมาจาก event ที่ server ส่งอยู่แล้ว ไม่มีข้อมูลลับใหม่
- **responsive**: flow-stage ต้องทำงานบนจอเล็กด้วย (stations จัด grid/fan ใหม่, อาจลดท่อเป็น list บนมือถือ)
- **ไม่แตะ AGENTS.md/CLAUDE.md** (Iron Law #5) — แก้ HTML เท่านั้น; อัปเดต `wiki/entities/ai-tools/live-dashboard.md` เป็น optional follow-up
