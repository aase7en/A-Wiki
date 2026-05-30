from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify-cross-platform.py"
spec = importlib.util.spec_from_file_location("verify_cross_platform", SCRIPT)
assert spec and spec.loader
verify_cross_platform = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = verify_cross_platform
spec.loader.exec_module(verify_cross_platform)


def test_exit_code_fails_only_on_fail():
    results = [
        verify_cross_platform.Check("OK", "a", "ok"),
        verify_cross_platform.Check("WARN", "b", "warn"),
    ]
    assert verify_cross_platform.exit_code(results) == 0

    results.append(verify_cross_platform.Check("FAIL", "c", "fail"))
    assert verify_cross_platform.exit_code(results) == 1


def test_vec_build_is_explicit_opt_in():
    result = verify_cross_platform.check_vec_build(False)

    assert result.level == "WARN"
    assert "--build-vec" in result.detail


def test_script_mentions_required_portable_checks():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "scripts/gen-index.py" in text
    assert "scripts/build-vec-index.py" in text
    assert "scripts/setup-cloud-link.sh" in text
    assert "apsw" in text
