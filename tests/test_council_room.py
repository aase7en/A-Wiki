"""
test_council_room.py — tests for scripts/lib/council_room.py

Brainstorm Council: the primary agent (in-session, top-tier model) is the
MODERATOR. This module only does the cheap part — fan one question out to K
free/cheap models in parallel via the EXISTING scripts/swarm/delegate.sh,
collect their answers into a transcript JSON, and emit dashboard events. It
never calls a paid model for synthesis; synthesis text is written back by
the moderator via add_synthesis()/`council.py synthesize`.

All tests here are offline: a fake runner/emitter is injected everywhere —
no real delegate.sh, no network, nothing written outside tmp_path.

Iron Law #1: these tests are written before scripts/lib/council_room.py
exists / before its logic is correct.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "swarm"))

import council_room as cr  # noqa: E402
import council as council_cli  # noqa: E402


def _noop_emit(event_type, **fields):
    pass


# ── plan_participants ───────────────────────────────────────────────────

class TestPlanParticipants:
    def _all_keys_env(self) -> dict:
        return {v: "x" for v in cr.ENGINE_KEY_ENV.values()}

    def test_free_first_order_respected(self):
        result = cr.plan_participants(6, self._all_keys_env())
        assert result == list(cr.FREE_FIRST_ORDER)

    def test_skips_missing_api_key(self):
        env = {"GEMINI_API_KEY": "g", "GROQ_API_KEY": "q"}
        result = cr.plan_participants(6, env)
        assert result == ["GEMINI", "GROQ"]

    def test_skips_disabled_engine(self):
        env = {
            "GEMINI_API_KEY": "g",
            "OPENROUTER_API_KEY": "o",
            "AWIKI_DISABLE_GEMINI": "1",
        }
        result = cr.plan_participants(6, env)
        assert result == ["OPENROUTER"]

    def test_truncates_to_n(self):
        result = cr.plan_participants(2, self._all_keys_env())
        assert result == ["GEMINI", "OPENROUTER"]

    def test_empty_when_none_available(self):
        assert cr.plan_participants(3, {}) == []

    # ── drive/.secrets visibility (Fix 3) ───────────────────────────────

    def test_engine_available_via_drive_secret_name_only(self):
        result = cr.plan_participants(6, {}, list_secret_names=lambda: ["GEMINI_API_KEY"])
        assert result == ["GEMINI"]

    def test_engine_absent_from_both_env_and_drive_is_excluded(self):
        result = cr.plan_participants(6, {}, list_secret_names=lambda: ["ANTHROPIC_API_KEY"])
        assert "GEMINI" not in result
        assert result == ["ANTHROPIC"]

    def test_key_in_both_env_and_drive_not_double_counted(self):
        env = {"GEMINI_API_KEY": "g"}
        result = cr.plan_participants(6, env, list_secret_names=lambda: ["GEMINI_API_KEY"])
        assert result.count("GEMINI") == 1

    def test_drive_disabled_engine_still_excluded(self):
        env = {"AWIKI_DISABLE_GEMINI": "1"}
        result = cr.plan_participants(6, env, list_secret_names=lambda: ["GEMINI_API_KEY"])
        assert "GEMINI" not in result

    def test_default_list_secret_names_performs_no_io(self):
        # No list_secret_names passed at all — must never touch the real
        # drive/.secrets file. Regression guard for a machine-dependence bug
        # found during planning: this repo's own dev machine has real drive
        # secrets configured, which would otherwise leak into this result
        # if the pure module defaulted to the real drive_secrets function.
        assert cr.plan_participants(3, {}) == []

    def test_raising_list_secret_names_degrades_to_empty(self):
        def boom():
            raise RuntimeError("drive unreachable")

        result = cr.plan_participants(6, {"GEMINI_API_KEY": "g"}, list_secret_names=boom)
        assert result == ["GEMINI"]  # env-only result, no crash


# ── plan_participants task_type tier filtering (Fix 4) ──────────────────

class TestPlanParticipantsTaskTypeTierFiltering:
    def _all_keys_env(self) -> dict:
        return {v: "x" for v in cr.ENGINE_KEY_ENV.values()}

    def test_no_task_type_applies_no_filtering(self):
        assert cr.plan_participants(6, self._all_keys_env()) == list(cr.FREE_FIRST_ORDER)

    def test_groq_excluded_for_reason_task_type(self):
        result = cr.plan_participants(6, self._all_keys_env(), task_type="reason")
        assert "GROQ" not in result
        assert {"GEMINI", "OPENROUTER"} <= set(result)

    def test_groq_excluded_for_scan_task_type(self):
        result = cr.plan_participants(6, self._all_keys_env(), task_type="scan")
        assert "GROQ" not in result

    def test_groq_included_for_summarize_search_lookup(self):
        for tt in ("summarize", "search", "lookup"):
            result = cr.plan_participants(6, self._all_keys_env(), task_type=tt)
            assert "GROQ" in result, tt

    def test_anthropic_only_for_scan(self):
        assert "ANTHROPIC" in cr.plan_participants(6, self._all_keys_env(), task_type="scan")
        assert "ANTHROPIC" not in cr.plan_participants(6, self._all_keys_env(), task_type="reason")

    def test_race_task_type_only_gemini_and_openrouter(self):
        result = cr.plan_participants(6, self._all_keys_env(), task_type="race")
        assert set(result) == {"GEMINI", "OPENROUTER"}

    def test_unknown_task_type_applies_no_filtering(self):
        result = cr.plan_participants(6, self._all_keys_env(), task_type="bogus")
        assert result == list(cr.FREE_FIRST_ORDER)

    def test_tier_filtering_combines_with_key_availability(self):
        env = {"GEMINI_API_KEY": "g", "GROQ_API_KEY": "q"}
        result = cr.plan_participants(6, env, task_type="reason")
        assert result == ["GEMINI"]


# ── force_engine_env ────────────────────────────────────────────────────

class TestForceEngineEnv:
    def test_disables_exactly_five_others(self):
        result = cr.force_engine_env("GROQ", {})
        disabled = {k for k, v in result.items() if k.startswith("AWIKI_DISABLE_") and v == "1"}
        expected = {f"AWIKI_DISABLE_{e}" for e in cr.FREE_FIRST_ORDER if e != "GROQ"}
        assert disabled == expected

    def test_removes_chosen_engine_disable_var(self):
        base = {"AWIKI_DISABLE_GROQ": "1"}
        result = cr.force_engine_env("GROQ", base)
        assert "AWIKI_DISABLE_GROQ" not in result

    def test_dashboard_autostart_var_passthrough_untouched(self):
        base = {"AWIKI_DISABLE_DASHBOARD_AUTOSTART": "1"}
        result = cr.force_engine_env("GEMINI", base)
        assert result["AWIKI_DISABLE_DASHBOARD_AUTOSTART"] == "1"

    def test_does_not_mutate_base_env(self):
        base = {"FOO": "bar"}
        cr.force_engine_env("GEMINI", base)
        assert base == {"FOO": "bar"}


# ── convene ──────────────────────────────────────────────────────────────

class TestConvene:
    def test_parallel_results_recorded_for_all_engines(self, tmp_path):
        env = {"GEMINI_API_KEY": "g", "OPENROUTER_API_KEY": "o", "GROQ_API_KEY": "q"}

        def runner(engine, question, task_type, timeout, env_):
            return True, f"answer-from-{engine}"

        # task_type="summarize" (tier 1) — was previously omitted (implicit
        # default "reason", tier 2), which relied on GROQ being selected for
        # a task type it can never actually succeed at per delegate.sh's
        # run_tier() (GROQ only appears in the tier-1 branch). Fixed by
        # plan_participants()'s tier-aware filtering (Fix 4) — this test now
        # asks for a tier GROQ genuinely supports, preserving its "3 engines
        # run in parallel" intent without the stale assumption.
        transcript = cr.convene(
            "what is 2+2", n=3, task_type="summarize", runner=runner, emit=_noop_emit,
            env=env, council_dir=tmp_path,
        )
        engines = {p["engine"] for p in transcript["participants"]}
        assert engines == {"GEMINI", "OPENROUTER", "GROQ"}
        for p in transcript["participants"]:
            assert p["status"] == "ok"
            assert p["answer"] == f"answer-from-{p['engine']}"
            assert "latency_s" in p

    def test_race_task_type_narrows_participants(self, tmp_path):
        env = {v: "x" for v in cr.ENGINE_KEY_ENV.values()}
        transcript = cr.convene(
            "q", n=6, task_type="race",
            runner=lambda *a, **k: (True, "x"), emit=_noop_emit,
            env=env, council_dir=tmp_path,
        )
        engines = {p["engine"] for p in transcript["participants"]}
        assert engines == {"GEMINI", "OPENROUTER"}

    def test_one_fail_others_ok(self, tmp_path):
        env = {"GEMINI_API_KEY": "g", "OPENROUTER_API_KEY": "o"}

        def runner(engine, question, task_type, timeout, env_):
            if engine == "OPENROUTER":
                return False, "boom"
            return True, "ok-answer"

        transcript = cr.convene(
            "q", n=2, runner=runner, emit=_noop_emit, env=env, council_dir=tmp_path,
        )
        statuses = {p["engine"]: p["status"] for p in transcript["participants"]}
        assert statuses == {"GEMINI": "ok", "OPENROUTER": "fail"}
        assert transcript["status"] == "ok"

    def test_all_fail_transcript_still_written(self, tmp_path):
        env = {"GEMINI_API_KEY": "g"}

        def runner(engine, question, task_type, timeout, env_):
            return False, "boom"

        transcript = cr.convene(
            "q", n=1, runner=runner, emit=_noop_emit, env=env, council_dir=tmp_path,
        )
        assert transcript["status"] == "all-failed"
        path = tmp_path / f"{transcript['id']}.json"
        assert path.is_file()

    def test_no_participants_status(self, tmp_path):
        transcript = cr.convene(
            "q", n=3, runner=lambda *a, **k: (True, "x"), emit=_noop_emit,
            env={}, council_dir=tmp_path,
        )
        assert transcript["status"] == "no-participants"
        assert transcript["participants"] == []
        path = tmp_path / f"{transcript['id']}.json"
        assert path.is_file()

    def test_transcript_schema_id_and_file_written(self, tmp_path):
        env = {"GEMINI_API_KEY": "g"}
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        transcript = cr.convene(
            "some question", n=1, task_type="reason",
            runner=lambda *a, **k: (True, "answer"), emit=_noop_emit,
            env=env, now=now, council_dir=tmp_path,
        )
        for key in ("id", "question", "task_type", "created_at", "participants", "synthesis"):
            assert key in transcript
        assert transcript["synthesis"] is None
        assert transcript["question"] == "some question"
        assert transcript["task_type"] == "reason"
        assert cr.COUNCIL_ID_RE.match(transcript["id"])
        on_disk = json.loads((tmp_path / f"{transcript['id']}.json").read_text(encoding="utf-8"))
        assert on_disk == transcript

    def test_emit_called_with_council_start_and_per_participant_answer(self, tmp_path):
        env = {"GEMINI_API_KEY": "g", "OPENROUTER_API_KEY": "o"}
        calls = []

        def emit(event_type, **fields):
            calls.append((event_type, fields))

        cr.convene(
            "q", n=2, runner=lambda *a, **k: (True, "x"), emit=emit,
            env=env, council_dir=tmp_path,
        )
        event_types = [c[0] for c in calls]
        assert event_types.count("council_start") == 1
        assert event_types.count("council_answer") == 2
        start_fields = next(f for t, f in calls if t == "council_start")
        assert start_fields.get("n") in (2, "2")

    def test_council_start_question_truncated_to_120_chars(self, tmp_path):
        long_q = "x" * 200
        env = {"GEMINI_API_KEY": "g"}
        calls = []

        def emit(event_type, **fields):
            calls.append((event_type, fields))

        cr.convene(long_q, n=1, runner=lambda *a, **k: (True, "x"), emit=emit, env=env, council_dir=tmp_path)
        start_fields = next(f for t, f in calls if t == "council_start")
        assert len(str(start_fields["question"])) <= 120


# ── add_synthesis ────────────────────────────────────────────────────────

class TestAddSynthesis:
    def _seed_transcript(self, tmp_path, council_id="council-20260101-120000-abcd"):
        transcript = {
            "id": council_id,
            "question": "q",
            "task_type": "reason",
            "created_at": "2026-01-01T12:00:00+00:00",
            "participants": [{"engine": "GEMINI", "status": "ok", "answer": "42", "latency_s": 0.1}],
            "synthesis": None,
            "status": "ok",
        }
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / f"{council_id}.json").write_text(json.dumps(transcript), encoding="utf-8")
        return council_id

    def test_roundtrip(self, tmp_path):
        council_id = self._seed_transcript(tmp_path)
        calls = []

        def emit(event_type, **fields):
            calls.append((event_type, fields))

        now = datetime(2026, 1, 1, 13, 0, 0, tzinfo=timezone.utc)
        result = cr.add_synthesis(
            council_id, "the synthesis text", council_dir=tmp_path, emit=emit, now=now,
        )
        assert result["synthesis"]["text"] == "the synthesis text"
        assert result["synthesis"]["author"] == "primary-agent"
        assert result["synthesis"]["added_at"] == now.isoformat()
        on_disk = json.loads((tmp_path / f"{council_id}.json").read_text(encoding="utf-8"))
        assert on_disk["synthesis"]["text"] == "the synthesis text"
        assert len(calls) == 1
        assert calls[0][0] == "council_synthesis"

    def test_rejects_path_traversal_id(self, tmp_path):
        with pytest.raises(ValueError):
            cr.add_synthesis("../evil", "text", council_dir=tmp_path, emit=_noop_emit)

    def test_rejects_unknown_id(self, tmp_path):
        with pytest.raises(ValueError):
            cr.add_synthesis(
                "council-20260101-120000-dead", "text", council_dir=tmp_path, emit=_noop_emit,
            )


# ── load_council / list_councils ────────────────────────────────────────

class TestLoadListCouncils:
    def _write(self, tmp_path, council_id, created_at, participants, synthesis=None):
        data = {
            "id": council_id,
            "question": f"question for {council_id}",
            "task_type": "reason",
            "created_at": created_at,
            "participants": participants,
            "synthesis": synthesis,
            "status": "ok",
        }
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / f"{council_id}.json").write_text(json.dumps(data), encoding="utf-8")
        return data

    def test_load_council_roundtrip(self, tmp_path):
        data = self._write(tmp_path, "council-20260101-120000-aaaa", "2026-01-01T12:00:00+00:00", [])
        loaded = cr.load_council("council-20260101-120000-aaaa", council_dir=tmp_path)
        assert loaded == data

    def test_load_council_rejects_bad_id(self, tmp_path):
        with pytest.raises(ValueError):
            cr.load_council("../evil", council_dir=tmp_path)

    def test_list_councils_ordering_and_summary_fields(self, tmp_path):
        self._write(
            tmp_path, "council-20260101-090000-aaaa", "2026-01-01T09:00:00+00:00",
            [{"engine": "GEMINI", "status": "ok"}, {"engine": "GROQ", "status": "fail"}],
        )
        self._write(
            tmp_path, "council-20260101-100000-bbbb", "2026-01-01T10:00:00+00:00",
            [{"engine": "GEMINI", "status": "ok"}],
            synthesis={"text": "s", "author": "a", "added_at": "x"},
        )
        result = cr.list_councils(council_dir=tmp_path)
        assert [c["id"] for c in result] == [
            "council-20260101-100000-bbbb",
            "council-20260101-090000-aaaa",
        ]
        newest, oldest = result
        assert newest["participants_ok"] == 1
        assert newest["participants_total"] == 1
        assert newest["has_synthesis"] is True
        assert oldest["participants_ok"] == 1
        assert oldest["participants_total"] == 2
        assert oldest["has_synthesis"] is False

    def test_list_councils_empty_dir_returns_empty_list(self, tmp_path):
        assert cr.list_councils(council_dir=tmp_path / "does-not-exist") == []


# ── default_runner ───────────────────────────────────────────────────────

class TestDefaultRunner:
    def test_timeout_returns_false_reason(self, monkeypatch):
        real_run = subprocess.run

        def fake_run(cmd, **kwargs):
            # Ignore the (bash, delegate.sh, ...) command and instead run a
            # real short-lived sleeping subprocess, so subprocess.run's own
            # timeout enforcement is exercised end-to-end without touching
            # bash or delegate.sh. Kept well under 3s via a tiny timeout.
            return real_run([sys.executable, "-c", "import time; time.sleep(5)"], **kwargs)

        monkeypatch.setattr(cr.subprocess, "run", fake_run)
        ok, reason = cr.default_runner("GEMINI", "question", "reason", 0.3, {})
        assert ok is False
        assert isinstance(reason, str) and reason

    def test_invokes_delegate_sh_with_utf8_encoding(self, monkeypatch):
        captured = {}

        class FakeResult:
            returncode = 0
            stdout = "the answer"
            stderr = ""

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["kwargs"] = kwargs
            return FakeResult()

        monkeypatch.setattr(cr.subprocess, "run", fake_run)
        ok, out = cr.default_runner("GROQ", "the question", "scan", 42, {"FOO": "bar"})
        assert ok is True
        assert out == "the answer"
        assert captured["cmd"][0] == "bash"
        assert captured["cmd"][1].endswith("delegate.sh")
        assert captured["cmd"][2] == "scan"
        assert captured["cmd"][3] == "the question"
        assert captured["kwargs"]["timeout"] == 42
        assert captured["kwargs"]["text"] is True
        assert captured["kwargs"]["encoding"] == "utf-8"
        assert captured["kwargs"]["errors"] == "replace"
        assert captured["kwargs"]["env"] == {"FOO": "bar"}


# ── CLI ──────────────────────────────────────────────────────────────────

class TestCLI:
    def _transcript(self, statuses: list[str]) -> dict:
        return {
            "id": "council-20260101-000000-abcd",
            "question": "q",
            "task_type": "reason",
            "created_at": "2026-01-01T00:00:00+00:00",
            "participants": [
                {"engine": f"ENGINE{i}", "status": s, "answer": f"a{i}", "latency_s": 0.1}
                for i, s in enumerate(statuses)
            ],
            "synthesis": None,
            "status": "ok" if "ok" in statuses else "all-failed",
        }

    def test_ask_happy_path_exit_zero(self, monkeypatch, capsys):
        monkeypatch.setattr(council_cli.cr, "convene", lambda *a, **k: self._transcript(["ok"]))
        rc = council_cli.main(["ask", "what is the answer"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "ENGINE0" in out
        assert "moderator" in out

    def test_ask_all_fail_exit_one(self, monkeypatch, capsys):
        monkeypatch.setattr(council_cli.cr, "convene", lambda *a, **k: self._transcript(["fail"]))
        rc = council_cli.main(["ask", "what is the answer"])
        assert rc == 1

    def test_synthesize_bad_id_exit_one(self, capsys):
        rc = council_cli.main(["synthesize", "../evil", "--text", "hello"])
        err = capsys.readouterr().err
        assert rc == 1
        assert err.strip() != ""


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
