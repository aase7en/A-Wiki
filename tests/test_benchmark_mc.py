"""Tests for the MC benchmark harness (M2).

M2: scripts/benchmark_mc.py runs pseudo-MC + Sobol + Halton at increasing N,
records (N, method, estimate, abs_error, se, wall_time_s), emits compact JSON.
Per AGENTS.md rule 7 (render, don't dump), the JSON is the durable artifact;
any HTML render is a gitignored leaf. This test pins the JSON contract so the
harness stays a reusable tool.

The harness is imported via importlib (no package; script lives in scripts/)
mirroring the test_render_mc_convergence.py pattern.

[verified 2026-07-15] scipy 1.17.1, numpy 2.4.6.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

pytest.importorskip("scipy")

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS_PATH = REPO_ROOT / "scripts" / "benchmark_mc.py"


@pytest.fixture(scope="module")
def harness_module():
    """Load scripts/benchmark_mc.py as a module (no package)."""
    spec = importlib.util.spec_from_file_location("benchmark_mc", HARNESS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestBenchmarkMcHarness:
    """M2: harness must emit valid JSON, scale accuracy with N, record timing."""

    def test_harness_emits_valid_json(self, harness_module):
        """run_benchmark() must return a dict with the documented contract.

        Top-level keys: title, subtitle, non_advisory_banner, integrand,
        d, seed, levels. Each level has N + results{method:{estimate,
        abs_error, se, wall_time_s}}. A regression that renamed keys would
        break downstream renderers.
        """
        result = harness_module.run_benchmark(
            integrand="normal_mean",
            n_levels=[1000, 4096],
            d=3,
            seed=42,
        )
        assert isinstance(result, dict)
        for key in ("title", "subtitle", "non_advisory_banner",
                    "integrand", "d", "seed", "levels"):
            assert key in result, f"missing top-level key: {key}"
        assert result["non_advisory_banner"], "Iron Law #8 banner must not be empty"
        assert isinstance(result["levels"], list)
        assert len(result["levels"]) == 2

        for lvl in result["levels"]:
            assert "N" in lvl and isinstance(lvl["N"], int)
            assert "results" in lvl
            for method in ("pseudo", "sobol", "halton"):
                assert method in lvl["results"], f"missing method {method} at N={lvl['N']}"
                r = lvl["results"][method]
                for field in ("estimate", "abs_error", "se", "wall_time_s"):
                    assert field in r, f"missing field {field} in {method}@N={lvl['N']}"
                    assert isinstance(r[field], (int, float)), (
                        f"{field} must be numeric, got {type(r[field])}"
                    )

    def test_harness_scales_with_n(self, harness_module):
        """QMC abs_error must decrease as N increases (sanity on known integral).

        For the normal_mean integrand (E[N(0,1)]=0), Sobol/Halton error should
        shrink as N grows (O(1/N) QMC rate). This catches a regression that
        broke the QMC samplers (e.g. didn't pass N through).
        """
        result = harness_module.run_benchmark(
            integrand="normal_mean",
            n_levels=[1024, 16384],  # 10× growth
            d=3,
            seed=42,
        )
        sobol_err_small = result["levels"][0]["results"]["sobol"]["abs_error"]
        sobol_err_large = result["levels"][1]["results"]["sobol"]["abs_error"]
        assert sobol_err_large < sobol_err_small, (
            f"Sobol error did not decrease with N: "
            f"N=1024 err={sobol_err_small:.6f}, N=16384 err={sobol_err_large:.6f}"
        )

    def test_harness_records_wall_time(self, harness_module):
        """Each method at each N must have a non-negative wall_time_s.

        Timing is the second axis of the benchmark (accuracy vs cost). A
        regression that forgot to time would leave zero/missing values.
        """
        result = harness_module.run_benchmark(
            integrand="normal_mean",
            n_levels=[1000],
            d=2,
            seed=42,
        )
        for lvl in result["levels"]:
            for method, r in lvl["results"].items():
                assert r["wall_time_s"] >= 0.0, (
                    f"wall_time_s negative for {method}@N={lvl['N']}: {r['wall_time_s']}"
                )
