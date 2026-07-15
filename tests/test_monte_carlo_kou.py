"""Integration tests bridging Kou (2002) double-exponential jump theory
(wiki/sources/jump-diffusion-variants.md) and the Monte Carlo practice skill
(skills/awiki/monte-carlo-quant-analysis §Extensions — L2 Jump-diffusion
variants subsection).

L2: the SKILL.md Merton family table names "Kou (2002)" with "double-
exponential" jump size but ships no code. These tests pin the mathematical
invariants a Kou MC sampler MUST satisfy, so that the code added to the skill
(L2 SKILL subsection) can be validated against them.

Kou replaces Merton's Gaussian jump size with a double-exponential (asymmetric
Laplace) density. Closed-form moments make it tractable and verifiable:

    f_Y(y) = p·λ₁·exp(-λ₁ y)        for y ≥ 0
           = (1-p)·λ₂·exp(λ₂ y)     for y < 0
    E[Y]   = p/λ₁ - (1-p)/λ₂
    E[Y²]  = 2[p/λ₁² + (1-p)/λ₂²]
    Var[Y] = E[Y²] - (E[Y])²

Drift compensation for the asset SDE uses k = E[exp(Y)-1] (NOT E[Y]); for Kou
this has closed form k = pλ₁/(λ₁-1) + (1-p)λ₂/(λ₂+1) - 1  (requires λ₁>1).

Scipy-only. Samplers live in-test. [verified 2026-07-15] scipy 1.17.1, numpy
2.4.6, fixed seeds. Prototype run BEFORE assertions (H6 discipline): mean
ratio 0.999, var ratio 1.001, jump excess kurtosis 4.15 — all confirmed.
"""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("scipy")
from scipy import stats  # noqa: E402

# Kou params — asymmetric: up jumps rare (p=0.3) + small (λ₁=10 fast decay),
# down jumps more frequent (1-p=0.7) + larger (λ₂=5 slower decay).
# Chosen for (a) clear downside bias, (b) λ₁>1 so drift-compensation k is finite.
P = 0.3
LAM1 = 10.0   # up-jump rate
LAM2 = 5.0    # down-jump rate
LAMBDA = 5.0  # Poisson intensity (jumps/year)
MU = 0.05
SIGMA = 0.2
T = 1.0


def kou_jump_sizes(n: int, p: float, lam1: float, lam2: float,
                   rng: np.random.Generator) -> np.ndarray:
    """Sample n iid Kou (double-exponential) jump sizes.

    Density: with prob p draw +Exp(λ₁), else -Exp(λ₂).
    numpy's rng.exponential(scale) uses scale = 1/rate, so scale=1/λ.
    """
    signs = np.where(rng.uniform(size=n) < p, 1.0, -1.0)
    mags_pos = rng.exponential(scale=1.0 / lam1, size=n)
    mags_neg = rng.exponential(scale=1.0 / lam2, size=n)
    return signs * np.where(signs > 0, mags_pos, mags_neg)


def kou_log_returns(mu, sigma, lam, p, lam1, lam2, T, n_paths, rng):
    """Kou-driven asset log-returns over [0,T]: GBM diffusion + Poisson(λT)
    Kou jumps per path, drift-compensated by k=E[exp(Y)-1]."""
    # Drift compensation: k = E[exp(Y)-1] (closed form for Kou, requires λ₁>1)
    k = p * lam1 / (lam1 - 1.0) + (1 - p) * lam2 / (lam2 + 1.0) - 1.0
    drift = (mu - 0.5 * sigma * sigma - lam * k) * T
    diffusion = sigma * np.sqrt(T) * rng.standard_normal(n_paths)

    n_jumps = rng.poisson(lam * T, size=n_paths)
    jump_sums = np.zeros(n_paths)
    for i in range(n_paths):
        if n_jumps[i] > 0:
            jump_sums[i] = kou_jump_sizes(n_jumps[i], p, lam1, lam2, rng).sum()
    return drift + diffusion + jump_sums


class TestKouMcInvariants:
    """L2: Kou jump-size sampler must match closed-form moments + induce
    leptokurtosis in Kou-driven returns."""

    def test_kou_mean_matches_analytic(self):
        """Sampled mean of jump-size Y ≈ p/λ₁-(1-p)/λ₂ (tolerance 3%).

        Closed-form mean of the double-exponential density. A regression that
        swapped p with 1-p or confused rate/scale would fail this.
        """
        rng = np.random.default_rng(42)
        n = 200_000
        sample = kou_jump_sizes(n, P, LAM1, LAM2, rng)
        mean_analytic = P / LAM1 - (1 - P) / LAM2  # = -0.11
        ratio = sample.mean() / mean_analytic
        assert abs(ratio - 1.0) < 0.03, (
            f"Kou mean doesn't match analytic: sampled={sample.mean():.5f}, "
            f"analytic={mean_analytic:.5f}, ratio={ratio:.4f}"
        )

    def test_kou_variance_matches_analytic(self):
        """Sampled variance of Y ≈ 2[p/λ₁²+(1-p)/λ₂²]-(mean)² (tolerance 5%).

        Second moment of double-exponential: E[Y²]=2[p/λ₁²+(1-p)/λ₂²].
        """
        rng = np.random.default_rng(123)
        n = 200_000
        sample = kou_jump_sizes(n, P, LAM1, LAM2, rng)
        e2_analytic = 2.0 * (P / LAM1**2 + (1 - P) / LAM2**2)
        mean_analytic = P / LAM1 - (1 - P) / LAM2
        var_analytic = e2_analytic - mean_analytic**2
        ratio = sample.var() / var_analytic
        assert abs(ratio - 1.0) < 0.05, (
            f"Kou variance doesn't match analytic: sampled={sample.var():.6f}, "
            f"analytic={var_analytic:.6f}, ratio={ratio:.4f}"
        )

    def test_kou_returns_leptokurtic(self):
        """Kou-driven log-returns must have excess kurtosis > GBM kurtosis.

        The double-exponential jump size is leptokurtic (excess kurtosis 4+ in
        prototype), so Kou returns have fatter tails than GBM at the same σ.
        This is the empirical reason Kou exists — Gaussian jumps (Merton) are
        also leptokurtic-inducing but double-exp does it with fewer params.
        """
        n_paths = 100_000
        rng_k = np.random.default_rng(7)
        lr_kou = kou_log_returns(MU, SIGMA, LAMBDA, P, LAM1, LAM2, T, n_paths, rng_k)

        # GBM at same diffusion σ
        rng_g = np.random.default_rng(99)
        lr_gbm = (MU - 0.5 * SIGMA * SIGMA) * T + SIGMA * np.sqrt(T) * rng_g.standard_normal(n_paths)

        kurt_kou = stats.kurtosis(lr_kou)
        kurt_gbm = stats.kurtosis(lr_gbm)
        assert kurt_kou > kurt_gbm, (
            f"Kou returns not more leptokurtic than GBM: "
            f"kou={kurt_kou:.4f}, gbm={kurt_gbm:.4f}"
        )
        assert kurt_kou > 0, (
            f"Kou excess kurtosis not positive: {kurt_kou:.4f}"
        )
