"""
test_format_cost.py — Tests for scripts/format-cost.py

Validates:
  - proxy backend is used and labeled when tiktoken/anthropic are absent
  - CSV < Markdown < HTML ordering on --demo (format-agnostic on exact counts)
  - --json output shape
  - stdin read with --in -
  - --demo smoke test runs and exits cleanly
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "format-cost.py"


def _run(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SCRIPT)] + list(args)
    return subprocess.run(
        cmd,
        input=stdin,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


# ── smoke test ───────────────────────────────────────────────────────────

class TestDemoSmoke:

    def test_demo_exits_zero(self):
        r = _run("--demo")
        assert r.returncode == 0

    def test_demo_mentions_backend(self):
        r = _run("--demo")
        output = r.stdout.lower()
        assert "backend" in output or "proxy" in output or "tiktoken" in output

    def test_demo_mentions_html(self):
        r = _run("--demo")
        assert "html" in r.stdout.lower()

    def test_no_args_exits_zero_with_hint(self):
        r = _run()
        assert r.returncode == 0
        assert "demo" in r.stdout.lower()

    def test_demo_falls_back_to_proxy_when_anthropic_has_no_key(self, tmp_path):
        """CI regression: `anthropic` is installed (requirements.txt) but no
        ANTHROPIC_API_KEY exists → backend selection must NOT pick the API
        backend, or --demo crashes before printing anything."""
        import os

        # Fake SDK that mimics the real one: constructs fine without a key,
        # raises only when the API is actually called.
        (tmp_path / "anthropic.py").write_text(
            "class _Raiser:\n"
            "    def __getattr__(self, name):\n"
            "        raise RuntimeError('no api key — API call attempted')\n"
            "class Anthropic:\n"
            "    def __init__(self, *a, **k):\n"
            "        pass\n"
            "    @property\n"
            "    def beta(self):\n"
            "        return _Raiser()\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env.pop("ANTHROPIC_API_KEY", None)
        env["PYTHONPATH"] = str(tmp_path)
        env["PYTHONIOENCODING"] = "utf-8"

        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--demo"],
            capture_output=True, cwd=str(REPO_ROOT), env=env,
            # child prints UTF-8 (PYTHONIOENCODING) — decode the same way,
            # not with the parent's locale codec (cp874 on Thai Windows)
            encoding="utf-8", errors="replace",
        )

        assert r.returncode == 0, r.stderr
        assert "proxy" in r.stdout.lower()


# ── format ordering ──────────────────────────────────────────────────────

class TestFormatOrdering:
    """CSV must be cheaper than Markdown, which must be cheaper than HTML."""

    def _parse_demo_json(self) -> list[dict]:
        r = _run("--demo", "--json")
        assert r.returncode == 0
        data = json.loads(r.stdout)
        return data["formats"]

    def test_csv_cheaper_than_markdown(self):
        formats = self._parse_demo_json()
        by_name = {f["name"]: f for f in formats}
        assert by_name["CSV"]["tokens"] < by_name["Markdown table"]["tokens"]

    def test_markdown_cheaper_than_html(self):
        formats = self._parse_demo_json()
        by_name = {f["name"]: f for f in formats}
        assert by_name["Markdown table"]["tokens"] < by_name["HTML table"]["tokens"]

    def test_html_more_expensive_than_markdown(self):
        """HTML must cost more tokens than Markdown — that's the key protocol finding.
        (JSON indent=2 may exceed HTML in some cases — that's fine; protocol still holds.)"""
        formats = self._parse_demo_json()
        by_name = {f["name"]: f for f in formats}
        assert by_name["HTML table"]["tokens"] > by_name["Markdown table"]["tokens"], \
            "HTML table must cost more tokens than Markdown table"

    def test_markdown_ratio_is_one(self):
        formats = self._parse_demo_json()
        by_name = {f["name"]: f for f in formats}
        assert by_name["Markdown table"]["ratio"] == 1.0


# ── --json output shape ──────────────────────────────────────────────────

class TestJsonShape:

    def test_json_output_has_required_keys(self):
        r = _run("--demo", "--json")
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert "backend" in data
        assert "n_records" in data
        assert "formats" in data
        assert isinstance(data["formats"], list)

    def test_json_formats_have_required_fields(self):
        r = _run("--demo", "--json")
        data = json.loads(r.stdout)
        for f in data["formats"]:
            assert "name" in f
            assert "chars" in f
            assert "tokens" in f
            assert "ratio" in f

    def test_json_format_names_include_all_five(self):
        r = _run("--demo", "--json")
        data = json.loads(r.stdout)
        names = {f["name"] for f in data["formats"]}
        assert "CSV" in names
        assert "Markdown table" in names
        assert "JSONL" in names
        assert "JSON" in names
        assert "HTML table" in names

    def test_json_backend_labeled(self):
        r = _run("--demo", "--json", "--tokenizer", "proxy")
        data = json.loads(r.stdout)
        assert "proxy" in data["backend"].lower() or "char" in data["backend"].lower()


# ── stdin read ───────────────────────────────────────────────────────────

class TestStdinRead:

    def test_reads_json_array_from_stdin(self):
        records = [
            {"name": "Alice", "score": 95},
            {"name": "Bob",   "score": 82},
        ]
        r = _run("--in", "-", stdin=json.dumps(records))
        assert r.returncode == 0

    def test_stdin_json_array_produces_output(self):
        records = [{"col": "val"} for _ in range(3)]
        r = _run("--in", "-", "--json", stdin=json.dumps(records))
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data["n_records"] == 3

    def test_stdin_single_object_wrapped(self):
        r = _run("--in", "-", stdin=json.dumps({"key": "value"}))
        assert r.returncode == 0

    def test_stdin_invalid_json_exits_nonzero(self):
        r = _run("--in", "-", stdin="not json")
        assert r.returncode != 0


# ── proxy backend ────────────────────────────────────────────────────────

class TestProxyBackend:

    def test_proxy_backend_produces_positive_counts(self):
        r = _run("--demo", "--json", "--tokenizer", "proxy")
        data = json.loads(r.stdout)
        for f in data["formats"]:
            assert f["tokens"] > 0

    def test_proxy_chars_matches_expected_direction(self):
        """CSV chars should be smallest, HTML largest."""
        r = _run("--demo", "--json", "--tokenizer", "proxy")
        data = json.loads(r.stdout)
        by_name = {f["name"]: f for f in data["formats"]}
        assert by_name["CSV"]["chars"] < by_name["HTML table"]["chars"]
