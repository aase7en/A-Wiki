"""Tests for the MC convergence widget renderer (K7).

Pins Iron Law #8 compliance (non-advisory banner must appear) + structural
invariants of the SVG output. The renderer is a pure function (dict → HTML
string), so tests call it directly without subprocess.

[verified 2026-07-15]
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Load the renderer module directly (it's a script, not a package)
REPO_ROOT = Path(__file__).resolve().parent.parent
RENDERER_PATH = REPO_ROOT / "scripts" / "render_mc_convergence.py"


@pytest.fixture(scope="module")
def renderer():
    """Load render_mc_convergence.py as a module."""
    spec = importlib.util.spec_from_file_location("render_mc_convergence", RENDERER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SAMPLE_DATA = {
    "title": "Test MC Convergence",
    "subtitle": "synthetic test",
    "non_advisory_banner": "PAPER-ONLY · NON-ADVISORY · synthetic data",
    "threshold_pct": 1.0,
    "series": [
        {"n": 1000, "mean": 1.04, "se": 0.014, "doubling_delta_pct": 4.8, "converged": False},
        {"n": 10000, "mean": 1.03, "se": 0.004, "doubling_delta_pct": 0.02, "converged": True},
    ],
}


class TestRenderMcConvergence:
    """K7: renderer must emit SVG with threshold line + banner + handle empty data."""

    def test_renderer_emits_svg_with_threshold_line(self, renderer):
        """Output must contain <svg> and the threshold line + label."""
        html = renderer.render_widget(SAMPLE_DATA)
        assert "<svg" in html, "No SVG element in output"
        # Label uses f"{threshold}% threshold" — 1.0 renders as "1.0%"
        assert "threshold" in html.lower(), "Threshold line/label missing"
        assert "% threshold" in html, "Threshold percentage label missing"

    def test_renderer_includes_non_advisory_banner(self, renderer):
        """Iron Law #8 compliance: non-advisory banner must appear in output."""
        html = renderer.render_widget(SAMPLE_DATA)
        assert "PAPER-ONLY" in html, "Iron Law #8 banner missing"
        assert "NON-ADVISORY" in html, "Non-advisory marker missing"
        assert "synthetic" in html.lower(), "Synthetic-data disclaimer missing"

    def test_renderer_handles_empty_data(self, renderer):
        """Empty or malformed data must produce graceful fallback, not crash."""
        html_empty = renderer.render_widget({})
        assert "No convergence data" in html_empty or "<svg" not in html_empty, (
            "Empty data should fall back gracefully"
        )
        html_no_series = renderer.render_widget({"title": "x", "series": []})
        assert "No convergence data" in html_no_series, (
            "Missing series should fall back gracefully"
        )

    def test_renderer_marks_converged_vs_not_converged(self, renderer):
        """Converged points must be green; non-converged must be red."""
        html = renderer.render_widget(SAMPLE_DATA)
        # Green for converged (#22c55e), red for non-converged (#ef4444)
        assert "#22c55e" in html, "No green marker for converged point"
        assert "#ef4444" in html, "No red marker for non-converged point"
