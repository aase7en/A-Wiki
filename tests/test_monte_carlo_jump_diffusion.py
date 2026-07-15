"""Integration tests bridging jump-diffusion theory (wiki/sources/merton-jump-
diffusion.md) and the Monte Carlo practice skill (skills/awiki/monte-carlo-
quant-analysis §Extensions — J2 Jump-diffusion subsection).

J2: the SKILL.md distribution table names "Poisson + jump-diffusion (Merton)"
but ships no code. These tests pin the mathematical invariants a Merton
jump-diffusion MC sampler MUST satisfy, so that the code added to the skill
(J2-c subsection) can be validated against them.

Scipy-only (scipy >= 1.7, declared in requirements-optional.txt). Samplers live
in-test rather than in a shared module so the tests stay authoritative even if
the skill's prose snippets change.

[verified 2026-07-15] — all assertions hold on scipy 1.17.1, numpy 2.4.6,
fixed seeds. Params (λ=5, μ_J=-0.05, σ_J=0.2) chosen for clear fat-tail signal
(excess kurt ≈ 0.4) and unambiguous VaR separation from GBM (≈0.6 magnitude).
"""
from __future__ import annotations

import numpy as np
import pytest

# scipy is an optional dependency (requirements-optional.txt). Skip the whole
# module if absent so CI's default `requirements.txt`-only run stays green.
pytest.importorskip("scipy")
from scipy import stats  # noqa: E402

# ---------------------------------------------------------------------------
# Test-local Merton jump-diffusion sampler. Simulates log-returns over [0, T]
# exactly (no time-step discretization) by drawing N_T ~ Poisson(λT) jumps per
# path directly — this is the right way per the ข้อควรระวัง in source page
# (Euler-Maruyama undercounts jumps if dt is too coarse).
# ---------------------------------------------------------------------------

# Merton params — chosen empirically before writing assertions.
# Anti-direction-bug discipline (H6 lesson): kurtosis 0.41, VaR gap 0.6.
LAMBDA = 5.0       # jump intensity (5 jumps/year expected)
MU_J = -0.05       # mean log-jump-size (downside bias)
SIGMA_J = 0.2      # std log-jump-size
SIGMA = 0.2        # diffusion (Brownian) volatility
MU = 0.05          # asset drift (annualized)
T = 1.0            # 1-year horizon


def merton_log_returns(
    mu: float,
    sigma: float,
    lam: float,
    mu_j: float,
    sigma_j: float,
    T: float,
    n_paths: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Merton (1976) jump-diffusion log-returns over [0, T] — exact simulation.

    Drift is compensated by λk so total expected return equals μ (jumps are
    not "free"). Returns shape (n_paths,).
    """
    n_jumps = rng.poisson(lam * T, size=n_paths)
    jump_sums = np.zeros(n_paths)
    max_j = int(n_jumps.max())
    if max_j > 0:
        all_jumps = rng.normal(mu_j, sigma_j, size=(n_paths, max_j))
        mask = np.arange(max_j)[None, :] < n_jumps[:, None]
        jump_sums = (all_jumps * mask).sum(axis=1)
    k = np.exp(mu_j + sigma_j * sigma_j / 2.0) - 1.0
    drift = (mu - sigma * sigma / 2.0 - lam * k) * T
    diffusion = sigma * np.sqrt(T) * rng.standard_normal(n_paths)
    return drift + diffusion + jump_sums


# ---------------------------------------------------------------------------
# Invariant tests
# ---------------------------------------------------------------------------

class TestMertonMcInvariants:
    """J2: Merton jump-diffusion must induce fat tails, reduce to GBM at λ=0, and worsen VaR."""

    def test_merton_kurtosis_exceeds_normal(self):
        """Log-returns under Merton must have excess kurtosis > 0.

        Jump component mixes normals with different means → unconditional
        distribution is a normal-mixture → heavier tails than any single
        normal. This is the empirical reason jump-diffusion models exist
        (GBM's kurtosis=3 under-estimates crash probability).
        """
        rng = np.random.default_rng(42)
        n_paths = 100_000

        lr = merton_log_returns(MU, SIGMA, LAMBDA, MU_J, SIGMA_J, T, n_paths, rng)
        kurt = stats.kurtosis(lr)  # excess kurtosis (0 = normal)

        assert kurt > 0, (
            f"Merton excess kurtosis not positive: {kurt:.4f} — "
            f"jump component should induce fat tails"
        )

    def test_zero_intensity_recovers_gbm(self):
        """At λ=0, Merton must reduce to pure GBM (mean + variance match within 2%).

        Sanity check: when there are no jumps, the sampler should produce
        drift + diffusion only. A regression that double-counts drift or
        leaves a jump term would fail this.
        """
        rng = np.random.default_rng(123)
        n_paths = 100_000

        lr_merton_zero = merton_log_returns(MU, SIGMA, 0.0, MU_J, SIGMA_J, T, n_paths, rng)

        # Paired GBM (same seed → same Brownian draws)
        rng2 = np.random.default_rng(123)
        lr_gbm = (MU - SIGMA * SIGMA / 2.0) * T + SIGMA * np.sqrt(T) * rng2.standard_normal(n_paths)

        mean_diff = abs(lr_merton_zero.mean() - lr_gbm.mean())
        var_ratio = lr_merton_zero.var() / lr_gbm.var()

        assert mean_diff < 0.01, (
            f"Merton λ=0 mean drifts from GBM: "
            f"merton={lr_merton_zero.mean():.5f}, gbm={lr_gbm.mean():.5f}, diff={mean_diff:.5f}"
        )
        assert abs(var_ratio - 1.0) < 0.02, (
            f"Merton λ=0 variance differs from GBM: ratio={var_ratio:.4f}"
        )

    def test_jump_component_worsens_tail_var(self):
        """Merton VaR(5%) must be more negative than pure-GBM VaR(5%) at same σ.

        Downside jumps (μ_J < 0) shift probability mass into the left tail,
        so the 5% quantile of P&L is materially worse under Merton than GBM.
        This is why risk managers add jumps — GBM materially under-states
        deep-tail loss.
        """
        rng_merton = np.random.default_rng(7)
        n_paths = 100_000

        lr_merton = merton_log_returns(MU, SIGMA, LAMBDA, MU_J, SIGMA_J, T, n_paths, rng_merton)

        # Pure GBM at same diffusion vol (different seed to avoid pairing bias)
        rng_gbm = np.random.default_rng(99)
        lr_gbm = (MU - SIGMA * SIGMA / 2.0) * T + SIGMA * np.sqrt(T) * rng_gbm.standard_normal(n_paths)

        var_merton = float(np.quantile(lr_merton, 0.05))
        var_gbm = float(np.quantile(lr_gbm, 0.05))

        # More-negative VaR = larger loss. Jumps must worsen the tail.
        assert var_merton < var_gbm, (
            f"Merton VaR(5%) not worse than GBM: "
            f"merton={var_merton:.4f}, gbm={var_gbm:.4f}"
        )
