"""
test_gen_index_chain.py — Coverage for the --no-chain flag (F7).

gen-index.py chains downstream scripts (raw-to-source.py, raw-to-synth.py,
build-wiki-index.py, build-wiki-graph.py, build-canvas.py, review-check.py,
build-vec-index.py) that create low-quality stubs and noise. The --no-chain
flag skips all of them so gen-index can refresh context cleanly.

Iron Law #1: these tests are written FIRST, fail before the flag exists,
and pass after the flag is implemented.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# scripts/gen-index.py (root, NOT scripts/wiki/gen-index.py) — has the chain code
_gen_index_path = REPO_ROOT / "scripts" / "gen-index.py"
_spec = importlib.util.spec_from_file_location("gen_index_root", _gen_index_path)
gen_index = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen_index)


class TestNoChainFlag:
    """F7 — --no-chain flag must exist and skip all downstream chain scripts."""

    def test_no_chain_flag_in_argparse(self):
        """The argparse setup must accept --no-chain without error."""
        # Simulate parsing --no-chain
        with mock.patch.object(sys, "argv", ["gen-index.py", "--no-chain", "--stdout"]):
            try:
                gen_index.main()
            except SystemExit as e:
                # argparse rejects unknown flags with exit code 2
                pytest.fail(f"--no-chain rejected by argparse: exit {e.code}")
            except Exception:
                # Other exceptions are OK for this test — we only care that
                # argparse did not reject the flag itself
                pass

    def test_no_chain_skips_raw_to_source(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """With --no-chain, raw-to-source.py must NOT be invoked via subprocess."""
        recorded_calls: list[list[str]] = []

        def fake_run(cmd, *args, **kwargs):
            recorded_calls.append(cmd)
            # Return a fake CompletedProcess-like object
            return mock.MagicMock(returncode=0, stdout=b"", stderr=b"")

        monkeypatch.setattr("subprocess.run", fake_run)
        # Point gen-index at a tiny wiki so collect_pages doesn't choke
        monkeypatch.setattr(gen_index, "WIKI_DIR", tmp_path / "wiki")
        monkeypatch.setattr(gen_index, "REPO_ROOT", tmp_path)
        (tmp_path / "wiki" / "entities").mkdir(parents=True, exist_ok=True)
        (tmp_path / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
        (tmp_path / "wiki" / "sources").mkdir(parents=True, exist_ok=True)
        (tmp_path / "wiki" / "synthesis").mkdir(parents=True, exist_ok=True)

        with mock.patch.object(sys, "argv", ["gen-index.py", "--no-chain", "--stdout"]):
            try:
                gen_index.main()
            except Exception:
                pass  # We only care about subprocess.run calls

        # Assert raw-to-source.py was never called
        all_cmds = [" ".join(str(c) for c in cmd) for cmd in recorded_calls]
        for forbidden in ("raw-to-source.py", "raw-to-synth.py"):
            hits = [c for c in all_cmds if forbidden in c]
            assert not hits, f"--no-chain should skip {forbidden}, but it was called: {hits}"

    def test_no_chain_skips_review_check(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """With --no-chain, review-check.py must NOT be invoked."""
        recorded_calls: list[list[str]] = []

        def fake_run(cmd, *args, **kwargs):
            recorded_calls.append(cmd)
            return mock.MagicMock(returncode=0, stdout=b"", stderr=b"")

        monkeypatch.setattr("subprocess.run", fake_run)
        monkeypatch.setattr(gen_index, "WIKI_DIR", tmp_path / "wiki")
        monkeypatch.setattr(gen_index, "REPO_ROOT", tmp_path)
        (tmp_path / "wiki" / "entities").mkdir(parents=True, exist_ok=True)
        (tmp_path / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
        (tmp_path / "wiki" / "sources").mkdir(parents=True, exist_ok=True)
        (tmp_path / "wiki" / "synthesis").mkdir(parents=True, exist_ok=True)

        with mock.patch.object(sys, "argv", ["gen-index.py", "--no-chain", "--stdout"]):
            try:
                gen_index.main()
            except Exception:
                pass

        all_cmds = [" ".join(str(c) for c in cmd) for cmd in recorded_calls]
        hits = [c for c in all_cmds if "review-check.py" in c]
        assert not hits, f"--no-chain should skip review-check.py, but it was called: {hits}"
