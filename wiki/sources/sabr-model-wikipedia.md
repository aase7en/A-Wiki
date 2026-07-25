---
type: source
title: "SABR volatility model"
slug: sabr-model-wikipedia
date_ingested: 2026-07-24
original_file: raw\sabr-model-wikipedia.md
tags: []
---

# SABR volatility model

Source: https://en.wikipedia.org/wiki/SABR_volatility_model
Fetched: 2026-07-15 (via web_reader mcp)
License: CC BY-SA 4.0

## Definition

The SABR model is a stochastic volatility model that attempts to capture the volatility smile in derivatives markets. The name stands for "stochastic alpha, beta, rho", referring to the parameters of the model. SABR is widely used by practitioners in the financial industry, especially in interest rate derivative markets. It was developed by Patrick S. Hagan, Deep Kumar, Andrew Lesniewski, and Diana Woodward (2002).

The SABR model describes a single forward F, such as a LIBOR forward rate, a forward swap rate, or a forward stock price. The volatility of the forward is described by a parameter σ. SABR is a dynamic model in which both F and σ are stochastic state variables whose time evolution is given by:

    dF_t = σ_t (F_t)^β dW_t
    dσ_t = α σ_t dZ_t

with the prescribed time-zero values F_0 and σ_0. W_t and Z_t are two correlated Wiener processes with correlation coefficient −1 < ρ < 1:

    dW_t dZ_t = ρ dt

The constant parameters β, α satisfy 0 ≤ β ≤ 1, α ≥ 0.

### Parameter meaning

- **α (alpha)** — vol-of-vol ("volvol"): lognormal volatility of the volatility parameter σ. Controls the curvature of the implied skew.
- **β (beta)** — CEV exponent. Controls the backbone shape:
  - β = 1: lognormal model (Black)
  - β = 0: normal model (Bachelier)
  - β = 1/2: CEV (constant elasticity of variance)
  - 0 < β < 1: intermediate
- **ρ (rho)** — instantaneous correlation between the underlying and its volatility. Controls the slope of the implied skew.
- **ν / σ_0** — initial volatility. Controls the height of the ATM implied volatility level.

The above dynamics is a stochastic version of the CEV model with the skewness parameter β: in fact, it reduces to the CEV model if α = 0.

## Asymptotic solution

For a European option on the forward F struck at K, the implied volatility (lognormal / Black) under SABR is approximately:

    σ_impl = α · [log(F_0/K) / D(ζ)] · { 1 + [(2γ_2 − γ_1^2 + 1/(F_mid)^2)/24 · (σ_0 C(F_mid)/α)^2 + ρ γ_1/4 · σ_0 C(F_mid)/α + (2−3ρ^2)/24] · ε }

where C(F) = F^β, F_mid is a midpoint between F_0 and K, ε = T α^2, and:

    ζ = α / σ_0 · (F_0^(1−β) − K^(1−β)) / (1−β)
    γ_1 = β / F_mid
    γ_2 = −β(1−β) / (F_mid)^2
    D(ζ) = log( (sqrt(1 − 2ρζ + ζ^2) + ζ − ρ) / (1 − ρ) )

The formula is undefined when K = F_0; replace the factor log(F_0/K)/D(ζ) by its limit (1).

The implied **normal** volatility (Bachelier) is:

    σ_impl^n = α · (F_0 − K) / D(ζ) · { 1 + [(2γ_2 − γ_1^2)/24 · (σ_0 C(F_mid)/α)^2 + ρ γ_1/4 · σ_0 C(F_mid)/α + (2−3ρ^2)/24] · ε }

The normal SABR implied volatility is generally somewhat more accurate than the lognormal implied volatility.

## SABR for negative rates

A SABR extension for negative interest rates is the **shifted SABR model**, where the shifted forward rate is assumed to follow a SABR process:

    dF_t = σ_t (F_t + s)^β dW_t
    dσ_t = α σ_t dZ_t

for some positive shift s. Shifted SABR has become market best practice to accommodate negative rates.

Alternative free-boundary form: dF_t = σ_t |F_t|^β dW_t for 0 ≤ β ≤ 1/2, with a free boundary at F = 0.

## Arbitrage problem

Although the asymptotic solution is easy to implement, the density implied by the approximation is not always arbitrage-free, especially for very low strikes (density becomes negative or does not integrate to one). Fixes:
- Stochastic collocation method — project on polynomial of an arbitrage-free variable (Grzelak & Oosterlee 2017)
- PDE solver on equivalent expansion preserving zero-th and first moment (Le Floc'h & Kennedy 2016)

## Simulation

As the stochastic volatility process follows a geometric Brownian motion, its exact simulation is straightforward. However, the simulation of the forward asset process is non-trivial. Taylor-based schemes (Euler–Maruyama, Milstein) are typically used.

## References

- Hagan, Patrick S.; Kumar, Deep; Lesniewski, Andrew S.; Woodward, Diana E. (January 2002). "Managing Smile Risk". Wilmott 1: 84–108.
- Choi, Jaehyuk; Wu, Lixin (July 2021). "The equivalent constant-elasticity-of-variance (CEV) volatility of the stochastic-alpha-beta-rho (SABR) model". Journal of Economic Dynamics and Control 128: 104143.
- Antonov, Alexandre; Konikov, Michael; Spector, Michael (2015). "The Free Boundary SABR: Natural Extension to Negative Rates". SSRN 2557046.
- Grzelak, Lech A.; Oosterlee, Cornelis W. (2017). "From arbitrage to arbitrage-free implied volatilities". Journal of Computational Finance 20 (3): 31–49.
- Le Floc'h, Fabien; Kennedy, Gary (2016). "Finite difference techniques for arbitrage-free SABR". Journal of Computational Finance.
- Leitao, Álvaro; Grzelak, Lech A.; Oosterlee, Cornelis W. (2017). "On an efficient multiple time step Monte Carlo simulation of the SABR model". Quantitative Finance 17 (10): 1549–1565.
