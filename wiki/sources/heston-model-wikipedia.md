---
type: source
title: "Heston model"
slug: heston-model-wikipedia
date_ingested: 2026-07-21
original_file: raw\heston-model-wikipedia.md
tags: []
---

# Heston model

Source: https://en.wikipedia.org/wiki/Heston_model
Fetched: 2026-07-15 (via web_reader mcp)
License: CC BY-SA 4.0

## Mathematical formulation

The Heston model, named after Steven L. Heston, is a mathematical model that describes the evolution of the volatility of an underlying asset. It is a stochastic volatility model: such a model assumes that the volatility of the asset is not constant, nor even deterministic, but follows a random process.

The Heston model assumes that S_t, the price of the asset, is determined by a stochastic process:

    dS_t = μ S_t dt + sqrt(ν_t) S_t dW_t^S

where the volatility sqrt(ν_t) is given by a Feller square-root or CIR process:

    dν_t = κ (θ − ν_t) dt + ξ sqrt(ν_t) dW_t^ν

and W_t^S, W_t^ν are Wiener processes (i.e., continuous random walks) with correlation ρ. The value ν_t, being the square of the volatility, is called the instantaneous variance.

The model has five parameters:
- ν_0: initial instantaneous variance
- θ (theta): long-variance (long-run average of the variance; as t tends to infinity, the expected value of ν_t tends to θ)
- κ (kappa): rate of mean reversion to θ
- ρ (rho): correlation of returns and volatility (typically negative for equities — "leverage effect")
- ξ (xi): vol of vol — the instantaneous volatility of the variance process

### Feller condition

If the parameters obey the following condition (known as the Feller condition) then the process ν_t is strictly positive:

    2 κ θ > ξ^2

When the Feller condition is violated, the variance process can reach zero. In Monte Carlo simulation, Euler–Maruyama discretization can drive ν_t negative; this is typically handled by absorption (max(ν, 0)) or reflection.

## Risk-neutral measure

In the Heston model, there is one asset (volatility is not directly tradeable) but two Wiener processes — one for the stock price and one for the variance of the stock price. The dimension of the set of equivalent martingale measures is one; there is no unique risk-free measure. To pin down a single pricing measure, one adds a volatility-dependent market instrument (e.g., variance swap).

## Implementation notes

- Carr and Madan (1999): Fourier transform to value options under Heston
- Kahl and Jäckel (2005): practical implementation discussion
- Cui et al. (2017): numerically continuous, easily differentiable characteristic function enabling fast, accurate calibration
- Le Floc'h (2018): adaptive Filon quadrature for efficient European option pricing

Calibration is typically formulated as a least squares problem minimizing the squared difference between market and model option prices.

## References

- Heston, Steven L. (1993). "A closed-form solution for options with stochastic volatility with applications to bond and currency options". Review of Financial Studies 6 (2): 327–343.
- Albrecher, H.; Mayer, P.; Schoutens, W.; Tistaert, J. (2007). "The little Heston trap". Wilmott Magazine: 83–92.
- Carr, P.; Madan, D. (1999). "Option valuation using the fast Fourier transform". Journal of Computational Finance 2 (4): 61–73.
- Kahl, C.; Jäckel, P. (2005). "Not-so-complex logarithms in the Heston model". Wilmott Magazine: 74–103.
- Cui, Y.; Del Baño Rollin, S.; Germano, G. (2017). "Full and fast calibration of the Heston stochastic volatility model". European Journal of Operational Research 263 (2): 625–638.
- Le Floc'h, Fabien (2018). "An adaptive Filon quadrature for stochastic volatility models". Journal of Computational Finance 22 (3): 65–88.
