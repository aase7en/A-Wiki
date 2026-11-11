"""WO-AWIKI-PIPE-01: read-only knowledge-pipeline status projection.

Contract tests (RED first) for `python -m conductor pipeline --json` —
the brain-side seam consumed by the A-Wiki-Conductor Inspector (AWC #739).
The projection must be evidence-derived and read-only: UNKNOWN over invented
values, no mutation, bounded outputs.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from conductor.pipeline import (  # noqa: E402
    SCHEMA,
    STALE_AFTER_DAYS,
    _classify_freshness,
    pipeline_status,
)


class TestFreshnessClassifier:
    def test_recent_timestamp_is_ready(self):
        assert _classify_freshness(datetime.now(timezone.utc).isoformat()) == "READY"

    def test_old_timestamp_is_stale(self):
        old = (datetime.now(timezone.utc) - timedelta(days=STALE_AFTER_DAYS + 5)).isoformat()
        assert _classify_freshness(old) == "STALE"

    def test_missing_or_garbage_is_unknown(self):
        assert _classify_freshness(None) == "UNKNOWN"
        assert _classify_freshness("not-a-date") == "UNKNOWN"

    def test_future_clock_skew_refuses_to_classify(self):
        future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        assert _classify_freshness(future) == "UNKNOWN"


class TestPipelineStatusProjection:
    def test_schema_and_top_level_sections(self):
        out = pipeline_status(REPO_ROOT)
        assert out["schema"] == SCHEMA
        assert out["read_only"] is True
        for section in ("routing", "ingestion", "verification"):
            assert section in out

    def test_registry_counts_match_registry_file(self):
        data = json.loads((REPO_ROOT / "skills-registry.json").read_text(encoding="utf-8"))
        reg = pipeline_status(REPO_ROOT)["routing"]["registry"]
        assert reg["total"] == len(data["skills"])
        assert reg["canonical"] + reg["deprecated"] + reg["alias"] + reg["other"] == reg["total"]
        expected = {}
        for entry in data["skills"]:
            status = entry.get("status") if isinstance(entry, dict) else None
            expected[status] = expected.get(status, 0) + 1
        for status in ("canonical", "deprecated", "alias"):
            assert reg[status] == expected.get(status, 0)

    def test_routing_state_rule_is_self_consistent(self):
        routing = pipeline_status(REPO_ROOT)["routing"]
        assert routing["state"] in ("READY", "DEGRADED", "UNKNOWN")
        assert routing["classification_rule"]
        if (routing["registry"] and routing["router_importable"]
                and routing["skill_cards_importable"]):
            assert routing["state"] == "READY"

    def test_sample_query_is_bounded_and_loads_no_bodies(self):
        out = pipeline_status(REPO_ROOT, query="fix error")
        assert out["routing"]["sample_query"] == "fix error"
        assert out["routing"]["sample_cards"] is not None
        assert len(out["routing"]["sample_cards"]) >= 1  # known-routing query
        assert len(out["routing"]["sample_cards"]) <= 3
        assert out["routing"]["full_skill_bodies_loaded"] == 0
        assert out["routing"]["sample_decision"] in (
            "AUTO_LOAD_CANDIDATE", "SUGGEST_ONLY", "NO_AUTO_SELECT")

    def test_ingestion_evidence_sources_are_labeled(self):
        ing = pipeline_status(REPO_ROOT)["ingestion"]
        assert ing["state"] in ("READY", "STALE", "UNKNOWN")
        assert ing["last_source_ingest"]["evidence"].startswith("git log")
        assert "mtime" in ing["last_raw_addition"]["evidence"]
        assert ing["source_notes"] >= 0
        assert ing["raw_files"] >= 0
        assert ing["stale_after_days"] == STALE_AFTER_DAYS

    def test_drift_unknown_without_explicit_flag(self):
        drift = pipeline_status(REPO_ROOT)["verification"]["surfaces_drift"]
        assert drift["state"] == "UNKNOWN"
        assert "not_checked" in drift["reason"]

    def test_projection_does_not_mutate_registry(self):
        reg = REPO_ROOT / "skills-registry.json"
        before = reg.stat().st_mtime_ns
        pipeline_status(REPO_ROOT, query="fix error")
        assert reg.stat().st_mtime_ns == before

    def test_empty_repo_degrades_to_unknown_not_crash(self, tmp_path):
        out = pipeline_status(tmp_path)
        assert out["schema"] == SCHEMA
        assert out["routing"]["state"] == "UNKNOWN"
        assert out["routing"]["registry"] is None
        assert out["ingestion"]["state"] == "UNKNOWN"


class TestPipelineCli:
    def test_cli_emits_valid_json(self):
        proc = subprocess.run(
            [sys.executable, "-m", "conductor", "pipeline", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=120)
        assert proc.returncode == 0, proc.stderr
        assert json.loads(proc.stdout)["schema"] == SCHEMA

    def test_cli_query_flag_routes_bounded_sample(self):
        proc = subprocess.run(
            [sys.executable, "-m", "conductor", "pipeline",
             "--query", "fix error", "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=120)
        assert proc.returncode == 0, proc.stderr
        routing = json.loads(proc.stdout)["routing"]
        assert routing["sample_cards"] is not None
        assert len(routing["sample_cards"]) >= 1
        assert len(routing["sample_cards"]) <= 3


class TestReviewRepairs:
    """Negative fixtures for the independent-review findings on PR #79."""

    def _write_registry(self, tmp_path, payload, raw=None):
        target = tmp_path / "skills-registry.json"
        target.write_text(raw if raw is not None else json.dumps(payload),
                          encoding="utf-8")

    def test_registry_list_root_is_unknown(self, tmp_path):
        self._write_registry(tmp_path, [])
        assert pipeline_status(tmp_path)["routing"]["state"] == "UNKNOWN"

    def test_registry_null_root_is_unknown(self, tmp_path):
        self._write_registry(tmp_path, None, raw="null")
        assert pipeline_status(tmp_path)["routing"]["state"] == "UNKNOWN"

    def test_registry_scalar_skills_is_unknown(self, tmp_path):
        self._write_registry(tmp_path, {"skills": 1})
        assert pipeline_status(tmp_path)["routing"]["state"] == "UNKNOWN"

    def test_registry_string_skills_never_counts_characters(self, tmp_path):
        self._write_registry(tmp_path, {"skills": "abc"})
        out = pipeline_status(tmp_path)["routing"]
        assert out["registry"] is None
        assert out["state"] == "UNKNOWN"

    def test_registry_unhashable_status_counts_other_without_crash(self, tmp_path):
        self._write_registry(
            tmp_path, {"skills": [{"name": "x", "status": ["canonical"]}]})
        reg = pipeline_status(tmp_path)["routing"]["registry"]
        assert reg is not None
        assert reg["other"] == 1 and reg["total"] == 1

    def test_registry_non_dict_entry_counts_other(self, tmp_path):
        self._write_registry(tmp_path, {"skills": ["junk"]})
        reg = pipeline_status(tmp_path)["routing"]["registry"]
        assert reg["other"] == 1 and reg["total"] == 1

    def test_naive_timestamps_are_unknown_not_crash(self):
        assert _classify_freshness("2026-11-01T00:00:00") == "UNKNOWN"
        assert _classify_freshness("2026-11-01") == "UNKNOWN"

    def test_raw_traversal_bounded_and_marks_truncation(self, tmp_path):
        from conductor.pipeline import _raw_tree_evidence
        raw = tmp_path / "raw"
        raw.mkdir()
        for i in range(8):
            (raw / ("f%d.md" % i)).write_text("x", encoding="utf-8")
        count, ts, truncated = _raw_tree_evidence(raw, bound=5)
        assert truncated is True
        assert count <= 5
        assert ts is not None  # sampled from the visited prefix only

    def test_raw_directory_heavy_tree_is_bounded(self, tmp_path):
        from conductor.pipeline import _raw_tree_evidence
        raw = tmp_path / "raw"
        raw.mkdir()
        for i in range(20):
            (raw / ("d%02d" % i)).mkdir()
        (raw / "only.md").write_text("x", encoding="utf-8")
        count, ts, truncated = _raw_tree_evidence(raw, bound=5)
        assert truncated is True  # bound applies to visited entries, not files
        assert count <= 1

    def test_raw_small_tree_not_truncated(self, tmp_path):
        from conductor.pipeline import _raw_tree_evidence
        raw = tmp_path / "raw"
        raw.mkdir()
        (raw / "a.md").write_text("x", encoding="utf-8")
        count, ts, truncated = _raw_tree_evidence(raw, bound=100)
        assert truncated is False and count == 1 and ts is not None

    def test_pipeline_reports_raw_truncation_flag(self, tmp_path):
        raw = tmp_path / "raw"
        raw.mkdir()
        for i in range(3):
            (raw / ("f%d.md" % i)).write_text("x", encoding="utf-8")
        ing = pipeline_status(tmp_path)["ingestion"]
        assert ing["raw_truncated"] is False
        assert ing["raw_files"] == 3

    def test_classify_drift_exit_code_honesty(self):
        from conductor.pipeline import _classify_drift
        assert _classify_drift(0, "anything")[0] == "CLEAN"
        state, reason = _classify_drift(1, "generated/kilo differs")
        assert state == "DRIFT_OR_VALIDATION"
        assert "generated/kilo differs" in reason
        state, reason = _classify_drift(2, "Traceback: dependency missing")
        assert state == "UNKNOWN" and "dependency missing" in reason
        assert _classify_drift(3, "")[0] == "UNKNOWN"

    def test_raw_enumeration_itself_is_bounded(self, tmp_path, monkeypatch):
        """OS-level enumeration must be bounded, not just the consumer loop.

        Regression for the re-review finding: pathlib rglob materializes
        whole directories via list(scandir), so a directory-heavy tree
        enumerated 1000 entries under bound=5. The scandir-based walk must
        pull at most bound+1 entries from the filesystem in total.
        """
        import os as _os
        import conductor.pipeline as pl

        raw = tmp_path / "raw"
        raw.mkdir()
        for i in range(1000):
            (raw / ("d%03d" % i)).mkdir()

        pulled = {"total": 0}
        real_scandir = _os.scandir

        def counting_scandir(path):
            it = real_scandir(path)
            pulled["total"] += 0  # count pulled entries at iteration time
            return _CountingDirIterator(it, pulled)

        class _CountingDirIterator:
            def __init__(self, inner, counter):
                self._inner = inner
                self._counter = counter

            def __iter__(self):
                return self

            def __next__(self):
                item = next(self._inner)
                self._counter["total"] += 1
                return item

            def __enter__(self):
                self._inner.__enter__()
                return self

            def __exit__(self, *exc):
                return self._inner.__exit__(*exc)

        monkeypatch.setattr(pl.os, "scandir", counting_scandir)
        count, ts, truncated = pl._raw_tree_evidence(raw, bound=5)
        assert truncated is True
        assert count == 0 and ts is None
        assert pulled["total"] <= 6, "enumeration leaked: %d entries pulled" % pulled["total"]
