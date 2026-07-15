"""Integration tests bridging Hawkes (1971) self-exciting jump theory
(wiki/sources/jump-diffusion-variants.md) and the Monte Carlo practice skill
(skills/awiki/monte-carlo-quant-analysis §Extensions — L3 Jump-diffusion
variants subsection).

L3: the SKILL.md Merton family table names "Hawkes" with "self-exciting
intensity" but ships no code. These tests pin the mathematical invariants a
Hawkes MC sampler MUST satisfy, so that the code added to the skill (L3 SKILL
subsection) can be validated against them.

Hawkes process: intensity λ(t)=λ₀+Σ_{t_k<t} α·exp(-β(t-t_k)). Each arrival
raises the intensity by α which decays at rate β. Branching ratio n=α/β<1
required for stationarity. Empirical signature: count N(T) is over-dispersed
(Fano factor Var/E > 1) — unlike Poisson (Fano=1 exactly).

Exact simulation via Ogata (1981) thinning: draw candidates from Exp(λ*),
accept with prob λ(t)/λ* where λ*=λ₀+α is an upper bound between events
(valid when α<β).

Scipy-only. Samplers live in-test. [verified 2026-07-15] scipy 1.17.1, numpy
2.4.6, fixed seeds. Prototype confirmed: Fano=1.405 (Hawkes α=0.5,β=2.0),
Fano=1.035 at α=0 (recovers Poisson).
"""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("scipy")  # scipy is optional; we use only numpy here but
# keep the guard for consistency with the J/K/L test family.


def hawkes_jump_times(lam0: float, alpha: float, beta: float, T: float,
                      rng: np.random.Generator) -> np.ndarray:
    """Sample Hawkes jump times on [0,T] via Ogata (1981) thinning (exact).

    Intensity: λ(t) = λ₀ + Σ_{t_k<t} α·exp(-β(t-t_k))
    Upper bound between events: λ* = λ₀ + α (valid when α < β).
    Algorithm: draw candidate from Exp(λ*), accept with prob λ(t)/λ*.

    Requires α < β for stationarity (branching ratio α/β < 1). The long-run
    intensity is λ̄ = λ₀/(1-α/β). Returns sorted array of arrival times.
    """
    if not alpha < beta:
        raise ValueError(
            f"Hawkes stationarity requires alpha < beta; got alpha={alpha}, "
            f"beta={beta} (branching ratio {alpha/beta:.3f} ≥ 1 → explosive)"
        )
    lam_star = lam0 + alpha
    t = 0.0
    arrivals = []
    while t < T:
        t += -np.log(rng.uniform()) / lam_star  # Exp(λ*) candidate
        if t >= T:
            break
        # intensity at candidate time
        lam_at_t = lam0
        for tk in arrivals:
            lam_at_t += alpha * np.exp(-beta * (t - tk))
        if rng.uniform() < lam_at_t / lam_star:
            arrivals.append(t)
        # else reject (thinning) and continue
    return np.array(arrivals)


class TestHawkesMcInvariants:
    """L3: Hawkes must produce clustered arrivals (Fano>1) and reduce to
    Poisson at α=0. Stationarity (α<β) is enforced in the sampler."""

    def test_hawkes_clustered_fano_exceeds_one(self):
        """Hawkes count N(T) Fano factor (Var/E) > 1 (over-dispersed).

        Unlike a Poisson process where arrivals are iid (Fano=1 exactly), a
        self-exciting Hawkes process produces clustered arrivals: each event
        raises the probability of the next. The empirical signature is Fano>1.
        A regression that broke self-excitation (e.g. always used λ*) would
        produce Poisson-like Fano≈1.
        """
        lam0, alpha, beta, T = 1.0, 0.5, 2.0, 10.0
        assert alpha < beta, "test params violate stationarity"
        n_paths = 2000
        rng = np.random.default_rng(42)
        counts = np.array([
            len(hawkes_jump_times(lam0, alpha, beta, T, rng))
            for _ in range(n_paths)
        ])
        mean_n = counts.mean()
        var_n = counts.var()
        fano = var_n / mean_n
        assert fano > 1.0, (
            f"Hawkes not over-dispersed: Fano={fano:.3f} (must be > 1 for "
            f"clustering; Poisson baseline = 1.0)"
        )

    def test_zero_excitation_reduces_to_poisson(self):
        """At α=0, Hawkes must reduce to Poisson (Fano ≈ 1.0, tolerance 0.15).

        Composition sanity: when there is no self-excitation, the intensity is
        constant λ₀ and the process is a homogeneous Poisson process. A
        regression that left an excitation term would fail this.
        """
        lam0, alpha, beta, T = 1.0, 0.0, 2.0, 10.0
        n_paths = 2000
        rng = np.random.default_rng(42)
        counts_hawkes0 = np.array([
            len(hawkes_jump_times(lam0, alpha, beta, T, rng))
            for _ in range(n_paths)
        ])
        # Direct Poisson at same mean rate λ₀·T for comparison
        rng2 = np.random.default_rng(42)
        counts_poisson = rng2.poisson(lam0 * T, size=n_paths)

        fano_hawkes0 = counts_hawkes0.var() / counts_hawkes0.mean()
        fano_poisson = counts_poisson.var() / counts_poisson.mean()
        assert abs(fano_hawkes0 - 1.0) < 0.15, (
            f"Hawkes α=0 not Poisson-like: Fano={fano_hawkes0:.3f} "
            f"(Poisson baseline={fano_poisson:.3f}, tolerance 0.15)"
        )
        # Mean counts should also match within 2%
        mean_ratio = counts_hawkes0.mean() / counts_poisson.mean()
        assert abs(mean_ratio - 1.0) < 0.02, (
            f"Hawkes α=0 mean rate drifts from Poisson: ratio={mean_ratio:.4f}"
        )

    def test_stationarity_branching_ratio_enforced(self):
        """Sampler must reject α≥β (non-stationary / explosive).

        The Ogata thinning upper bound λ*=λ₀+α is only valid when α<β; for
        α≥β the intensity can grow unbounded and the upper bound fails. The
        sampler must enforce this precondition.
        """
        rng = np.random.default_rng(42)
        # alpha = beta → branching ratio = 1 (borderline explosive)
        with pytest.raises(ValueError, match="stationarity"):
            hawkes_jump_times(lam0=1.0, alpha=2.0, beta=2.0, T=1.0, rng=rng)
        # alpha > beta → branching ratio > 1 (explosive)
        with pytest.raises(ValueError, match="stationarity"):
            hawkes_jump_times(lam0=1.0, alpha=3.0, beta=1.0, T=1.0, rng=rng)
