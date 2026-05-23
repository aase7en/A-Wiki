---
type: concept
category: pharmacy
tags: [pharmacy, drug-aliases, fuzzy-match, drug-ordering]
sources: [sp-drugstore-2020-catalog, drug-aliases-reference]
created: 2026-04-29
updated: 2026-04-30
---

# Drug Aliases (ชื่อเรียกอื่น/ตัวย่อของยา)

**ประเภท**: Reference / Dictionary
**สถานะ**: Active

## ภาพรวม
หน้านี้รวบรวม "ชื่อเล่น" (aliases), ชื่อย่อ (abbreviations), หรือการสะกดคำที่พบบ่อยในการสั่งยาของลูกน้อง เพื่อใช้เป็นฐานข้อมูลให้ AI ([[wiki/synthesis/pharmacy-order-checker]]) นำไปทำ Fuzzy Match กับฐานข้อมูลยาหลัก ([[raw/pharmacy/sp_drugs_full_3760.json]])

## รายการ Aliases ที่พบบ่อย

| ชื่อทางการ | ชื่อเล่น / ตัวย่อ / สะกดผิด | หมายเหตุ |
|-----------|-------------------------|---------|
| **AMOXYCILLIN** | อม็อก, amox, amoxil, amoxy, a.m.mox, อมอก, อ.ม.มอก | |
| **PARACETAMOL** | พารา, para, p.para, paracet, การา | |
| **IBUPROFEN** | ไอบู, ibu, ibufen | |
| **DICLOFENAC** | ไดโคล, diclo, di-clo | |
| **MEFENAMIC ACID** | พอนสแตน, ponstan, mefe, mefen, ปนสตัน | มักเรียกตามชื่อการค้า |
| **CHLORPHENIRAMINE** | CPM, ซีพีเอ็ม, ยาแก้แพ้เม็ดเหลือง | |
| **CETIRIZINE** | เซทิ, cetir | |
| **LORATADINE** | ลอรา, lora, ความโล่ง, lorata | |
| **OMEPRAZOLE** | โอเม, ome, omep, ออมเพ, omeprazol | |
| **AMBROXOL** | แอมบรอก, ambrox, ยาไอ | |
| **BROMHEXINE** | บรอมเฮก, bromhex | |
| **SIMVASTATIN** | ซิมวา, simva | |
| **AMLODIPINE** | แอมโล, amlo | |
| **ENALAPRIL** | อีน่า, ena, enalapril | |
| **METFORMIN** | เมทฟอร์, metfor | |
| **METRONIDAZOLE** | เมโทร, metro, metronidazole | |
| **HYOSCINE** | บุสโคพาน, buscopan, ไฮออสซิน, hyoscine | มักเรียกตามชื่อการค้า Buscopan |
| **SIMETHICONE** | ไซเมท, air-x, แอร์เอ็กซ์, simeth | |
| **DEXTROMETHORPHAN** | เดกซ์โทร, dex, dextro | |
| **PREDNISOLONE** | เพรด, pred, predni | |
| **DOMPERIDONE** | โมทิเลียม, motilium, ดอมเพอ, domper | |
| **ASPIRIN** | แอสไพริน, aspi, aspirin | |
| **ORAL REHYDRATION SALTS** | ORS, เกลือแร่, ออเรส | |
| **CLINDAMYCIN** | ดาซิน, dacin, clinda | |
| **AMOX + CLAVULANATE** | ออกเมนติน, augmentin, คลาวู, clavu | |
| **NORFLOXACIN** | นอร์ฟล็อก, norflox | |

## หลักการ Mapping สำหรับ AI
1. **ชื่อย่อมาตรฐาน**: เช่น CPM, ORS, GPO (ถ้าเป็นยารัฐบาล)
2. **การตัดท้ายคำ**: เช่น Amoxycillin -> Amox
3. **การทับศัพท์ภาษาไทย**: เช่น Paracetamol -> พารา
4. **ชื่อการค้าที่ใช้แทนชื่อสามัญ**: เช่น Mefenamic Acid -> Ponstan

## ความสัมพันธ์
- [[wiki/synthesis/pharmacy-order-checker]] — ระบบที่นำข้อมูลนี้ไปใช้
- [[wiki/concepts/pharmacy/ordering-workflow]] — workflow การสั่งซื้อ
- [[wiki/concepts/pharmacy/drug-classification]] — หมวดยาหลัก

## Aliases เพิ่มเติม — ยี่ห้อ/ชื่อการค้าที่พบในร้านภูฟาร์มาซี

| ชื่อทางการ | ชื่อเล่น / ตัวย่อ / สะกดผิด | หมายเหตุ |
|-----------|-------------------------|---------|
| **NEUROBION** | นิวโรเบียน, neurobion | ทับศัพท์ |
| **MARVELON** | มาร์วีลอน, marvelon | ทับศัพท์ |
| **MINNY** | มินนี่, minny | ทับศัพท์ |
| **PREME** | พรีม, preme | ทับศัพท์ |
| **ANNYLYN** | แอนนี่ ลินน์, annylyn | ทับศัพท์ |
| **BRONPECT-D** | บรองเพค-ดี, bronpect | ทับศัพท์ |
| **FLEMEX** | เฟลมเม็กซ์, เฟลมเม็ค, flemex | ทับศัพท์ |
| **MUCOLID** | มูโคลิด, mucolid | ทับศัพท์ |
| **HIRUDOID** | Hirudiid, hirudoid | สะกดผิด |
| **BETA-DIPO** | BETA-DOPO, beta-dopo | สะกดผิด |
| **ANTACIL GEL** | ANTAC GEL, antac gel | สะกดผิด |
| **BELCID FORTE** | Belched FORTE, belched forte | สะกดผิด |
| **TRAM LOTION** | แทรมโลชั่น, tram lotion | ทับศัพท์ผิด |
| **T.V. LONE LOTION** | ทีวีโลชั่น, tv lotion, ทีวี โลชั่น | ชื่อย่อ |
| **MYDA-B** | ไมด้าบี, myda-b, ไมดาบี | ทับศัพท์ |
| **PIRCAM-20** | เพียแคม20, เพียแคม, pircam | ทับศัพท์ผิด (Piroxicam) |
| **PUDINHARA** | พูดินฮาร่า, pudin hara, pudinhara | ทับศัพท์ |
| **TYLENOL INFANT DROP** | ไทยดีม่อน เด็กเล็ก, para drop, tylenol infant | ชื่อยี่ห้อจริง |
| **POX 109** | pox109, pox 109 | ชื่อ code supplier |
| **M16 PATAR** | m16, m16 ที่อุดฟัน | ต้องระบุยี่ห้อ PATAR |
| **HERBAL ONE GARLIC** | กระเทียมแคปซูล, กระเทียมแคป, garlic cap | ต้องระบุยี่ห้อ |
| **B-GARLIC** | กระเทียมดำ, b garlic | ต้องระบุยี่ห้อ |
| **ROHTO VITA 40** | น้ำตาเทียมญี่ปุ่น, rohto vita | ต้องระบุยี่ห้อ+ขนาด |
| **OKAMOTO 003** | ถุงยางอนามัยญี่ปุ่น, okamoto | ต้องระบุยี่ห้อ |
| **METHYCOBAL 500MCG** | Methycobal 500mg | หน่วยผิด mg→mcg |
| **SELFIDE** | selfide, selenium sulfide | ต้องระบุ active ingredient |

## Aliases เพิ่มเติม — ออเดอร์ 2026-05-19

| ชื่อทางการ | ชื่อเล่น / ตัวย่อ / สะกดผิด | หมายเหตุ |
|-----------|-------------------------|---------|
| **MARVELON** | มาร์นอน, marnon, marlon | สะกดผิด/ตัดสั้น จากมาร์วีลอน |
| **YAZ** | ยาส, ยาซ, yas | ทับศัพท์ผิด — YAZ 28เม็ด Bayer |
| **DAFOMIN** | ดาโฟมิน, dafomin | ทับศัพท์ — Metformin 500mg brand |
| **CETIRIZINE** | cetrizin, ซีทริซิน, cetirizin | สะกดผิด |
| **BEPANTHEN OINTMENT** | บีแพนเธน, bipanthen, บีแพน, bepantene | ทับศัพท์ |
| **MYDOCALM** | tolperisone, ทอลเพอริโซน, tolper | generic→brand: Tolperisone = Mydocalm |
| **NASOTAPP TABLET** | nasotap, นาโซแท็บ, นาโซแท็ป | สะกดผิด/ตัดสั้น |
| **BENDA 500** | benda, เบนด้า 500, เบนด้า, เบนดา, เบนดาโซล, mebendazole 500 | ชื่อยี่ห้อ BENDA |
| **มหาหิงค์ วี.เอส.** | มหาหิงค์ลูกกลิ้ง, มหาหิงค์, mahahingko, asafoetida roll | ชื่อยี่ห้อ วี.เอส. |
| **BACTIGRAS** | แบคทิแกรส, แบคทีแกรส, bactigras, ตาข่ายกันติดแผล bactigras | Smith&Nephew paraffin gauze |
| **TIMI CREAM** | timi, ไทมี, timi cream, ยาทาแก้เชื้อรา timi | ยาทาเชื้อรา |
| **AZYCIN** | azycin, อาซีซิน, azithromycin 250 brand | ยี่ห้อ Azithromycin |
| **TIMI CREAM** | timi, ไทมี, timi cream | ยาทาเชื้อรา |
| **PERSKINDOL CLASSIC GEL** | perskindol, perskindol gel | ระบุสี classic=เหลือง, cool=ฟ้า |
| **BACTIGRAS** | bactigras, แบคทิแกรส, แบคทีแกรส | ตาข่ายกันติดแผล Smith&Nephew |
| **NEOBUN** | neobun, นีโอบัน | แผ่นพลาสเตอร์ menthol |
| **FISH OIL salmon 75s [VISTRA]** | vistra salmon fish oil 75, vistra fish oil 75 | ระบุยี่ห้อ VISTRA + ขนาด |

## แหล่งข้อมูล
- [[raw/pharmacy/sp_drugs_full_3760.json]]
- [[wiki/sources/drug-aliases-reference]]
