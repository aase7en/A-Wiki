"""Workspace-vs-brain repo-root seam — Slice A (`awiki adopt`) prereq.

When the brain's hooks run FOR a foreign adopted repo, the provider
payload carries `cwd` = the workspace the agent is editing. Workspace
hooks (raw-immutable, source-provenance...) must resolve THAT root;
brain-state consumers (registry, ledger) keep using the brain root.
Without this seam every relative path resolves against the brain and
foreign repos get no protection.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS = REPO_ROOT / "scripts" / "hooks"
sys.path.insert(0, str(HOOKS))


def _run_hook(hook: str, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOKS / hook)],
        input=json.dumps(payload), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60,
        cwd=str(REPO_ROOT))


def test_helper_resolves_payload_cwd_first(tmp_path):
    from _repo_root import brain_root, resolve_repo_root
    target = tmp_path / "foreign-repo"
    target.mkdir()
    assert resolve_repo_root({"cwd": str(target)}) == str(target)
    # no cwd -> legacy behavior: the brain itself
    assert Path(resolve_repo_root({})) == Path(brain_root())


def test_brain_root_points_at_awiki():
    from _repo_root import brain_root
    assert (Path(brain_root()) / "skills-registry.json").is_file()


def test_raw_immutable_guards_foreign_repo_via_cwd(tmp_path):
    """Adopted repo with its own raw/ must be protected through cwd.

    Discriminating case: an ABSOLUTE path inside the foreign repo.
    Today the hook checks it only against the brain root -> it slips
    through (real adopt bug). With the cwd seam it must be blocked."""
    target = tmp_path / "adopted"
    (target / "raw").mkdir(parents=True)
    foreign = target / "raw" / "doc.pdf"
    foreign.write_bytes(b"%PDF-1.4")
    assert not (REPO_ROOT / "raw" / "doc.pdf").exists()
    res = _run_hook("check_raw_immutable.py", {
        "cwd": str(target),
        "tool_name": "Edit",
        "tool_input": {"file_path": str(foreign),
                        "old_string": "a", "new_string": "b"},
    })
    assert res.returncode == 2, "foreign raw/ edit must be blocked via cwd"

    # and a foreign file OUTSIDE raw/ stays allowed
    ok = target / "src" / "main.py"
    ok.parent.mkdir(exist_ok=True)
    ok.write_text("print(1)")
    res2 = _run_hook("check_raw_immutable.py", {
        "cwd": str(target),
        "tool_name": "Edit",
        "tool_input": {"file_path": str(ok),
                        "old_string": "1", "new_string": "2"},
    })
    assert res2.returncode == 0, "foreign non-raw edit must pass"


def test_raw_immutable_legacy_behavior_without_cwd():
    """No cwd field -> resolve against the brain (today's behavior)."""
    res = _run_hook("check_raw_immutable.py", {
        "tool_name": "Edit",
        "tool_input": {"file_path": "raw/legacy-guard.pdf",
                        "old_string": "a", "new_string": "b"},
    })
    assert res.returncode == 2, "brain raw/ still guarded without cwd"


def test_source_provenance_resolves_foreign_repo_via_cwd(tmp_path):
    """Iron Law #8 in an adopted repo: a wiki/sources page whose
    original_file points at the FOREIGN raw/ must pass there (and a
    dangling one must block) — resolved through payload cwd."""
    target = tmp_path / "adopted2"
    (target / "raw").mkdir(parents=True)
    (target / "raw" / "spec.md").write_text("source", encoding="utf-8")
    src_dir = target / "wiki" / "sources"
    src_dir.mkdir(parents=True)

    def _payload(original_file: str) -> dict:
        return {"cwd": str(target), "tool_name": "Write",
                "tool_input": {
                    "file_path": str(src_dir / "spec-page.md"),
                    "content": ("---\ntype: source\noriginal_file: "
                                f"{original_file}\n---\n\n# s\n")}}

    ok = _run_hook("check_source_original_file.py", _payload("raw/spec.md"))
    assert ok.returncode == 0, f"valid foreign provenance must pass: {ok.stderr[-200:]}"

    bad = _run_hook("check_source_original_file.py",
                    _payload("raw/does-not-exist.md"))
    assert bad.returncode == 2, "dangling foreign raw/ must block"


def test_hooks_runner_scopes_claims_store_to_workspace(tmp_path):
    """Adopted repos get their own claims store derived from payload cwd:
    the runner exports AWIKI_CLAIMS_STORE (unless the caller set one) so
    every claim gate in a foreign repo is isolated from the brain's."""
    import importlib.util as ilu
    spec = ilu.spec_from_file_location("hr", REPO_ROOT / "scripts" / "hooks_runner.py")
    hr = ilu.module_from_spec(spec); spec.loader.exec_module(hr)
    target = tmp_path / "adopted3"
    payload = {"cwd": str(target), "session_id": "t", "tool_name": "Edit",
               "tool_input": {"file_path": "x.py", "old_string": "a", "new_string": "b"}}
    env = {}
    hr._export_workspace_env(payload, env)
    assert env["AWIKI_CLAIMS_STORE"] == str(target / ".tmp" / "agent-claims.json")
    # explicit env wins (caller-controlled), no cwd -> nothing exported
    kept = hr._export_workspace_env({"cwd": str(target)},
                                    {"AWIKI_CLAIMS_STORE": "custom"})
    assert kept["AWIKI_CLAIMS_STORE"] == "custom"
    assert hr._export_workspace_env({}, {}) == {}
