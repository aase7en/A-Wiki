"""
test_vendor_watch.py — tests for scripts/lib/vendor_watch.py

Vendor upstream-watch: on SessionStart, silently `git ls-remote <url> HEAD`
each vendored-skill upstream (throttled to once per 24h per vendor, cached in
.tmp/vendor-check-cache.json) and print a one-line nudge only when the
upstream HEAD sha has moved since the last known sha. Any failure (offline,
timeout, corrupt cache, bad JSON) must degrade to silence — never raise and
never spam.

Iron Law #1: these tests are written before scripts/lib/vendor_watch.py
exists / before its logic is correct.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import vendor_watch as vw  # noqa: E402


# ── VENDORS table ──────────────────────────────────────────────────────

class TestVendorsTable:
    def test_vendors_is_nonempty_tuple(self):
        assert isinstance(vw.VENDORS, (tuple, list))
        assert len(vw.VENDORS) >= 5

    def test_vendors_have_required_fields(self):
        for vendor in vw.VENDORS:
            assert vendor.name
            assert vendor.url.startswith("https://")
            assert vendor.refresh_script.startswith("scripts/refresh-")

    def test_vendors_cover_known_upstreams(self):
        names = {v.name for v in vw.VENDORS}
        # Derived from scripts/refresh-9arm.sh, refresh-ecosystem.sh,
        # refresh-mattpocock.sh, refresh-anthropic-skills.sh, refresh-skillopt.sh
        assert names == {"9arm", "ecosystem", "mattpocock", "anthropic-skills", "skillopt"}

    def test_vendor_urls_match_refresh_scripts_on_disk(self):
        """Cross-check the hardcoded URL table against the actual refresh scripts
        so the table can't silently drift from the source of truth."""
        expected_urls = {
            "9arm": "https://github.com/thananon/9arm-skills.git",
            "ecosystem": "https://github.com/affaan-m/ECC.git",
            "mattpocock": "https://github.com/mattpocock/skills.git",
            "anthropic-skills": "https://github.com/anthropics/skills.git",
            "skillopt": "https://github.com/microsoft/SkillOpt.git",
        }
        for vendor in vw.VENDORS:
            assert vendor.url == expected_urls[vendor.name]

    def test_refresh_scripts_exist_on_disk(self):
        for vendor in vw.VENDORS:
            script_path = REPO_ROOT / vendor.refresh_script
            assert script_path.is_file(), f"missing {script_path}"


# ── cache read/write ───────────────────────────────────────────────────

class TestCache:
    def test_load_cache_missing_file_returns_empty_dict(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"
        assert vw.load_cache(cache_path) == {}

    def test_load_cache_corrupt_json_returns_empty_dict(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"
        cache_path.write_text("{not valid json", encoding="utf-8")
        assert vw.load_cache(cache_path) == {}

    def test_load_cache_non_dict_json_returns_empty_dict(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"
        cache_path.write_text("[1, 2, 3]", encoding="utf-8")
        assert vw.load_cache(cache_path) == {}

    def test_save_then_load_roundtrip(self, tmp_path):
        cache_path = tmp_path / "nested" / "vendor-check-cache.json"
        data = {"9arm": {"last_checked": "2026-07-10T00:00:00+00:00", "last_sha": "abc1234"}}
        vw.save_cache(data, cache_path)
        assert cache_path.is_file()
        assert vw.load_cache(cache_path) == data

    def test_save_cache_never_raises_on_bad_path(self, tmp_path):
        # Path where a parent component is a file, not a directory -> mkdir fails.
        blocker = tmp_path / "blocker"
        blocker.write_text("x", encoding="utf-8")
        bad_path = blocker / "vendor-check-cache.json"
        vw.save_cache({"a": 1}, bad_path)  # must not raise


# ── check_vendors: staleness gate ────────────────────────────────────

class TestStalenessGate:
    def test_fresh_cache_entry_skips_network_call(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"
        now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
        fresh = (now - timedelta(hours=1)).isoformat()
        vendor = vw.Vendor("solo", "https://example.invalid/solo.git", "scripts/refresh-solo.sh")
        vw.save_cache({"solo": {"last_checked": fresh, "last_sha": "deadbee"}}, cache_path)

        calls = []

        def runner(name, url):
            calls.append((name, url))
            return "1111111"

        notices = vw.check_vendors(
            vendors=(vendor,), cache_path=cache_path, runner=runner, now=now,
        )
        assert calls == []
        assert notices == []

    def test_stale_cache_entry_triggers_network_call(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"
        now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
        old = (now - timedelta(hours=25)).isoformat()
        vendor = vw.Vendor("solo", "https://example.invalid/solo.git", "scripts/refresh-solo.sh")
        vw.save_cache({"solo": {"last_checked": old, "last_sha": "deadbee"}}, cache_path)

        calls = []

        def runner(name, url):
            calls.append((name, url))
            return "deadbee"

        vw.check_vendors(vendors=(vendor,), cache_path=cache_path, runner=runner, now=now)
        assert calls == [("solo", "https://example.invalid/solo.git")]

    def test_missing_cache_entry_is_treated_as_stale(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"  # no file at all
        vendor = vw.Vendor("solo", "https://example.invalid/solo.git", "scripts/refresh-solo.sh")

        calls = []

        def runner(name, url):
            calls.append((name, url))
            return "abc0000"

        vw.check_vendors(vendors=(vendor,), cache_path=cache_path, runner=runner)
        assert calls == [("solo", "https://example.invalid/solo.git")]

    def test_exactly_24h_boundary_is_not_yet_stale(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"
        now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
        exactly_24h = (now - timedelta(hours=24)).isoformat()
        vendor = vw.Vendor("solo", "https://example.invalid/solo.git", "scripts/refresh-solo.sh")
        vw.save_cache({"solo": {"last_checked": exactly_24h, "last_sha": "deadbee"}}, cache_path)

        calls = []
        vw.check_vendors(
            vendors=(vendor,), cache_path=cache_path,
            runner=lambda n, u: calls.append((n, u)) or "deadbee", now=now,
        )
        assert calls == []


# ── check_vendors: notify decision ─────────────────────────────────────

class TestNotifyDecision:
    def _vendor(self):
        return vw.Vendor("solo", "https://example.invalid/solo.git", "scripts/refresh-solo.sh")

    def test_first_ever_check_writes_cache_but_does_not_notify(self, tmp_path):
        """No prior sha to compare against -> establish baseline silently."""
        cache_path = tmp_path / "vendor-check-cache.json"
        vendor = self._vendor()
        notices = vw.check_vendors(
            vendors=(vendor,), cache_path=cache_path, runner=lambda n, u: "aaa1111",
        )
        assert notices == []
        cache = vw.load_cache(cache_path)
        assert cache["solo"]["last_sha"] == "aaa1111"
        assert "last_checked" in cache["solo"]

    def test_sha_unchanged_since_last_check_is_quiet(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"
        now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
        old = (now - timedelta(hours=25)).isoformat()
        vendor = self._vendor()
        vw.save_cache({"solo": {"last_checked": old, "last_sha": "aaa1111"}}, cache_path)

        notices = vw.check_vendors(
            vendors=(vendor,), cache_path=cache_path,
            runner=lambda n, u: "aaa1111", now=now,
        )
        assert notices == []

    def test_sha_changed_since_last_check_notifies(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"
        now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
        old = (now - timedelta(hours=25)).isoformat()
        vendor = self._vendor()
        vw.save_cache({"solo": {"last_checked": old, "last_sha": "aaa1111"}}, cache_path)

        notices = vw.check_vendors(
            vendors=(vendor,), cache_path=cache_path,
            runner=lambda n, u: "bbb2222", now=now,
        )
        assert len(notices) == 1
        assert "bbb2222"[:7] in notices[0]
        cache = vw.load_cache(cache_path)
        assert cache["solo"]["last_sha"] == "bbb2222"

    def test_multiple_vendors_only_changed_ones_notify(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"
        now = datetime(2026, 7, 10, 12, 0, 0, tzinfo=timezone.utc)
        old = (now - timedelta(hours=25)).isoformat()
        v1 = vw.Vendor("one", "https://example.invalid/one.git", "scripts/refresh-one.sh")
        v2 = vw.Vendor("two", "https://example.invalid/two.git", "scripts/refresh-two.sh")
        vw.save_cache(
            {
                "one": {"last_checked": old, "last_sha": "1111111"},
                "two": {"last_checked": old, "last_sha": "2222222"},
            },
            cache_path,
        )

        def runner(name, url):
            return {"one": "1111111", "two": "2222999"}[name]

        notices = vw.check_vendors(vendors=(v1, v2), cache_path=cache_path, runner=runner, now=now)
        assert len(notices) == 1
        assert "two" in notices[0]


# ── check_vendors: silent-failure guarantee ─────────────────────────────

class TestSilentFailure:
    def _vendor(self):
        return vw.Vendor("solo", "https://example.invalid/solo.git", "scripts/refresh-solo.sh")

    def test_runner_exception_is_swallowed(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"

        def boom(name, url):
            raise RuntimeError("network is down")

        notices = vw.check_vendors(vendors=(self._vendor(),), cache_path=cache_path, runner=boom)
        assert notices == []

    def test_runner_returning_none_offline_is_silent(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"
        notices = vw.check_vendors(
            vendors=(self._vendor(),), cache_path=cache_path, runner=lambda n, u: None,
        )
        assert notices == []
        # No sha was learned, so nothing should have been written for this vendor.
        cache = vw.load_cache(cache_path)
        assert "solo" not in cache or cache.get("solo", {}).get("last_sha") is None

    def test_one_vendor_failing_does_not_block_others(self, tmp_path):
        cache_path = tmp_path / "vendor-check-cache.json"
        v1 = vw.Vendor("broken", "https://example.invalid/broken.git", "scripts/refresh-broken.sh")
        v2 = vw.Vendor("ok", "https://example.invalid/ok.git", "scripts/refresh-ok.sh")

        def runner(name, url):
            if name == "broken":
                raise RuntimeError("boom")
            return "cafe123"

        notices = vw.check_vendors(vendors=(v1, v2), cache_path=cache_path, runner=runner)
        # first-ever check for both -> baseline only, no notices, but "ok" cached
        assert notices == []
        cache = vw.load_cache(cache_path)
        assert "ok" in cache
        assert "broken" not in cache

    def test_default_runner_never_raises_on_timeout(self, monkeypatch):
        import subprocess

        def fake_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="git", timeout=3)

        monkeypatch.setattr(vw.subprocess, "run", fake_run)
        result = vw.default_runner("solo", "https://example.invalid/solo.git")
        assert result is None

    def test_default_runner_never_raises_on_generic_exception(self, monkeypatch):
        def fake_run(*args, **kwargs):
            raise OSError("no network")

        monkeypatch.setattr(vw.subprocess, "run", fake_run)
        result = vw.default_runner("solo", "https://example.invalid/solo.git")
        assert result is None

    def test_default_runner_parses_ls_remote_output(self, monkeypatch):
        class FakeResult:
            returncode = 0
            stdout = "abcdef0123456789abcdef0123456789abcdef01\tHEAD\n"
            stderr = ""

        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["timeout"] = kwargs.get("timeout")
            return FakeResult()

        monkeypatch.setattr(vw.subprocess, "run", fake_run)
        result = vw.default_runner("solo", "https://example.invalid/solo.git")
        assert result == "abcdef0123456789abcdef0123456789abcdef01"
        assert captured["cmd"] == ["git", "ls-remote", "https://example.invalid/solo.git", "HEAD"]
        assert captured["timeout"] == 3

    def test_default_runner_nonzero_returncode_is_none(self, monkeypatch):
        class FakeResult:
            returncode = 128
            stdout = ""
            stderr = "fatal: could not read"

        monkeypatch.setattr(vw.subprocess, "run", lambda *a, **k: FakeResult())
        assert vw.default_runner("solo", "https://example.invalid/solo.git") is None

    def test_default_runner_empty_stdout_is_none(self, monkeypatch):
        class FakeResult:
            returncode = 0
            stdout = ""
            stderr = ""

        monkeypatch.setattr(vw.subprocess, "run", lambda *a, **k: FakeResult())
        assert vw.default_runner("solo", "https://example.invalid/solo.git") is None

    def test_check_vendors_never_raises_even_with_broken_cache_dir(self, tmp_path):
        """Whole call must degrade to empty list, never raise, even if cache
        write target is unwritable."""
        blocker = tmp_path / "blocker"
        blocker.write_text("x", encoding="utf-8")
        bad_cache_path = blocker / "vendor-check-cache.json"
        notices = vw.check_vendors(
            vendors=(self._vendor(),), cache_path=bad_cache_path, runner=lambda n, u: "abc1234",
        )
        assert notices == []  # first run -> baseline only anyway


# ── message format ───────────────────────────────────────────────────

class TestMessageFormat:
    def test_format_notice_matches_spec(self):
        vendor = vw.Vendor("9arm", "https://github.com/thananon/9arm-skills.git", "scripts/refresh-9arm.sh")
        msg = vw.format_notice(vendor, "abcdef0123456789")
        assert msg == "🔄 vendor 9arm: new upstream commit abcdef0 — run: bash scripts/refresh-9arm.sh"

    def test_format_notice_truncates_sha_to_7_chars(self):
        vendor = vw.Vendor("ecosystem", "https://github.com/affaan-m/ECC.git", "scripts/refresh-ecosystem.sh")
        msg = vw.format_notice(vendor, "1234567890")
        assert "1234567" in msg
        assert "1234567890" not in msg


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
