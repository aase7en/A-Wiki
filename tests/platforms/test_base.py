"""Tests for scripts/lib/platforms/base.py.

Iron Law #1 — test written FIRST. The `ordered_backends` 2-pass routing
pattern is ADAPTED from Agent-Reach (channels/base.py:29-70, MIT, 2026
Pnant/Panniantong) — re-implemented to A-Wiki conventions (no third-party
deps, plain ABC, narrower scope).

base.py must provide:
- `Channel` ABC with: name, backends list, check(), ordered_backends(config)
- `ordered_backends(config=None)`: ordered candidate list where:
  - The declared order is preserved unless `<name>_backend` override exists
  - The override backend is promoted to front (only if it matches a declared one)
- `check_all(channels, config=None)`: returns dict[backend_name -> status_dict]
  where each status_dict has keys (status, message, active_backend).
  status ∈ {"ok", "warn", "error"}. ONE broken channel must not kill the
  whole report (resilience pattern borrowed from Agent-Reach doctor.py:16-45).
"""
from __future__ import annotations

import pytest


# ── ordered_backends ──────────────────────────────────────────────────────

class TestOrderedBackends:

    def test_module_importable(self):
        from platforms import base
        assert hasattr(base, "Channel")

    def test_preserves_declared_order_when_no_override(self):
        from platforms.base import Channel

        class FakeChannel(Channel):
            name = "demo"
            backends = ["a", "b", "c"]
            def check(self, config=None):  # type: ignore[override]
                return ("ok", "fine", "a")

        c = FakeChannel()
        assert c.ordered_backends() == ["a", "b", "c"]

    def test_override_promotes_matching_backend_to_front(self):
        from platforms.base import Channel

        class FakeChannel(Channel):
            name = "demo"
            backends = ["a", "b", "c"]
            def check(self, config=None):  # type: ignore[override]
                return ("ok", "fine", "b")

        c = FakeChannel()
        # config key is f"{name}_backend" — override key matches a backend
        assert c.ordered_backends({"demo_backend": "c"}) == ["c", "a", "b"]

    def test_override_ignored_when_no_match(self):
        """User asked for a backend that doesn't exist — fall back to declared order."""
        from platforms.base import Channel

        class FakeChannel(Channel):
            name = "demo"
            backends = ["a", "b"]
            def check(self, config=None):  # type: ignore[override]
                return ("ok", "fine", "a")

        c = FakeChannel()
        assert c.ordered_backends({"demo_backend": "nonexistent"}) == ["a", "b"]

    def test_empty_backends_returns_empty(self):
        from platforms.base import Channel

        class FakeChannel(Channel):
            name = "demo"
            backends = []
            def check(self, config=None):  # type: ignore[override]
                return ("warn", "no backends", None)

        c = FakeChannel()
        assert c.ordered_backends() == []


# ── check_all resilience ─────────────────────────────────────────────────

class TestCheckAllResilience:

    def test_one_broken_channel_does_not_kill_report(self):
        """If channel B raises, channels A and C must still get reported."""
        from platforms.base import Channel, check_all

        class Good(Channel):
            name = "good"
            backends = ["x"]
            def check(self, config=None):  # type: ignore[override]
                return ("ok", "alive", "x")

        class Bad(Channel):
            name = "bad"
            backends = ["x"]
            def check(self, config=None):  # type: ignore[override]
                raise RuntimeError("kaboom")

        class AlsoGood(Channel):
            name = "alsogood"
            backends = ["x"]
            def check(self, config=None):  # type: ignore[override]
                return ("warn", "needs login", "x")

        result = check_all([Good(), Bad(), AlsoGood()])
        assert "good" in result
        assert "bad" in result
        assert "alsogood" in result
        # Bad channel must be reported as error, not crash the report
        assert result["bad"]["status"] == "error"
        assert "kaboom" in result["bad"]["message"]
        # Other channels unaffected
        assert result["good"]["status"] == "ok"
        assert result["alsogood"]["status"] == "warn"

    def test_check_all_returns_status_message_active_for_each(self):
        from platforms.base import Channel, check_all

        class Foo(Channel):
            name = "foo"
            backends = ["x"]
            def check(self, config=None):  # type: ignore[override]
                return ("ok", "running", "x")

        result = check_all([Foo()])
        for key in ("status", "message", "active_backend"):
            assert key in result["foo"]
