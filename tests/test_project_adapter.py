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
        "integrations": {"allowed": []},
        "memory": {"scopes": {"global": True, "project": True, "session": True, "private": False}},
        "privacy": {"project_private": True},
        "trust": {"deep_enrichment": "project-policy", "private_context": False},
        "code_context": {
            "enabled": False,
            "preferred": [],
            "cache_policy": "local-regenerable",
            "global_memory_promotion": False,
        },
        "resources": [],
    }
    data.update(overrides)
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=True).strip()


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
    """Create the FULL canonical surface so 'valid' fixtures really are valid."""
    aw = project / ".awiki"
    aw.mkdir(parents=True, exist_ok=True)
    (aw / "project.yaml").write_text(yaml_text, encoding="utf-8")
    (aw / "context.md").write_text(context, encoding="utf-8")
    (aw / "state").mkdir(exist_ok=True)
    agents = project / "AGENTS.md"
    if not agents.exists():
        agents.write_text(f"hdr\n<!-- {AGENTS_MARKER} v1 -->\n", encoding="utf-8")
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
    # inject into an existing string value (flow-style yaml: no raw newlines)
    text = _valid_project_yaml().replace(
        "domains: [web-development]", f"domains: ['web-development {token}']")
    assert token in text, "injection must land"
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


# ---------------------------------------------------------------------------
# R-P4-001 — containment-safe resource + cross-platform path detection
# ---------------------------------------------------------------------------
def test_validate_rejects_nested_traversal_resource(tmp_path):
    secret_outside = tmp_path / "outside.txt"
    secret_outside.write_text("outside", encoding="utf-8")
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    (project / "docs").mkdir()
    (project / "docs" / "real.md").write_text("x", encoding="utf-8")
    text = _valid_project_yaml().replace(
        "resources: []", "resources: ['docs/real.md', 'docs/../../outside.txt']")
    (project / ".awiki" / "project.yaml").write_text(text, encoding="utf-8")
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("outside.txt" in e or "escape" in e.lower() for e in result.errors)


def test_validate_rejects_symlink_escape_resource(tmp_path):
    if not hasattr(__import__("os"), "symlink"):
        pytest.skip("symlinks unavailable on this platform")
    import os
    outside = tmp_path / "outside-doc.md"
    outside.write_text("outside", encoding="utf-8")
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    (project / "docs").mkdir()
    os.symlink(outside, project / "docs" / "linked.md")
    text = _valid_project_yaml().replace("resources: []", "resources: ['docs/linked.md']")
    (project / ".awiki" / "project.yaml").write_text(text, encoding="utf-8")
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("escape" in e.lower() or "symlink" in e.lower() for e in result.errors)


@pytest.mark.parametrize("bad_path", [
    "/etc/passwd", "/tmp/x", "~" + chr(47) + "secrets",       # unix absolute/private + tilde
    chr(92) * 2 + "server" + chr(92) + "share" + chr(92) + "f",  # UNC
    chr(92) * 2 + "?" + chr(92) + "C:" + chr(92) + "x",          # Windows extended/device
])
def test_validate_rejects_cross_platform_path_strings(tmp_path, bad_path):
    # quoted injection: flow-style yaml keeps any path shape parseable
    text = _valid_project_yaml().replace("domains: [web-development]",
                                         "domains: ['" + bad_path + "']")
    assert "web-development" not in text, "injection must land"
    project = _adapter_dir(tmp_path)
    _write_adapter(project, text)
    result = pv.validate(project)
    assert result.exit_code() == 1, f"must reject path string: {bad_path}"
    assert any("machine path" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# R-P4-002 — attach must not follow unsafe pre-existing symlinks
# ---------------------------------------------------------------------------
def test_attach_refuses_agents_md_symlink_and_leaves_target_untouched(tmp_path):
    if not hasattr(__import__("os"), "symlink"):
        pytest.skip("symlinks unavailable on this platform")
    import os
    external = tmp_path / "external-agents.md"
    external.write_text("PRECIOUS EXTERNAL CONTENT\n", encoding="utf-8")
    project = _adapter_dir(tmp_path)
    os.symlink(external, project / "AGENTS.md")
    proc = _run(ATTACH, str(project), "--id", "fixture-app", cwd=tmp_path)
    assert proc.returncode != 0, "attach must refuse a symlinked AGENTS.md"
    assert external.read_text(encoding="utf-8") == "PRECIOUS EXTERNAL CONTENT\n"
    assert not (project / ".awiki" / "project.yaml").exists(), "no partial attach after refusal"


def test_attach_refuses_awiki_dir_symlink(tmp_path):
    if not hasattr(__import__("os"), "symlink"):
        pytest.skip("symlinks unavailable on this platform")
    import os
    outside_dir = tmp_path / "outside-aw"
    outside_dir.mkdir()
    project = _adapter_dir(tmp_path)
    os.symlink(outside_dir, project / ".awiki")
    proc = _run(ATTACH, str(project), "--id", "fixture-app", cwd=tmp_path)
    assert proc.returncode != 0
    assert list(outside_dir.iterdir()) == [], "external dir must remain untouched"


# ---------------------------------------------------------------------------
# R-P4-003 — privacy/trust/memory policy structurally required
# ---------------------------------------------------------------------------
def test_adapter_without_trust_is_invalid(tmp_path):
    data = yaml.safe_load(_valid_project_yaml())
    del data["trust"]
    project = _adapter_dir(tmp_path)
    _write_adapter(project, yaml.safe_dump(data, sort_keys=False))
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("trust" in e.lower() for e in result.errors)


def test_adapter_without_privacy_is_invalid(tmp_path):
    data = yaml.safe_load(_valid_project_yaml())
    del data["privacy"]
    project = _adapter_dir(tmp_path)
    _write_adapter(project, yaml.safe_dump(data, sort_keys=False))
    result = pv.validate(project)
    assert result.exit_code() == 1


def test_adapter_without_memory_is_invalid(tmp_path):
    data = yaml.safe_load(_valid_project_yaml())
    del data["memory"]
    project = _adapter_dir(tmp_path)
    _write_adapter(project, yaml.safe_dump(data, sort_keys=False))
    result = pv.validate(project)
    assert result.exit_code() == 1


def test_trust_without_private_context_is_invalid(tmp_path):
    data = yaml.safe_load(_valid_project_yaml())
    data["trust"] = {"deep_enrichment": "project-policy"}
    project = _adapter_dir(tmp_path)
    _write_adapter(project, yaml.safe_dump(data, sort_keys=False))
    result = pv.validate(project)
    assert result.exit_code() == 1


def test_fresh_attach_generates_trust_policy(tmp_path):
    project = _adapter_dir(tmp_path)
    _run(ATTACH, str(project), "--id", "fixture-app", cwd=tmp_path)
    data = yaml.safe_load((project / ".awiki" / "project.yaml").read_text(encoding="utf-8"))
    assert isinstance(data.get("trust"), dict)
    assert "private_context" in data["trust"]


# ---------------------------------------------------------------------------
# R-P4-004 — safe YAML generation + id reconciliation + self-validation
# ---------------------------------------------------------------------------
def test_attach_survives_punctuated_and_unicode_domains(tmp_path):
    project = tmp_path / "p"
    project.mkdir()
    weird = "web, dev: #1 [x] — ไทย/中文"
    proc = _run(ATTACH, str(project), "--id", "weird-app",
                "--domain", weird, cwd=tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = yaml.safe_load((project / ".awiki" / "project.yaml").read_text(encoding="utf-8"))
    assert weird in data["domains"], "domain must round-trip verbatim"
    assert pv.validate(project).exit_code() == 0


def test_attach_single_char_id_round_trips(tmp_path):
    project = tmp_path / "x"
    project.mkdir()
    proc = _run(ATTACH, str(project), cwd=tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = yaml.safe_load((project / ".awiki" / "project.yaml").read_text(encoding="utf-8"))
    assert data["id"]
    assert pv.validate(project).exit_code() == 0


def test_attach_reports_failure_if_generated_adapter_invalid(tmp_path):
    # Subprocess sabotage via a REAL pre-existing invalid project.yaml:
    # attach must preserve it (non-destructive) and then FAIL self-validation.
    project = _adapter_dir(tmp_path)
    aw = project / ".awiki"
    aw.mkdir()
    (aw / "project.yaml").write_text(
        "schema: awiki-project/v1\nid: incomplete\n", encoding="utf-8")  # missing required policy
    proc = _run(ATTACH, str(project), "--id", "fixture-app", cwd=tmp_path)
    assert proc.returncode != 0, "attach must not report success on an invalid resulting adapter"
    # the invalid pre-existing policy must still be byte-preserved
    assert (aw / "project.yaml").read_text(encoding="utf-8") == \
        "schema: awiki-project/v1\nid: incomplete\n"


# ---------------------------------------------------------------------------
#


# ---------------------------------------------------------------------------
# R-P4-005 — integration allowlist cross-checked against canonical registry
# ---------------------------------------------------------------------------
def test_validate_rejects_unknown_integration_id(tmp_path):
    text = _valid_project_yaml().replace(
        "allowed: []", "allowed: [not-a-real-integration]")
    project = _adapter_dir(tmp_path)
    _write_adapter(project, text)
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("not-a-real-integration" in e for e in result.errors)


def test_validate_accepts_known_integration_id(tmp_path):
    text = _valid_project_yaml().replace("allowed: []", "allowed: [gitnexus]")
    project = _adapter_dir(tmp_path)
    _write_adapter(project, text)
    result = pv.validate(project)
    assert result.exit_code() == 0, result.errors


# ---------------------------------------------------------------------------
# R-P4-006 — canonical attachment surface enforced
# ---------------------------------------------------------------------------
def test_adapter_without_agents_md_is_invalid(tmp_path):
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    (project / "AGENTS.md").unlink()  # remove the discovery surface explicitly
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("AGENTS.md" in e for e in result.errors)


def test_adapter_with_markerless_agents_md_is_invalid(tmp_path):
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    (project / "AGENTS.md").write_text("# plain instructions\n", encoding="utf-8")
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("marker" in e.lower() for e in result.errors)


def test_adapter_without_state_dir_is_invalid(tmp_path):
    import shutil
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    shutil.rmtree(project / ".awiki" / "state")  # remove state/ explicitly
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("state" in e.lower() for e in result.errors)


def test_full_canonical_surface_is_valid(tmp_path):
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())  # already creates the full surface
    result = pv.validate(project)
    assert result.exit_code() == 0, result.errors


# ---------------------------------------------------------------------------
# R-P4-007 — read path must reject symlinked canonical adapter surfaces
# ---------------------------------------------------------------------------
def _can_symlink():
    return hasattr(__import__("os"), "symlink")


def test_validate_rejects_symlinked_awiki_dir(tmp_path):
    if not _can_symlink():
        pytest.skip("symlinks unavailable")
    import os
    project = _adapter_dir(tmp_path)
    real = tmp_path / "real-aw"
    _write_adapter(project, _valid_project_yaml())
    real_aw = project / ".awiki"
    real_aw.rename(real)
    os.symlink(real, real_aw)  # canonical .awiki now a symlink (even in-tree)
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("symlink" in e.lower() for e in result.errors)


def test_validate_rejects_symlinked_agents_md(tmp_path):
    if not _can_symlink():
        pytest.skip("symlinks unavailable")
    import os
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    external = tmp_path / "external-agents.md"
    external.write_text(f"<!-- {AGENTS_MARKER} v1 -->\n", encoding="utf-8")
    (project / "AGENTS.md").unlink()
    os.symlink(external, project / "AGENTS.md")
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("symlink" in e.lower() for e in result.errors)


def test_validate_rejects_symlinked_project_yaml(tmp_path):
    if not _can_symlink():
        pytest.skip("symlinks unavailable")
    import os
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    external = tmp_path / "external-project.yaml"
    external.write_text(_valid_project_yaml(), encoding="utf-8")
    (project / ".awiki" / "project.yaml").unlink()
    os.symlink(external, project / ".awiki" / "project.yaml")
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("symlink" in e.lower() for e in result.errors)


def test_status_reports_invalid_for_symlinked_surface(tmp_path):
    if not _can_symlink():
        pytest.skip("symlinks unavailable")
    import os
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    external = tmp_path / "ext-agents.md"
    external.write_text(f"<!-- {AGENTS_MARKER} v1 -->\n", encoding="utf-8")
    (project / "AGENTS.md").unlink()
    os.symlink(external, project / "AGENTS.md")
    proc = _run(STATUS, "--json", str(project), cwd=tmp_path)
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["adapter_valid"] is False


# ---------------------------------------------------------------------------
# R-P4-008 — allowlist eligibility by registry semantics, not id existence
# ---------------------------------------------------------------------------
def test_validate_rejects_rejected_integration(tmp_path):
    text = _valid_project_yaml().replace("allowed: []", "allowed: [deer-flow]")
    project = _adapter_dir(tmp_path)
    _write_adapter(project, text)
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("deer-flow" in e for e in result.errors)


def test_validate_rejects_pattern_only_integration(tmp_path):
    text = _valid_project_yaml().replace("allowed: []", "allowed: [autoresearch]")
    project = _adapter_dir(tmp_path)
    _write_adapter(project, text)
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("autoresearch" in e for e in result.errors)


# ---------------------------------------------------------------------------
# R-P4-009 — malformed encoding must fail closed, never traceback
# ---------------------------------------------------------------------------
def test_validate_fails_closed_on_invalid_utf8_project_yaml(tmp_path):
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    (project / ".awiki" / "project.yaml").write_bytes(
        b"\xff\xfe not-utf8 \x80\x81")
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("decode" in e.lower() or "utf-8" in e.lower() or "malformed" in e.lower()
               for e in result.errors)


def test_status_reports_invalid_on_invalid_utf8(tmp_path):
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    (project / ".awiki" / "project.yaml").write_bytes(b"\xff\xfe\x80")
    proc = _run(STATUS, "--json", str(project), cwd=tmp_path)
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["adapter_valid"] is False


# ---------------------------------------------------------------------------
# R-P4-007 (re-review) — unsafe symlink targets must NEVER be read
# ---------------------------------------------------------------------------
_TOKEN = "ghp_" + "T9" + "0123456789abcdef" * 2  # secret-shaped canary


def _can_symlink():
    return hasattr(__import__("os"), "symlink")


def test_validate_does_not_read_symlinked_project_yaml_target(tmp_path):
    if not _can_symlink():
        pytest.skip("symlinks unavailable")
    import os
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    external = tmp_path / "external-project.yaml"
    external.write_text(_valid_project_yaml().replace(
        "domains: [web-development]", f"domains: [canary-{_TOKEN}]"),
        encoding="utf-8")  # secret-shaped canary inside the external target
    (project / ".awiki" / "project.yaml").unlink()
    os.symlink(external, project / ".awiki" / "project.yaml")
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("symlink" in e.lower() for e in result.errors)
    assert not any("secret" in e.lower() for e in result.errors),         "external target content was read (secret canary leaked into validation)"


def test_validate_does_not_read_symlinked_awiki_target(tmp_path):
    if not _can_symlink():
        pytest.skip("symlinks unavailable")
    import os
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    real = tmp_path / "real-aw"
    (project / ".awiki").rename(real)
    (real / "project.yaml").write_text(
        _valid_project_yaml().replace(
            "domains: [web-development]", f"domains: [canary-{_TOKEN}]"),
        encoding="utf-8")
    os.symlink(real, project / ".awiki")
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("symlink" in e.lower() for e in result.errors)
    assert not any("secret" in e.lower() for e in result.errors),         "external .awiki target content was read"


def test_validate_does_not_read_symlinked_agents_md_target(tmp_path):
    if not _can_symlink():
        pytest.skip("symlinks unavailable")
    import os
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    external = tmp_path / "external-agents.md"
    external.write_text(f"canary {_TOKEN}\n", encoding="utf-8")
    (project / "AGENTS.md").unlink()
    os.symlink(external, project / "AGENTS.md")
    result = pv.validate(project)
    assert result.exit_code() == 1
    assert any("symlink" in e.lower() for e in result.errors)
    assert not any("secret" in e.lower() for e in result.errors)


def test_status_does_not_report_from_symlinked_surface(tmp_path):
    if not _can_symlink():
        pytest.skip("symlinks unavailable")
    import os
    project = _adapter_dir(tmp_path)
    _write_adapter(project, _valid_project_yaml())
    external = tmp_path / "ext-project.yaml"
    external.write_text(_valid_project_yaml().replace(
        "id: fixture-app", "id: attacker-controlled-id"), encoding="utf-8")
    (project / ".awiki" / "project.yaml").unlink()
    os.symlink(external, project / ".awiki" / "project.yaml")
    proc = _run(STATUS, "--json", str(project), cwd=tmp_path)
    assert proc.returncode == 1
    data = json.loads(proc.stdout)
    assert data["adapter_valid"] is False
    assert data.get("id") != "attacker-controlled-id", \
        "status must not parse/report fields from an unsafe surface"


# ---------------------------------------------------------------------------
# R-P4-008 (re-review) — MODULE+PATTERN eligible; pattern-only/reject not
# ---------------------------------------------------------------------------
def test_graft_module_pattern_is_eligible(tmp_path):
    text = _valid_project_yaml().replace("allowed: []", "allowed: [graft]")
    project = _adapter_dir(tmp_path)
    _write_adapter(project, text)
    result = pv.validate(project)
    assert result.exit_code() == 0, result.errors


def test_gitnexus_pure_module_remains_eligible(tmp_path):
    text = _valid_project_yaml().replace("allowed: []", "allowed: [gitnexus]")
    project = _adapter_dir(tmp_path)
    _write_adapter(project, text)
    result = pv.validate(project)
    assert result.exit_code() == 0, result.errors
