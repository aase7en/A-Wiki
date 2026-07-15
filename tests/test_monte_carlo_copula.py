"""Integration tests bridging the copula theory (wiki/sources/copula-multivariate-
finance.md) and the Monte Carlo practice skill (skills/awiki/monte-carlo-
quant-analysis).

H6: the SKILL.md distribution table names "Copula" but ships no copula code.
These tests pin the mathematical invariants a copula-based MC sampler MUST
satisfy, so that future code added to the skill (G1 subsection) can be validated
against them.

Scipy-only (scipy >= 1.7, declared in requirements-optional.txt). Samplers live
in-test rather than in a shared module so the tests stay authoritative even if
the skill's prose snippets change.

[verified 2026-07-15] — all assertions hold on scipy 1.17.1, numpy 2.4.6,
fixed seeds. VaR is computed on the *sum* of two equal-weight standard-normal
marginals; more-negative VaR = worse loss = higher risk.
"""
from __future__ import annotations

import numpy as np
import pytest

# scipy is an optional dependency (requirements-optional.txt). Skip the whole
# module if absent so CI's default `requirements.txt`-only run stays green;
# the copula math runs under richer envs (local dev, the H7 CI step).
pytest.importorskip("scipy")
from scipy.stats import norm  # noqa: E402

# ---------------------------------------------------------------------------
# Test-local copula samplers (Gaussian + Clayton, uniform-marginal output).
# ---------------------------------------------------------------------------

N = 100_000  # large enough for <0.5% MC error on the 5% percentile


def sample_gaussian_copula(rho: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """Gaussian copula → (n, 2) uniforms preserving Pearson rank correlation rho.

    Uses the Cholesky form: z1 ~ N(0,1) independent; z2 = rho*z1 + sqrt(1-rho²)*e.
    Maps through norm.cdf so marginals are U(0,1) while Spearman correlation ≈ rho.
    """
    z = rng.normal(size=(n, 2))
    z[:, 1] = rho * z[:, 0] + np.sqrt(1.0 - rho * rho) * z[:, 1]
    return norm.cdf(z)


def sample_clayton_copula(theta: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """Clayton copula → (n, 2) uniforms with lower-tail dependence.

    Conditional-inverse sampler (Marshall–Olkin form): for U uniform, draw W
    uniform, then V = (1 + U^(-θ) (W^(-θ/(θ+1)) - 1))^(-1/θ). theta>0 →
    stronger lower-tail dependence.
    """
    u = rng.uniform(size=n)
    w = rng.uniform(size=n)
    v = (1.0 + u ** (-theta) * (w ** (-theta / (theta + 1.0)) - 1.0)) ** (-1.0 / theta)
    return np.column_stack([u, v])


def mc_var_2asset(u: np.ndarray, alpha: float = 0.05) -> float:
    """VaR(alpha) of an equal-weight 2-asset portfolio of standard-normal returns.

    u: (n, 2) uniforms from any copula. Returns the alpha-quantile of the
    portfolio sum (more-negative = larger loss).
    """
    x = norm.ppf(u).sum(axis=1)
    return float(np.quantile(x, alpha))


# ---------------------------------------------------------------------------
# Invariant tests
# ---------------------------------------------------------------------------

class TestCopulaMcBounds:
    """H6: copula-sampled VaR must respect correlation ordering + tail structure."""

    def test_correlation_increases_tail_loss(self):
        """VaR(5%) must worsen (become more negative) as Gaussian correlation rises.

        Independent → rho=0.5 → rho=0.95 should be monotonically decreasing in
        the numeric VaR value (i.e. monotonically increasing in loss magnitude).
        Drives the intuition: "diversification helps; concentration kills tails".
        """
        rng = np.random.default_rng(42)
        alpha = 0.05

        var_indep = mc_var_2asset(rng.uniform(size=(N, 2)), alpha)
        var_mid = mc_var_2asset(sample_gaussian_copula(0.5, N, rng), alpha)
        var_high = mc_var_2asset(sample_gaussian_copula(0.95, N, rng), alpha)

        # More-negative VaR = larger loss. Correlation makes losses co-occur.
        assert var_indep > var_mid > var_high, (
            f"correlation ordering violated: "
            f"indep={var_indep:.4f}, rho=0.5={var_mid:.4f}, rho=0.95={var_high:.4f}"
        )

    def test_clayton_lower_tail_heavier_than_gaussian(self):
        """At matched Kendall τ, Clayton VaR(5%) must be more negative than Gaussian.

        Clayton exhibits asymptotic lower-tail dependence; Gaussian does not
        (λ_L = 0 for all rho < 1). At comparable rank correlation (Clayton
        θ=5 → Kendall τ≈0.714; Gaussian rho=0.9 → Kendall τ≈0.713), Clayton
        must concentrate more probability mass in the joint lower tail.
        """
        rng = np.random.default_rng(123)
        alpha = 0.05

        var_clayton = mc_var_2asset(sample_clayton_copula(5.0, N, rng), alpha)
        var_gaussian = mc_var_2asset(sample_gaussian_copula(0.9, N, rng), alpha)

        assert var_clayton < var_gaussian, (
            f"Clayton lower tail not heavier at matched τ: "
            f"clayton={var_clayton:.4f}, gaussian={var_gaussian:.4f}"
        )

    def test_gaussian_copula_preserves_rank_correlation(self):
        """Sanity: the Gaussian copula sampler's Spearman correlation must ≈ rho.

        Guards against a sign / scale bug in the Cholesky construction. Tolerance
        0.03 is generous given MC noise on 100k samples.
        """
        rng = np.random.default_rng(7)
        rho_target = 0.7
        u = sample_gaussian_copula(rho_target, N, rng)
        # Spearman = Pearson of rank-transformed uniforms ≈ Pearson of uniforms here.
        rho_observed = np.corrcoef(u[:, 0], u[:, 1])[0, 1]
        assert abs(rho_observed - rho_target) < 0.03, (
            f"Gaussian copula rank correlation off: target={rho_target}, "
            f"observed={rho_observed:.4f}"
        )

    def test_perfect_correlation_matches_single_asset(self):
        """At rho≈1, the 2-asset portfolio VaR must approach 2× a single-asset VaR.

        Perfect correlation collapses the portfolio to 2× one asset, so VaR(α)
        of the sum = 2 × norm.ppf(α). A regression that breaks the copula
        scaling would fail this.
        """
        rng = np.random.default_rng(99)
        alpha = 0.05
        # rho=0.999 ≈ perfect without numerical singularity
        var_portfolio = mc_var_2asset(sample_gaussian_copula(0.999, N, rng), alpha)
        var_expected = 2.0 * norm.ppf(alpha)
        # ~3% tolerance for the residual 0.001 independence + MC noise
        assert abs(var_portfolio - var_expected) / abs(var_expected) < 0.03, (
            f"perfect-correlation scaling off: portfolio={var_portfolio:.4f}, "
            f"expected={var_expected:.4f}"
        )
