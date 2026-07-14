"""tests/test_pid_check.py — regression guard for scripts/lib/pid_check.py.

Iron Law #1: written before pid_check.py exists / before its logic is
correct. The single most important case is
test_probe_never_kills_the_process_it_checks — see pid_check.py's docstring
for the concrete Windows os.kill(pid, 0) landmine this guards against
(reproduced empirically on this machine 2026-07-14: calling
os.kill(real_pid, 0) from native Windows Python terminated the process
instead of merely probing it).
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "scripts" / "lib" / "pid_check.py"

spec = importlib.util.spec_from_file_location("pid_check", MODULE_PATH)
assert spec and spec.loader
pid_check = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pid_check
spec.loader.exec_module(pid_check)


@pytest.fixture
def sleeper():
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        yield proc
    finally:
        if proc.poll() is None:
            proc.terminate()
        proc.wait(timeout=5)


def test_is_pid_alive_true_for_running_process(sleeper):
    assert pid_check.is_pid_alive(sleeper.pid) is True


def test_is_pid_alive_false_after_process_exits(sleeper):
    sleeper.terminate()
    sleeper.wait(timeout=5)
    assert pid_check.is_pid_alive(sleeper.pid) is False


def test_is_pid_alive_false_for_huge_nonexistent_pid():
    assert pid_check.is_pid_alive(2**31 - 1) is False


def test_is_pid_alive_never_raises_for_well_typed_nonexistent_pid():
    try:
        result = pid_check.is_pid_alive(999999999)
    except Exception as exc:  # pragma: no cover - failure path documented
        pytest.fail(f"is_pid_alive raised for a nonexistent PID: {exc!r}")
    assert result is False


def test_probe_never_kills_the_process_it_checks(sleeper):
    """The regression this module exists to prevent."""
    assert pid_check.is_pid_alive(sleeper.pid) is True
    assert pid_check.is_pid_alive(sleeper.pid) is True  # probed twice
    assert sleeper.poll() is None, "process exited after being probed — probe killed it"


def test_rejects_non_positive_pid():
    with pytest.raises(ValueError):
        pid_check.is_pid_alive(0)
    with pytest.raises(ValueError):
        pid_check.is_pid_alive(-123)


def test_rejects_non_int_pid():
    with pytest.raises(TypeError):
        pid_check.is_pid_alive("123")
    with pytest.raises(TypeError):
        pid_check.is_pid_alive(True)  # bool is a subclass of int — reject explicitly


# ── CLI ──────────────────────────────────────────────────────────────────

def test_cli_exit_0_for_alive_pid(sleeper):
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), str(sleeper.pid)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert result.returncode == 0


def test_cli_exit_1_for_dead_pid():
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), "999999999"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert result.returncode == 1


def test_cli_exit_2_for_bad_arg():
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), "not-a-pid"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert result.returncode == 2


def test_cli_exit_2_for_missing_arg():
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    assert result.returncode == 2


# ── server.py integration — the actual landmine site ────────────────────

class TestServerIsAlreadyRunningIntegration:
    SERVER = REPO_ROOT / "scripts" / "live-dashboard" / "server.py"

    def _load_server(self):
        spec = importlib.util.spec_from_file_location("ld_server_pidcheck", self.SERVER)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_is_already_running_true_and_never_kills(self, tmp_path, sleeper):
        mod = self._load_server()
        mod.PID_FILE = tmp_path / "live-dashboard.pid"
        mod.PID_FILE.write_text(str(sleeper.pid))
        assert mod.is_already_running() is True
        assert sleeper.poll() is None, "is_already_running() killed the process it checked"

    def test_is_already_running_false_cleans_up_pidfile(self, tmp_path):
        mod = self._load_server()
        mod.PID_FILE = tmp_path / "live-dashboard.pid"
        mod.PID_FILE.write_text("999999999")
        assert mod.is_already_running() is False
        assert not mod.PID_FILE.exists()
