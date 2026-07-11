from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-privacy.py"
spec = importlib.util.spec_from_file_location("check_privacy", SCRIPT)
assert spec and spec.loader
check_privacy = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = check_privacy
spec.loader.exec_module(check_privacy)


def test_privacy_scan_skips_vendored_anthropic_skills():
    path = check_privacy.REPO_ROOT / "skills" / "anthropic-skills" / "canvas-design" / "canvas-fonts" / "Font-OFL.txt"

    assert check_privacy.should_skip(path)


def test_privacy_scan_does_not_skip_public_wiki_pages():
    path = check_privacy.REPO_ROOT / "wiki" / "synthesis" / "example.md"

    assert not check_privacy.should_skip(path)


# ---------------------------------------------------------------------------
# Fix 1 — Windows cp874 crash: emoji prints must not raise UnicodeEncodeError
# on Thai-locale consoles. Same pattern as scripts/regen-skill-surfaces.py.
# ---------------------------------------------------------------------------

def test_scan_does_not_crash_on_cp874_console(tmp_path):
    import os

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp874"

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--verbose"],
        cwd=str(check_privacy.REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert "UnicodeEncodeError" not in result.stderr
    assert "UnicodeEncodeError" not in result.stdout


# ---------------------------------------------------------------------------
# Fix 2 — binary files (e.g. .xlsx) must not be scanned as text
# ---------------------------------------------------------------------------

def test_is_binary_detects_null_byte_in_first_8kb(tmp_path):
    binfile = tmp_path / "workbook.xlsx"
    binfile.write_bytes(b"PK\x03\x04" + b"\x00" * 10 + b"leakedperson@personaldomain.com")

    assert check_privacy.is_binary(binfile)


def test_is_binary_is_false_for_plain_text(tmp_path):
    textfile = tmp_path / "notes.md"
    textfile.write_text("just some plain markdown text, no null bytes here")

    assert not check_privacy.is_binary(textfile)


def test_binary_xlsx_with_email_like_bytes_is_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    binfile = tmp_path / "customers.xlsx"
    binfile.write_bytes(
        b"PK\x03\x04\x00\x00" + b"\x00binarydata\x00" + b"leakedperson@personaldomain.com" + b"\x00tail\x00"
    )

    findings = check_privacy.scan(files=[binfile])

    assert findings == []


# ---------------------------------------------------------------------------
# Fix 3a — font license files (*-OFL.txt, LICENSE*) skip email checks
# ---------------------------------------------------------------------------

def test_ofl_font_license_file_email_is_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    lic = tmp_path / "SomeFont-OFL.txt"
    lic.write_text("Contact the foundry at designer@fontfoundry-personal.com for support.")

    findings = check_privacy.scan(files=[lic])

    assert not any(f["kind"] == "email" for f in findings)


def test_license_file_email_is_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    lic = tmp_path / "LICENSE"
    lic.write_text("Copyright holder: someone@personal-example-domain.net")

    findings = check_privacy.scan(files=[lic])

    assert not any(f["kind"] == "email" for f in findings)


def test_license_variant_filename_email_is_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    lic = tmp_path / "LICENSE-MIT.txt"
    lic.write_text("owner@personal-example-domain.net owns this.")

    findings = check_privacy.scan(files=[lic])

    assert not any(f["kind"] == "email" for f in findings)


def test_non_license_file_email_is_still_flagged_control_case(tmp_path, monkeypatch):
    # Proves the license skip is scoped to license-like filenames only.
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    ordinary = tmp_path / "notes.md"
    ordinary.write_text("Contact me at leakedperson@personal-example-domain.net please.")

    findings = check_privacy.scan(files=[ordinary])

    assert any(f["kind"] == "email" for f in findings)


# ---------------------------------------------------------------------------
# Fix 3b — bot@<anything> is not a personal email
# ---------------------------------------------------------------------------

def test_bot_email_is_not_personal():
    assert not check_privacy.email_is_personal("bot@sunday-estate.duckdns.org")
    assert not check_privacy.email_is_personal("bot@example-internal.net")


def test_bot_email_finding_is_suppressed_in_scan(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    f = tmp_path / "webhook.md"
    f.write_text("Webhook sender: bot@sunday-estate.duckdns.org")

    findings = check_privacy.scan(files=[f])

    assert not any(x["kind"] == "email" for x in findings)


def test_non_bot_email_at_same_domain_is_still_flagged_control_case(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    f = tmp_path / "webhook.md"
    f.write_text("Human contact: owner@sunday-estate-personal.duckdns.org")

    findings = check_privacy.scan(files=[f])

    assert any(x["kind"] == "email" for x in findings)


# ---------------------------------------------------------------------------
# Fix 3c — doc-placeholder home paths extend SYSTEM_USERS
# ---------------------------------------------------------------------------

def test_windows_placeholder_home_paths_are_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    f = tmp_path / "doc.md"
    f.write_text(
        "C:/Users/name/project\n"
        "C:/Users/user/project\n"
        "C:/Users/work/project\n"
        "C:/Users/you/project\n"
    )

    findings = check_privacy.scan(files=[f])

    assert not any(x["kind"] == "home_path" for x in findings)


def test_linux_placeholder_home_paths_are_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    f = tmp_path / "doc.md"
    f.write_text("/home/user/project\n/home/you/project\n")

    findings = check_privacy.scan(files=[f])

    assert not any(x["kind"] == "home_path" for x in findings)


def test_real_looking_username_home_path_is_still_flagged_control_case(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    f = tmp_path / "doc.md"
    f.write_text("C:/Users/johnsmith2024/project\n")

    findings = check_privacy.scan(files=[f])

    assert any(x["kind"] == "home_path" for x in findings)


# ---------------------------------------------------------------------------
# Fix 4 — email regex must not match `ssh user@host` targets
# ---------------------------------------------------------------------------

def test_ssh_target_is_not_flagged_as_email(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    f = tmp_path / "pi5-quick-start.md"
    f.write_text("ssh umbrel@umbrel-1.tail<id>.ts.net\n# ใส่รหัสผ่าน umbrel\n")

    findings = check_privacy.scan(files=[f])

    assert not any(x["kind"] == "email" for x in findings)


def test_tailscale_and_local_domains_are_not_personal():
    assert not check_privacy.email_is_personal("root@nas1.ts.net")
    assert not check_privacy.email_is_personal("admin@myhost.local")


def test_ordinary_email_on_non_ssh_line_is_still_flagged_control_case(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    f = tmp_path / "doc.md"
    f.write_text("Reach me at leakedperson@personal-example-domain.net anytime.\n")

    findings = check_privacy.scan(files=[f])

    assert any(x["kind"] == "email" for x in findings)


# ---------------------------------------------------------------------------
# Fix 5 — NEW check: tracked-but-gitignored files (escaped-private-file bug)
# ---------------------------------------------------------------------------

def _init_tmp_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)


def test_tracked_but_ignored_detects_escaped_private_file(tmp_path, monkeypatch):
    _init_tmp_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("session-memory.md\n")
    (tmp_path / "session-memory.md").write_text("private notes")
    (tmp_path / "normal.md").write_text("public notes")
    subprocess.run(
        ["git", "add", "-f", "session-memory.md", "normal.md", ".gitignore"],
        cwd=tmp_path, check=True,
    )
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)

    ignored = check_privacy.tracked_but_ignored()

    assert "session-memory.md" in ignored
    assert "normal.md" not in ignored


def test_scan_surfaces_tracked_but_ignored_as_high_priority_finding(tmp_path, monkeypatch):
    _init_tmp_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("session-memory.md\n")
    (tmp_path / "session-memory.md").write_text("private notes, nothing else sensitive")
    subprocess.run(["git", "add", "-f", "session-memory.md", ".gitignore"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)

    findings = check_privacy.scan()  # files=None -> full default scan path

    kinds = {f["kind"] for f in findings}
    assert "tracked-but-gitignored" in kinds
    hit = next(f for f in findings if f["kind"] == "tracked-but-gitignored")
    assert hit["file"] == "session-memory.md"


def test_tracked_but_ignored_is_empty_when_nothing_escaped(tmp_path, monkeypatch):
    _init_tmp_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("*.secret\n")
    (tmp_path / "normal.md").write_text("public notes")
    subprocess.run(["git", "add", "normal.md", ".gitignore"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)

    assert check_privacy.tracked_but_ignored() == []


# ---------------------------------------------------------------------------
# Fix 6 — NEW check: extra personal patterns loaded from a private file
# ---------------------------------------------------------------------------

def test_extra_personal_patterns_from_explicit_path_are_flagged_p0(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    pattern_file = tmp_path / "patterns.txt"
    pattern_file.write_text("# comment line\n\nReallyPersonalNameXYZ\n123 Totally Real Street\n")
    target = tmp_path / "leaky.md"
    target.write_text("Contact ReallyPersonalNameXYZ at 123 Totally Real Street please.")

    findings = check_privacy.scan(files=[target], extra_patterns_path=pattern_file)

    assert len(findings) >= 2
    assert all(f["kind"] == "P0/personal-data" for f in findings)


def test_extra_personal_patterns_file_missing_is_a_noop(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    target = tmp_path / "clean.md"
    target.write_text("Nothing sensitive in here at all.")

    findings = check_privacy.scan(
        files=[target], extra_patterns_path=tmp_path / "does-not-exist.txt"
    )

    assert findings == []


def test_extra_personal_patterns_env_override(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    pattern_file = tmp_path / "custom-patterns.txt"
    pattern_file.write_text("SuperSecretCodeword\n")
    monkeypatch.setenv(check_privacy.PRIVACY_PATTERNS_ENV, str(pattern_file))
    target = tmp_path / "f.md"
    target.write_text("this contains SuperSecretCodeword right here")

    findings = check_privacy.scan(files=[target])  # no explicit path -> env used

    assert any(f["kind"] == "P0/personal-data" for f in findings)


def test_public_scanner_source_has_no_hardcoded_pii_regex_defaults():
    # Iron Law: real name/address patterns must NEVER be hardcoded in the
    # public scanner — only loaded at runtime from a private gitignored file
    # under drive/personal/ (already gitignored).
    assert "DEFAULT_PRIVACY_PATTERNS_FILE" in SCRIPT.read_text(encoding="utf-8")
    default_path = str(check_privacy.DEFAULT_PRIVACY_PATTERNS_FILE)
    assert "drive" in default_path and "personal" in default_path
    # No default patterns file shipped in the repo -> loader must be a no-op
    # unless a test/user explicitly points it elsewhere.
    if not check_privacy.DEFAULT_PRIVACY_PATTERNS_FILE.exists():
        assert check_privacy.load_extra_personal_patterns() == []


# ---------------------------------------------------------------------------
# Fix 7 — aase7en codename lookahead: github.io pages + repo URL are OK
# ---------------------------------------------------------------------------

def test_codename_allows_github_io_pages_url(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    f = tmp_path / "readme.md"
    f.write_text("See https://aase7en.github.io/A-Wiki/ for docs.\n")

    findings = check_privacy.scan(files=[f])

    assert not any(x["kind"] == "codename" for x in findings)


def test_codename_still_allows_repo_url(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    f = tmp_path / "readme.md"
    f.write_text("Source: https://github.com/aase7en/A-Wiki\n")

    findings = check_privacy.scan(files=[f])

    assert not any(x["kind"] == "codename" for x in findings)


def test_codename_still_flagged_in_ordinary_context_control_case(tmp_path, monkeypatch):
    monkeypatch.setattr(check_privacy, "REPO_ROOT", tmp_path)
    f = tmp_path / "notes.md"
    f.write_text("Contact aase7en directly for access.\n")

    findings = check_privacy.scan(files=[f])

    assert any(x["kind"] == "codename" for x in findings)
