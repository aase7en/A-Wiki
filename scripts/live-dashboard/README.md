# A-Wiki Live Dashboard

Real-time monitor ของ A-Wiki swarm — เห็นว่าใช้ AI ตัวไหน แบ่งงานอะไร อยู่ workflow ไหน
ทำ parallel กี่ model และ hook ตัวไหนทำงาน/บล็อก — แบบ live ผ่าน Server-Sent Events.
รวม **Settings panel** ให้ผู้ใช้เลือก model + ใส่ API key เองได้ และจัดลำดับ model
ตาม **capability** (อ้างอิง leaderboard) โดยยึด cost-first.

## รัน

```bash
python3 scripts/live-dashboard/server.py        # foreground (Ctrl+C หยุด)
```
เปิด `http://localhost:7790/` ใน browser. Port 7790 (แยกจาก render-html-preview 7788).
มี config ใน `.claude/launch.json` ชื่อ `live-dashboard` ด้วย.

## Endpoints

| Endpoint | Method | Purpose |
|----------|:------:|---------|
| `/` | GET | Dashboard HTML |
| `/events` | GET | SSE stream (tails `.tmp/live-events.jsonl`) |
| `/clear` | GET | เคลียร์ event log |
| `/status` | GET | JSON status |
| `/api/models` | GET/POST | อ่าน/บันทึก model config |
| `/api/keys` | GET/POST | สถานะ key (set/unset, **ไม่คืนค่า**) / บันทึก key |
| `/api/capabilities` | GET | capability scorecard + `recommended_by_task` |

> Server เป็น `ThreadingHTTPServer` — SSE stream ที่ค้างยาวจะไม่บล็อก `/api/*` calls.

## Settings panel (⚙️ models)

- **Models tab** — toggle เปิด/ปิดแต่ละ model, แก้ `model_id`, ดู capability badge
  (SWE-bench · Terminal-Bench · NL2Repo · reasoning · speed). กด "บันทึก Models" →
  POST `/api/models` → เขียน `.tmp/model-config.json` (gitignored) → มีผลรอบ delegate ถัดไป.
- **API Keys tab** — ใส่ API key ต่อ provider → POST `/api/keys`. ถ้าไม่ตั้งอะไร →
  ใช้ default config (GLM ปิดไว้จนกว่าจะใส่ key).

## Key storage (binding กับ Iron Law #6)

Key ที่ใส่ผ่าน dashboard เก็บที่:
1. `.tmp/live-dashboard-keys.env` (gitignored — `export KEY="..."`, delegate.sh `source` เอง)
2. `drive/.secrets` (best-effort ถ้า `drive/` mount อยู่ — cloud-synced, ไม่ขึ้น git)

**ไม่เคย** เขียน key ลง repo file หรือ `.claude/settings.local.json`. โดน `.tmp/` gitignored
จึงไม่ trip `check_secret_leak` hook (ไม่ stage). delegate.sh `source` keys file นี้อัตโนมัติ.

## Model config schema (`.tmp/model-config.json`)

```json
{ "models": [
  { "id": "zhipu", "name": "GLM 5.2 (Z.ai)", "enabled": false,
    "provider": "zhipu", "key_env": "ZHIPU_API_KEY",
    "model_id": "glm-4.6",
    "api_url": "https://api.z.ai/api/paas/v4/chat/completions" }
]}
```
`enabled:false` → delegate.sh emit `AWIKI_DISABLE_<ID>=1` → engine ตัวนั้นถูกข้าม.
`model_id` แก้ได้ → delegate.sh export ทับ seed (เช่น `ZHIPU_DIRECT_MODEL=glm-5.2`).

## Capability-based routing

`wiki/context/model-capability-scores.json` = scorecard committed (offline-first floor),
keyed by family + `match` substrings, คะแนน 0-100 ต่อ dimension. `scripts/model-capability-scout.py`
refresh best-effort จาก 3 leaderboard (SWE-bench / Terminal-Bench 2.0 / NL2RepoBench) →
`.tmp/model-capability-cache.json`. delegate.sh `_rank_by_capability()` จัดลำดับ engine
ด้วย sort key `(cost_rank ASC, capability_score DESC)` → **paid ห้ามแซง free**; capability
สลับลำดับเฉพาะภายใน cost class. ดู [[zhipu-glm]] · [[model-capability-bench]].

## เพิ่ม model ใหม่

1. Settings → Models → แก้ `model_id` ของ provider ที่มีอยู่ (gemini/deepseek/openrouter/groq/anthropic/zhipu), หรือ
2. แก้ `DEFAULT_MODEL_CONFIG` ใน `server.py` + เพิ่ม `try_<provider>_direct()` ใน `delegate.sh`
   (clone จาก `try_groq_model` ถ้า OpenAI-compatible) + wire ใน `run_tier()`.

## Troubleshooting

- **Dashboard ว่าง/offline overlay** → server ยังไม่รัน. รัน `python3 scripts/live-dashboard/server.py`.
- **GLM ไม่ทำงาน** → ใส่ ZHIPU_API_KEY (Settings → API Keys) + เปิด toggle GLM + Save.
  ตรวจ endpoint Z.ai สากล `api.z.ai` (ไม่ใช่ `bigmodel.cn` ของ mainland).
- **capability ไม่อัปเดต** → `python3 scripts/model-capability-scout.py` (best-effort; ถ้า leaderboard
  parse ไม่ได้จะคง committed score). `--offline` = ใช้ committed อย่างเดียว.
