from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify-next-machine.py"
spec = importlib.util.spec_from_file_location("verify_next_machine", SCRIPT)
assert spec and spec.loader
verify_next_machine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = verify_next_machine
spec.loader.exec_module(verify_next_machine)


def test_exit_code_fails_only_on_fail():
    steps = [
        verify_next_machine.Step("OK", "a", "ok"),
        verify_next_machine.Step("WARN", "b", "warn"),
    ]
    assert verify_next_machine.exit_code(steps) == 0

    steps.append(verify_next_machine.Step("FAIL", "c", "fail"))
    assert verify_next_machine.exit_code(steps) == 1


def test_checks_include_work_pc_relevant_steps(monkeypatch):
    names: list[str] = []

    def fake_command_step(name, args, timeout=180):
        names.append(name)
        return verify_next_machine.Step("OK", name, "ok")

    monkeypatch.setattr(verify_next_machine, "command_step", fake_command_step)
    monkeypatch.setattr(verify_next_machine, "docker_step", lambda: verify_next_machine.Step("WARN", "docker", "missing"))

    steps = verify_next_machine.checks(build_vec=True)

    assert [step.name for step in steps] == [
        "cloud link",
        "drive secrets",
        "import keys",
        "kilo config",
        "readiness",
        "cross-platform",
        "sync smoke",
        "docker",
    ]
    assert "cross-platform" in names

