---
type: source
title: "Jump-diffusion variants (Kou / Hawkes / Bates)"
slug: jump-diffusion-variants-wikipedia
date_ingested: 2026-07-24
original_file: raw\jump-diffusion-variants-wikipedia.md
tags: []
---

# Jump-diffusion variants (Kou / Hawkes / Bates)

Source: https://en.wikipedia.org/wiki/Jump_diffusion + https://en.wikipedia.org/wiki/Hawkes_process
        (+ canonical refs Kou 2002, Bates 1996 — see References)
Fetched: 2026-07-15 (via web_reader mcp)
License: CC BY-SA 4.0

## Summary

Three extensions of the Merton (1976) jump-diffusion model that change the
**jump-size distribution**, the **jump-arrival intensity**, or **combine with
stochastic volatility**. The Merton model assumes (i) Gaussian jump sizes and
(ii) constant Poisson intensity. Each variant relaxes one of these to capture
empirical regularities Merton misses:

- **Kou (2002)** — double-exponential (asymmetric Laplace) jump sizes
- **Hawkes (1971)** — self-exciting intensity λ(t) (jumps cluster)
- **Bates (1996)** — Heston SV + Merton jumps (most general equity model)

---

## Kou (2002) — double-exponential jump sizes

The Kou model replaces Merton's Gaussian jump size with a **double-exponential
(asymmetric Laplace)** density:

    f_Y(y) = p · λ₁ · exp(-λ₁ y)       for y ≥ 0
           = (1-p) · λ₂ · exp(λ₂ y)    for y < 0

where p ∈ (0,1) is the probability of an upward jump, and λ₁, λ₂ > 0 are the
rates of the exponential decay on the up and down sides respectively.

**Closed-form moments** (the reason Kou is tractable):

    E[Y]   = p/λ₁ - (1-p)/λ₂
    E[Y²]  = 2[p/λ₁² + (1-p)/λ₂²]
    Var[Y] = E[Y²] - (E[Y])²

**Why Kou over Merton**: the double-exponential captures **leptokurtosis with
fewer parameters** than a Gaussian mixture — the tail decay rate (λ₁, λ₂)
differs on each side, allowing asymmetric crash-vs-rally behavior from a single
jump distribution. Kou (2002) provides a closed-form European option price
(analogous to Merton's infinite-BS sum but with Yiurie-series terms).

**Parameter identifiability**: p, λ₁, λ₂ are weakly identified from return
data alone; maximum-likelihood estimates can be unstable when λ₁ ≈ λ₂ (the
distribution degenerates to a symmetric Laplace). Pin down via option-implied
jumps or high-frequency jump detection (Lee-Mykland 2008).

---

## Hawkes (1971) — self-exciting intensity

A **Hawkes process** is a point process whose intensity λ(t) depends on its
own history:

    λ(t) = λ₀ + Σ_{t_k < t} φ(t - t_k)

where λ₀ > 0 is the baseline (exogenous) intensity and φ(·) ≥ 0 is the
**excitation kernel**. The standard choice is exponential:

    φ(s) = α · exp(-β s),   α, β > 0

so each arrival raises the intensity by α which then decays at rate β.

**Branching ratio** (key stability condition):

    n = ∫₀^∞ φ(s) ds = α/β    (for exponential kernel)

- **n < 1** (stationary): each arrival produces on average fewer than 1
  descendant; process is ergodic with finite long-run intensity
  λ̄ = λ₀/(1-n). **Required for any meaningful long-horizon MC.**
- **n ≥ 1** (explosive): arrivals cascade; intensity diverges. Models of
  financial contagion sometimes use n near 1 (near-critical).

**Cluster property (empirical signature)**: unlike a Poisson process where
arrivals are iid, Hawkes arrivals are **over-dispersed** — the count N(T) in
any interval has Fano factor (Var/E) > 1. For Poisson, Fano = 1 exactly. This
is the empirical reason Hawkes models crises / flash crashes / order-book
cascades better than Merton.

**Exact simulation (Ogata thinning, 1981)**:

    λ* = λ₀ + α  (upper bound on λ between events when α<β)
    t = 0
    while t < T:
        # draw candidate from exponential(λ*)
        t += -log(U₁) / λ*
        if t >= T: break
        # accept with prob λ(t)/λ*
        λ_at_t = λ₀ + α * Σ exp(-β (t - t_k))   over past arrivals t_k
        if U₂ < λ_at_t / λ*:
            emit arrival at t
        # else reject, continue (thinning)

This is the standard exact sampler — produces the true Hawkes distribution
(no time-discretization bias). Used in finance (Bacry et al. 2015) and
seismology (Ogata's original application).

**Why Hawkes over Merton**: Merton assumes jumps arrive at a constant rate,
so two crashes in one week has the same probability as two crashes a year
apart. Hawkes captures **temporal clustering** — a crash today raises the
probability of another crash tomorrow, matching empirical volatility- and
tail-loss clustering (Mandelbrot's "volatility begets volatility").

---

## Bates (1996) — Heston SV + Merton jumps

The Bates model is an **affine jump-diffusion** combining:

1. **Heston (1993) stochastic volatility** — CIR variance process:
       dv_t = κ(θ - v_t) dt + ξ √v_t dW_v(t)
       dS/S = (μ - ½v_t) dt + √v_t dW_s(t),   corr(dW_v, dW_s) = ρ dt

2. **Merton (1976) jump component** — compound Poisson with Gaussian sizes:
       dS/S += J dN(t),   N(t) ~ Poisson(λ),   J ~ N(μ_J, σ_J²)

Drift is compensated by λk (k = exp(μ_J + ½σ_J²) - 1) so total expected
return equals μ — jumps are not "free".

**Why Bates**: it is the **most general** of the standard equity models —
captures both volatility clustering (Heston) AND discontinuous crashes
(Merton). SV-only models (Heston) under-price deep-tail risk because they
produce continuous paths; jump-only models (Merton) miss vol clustering.
Bates is the standard model for **crash-sensitive equity options** (early-
exercise Americans, long-dated deep-OTM puts) where both effects matter.

**Calibration cost**: Bates has 8+ free parameters (κ, θ, ξ, ρ, v₀, λ, μ_J,
σ_J) vs Heston's 5 or Merton's 4 (σ, λ, μ_J, σ_J). Joint calibration is
ill-conditioned — typically fix some params from historical data (e.g. λ
from jump-count estimates) then calibrate the rest to option prices.

**Closed-form**: Bates (1996) gives a European option price via
characteristic-function inversion (extension of Heston's Fourier method with
jump terms added to the CF). No simple closed form — numerical integration.

---

## Comparison

| Model     | Jump size          | Intensity λ(t)            | Vol process  | Closed-form option |
|-----------|--------------------|---------------------------|--------------|--------------------|
| Merton    | Gaussian           | constant                  | constant (GBM) | infinite-BS sum    |
| Kou       | double-exponential | constant                  | constant (GBM) | Yiurie series      |
| Hawkes    | (any)              | self-exciting λ₀+Σαe^(-β) | constant     | simulation-only    |
| Bates     | Gaussian           | constant                  | CIR (Heston) | Fourier inversion  |

## References

- Kou, S. G. (2002). "A jump-diffusion model for option pricing". *Management
  Science* 48(8): 1086-1101.
- Hawkes, A. G. (1971). "Spectra of some self-exciting and mutually exciting
  point processes". *Biometrika* 58(1): 83-90.
- Bates, D. S. (1996). "Jumps and stochastic volatility: exchange rate
  processes implicit in deutsche mark options". *Review of Financial
  Studies* 9(1): 69-107.
- Ogata, Y. (1981). "On Lewis' simulation method for point processes". IEEE
  Trans. Information Theory 27(1): 23-31. [Ogata thinning algorithm]
- Bacry, E.; Mastromatteo, I.; Muzy, J.-F. (2015). "Hawkes processes in
  finance". arXiv:1502.04592 [q-fin.TR].
- Laub, P. J.; Lee, Y.; Taimre, T. (2021). *The Elements of Hawkes
  Processes*. Springer. doi:10.1007/978-3-030-84639-8.
