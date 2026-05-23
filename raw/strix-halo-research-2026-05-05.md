# AMD Ryzen AI Max+ 395 (Strix Halo) — Research Notes
> Source: Gemini CLI 3 queries (web search) — 2026-05-05
> Status: PENDING verification — URLs ต้อง spot-check ก่อน commit ลง wiki ที่สำคัญ

## Query 1: Pricing (mini-PC, 128GB unified)

| รุ่น | RAM | ราคา USD (Base) | ราคาไทย | URL |
|---|---|---|---|---|
| GMKtec EVO-X2 | 128GB | $2,199 | **78,900฿** (ศูนย์ไทย) / 40-45K฿ (overseas/sale) | gmktec.com |
| PELADN YO1 | 128GB | $2,299 | **78,900฿** (ศูนย์ไทย) | shopee.co.th |
| Framework Desktop | 128GB | $2,459 | ~125-135K฿ (นำเข้าเอง รวมภาษี) | frame.work |
| HP ZBook Ultra G1a | 128GB | $4,996 | ~199,900฿ (สเปกท็อป 4TB, laptop) | hp.com/th |

**หมายเหตุ Gemini**: อ้าง "DRAM Crisis ปี 2026" ทำให้ราคาตลาดโลกเพิ่ม — ⚠️ ยังไม่ verify

## Query 2: LLM Benchmarks (llama.cpp/ROCm/Vulkan)

| Model | Quantization | tok/s | Source |
|---|---|---|---|
| Llama 3.3 70B | Q4_K_M | **5.0 - 5.5** | llm-tracker.info/howto/AMD-Strix-Halo |
| Qwen 2.5 72B | Q4_K_M | 4.5 - 5.5 | reddit.com/r/LocalLLaMA |
| Llama 3.1 8B | Q4_K_M | 45 - 55 | techpowerup.com |

**Memory bandwidth จริง**: ~215 GB/s (LPDDR5X-8000, 256-bit bus)
**iGPU shared VRAM**: max 96GB (จาก 128GB unified)

## Query 3: Power Consumption

| เครื่อง | Idle W | LLM Load W | Peak W | Source |
|---|---|---|---|---|
| GMKtec EVO-X2 (Strix Halo) | 10-13W | ~82W | 220W | gmktec.com, techpowerup.com |
| Mac Studio M4 Max | 6-10W | 80-120W | 145-170W | support.apple.com, reddit |

**Bandwidth comparison** (สำคัญกับ LLM speed):
- Strix Halo: ~215 GB/s
- Mac M4 Max: **546 GB/s** (binned variant) — เร็วกว่า ~2.5 เท่า

## Reality check vs my earlier claim

ก่อนหน้านี้ผมประเมิน Strix Halo 70B Q4 = 8-12 tok/s — **ผิด**
ตัวเลขจริง (Gemini benchmark): **5.0-5.5 tok/s** — ช้ากว่า M4 Max 64GB (6-10 tok/s)

สาเหตุ: bandwidth จริงต่ำกว่าที่คิด (215 vs 256 GB/s) + Mac M4 Max bandwidth สูงกว่าที่คิด (546 vs 410 GB/s)

→ **Strix Halo ไม่เหนือ M4 Max ที่ 70B speed** — เหนือเฉพาะ RAM size (128GB > 64GB) + ราคา + Linux

## URL Verification needed

- llm-tracker.info/howto/AMD-Strix-Halo — ✅ น่าจะมีจริง (เป็น tracker ของ community)
- gmktec.com / shopee.co.th — ✅ ของจริง
- ราคาศูนย์ไทย 78,900฿ — ⚠️ ต้อง spot-check จาก Shopee/Lazada Official ก่อนตัดสินใจซื้อ
