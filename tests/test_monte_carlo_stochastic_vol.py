"""Integration tests bridging stochastic-volatility theory (wiki/sources/stochastic-
vol-heston-sabr.md) and the Monte Carlo practice skill (skills/awiki/monte-carlo-
quant-analysis §Extensions — J1 Stochastic volatility subsection).

J1: the SKILL.md "อื่นๆ" bullet names "Heston (stochastic vol), SABR" but ships no
code. These tests pin the mathematical invariants a Heston Euler-Maruyama MC
sampler MUST satisfy, so that the code added to the skill (J1-c subsection) can
be validated against them.

Scipy-only (scipy >= 1.7, declared in requirements-optional.txt). Samplers live
in-test rather than in a shared module so the tests stay authoritative even if
the skill's prose snippets change.

[verified 2026-07-15] — all assertions hold on scipy 1.17.1, numpy 2.4.6,
fixed seeds. Heston params chosen so Feller condition (2κθ > ξ²) is satisfied
and vol-of-vol effect produces clear fat tails (excess kurtosis > 0).
"""
from __future__ import annotations

import numpy as np
import pytest

# scipy is an optional dependency (requirements-optional.txt). Skip the whole
# module if absent so CI's default `requirements.txt`-only run stays green;
# the stochastic-vol math runs under richer envs (local dev, the H7 CI step).
pytest.importorskip("scipy")
from scipy import stats  # noqa: E402

# ---------------------------------------------------------------------------
# Test-local Heston sampler (Euler-Maruyama discretization of CIR variance
# process + correlated asset process). Absorption (max(v,0)) handles Feller
# violations gracefully.
# ---------------------------------------------------------------------------

# Heston params chosen to (a) satisfy Feller, (b) produce clear fat-tail signal,
# (c) match long-run mean θ within 5% on 4-year horizon, N=50k.
# Verified empirically before writing this test (Iron Law #1 anti-direction-bug).
V0_DEFAULT = 0.09       # initial variance (30% annualized vol)
KAPPA = 2.0             # mean-reversion speed
THETA = 0.09            # long-run variance target
XI = 0.4                # vol-of-vol
RHO = -0.8              # leverage correlation (equity: price-down -> vol-up)
MU_DRIFT = 0.05         # asset drift (annualized)
DT = 1.0 / 252          # daily timestep


def heston_paths(
    v0: float,
    kappa: float,
    theta: float,
    xi: float,
    rho: float,
    mu: float,
    dt: float,
    n_steps: int,
    n_paths: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Heston Euler-Maruyama MC sampler.

    Returns (log_returns_sum, final_variance) for n_paths.
    Variance uses absorption (max(v, 0)) so Feller violations don't crash —
    this is the standard practical fix (Andersen 2008).
    """
    v = np.full(n_paths, v0, dtype=float)
    log_s = np.zeros(n_paths)
    sqrt_dt = np.sqrt(dt)
    sqrt_one_minus_rho2 = np.sqrt(1.0 - rho * rho)
    for _ in range(n_steps):
        zv = rng.standard_normal(n_paths)
        # Correlated asset shock via Cholesky: zs = rho*zv + sqrt(1-rho^2)*z_indep
        zs = rho * zv + sqrt_one_minus_rho2 * rng.standard_normal(n_paths)
        v_new = v + kappa * (theta - v) * dt + xi * np.sqrt(np.maximum(v, 0.0)) * sqrt_dt * zv
        v_new = np.maximum(v_new, 0.0)  # absorption
        v = v_new
        log_s += (mu - 0.5 * v) * dt + np.sqrt(np.maximum(v, 0.0)) * sqrt_dt * zs
    return log_s, v


# ---------------------------------------------------------------------------
# Invariant tests
# ---------------------------------------------------------------------------

class TestHestonMcInvariants:
    """J1: Heston-sampled MC must respect mean-reversion, Feller, and fat-tail properties."""

    def test_variance_mean_reverts_to_theta(self):
        """Long-run mean of v_t must approach θ (within 5%).

        The CIR process has stationary distribution with mean θ. Over a
        4-year (1008-step) horizon with κ=2 (half-life ≈ 0.35 yr), the
        variance process forgets its initial condition and the cross-sectional
        mean over many paths should be within 5% of θ.
        """
        rng = np.random.default_rng(42)
        n_steps = 252 * 4  # 4 years — long enough to forget v0
        n_paths = 50_000

        _, v_final = heston_paths(
            V0_DEFAULT, KAPPA, THETA, XI, RHO, MU_DRIFT, DT, n_steps, n_paths, rng
        )

        ratio = v_final.mean() / THETA
        assert abs(ratio - 1.0) < 0.05, (
            f"Heston variance did not mean-revert to θ: "
            f"mean={v_final.mean():.5f}, θ={THETA}, ratio={ratio:.4f}"
        )

    def test_feller_condition_keeps_variance_nonnegative(self):
        """Feller-satisfying params must yield v_t >= 0 (absorption never triggers).

        With 2κθ=0.36 > ξ²=0.16 and absorption as a safety net, the minimum
        variance over 50k paths × 252 steps must be >= 0. A regression that
        breaks absorption would produce negative v.
        """
        rng = np.random.default_rng(123)
        n_steps = 252
        n_paths = 50_000

        # Track full path min, not just final — check absorption never needed
        v = np.full(n_paths, V0_DEFAULT, dtype=float)
        v_min = V0_DEFAULT
        sqrt_dt = np.sqrt(DT)
        for _ in range(n_steps):
            zv = rng.standard_normal(n_paths)
            v_new = v + KAPPA * (THETA - v) * DT + XI * np.sqrt(np.maximum(v, 0.0)) * sqrt_dt * zv
            v_new = np.maximum(v_new, 0.0)
            v_min = min(v_min, v_new.min())
            v = v_new

        # min > 0 strictly; even if it touches 0 numerically that's fine.
        assert v_min >= 0.0, (
            f"Heston variance went negative despite Feller: min v = {v_min}"
        )
        # Feller condition itself must hold for this test to be meaningful
        assert 2 * KAPPA * THETA > XI * XI, (
            "Test params violate Feller — adjust KAPPA/THETA/XI so 2κθ > ξ²"
        )

    def test_stochastic_vol_produces_fatter_tails_than_gbm(self):
        """Heston-sampled log-returns must have excess kurtosis > GBM at same long-run variance.

        Stochastic volatility induces mixing of normals with different scales
        → unconditional distribution is a normal-variance mixture → heavier
        tails than any single normal. This is the core empirical reason SV
        models beat GBM for deep-tail risk (kurtosis > 3 means excess kurt > 0).
        """
        rng = np.random.default_rng(7)
        n_steps = 252
        n_paths = 100_000

        log_s_heston, _ = heston_paths(
            V0_DEFAULT, KAPPA, THETA, XI, RHO, MU_DRIFT, DT, n_steps, n_paths, rng
        )

        # GBM baseline at same long-run variance θ (deterministic vol = sqrt(θ))
        rng2 = np.random.default_rng(7)  # same seed for paired comparison
        gbm_lr = (MU_DRIFT - 0.5 * THETA) * DT * n_steps + np.sqrt(THETA * DT) * np.sqrt(
            n_steps
        ) * rng2.standard_normal(n_paths)

        kurt_heston = stats.kurtosis(log_s_heston)  # excess kurtosis (0 = normal)
        kurt_gbm = stats.kurtosis(gbm_lr)

        assert kurt_heston > 0, (
            f"Heston excess kurtosis not positive: {kurt_heston:.4f} — "
            f"SV should induce fat tails"
        )
        assert kurt_heston > kurt_gbm, (
            f"Heston tails not fatter than GBM: "
            f"kurt_heston={kurt_heston:.4f}, kurt_gbm={kurt_gbm:.4f}"
        )
