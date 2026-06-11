---
type: concept
tags: [claude-code, openrouter, llm-routing, cost-optimization, free-models, ai-tools]
sources: []
created: 2026-04-26
updated: 2026-04-26
---

# OpenRouter + Claude Code — ใช้ free models เป็นเครื่องยนต์

> **TL;DR:** Claude Code = "หน้ากาก" (terminal UI + tool integration) เปลี่ยนเครื่องยนต์ผ่าน 3 env var (`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL`) ชี้ไป OpenRouter ใช้ Qwen/Gemini/Llama ฟรีได้ — ใช้คู่กับ Claude จริงสำหรับงานซับซ้อน

---

## Scope
หน้านี้เป็นคู่มือเฉพาะสำหรับการใช้ Claude Code ผ่าน OpenRouter เท่านั้น ไม่ได้เป็น overview ของ OpenRouter API โดยรวม. ถ้าต้องการภาพรวม OpenRouter gateway ให้ดู [[concepts/ai-tools/openrouter-api]].

## หลักการ

Claude Code (CLI tool ของ Anthropic) คุยกับ model ผ่าน **Anthropic Messages API format**
ปกติ → ส่งไป `api.anthropic.com` → ใช้ Claude Sonnet/Opus → จ่ายค่า API

Trick: ตั้ง 3 environment variables เปลี่ยนปลายทางเป็น OpenRouter (ที่ proxy เป็น Anthropic format) → ใช้ model อื่นได้

```
┌──────────────────┐    Anthropic format     ┌─────────────────┐
│  Claude Code CLI │ ─────────────────────→  │   OpenRouter    │
│  (UI + tools)    │  (set BASE_URL ใหม่)    │   Gateway       │
└──────────────────┘                          └────────┬────────┘
                                                       │
                              ┌────────────────────────┼────────────────────┐
                              ▼                        ▼                    ▼
                       Qwen Coder 480B         Gemini 2.0 Flash       Llama 3.3 70B
                       (เก่ง code)             (เร็ว, Thai ดี)        (general)
                       ฟรี 200 req/วัน        ฟรี                    ฟรี
```

---

## เมื่อไหร่ใช้ free / เมื่อไหร่ใช้ Claude จริง

| งาน | Qwen Coder | Gemini Flash | Llama 70B | Claude Sonnet/Opus |
|-----|-----------|--------------|-----------|----------------------|
| ค้น/อ่าน wiki, ตอบทั่วไป | ✅ | ✅ | ✅ | ⭐ |
| แก้ syntax/typo | ✅ | ✅ | ✅ | ⭐ |
| Ingest source ขนาดกลาง | 🟡 | 🟡 | 🟡 | ✅ |
| Refactor หลายไฟล์ตามกฎ CLAUDE.md | 🟠 | 🟠 | 🟠 | ⭐ |
| Debug ปัญหาซับซ้อน | ❌ | ❌ | 🟠 | ⭐ |
| Architecture / synthesis | ❌ | 🟠 | 🟠 | ⭐ |

> ตัวอย่างจากประสบการณ์: งาน Phase 2 ของ wiki (debug git corruption + relocate .git) — ต้อง Claude จริง free models น่าจะพลาด

---

## OpenRouter Free Limit

| รายการ | Limit |
|-------|-------|
| Requests / นาที | 20 req/min |
| Requests / วัน | 200 req/day |
| Reset | Daily (UTC midnight) |
| ถ้าเกิน | HTTP 429 error → รอจนกว่าจะ reset |

> Session แบบ refactoring 80+ tool calls = ใกล้เต็ม limit ใน 1 session
> ถ้าใช้บ่อย เติม credit $5 = แทบไม่หมด (~5,000 requests with paid models)

---

## Setup ครั้งเดียว

### 1. ติดตั้ง prerequisites
```bash
# ติดตั้ง nvm (ถ้ายังไม่มี — กัน permission error)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# ปิด terminal เปิดใหม่ แล้ว:
nvm install --lts

# ติดตั้ง Claude Code CLI
npm install -g @anthropic-ai/claude-code
```

### 2. สมัคร OpenRouter + เก็บ key ปลอดภัย
1. https://openrouter.ai → Sign up → Keys → Create Key
2. **เก็บ key ใน file แยก** (ห้ามใส่ใน `.zshrc` ตรงๆ ป้องกัน leak):
```bash
echo 'OPENROUTER_API_KEY=your-openrouter-key' > ~/.openrouter-key
chmod 600 ~/.openrouter-key   # เฉพาะเจ้าของอ่านได้
```

### 3. ตั้ง functions ใน `~/.zshrc`
```bash
# Load API key from secure file
export OPENROUTER_API_KEY="$(cat ~/.openrouter-key 2>/dev/null)"

# Wiki paths
WIKI_DRIVE="$HOME/Library/CloudStorage/GoogleDrive-<account>/My Drive/A-Wiki-Data"
WIKI_CLEAN="$HOME/Code/wiki-clean"

# Multi-model launchers
claude-qwen() {
  ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1" \
  ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY" \
  ANTHROPIC_MODEL="qwen/qwen3-coder:free" \
  claude "$@"
}

claude-gemini() {
  ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1" \
  ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY" \
  ANTHROPIC_MODEL="google/gemini-2.0-flash-exp:free" \
  claude "$@"
}

claude-router() {
  # Auto-select free model — กัน hardcode model deprecated
  ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1" \
  ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY" \
  ANTHROPIC_MODEL="openrouter/free" \
  claude "$@"
}

claude-or() {
  # ad-hoc: claude-or <model-id> [args]
  local model="$1"; shift
  ANTHROPIC_BASE_URL="https://openrouter.ai/api/v1" \
  ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY" \
  ANTHROPIC_MODEL="$model" \
  claude "$@"
}

claude-list-free() {
  curl -s 'https://openrouter.ai/api/v1/models' | python3 -c "
import json, sys
data = json.load(sys.stdin)
free = [m for m in data['data']
        if str(m.get('pricing', {}).get('prompt', '0')) == '0'
        and 'tools' in (m.get('supported_parameters') or [])]
for m in sorted(free, key=lambda x: -x.get('context_length', 0))[:20]:
    print(f\"{m['id']:50} ctx={m.get('context_length',0):>7,}  {m.get('name','')[:40]}\")
"
}

claude-real() {
  unset ANTHROPIC_BASE_URL ANTHROPIC_AUTH_TOKEN ANTHROPIC_MODEL
  claude "$@"
}

# Wiki shortcuts (cd + launch)
wiki-qwen()   { cd "$WIKI_CLEAN" && claude-qwen "$@"; }
wiki-router() { cd "$WIKI_CLEAN" && claude-router "$@"; }
wiki-real()   { cd "$WIKI_CLEAN" && claude-real "$@"; }
```

> ใช้ **functions** ไม่ใช่ aliases — เพราะ aliases ถ้าใส่ env var แล้วเว้นบรรทัดจะ broken (env var ไม่ propagate ไปคำสั่งถัดไป)

### 4. Apply
```bash
source ~/.zshrc
```

---

## ใช้งาน

| Command | ทำอะไร |
|---------|--------|
| `claude-smart "<task>"` | 🎯 **Smart launcher** — ประเมิน task ก่อนเลือก model ให้ (qwen/router/real) |
| `claude-qwen` | เปิด Claude Code (engine: Qwen Coder ฟรี) ใน CWD ปัจจุบัน |
| `claude-router` | OpenRouter auto-select free model (กัน model deprecated) |
| `claude-or <model>` | ad-hoc — เลือก model เองครั้งเดียว (e.g. `claude-or qwen/qwen3-coder:free`) |
| `claude-list-free` | ดึง list **ปัจจุบัน** ของ free models ที่ support tools |
| `claude-real` | เปิด Claude Code (Anthropic Claude จริง — จ่ายเงิน) |
| `wiki-smart "<task>"` | smart launcher ใน `~/Code/wiki-clean` ⭐ |
| `wiki-qwen` / `wiki-router` / `wiki-real` | shortcuts cd + launch ที่ wiki-clean |

> ⚠️ **`claude-gemini` deprecated** — `google/gemini-2.0-flash-exp:free` ถูกปิด Feb 2026 ใช้ `claude-router` แทน

---

## 🤖 Auto-routing — ถามง่ายฟรี ถามยากเสียเงิน

### ความจริง: Claude Code lock 1 model ต่อ session
เปลี่ยน model **กลางคันไม่ได้** — แต่เลือก model ตอนเปิดได้

### 3 ระดับของ auto-routing

| Level | ทำได้แค่ไหน | Setup |
|-------|-----------|-------|
| 🟢 **1. Smart launcher** (`claude-smart`) | classify task ก่อน launch (rule-based, no API call) | ผมตั้งให้แล้ว |
| 🟡 **2. Multi-tab manual** | เปิด 2-3 terminals แต่ละตัวใช้ model ต่างกัน | เปิด tab เพิ่ม |
| 🔴 **3. LiteLLM proxy** | switch ทุก request mid-session | ติดตั้ง daemon (ดูล่าง) |

### Level 1: `claude-smart` — Rule-based classifier

```bash
$ claude-smart "DHT11 คืออะไร"
🎯 แนะนำ: qwen  (keyword: simple query)
    1) qwen      — Qwen Coder ฟรี
    2) router    — OpenRouter auto-pick
    3) real      — Claude Sonnet/Opus จริง
เลือก (Enter=qwen, 1/2/3): _
```

**กฎการประเมิน:**
| ตรวจอะไร | ผลลัพธ์ |
|---------|--------|
| มี keyword `phase / refactor / architecture / debug / ออกแบบ / วิเคราะห์ / แก้ปัญหา / fix bug` | → **real** |
| Task ยาว > 200 chars | → **real** |
| มี keyword `คืออะไร / อธิบาย / ดูหน่อย / ค้น / what is / show / list / แสดง` | → **qwen** |
| Task สั้น < 30 chars | → **qwen** |
| อื่นๆ | → **router** (auto-pick free) |

User เลือก override ได้ตลอด (กด 1/2/3) — ใช้กฎเป็นค่าแนะนำ

### Level 3: LiteLLM proxy (advanced)

ถ้าต้องการ **switch ทุก request** mid-session:
```bash
pip install 'litellm[proxy]'

cat > ~/litellm_config.yaml <<EOF
model_list:
  - model_name: smart
    litellm_params:
      model: openrouter/qwen/qwen3-coder:free
      max_tokens: 1000
  - model_name: smart-fallback
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
EOF

litellm --config ~/litellm_config.yaml --port 4000 &
export ANTHROPIC_BASE_URL=http://localhost:4000
claude
```

LiteLLM router rules: https://docs.litellm.ai/docs/routing
- routing by tokens, fallback, prompt classification (with custom Python)
- **ข้อเสีย**: ต้อง daemon ตลอด, debug ยาก, latency เพิ่มเล็กน้อย

> สำหรับ user ทั่วไป **Level 1 (claude-smart) เพียงพอ** — Level 3 เหมาะ enterprise/heavy users

---

## ทำงานข้ามแพลตฟอร์ม

### macOS — ใช้ functions ใน `~/.zshrc` (ตามด้านบน)

### Windows PowerShell
```powershell
# $PROFILE
$env:OPENROUTER_API_KEY = Get-Content "$HOME\.openrouter-key" -ErrorAction SilentlyContinue

function claude-qwen {
  $env:ANTHROPIC_BASE_URL = "https://openrouter.ai/api/v1"
  $env:ANTHROPIC_AUTH_TOKEN = $env:OPENROUTER_API_KEY
  $env:ANTHROPIC_MODEL = "qwen/qwen3-coder:free"
  claude $args
}

function claude-real {
  Remove-Item Env:ANTHROPIC_BASE_URL -ErrorAction SilentlyContinue
  Remove-Item Env:ANTHROPIC_AUTH_TOKEN -ErrorAction SilentlyContinue
  Remove-Item Env:ANTHROPIC_MODEL -ErrorAction SilentlyContinue
  claude $args
}
```

---

## ⚠️ ข้อควรระวัง

### Security
- **ห้ามใส่ key ใน `.zshrc` ตรงๆ** — ใช้ `~/.openrouter-key` (chmod 600) แทน
- **ห้าม commit key ขึ้น GitHub** — เพิ่ม `.openrouter-key` ใน `.gitignore` ของทุก project
- ถ้า key รั่ว → ไป https://openrouter.ai/keys → revoke + create ใหม่

### Quality
- Free models **ทำตามกฎ CLAUDE.md ที่ซับซ้อนได้แม่นน้อยกว่า** Claude จริง
- งาน wiki ที่ต้องอ่าน CLAUDE.md (300+ บรรทัด) + ทำตาม Fast Query Protocol → Claude จริงน่าเชื่อถือกว่า
- ทดสอบ free model ก่อนพึ่งพาเต็มที่

### Compatibility
- Claude Code อาจ update parser ของ env var → broken
- Workaround: ทดสอบหลัง update ทุกครั้ง (`claude-qwen` แล้วลองพิมพ์ "hello")

---

## Model Lifecycle — กันโดนตัด

### ปัญหา: model name ใน function เป็น **hardcode**
- OpenRouter เพิ่ม/ลบ free model เรื่อยๆ (Gemini 2.0 Flash Exp ถูกตัด Feb 2026)
- Function `claude-gemini` ที่ hardcode model name → 400/404 error เมื่อ model ถูกลบ
- ไม่มีระบบ auto-detect

### วิธีแก้ — 3 ระดับ

**1. ใช้ `claude-router` (auto-select)** ⭐ แนะนำ
- ใช้ model `openrouter/free` — OpenRouter เลือกให้เอง
- ไม่ต้องอัปเดตเมื่อ model ถูก deprecate
- คุณภาพไม่คงที่ (เปลี่ยนตามใจ OpenRouter) แต่ใช้งานได้แน่นอน

**2. ใช้ `claude-list-free` ก่อนเลือก** — เห็น current state
```bash
claude-list-free        # ดู free models ที่ support tools ปัจจุบัน
claude-or <model-id>    # ลองตัวที่อยากใช้
```

**3. ดู web UI ของ OpenRouter** (เร็วที่สุด)
- https://openrouter.ai/models?modality=text&supported_parameters=tools&max_price=0
- filter: tools support + price 0
- copy model id → `claude-or <id>`

### Model ปัจจุบัน (April 2026, ตรวจ `claude-list-free` ทุกเดือน)

| ID | ความเก่ง | Context | หมายเหตุ |
|----|---------|---------|---------|
| `qwen/qwen3-coder:free` | code | 262K | hardcode ใน `claude-qwen` |
| `qwen/qwen3-next-80b-a3b-instruct:free` | general | 262K | ใหม่ ลองดู |
| `inclusionai/ling-2.6-flash:free` | general | 262K | speed-focused |
| `tencent/hy3-preview:free` | general | 262K | ทดลอง |
| `google/gemma-4-26b-a4b-it:free` | general | 262K | Google Gemma 4 |
| `nvidia/nemotron-3-super-120b-a12b:free` | reasoning | 262K | ใหญ่ |
| `openai/gpt-oss-120b:free` | general | 131K | OpenAI open-source |
| `z-ai/glm-4.5-air:free` | code | 131K | Zhipu (จีน) |
| `openrouter/free` | meta | 200K | auto-router (ใช้กับ `claude-router`) |

### ทำให้ไม่พลาด

```bash
# Cron job ทุกอาทิตย์ — บันทึก list ปัจจุบัน
0 9 * * 1 zsh -c 'claude-list-free > ~/openrouter-models-$(date +\%Y\%m\%d).txt'
```

หรือเปิด `claude-list-free` ทุกครั้งก่อนเลือก model

---

## Troubleshooting

| Error | สาเหตุ | แก้ |
|-------|-------|-----|
| `401 Unauthorized` | key ผิด/หมดอายุ | check `cat ~/.openrouter-key` แล้วลอง regenerate |
| `429 Rate limit` | เกิน 200/วัน หรือ 20/นาที | รอ reset (UTC midnight) หรือเติม credit |
| `400 Bad Request` | model ไม่มี/ปิดให้บริการ | check https://openrouter.ai/models — บางตัว free แล้วถูกย้ายเป็น paid |
| `claude` ไม่รู้จัก function | ลืม `source ~/.zshrc` | `source ~/.zshrc` หรือเปิด terminal ใหม่ |

---

## Decision Log

### 2026-04-26: เลือก Level 1 (`claude-smart`) — ข้าม Level 3 (LiteLLM)

**ทำไม:**
- ใช้ Claude Code 1-2 sessions/วัน (light user) — daemon overhead ไม่คุ้ม
- Setup LiteLLM ซับซ้อน (venv + yaml + port + systemd) ใช้เวลา maintain มากกว่าประโยชน์
- `claude-smart` rule-based ตัดสินใจถูก ~80% เพียงพอ
- Multi-tab manual (Level 2) backup ได้ตอน auto-pick พลาด

**เงื่อนไขที่จะกลับมาพิจารณา Level 3:**
- ✅ ตั้ง **Mac Mini local LLM server** ได้แล้ว (ตอนนั้นต้องการ proxy เชื่อม Ollama local + OpenRouter cloud + Anthropic real)
- ✅ ใช้ Claude Code เกิน 5 sessions/วัน
- ✅ มี automation/script ที่ต้องการ auto-fallback resilience
- ✅ เริ่มสร้าง production agent (ไม่ใช่ใช้คนเดียว)

**Reference future:**
- [[wiki/sources/local-llm-mac-mini-guide]] — Mac Mini setup สำหรับ Local LLM
- LiteLLM docs: https://docs.litellm.ai/docs/proxy/quick_start

---

## ความสัมพันธ์
- [[wiki/concepts/ai-tools/local-llm-routing]] — concept routing โมเดลตามความซับซ้อน
- [[wiki/entities/ai-tools/telegram-ai-router]] — design routing tier (Ollama → Gemini → Claude)
- [[wiki/concepts/ai-tools/session-setup]] — Claude Code workflow + Phase 2 .git setup
- `scripts/setup-drive-redirect.sh` — setup script สำหรับคอมใหม่
