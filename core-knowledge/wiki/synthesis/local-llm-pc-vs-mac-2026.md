---
type: synthesis
tags: [local-llm, pc-build, mac-mini, mac-studio, hardware-comparison, ryzen, apple-silicon, vram, unified-memory, strix-halo]
sources: [ai-iot-server-build-v3, local-llm-mac-mini-guide, strix-halo-research-2026-05-05]
created: 2026-05-05
updated: 2026-05-05
---

> 🔄 **อัปเดต 2026-05-05 (later)**: เพิ่ม section "Strix Halo verified data" หลัง verify ผ่าน Gemini CLI — **ตัวเลขเดิมที่ผมประเมินผิด** ดูใน [[sources/strix-halo-research-2026-05-05]]

# Local LLM Hardware: PC Build vs Mac (2026)

## คำถามที่ตอบ

ในงบ ~100,000฿ สำหรับงาน Local LLM 24/7 + IoT monitor + AI agent + web server ควรเลือก:

- **PC build** (Ryzen + RTX 4070 Ti Super 16GB + 128GB DDR5)
- **Mac mini M4 Pro 64GB** หรือ
- **Mac Studio M4 Max 64GB**

## TL;DR

| ปัจจัย | PC ชนะ | Mac ชนะ |
|---|---|---|
| Upgradeability | ✅ เปลี่ยน GPU/RAM/SSD ได้ตลอด | ❌ ทุกอย่างบัดกรี |
| ราคาต่อ spec ดิบ | ✅ 16GB VRAM + 128GB RAM ในงบเดียวกัน | ❌ unified memory แพงกว่า/GB |
| **70B+ model speed** | ❌ VRAM ไม่พอ ต้อง offload → ช้า | ✅ unified memory bandwidth สูง รันได้ลื่น |
| ประหยัดไฟ 24/7 | ❌ idle 50-80W, load 200-400W | ✅ idle 5-10W, load 30-80W |
| เสียงเงียบ | ⚠️ ขึ้นกับ build (TK-1 + Noctua = เงียบ) | ✅ เงียบสนิท |
| OS ecosystem | ✅ Linux/Windows native, CUDA | ⚠️ macOS ผูก ecosystem |
| รัน Docker/IoT broker | ✅ Linux native, Home Assistant, Mosquitto | ⚠️ ใช้ Docker Desktop ได้ แต่กิน resource |
| Resale value 5 ปี | ⚠️ depreciate เร็ว (GPU ใหม่ออก) | ✅ Mac คงราคาดี |

## เปรียบเทียบ Spec ที่งบใกล้กัน

### PC build (~98,500฿) — จาก [[sources/ai-iot-server-build-v3]]

```
CPU:    Ryzen 7 9700X (8C/16T, Eco 65W)
GPU:    RTX 4070 Ti Super 16GB GDDR6X
RAM:    128GB DDR5-5600 (4x 32GB)
SSD:    2TB NVMe Gen4
HDD:    8TB NAS-grade
PSU:    750W SFX Gold
Case:   Jonsbo TK-1 v2 (mini)
```

**Local LLM throughput:**
- 7B Q4: ~80-100 tok/s (in VRAM)
- 14B Q4: ~40-60 tok/s (in VRAM)
- 32B Q4: ~15-25 tok/s (partial offload)
- 70B Q4: ~3-6 tok/s (heavy CPU offload — ใช้ DDR5 bandwidth ~70 GB/s)

### Mac Studio M4 Max 64GB (~120,000-130,000฿)

```
CPU:    M4 Max (16C: 12P+4E)
GPU:    40-core integrated
RAM:    64GB unified (~410 GB/s bandwidth)
SSD:    512GB - 1TB
```

**Local LLM throughput** (จาก [[sources/local-llm-mac-mini-guide]]):
- 7B-8B Q4: ~25-35 tok/s
- 14B-32B Q4: ~12-18 tok/s
- 70B Q4: ~6-10 tok/s (อยู่ใน unified memory ได้ ไม่ต้อง offload)

### Mac mini M4 Pro 64GB (~80,000-90,000฿)

```
CPU:    M4 Pro (12-14C)
GPU:    16-20 core integrated
RAM:    64GB unified (~273 GB/s bandwidth)
SSD:    512GB - 1TB
```

**Local LLM throughput:**
- 14B-32B Q4: 12-18 tok/s
- 70B Q4: <10 tok/s (ใช้ 60% rule = ~38GB available ไม่พอ 70B Q4 ที่ ~40GB → ต้อง quant ลง)

## การวิเคราะห์เชิงลึก

### 1. VRAM vs Unified Memory — แตกต่างยังไงบน Local LLM

**PC (discrete GPU):**
- VRAM (16GB) เร็วมาก (~700 GB/s) แต่จำกัดขนาด model
- ถ้า model ใหญ่กว่า VRAM → ต้อง offload layer ไป system RAM (DDR5 = 70 GB/s) → ช้าลง 5-10 เท่า
- **Sweet spot**: model ที่ fit ใน VRAM (ปัจจุบัน Q4 ขนาด 7B-13B fit สบาย, 32B ต้อง Q3 หรือ partial offload)

**Mac (unified memory):**
- หน่วยความจำเดียว GPU+CPU แชร์กัน, bandwidth ปานกลาง (273-546 GB/s)
- model ใหญ่อยู่ในหน่วยความจำเดียว ไม่ต้อง offload
- **Sweet spot**: model ใหญ่กว่า VRAM ของ GPU consumer (เช่น 70B Q4 ใน 64GB Mac คุ้มกว่า 16GB VRAM)

### 2. งบเท่าไรจึงคุ้มแต่ละแบบ

```
< 50,000฿:  Mac mini M4 24GB หรือ Pi5+AI HAT (ดู [[sources/rpi-ai-hat-plus-2-official]])
50-90,000฿: Mac mini M4 Pro 48-64GB (ดี balance)
90-120,000฿: PC build 16GB VRAM + 128GB RAM ⚠️ หรือ Mac mini M4 Pro 64GB
120-180,000฿: Mac Studio M4 Max 64GB หรือ PC + RTX 5080 16GB
> 180,000฿: PC + RTX 5090 32GB ⭐ หรือ Mac Studio M4 Ultra 128GB+
```

### 3. การ Upgrade ในอนาคต

**PC เลือก path ได้:**
- เปลี่ยน GPU เป็น RTX 5090 (32GB) ภายหลัง — รัน 70B Q4 ใน VRAM เต็ม
- เพิ่ม GPU ใบที่ 2 (ถ้า PSU+case รับได้) — กระจาย model
- เพิ่ม HDD/SSD ได้ตลอด
- ✅ **PC build จะอายุยาว 5-7 ปี** ถ้า upgrade GPU ทุก 2-3 ปี

**Mac:**
- ❌ RAM/SSD บัดกรี เปลี่ยนไม่ได้
- ขายเครื่องเก่าซื้อรุ่นใหม่ (Mac คงราคาดี ~60-70% หลัง 2 ปี)
- ✅ รุ่นใหม่ทุก 1-2 ปี ดีขึ้นชัดเจน (M4→M5)

### 4. นอกเหนือจาก Local LLM

**PC ดีกว่าเรื่อง:**
- Linux native → Docker, Home Assistant, Mosquitto MQTT, Node-RED, Grafana ลื่น
- IoT broker 24/7 + Local LLM พร้อมกันได้สบาย
- 4K entertainment (HDMI 2.1 + GPU)
- Gaming (ถ้าอยาก)
- Bitcoin full node, file server, etc.

**Mac ดีกว่าเรื่อง:**
- ใช้เป็น workstation หลักได้ด้วย (PC + Mac = 2 เครื่อง)
- เสียงเงียบสนิท (เหมาะตั้งห้องนอน)
- ไฟน้อย (idle 5W vs PC idle 50-80W)
- macOS native apps + iCloud sync

## 🆕 Option ที่ 3: AMD Strix Halo (Ryzen AI Max+ 395) — verified 2026-05-05

ทางที่ Gemini Pro ใน PDF [[sources/ai-iot-server-build-v3]] ไม่ได้เสนอ — สเปกคล้าย Mac แต่ใช้ AMD + Linux ได้

### Spec
```
CPU:    Ryzen AI Max+ 395 (16C Zen 5)
GPU:    Radeon 8060S (40 RDNA 3.5 CUs) — iGPU
RAM:    128GB LPDDR5X-8000 unified, 256-bit bus
Bandwidth: ~215 GB/s (verified)
iGPU shared VRAM: max 96GB
TDP: 45-120W configurable
```

### ราคาในไทย (verified)

| เครื่อง | ราคา |
|---|---|
| **GMKtec EVO-X2 128GB** ⭐ | **78,900฿** (ศูนย์ไทย, Lazada/Shopee) |
| PELADN YO1 128GB | 78,900฿ (ศูนย์ไทย) |
| Framework Desktop 128GB | 125-135K฿ (นำเข้า) |
| HP ZBook Ultra G1a (laptop) | 199,900฿ |

### Benchmark Local LLM (verified)
- Llama 3.3 70B Q4_K_M: **5.0-5.5 tok/s** ⚠️ ช้ากว่า M4 Max
- Qwen 2.5 72B Q4: 4.5-5.5 tok/s
- Llama 3.1 8B Q4: 45-55 tok/s

### Power consumption
- Idle: 10-13W (เทียบ Mac M4 Max 6-10W — ใกล้เคียง)
- LLM load: ~82W (เทียบ Mac 80-120W — ดีกว่าเล็กน้อย)
- Peak: 220W (เทียบ Mac 145-170W)

### Strix Halo เหนือ M4 Max ตรงไหนบ้าง?

| ปัจจัย | Strix Halo 128GB | M4 Max 64GB |
|---|---|---|
| **70B Q4 speed** | ❌ 5 tok/s | ✅ 6-10 tok/s (bandwidth 2.5x) |
| **RAM size** | ✅ 128GB → รัน 100B+ ได้ | ❌ 64GB เพดาน |
| **ราคาในไทย** | ✅ **78,900฿** | ❌ 120-130K฿ |
| **Linux native** | ✅ | ⚠️ macOS only |
| **Idle power** | ใกล้เคียง 10-13W | 6-10W |
| **Resale 5 ปี** | ⚠️ AMD | ✅ Mac คงราคา |
| **Upgradeable** | ❌ บัดกรี | ❌ บัดกรี |

**Verdict**: เหนือ Mac เรื่อง "ขนาด RAM + ราคา + Linux" / **แพ้ Mac เรื่อง 70B speed**

ดูรายละเอียด → [[sources/strix-halo-research-2026-05-05]]

## เปรียบเทียบ 3 ทางเลือกหลัก (สำหรับเงื่อนไข "เหนือ M4 Max + ประหยัดไฟ + ราคาเหมาะสม + ระยะยาว")

| เกณฑ์ | A: Strix Halo 128GB | B: PC + RTX 5090 | C: PC + RTX 4090 มือสอง |
|---|---|---|---|
| **70B Q4 speed** | ⚠️ 5 tok/s (ช้ากว่า Mac) | ✅✅ 25-35 tok/s | ✅ 10-15 tok/s |
| **RAM/VRAM size** | ✅✅ 128GB unified | ⚠️ 32GB VRAM | ⚠️ 24GB VRAM |
| **ประหยัดไฟ 24/7** | ✅✅ idle 12W | ❌ ~80W idle (system+GPU) | ⚠️ ~70W idle |
| **ราคาในไทย** | ✅✅ **78,900฿** | ❌ ~140-150K฿ | ✅ ~95-105K฿ |
| **ระยะยาว** | ✅ 5+ ปี (แต่ไม่ upgrade) | ⚠️ GPU ใหม่ทุก 3-4 ปี | ⚠️ GPU เก่าแล้ว ใช้ 3-4 ปี |
| **Linux/IoT/Docker** | ✅ | ✅ | ✅ |

### Verdict ตามค่านิยมของผู้ใช้

ถ้า "**เหนือ M4 Max**" = เร็วกว่าที่ 70B → **Option B (RTX 5090)** เท่านั้น แต่ขัดประหยัดไฟ + ราคา
ถ้า "**เหนือ M4 Max**" = RAM ใหญ่กว่า + ถูกกว่า + Linux → **Option A (Strix Halo)** ✅ คุ้มที่สุด
ถ้าต้องการ balance → **Option C (RTX 4090 used)** เร็วกว่า A, ถูกกว่า B, แต่ idle power สูง

**คำเตือน**: PC build ใน PDF [[sources/ai-iot-server-build-v3]] (RTX 4070 Ti Super 16GB) **ไม่ตอบโจทย์ "เหนือ M4 Max"** ที่ 70B เลย → 70B Q4 จะรันที่ 3-6 tok/s (offload หนัก) ซึ่งช้ากว่าทั้ง M4 Max และ Strix Halo

## 🆕 Option ที่ 4: Mac Studio มือสอง — verified 2026-05-05

⭐ **Plot twist**: Mac Studio M1 Ultra 128GB มือสองในไทย **ถูกกว่า + เร็วกว่า** Strix Halo

### ราคามือสองไทย + 70B Q4 (verified)

| รุ่น | RAM | Bandwidth | ราคามือสอง | 70B Q4 |
|---|---|---|---|---|
| M1 Max | 64GB | 400 GB/s | **36-42K฿** | 6.3-7.0 |
| **M1 Ultra** | **128GB** | **800 GB/s** | **65-75K฿** ⭐ | **12.5-13.5** |
| M2 Max | 64GB | 400 GB/s | 55-62K฿ | 7.5-8.2 |
| M2 Ultra | 128GB | 800 GB/s | 105-120K฿ | 14.0-15.5 |
| M2 Ultra | 192GB | 800 GB/s | 115-135K฿ | 14.0-15.5 |
| M3 Ultra | 96GB | 819 GB/s | 115-125K฿ | 16.5-18.0 |
| M3 Ultra | 256GB | 819 GB/s | 165-195K฿ | 16.5-18.0 |

### M1 Ultra 128GB used vs Strix Halo (head-to-head)

| | Strix Halo 128GB | M1 Ultra 128GB used |
|---|---|---|
| ราคา | 78,900฿ | **65-75K฿** ⭐ |
| Bandwidth | 215 GB/s | **800 GB/s** (3.7x) |
| 70B Q4 | 5.0-5.5 tok/s | **12.5-13.5 tok/s** (2.3x) |
| RAM | 128GB | 128GB |
| ประกัน | ✅ ใหม่ | ❌ มือสอง 4 ปี |
| Linux/Docker | ✅ native | ⚠️ Docker Desktop |
| Resale 5 ปี | ⚠️ AMD | ✅ Mac คงราคาดี |
| macOS support | - | ถึง ~2030 |

→ **M1 Ultra 128GB used ชนะที่: ราคา + speed + bandwidth**
→ **Strix Halo ชนะที่: ใหม่+ประกัน, Linux native, อายุการใช้งานยาวกว่าแน่ๆ**

### ⚠️ Caveats ของ Mac มือสอง
1. ไม่มีประกัน — เช็ค AppleCare ที่เหลือ
2. M1 Ultra ปี 2022 → 4 ปีแล้ว, โอกาส SSD wear / fan / power supply เสื่อม
3. macOS support ลด (M1 อาจถูก deprecate ใน macOS 19-20)
4. ราคามือสองผันผวน — เช็ค Facebook Group "ซื้อขาย Mac"
5. Software lock / iCloud lock — verify ก่อนโอนเงิน

ดูรายละเอียด → `raw/mac-studio-used-thailand-2026-05-05.md`

## เปรียบเทียบ 4 ทางเลือกหลัก (Final)

| เกณฑ์ | Strix Halo new | M1 Ultra used | RTX 5090 PC | RTX 4090 used PC |
|---|---|---|---|---|
| ราคา | 78,900฿ | **65-75K** ⭐ | 140-150K | 95-105K |
| 70B Q4 tok/s | 5 | **12-13** | 25-35 | 10-15 |
| RAM/VRAM | 128GB | 128GB | 32GB | 24GB |
| ประหยัดไฟ idle | ✅ 12W | ⚠️ 6-10W | ❌ 80W | ❌ 70W |
| Linux/IoT | ✅ | ⚠️ Docker | ✅ | ✅ |
| ประกัน | ✅ ใหม่ | ❌ | ✅ ใหม่ | ❌ |
| ระยะยาว 5 ปี | ✅ | ⚠️ HW เสื่อม | ⚠️ GPU obsolete | ⚠️ |
| Resale | ⚠️ | ✅ | ⚠️ | ⚠️ |

### 🎯 Verdict ตามค่านิยมของผู้ใช้

**ถ้ารับ "มือสอง" ได้** → **M1 Ultra 128GB มือสอง 65-75K฿** ⭐ คุ้มที่สุด:
- ถูกกว่า Strix Halo ~5-15K
- เร็วกว่า Strix Halo ที่ 70B 2.3 เท่า
- "ใช้ระยะยาว" ได้ ~3-5 ปีก่อนเสี่ยง hardware fail (เพราะ 4 ปีแล้ว)

**ถ้าต้อง "ใหม่ + ประกัน + Linux native"** → **Strix Halo (GMKtec EVO-X2) 78,900฿**:
- ใหม่ทั้งเครื่อง, support เต็มที่
- Linux/Docker/IoT native
- 70B 5 tok/s ก็ยังพอใช้

**ถ้าต้อง "70B เร็วสุดในงบ"** → **M2 Ultra 128GB used 105-120K** (14-15 tok/s) หรือ **PC + RTX 5090** (25-35 tok/s)

## ข้อเสนอแนะ (Decision Logic)

> ผู้ใช้กำลังเปลี่ยนใจจาก Mac → PC เพราะ "spec แรงกว่า อัพเดทได้ ในราคาใกล้เคียงกัน"

**ถ้าจะเลือก PC:**
1. ✅ ถูกต้องที่จะเลือก PC ถ้าต้องการ:
   - Upgradeability (เปลี่ยน GPU ในอนาคต)
   - รัน IoT broker + Home Assistant 24/7 native บน Linux
   - Bitcoin full node + Umbrel-style apps
2. ⚠️ แต่ต้องรู้ว่า **16GB VRAM ไม่พอรัน 70B Q4 เต็มความเร็ว** — รันได้แต่ช้ากว่า Mac unified memory
3. ⚠️ **ตรวจสอบ mainboard อีกครั้ง** — PDF ระบุ B860M ซึ่งเป็น Intel chipset, ของจริง AMD ต้องเป็น **B850M**

**ทางเลือกอื่นในงบเดียวกัน:**
- **PC + RTX 5070 Ti 16GB** (รุ่นใหม่กว่า ราคาใกล้กัน) — efficiency ดีกว่า 4070 Ti Super
- **PC + RTX 4090 24GB ซื้อมือสอง** — VRAM เพิ่มเป็น 24GB, รัน 32B Q4 เต็ม + 70B Q3 ได้
- **PC ลด RAM เป็น 64GB** ประหยัด ~10,000฿ → upgrade GPU ดีกว่า

**Hybrid approach (น่าสนใจสุด):**
- ใช้ Pi5 ปัจจุบันเป็น IoT broker + Bitcoin node 24/7 (ใช้ไฟ ~10W)
- สร้าง PC สำหรับ Local LLM (เปิดเฉพาะตอนใช้)
- ลดปัญหา PC ใช้ไฟ 50-80W idle 24/7

## แหล่งข้อมูลที่ใช้

- [[sources/ai-iot-server-build-v3]] — สเปก PC build ที่ Gemini Pro เสนอ (พบ chipset typo + 16GB VRAM ไม่พอ 70B)
- [[sources/strix-halo-research-2026-05-05]] — verified ราคา/benchmark/power ของ Ryzen AI Max+ 395
- [[sources/local-llm-mac-mini-guide]] — ตัวเลข tok/s, 60% rule, Apple Silicon
- [[sources/rpi-ai-hat-plus-2-official]] — ทางเลือก low-end (Pi5 + AI HAT+)
- [[sources/ollama-pi5]] — บริบท Ollama บน ARM
- [[concepts/ai-tools/local-llm-routing]] — pattern routing local↔cloud

## ความสัมพันธ์

- ขยายแนวคิดจาก [[synthesis/dual-ai-workflow]] (ใช้ทั้ง local + cloud)
- เกี่ยวข้องกับ [[entities/ai-tools/telegram-ai-router]] (ใช้ local LLM เป็น tier 1)
