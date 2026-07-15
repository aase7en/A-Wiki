---
type: source
title: "Merton jump-diffusion model — discontinuous price paths for quant finance"
slug: merton-jump-diffusion
date_ingested: 2026-07-15
original_file: raw/merton-jump-diffusion-wikipedia.md
source_url: https://en.wikipedia.org/wiki/Jump_diffusion
domain: trader
tags: [trader, merton, jump-diffusion, compound-poisson, fat-tail, levy-process, quant, risk, var]
confidence: [verified 2026-07-15]
---

# Merton jump-diffusion model — discontinuous price paths for quant finance

> สรุปจาก Wikipedia "Jump diffusion" + เชื่อมโยงกับ skill `monte-carlo-quant-analysis`
> §Extensions (Jump-diffusion subsection ใหม่ — J2). [verified 2026-07-15]

## ประเด็นหลัก

1. **Jump diffusion** = stochastic process ที่ผสม diffusion (Brownian) + jump process (compound Poisson) — เป็น Lévy process ตาม classification ทางคณิตศาสตร์
2. **Merton (1976)** แนะนำใน finance: extends GBM ด้วย jump component `dS/S = (μ−λk)dt + σdW + JdN` — จับ **discontinuous crashes** (1987 Black Monday, 2008, 2020-COVID) ที่ continuous-path models พลาด
3. **Compound Poisson**: จำนวน jumps `N_T ~ Poisson(λT)`, jump size `J ~ N(μ_J, σ_J²)` — λ = jump intensity, k = E[J] expected relative jump size
4. **Drift compensation**: drift term ลดด้วย `λk` เพื่อให้ expected return รวมยังเท่ากับ μ (jumps ไม่ "ฟรี")
5. **Fat tails**: jump component ทำให้ returns kurtosis > 3 (heavier than normal) — critical สำหรับ deep-tail VaR (99%+)

## ข้อมูลที่น่าสนใจ

### Merton (1976) SDE

```
dS_t / S_t = (μ − λ k) dt + σ dW_t + J dN_t

โดยที่:
  μ    = drift (annualized)
  σ    = diffusion volatility (Brownian component)
  W_t  = Wiener process
  N_t  = Poisson process with intensity λ (jump arrival rate)
  J    = random jump size (lognormal: log(1+J) ~ N(μ_J, σ_J²))
  k    = E[J] = exp(μ_J + σ_J²/2) − 1   (expected relative jump size)
```

**Solution over [0, T]:**

```
S_T = S_0 · exp[ (μ − σ²/2 − λk) T + σ W_T + Σ_{i=1}^{N_T} log(1 + J_i) ]

โดย N_T ~ Poisson(λT) = จำนวน jumps ใน [0, T]
แต่ละ jump เป็นอิสระ N(μ_J, σ_J²)
```

### Parameters

| พารามิเตอร์ | ความหมาย | Effect |
|-------------|----------|--------|
| **λ** | jump intensity (jumps/unit time) | สูง → jumps บ่อย; crash risk สูง |
| **μ_J** | mean log-jump-size | ลบ → downside jumps dominate (negative skew) |
| **σ_J** | std log-jump-size | สูง → jump sizes กระจายมาก (uncertain magnitude) |
| **k = E[J]** | expected relative jump | drift compensation = λk |

### Variant families

| โมเดล | λ | Jump size | ใช้เมื่อ |
|-------|---|-----------|---------|
| **Merton (1976)** | constant | Gaussian (lognormal) | baseline, closed-form option |
| **Kou (2002)** | constant | double-exponential (asymmetric) | leptokurtosis + skew น้อย params |
| **Hawkes / self-exciting** | stochastic, jump-dependent | (any) | clustered jumps (financial crises cascade) |
| **Bates (1996)** | constant | Gaussian | Heston SV + Merton jumps (most general affine-jump) |

### Closed-form European option (Merton 1976)

European call under Merton = infinite sum ของ Black-Scholes terms:

```
C_Merton = Σ_{n=0}^∞ [ e^{-λT} (λT)^n / n! · C_BS(S_0 e^{n μ_J + n σ_J²/2 − λk T}, σ_n) ]

โดย σ_n² = σ² + n σ_J² / T
```

Practical: truncate ที่ n=20-50 (probability ของ n > 20 negligible สำหรับ λT ≤ 5)

### เปรียบเทียบ vs pure GBM

| Property | **GBM** | **Merton jump-diffusion** |
|----------|---------|--------------------------|
| Returns distribution | lognormal | lognormal + jump mixture |
| Kurtosis | 3 (normal) | > 3 (fat tails) |
| Skewness | 0 | < 0 if μ_J < 0 (downside) |
| Sample paths | continuous | discontinuous (jumps) |
| Closed-form Euro option | Black-Scholes | infinite BS sum |
| Tail behavior | exponential decay | power-law-like (heavier) |
| Captures crashes (1987/2008/2020) | ❌ | ✅ (with λ > 0) |

## ข้อควรระวัง

- **λ calibration sensitive** — λ และ σ_J มี manifold of near-equivalent fits (jumps น้อยใหญ่ ↔ jumps บ่อยเล็ก) ต้องใช้ long history + options-implied
- **Jump-size identifiability** — μ_J, σ_J ยาก fit จาก returns อย่างเดียว (jumps ผสม diffusion); ใช้ options data + filtering (Aït-Sahalia)
- **Discretization** — Euler–Maruyama ต้องการ dt เล็กพอ (jumps หลายครั้งใน 1 step → undercount); ทางที่ดีคือ simulate jump times ตรงๆ (exact Poisson) แทน discretize
- **MC variance** — jump component เพิ่ม variance; ใช้ QMC หรือ Importance Sampling ช่วยได้
- **Risk-neutral drift** — Girsanov + jump-compensated measure เปลี่ยน μ → r แต่ λ, μ_J, σ_J **not** uniquely identified by no-arbitrage (jump risk premium)

## เชื่อมโยงกับ skill monte-carlo-quant-analysis

skill §Extensions (J2 ใหม่) ครอบคลุม:
- Merton sampler code (Poisson(λT) jumps + Brownian diffusion)
- Family table (Merton/Kou/Hawkes/Bates)
- **Math invariant** test: `tests/test_monte_carlo_jump_diffusion.py` — pin 3 properties:
  1. Returns kurtosis > 3 (jump-induced fat tails)
  2. λ=0 recovers GBM (mean/variance tolerance 2%)
  3. Jump component worsens VaR(5%) vs pure GBM at same σ

**Decision rule ใน skill workflow:**
- baseline: GBM (continuous, fast, under-estimates crash risk)
- + discontinuous risk: Merton (constant λ, Gaussian jumps)
- + jump clustering: Hawkes (self-exciting, ใช้ใน crisis modeling)
- + vol clustering + jumps: Bates (Heston + Merton)

## References

- Merton, R. C. (1976). "Option pricing when underlying stock returns are discontinuous". *Journal of Financial Economics* 3 (1–2): 125–144.
- Kou, S. G. (2002). "A Jump-Diffusion Model for Option Pricing". *Management Science* 48 (8): 1086–1101.
- Bates, D. S. (1996). "Jumps and Stochastic Volatility: Exchange Rate Processes Implicit in Deutsche Mark Options". *Review of Financial Studies* 9 (1): 69–107.
- Hawkes, A. G. (1971). "Spectra of some self-exciting and mutually exciting point processes". *Biometrika* 58 (1): 83–90.
- Cont, R.; Tankov, P. (2004). *Financial Modelling with Jump Processes*. Chapman & Hall/CRC.
- Aït-Sahalia, Y.; Cacho-Diaz, J.; Hurd, T. (2009). "Portfolio choice with jumps: A closed-form solution". *Annals of Applied Probability* 19 (2): 556–584.

## เชื่อมโยง (A-Wiki internal)

- Skill: `monte-carlo-quant-analysis` (`skills/awiki/monte-carlo-quant-analysis/SKILL.md`) §Extensions Jump-diffusion
- Entity: [[monte-carlo-simulation]] — concept hub
- Source siblings: [[copula-multivariate-finance]], [[stochastic-vol-heston-sabr]] (Bates = Heston + Merton), [[firmai-financial-machine-learning]], [[akashdeepo-monte-carlo-rrr]], [[unpingco-python-stats-ml]]
- Test (math invariant): `tests/test_monte_carlo_jump_diffusion.py` (J2-b)
