"""Tests for scripts/live-dashboard/mc_snapshot.py — dashboard MC risk payload (P1).

Iron Law #1: failing tests written FIRST. These pin the contract of
build_payload() before the implementation exists.

P1 wraps `scripts/mc_quant.py::_demo()` → JSON payload for the
`GET /api/mc-snapshot` dashboard endpoint. All data is synthetic N(0,1)
seed=42 (PAPER-ONLY · NON-ADVISORY — Iron Law #8).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))

# scipy/numpy come in transitively via mc_quant; guard once at import time.
pytest.importorskip("numpy")

import mc_snapshot  # noqa: E402  -- module under test (created by P1)


class TestMcSnapshotPayload:
    """Contract for build_payload() — the JSON served at /api/mc-snapshot."""

    def test_build_payload_returns_dict_with_banner(self):
        """Payload is a dict; banner surfaces Iron Law #8 (paper-only)."""
        payload = mc_snapshot.build_payload()
        assert isinstance(payload, dict)
        banner = payload.get("banner", "")
        assert "PAPER-ONLY" in banner or "NON-ADVISORY" in banner, (
            f"Iron Law #8 banner missing/weak: {banner!r}"
        )

    def test_build_payload_has_var_cvar_sharpe_rr(self):
        """All four MC risk metrics are present (mc_quant._demo contract)."""
        payload = mc_snapshot.build_payload()
        for key in ("var_5pct", "cvar_5pct", "sharpe_distribution", "rr_distribution"):
            assert key in payload, f"missing metric key: {key}"

    def test_build_payload_data_field_marks_synthetic(self):
        """data field must mark synthetic + seed — no real-data leak surface."""
        payload = mc_snapshot.build_payload()
        data = str(payload.get("data", ""))
        assert "synthetic" in data.lower() or "seed=42" in data, (
            f"data field must flag synthetic seed: {data!r}"
        )

    def test_build_payload_is_json_serializable(self):
        """Payload must serialize — dashboard _json_response calls json.dumps."""
        payload = mc_snapshot.build_payload()
        # Must not raise. Bytes length is a sanity floor (banner alone > 30).
        body = json.dumps(payload, ensure_ascii=False)
        assert len(body) > 30
