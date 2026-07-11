"""Tests for scripts/new-skill.py — skill scaffold+register (Iron Law #1: failing first).

Covers:
  - kebab-case name validation
  - domain/lifecycle_phase validation against the canonical skills_registry sets
  - dry-run touches nothing (no fs/subprocess side effects)
  - registry entry shape matches a sibling registry entry's key set
  - registry-write-before-skill-write ordering (hook #15 depends on this)
  - regen-skill-surfaces.py invoked with PYTHONIOENCODING=utf-8
  - runtime guards (duplicate name, existing SKILL.md)
  - CLI arg parsing / config building

Everything runs against injectable fakes (FakeFS / FakeRunner) — no real
filesystem writes and no real subprocesses, per the task's "no real
subprocess" constraint. The one exception is the E2E sanity check, which is
a separate manual step (not part of this test module).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

SCRIPT = REPO_ROOT / "scripts" / "new-skill.py"
spec = importlib.util.spec_from_file_location("new_skill", SCRIPT)
assert spec and spec.loader
new_skill = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = new_skill
spec.loader.exec_module(new_skill)

from skills_registry import VALID_DOMAINS, VALID_LIFECYCLE_PHASES  # noqa: E402


# ---------------------------------------------------------------------------
# Fakes — injectable fs/runner so scaffold logic is testable without real I/O
# ---------------------------------------------------------------------------

class FakeFS:
    """In-memory filesystem double. Keys are str(path)."""

    def __init__(self, initial: dict[str, str] | None = None) -> None:
        self.files: dict[str, str] = dict(initial or {})

    def read_text(self, path) -> str:
        return self.files[str(path)]

    def write_text(self, path, content: str) -> None:
        self.files[str(path)] = content

    def exists(self, path) -> bool:
        return str(path) in self.files


class FakeRunner:
    """Records subprocess-shaped calls without spawning anything real."""

    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode
        self.calls: list[dict] = []

    def run(self, cmd, env, cwd):
        self.calls.append({"cmd": list(cmd), "env": dict(env), "cwd": cwd})
        return SimpleNamespace(returncode=self.returncode, stdout="ok", stderr="")


EMPTY_REGISTRY = {
    "schema_version": 1,
    "generated_at": "2026-07-01T00:00:00Z",
    "skills": [],
}


def make_cfg(**overrides):
    defaults = dict(
        name="demo-skill",
        domain=("code",),
        phase="build",
        category="uncategorized",
        description="Demo skill for tests.",
        path_root="skills/awiki",
        apply=False,
    )
    defaults.update(overrides)
    return new_skill.ScaffoldConfig(**defaults)


# ---------------------------------------------------------------------------
# Name validation
# ---------------------------------------------------------------------------

class TestNameValidation:
    @pytest.mark.parametrize("name", ["demo-skill", "a", "a1-b2", "wiki-search-local"])
    def test_valid_kebab_case_accepted(self, name):
        new_skill.validate_kebab_case(name)  # must not raise

    @pytest.mark.parametrize(
        "name",
        ["Demo-Skill", "demo_skill", "demo skill", "-demo", "demo-", "demo--skill", "", "démo"],
    )
    def test_invalid_names_rejected(self, name):
        with pytest.raises(new_skill.ScaffoldError):
            new_skill.validate_kebab_case(name)


# ---------------------------------------------------------------------------
# Domain / phase validation against canonical VALID_* sets
# ---------------------------------------------------------------------------

class TestDomainPhaseValidation:
    def test_valid_domain_accepted(self):
        new_skill.validate_domains(["code", "debug"])  # must not raise

    def test_invalid_domain_rejected(self):
        with pytest.raises(new_skill.ScaffoldError) as exc:
            new_skill.validate_domains(["not-a-real-domain"])
        assert "not-a-real-domain" in str(exc.value)

    def test_empty_domain_list_rejected(self):
        with pytest.raises(new_skill.ScaffoldError):
            new_skill.validate_domains([])

    def test_valid_phase_accepted(self):
        new_skill.validate_phase("build")  # must not raise

    def test_invalid_phase_rejected(self):
        with pytest.raises(new_skill.ScaffoldError):
            new_skill.validate_phase("not-a-real-phase")

    def test_module_uses_canonical_domain_set(self):
        # Must be the SAME set object/values as skills_registry, not a stale copy.
        assert new_skill.VALID_DOMAINS == VALID_DOMAINS

    def test_module_uses_canonical_phase_set(self):
        assert new_skill.VALID_LIFECYCLE_PHASES == VALID_LIFECYCLE_PHASES


# ---------------------------------------------------------------------------
# Dry-run touches nothing
# ---------------------------------------------------------------------------

class TestDryRun:
    def test_dry_run_makes_no_fs_or_runner_calls(self, tmp_path):
        cfg = make_cfg(apply=False)
        fs = FakeFS()  # deliberately empty — a real read would KeyError
        runner = FakeRunner()
        recorder = new_skill.StepRecorder()

        result = new_skill.run_scaffold(
            cfg, fs=fs, runner=runner, recorder=recorder, repo_root=tmp_path
        )

        assert fs.files == {}, "dry-run must not write or read any files"
        assert runner.calls == [], "dry-run must not invoke regen"
        assert recorder.steps == [], "dry-run must not record any apply steps"
        assert result.applied is False

    def test_dry_run_still_builds_the_plan(self, tmp_path):
        cfg = make_cfg(apply=False)
        result = new_skill.run_scaffold(
            cfg, fs=FakeFS(), runner=FakeRunner(), recorder=new_skill.StepRecorder(), repo_root=tmp_path
        )
        assert result.entry["name"] == "demo-skill"
        assert result.skill_md_path == tmp_path / "skills" / "awiki" / "demo-skill" / "SKILL.md"

    def test_dry_run_rejects_invalid_config_without_touching_anything(self, tmp_path):
        cfg = make_cfg(apply=False, name="Not_Kebab")
        fs = FakeFS()
        with pytest.raises(new_skill.ScaffoldError):
            new_skill.run_scaffold(
                cfg, fs=fs, runner=FakeRunner(), recorder=new_skill.StepRecorder(), repo_root=tmp_path
            )
        assert fs.files == {}


# ---------------------------------------------------------------------------
# Registry entry shape
# ---------------------------------------------------------------------------

class TestEntryShape:
    def test_entry_key_set_matches_sibling_entry(self, tmp_path):
        with open(REPO_ROOT / "skills-registry.json", encoding="utf-8") as f:
            real_registry = json.load(f)
        sibling = next(s for s in real_registry["skills"] if s["name"] == "wiki")

        cfg = make_cfg(apply=False)
        result = new_skill.run_scaffold(
            cfg, fs=FakeFS(), runner=FakeRunner(), recorder=new_skill.StepRecorder(), repo_root=tmp_path
        )

        assert set(result.entry.keys()) == set(sibling.keys())

    def test_entry_fields_mirror_schema_defaults(self, tmp_path):
        cfg = make_cfg(apply=False)
        result = new_skill.run_scaffold(
            cfg, fs=FakeFS(), runner=FakeRunner(), recorder=new_skill.StepRecorder(), repo_root=tmp_path
        )
        entry = result.entry
        assert entry["status"] == "canonical"
        assert entry["agents"] == ["all"]
        assert entry["version"] == "1.0.0"
        assert entry["source"] == "repo"
        assert entry["domain"] == ["code"]
        assert entry["lifecycle_phase"] == "build"
        assert entry["path"] == "skills/awiki/demo-skill/SKILL.md"

    def test_entry_validates_clean_against_the_real_schema(self, tmp_path):
        from skills_registry import validate_registry

        cfg = make_cfg(apply=False)
        result = new_skill.run_scaffold(
            cfg, fs=FakeFS(), runner=FakeRunner(), recorder=new_skill.StepRecorder(), repo_root=tmp_path
        )
        candidate = dict(EMPTY_REGISTRY)
        candidate["skills"] = [result.entry]
        p = tmp_path / "candidate-registry.json"
        p.write_text(json.dumps(candidate), encoding="utf-8")
        assert validate_registry(p) == []


# ---------------------------------------------------------------------------
# Ordering: registry write BEFORE SKILL.md write (hook #15 depends on this)
# ---------------------------------------------------------------------------

class TestOrdering:
    def test_registry_written_before_skill_md(self, tmp_path):
        cfg = make_cfg(apply=True)
        registry_path = tmp_path / "skills-registry.json"
        fs = FakeFS({str(registry_path): json.dumps(EMPTY_REGISTRY)})
        runner = FakeRunner(returncode=0)
        recorder = new_skill.StepRecorder()

        result = new_skill.run_scaffold(
            cfg, fs=fs, runner=runner, recorder=recorder, repo_root=tmp_path
        )

        assert "write_registry" in recorder.steps
        assert "write_skill_md" in recorder.steps
        assert recorder.steps.index("write_registry") < recorder.steps.index("write_skill_md")
        assert result.applied is True

        written = json.loads(fs.files[str(registry_path)])
        assert any(s["name"] == "demo-skill" for s in written["skills"])


# ---------------------------------------------------------------------------
# regen invoked with utf-8 env
# ---------------------------------------------------------------------------

class TestRegenInvocation:
    def test_regen_called_with_pythonioencoding_utf8(self, tmp_path):
        cfg = make_cfg(apply=True)
        registry_path = tmp_path / "skills-registry.json"
        fs = FakeFS({str(registry_path): json.dumps(EMPTY_REGISTRY)})
        runner = FakeRunner(returncode=0)
        recorder = new_skill.StepRecorder()

        new_skill.run_scaffold(cfg, fs=fs, runner=runner, recorder=recorder, repo_root=tmp_path)

        assert len(runner.calls) == 2, "expects regen + regen --check"
        for call in runner.calls:
            assert call["env"].get("PYTHONIOENCODING") == "utf-8"
        assert runner.calls[1]["cmd"][-1] == "--check"
        assert "regen-skill-surfaces.py" in runner.calls[0]["cmd"][-1]

    def test_run_scaffold_reports_drift_when_check_fails(self, tmp_path):
        cfg = make_cfg(apply=True)
        registry_path = tmp_path / "skills-registry.json"
        fs = FakeFS({str(registry_path): json.dumps(EMPTY_REGISTRY)})
        runner = FakeRunner(returncode=1)
        recorder = new_skill.StepRecorder()

        result = new_skill.run_scaffold(
            cfg, fs=fs, runner=runner, recorder=recorder, repo_root=tmp_path
        )

        assert result.regen_ok is False
        assert result.regen_check_ok is False


# ---------------------------------------------------------------------------
# Runtime guards
# ---------------------------------------------------------------------------

class TestRuntimeGuards:
    def test_apply_rejects_duplicate_name(self, tmp_path):
        registry_path = tmp_path / "skills-registry.json"
        existing = {
            "schema_version": 1,
            "generated_at": "x",
            "skills": [
                {
                    "name": "demo-skill", "domain": ["code"], "lifecycle_phase": "none",
                    "category": "uncategorized", "source": "repo", "path": "p", "status": "canonical",
                }
            ],
        }
        fs = FakeFS({str(registry_path): json.dumps(existing)})
        cfg = make_cfg(apply=True)
        with pytest.raises(new_skill.ScaffoldError):
            new_skill.run_scaffold(
                cfg, fs=fs, runner=FakeRunner(), recorder=new_skill.StepRecorder(), repo_root=tmp_path
            )

    def test_apply_rejects_existing_skill_md(self, tmp_path):
        registry_path = tmp_path / "skills-registry.json"
        skill_md_path = tmp_path / "skills" / "awiki" / "demo-skill" / "SKILL.md"
        fs = FakeFS(
            {
                str(registry_path): json.dumps(EMPTY_REGISTRY),
                str(skill_md_path): "already here",
            }
        )
        cfg = make_cfg(apply=True)
        with pytest.raises(new_skill.ScaffoldError):
            new_skill.run_scaffold(
                cfg, fs=fs, runner=FakeRunner(), recorder=new_skill.StepRecorder(), repo_root=tmp_path
            )
        # Must not have clobbered the registry before raising.
        assert json.loads(fs.files[str(registry_path)]) == EMPTY_REGISTRY


# ---------------------------------------------------------------------------
# CLI parsing / build_config
# ---------------------------------------------------------------------------

class TestCLI:
    def test_parse_args_defaults(self):
        args = new_skill.parse_args(["demo-skill", "--domain", "code", "--phase", "build"])
        assert args.name == "demo-skill"
        assert args.domain == "code"
        assert args.phase == "build"
        assert args.category == "uncategorized"
        assert args.path_root == "skills/awiki"
        assert args.apply is False

    def test_build_config_splits_comma_domains(self):
        args = new_skill.parse_args(["demo-skill", "--domain", "code,debug", "--phase", "build"])
        cfg = new_skill.build_config(args)
        assert cfg.domain == ("code", "debug")

    def test_build_config_default_description_placeholder(self):
        args = new_skill.parse_args(["demo-skill", "--domain", "code", "--phase", "build"])
        cfg = new_skill.build_config(args)
        assert "demo-skill" in cfg.description

    def test_build_config_uses_explicit_description(self):
        args = new_skill.parse_args(
            ["demo-skill", "--domain", "code", "--phase", "build", "--description", "Does the thing."]
        )
        cfg = new_skill.build_config(args)
        assert cfg.description == "Does the thing."

    def test_build_config_rejects_bad_name(self):
        args = new_skill.parse_args(["Bad_Name", "--domain", "code", "--phase", "build"])
        with pytest.raises(new_skill.ScaffoldError):
            new_skill.build_config(args)

    def test_build_config_rejects_bad_domain(self):
        args = new_skill.parse_args(["demo-skill", "--domain", "nonsense", "--phase", "build"])
        with pytest.raises(new_skill.ScaffoldError):
            new_skill.build_config(args)

    def test_build_config_rejects_bad_phase(self):
        args = new_skill.parse_args(["demo-skill", "--domain", "code", "--phase", "nonsense"])
        with pytest.raises(new_skill.ScaffoldError):
            new_skill.build_config(args)

    def test_main_dry_run_returns_zero_and_touches_nothing(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(new_skill, "REPO_ROOT", tmp_path)
        rc = new_skill.main(["demo-skill", "--domain", "code", "--phase", "build"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "demo-skill" in out
        assert not (tmp_path / "skills-registry.json").exists()

    def test_main_invalid_name_returns_nonzero(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(new_skill, "REPO_ROOT", tmp_path)
        rc = new_skill.main(["Bad_Name", "--domain", "code", "--phase", "build"])
        assert rc != 0
