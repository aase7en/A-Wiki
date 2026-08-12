"""Pytest wrapper for scripts/hospital/verify_regression.py.

Runs the verifier as a subprocess and asserts exit 0. This makes the
regression HNs part of the standard `pytest tests/` run.

To add new pinned HNs: edit scripts/hospital/regression_HNs.yaml
(don't touch this file).
"""
import subprocess
import sys
from pathlib import Path

import pytest

VERIFIER = Path(__file__).resolve().parent.parent / "scripts" / "hospital" / "verify_regression.py"


def test_regression_hns_pass():
    """All HNs in regression_HNs.yaml must match expected classification.

    Exit 0 = pass. Exit 2 = regression (engine output != YAML expected).
    Exit 1 = YAML/schema problem.
    """
    proc = subprocess.run(
        [sys.executable, str(VERIFIER)],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, (
        f"verify_regression.py failed (exit {proc.returncode}):\n"
        f"{proc.stderr}\n{proc.stdout}\n"
        f"If expected classification in YAML is wrong, update it to match "
        f"actual engine behavior. If engine has regressed, FIX the engine."
    )


def test_yaml_exists_and_loadable():
    """Sanity: YAML file exists at expected path and parses."""
    import yaml
    yaml_path = Path(__file__).resolve().parent.parent / "scripts" / "hospital" / "regression_HNs.yaml"
    assert yaml_path.exists(), f"regression_HNs.yaml missing at {yaml_path}"
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert isinstance(data, list), "YAML top-level must be a list"
    assert len(data) >= 3, f"Expected ≥3 regression HNs, got {len(data)}"
    for entry in data:
        assert "hn" in entry, f"Entry missing 'hn' field: {entry}"
        assert "timeline" in entry, f"HN {entry.get('hn')} missing 'timeline'"
        assert "expected" in entry, f"HN {entry.get('hn')} missing 'expected'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
