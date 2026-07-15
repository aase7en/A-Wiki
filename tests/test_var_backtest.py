"""Christoffersen (1998) VaR backtest LR tests — validation layer for the
monte-carlo-quant-analysis skill (K8).

K8: the skill computes VaR via MC, but there is no validation layer to check
whether the VaR forecasts are *correct* — i.e., whether the observed breach
rate matches the nominal α. Christoffersen's likelihood-ratio tests pin three
properties of a VaR model:

1. **Unconditional coverage (Kupiec POF)** — breach rate π should = α
2. **Independence** — breaches should not cluster (tomorrow's breach prob
   independent of today's)
3. **Conditional coverage** — joint test of (1) + (2)

All three use chi-squared LR statistics (scipy.stats.chi2.sf for p-values).

[verified 2026-07-15] — all assertions hold on scipy 1.17.1, numpy 2.4.6,
fixed seeds. Reference: Christoffersen (1998), "Evaluating Interval
Forecasts", International Economic Review 39(4): 841-862.
"""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("scipy")
from scipy.stats import chi2  # noqa: E402


# ---------------------------------------------------------------------------
# Test-local Christoffersen LR implementation (scipy-only)
# ---------------------------------------------------------------------------

def christoffersen_lr(breaches: np.ndarray, alpha: float = 0.05) -> dict:
    """Christoffersen (1998) LR tests for VaR backtesting.

    breaches: int/bool array (1 = VaR exceeded, 0 = not).
    Returns dict with LR_uc, LR_ind, LR_cc + p-values + counts.
    """
    breaches = np.asarray(breaches, dtype=int)
    n = len(breaches)
    n_b = int(breaches.sum())
    pi = n_b / n  # observed breach rate

    # Kupiec POF (unconditional coverage)
    if pi == 0 or pi == 1:
        LR_uc = float("inf")
    else:
        LR_uc = -2.0 * (
            n_b * np.log(alpha) + (n - n_b) * np.log(1 - alpha)
            - n_b * np.log(pi) - (n - n_b) * np.log(1 - pi)
        )
    p_uc = float(chi2.sf(LR_uc, df=1))

    # Independence: 2x2 transition matrix
    n00 = n01 = n10 = n11 = 0
    for t in range(n - 1):
        i, j = breaches[t], breaches[t + 1]
        if i == 0 and j == 0:
            n00 += 1
        elif i == 0 and j == 1:
            n01 += 1
        elif i == 1 and j == 0:
            n10 += 1
        else:
            n11 += 1

    pi01 = n01 / (n00 + n01) if (n00 + n01) > 0 else 0.0
    pi11 = n11 / (n10 + n11) if (n10 + n11) > 0 else 0.0
    pi2 = (n01 + n11) / (n00 + n01 + n10 + n11)

    L0 = ((1 - pi2) ** (n00 + n10)) * (pi2 ** (n01 + n11)) if 0 < pi2 < 1 else 0.0
    L1a = ((1 - pi01) ** n00) * (pi01 ** n01) if 0 < pi01 < 1 else 0.0
    L1b = ((1 - pi11) ** n10) * (pi11 ** n11) if 0 < pi11 < 1 else 0.0
    L1 = L1a * L1b
    LR_ind = -2.0 * np.log(L0 / L1) if L0 > 0 and L1 > 0 else 0.0
    p_ind = float(chi2.sf(LR_ind, df=1))

    LR_cc = LR_uc + LR_ind
    p_cc = float(chi2.sf(LR_cc, df=2))

    return {
        "LR_uc": float(LR_uc),
        "LR_ind": float(LR_ind),
        "LR_cc": float(LR_cc),
        "p_uc": p_uc,
        "p_ind": p_ind,
        "p_cc": p_cc,
        "n_breaches": n_b,
        "expected": n * alpha,
        "pi": float(pi),
    }


# ---------------------------------------------------------------------------
# Invariant tests
# ---------------------------------------------------------------------------

class TestChristoffersenBacktest:
    """K8: LR tests must pass correct coverage and fail wrong coverage + clustering."""

    def test_correct_coverage_passes(self):
        """Breaches at exactly expected rate α must NOT reject (p_uc > 0.05).

        With iid Bernoulli(α) breaches, the Kupiec POF test should not
        reject the null that π = α. A regression that sign-flipped the LR
        or miscalculated df would spuriously reject.
        """
        rng = np.random.default_rng(42)
        n = 1000
        alpha = 0.05
        breaches = (rng.uniform(size=n) < alpha).astype(int)
        r = christoffersen_lr(breaches, alpha)
        assert r["p_uc"] > 0.05, (
            f"Correct coverage rejected by Kupiec: p_uc={r['p_uc']:.4f}, "
            f"breaches={r['n_breaches']}, expected={r['expected']:.0f}"
        )

    def test_too_few_breaches_fails_unconditional(self):
        """Breaches below expected rate must reject unconditional coverage.

        If the VaR model is too conservative (breach rate < α), the Kupiec
        test should flag it. A regression that always returned p > 0.05
        would fail to catch under-breaching.
        """
        rng = np.random.default_rng(42)
        n = 1000
        alpha = 0.05
        breaches = (rng.uniform(size=n) < 0.02).astype(int)  # 2% instead of 5%
        r = christoffersen_lr(breaches, alpha)
        assert r["p_uc"] < 0.05, (
            f"Under-breaching not flagged: p_uc={r['p_uc']:.4f}, "
            f"breaches={r['n_breaches']}, expected={r['expected']:.0f}"
        )

    def test_clustered_breaches_fail_independence(self):
        """Clustered breaches (high follow-through) must reject independence.

        If a breach today raises the prob of a breach tomorrow (vol
        clustering, regime persistence), the Christoffersen independence
        test should flag it. A regression that ignored the transition
        matrix would miss this.
        """
        rng = np.random.default_rng(42)
        n = 1000
        alpha = 0.05
        breaches = np.zeros(n, dtype=int)
        for t in range(1, n):
            if breaches[t - 1] == 1:
                breaches[t] = 1 if rng.uniform() < 0.3 else 0  # 30% follow-through
            else:
                breaches[t] = 1 if rng.uniform() < 0.04 else 0
        r = christoffersen_lr(breaches, alpha)
        assert r["p_ind"] < 0.05, (
            f"Clustering not flagged by independence test: p_ind={r['p_ind']:.4f}"
        )

    def test_conditional_coverage_is_sum_of_uc_and_ind(self):
        """LR_cc must equal LR_uc + LR_ind (chi2 dof adds).

        Sanity check on the conditional coverage composition. A regression
        that computed LR_cc independently (not as the sum) would drift.
        """
        rng = np.random.default_rng(42)
        breaches = (rng.uniform(size=500) < 0.05).astype(int)
        r = christoffersen_lr(breaches, 0.05)
        assert abs(r["LR_cc"] - (r["LR_uc"] + r["LR_ind"])) < 1e-9, (
            f"LR_cc != LR_uc + LR_ind: "
            f"cc={r['LR_cc']:.6f}, uc+ind={r['LR_uc'] + r['LR_ind']:.6f}"
        )
