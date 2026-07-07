"""Tests for scripts/link-agent-configs.sh — universal agent-config linker.

Runs the real bash script against a sandboxed HOME + fake drive
(A_WIKI_DRIVE_PATH) so the developer machine's real agent dirs and the
real Google Drive mount are never touched.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "link-agent-configs.sh"


def run_script(
    *args: str,
    home: Path,
    drive: Path,
    extra_env: dict[str, str] | None = None,
    manage_repo_env: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run the real script against a sandboxed HOME + fake drive.

    manage_repo_env defaults to False so tests can NEVER touch this real
    repo's own .env by accident (the script's default --repo-root is the
    real A-Wiki checkout unless overridden) — only the test that explicitly
    passes --repo-root with a sandbox repo may set this True.
    """
    env = {
        "HOME": str(home),
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "A_WIKI_DRIVE_PATH": str(drive),
    }
    if extra_env:
        env.update(extra_env)
    full_args = list(args)
    if not manage_repo_env:
        full_args.append("--no-repo-env")
    return subprocess.run(
        ["bash", str(SCRIPT), *full_args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def make_env(
    tmp_path: Path, agents: tuple[str, ...] = (".claude", ".hermes", ".antigravity")
) -> tuple[Path, Path]:
    home = tmp_path / "home"
    drive = tmp_path / "drive"
    for a in agents:
        (home / a).mkdir(parents=True)
    drive.mkdir(parents=True, exist_ok=True)
    return home, drive


def make_sandbox_repo(tmp_path: Path) -> Path:
    """Minimal fake repo so --repo-root tests never touch the real repo's .env."""
    repo = tmp_path / "repo"
    skill = repo / "agent-skills" / "testing" / "dummy-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: dummy-skill\n---\n", encoding="utf-8")
    (repo / ".env.example").write_text("EXAMPLE_KEY=fill-me\n", encoding="utf-8")
    return repo


# ── skills linking ──────────────────────────────────────────────────────


def test_links_skills_for_detected_agents(tmp_path):
    home, drive = make_env(tmp_path)
    result = run_script(home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout

    for agent in (".claude", ".hermes", ".antigravity"):
        link = home / agent / "skills" / "debug-mantra"
        assert link.is_symlink(), f"{link} not linked\n{result.stdout}"
        assert os.readlink(link) == str(
            REPO_ROOT / "agent-skills" / "engineering" / "debug-mantra"
        )

    # Agents not installed on this machine are skipped, not created.
    assert not (home / ".zcode").exists()


def test_keeps_existing_real_directory(tmp_path):
    home, drive = make_env(tmp_path, agents=(".claude",))
    real = home / ".claude" / "skills" / "debug-mantra"
    real.mkdir(parents=True)
    marker = real / "KEEP"
    marker.write_text("do not delete", encoding="utf-8")

    result = run_script(home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    assert marker.read_text(encoding="utf-8") == "do not delete"
    assert "Skipping existing directory" in result.stdout


def test_force_skills_replaces_matching_real_dir_and_backs_up_content(tmp_path):
    home, drive = make_env(tmp_path, agents=(".claude",))
    real = home / ".claude" / "skills" / "debug-mantra"
    real.mkdir(parents=True)
    marker = real / "KEEP"
    marker.write_text("pre-existing content", encoding="utf-8")

    result = run_script("--force-skills", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout

    link = home / ".claude" / "skills" / "debug-mantra"
    assert link.is_symlink()
    assert os.readlink(link) == str(
        REPO_ROOT / "agent-skills" / "engineering" / "debug-mantra"
    )

    # Original content must be backed up somewhere under the skills dir, not deleted.
    skills_dir = home / ".claude" / "skills"
    backups = list(skills_dir.glob("debug-mantra.pre-link-backup-*"))
    assert len(backups) == 1, f"expected exactly one backup, found: {list(skills_dir.iterdir())}"
    assert (backups[0] / "KEEP").read_text(encoding="utf-8") == "pre-existing content"


def test_force_skills_does_not_touch_unmatched_real_dir(tmp_path):
    home, drive = make_env(tmp_path, agents=(".claude",))
    custom = home / ".claude" / "skills" / "my-totally-custom-skill"
    custom.mkdir(parents=True)
    marker = custom / "KEEP"
    marker.write_text("not an A-Wiki skill", encoding="utf-8")

    result = run_script("--force-skills", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout

    assert not custom.is_symlink()
    assert custom.is_dir()
    assert marker.read_text(encoding="utf-8") == "not an A-Wiki skill"


def test_without_force_skills_real_dir_is_left_alone(tmp_path):
    home, drive = make_env(tmp_path, agents=(".claude",))
    real = home / ".claude" / "skills" / "debug-mantra"
    real.mkdir(parents=True)

    result = run_script(home=home, drive=drive)  # no --force-skills
    assert result.returncode == 0, result.stderr + result.stdout
    assert not real.is_symlink()
    assert "Skipping existing directory" in result.stdout


def test_agent_flag_creates_dir(tmp_path):
    home, drive = make_env(tmp_path, agents=())
    home.mkdir(parents=True, exist_ok=True)
    result = run_script("--agent", "zcode", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    assert (home / ".zcode" / "skills" / "debug-mantra").is_symlink()
    assert (home / ".zcode" / ".env").is_symlink()


def test_idempotent_rerun(tmp_path):
    home, drive = make_env(tmp_path)
    first = run_script(home=home, drive=drive)
    assert first.returncode == 0, first.stderr + first.stdout
    second = run_script(home=home, drive=drive)
    assert second.returncode == 0, second.stderr + second.stdout
    assert (home / ".claude" / "skills" / "debug-mantra").is_symlink()


# ── .env linking ────────────────────────────────────────────────────────


def test_env_linked_for_hermes(tmp_path):
    home, drive = make_env(tmp_path)
    result = run_script(home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout

    env_link = home / ".hermes" / ".env"
    env_target = drive / ".agents" / "hermes" / ".env"
    assert env_link.is_symlink(), result.stdout
    assert os.readlink(env_link) == str(env_target)
    assert env_target.is_file()


def test_hermes_home_override(tmp_path):
    home, drive = make_env(tmp_path, agents=())
    hermes_home = home / "hermes-profile"
    hermes_home.mkdir(parents=True)
    result = run_script(
        "--agent",
        "hermes",
        home=home,
        drive=drive,
        extra_env={"HERMES_HOME": str(hermes_home)},
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert (hermes_home / ".env").is_symlink()
    assert (hermes_home / "skills" / "debug-mantra").is_symlink()


def test_existing_real_env_not_overwritten(tmp_path):
    home, drive = make_env(tmp_path, agents=(".hermes",))
    real_env = home / ".hermes" / ".env"
    real_env.write_text("SECRET=local-only\n", encoding="utf-8")

    result = run_script(home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    assert not real_env.is_symlink()
    assert real_env.read_text(encoding="utf-8") == "SECRET=local-only\n"


def test_force_migrates_real_env_to_drive(tmp_path):
    home, drive = make_env(tmp_path, agents=(".hermes",))
    real_env = home / ".hermes" / ".env"
    real_env.write_text("SECRET=migrate-me\n", encoding="utf-8")

    result = run_script("--force", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    assert real_env.is_symlink()
    target = drive / ".agents" / "hermes" / ".env"
    assert target.read_text(encoding="utf-8") == "SECRET=migrate-me\n"


def test_repo_env_linked_via_repo_root(tmp_path):
    home, drive = make_env(tmp_path, agents=(".claude",))
    sandbox = make_sandbox_repo(tmp_path)

    result = run_script(
        "--repo-root", str(sandbox), home=home, drive=drive, manage_repo_env=True
    )
    assert result.returncode == 0, result.stderr + result.stdout

    repo_env = sandbox / ".env"
    assert repo_env.is_symlink()
    assert os.readlink(repo_env) == str(drive / ".env")
    # Drive copy seeded from the sandbox's .env.example
    assert (drive / ".env").read_text(encoding="utf-8") == "EXAMPLE_KEY=fill-me\n"
    # Skills come from the sandbox repo, not the real one
    link = home / ".claude" / "skills" / "dummy-skill"
    assert link.is_symlink()
    assert os.readlink(link) == str(
        sandbox / "agent-skills" / "testing" / "dummy-skill"
    )


# ── status / unlink ─────────────────────────────────────────────────────


def test_status_ok_after_link(tmp_path):
    home, drive = make_env(tmp_path)
    run_script(home=home, drive=drive)
    result = run_script("--status", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    assert "claude" in result.stdout


def test_status_counts_real_link_target_not_just_symlink_bit(tmp_path):
    """Regression guard for the realpath-based rewrite (Windows junctions
    aren't `-L` true but do resolve correctly via realpath) — an unrelated
    real directory sitting alongside must never be miscounted as managed."""
    home, drive = make_env(tmp_path, agents=(".claude",))
    unrelated = home / ".claude" / "skills" / "not-an-a-wiki-skill"
    unrelated.mkdir(parents=True)

    run_script(home=home, drive=drive)
    result = run_script("--status", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    for line in result.stdout.splitlines():
        if line.strip().startswith("[ OK ] claude:"):
            assert "0 skills linked" not in line, line
            break
    else:
        raise AssertionError(f"no claude status line found:\n{result.stdout}")


def test_status_fails_on_dangling_env(tmp_path):
    home, drive = make_env(tmp_path)
    run_script(home=home, drive=drive)
    (drive / ".agents" / "hermes" / ".env").unlink()
    result = run_script("--status", home=home, drive=drive)
    assert result.returncode == 1, result.stdout


def test_unlink_removes_managed_links_only(tmp_path):
    home, drive = make_env(tmp_path, agents=(".claude", ".hermes"))
    real = home / ".claude" / "skills" / "my-own-skill"
    real.mkdir(parents=True)
    run_script(home=home, drive=drive)

    result = run_script("--unlink", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    assert not (home / ".claude" / "skills" / "debug-mantra").exists()
    assert not (home / ".hermes" / ".env").exists()
    # unmanaged real dir survives; drive-side data survives
    assert real.is_dir()
    assert (drive / ".agents" / "hermes" / ".env").is_file()
