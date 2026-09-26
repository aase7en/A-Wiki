from __future__ import annotations

import io
import tarfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "refresh-cloudflare-security-audit.py"
SPEC = spec_from_file_location("refresh_cloudflare_security_audit", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
refresh = module_from_spec(SPEC)
SPEC.loader.exec_module(refresh)


def _tar_bytes(
    files: dict[str, bytes],
    *,
    symlink: tuple[str, str] | None = None,
) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, payload in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
        if symlink is not None:
            name, target = symlink
            info = tarfile.TarInfo(name)
            info.type = tarfile.SYMTYPE
            info.linkname = target
            archive.addfile(info)
    return buffer.getvalue()


def test_extract_snapshot_only_copies_upstream_skill_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    snapshot = tmp_path / "snapshot"
    monkeypatch.setattr(refresh, "SNAPSHOT_DIR", snapshot)
    archive = _tar_bytes(
        {
            "skills/security-audit/SKILL.md": b"# upstream\n",
            "skills/security-audit/report-schema.json": b"[]\n",
            "skills/other/SKILL.md": b"# ignore\n",
            "README.md": b"ignore\n",
        }
    )

    refresh.extract_snapshot(archive)

    assert (snapshot / "SKILL.md").read_bytes() == b"# upstream\n"
    assert (snapshot / "report-schema.json").read_bytes() == b"[]\n"
    assert not (snapshot / "skills").exists()
    assert not (snapshot / "README.md").exists()


def test_safe_members_rejects_symlink_inside_upstream_tree() -> None:
    archive = _tar_bytes(
        {"skills/security-audit/SKILL.md": b"# upstream\n"},
        symlink=("skills/security-audit/link", "../../outside"),
    )
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tf:
        with pytest.raises(SystemExit, match="Unsupported archive member"):
            list(refresh.safe_members(tf))


def test_ensure_remote_refuses_existing_remote_with_different_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_git(*args: str, check: bool = True):
        assert args == ("remote", "get-url", refresh.REMOTE)
        return SimpleNamespace(returncode=0, stdout="https://example.invalid/wrong.git\n")

    monkeypatch.setattr(refresh, "git", fake_git)

    with pytest.raises(SystemExit, match="Refusing to replace existing remote"):
        refresh.ensure_remote()


def test_ensure_remote_adds_expected_remote_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[tuple[str, ...], bool]] = []

    def fake_git(*args: str, check: bool = True):
        calls.append((args, check))
        if args == ("remote", "get-url", refresh.REMOTE):
            return SimpleNamespace(returncode=2, stdout="")
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr(refresh, "git", fake_git)

    refresh.ensure_remote()

    assert calls == [
        (("remote", "get-url", refresh.REMOTE), False),
        (("remote", "add", refresh.REMOTE, refresh.URL), True),
    ]
