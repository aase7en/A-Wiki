---
type: source
title: "Jump-diffusion variants (Kou/Hawkes/Bates) — tail-structure extensions beyond Merton"
slug: jump-diffusion-variants
date_ingested: 2026-07-15
original_file: raw/jump-diffusion-variants-wikipedia.md
additional_sources: [raw/merton-jump-diffusion-wikipedia.md, raw/heston-model-wikipedia.md]
source_url: https://en.wikipedia.org/wiki/Jump_diffusion
domain: trader
tags: [trader, kou, hawkes, bates, jump-diffusion, double-exponential, self-exciting, fat-tail, quant, risk, option-pricing]
confidence: [verified 2026-07-15]
---

# Jump-diffusion variants (Kou / Hawkes / Bates)

แหล่งรวบรวม 3 extensions ของ Merton (1976) ที่ผ่อนปรน assumptions อย่างน้อยหนึ่งข้อ:
Gaussian jump size หรือ constant Poisson intensity. ดูทฤษฎีเต็ม + SDE + variants
table ใน [[merton-jump-diffusion]] (baseline) และ [[stochastic-vol-heston-sabr]]
(Heston SV ที่ Bates ใช้).

## ประเด็นหลัก

| Variant | สิ่งที่ relax | เหตุผลเชิงประจักษ์ | Use case |
|---------|---------------|---------------------|----------|
| **Kou (2002)** | jump size → double-exp | leptokurtosis + asymmetric crash/rally ในพารามิเตอร์น้อย | equity ที่ skew สำคัญ |
| **Hawkes (1971)** | intensity → self-exciting | crises cluster (volatility begets volatility) | flash crash, contagion |
| **Bates (1996)** | + Heston SV | ทั้ง vol clustering AND crashes สำคัญ | crash-sensitive deep-OTM options |

## Kou (2002) — double-exponential jump sizes

แทน Gaussian jump size ด้วย **double-exponential (asymmetric Laplace)** density:

    f_Y(y) = p · λ₁ · exp(-λ₁ y)        for y ≥ 0      (up jump, prob p)
           = (1-p) · λ₂ · exp(λ₂ y)     for y < 0       (down jump, prob 1-p)

**Closed-form moments** (เหตุผลที่ Kou tractable):

    E[Y]   = p/λ₁ - (1-p)/λ₂
    E[Y²]  = 2[p/λ₁² + (1-p)/λ₂²]
    Var[Y] = E[Y²] - (E[Y])²

เลือกเมื่อ tail decay rate ต่างกันสองฝั่ง (crash ลึกแต่ rally ตื้น หรือกลับกัน) จาก
พารามิเตอร์เดียว — Gaussian ต้องใช้ mixture หลายตัวถึงจะจับ asymmetry ได้.
Kou (2002) ให้ closed-form European option (Yiurie series) เหมือน Merton.

**ข้อควรระวัง**: p/λ₁/λ₂ 识别 ยากจาก return data อย่างเดียว (identifiability ต่ำ);
MLE ไม่เสถียรเมื่อ λ₁ ≈ λ₂. ใช้ option-implied jumps หรือ Lee-Mykland (2008)
high-frequency jump detection เพื่อ pin down.

## Hawkes (1971) — self-exciting intensity

Point process ที่ intensity λ(t) พึ่งพาประวัติตัวเอง:

    λ(t) = λ₀ + Σ_{t_k < t} α · exp(-β (t - t_k))

- **λ₀** = baseline (exogenous) intensity
- **α** = excitation magnitude (แต่ละ arrival ยก intensity ขึ้น α)
- **β** = decay rate

**Branching ratio** `n = α/β` — เงื่อนไขเสถียรภาพ:
- **n < 1** (stationary): long-run intensity λ̄ = λ₀/(1-n). **จำเป็นสำหรับ long-horizon MC.**
- **n ≥ 1** (explosive): intensity diverges — ใช้จำลอง contagion ระยะสั้นเท่านั้น

**Cluster signature (Fano factor)**: ต่างจาก Poisson (arrivals iid), Hawkes
arrivals over-dispersed — N(T) มี Fano factor (Var/E) > 1. Poisson = 1 เป๊ะ.
นี่คือเหตุผล Hawkes จับ crises/flash-crash/order-book cascade ได้ดีกว่า Merton.

**Exact simulation — Ogata thinning (1981)**:

```python
def hawkes_jump_times(lam0, alpha, beta, T, rng):
    """Sample Hawkes jump times on [0,T] via Ogata thinning (exact).

    Requires alpha < beta for stationarity (lam* = lam0 + alpha is a valid
    upper bound).  Returns sorted array of arrival times.
    """
    lam_star = lam0 + alpha
    t = 0.0
    arrivals = []
    while t < T:
        t += -np.log(rng.uniform()) / lam_star  # exponential(lam*) candidate
        if t >= T:
            break
        # intensity at candidate time = lam0 + sum of decayed excitations
        lam_at_t = lam0 + alpha * sum(np.exp(-beta * (t - tk)) for tk in arrivals)
        if rng.uniform() < lam_at_t / lam_star:
            arrivals.append(t)
        # else reject (thinning)
    return np.array(arrivals)
```

ใช้ใน finance (Bacry et al. 2015 market microstructure) และ seismology (Ogata
original). เลือกเมื่อ temporal clustering ของ jumps สำคัญ (crises cascade);
ไม่เลือกเมื่อ jumps iid พอ (short horizon ไม่มี cascade evidence).

## Bates (1996) — Heston SV + Merton jumps

**Affine jump-diffusion** ที่ combine:

1. **Heston (1993) SV** — CIR variance + correlated asset (ดู
   [[stochastic-vol-heston-sabr]]):
       dv_t = κ(θ - v_t) dt + ξ √v_t dW_v(t)
       dS/S = (μ - ½v_t) dt + √v_t dW_s(t),   ρ = corr(dW_v, dW_s)

2. **Merton (1976) jumps** — compound Poisson + Gaussian (ดู
   [[merton-jump-diffusion]]):
       dS/S += J dN(t),   N ~ Poisson(λ),   J ~ N(μ_J, σ_J²)

Drift compensated by λk เหมือน Merton เพื่อให้ E[return] = μ.

**เลือก Bates เพราะ** = most general standard equity model — จับทั้ง volatility
clustering (Heston) AND discontinuous crashes (Merton). SV-only (Heston)
under-price deep-tail เพราะ path continuous; jump-only (Merton) พลาด vol
clustering. Bates = standard สำหรับ crash-sensitive equity options
(long-dated deep-OTM puts, early-exercise Americans) ที่ทั้งสอง effect สำคัญ.

**ข้อควรระวัง**: 8+ พารามิเตอร์ (κ, θ, ξ, ρ, v₀, λ, μ_J, σ_J) vs Heston 5 / Merton 4.
Joint calibration ill-conditioned — fix λ จาก jump-count estimates ก่อนแล้วค่อย
calibrate ที่เหลือกับ option prices. European option price ผ่าน Fourier inversion
(Bates 1996) — ไม่มี closed form ง่าย, ใช้ numerical integration.

## Comparison

| โมเดล | Jump size | Intensity λ(t) | Vol process | Closed-form option |
|-------|-----------|----------------|-------------|--------------------|
| **Merton** | Gaussian | constant | constant (GBM) | infinite-BS sum |
| **Kou** | double-exponential | constant | constant (GBM) | Yiurie series |
| **Hawkes** | (any) | self-exciting λ₀+Σαe^(-β·) | constant | simulation-only |
| **Bates** | Gaussian | constant | CIR (Heston) | Fourier inversion |

## ข้อควรระวัง

- **Kou identifiability**: p/λ₁/λ₂ 识别 ยาก โดยเฉพาะเมื่อ λ₁ ≈ λ₂ (degenerate to
  symmetric Laplace). ใช้ high-frequency jump detection (Lee-Mykland 2008)
  เพื่อ constrain.
- **Hawkes stationarity**: ต้องตรวจ α < β (branching ratio < 1) ทุกครั้งก่อน
  long-horizon MC; ถ้า α ≥ β intensity diverges และผล MC ไร้ความหมาย.
- **Bates param explosion**: 8+ params calibration ใช้ historical estimate +
  option-implied ร่วมกัน; pure option-fit overfits.
- **ทุก model ใช้ MC เพื่อ path-dependent payoffs** (American, barrier, Asian) —
  closed-form มีเฉพาะ European.

## เชื่อมโยงกับ skill

skill `monte-carlo-quant-analysis` §Extensions — `### Jump-diffusion variants
(Bates/Kou/Hawkes)` subsection (L1/L2/L3) ครอบคลุม code pattern สำหรับทั้งสาม +
math invariant tests (`tests/test_monte_carlo_bates.py`,
`test_monte_carlo_kou.py`, `test_monte_carlo_hawkes.py`).

ดูเพิ่ม:
- [[merton-jump-diffusion]] — baseline (Gaussian jumps, constant λ)
- [[stochastic-vol-heston-sabr]] — Heston CIR variance process (ที่ Bates reuse)
- [[monte-carlo-simulation]] — entity page

## References

- Kou, S. G. (2002). "A jump-diffusion model for option pricing". *Management
  Science* 48(8): 1086-1101.
- Hawkes, A. G. (1971). "Spectra of some self-exciting and mutually exciting
  point processes". *Biometrika* 58(1): 83-90.
- Bates, D. S. (1996). "Jumps and stochastic volatility: exchange rate
  processes implicit in deutsche mark options". *Review of Financial Studies*
  9(1): 69-107.
- Ogata, Y. (1981). "On Lewis' simulation method for point processes". *IEEE
  Trans. Information Theory* 27(1): 23-31.
- Bacry, E.; Mastromatteo, I.; Muzy, J.-F. (2015). "Hawkes processes in
  finance". arXiv:1502.04592.
- Lee, S. S.; Mykland, P. A. (2008). "Jumps in financial markets: a new
  nonparametric test and jump dynamics". *Review of Financial Studies* 21(6).
