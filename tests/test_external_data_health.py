from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
HEALTH_PATH = REPO_ROOT / "scripts" / "health_external_data.py"

spec = importlib.util.spec_from_file_location("health_external_data", HEALTH_PATH)
health_external_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(health_external_data)


def test_status_line_never_prints_secret_values():
    assert health_external_data.status_line(True, ".secrets", "present; values not printed") == (
        "[OK] .secrets - present; values not printed"
    )


def test_count_files_handles_missing_path(tmp_path):
    missing = tmp_path / "missing"
    assert health_external_data.count_files(missing) is None
