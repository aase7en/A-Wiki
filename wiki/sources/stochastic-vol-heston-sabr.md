---
type: source
title: "Stochastic volatility (Heston/SABR) — vol-clustering modeling for quant finance"
slug: stochastic-vol-heston-sabr
date_ingested: 2026-07-15
original_file: raw/heston-model-wikipedia.md
additional_sources: [raw/sabr-model-wikipedia.md]
source_url: https://en.wikipedia.org/wiki/Heston_model
domain: trader
tags: [trader, stochastic-vol, heston, sabr, volatility-clustering, quant, risk, option-pricing, feller, cir-process]
confidence: [verified 2026-07-15]
---

# Stochastic volatility (Heston/SABR) — vol-clustering modeling for quant finance

> สรุปจาก Wikipedia "Heston model" + "SABR volatility model" + เชื่อมโยงกับ skill `monte-carlo-quant-analysis`
> §Extensions (Stochastic volatility subsection ใหม่ — J1). [verified 2026-07-15]

## ประเด็นหลัก

1. **Stochastic volatility (SV)** = vol ไม่ใช่ค่าคงที่ แต่เป็น stochastic process ตามด้วย mean-reversion — จับ **volatility clustering** (Mandelbrot 1963: "large changes tend to be followed by large changes") ที่ GBM พลาด
2. **Heston (1993)** — variance ν_t เป็น CIR/Feller square-root process: `dν_t = κ(θ−ν_t)dt + ξ√ν_t dW_t^ν`, สัมพันธ์กับ asset process ผ่าน ρ
3. **SABR (Hagan 2002)** — "stochastic alpha beta rho" — σ_t เป็น lognormal process: `dσ_t = ασ_t dZ_t`; β exponent เลือก backbone (lognormal/normal/CEV)
4. **Feller condition**: `2κθ > ξ²` รับประกัน ν_t > 0 เสมอ ถ้าผิดเงื่อนไข Euler–Maruyama MC ให้ค่าติดลบ → แก้ด้วย absorption (max(ν,0)) หรือ reflection
5. **Fat tails**: SV ทำให้ returns มี kurtosis > 3 แม้ marginal เป็น normal — จำเป็นสำหรับ deep-tail risk (VaR 99%+)

## ข้อมูลที่น่าสนใจ

### Heston model (mean-reverting equity vol)

SDE pair ที่กำหนดราคา + variance:

```
dS_t = μ S_t dt + √ν_t S_t dW_t^S            (asset price, GBM ที่ vol เป็น stochastic)
dν_t = κ (θ − ν_t) dt + ξ √ν_t dW_t^ν          (variance, CIR process)

โดยที่:
  ν_0  = initial variance
  θ    = long-run variance (mean-reversion target)
  κ    = mean-reversion speed (สูง → กลับสู่ θ เร็ว)
  ρ    = correlation ระหว่าง price-shock และ vol-shock
         (equity: ปกติ ρ < 0 "leverage effect" — price ตก → vol ขึ้น)
  ξ    = vol-of-vol (volatility ของตัว variance process เอง)
```

**Feller condition**: `2 κ θ > ξ²` — รับประกัน ν_t > 0 ตลอดเวลา (CIR process ไม่ cross zero)

**Risk-neutral ambiguity**: SV มี 2 Wiener แต่ tradeable asset มี 1 (vol ไม่ได้ซื้อขายตรงๆ) → market price of volatility risk ไม่ unique → ต้องใช้ instrument เสริม (เช่น variance swap) เพื่อ pin down pricing measure

### SABR model (rates/FX/forward — Hagan 2002)

```
dF_t = σ_t (F_t)^β dW_t        (forward F, CEV backbone)
dσ_t = α σ_t dZ_t              (σ = lognormal vol, "stochastic alpha")

dW_t dZ_t = ρ dt               (correlation ระหว่าง underlying + vol)
```

**พารามิเตอร์ 4 ตัว:**

| พารามิเตอร์ | ความหมาย | Effect บน implied vol surface |
|-------------|----------|-------------------------------|
| **α** | vol-of-vol (volvol) | curvature ของ skew (smile convexity) |
| **β** | CEV exponent — backbone shape | slope ที่ ATM (forward level) |
| **ρ** | correlation underlying-vol | slope ของ implied skew |
| **σ_0 / ν** | initial volatility | level ของ ATM implied vol |

**β กำหนด backbone:**
- β = 1 → lognormal (Black) — ATM vol flat
- β = 0 → normal (Bachelier) — ใช้กับ negative rates
- β = 1/2 → CEV (constant elasticity of variance)
- 0 < β < 1 → intermediate

**Hagan 2002 closed-form (asymptotic) implied vol:**

```
σ_impl(K, T) ≈ α · [log(F_0/K) / D(ζ)] · {1 + correction(γ_1, γ_2, ρ, α, T)}

ζ      = α/σ_0 · (F_0^(1−β) − K^(1−β)) / (1−β)
γ_1    = β / F_mid
γ_2    = −β(1−β) / F_mid²
D(ζ)   = log[(√(1−2ρζ+ζ²) + ζ − ρ) / (1−ρ)]
```

ถ้า K = F_0 (ATM) ให้แทน factor `log(F_0/K)/D(ζ)` ด้วย limit 1.

### เปรียบเทียบ Heston vs SABR vs GARCH

| Aspect | **Heston** | **SABR** | **GARCH(p,q)** |
|--------|-----------|----------|----------------|
| Domain | equity, index | rates, FX, forward | time-series econometrics |
| Vol process | CIR (mean-reverting) | lognormal (no mean reversion) | discrete-time ARMA-GARCH |
| Closed-form option | Heston 1993 (Fourier) | Hagan 2002 (asymptotic) | typically simulation-only |
| Jump-diffusion extension | Bates 1996 (Heston + Merton) | N/A | GARCH-J |
| Calibration | 5 params (ν_0, θ, κ, ρ, ξ) | 4 params (α, β, ρ, σ_0) | p+q+1 params |
| Negative rates support | via shifted Heston | via shifted SABR (free boundary) | N/A |

### Arbitrage risk ใน SABR asymptotic formula

Hagan 2002 implied vol approximation **not always arbitrage-free** สำหรับ deep OTM strikes — density implied อาจเป็นลบหรือ integrate ≠ 1. แก้:
- **Stochastic collocation** (Grzelak–Oosterlee 2017) — project on polynomial of arbitrage-free variable
- **PDE solver** (Le Floc'h–Kennedy 2016) — preserve 0th + 1st moment

## ข้อควรระวัง

- **Feller violation** — ถ้า `2κθ ≤ ξ²` แล้ว Euler–Maruyama MC ให้ ν < 0 → ใช้ absorption `v = max(v, 0)` หรือ reflection; ทำให้ long-run mean deviate จาก θ
- **Calibration instability** — Heston 5 params มี manifold of near-equivalent fits (Levenberg–Marquardt may land in local min); calibrate ด้วย multiple starting points + global optimizer (differential evolution)
- **ρ sign ambiguity** — equity (leverage) ρ < 0, FX ρ ≈ 0, rates SABR ρ < 0 (skew); ใส่ผิดเครื่องหมาย → skew กลับด้าน
- **SABR asymptotic breakdown** — accuracy ลดเมื่อ T ใหญ่ หรือ strike ห่างจาก ATM; Hagan formula เป็น leading-order only
- **SV ไม่ catch jumps** — Heston/SABR เป็น continuous process ทั้งคู่; วิกฤตที่มี discontinuous crashes (1987, 2008, 2020-COVID) ต้องใช้ jump-diffusion (Merton) หรือ Bates (Heston+Merton)

## เชื่อมโยงกับ skill monte-carlo-quant-analysis

skill §Extensions (J1 ใหม่) ครอบคลุม:
- Heston Euler–Maruyama discretization code (`v_path(κ, θ, ξ, dt, n, rng)` + `asset_path`)
- SABR implied-vol approximation code (Hagan 2002)
- **Math invariant** test: `tests/test_monte_carlo_stochastic_vol.py` — pin 3 properties:
  1. Long-run mean → θ (mean reversion)
  2. Feller condition → ν ≥ 0
  3. SV → kurtosis > 3 (fat tails)

**Decision rule ใน skill workflow:**
- baseline: constant-vol GBM (เร็ว, ง่าย, แต่ under-estimate tails + ไม่จับ vol clustering)
- risk-sensitive equity: Heston (mean-reverting, leverage ρ < 0)
- rates/FX forward: SABR (CEV backbone, capture skew + negative-rate extension)
- + jump risk: Bates (Heston + Merton)

## References

- Heston, Steven L. (1993). "A closed-form solution for options with stochastic volatility with applications to bond and currency options". *Review of Financial Studies* 6 (2): 327–343.
- Hagan, Patrick S.; Kumar, Deep; Lesniewski, Andrew S.; Woodward, Diana E. (2002). "Managing Smile Risk". *Wilmott Magazine* 1: 84–108.
- Bates, D. S. (1996). "Jumps and Stochastic Volatility: Exchange Rate Processes Implicit in Deutsche Mark Options". *Review of Financial Studies* 9 (1): 69–107.
- Mandelbrot, B. (1963). "The Variation of Certain Speculative Prices". *Journal of Business* 36 (4): 394–419.
- Carr, P.; Madan, D. (1999). "Option valuation using the fast Fourier transform". *Journal of Computational Finance* 2 (4): 61–73.
- Grzelak, L.A.; Oosterlee, C.W. (2017). "From arbitrage to arbitrage-free implied volatilities". *Journal of Computational Finance* 20 (3): 31–49.
- Cui, Y.; Del Baño Rollin, S.; Germano, G. (2017). "Full and fast calibration of the Heston stochastic volatility model". *European Journal of Operational Research* 263 (2): 625–638.

## เชื่อมโยง (A-Wiki internal)

- Skill: `monte-carlo-quant-analysis` (`skills/awiki/monte-carlo-quant-analysis/SKILL.md`) §Extensions Stochastic volatility
- Entity: [[monte-carlo-simulation]] — concept hub
- Source siblings: [[copula-multivariate-finance]], [[firmai-financial-machine-learning]], [[akashdeepo-monte-carlo-rrr]], [[unpingco-python-stats-ml]]
- Test (math invariant): `tests/test_monte_carlo_stochastic_vol.py` (J1-b)
