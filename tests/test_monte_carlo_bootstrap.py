"""Integration tests for bootstrap historical simulation as an extension of the
monte-carlo-quant-analysis skill (§Extensions — J4 Bootstrap subsection).

J4: SKILL.md mentions "bootstrap" in distribution-selection table + probability
foundations, but ships no code and does not distinguish iid vs block bootstrap.
These tests pin the invariants a bootstrap sampler MUST satisfy, so that the
code added to the skill (J4 subsection) can be validated against them.

Key distinction:
- **iid bootstrap** — resample individual observations → destroys serial
  correlation. Correct for stationary, independent data.
- **block bootstrap** (circular) — resample contiguous blocks → preserves
  short-range autocorrelation. Required for time series with temporal
  dependence (AR, GARCH, vol-clustering).

[verified 2026-07-15] — all assertions hold on numpy 2.4.6, fixed seeds.
"""
from __future__ import annotations

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Test-local bootstrap sampler
# ---------------------------------------------------------------------------

def bootstrap_returns(
    historical: np.ndarray,
    n: int,
    rng: np.random.Generator,
    block_size: int | None = None,
) -> np.ndarray:
    """Resample n returns from historical.

    block_size=None → iid bootstrap (destroys serial correlation).
    block_size=int  → circular block bootstrap (preserves autocorrelation
                      within each block).
    """
    N = len(historical)
    if block_size is None:
        idx = rng.integers(0, N, size=n)
        return historical[idx]
    n_blocks = (n + block_size - 1) // block_size
    starts = rng.integers(0, N, size=n_blocks)
    idx = np.concatenate(
        [np.arange(s, s + block_size) % N for s in starts]
    )[:n]
    return historical[idx]


def autocorr(x: np.ndarray, lag: int = 1) -> float:
    """Sample autocorrelation at given lag."""
    return float(np.corrcoef(x[:-lag], x[lag:])[0, 1])


# ---------------------------------------------------------------------------
# Invariant tests
# ---------------------------------------------------------------------------

class TestBootstrapInvariants:
    """J4: bootstrap must respect autocorrelation preservation + range containment."""

    def test_block_bootstrap_preserves_autocorrelation(self):
        """Block bootstrap must preserve AR(1) autocorrelation; iid must not.

        On a strong AR(1) series (φ=0.7, lag-1 autocorr ≈ 0.72), block bootstrap
        with block_size large enough to span multiple autocorrelation lengths
        must reproduce the autocorrelation, while iid bootstrap must destroy it
        (autocorr → 0). A bug that shuffles within blocks or draws individual
        samples inside block mode would fail this.
        """
        rng = np.random.default_rng(42)
        N = 1000
        phi = 0.7
        e = rng.standard_normal(N)
        ar1 = np.zeros(N)
        for t in range(1, N):
            ar1[t] = phi * ar1[t - 1] + e[t]
        original_ac = autocorr(ar1)

        # iid bootstrap (destroys autocorr)
        rng_iid = np.random.default_rng(42)
        iid = bootstrap_returns(ar1, 5000, rng_iid, block_size=None)
        iid_ac = autocorr(iid)

        # block bootstrap (preserves autocorr — block_size=50 >> autocorr length)
        rng_block = np.random.default_rng(42)
        block = bootstrap_returns(ar1, 5000, rng_block, block_size=50)
        block_ac = autocorr(block)

        assert block_ac > iid_ac, (
            f"Block bootstrap did not preserve more autocorrelation than iid: "
            f"block_ac={block_ac:.4f}, iid_ac={iid_ac:.4f}"
        )
        # Block should recover at least half the original autocorrelation
        assert block_ac > 0.5 * original_ac, (
            f"Block bootstrap under-recovered autocorrelation: "
            f"block_ac={block_ac:.4f}, original={original_ac:.4f}"
        )

    def test_bootstrap_var_within_historical_range(self):
        """Bootstrap VaR(5%) must lie within [min, max] of the historical sample.

        Bootstrap resamples from empirical data, so no synthetic value outside
        the historical range can appear. A regression that interpolated or
        extrapolated would fail this.
        """
        rng = np.random.default_rng(42)
        # Synthetic daily returns — small drift, modest vol
        historical = rng.standard_normal(500) * 0.01 + 0.0005
        boot = bootstrap_returns(historical, 10_000, np.random.default_rng(42), block_size=None)
        var_5pct = float(np.quantile(boot, 0.05))

        h_min = float(historical.min())
        h_max = float(historical.max())

        assert h_min <= var_5pct <= h_max, (
            f"Bootstrap VaR(5%) outside historical range: "
            f"var={var_5pct:.6f}, range=[{h_min:.6f}, {h_max:.6f}]"
        )

    def test_iid_bootstrap_destroys_serial_correlation(self):
        """iid bootstrap must produce near-zero autocorrelation on AR(1) input.

        Sanity inverse of test_block_bootstrap_preserves_autocorrelation:
        drawing individual samples at random destroys temporal ordering, so
        lag-1 autocorr must collapse to ~0. A regression that accidentally
        used block mode when block_size=None was requested would fail this.
        """
        rng = np.random.default_rng(123)
        N = 1000
        phi = 0.7
        e = rng.standard_normal(N)
        ar1 = np.zeros(N)
        for t in range(1, N):
            ar1[t] = phi * ar1[t - 1] + e[t]

        rng_iid = np.random.default_rng(123)
        iid = bootstrap_returns(ar1, 5000, rng_iid, block_size=None)
        iid_ac = autocorr(iid)

        assert abs(iid_ac) < 0.1, (
            f"iid bootstrap did not destroy serial correlation: "
            f"autocorr(1)={iid_ac:.4f} (should be ~0)"
        )
