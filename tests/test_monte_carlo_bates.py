"""Integration tests bridging jump-diffusion-variant theory (wiki/sources/jump-
diffusion-variants.md) and the Monte Carlo practice skill (skills/awiki/monte-
carlo-quant-analysis §Extensions — L1 Jump-diffusion variants subsection).

L1: the SKILL.md Merton family table names "Bates (1996)" as the Heston+Merton
superposition but ships no code. These tests pin the mathematical invariants a
Bates MC sampler MUST satisfy, so that the code added to the skill (L1 SKILL
subsection) can be validated against them.

Bates = Heston (1993) CIR variance + correlated asset, with Merton (1976)
compound-Poisson Gaussian jumps added per path. Drift compensated by λk so
total expected return = μ.

Scipy-only (scipy >= 1.7, declared in requirements-optional.txt). Samplers live
in-test rather than in a shared module so the tests stay authoritative even if
the skill's prose snippets change.

[verified 2026-07-15] — all assertions hold on scipy 1.17.1, numpy 2.4.6,
fixed seeds. Params reuse J1 Heston (κ=2, θ=0.09, ξ=0.4, ρ=-0.8) + J2 Merton
(λ=5, μ_J=-0.05, σ_J=0.2). Math prototype run BEFORE writing assertions
(H6 anti-direction-bug discipline): VaR ordering confirmed (Bates < both),
kurtosis-subtlety discovered (Bates > Merton kurt but < Heston kurt — adding
near-Gaussian Merton diffusion dilutes Heston's high per-variance kurtosis).
"""
from __future__ import annotations

import numpy as np
import pytest

# scipy is an optional dependency (requirements-optional.txt). Skip the whole
# module if absent so CI's default `requirements.txt`-only run stays green.
pytest.importorskip("scipy")
from scipy import stats  # noqa: E402

# ---------------------------------------------------------------------------
# Test-local Heston (CIR variance + correlated asset) and Merton (exact
# compound-Poisson jumps) samplers. Bates composes both — copy both into the
# test rather than importing from sibling test modules (J/K convention: tests
# stay authoritative even if skill prose changes).
# ---------------------------------------------------------------------------

# Heston params (mirror tests/test_monte_carlo_stochastic_vol.py J1)
V0 = 0.09
KAPPA = 2.0
THETA = 0.09
XI = 0.4
RHO = -0.8
MU = 0.05
DT = 1.0 / 252

# Merton params (mirror tests/test_monte_carlo_jump_diffusion.py J2)
LAMBDA = 5.0
MU_J = -0.05
SIGMA_J = 0.2
T = 1.0


def heston_log_returns(v0, kappa, theta, xi, rho, mu, dt, n_steps, n_paths, rng):
    """Heston Euler-Maruyama: variance CIR + correlated asset. Returns log-returns."""
    v = np.full(n_paths, v0, dtype=float)
    log_s = np.zeros(n_paths)
    sqrt_dt = np.sqrt(dt)
    sqrt_1mr2 = np.sqrt(1.0 - rho * rho)
    for _ in range(n_steps):
        zv = rng.standard_normal(n_paths)
        zs = rho * zv + sqrt_1mr2 * rng.standard_normal(n_paths)
        v = v + kappa * (theta - v) * dt + xi * np.sqrt(np.maximum(v, 0.0)) * sqrt_dt * zv
        v = np.maximum(v, 0.0)
        log_s += (mu - 0.5 * v) * dt + np.sqrt(np.maximum(v, 0.0)) * sqrt_dt * zs
    return log_s


def merton_jump_sum(lam, mu_j, sigma_j, T, n_paths, rng):
    """Sum of Poisson(λT) Gaussian jumps per path — exact (no time-step)."""
    n_jumps = rng.poisson(lam * T, size=n_paths)
    jump_sums = np.zeros(n_paths)
    max_j = int(n_jumps.max())
    if max_j > 0:
        all_jumps = rng.normal(mu_j, sigma_j, size=(n_paths, max_j))
        mask = np.arange(max_j)[None, :] < n_jumps[:, None]
        jump_sums = (all_jumps * mask).sum(axis=1)
    return jump_sums


def bates_log_returns(mu, kappa, theta, xi, rho, v0, lam, mu_j, sigma_j,
                      dt, n_steps, n_paths, rng):
    """Bates (1996): Heston SV + Merton jumps. Returns log-returns over [0, T].

    Composition: run Heston asset path with drift reduced by λk (jump
    compensation), then add exact Merton jumps per path.
    """
    T = n_steps * dt
    k = np.exp(mu_j + sigma_j * sigma_j / 2.0) - 1.0
    # Heston path with drift (μ - λk) so total E[return] = μ once jumps added.
    lr_sv = heston_log_returns(v0, kappa, theta, xi, rho, mu - lam * k,
                               dt, n_steps, n_paths, rng)
    jump_sums = merton_jump_sum(lam, mu_j, sigma_j, T, n_paths, rng)
    return lr_sv + jump_sums


# ---------------------------------------------------------------------------
# Invariant tests
# ---------------------------------------------------------------------------

class TestBatesMcInvariants:
    """L1: Bates must worsen tail vs BOTH Heston and Merton, and add fat tails
    beyond Merton. The kurtosis-vs-Heston direction is subtle (see prototype
    note in module docstring) so we test VaR ordering + Bates>Merton kurt."""

    def test_bates_tail_worse_than_heston(self):
        """Bates VaR(5%) < Heston VaR(5%) at same SV params (jumps worsen tail).

        Adding downside jumps (μ_J<0) shifts mass into the left tail on top of
        the already-fat-tailed Heston path → deeper 5% quantile. Paired seeds
        isolate the jump effect.
        """
        n_paths = 100_000
        n_steps = 252

        # Bates: full sampler
        rng_b = np.random.default_rng(42)
        lr_bates = bates_log_returns(
            MU, KAPPA, THETA, XI, RHO, V0, LAMBDA, MU_J, SIGMA_J,
            DT, n_steps, n_paths, rng_b,
        )

        # Heston: same base seed → same Brownian/variance draws, no jumps
        rng_h = np.random.default_rng(42)
        lr_heston = heston_log_returns(
            V0, KAPPA, THETA, XI, RHO, MU, DT, n_steps, n_paths, rng_h,
        )

        var_bates = float(np.quantile(lr_bates, 0.05))
        var_heston = float(np.quantile(lr_heston, 0.05))
        assert var_bates < var_heston, (
            f"Bates VaR(5%) not worse than Heston: "
            f"bates={var_bates:.4f}, heston={var_heston:.4f}"
        )

    def test_bates_tail_worse_than_merton(self):
        """Bates VaR(5%) < Merton VaR(5%) (SV adds fat tails beyond pure jumps).

        Merton alone (constant vol) misses volatility clustering; pairing it
        with Heston SV produces a deeper 5% quantile than Merton at the same
        long-run variance θ.
        """
        n_paths = 100_000
        n_steps = 252
        T_horizon = n_steps * DT
        sigma_m = np.sqrt(THETA)  # Merton diffusion vol = sqrt(long-run var)

        # Merton-only: GBM + jumps at constant vol sqrt(θ)
        rng_m = np.random.default_rng(42)
        k = np.exp(MU_J + SIGMA_J * SIGMA_J / 2.0) - 1.0
        drift_m = (MU - 0.5 * sigma_m * sigma_m - LAMBDA * k) * T_horizon
        diff_m = sigma_m * np.sqrt(T_horizon) * rng_m.standard_normal(n_paths)
        jump_m = merton_jump_sum(LAMBDA, MU_J, SIGMA_J, T_horizon, n_paths, rng_m)
        lr_merton = drift_m + diff_m + jump_m

        # Bates: same seed → comparable Brownian pool (roughly)
        rng_b = np.random.default_rng(42)
        lr_bates = bates_log_returns(
            MU, KAPPA, THETA, XI, RHO, V0, LAMBDA, MU_J, SIGMA_J,
            DT, n_steps, n_paths, rng_b,
        )

        var_bates = float(np.quantile(lr_bates, 0.05))
        var_merton = float(np.quantile(lr_merton, 0.05))
        assert var_bates < var_merton, (
            f"Bates VaR(5%) not worse than Merton: "
            f"bates={var_bates:.4f}, merton={var_merton:.4f}"
        )

    def test_bates_kurtosis_exceeds_merton(self):
        """Bates excess kurtosis > Merton excess kurtosis (SV adds fat tails).

        NOTE (H6 lesson from prototype): this asserts Bates > MERTON, not Bates
        > Heston. Empirically Heston alone produces higher per-variance excess
        kurtosis (≈1.5) than Bates (≈0.4), because adding Merton's near-
        Gaussian diffusion dilutes the kurtosis. The mathematically correct
        comparison for "jumps+SV compound" is against Merton (jumps-only): the
        SV component does add fat tails beyond what jumps alone produce.
        """
        n_paths = 100_000
        n_steps = 252
        T_horizon = n_steps * DT
        sigma_m = np.sqrt(THETA)

        # Merton-only
        rng_m = np.random.default_rng(7)
        k = np.exp(MU_J + SIGMA_J * SIGMA_J / 2.0) - 1.0
        drift_m = (MU - 0.5 * sigma_m * sigma_m - LAMBDA * k) * T_horizon
        diff_m = sigma_m * np.sqrt(T_horizon) * rng_m.standard_normal(n_paths)
        jump_m = merton_jump_sum(LAMBDA, MU_J, SIGMA_J, T_horizon, n_paths, rng_m)
        lr_merton = drift_m + diff_m + jump_m

        # Bates
        rng_b = np.random.default_rng(7)
        lr_bates = bates_log_returns(
            MU, KAPPA, THETA, XI, RHO, V0, LAMBDA, MU_J, SIGMA_J,
            DT, n_steps, n_paths, rng_b,
        )

        kurt_bates = stats.kurtosis(lr_bates)
        kurt_merton = stats.kurtosis(lr_merton)
        assert kurt_bates > kurt_merton, (
            f"Bates excess kurtosis not above Merton: "
            f"bates={kurt_bates:.4f}, merton={kurt_merton:.4f}"
        )

    def test_zero_jumps_reduces_to_heston(self):
        """At λ=0, Bates must reduce to Heston (mean + variance match, 5% tol).

        Composition sanity: when there are no jumps, the sampler should produce
        pure Heston paths. A regression that leaves a jump term or double-
        compensates drift would fail this. Paired seeds give near-exact match.
        """
        n_paths = 100_000
        n_steps = 252

        # Bates at λ=0
        rng_b = np.random.default_rng(123)
        lr_bates0 = bates_log_returns(
            MU, KAPPA, THETA, XI, RHO, V0, 0.0, MU_J, SIGMA_J,
            DT, n_steps, n_paths, rng_b,
        )

        # Heston (same seed → same draws; merton_jump_sum(λ=0) draws 0 jumps
        # so the rng streams stay in sync)
        rng_h = np.random.default_rng(123)
        lr_heston = heston_log_returns(
            V0, KAPPA, THETA, XI, RHO, MU, DT, n_steps, n_paths, rng_h,
        )

        mean_diff = abs(lr_bates0.mean() - lr_heston.mean())
        var_ratio = lr_bates0.var() / lr_heston.var()
        assert mean_diff < 0.005, (
            f"Bates λ=0 mean drifts from Heston: "
            f"bates={lr_bates0.mean():.5f}, heston={lr_heston.mean():.5f}"
        )
        assert abs(var_ratio - 1.0) < 0.05, (
            f"Bates λ=0 variance differs from Heston: ratio={var_ratio:.4f}"
        )
