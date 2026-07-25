---
type: source
title: "Jump diffusion"
slug: merton-jump-diffusion-wikipedia
date_ingested: 2026-07-24
original_file: raw\merton-jump-diffusion-wikipedia.md
tags: []
---

# Jump diffusion

Source: https://en.wikipedia.org/wiki/Jump_diffusion
Fetched: 2026-07-15 (via web_reader mcp)
License: CC BY-SA 4.0

## Definition

Jump diffusion is a stochastic process that involves jumps and diffusion. It is a type of Lévy process. It has applications in magnetic reconnection, condensed matter physics, pattern theory, and computational vision.

In crystals, atomic diffusion typically consists of jumps between vacant lattice sites. On time and length scales that average over many single jumps, the net motion can be described as regular diffusion.

## In economics and finance

A jump-diffusion model is a form of mixture model, mixing a jump process and a diffusion process. In finance, jump-diffusion models were first introduced by Robert C. Merton (1976). Such models have a range of financial applications from option pricing, to credit risk, to time series forecasting.

### Merton (1976) model

Merton's model extends geometric Brownian motion with a compound Poisson jump component. The asset price S_t evolves according to:

    dS_t / S_t = (μ − λ k) dt + σ dW_t + J dN_t

where:
- μ is the drift (compensated for the expected jump size)
- σ is the diffusion (Brownian) volatility
- W_t is a Wiener process
- N_t is a Poisson process with intensity λ (rate of jump arrival)
- J is the random jump size, typically assumed lognormal: log(1 + J) ~ N(μ_J, σ_J^2)
- k = E[J] = exp(μ_J + σ_J^2 / 2) − 1 is the expected relative jump size
- The (μ − λ k) drift compensation keeps the total expected return equal to μ

Solution over a time horizon T:

    S_T = S_0 · exp[ (μ − σ^2/2 − λ k) T + σ W_T + Σ_{i=1}^{N_T} log(1 + J_i) ]

where N_T ~ Poisson(λ T) is the number of jumps in [0, T].

### Parameters

- **λ (lambda)** — jump intensity (expected number of jumps per unit time). Higher λ → more frequent jumps.
- **μ_J (mu_J)** — mean of log-jump-size (negative for downward jumps).
- **σ_J (sigma_J)** — standard deviation of log-jump-size (jump magnitude dispersion).
- The product λ k captures the average contribution of jumps to total return.

### Variants

- **Merton (1976)**: constant λ, Gaussian jumps. Closed-form European option prices via infinite series.
- **Kou (2002)**: double-exponential jump-size distribution (asymmetric up/down). Captures leptokurtosis + skew with fewer parameters than Gaussian; analytically tractable.
- **Hawkes / self-exciting**: jump intensity λ(t) is itself stochastic and depends on past jumps (clustering of extreme events — financial crises cascade). Calibration harder but captures empirically observed jump clustering.
- **Bates (1996)**: combines Heston stochastic volatility + Merton jumps — most general affine-jump-diffusion for equity.

### Applications

- **Option pricing**: European options under Merton have closed-form infinite-sum Black–Scholes formula (Merton 1976)
- **Credit risk**: jumps model default (Merton structural default + jump-to-default extensions)
- **Time series forecasting**: fat-tailed returns, volatility clustering with Hawkes

### Compared to pure diffusion (GBM)

Pure geometric Brownian motion produces lognormal returns (kurtosis = 3). Adding a jump component produces:
- Heavier tails (kurtosis > 3) — both up and down
- Negative skewness if μ_J < 0 (downside jumps dominate)
- Tail behavior inconsistent with any single parametric distribution — characteristic Lévy signature

This matters for VaR/CVaR estimation: a jump-diffusion MC run will show materially worse deep-tail losses than a same-volatility GBM run.

## References

- Merton, R. C. (1976). "Option pricing when underlying stock returns are discontinuous". Journal of Financial Economics 3 (1–2): 125–144. doi:10.1016/0304-405X(76)90022-2.
- Kou, S. G. (2002). "A Jump-Diffusion Model for Option Pricing". Management Science 48 (8): 1086–1101.
- Bates, D. S. (1996). "Jumps and Stochastic Volatility: Exchange Rate Processes Implicit in Deutsche Mark Options". Review of Financial Studies 9 (1): 69–107.
- Hawkes, A. G. (1971). "Spectra of some self-exciting and mutually exciting point processes". Biometrika 58 (1): 83–90.
- Christensen, H. L. (2012). "Forecasting high-frequency futures returns using online Langevin dynamics". IEEE Journal of Selected Topics in Signal Processing 6 (4): 366–380.
- Grenander, U.; Miller, M. I. (1994). "Representations of Knowledge in Complex Systems". Journal of the Royal Statistical Society, Series B 56 (4): 549–603.
