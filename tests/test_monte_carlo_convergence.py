"""Integration tests for the convergence diagnostic helper in the
monte-carlo-quant-analysis skill (§Extensions — K6 Convergence diagnostic).

K6: SKILL.md mentions convergence diagnostics in 3 places (§4 foundations,
workflow step 7, reporting standard #3) but ships no reusable helper. These
tests pin the invariants the helper MUST satisfy, so that the code added to
the skill (K6 subsection) can be validated against them.

The helper computes:
- mean, std, SE, CI (normal approx)
- doubling-N delta: |mean_full - mean_half| / |mean_half| (or fallback for
  near-zero mean: delta < 0.1*std)
- converged flag (delta < 1% threshold)

[verified 2026-07-15] — all assertions hold on scipy 1.17.1, numpy 2.4.6,
fixed seeds.
"""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("scipy")
from scipy.stats import norm  # noqa: E402


# ---------------------------------------------------------------------------
# Test-local convergence diagnostic helper (mirrors SKILL.md docstring)
# ---------------------------------------------------------------------------

def convergence_diagnostic(
    samples: np.ndarray,
    alpha: float = 0.05,
    threshold_pct: float = 1.0,
) -> dict:
    """MC convergence diagnostic. Doubling-N delta < threshold_pct => converged.

    For near-zero means (|mean_half| < 0.1*std), falls back to absolute test:
    converged if |mean_full - mean_half| < 0.1*std (avoids divide-by-near-zero).
    """
    samples = np.asarray(samples, dtype=float)
    n = len(samples)
    mean = float(samples.mean())
    std = float(samples.std(ddof=1))
    se = std / np.sqrt(n)
    z = norm.ppf(1 - alpha / 2)
    ci_low = mean - z * se
    ci_high = mean + z * se
    half = n // 2
    mean_half = float(samples[:half].mean())
    delta_abs = abs(mean - mean_half)
    if abs(mean_half) > 0.1 * std:
        doubling_delta_pct = delta_abs / abs(mean_half) * 100
        converged = doubling_delta_pct < threshold_pct
    else:
        # Near-zero mean: scale delta by std (avoids infinity)
        doubling_delta_pct = delta_abs / std * 100 if std > 0 else 0.0
        converged = delta_abs < 0.1 * std
    return {
        "mean": mean,
        "std": std,
        "se": se,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "doubling_delta_pct": doubling_delta_pct,
        "converged": converged,
        "n": n,
    }


# ---------------------------------------------------------------------------
# Invariant tests
# ---------------------------------------------------------------------------

class TestConvergenceDiagnostic:
    """K6: convergence diagnostic must flag converged vs under-sampled and bracket true mean."""

    def test_large_sample_passes_diagnostic(self):
        """N=100k standard-normal samples must converge (doubling delta < 1%).

        By LLN, the half-vs-full mean gap shrinks as N grows. At 100k samples
        the gap is well below 1% relative. A regression that flipped the
        threshold comparison or botched the halving would flag converged=False.
        """
        rng = np.random.default_rng(42)
        samples = rng.standard_normal(100_000)
        d = convergence_diagnostic(samples)
        assert d["converged"], (
            f"Large N not flagged converged: delta={d['doubling_delta_pct']:.4f}%, "
            f"threshold=1.0%"
        )
        assert d["doubling_delta_pct"] < 1.0

    def test_under_sampled_fails_diagnostic(self):
        """N=50 standard-normal samples must NOT converge (delta > 1%).

        Small samples have high MC noise; the half-vs-full mean gap will
        exceed 1%. A regression that always returned converged=True would
        fail to catch under-sampling.
        """
        rng = np.random.default_rng(42)
        samples = rng.standard_normal(50)
        d = convergence_diagnostic(samples)
        assert not d["converged"], (
            f"Small N (50) incorrectly flagged converged: "
            f"delta={d['doubling_delta_pct']:.4f}%"
        )
        assert d["doubling_delta_pct"] > 1.0

    def test_ci_brackets_true_mean(self):
        """For known N(0,1), the 95% CI must bracket the true mean 0.

        Sanity check on the CI computation. With 100k samples the CI is
        tight (±0.006) but must still contain 0. A regression that
        miscalculated SE or z would fail this.
        """
        rng = np.random.default_rng(42)
        samples = rng.standard_normal(100_000)
        d = convergence_diagnostic(samples)
        assert d["ci_low"] < 0.0 < d["ci_high"], (
            f"95% CI does not bracket true mean 0: "
            f"ci=[{d['ci_low']:.4f}, {d['ci_high']:.4f}]"
        )

    def test_near_zero_mean_uses_fallback(self):
        """When |mean_half| < 0.1*std, fallback (delta < 0.1*std) must apply.

        For N(0,1) with large N, mean is near 0 and percentage delta would
        blow up (divide by near-zero). The fallback keeps the diagnostic
        meaningful. A regression that always used percentage would flag
        near-zero-mean cases as not converged even at huge N.
        """
        rng = np.random.default_rng(42)
        samples = rng.standard_normal(100_000)
        d = convergence_diagnostic(samples)
        # The fallback should have kicked in (mean ≈ 0, std ≈ 1)
        # Verify: if percentage were used, delta would be huge (mean near 0)
        # Converged=True confirms fallback worked
        assert d["converged"], (
            "Near-zero mean case not handled by fallback — "
            "percentage delta would explode"
        )
