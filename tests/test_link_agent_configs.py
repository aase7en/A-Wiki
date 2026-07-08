"""Tests for scripts/link-agent-configs.sh — universal agent-config linker.

Runs the real bash script against a sandboxed HOME + fake drive
(A_WIKI_DRIVE_PATH) so the developer machine's real agent dirs and the
real Google Drive mount are never touched.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "link-agent-configs.sh"

IS_WINDOWS = sys.platform == "win32" or os.name == "nt"


def _is_managed_link(link: Path, expected_target: Path) -> bool:
    """A link is "managed" if it is a real symlink OR a Windows junction that
    resolves to the expected repo target. Path.is_symlink() returns False for
    NTFS junctions on Windows even though they are valid working links, so
    tests must also accept a junction whose realpath matches the target.
    """
    if link.is_symlink():
        return os.readlink(link) == str(expected_target) or link.exists()
    # Junction fallback: resolve through the OS and compare to the target.
    try:
        resolved = Path(os.path.realpath(link))
        return resolved.exists() and resolved.samefile(expected_target)
    except (OSError, ValueError):
        return False


def _base_path() -> str:
    """PATH that lets the script find its tools.

    On Windows the script's junction fallback needs powershell.exe (and the
    cmd.exe mklink fallback), both of which live under System32 — a minimal
    Unix-only PATH makes every junction test fail spuriously. Preserve the
    restricted-Unix-tools intent on non-Windows by keeping the short PATH.
    """
    if IS_WINDOWS:
        # Keep Unix tools first (bash, ln, readlink), then add Windows system
        # dirs so powershell.exe / cmd.exe resolve. /c/WINDOWS/* are the Git
        # Bash mounts of %SystemRoot%.
        return (
            "/usr/bin:/bin:/usr/sbin:/sbin:"
            "/c/WINDOWS/System32:"
            "/c/WINDOWS/System32/WindowsPowerShell/v1.0"
        )
    return "/usr/bin:/bin:/usr/sbin:/sbin"


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
        "PATH": _base_path(),
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

    expected = REPO_ROOT / "agent-skills" / "engineering" / "debug-mantra"
    for agent in (".claude", ".hermes", ".antigravity"):
        link = home / agent / "skills" / "debug-mantra"
        assert _is_managed_link(link, expected), (
            f"{link} not linked to {expected}\n{result.stdout}"
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
    expected = REPO_ROOT / "agent-skills" / "engineering" / "debug-mantra"
    assert _is_managed_link(link, expected)
    # readlink check stays for the symlink case (junctions won't have one)

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
    # Left as a real directory, not converted to a link.
    expected = REPO_ROOT / "agent-skills" / "engineering" / "debug-mantra"
    assert not _is_managed_link(real, expected)
    assert "Skipping existing directory" in result.stdout


def test_agent_flag_creates_dir(tmp_path):
    home, drive = make_env(tmp_path, agents=())
    home.mkdir(parents=True, exist_ok=True)
    result = run_script("--agent", "zcode", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    expected = REPO_ROOT / "agent-skills" / "engineering" / "debug-mantra"
    assert _is_managed_link(home / ".zcode" / "skills" / "debug-mantra", expected)
    # .env may be a symlink OR a copy on Windows (script's copy fallback).
    env_path = home / ".zcode" / ".env"
    assert env_path.exists()


def test_idempotent_rerun(tmp_path):
    home, drive = make_env(tmp_path)
    first = run_script(home=home, drive=drive)
    assert first.returncode == 0, first.stderr + first.stdout
    second = run_script(home=home, drive=drive)
    assert second.returncode == 0, second.stderr + second.stdout
    expected = REPO_ROOT / "agent-skills" / "engineering" / "debug-mantra"
    assert _is_managed_link(home / ".claude" / "skills" / "debug-mantra", expected)


# ── .env linking ────────────────────────────────────────────────────────


def test_env_linked_for_hermes(tmp_path):
    home, drive = make_env(tmp_path)
    result = run_script(home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout

    env_link = home / ".hermes" / ".env"
    env_target = drive / ".agents" / "hermes" / ".env"
    # On systems with symlink support this is a real symlink; on Windows
    # without symlink support the script copies the Drive file as a fallback.
    # Either way the local file must exist and the Drive copy must be real.
    assert env_link.exists(), result.stdout
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
    assert (hermes_home / ".env").exists()
    expected = REPO_ROOT / "agent-skills" / "engineering" / "debug-mantra"
    assert _is_managed_link(
        hermes_home / "skills" / "debug-mantra", expected
    )


def test_existing_real_env_not_overwritten(tmp_path):
    home, drive = make_env(tmp_path, agents=(".hermes",))
    real_env = home / ".hermes" / ".env"
    real_env.write_text("SECRET=local-only\n", encoding="utf-8")

    result = run_script(home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    # The real local file must be left as-is (not migrated without --force).
    assert not real_env.is_symlink()
    assert real_env.read_text(encoding="utf-8") == "SECRET=local-only\n"


def test_force_migrates_real_env_to_drive(tmp_path):
    home, drive = make_env(tmp_path, agents=(".hermes",))
    real_env = home / ".hermes" / ".env"
    real_env.write_text("SECRET=migrate-me\n", encoding="utf-8")

    result = run_script("--force", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    # After --force, local .env is either a symlink to Drive or a copy of it.
    # Either way, the migrated content must land on Drive.
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
    # On Windows this may be a copy rather than a symlink.
    assert repo_env.exists()
    # Drive copy seeded from the sandbox's .env.example
    assert (drive / ".env").read_text(encoding="utf-8") == "EXAMPLE_KEY=fill-me\n"
    # Skills come from the sandbox repo, not the real one
    link = home / ".claude" / "skills" / "dummy-skill"
    expected = sandbox / "agent-skills" / "testing" / "dummy-skill"
    assert _is_managed_link(link, expected)


def test_msys_ln_copy_behavior_never_leaves_silent_copy(tmp_path):
    """Git Bash/MSYS `ln -s` silently deep-copies (or creates a fake dir) and
    exits 0 when symlink support is off. Simulate that with a stub `ln` that
    copies: create_link must detect the non-link result, remove the fake, and
    report the failure — never leave a copy masquerading as a live link.

    PATH is pinned to the stub + minimal Unix dirs on ALL platforms so the
    junction fallback (powershell.exe) is unavailable and the only honest
    outcome is a reported failure. Runs fast on Linux CI — no junctions.
    """
    home, drive = make_env(tmp_path, agents=(".claude",))
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()
    stub = fakebin / "ln"
    stub.write_text(
        "#!/bin/bash\n"
        '# mimic MSYS silent fallback: `ln -s <target> <link>` deep-copies, exit 0\n'
        'if [ "$1" = "-s" ]; then cp -r "$2" "$3"; exit 0; fi\n'
        'exec /bin/ln "$@"\n',
        encoding="utf-8",
    )
    stub.chmod(0o755)

    result = run_script(
        home=home,
        drive=drive,
        extra_env={"PATH": f"{fakebin}:/usr/bin:/bin:/usr/sbin:/sbin"},
    )
    assert result.returncode == 0, result.stderr + result.stdout

    target = home / ".claude" / "skills" / "debug-mantra"
    assert not target.exists(), "silent copy left behind masquerading as a link"
    assert "failed to link" in result.stdout, result.stdout


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
    # On systems with symlink support, the local .env is a symlink to Drive,
    # so removing the Drive copy dangles it → status fails (exit 1).
    # On Windows without symlink support the script COPIES the Drive file as
    # a fallback, so the local copy still exists after the Drive file is
    # removed and status stays OK. Accept both platform behaviors.
    env_link = home / ".hermes" / ".env"
    if env_link.is_symlink():
        assert result.returncode == 1, result.stdout
    else:
        # Copy fallback: local copy survives, status OK.
        assert result.returncode == 0, result.stdout


def test_unlink_removes_managed_links_only(tmp_path):
    home, drive = make_env(tmp_path, agents=(".claude", ".hermes"))
    real = home / ".claude" / "skills" / "my-own-skill"
    real.mkdir(parents=True)
    run_script(home=home, drive=drive)

    result = run_script("--unlink", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    assert not (home / ".claude" / "skills" / "debug-mantra").exists()
    # On symlink-capable systems the managed .env symlink is removed; on
    # Windows copy-fallback systems the local copy is left behind (unlink
    # detects managed links via readlink, which only sees true symlinks).
    env_link = home / ".hermes" / ".env"
    if env_link.is_symlink():
        assert not env_link.exists()
    # unmanaged real dir survives; drive-side data survives
    assert real.is_dir()
    assert (drive / ".agents" / "hermes" / ".env").is_file()


# ── clean-backups (destructive: verify-then-delete) ──────────────────────


def test_clean_backups_deletes_only_when_live_link_verified(tmp_path):
    """--clean-backups removes a <skill>.pre-link-backup-* dir ONLY when the
    live <skill> is a working managed link into the repo."""
    home, drive = make_env(tmp_path, agents=(".claude",))
    run_script("--force-skills", home=home, drive=drive)  # create live links

    skills = home / ".claude" / "skills"
    backup = skills / "debug-mantra.pre-link-backup-20260101000000"
    backup.mkdir()
    (backup / "old.txt").write_text("stale copy", encoding="utf-8")

    # sanity: the live link is verified working
    expected = REPO_ROOT / "agent-skills" / "engineering" / "debug-mantra"
    assert _is_managed_link(skills / "debug-mantra", expected)

    result = run_script("--clean-backups", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    assert not backup.exists(), "backup should be deleted once link verified"
    # live link untouched
    assert _is_managed_link(skills / "debug-mantra", expected)


def test_clean_backups_keeps_backup_when_no_working_link(tmp_path):
    """Safety: if the live skill is missing/not a managed link, the backup is
    KEPT — never delete the only surviving copy."""
    home, drive = make_env(tmp_path, agents=(".claude",))
    skills = home / ".claude" / "skills"
    skills.mkdir(parents=True)
    backup = skills / "debug-mantra.pre-link-backup-20260101000000"
    backup.mkdir()
    marker = backup / "only-copy.txt"
    marker.write_text("do not lose me", encoding="utf-8")
    # NOTE: no live debug-mantra link created

    result = run_script("--clean-backups", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    assert backup.exists(), "backup must be kept when no working link exists"
    assert marker.read_text(encoding="utf-8") == "do not lose me"


def test_clean_backups_dry_run_deletes_nothing(tmp_path):
    home, drive = make_env(tmp_path, agents=(".claude",))
    run_script("--force-skills", home=home, drive=drive)

    skills = home / ".claude" / "skills"
    backup = skills / "debug-mantra.pre-link-backup-20260101000000"
    backup.mkdir()
    (backup / "x.txt").write_text("keep", encoding="utf-8")

    result = run_script("--clean-backups", "--dry-run", home=home, drive=drive)
    assert result.returncode == 0, result.stderr + result.stdout
    assert backup.exists(), "dry-run must not delete"
    assert "dry-run" in result.stdout.lower()
