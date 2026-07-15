"""Integration tests for Multi-level Monte Carlo (MLMC) as an extension of the
monte-carlo-quant-analysis skill (§Extensions — J3 Multi-level MC subsection).

J3: SKILL.md 'อื่นๆ' names 'Multi-level MC — variance reduction hierarchy' but
ships no code. These tests pin the mathematical invariants an MLMC telescoping
estimator MUST satisfy, so that the code added to the skill (J3 subsection)
can be validated against them.

MLMC core idea (Giles 2015): estimate E[g_fine(X)] via telescoping sum
  E[g_fine] = E[g_coarse] + Σ_{l=1}^L E[g_fine(X) - g_coarse(X)]
where each level uses *paired* samples sharing the SAME underlying X (shared
randomness). The diff has lower variance than g alone because fine and coarse
are positively correlated through X. Total cost is dominated by cheap coarse
levels; accuracy is dominated by the (few) fine samples.

**Shared-randomness contract**: g_fine(x) and g_coarse(x) take the same x
(drawn once per sample) and return scalars. This is the correct MLMC interface
— NOT g_fine(rng) where rng is called independently inside each function,
which would destroy the correlation that makes MLMC work.

[verified 2026-07-15] — all assertions hold on numpy 2.4.6, fixed seeds.
"""
from __future__ import annotations

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Test-local MLMC telescoping estimator (shared-randomness interface)
# ---------------------------------------------------------------------------

def mlmc_telescoping(
    g_fine,
    g_coarse,
    n_levels: int,
    n_per_level: int,
    rng: np.random.Generator,
) -> tuple[float, float]:
    """MLMC estimator via telescoping sum (shared-randomness).

    g_fine(x), g_coarse(x): callables taking a scalar x and returning a scalar.
    Level 0: E[g_coarse(X)] (n_per_level samples)
    Level l>0: E[g_fine(X) - g_coarse(X)] (n_per_level paired samples, same X)
    Returns (estimate, estimator_variance).
    """
    x0 = rng.standard_normal(n_per_level)
    samples0 = np.array([g_coarse(xi) for xi in x0])
    est = float(samples0.mean())
    var = float(samples0.var(ddof=1) / n_per_level)
    for _ in range(1, n_levels):
        x = rng.standard_normal(n_per_level)
        diffs = np.array([g_fine(xi) - g_coarse(xi) for xi in x])
        est += float(diffs.mean())
        var += float(diffs.var(ddof=1) / n_per_level)
    return est, var


# ---------------------------------------------------------------------------
# Invariant tests
# ---------------------------------------------------------------------------

class TestMlmcInvariants:
    """J3: MLMC must satisfy telescoping, paired-variance-reduction, and identical-fine=level-0."""

    def test_identical_fine_coarse_yields_zero_diff(self):
        """When fine == coarse, g_fine(x) - g_coarse(x) = 0 exactly (same x).

        The MLMC contract: shared randomness means g_fine and g_coarse see
        the SAME x. If g_fine == g_coarse (no refinement), the diff is
        identically zero at every level > 0. A regression that drew x
        independently for fine and coarse would produce a nonzero diff.
        """
        rng = np.random.default_rng(42)
        n_per_level = 5000

        def g(x):
            return float(np.exp(x))

        # MLMC with identical fine/coarse
        est_mlmc, var_mlmc = mlmc_telescoping(g, g, n_levels=4, n_per_level=n_per_level, rng=rng)

        # Independent re-run for level-0 baseline
        rng2 = np.random.default_rng(42)
        x0 = rng2.standard_normal(n_per_level)
        samples0 = np.array([g(xi) for xi in x0])
        est_level0 = float(samples0.mean())
        var_level0 = float(samples0.var(ddof=1) / n_per_level)

        # MLMC estimate must equal level-0 estimate (diffs are 0.0 by construction)
        assert abs(est_mlmc - est_level0) < 1e-12, (
            f"MLMC with identical fine/coarse diverged from level-0: "
            f"mlmc={est_mlmc:.6f}, level0={est_level0:.6f} "
            f"(likely shared-randomness contract broken — drawing x twice)"
        )
        # Variance of MLMC estimator: only level-0 contributes (diffs are exactly 0)
        assert var_mlmc < var_level0 * 1.001, (
            f"MLMC variance inflated by zero diffs: "
            f"mlmc_var={var_mlmc:.6e}, level0_var={var_level0:.6e}"
        )

    def test_telescoping_estimate_unbiased_for_e_fine(self):
        """MLMC telescoping must converge to E[g_fine], not E[g_coarse].

        With g_fine(x) = exp(x), g_coarse(x) = exp(x/2) (less spread), the
        telescoping sum E[g_coarse] + E[g_fine - g_coarse] = E[g_fine].
        A bug that drops the diff term or sign-flips it would bias the
        estimate toward E[g_coarse].
        """
        rng = np.random.default_rng(123)
        n_per_level = 20_000  # large N for tight tolerance

        def g_fine(x):
            return float(np.exp(x))

        def g_coarse(x):
            return float(np.exp(0.5 * x))

        est, _ = mlmc_telescoping(g_fine, g_coarse, n_levels=2, n_per_level=n_per_level, rng=rng)

        # E[exp(X)] = exp(0.5) ≈ 1.6487 for X ~ N(0,1)
        # E[exp(X/2)] = exp(0.125) ≈ 1.1331 — if diff term dropped, est lands here
        true_fine = float(np.exp(0.5))
        true_coarse = float(np.exp(0.125))

        assert abs(est - true_fine) < abs(est - true_coarse), (
            f"MLMC biased toward coarse: est={est:.4f}, "
            f"true_fine={true_fine:.4f}, true_coarse={true_coarse:.4f}"
        )
        # Tighter: within 3% of true_fine
        assert abs(est - true_fine) / true_fine < 0.03, (
            f"MLMC not converging to E[g_fine]: est={est:.4f}, true={true_fine:.4f}"
        )

    def test_paired_difference_has_lower_variance_than_single_sample(self):
        """Var(g_fine(X) - g_coarse(X)) < Var(g_fine(X)) when paired on same X.

        The core MLMC insight: paired samples (same X) produce a diff whose
        variance is materially below either term's alone, because g_fine and
        g_coarse are positively correlated through X. This is why MLMC beats
        standard MC at fixed cost — the high-variance part (g alone) is
        replaced by a low-variance correction.
        """
        rng = np.random.default_rng(7)
        n = 50_000

        x = rng.standard_normal(n)
        g_fine_samples = np.exp(x)
        g_coarse_samples = np.exp(0.5 * x)
        diffs = g_fine_samples - g_coarse_samples

        var_fine = float(g_fine_samples.var(ddof=1))
        var_diff = float(diffs.var(ddof=1))

        assert var_diff < var_fine, (
            f"Paired diff variance not below single-sample: "
            f"var(diff)={var_diff:.4f}, var(g_fine)={var_fine:.4f} "
            f"(shared-randomness broken?)"
        )
