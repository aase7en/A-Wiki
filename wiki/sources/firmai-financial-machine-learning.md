---
type: source
title: "firmai/financial-machine-learning — curated ML-in-finance project index (Sov.ai / ml-quant.com)"
slug: firmai-financial-machine-learning
date_ingested: 2026-07-14
original_file: raw/firmai-financial-ml-readme.md
source_url: https://github.com/firmai/financial-machine-learning
tags: [ai-tools, monte-carlo, quant, finance, machine-learning, portfolio, risk, alternative-data]
---

# firmai/financial-machine-learning

**ประเภท**: repository index (curated projects + wiki)
**วันที่ verify**: 2026-07-14
**ผู้เขียน/ดูแล**: firmai / Sov.ai (collaborates with quantitative hedge funds)
**License**: ดูใน repo (แต่ละ sub-project ต่าง license กัน — ตรวจก่อน vendor)

> คลัง curated ที่ใหญ่ที่สุดแห่งหนึ่งของ Machine-Learning-in-Finance projects พร้อม wiki ที่จัดหมวดตามเทคนิค ใช้เป็น "map" หาเทคนิคเฉพาะทางก่อนเจาะรายตัว

## ประเด็นหลัก

1. **Map ก่อน dive** — README ทำหน้าที่เป็น index ของหมวดวิธีการ (ไม่ใช่ code repo ตัวเดียว) แต่ละหมวด link ไป GitHub wiki ที่รวบรวม project ย่อยพร้อม paper reference
2. **หมวดที่เกี่ยวกับ Monte Carlo / risk / portfolio โดยตรง** (สำคัญที่สุดสำหรับ skill เรา):
   - **Portfolio Selection and Optimisation** — mean-variance, risk parity, Black-Litterman
   - **Factor and Risk Analysis** — factor models, VaR/CVaR, stress testing
   - **Derivatives and Hedging** — option pricing, Greeks, Monte Carlo pricing
3. **หมวด supporting**:
   - **Deep Learning & Reinforcement Learning** — time-series forecasting, trading RL
   - **Data Processing Techniques and Transformations** — feature engineering, normalization
   - **Alternative Finance** — non-traditional data (satellite, sentiment, GitHub logs)
   - **Textual** — NLP on filings/news, sentiment
   - **Fixed Income**, **Unsupervised**, **Other Models**

## ข้อมูลที่น่าสนใจสำหรับ skill

- การแบ่งหมวดนี้เป็น taxonomy ที่ดีสำหรับ scope ของ `monte-carlo-quant-analysis` skill — แยก portfolio/risk/derivatives ออกจาก ML-forecasting
- แต่ละหมวดมี paper-backed reference → เหมาะเป็น "further reading" pointer
- Sov.ai เน้น alternative data + predictive modeling → เชื่อมโยงกับ synthetic-data generation ใน skill

## ข้อควรระวัง

- repo นี้เป็น **index/meta** ไม่ใช่ implementation — ห้ามอ้างว่า "code มาจาก firmal" ถ้าเราเขียน skeleton เอง
- sub-projects ใน wiki มี license ต่างกัน → ถ้าจะ vendor code จริงต้องตรวจทีละ repo
- มี bias สูงด้าน institutional quant (hedge-fund-shaped problems) — อาจมากเกินไปสำหรับ personal/portfolio use case

## Wiki pages ที่เกี่ยวข้อง

- [[monte-carlo-quant-analysis]] (skill — สังเคราะห์จาก source นี้ + akashdeepo + unpingco)
- [[akashdeepo-monte-carlo-rrr]] (source คู่หู — MC implementation จริง)
- [[unpingco-python-stats-ml]] (source รากฐาน statistics)
