from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "import-keys.py"

spec = importlib.util.spec_from_file_location("import_keys", SCRIPT)
assert spec and spec.loader
import_keys = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = import_keys
spec.loader.exec_module(import_keys)


def test_check_does_not_print_secret_values(tmp_path, monkeypatch, capsys):
    secrets = tmp_path / ".secrets"
    secrets.write_text("OPENROUTER_API_KEY=sk-or-v1-secret-value\n", encoding="utf-8")

    monkeypatch.setattr(import_keys, "find_secrets_file", lambda: secrets)
    monkeypatch.setattr(sys, "argv", ["import-keys.py", "--check"])

    assert import_keys.main() == 0
    out = capsys.readouterr().out
    assert "OPENROUTER_API_KEY" not in out
    assert "sk-or-v1" not in out
    assert "cacheable key name" in out


def test_list_prints_names_only(tmp_path, monkeypatch, capsys):
    secrets = tmp_path / ".secrets"
    secrets.write_text("OPENROUTER_API_KEY=sk-or-v1-secret-value\n", encoding="utf-8")

    monkeypatch.setattr(import_keys, "find_secrets_file", lambda: secrets)
    monkeypatch.setattr(sys, "argv", ["import-keys.py", "--list"])

    assert import_keys.main() == 0
    out = capsys.readouterr().out
    assert "OPENROUTER_API_KEY" in out
    assert "sk-or-v1-secret-value" not in out

