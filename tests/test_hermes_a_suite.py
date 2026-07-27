"""Tests for Hermes (Pi5) reachability of the A-Suite skill system.

Iron Law #1: failing tests written FIRST.

Context — before this change the A-Suite was invisible to Hermes at every layer:

1. ``gen_hermes.py`` is **opt-in**: a skill reaches ``hermes.skills.json`` only
   when its ``agents`` list literally contains ``"hermes"``.  All 24 ``a-*``
   skills were ``agents: ["all"]``, which that generator deliberately EXCLUDES
   (free-tier Pi5 models have 8k-32k context; preloading everything blows it).
2. ``awiki-init-pi5.sh`` hard-coded three skill dirs — ``engineering-lifecycle``,
   ``engineering``, ``mattpocock`` — and never touched ``skills/awiki/``.
3. ``hermes.skills.json`` had **no consumer at all** (repo-wide grep: zero hits
   outside its own generator, its own test, and one comment) even though the
   file is shipped to the device.
4. ``lifecycle-config.json``'s BUILD phase named seven skills that do not exist
   anywhere in the registry, and its DEFINE phase named a deprecated alias.

Why symlinking is the fix: the Pi5 gateway uses **Skills-as-Commands** — every
directory under ``/opt/data/skills/`` is auto-exposed as ``/<dirname>`` on
Telegram (docs/architecture/hermes-cross-agent-handoff.md §"Skills-as-Commands",
chunk hermes-e).  So linking ``skills/awiki/a-debug/`` is exactly what makes
``/a-debug`` answerable from the phone.  A-Suite skills are prompt dispatchers,
not script-backed commands, so they need no ``telegram-commands.json`` entry —
the SKILL.md body IS the payload.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hermes"))

REGISTRY_PATH = REPO_ROOT / "skills-registry.json"
MANIFEST_PATH = REPO_ROOT / "scripts" / "skills_registry" / "generated" / "hermes.skills.json"
LIFECYCLE_CONFIG = REPO_ROOT / "scripts" / "hermes" / "lifecycle-config.json"
INIT_PI5 = REPO_ROOT / "scripts" / "hermes" / "awiki-init-pi5.sh"

# The A-Suite spine entry points.  Deliberately NOT the whole a-* family: the
# ten ``a-doc/types/<x>/`` subskills are reached through ``a-doc`` and must not
# each burn a slot in an 8k-context manifest.
A_SUITE_ENTRY_POINTS = (
    "a-router",
    "a-think",
    "a-plan",
    "a-debug",
    "a-doc",
    "a-council",
    "a-loop",
    "a-escalate",
    "a-claim",
)

# Skills the A-Suite chains hand off to.  A chain that lands on an untagged
# skill dead-ends on the Pi5 — the model is told to run something it cannot
# load.  ``a-debug`` alone walks debug-mantra → tdd → verify-before-done →
# scrutinize (+ post-mortem when the bug was big).
A_SUITE_CHAIN_TARGETS = (
    "debug-mantra",
    "tdd",
    "verify-before-done",
    "scrutinize",
    "post-mortem",
    "delegate-subagent",
)


def _registry() -> dict:
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


def _by_name() -> dict[str, dict]:
    return {s["name"]: s for s in _registry()["skills"]}


def _is_hermes_tagged(skill: dict) -> bool:
    return "hermes" in (skill.get("agents") or [])


# ---------------------------------------------------------------------------
# 1. Registry tagging — the opt-in gate gen_hermes.py enforces
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", A_SUITE_ENTRY_POINTS)
def test_a_suite_entry_point_tagged_for_hermes(name):
    """Each A-Suite entry point must opt into Hermes explicitly.

    ``agents: ["all"]`` is NOT enough — gen_hermes.py requires the literal
    ``"hermes"`` string, by design.
    """
    skill = _by_name().get(name)
    assert skill is not None, f"{name} missing from skills-registry.json"
    assert skill.get("status") == "canonical", (
        f"{name} is {skill.get('status')!r} — a non-canonical skill must not be "
        f"tagged for Hermes"
    )
    assert _is_hermes_tagged(skill), (
        f"{name} is not tagged for Hermes: agents={skill.get('agents')!r}. "
        f"gen_hermes.py excludes agents:['all'], so this skill never reaches the Pi5."
    )


@pytest.mark.parametrize("name", A_SUITE_CHAIN_TARGETS)
def test_a_suite_chain_target_reachable_on_hermes(name):
    """A chain must not hand off to a skill Hermes cannot load."""
    skill = _by_name().get(name)
    assert skill is not None, f"{name} missing from skills-registry.json"
    assert _is_hermes_tagged(skill), (
        f"{name} is referenced by an A-Suite chain but is not tagged for Hermes "
        f"(agents={skill.get('agents')!r}) — the chain dead-ends on the Pi5."
    )


# ---------------------------------------------------------------------------
# 2. Generated manifest — what actually ships to the device
# ---------------------------------------------------------------------------
def test_hermes_manifest_exposes_a_suite():
    """hermes.skills.json must carry every A-Suite entry point.

    Guards the regen step: tagging the registry without regenerating leaves the
    device with a manifest that disagrees with the source of truth.
    """
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    names = {s["name"] for s in manifest["skills"]}
    missing = [n for n in A_SUITE_ENTRY_POINTS if n not in names]
    assert not missing, f"A-Suite entry points absent from hermes.skills.json: {missing}"


def test_hermes_manifest_stays_within_context_budget():
    """The manifest is opt-in precisely to stay small — keep it that way.

    Free-tier Pi5 models run 8k-32k context.  The original target was ~40-50
    skills; the A-Suite spine plus its chain targets pushes that up, so the
    ceiling is raised deliberately rather than silently.  If this trips, decide
    what to DROP — do not just raise the number.
    """
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    n = len(manifest["skills"])
    assert n <= 70, (
        f"hermes.skills.json has grown to {n} skills. The Pi5 context budget is "
        f"the constraint — drop something before raising this ceiling."
    )


def test_a_doc_subskills_not_individually_tagged():
    """``a-doc/types/<x>/`` subskills reach Hermes through ``a-doc``, not directly.

    Tagging all ten would burn a fifth of the manifest on one domain.
    """
    leaked = [
        s["name"] for s in _registry()["skills"]
        if s["name"].startswith("a-doc-") and _is_hermes_tagged(s)
    ]
    assert not leaked, (
        f"a-doc subskills tagged for Hermes individually: {leaked}. "
        f"Route them through the a-doc entry point instead."
    )


# ---------------------------------------------------------------------------
# 3. lifecycle-config.json — copied to ~/.hermes/config.d/ on the device
# ---------------------------------------------------------------------------
def _config_phase_skills() -> list[tuple[str, str, str]]:
    cfg = json.loads(LIFECYCLE_CONFIG.read_text(encoding="utf-8"))
    out = []
    for phase, body in cfg["phases"].items():
        for key in ("skills", "a_wiki_skills"):
            for name in body.get(key, []):
                out.append((phase, key, name))
    return out


def test_lifecycle_config_phase_skills_exist():
    """Every skill named in a phase must exist in the registry.

    The BUILD phase used to name seven skills that were never in the registry
    (incremental-implementation, test-driven-development, doubt-driven-development,
    source-driven-development, frontend-ui-engineering, api-and-interface-design,
    context-engineering) — Hermes was handed an empty phase.
    """
    known = _by_name()
    missing = [
        f"{phase}.{key}: {name}"
        for phase, key, name in _config_phase_skills()
        if name not in known
    ]
    assert not missing, f"lifecycle-config.json names skills that do not exist: {missing}"


def test_lifecycle_config_phase_skills_are_canonical():
    """No phase may route to a deprecated skill or a bare alias."""
    known = _by_name()
    bad = [
        f"{phase}.{key}: {name} ({known[name].get('status')})"
        for phase, key, name in _config_phase_skills()
        if name in known and known[name].get("status") != "canonical"
    ]
    assert not bad, f"lifecycle-config.json routes to non-canonical skills: {bad}"


def test_lifecycle_config_phase_skills_are_hermes_tagged():
    """Hermes is the ONLY consumer of this file — every name must be loadable there."""
    known = _by_name()
    untagged = [
        f"{phase}.{key}: {name}"
        for phase, key, name in _config_phase_skills()
        if name in known and not _is_hermes_tagged(known[name])
    ]
    assert not untagged, (
        f"lifecycle-config.json names skills Hermes cannot load: {untagged}"
    )


def test_lifecycle_config_build_phase_not_empty():
    """Regression guard: BUILD must keep real content after the dead-name purge."""
    cfg = json.loads(LIFECYCLE_CONFIG.read_text(encoding="utf-8"))
    build = cfg["phases"]["build"]
    assert build.get("skills"), "BUILD phase has no skills"


# ---------------------------------------------------------------------------
# 4. link_awiki_skills.py — the first real consumer of hermes.skills.json
# ---------------------------------------------------------------------------
def test_link_helper_module_exists():
    import link_awiki_skills  # noqa: F401


def test_build_link_plan_selects_only_awiki_paths(tmp_path):
    """Only skills living under skills/awiki/ become Telegram commands.

    Lifecycle/mattpocock skills are linked by their own steps in the init
    script; re-linking them here would create duplicate command names.
    """
    import link_awiki_skills as las

    repo = tmp_path / "repo"
    for rel in ("skills/awiki/a-debug", "skills/engineering/debug-mantra"):
        (repo / rel).mkdir(parents=True)
        (repo / rel / "SKILL.md").write_text("x", encoding="utf-8")
    manifest = {"skills": [
        {"name": "a-debug", "path": "skills/awiki/a-debug/SKILL.md"},
        {"name": "debug-mantra", "path": "skills/engineering/debug-mantra/SKILL.md"},
    ]}

    plan = las.build_link_plan(manifest, repo, tmp_path / "hskills")
    assert [p["name"] for p in plan] == ["a-debug"]


def test_build_link_plan_targets_awiki_namespace(tmp_path):
    """Links land in <skills_root>/awiki/<name> — the proven on-device layout.

    chunk hermes-e put the seven command skills at
    /opt/data/skills/awiki/<name>; matching that keeps one convention.
    """
    import link_awiki_skills as las

    repo = tmp_path / "repo"
    (repo / "skills/awiki/a-plan").mkdir(parents=True)
    (repo / "skills/awiki/a-plan/SKILL.md").write_text("x", encoding="utf-8")
    manifest = {"skills": [{"name": "a-plan", "path": "skills/awiki/a-plan/SKILL.md"}]}

    plan = las.build_link_plan(manifest, repo, tmp_path / "hskills")
    assert plan[0]["link"] == tmp_path / "hskills" / "awiki" / "a-plan"
    assert plan[0]["source"] == repo / "skills" / "awiki" / "a-plan"


def test_build_link_plan_skips_missing_source_dir(tmp_path):
    """A manifest entry whose dir is absent must be skipped, not linked broken.

    The device has hit broken symlinks before (the ``lifecycle/idea-refine``
    orphan); never create one.
    """
    import link_awiki_skills as las

    repo = tmp_path / "repo"
    repo.mkdir()
    manifest = {"skills": [{"name": "ghost", "path": "skills/awiki/ghost/SKILL.md"}]}
    assert las.build_link_plan(manifest, repo, tmp_path / "hskills") == []


def test_build_link_plan_is_deterministic(tmp_path):
    """Same input, same order — the plan is printed and diffed by operators."""
    import link_awiki_skills as las

    repo = tmp_path / "repo"
    for n in ("a-plan", "a-debug", "a-router"):
        (repo / "skills/awiki" / n).mkdir(parents=True)
        (repo / "skills/awiki" / n / "SKILL.md").write_text("x", encoding="utf-8")
    manifest = {"skills": [
        {"name": n, "path": f"skills/awiki/{n}/SKILL.md"}
        for n in ("a-router", "a-plan", "a-debug")
    ]}

    plan = las.build_link_plan(manifest, repo, tmp_path / "h")
    assert [p["name"] for p in plan] == ["a-debug", "a-plan", "a-router"]


def test_apply_plan_creates_symlink(tmp_path):
    import link_awiki_skills as las

    repo = tmp_path / "repo"
    (repo / "skills/awiki/a-debug").mkdir(parents=True)
    (repo / "skills/awiki/a-debug/SKILL.md").write_text("x", encoding="utf-8")
    manifest = {"skills": [{"name": "a-debug", "path": "skills/awiki/a-debug/SKILL.md"}]}

    plan = las.build_link_plan(manifest, repo, tmp_path / "h")
    n = las.apply_plan(plan)
    assert n == 1
    link = tmp_path / "h" / "awiki" / "a-debug"
    assert link.exists(), "link target must resolve"


def test_apply_plan_is_idempotent(tmp_path):
    """Re-running the init script must not fail on links that already exist."""
    import link_awiki_skills as las

    repo = tmp_path / "repo"
    (repo / "skills/awiki/a-debug").mkdir(parents=True)
    (repo / "skills/awiki/a-debug/SKILL.md").write_text("x", encoding="utf-8")
    manifest = {"skills": [{"name": "a-debug", "path": "skills/awiki/a-debug/SKILL.md"}]}

    plan = las.build_link_plan(manifest, repo, tmp_path / "h")
    las.apply_plan(plan)
    las.apply_plan(plan)  # must not raise
    assert (tmp_path / "h" / "awiki" / "a-debug").exists()


def test_dry_run_is_the_default(tmp_path):
    """Default run must not touch the filesystem — mirrors persona-orchestrator."""
    import link_awiki_skills as las

    repo = tmp_path / "repo"
    (repo / "skills/awiki/a-debug").mkdir(parents=True)
    (repo / "skills/awiki/a-debug/SKILL.md").write_text("x", encoding="utf-8")
    manifest_path = tmp_path / "m.json"
    manifest_path.write_text(json.dumps(
        {"skills": [{"name": "a-debug", "path": "skills/awiki/a-debug/SKILL.md"}]}
    ), encoding="utf-8")

    rc = las.main([
        "--manifest", str(manifest_path),
        "--repo-root", str(repo),
        "--skills-root", str(tmp_path / "h"),
    ])
    assert rc == 0
    assert not (tmp_path / "h" / "awiki" / "a-debug").exists(), "dry-run must not link"


# ---------------------------------------------------------------------------
# 5. awiki-init-pi5.sh wiring
# ---------------------------------------------------------------------------
def test_init_pi5_invokes_the_link_helper():
    """The init script must actually call the helper — a helper nothing runs is dead code."""
    body = INIT_PI5.read_text(encoding="utf-8")
    assert "link_awiki_skills.py" in body, (
        "awiki-init-pi5.sh does not run link_awiki_skills.py, so skills/awiki/ "
        "still never reaches the device"
    )
    assert "--apply" in body, "init script must pass --apply (default is dry-run)"


# ---------------------------------------------------------------------------
# 6. tag_hermes.py — the tagger itself
# ---------------------------------------------------------------------------
def test_tag_hermes_allowlist_covers_a_suite():
    """Record the intent in code so a future --apply run stays a no-op for these."""
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "skills_registry"))
    import tag_hermes

    missing = [n for n in A_SUITE_ENTRY_POINTS if n not in tag_hermes.META_ALLOWLIST]
    assert not missing, f"A-Suite entry points absent from META_ALLOWLIST: {missing}"


def test_tag_hermes_survives_a_legacy_codepage():
    """Regression: the dry-run printed '→' and died on Windows cp874.

    Every hook and CLI in this repo must reconfigure its streams to UTF-8; the
    tagger did not, so `python scripts/skills_registry/tag_hermes.py` crashed
    with UnicodeEncodeError on a Thai-locale console — the exact machine that
    needs to run it.
    """
    env = dict(os.environ, PYTHONIOENCODING="cp874")
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "skills_registry" / "tag_hermes.py")],
        capture_output=True, env=env, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, (
        f"tag_hermes.py crashed under a legacy codepage:\n"
        f"{proc.stderr.decode('utf-8', 'replace')}"
    )
