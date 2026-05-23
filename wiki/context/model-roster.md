# Model Roster — AI Crew Lineup

> **Auto-updated** by `scripts/update-model-roster.sh` | Last updated: 2026-05-20
> อัปเดตทุก 7 วัน หรือเมื่อ user รัน `bash scripts/update-model-roster.sh`
> Machine config: `wiki/context/model-roster.conf` (sourced by `scripts/delegate.sh`)

---

## Current Champions (2026-05-20)

| Tier | Task | Champion Model | Provider | Cost |
|------|------|----------------|----------|------|
| **T1** | search / lookup / summarize | `deepseek/deepseek-chat-v3-0324:free` | DeepSeek | ฟรี |
| **T1-FB** | fallback T1 | `qwen/qwen3-235b-a22b:free` | Alibaba | ฟรี |
| **T1-FB2** | fallback T1 | `meta-llama/llama-3.3-70b-instruct:free` | Meta | ฟรี |
| **T2** | reason / compare / analyze | `deepseek/deepseek-r1:free` | DeepSeek | ฟรี |
| **T2-FB** | fallback T2 | `qwen/qwen3-235b-a22b:free` | Alibaba | ฟรี |
| **T2-FB2** | fallback T2 | `openrouter/auto` | OpenRouter | ถูก |
| **T3** | scan / long-context | `qwen/qwen3-30b-a3b:free` | Alibaba | ฟรี |
| **T3-FB** | fallback T3 | `openai/gpt-4o-mini` | OpenAI | ถูก |

---

## ทำไมใช้ OpenRouter เป็น Gateway เดียว

```
OPENROUTER_API_KEY (1 key)
    ├── DeepSeek V3-0324:free    — coding, search, general
    ├── DeepSeek R1:free         — reasoning, math, logic
    ├── Qwen3-235B:free          — 235B params, ดีที่สุดในบรรดา free
    ├── Qwen3-30B:free           — เร็วกว่า Qwen3-235B, ดีพอสำหรับ scan
    ├── Llama 3.3 70B:free       — solid general purpose
    ├── GPT-4o-mini              — cheap paid, ดีสำหรับ structured output
    └── 200+ models อื่นๆ
```

---

## Parallel Race Mode

`scripts/delegate.sh race "<prompt>"` รัน top-3 free models พร้อมกัน → ใช้คำตอบแรกที่ตอบกลับ

ดีสำหรับ:
- คำถามที่ต้องการคำตอบเร็วที่สุด
- เมื่อไม่รู้ว่า model ไหน rate-limit อยู่
- High-availability: ถ้า 1 ล้ม ก็ยังมีอีก 2

---

## New Model Alert (run update-model-roster.sh เพื่อ refresh)

หน้านี้จะแสดง top-5 free models ล่าสุดที่ OpenRouter มีหลัง update:

```
[รอ update-model-roster.sh รัน]
```

---

## Version History

| วันที่ | การเปลี่ยนแปลง |
|--------|----------------|
| 2026-05-20 | สร้างครั้งแรก — roster เริ่มต้น |
