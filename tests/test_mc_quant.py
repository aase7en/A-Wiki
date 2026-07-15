"""Tests for the reusable quant-risk module (O-A).

O-A: scripts/mc_quant.py exposes the SKILL.md §3 Quant Risk Metrics table as a
real API — var_estimate(), cvar_estimate(), sharpe_distribution(),
rr_distribution(). Before O-A these metrics only lived inside individual test
files as inline computations, so no external agent/skill could call them.

Per AGENTS.md rule 7 (render, don't dump), the module emits no HTML; it returns
plain Python objects (float / dict) that callers render themselves.

The module is imported via importlib (no package; script lives in scripts/)
mirroring the test_benchmark_mc.py / test_render_mc_convergence.py pattern.

[verified 2026-07-16] scipy 1.17.1, numpy 2.4.6.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("scipy")

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "scripts" / "mc_quant.py"


@pytest.fixture(scope="module")
def mc_quant_module():
    """Load scripts/mc_quant.py as a module (no package)."""
    spec = importlib.util.spec_from_file_location("mc_quant", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestMcQuantApi:
    """O-A: SKILL.md §3 Quant Risk Metrics table must be backed by real code."""

    def test_var_estimate_known_normal(self, mc_quant_module):
        """VaR(α=5%) of standard-normal samples must ≈ analytic z-score -1.6449.

        H6 discipline: prototype verified np.percentile(N(0,1), 5) → -1.658 at
        N=100000 (seed 42), within 5% of -1.6449. Direction confirmed before
        asserting. Catches a regression that flipped percentile (e.g. used
        100-α or sorted ascending then indexed from the wrong end).
        """
        rng = np.random.default_rng(42)
        samples = rng.standard_normal(100_000)
        var = mc_quant_module.var_estimate(samples, alpha=0.05)
        assert isinstance(var, float)
        # VaR(5%) N(0,1) ≈ -1.645; allow generous 10% tolerance (MC noise)
        assert -1.85 < var < -1.45, (
            f"VaR(5%) of N(0,1) should be ≈ -1.645, got {var:.4f}"
        )

    def test_cvar_exceeds_var_in_tail(self, mc_quant_module):
        """CVaR(α) must be worse (more negative) than VaR(α).

        CVaR = E[loss | loss ≤ VaR] is the tail mean beyond the percentile, so
        it must be ≤ VaR (strictly < on continuous distributions). A regression
        that computed CVaR as `samples[samples <= 0].mean()` or used the wrong
        side of the tail would flip this invariant.
        """
        rng = np.random.default_rng(7)
        samples = rng.standard_normal(50_000)
        var = mc_quant_module.var_estimate(samples, alpha=0.05)
        cvar = mc_quant_module.cvar_estimate(samples, alpha=0.05)
        assert cvar < var, (
            f"CVaR {cvar:.4f} must be < VaR {var:.4f} (tail mean is worse)"
        )

    def test_sharpe_distribution_returns_dict(self, mc_quant_module):
        """sharpe_distribution must return {median, p5, p95, mean, std}.

        SKILL.md §3 declares Sharpe is "reported as distribution + CI", not a
        point estimate. Per-path Sharpe is aggregated into percentile band.
        A regression returning a single float would lose the uncertainty info.
        """
        rng = np.random.default_rng(11)
        # (N_paths, T) daily log-returns — shape contract from §3 workflow
        paths = rng.standard_normal((2000, 252)) * 0.01
        result = mc_quant_module.sharpe_distribution(paths)
        assert isinstance(result, dict)
        for key in ("median", "p5", "p95", "mean", "std"):
            assert key in result, f"missing key {key} in sharpe_distribution"
            assert isinstance(result[key], (int, float)), (
                f"{key} must be numeric, got {type(result[key])}"
            )
        # p5 ≤ median ≤ p95 (percentile ordering sanity)
        assert result["p5"] <= result["median"] <= result["p95"], (
            f"percentile ordering broken: p5={result['p5']}, "
            f"median={result['median']}, p95={result['p95']}"
        )

    def test_module_has_non_advisory_banner(self, mc_quant_module):
        """Iron Law #8: module docstring must state PAPER-ONLY / NON-ADVISORY.

        The module is reusable across agents (finance-analyst subagent, etc.),
        so the non-advisory framing must travel with the code, not just live in
        SKILL.md prose. A regression that stripped the docstring would let
        downstream agents treat outputs as actionable advice.
        """
        doc = (mc_quant_module.__doc__ or "") + " " + getattr(
            mc_quant_module, "NON_ADVISORY_BANNER", ""
        )
        doc_upper = doc.upper()
        assert "PAPER-ONLY" in doc_upper or "NON-ADVISORY" in doc_upper, (
            "Iron Law #8: module must declare PAPER-ONLY or NON-ADVISORY"
        )
