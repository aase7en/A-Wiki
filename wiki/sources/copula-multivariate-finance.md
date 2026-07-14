---
type: source
title: "Copula (probability theory) — multivariate dependency modeling for quant finance"
slug: copula-multivariate-finance
date_ingested: 2026-07-14
original_file: raw/copula-wikipedia.md
source_url: https://en.wikipedia.org/wiki/Copula_(probability_theory)
domain: trader
tags: [trader, copula, multivariate, dependence, quant, risk, monte-carlo, tail-risk, statistics]
confidence: [verified 2026-07-14]
---

# Copula — multivariate dependency modeling for quant finance

> สรุปจาก Wikipedia "Copula (probability theory)" + เชื่อมโยงกับ skill `monte-carlo-quant-analysis` §2 (Multivariate Normal + Copula row). [verified 2026-07-14]

## ประเด็นหลัก

1. **Copula** = multivariate CDF ที่ marginals ทุกตัว uniform บน [0,1] — ใช้แยก **dependence structure** ออกจาก **marginal distributions** ของแต่ละ variable
2. **Sklar's theorem** (1959): joint CDF H(x₁,...,xₐ) = C(F₁(x₁),...,Fₐ(xₐ)) — ทำให้ model ความสัมพันธ์ได้โดยไม่ต้อง assume joint distribution ทั้งก้อน
3. **Gaussian copula** (David X. Li, 2000) เคยเป็น standard ใน CDO pricing — แต่ underestimate tail dependence → ปัจจัยหนึ่งในวิกฤต 2008 (Salmon, Wired 2009)
4. **Archimedean copulas** (Clayton/Gumbel/Frank/Joe) ใช้พารามิเตอร์เดียว θ — เลือกตาม tail behavior: Clayton = lower-tail strong, Gumbel = upper-tail strong
5. **Student-t copula** แก้ปัญหา Gaussian ด้วย heavier tails (capture tail dependence ที่ Gaussian พลาด)

## ข้อมูลที่น่าสนใจ

### Sklar's theorem (พื้นฐาน)

```
H(x₁,...,xₐ) = C(F₁(x₁), ..., Fₐ(xₐ))

โดยที่:
  H  = multivariate joint CDF
  Fᵢ = marginal CDF ของตัวแปร Xᵢ
  C  = copula function (dependence structure)
```

density form: `h(x₁,...,xₐ) = c(F₁(x₁),...,Fₐ(xₐ)) · f₁(x₁) · ... · fₐ(xₐ)` (c = copula density, fᵢ = marginal density)

### ตารางเปรียบเทียบ copula families

| Copula | Parameter | Tail dependence | ใช้เมื่อ |
|--------|-----------|-----------------|---------|
| **Gaussian** | correlation matrix R | ไม่มี (symmetric) | baseline, marginals ใกล้ normal |
| **Student-t** | R + degrees of freedom ν | symmetric, heavy tails | capture crisis correlations |
| **Clayton** (Archimedean) | θ ∈ [-1, ∞) | lower-tail strong | downside risk, flight-to-quality |
| **Gumbel** (Archimedean) | θ ∈ [1, ∞) | upper-tail strong | bull-market co-movement |
| **Frank** (Archimedean) | θ ∈ ℝ | ไม่มี | symmetric, no extreme tails |

### Monte Carlo with copulas (สำคัญ — เชื่อมกับ skill)

```
1. Draw (U₁,...,Uₐ) ~ C  ขนาด n จาก copula
2. Apply inverse marginals: Xᵢ = Fᵢ⁻¹(Uᵢ)
3. E[g(X₁,...,Xₐ)] ≈ (1/n) Σ g(X₁ᵏ,...,Xₐᵏ)
```

→ copula = ทางเข้า multivariate MC: sample uniform → transform → correlated samples ที่ preserve tail structure

### Quant finance use cases

- **Risk management**: stress-tests ใน downside/crisis regime (correlation เพิ่มขึ้นฝั่ง downside — flight-to-quality)
- **Portfolio optimization**: minimize tail risk, higher-moment optimization (ไม่ใช่ mean-variance อย่างเดียว)
- **VaR forecasting**: US + international equities (Student-t copula ดีกว่า Gaussian ตอนวิกฤต)
- **Derivatives pricing**: CDOs, basket options, spread options
- **Statistical arbitrage**: pairs trading — copula stability > correlation stability
- **Vine copulas** (pair copulas): flexible สำหรับ high-dimensional portfolios — Clayton canonical vine ดีกว่า Gaussian/Student-t ใน downside

### ข้อควรระวัง

- **Stationarity บังคับ** — copula ใช้ได้เฉพาะ time series ที่ stationary + continuous. Auto-correlated/trended/seasonal series → dependence structure ผิด
- **Gaussian copula under-estimate tail dependence** — อย่าใช้เป็น default สำหรับ risk management (บทเรียนจาก 2008)
- **Asymmetric tail dependence เป็น norm** — correlations ฝั่ง downside ≠ upside ในตลาดจริง

## เชื่อมโยงกับ skill monte-carlo-quant-analysis

skill §2 (Distribution Selection) มี row: **"Multi-asset with correlation → Multivariate Normal + Copula → preserve correlation structure"**

copula เป็นวิธีที่ general กว่า Multivariate Normal เพราะ:
1. แยก marginals จาก dependence — ใช้ empirical marginal + Clayton copula ได้
2. capture asymmetric tail dependence (Clayton = lower-tail strong = เหมาะ downside risk)
3. vine copulas scale ไป high dimensions ได้โดยไม่ต้อง assume single correlation matrix

**Decision rule ใน skill workflow**:
- baseline: Multivariate Normal (เร็ว, ง่าย, แต่ under-estimate tails)
- risk-sensitive: Student-t copula (heavy tails, symmetric)
- downside-focused: Clayton copula (lower-tail strong)
- เปรียบเทียบ ≥ 2 copula → report model risk (reporting standard #4)

## References

- Nelsen, R.B. (2006). *An Introduction to Copulas* (2nd ed.). Springer.
- Sklar, A. (1959). *Fonctions de repartition à n dimensions et leurs marges*. Publ. Inst. Statist. Univ. Paris 8: 229–231.
- Low, R.K.Y.; Alcock, J.; Faff, R.; Brailsford, T. (2013). Canonical vine copulas in modern portfolio management. *Journal of Banking & Finance* 37(8): 3085–3099.
- McNeil, A.J.; Frey, R.; Embrechts, P. (2005). *Quantitative Risk Management*. Princeton.
- Salmon, F. (2009). Recipe for disaster: The formula that killed Wall Street. *Wired*.

## เชื่อมโยง (A-Wiki internal)

- Skill: `monte-carlo-quant-analysis` (`skills/awiki/monte-carlo-quant-analysis/SKILL.md`) §2 distribution selection
- Entity: [[monte-carlo-simulation]] — concept hub
- Source siblings: [[firmai-financial-machine-learning]], [[akashdeepo-monte-carlo-rrr]], [[unpingco-python-stats-ml]]
