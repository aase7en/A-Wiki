---
type: source
title: "Copula (probability theory) — multivariate dependency modeling for quant finance"
slug: copula-multivariate-finance
date_ingested: 2026-07-14
original_file: raw/copula-wikipedia.md
additional_sources: [raw/vine-copula-wikipedia.md]
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
- **Vine copulas** (pair copulas): flexible สำหรับ high-dimensional portfolios — ดู subsection เฉพาะด้านล่าง

### Vine copulas (pair-copula constructions)

สำหรับ **d ≥ 5** assets, single multivariate copula (Gaussian/Student-t) มีข้อจำกัด:
impose dependence structure เดียวทั้ง portfolio, จำกัดในการจับ asymmetric tail.
**Vine copulas** แก้โดย decompose d-dimensional density เป็น d(d-1)/2 bivariate copulas
บน conditional distributions (pair-copula construction, Joe 1996 / Bedford-Cooke 2002) —
scale ไป high dimensions โดยไม่ต้อง assume single correlation matrix.

| Type | โครงสร้าง tree | เลือกเมื่อ | ตัวอย่าง use |
|------|----------------|-----------|--------------|
| **C-vine** (canonical) | star: root หนึ่งตัวต่อ tree | มี asset ที่ dominate (market index, factor) | equity portfolio มี SPY เป็นหัวใจ |
| **D-vine** (drawable) | path: sequential ordering | time-series มี temporal order | yield curve (maturities เรียงตามเวลา) |
| **R-vine** (regular) | ทั่วไปที่สุด (nested tree) | dependence structure ซับซ้อน ไม่มี root ชัด | multi-asset class portfolio |

**Pair-copula formula:**

    f(x₁,...,x_d) = Πᵢ fᵢ(xᵢ) · Π_{e∈E(V)} c_{e₁,e₂|D_e}(F_{e₁|D_e}, F_{e₂|D_e})

โดย E(V) = edges ของ vine tree, D_e = conditioning set ของ edge e. Simplifying assumption
(constant conditional copulas) ใช้บ่อยใน application ลด parameter count.

**Truncated vines**: independence copulas ใน tree ลำดับสูง → encode conditional independence
→ ลด parameter count สำหรับ d ใหญ่มาก (เช่น 50+ assets). เลือกตัวแปรที่ strong dependence
ไว้ tree ต่ำเพื่อ higher-order trees มี dependence เบาบาง (truncation เหมาะ).

[verified 2026-07-15] — raw provenance: `raw/vine-copula-wikipedia.md` (Wikipedia CC BY-SA).
Portfolio evidence: Low et al. (2013) แสดง Clayton canonical vine outperform Gaussian/Student-t
ใน downside risk management สำหรับ international equity portfolios.

**Python tooling**: `VineCopula` (R package, Schepsmeier et al. 2014 — production-grade);
ใน Python `copulae` package มี vine support; scipy ไม่มี native (ใช้ manual pair-copula
construction หรือ R binding). ดู `[[model-capability-bench]]` สำหรับ routing เมื่อ d ใหญ่.

### Python library comparison (K5)

[verified 2026-07-15] — เปรียบเทียบ 4 ทางเลือกสำหรับ copula work ใน Python.

| Library | Vine (C/D/R) | Archimedean | Gaussian/Student-t | Install | ใช้เมื่อ |
|---------|:---:|:---:|:---:|---------|---------|
| **`scipy.stats`** | ❌ manual pair-copula | ❌ (Cholesky trick only) | ✅ via `multivariate_normal` | มีอยู่แล้ว (requirements-optional) | baseline, bivariate Gaussian/Clayton เดียว |
| **`copulae`** (Bokofer) | ✅ native C/D/R-vine | ✅ all (Clayton/Gumbel/Frank/Joe) | ✅ | `pip install copulae` | production vine fitting, multi-family portfolio |
| **`pyvinecopulib`** | ✅ R-binding (`VineCopula`) | ✅ | ✅ | `pip install pyvinecopulib` (needs R deps) | R interop, fitting speed, cutting-edge vine research |
| **`statsmodels`** | ❌ | ⚠️ Gaussian + Elliptical (limited) | ✅ | `pip install statsmodels` | regression-copula hybrid (copula + GLM) |

**Decision rule:**
- **scipy-only** (default ใน A-Wiki MC skill + tests) — เพียงพอสำหรับ 2-3 assets, bivariate Gaussian/Clayton, และ math-invariant testing. ไม่ต้อง install เพิ่ม.
- **`copulae`** — production vine fitting (d ≥ 5), ต้องการ Archimedean families หลายตัวพร้อมกัน.
- **`pyvinecopulib`** — R interop, ใช้ cutting-edge VineCopula features (truncated vines, non-parametric).
- **`statsmodels`** — copula-regression hybrids (GLM + copula for residuals).

**A-Wiki convention**: tests/skill ใช้ scipy-only (mirror H6 pattern — `pytest.importorskip("scipy")`,
test-local samplers). ถ้าต้องการ production vine fitting ในอนาคต → eval `copulae` ใน `drive/`
private workspace ก่อน promote เป็น skill dependency (Brain Improvement Gate: cost-first).

ดู `[[model-capability-bench]]` สำหรับ routing เมื่อ d ใหญ่.

**เชื่อมโยงกับ skill**: skill `monte-carlo-quant-analysis` §Copula subsection ครอบคลุม
Gaussian/Student-t/Clayton/Gumbel (baseline + tail). Vine = extension เมื่อ dimension สูง
(d ≥ 5) ที่ single copula ไม่พอ — เลือกเมื่อ portfolio มี assets หลายประเภทต่าง dependence regime.

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
