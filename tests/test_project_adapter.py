"""Phase 4 — A-Wiki Project Adapter tests (attach / status / validate).

Iron Law #1: failing tests written FIRST.

Pins the thin, portable adapter contract (kernel §control-plane-vs-project):
  - .awiki/{project.yaml, context.md, state/} minimal structure
  - attach: idempotent, non-destructive, marker-merge for existing AGENTS.md
  - status: read-only, deterministic, --json
  - validate: JSON Schema + semantic (no absolute/private paths, no secrets,
    referenced local files must exist), fail closed
All fixtures are temp repos — no real project is ever touched.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "project"))

import validate as pv  # noqa: E402 -- module under test

ATTACH = REPO_ROOT / "scripts" / "project" / "attach.py"
STATUS = REPO_ROOT / "scripts" / "project" / "status.py"
VALIDATE_CLI = REPO_ROOT / "scripts" / "project" / "validate.py"

AGENTS_MARKER = "awiki-project-adapter"


def _run(script: Path, *args, cwd: Path):
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def _valid_project_yaml(**overrides) -> str:
    data = {
        "schema": "awiki-project/v1",
        "id": "fixture-app",
        "repository": {"url": "https://github.com/example/fixture-app"},
        "domains": ["web-development"],
        "skills": {"auto": ["a-router"]},
        "integrations": {"allowed": ["gitnexus"]},
        "memory": {"scopes": {"global": True, "project": True, "session": True, "private": False}},
        "privacy": {"project_private": True},
        "code_context": {
            "enabled": False,
            "preferred": [],
            "cache_policy": "local-regenerable",
            "global_memory_promotion": False,
        },
        "resources": [],
    }
    data.update(overrides)
    return yaml.safe_dump(data, sort_keys=False)


def _adapter_dir(tmp_path: Path) -> Path:
    d = tmp_path / "fixture-app"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# schema (awiki-project/v1)
# ---------------------------------------------------------------------------
def test_project_schema_exists_and_valid_instance_passes():
    import jsonschema

    schema = json.loads(
        (REPO_ROOT / "schemas" / "awiki-project" / "v1.schema.json").read_text(encoding="utf-8"))
    instance = yaml.safe_load(_valid_project_yaml())
    jsonschema.Draft202012Validator(schema).validate(instance)


def test_project_schema_rejects_unknown_field():
    import jsonschema

    schema = json.loads(
        (REPO_ROOT / "schemas" / "awiki-project" / "v1.schema.json").read_text(encoding="utf-8"))
    instance = yaml.safe_load(_valid_project_yaml())
    instance["quota_state"] = "runtime telemetry must not live here"
    with pytest.raises(Exception):
        jsonschema.Draft202012Validator(schema).validate(instance)


def test_project_schema_rejects_missing_id():
    import jsonschema

    schema = json.loads(
        (REPO_ROOT / "schemas" / "awiki-project" / "v1.schema.json").read_text(encoding="utf-8"))
    instance = yaml.safe_load(_valid_project_yaml())
    del instance["id"]
    with pytest.raises(Exception):
        jsonschema.Draft202012Validator(schema).validate(instance)


# ---------------------------------------------------------------------------
# validate — deterministic/offline, fail closed
# ---------------------------------------------------------------------------
def _write_adapter(project: Path, yaml_text: str, context: str = "# context\n"):
    aw = project / ".awiki"
    aw.mkdir(parents=True, exist_ok=True)
    (aw / "project.yaml").write_text(yaml_text, encoding="utf-8")
    (aw / "context.md").write_text(context, encoding="utf-8")
    return aw


def test_validate_accepts_clean_adapter(tmp_path):
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    result = pv.validate(project)
    assert result.errors == [], result.errors
    assert result.exit_code() == 0


def test_validate_rejects_absolute_private_path(tmp_path):
    drive = "C" + chr(58) + chr(92) + "Users" + chr(92) + "someone" + chr(92) + "key.pem"
    text = _valid_project_yaml().replace("resources: []", f"resources: ['{drive}']")
    project = _adapter_dir(tmp_path)
    _write_adapter(project, text)
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("path" in e.lower() for e in result.errors)


def test_validate_rejects_secret_shaped_value(tmp_path):
    token = "ghp_" + "S1" + "0123456789abcdef" * 2
    text = _valid_project_yaml().replace("id: fixture-app", f"id: fixture-app\nnote: token {token}")
    project = _adapter_dir(tmp_path)
    _write_adapter(project, text)
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("secret" in e.lower() for e in result.errors)


def test_validate_rejects_dangling_resource_reference(tmp_path):
    text = _valid_project_yaml().replace("resources: []", "resources: ['docs/plan.md']")
    project = _adapter_dir(tmp_path)
    _write_adapter(project, text)  # docs/plan.md never created
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("docs/plan.md" in e for e in result.errors)


def test_validate_fails_closed_on_malformed_yaml(tmp_path):
    project = _adapter_dir(tmp_path)
    _write_adapter(project, "schema: [unclosed")
    result = pv.validate(project)
    assert result.exit_code() == 1


def test_validate_missing_context_md_fails(tmp_path):
    project = _adapter_dir(tmp_path)
    aw = project / ".awiki"
    aw.mkdir(parents=True)
    (aw / "project.yaml").write_text(_valid_project_yaml(), encoding="utf-8")
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("context.md" in e for e in result.errors)


def test_validate_cli_exit_codes(tmp_path):
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    ok = _run(VALIDATE_CLI, str(project), cwd=tmp_path)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    (project / ".awiki" / "project.yaml").write_text("schema: [unclosed", encoding="utf-8")
    bad = _run(VALIDATE_CLI, str(project), cwd=tmp_path)
    assert bad.returncode == 1


# ---------------------------------------------------------------------------
# attach — idempotent, non-destructive
# ---------------------------------------------------------------------------
def test_attach_creates_minimal_structure(tmp_path):
    project = _adapter_dir(tmp_path)
    proc = _run(ATTACH, str(project), "--id", "fixture-app", cwd=tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    aw = project / ".awiki"
    assert (aw / "project.yaml").is_file()
    assert (aw / "context.md").is_file()
    assert (aw / "state").is_dir()
    assert (project / "AGENTS.md").is_file()
    assert AGENTS_MARKER in (project / "AGENTS.md").read_text(encoding="utf-8")


def test_attach_is_idempotent(tmp_path):
    project = _adapter_dir(tmp_path)
    _run(ATTACH, str(project), "--id", "fixture-app", cwd=tmp_path)
    first = {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}
    proc = _run(ATTACH, str(project), "--id", "fixture-app", cwd=tmp_path)
    assert proc.returncode == 0
    second = {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}
    assert first == second, "second attach must not change any file"


def test_attach_preserves_existing_agents_md_content(tmp_path):
    project = _adapter_dir(tmp_path)
    original = "# Project Rules\n\nNever deploy on Friday.\n"
    (project / "AGENTS.md").write_text(original, encoding="utf-8")
    _run(ATTACH, str(project), "--id", "fixture-app", cwd=tmp_path)
    merged = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert merged.startswith(original), "project-owned instructions must be preserved verbatim"
    assert AGENTS_MARKER in merged
    # and a third run adds nothing new
    _run(ATTACH, str(project), "--id", "fixture-app", cwd=tmp_path)
    assert (project / "AGENTS.md").read_text(encoding="utf-8") == merged


def test_attach_never_overwrites_existing_project_yaml(tmp_path):
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    before = (project / ".awiki" / "project.yaml").read_text(encoding="utf-8")
    _run(ATTACH, str(project), "--id", "different-id", cwd=tmp_path)
    assert (project / ".awiki" / "project.yaml").read_text(encoding="utf-8") == before


def test_attach_creates_no_symlinks_or_submodules(tmp_path):
    project = _adapter_dir(tmp_path)
    _run(ATTACH, str(project), "--id", "fixture-app", cwd=tmp_path)
    for p in project.rglob("*"):
        assert not p.is_symlink(), f"adapter must not symlink: {p}"
    assert not (project / ".gitmodules").exists()


# ---------------------------------------------------------------------------
# status — read-only, deterministic, JSON
# ---------------------------------------------------------------------------
def test_status_json_reports_adapter_state(tmp_path):
    project = _adapter_dir(tmp_path)
    _run(ATTACH, str(project), "--id", "fixture-app", cwd=tmp_path)
    proc = _run(STATUS, "--json", str(project), cwd=tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["id"] == "fixture-app"
    assert data["adapter_valid"] is True
    for key in ("domains", "memory", "integrations", "privacy", "state_dir_available"):
        assert key in data


def test_status_is_read_only(tmp_path):
    project = _adapter_dir(tmp_path)
    _run(ATTACH, str(project), "--id", "fixture-app", cwd=tmp_path)
    before = {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}
    _run(STATUS, "--json", str(project), cwd=tmp_path)
    after = {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}
    assert before == after


def test_status_fails_deterministically_without_adapter(tmp_path):
    project = _adapter_dir(tmp_path)
    proc = _run(STATUS, "--json", str(project), cwd=tmp_path)
    assert proc.returncode == 1
    data = json.loads(proc.stdout)
    assert data["adapter_valid"] is False
