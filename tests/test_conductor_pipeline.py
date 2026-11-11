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
        assert len(routing["sample_cards"]) <= 3
