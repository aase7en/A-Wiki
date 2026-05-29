from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_DRIVE_LINK_PATH = REPO_ROOT / "scripts" / "hooks" / "check_drive_link.py"
DRIVE_PATH_MODULE = REPO_ROOT / "scripts" / "drive_path.py"

spec = importlib.util.spec_from_file_location("check_drive_link", CHECK_DRIVE_LINK_PATH)
check_drive_link = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_drive_link)

drive_spec = importlib.util.spec_from_file_location("drive_path", DRIVE_PATH_MODULE)
drive_path = importlib.util.module_from_spec(drive_spec)
drive_spec.loader.exec_module(drive_path)


def test_check_drive_accepts_windows_junction(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    drive_link = repo / "drive"
    raw_link = repo / "raw"
    drive_target = tmp_path / "A-Wiki-Data"
    raw_target = drive_target / "raw"
    raw_target.mkdir(parents=True)
    drive_link.mkdir()
    raw_link.mkdir()

    monkeypatch.setattr(check_drive_link, "DRIVE_LINK", drive_link)
    monkeypatch.setattr(check_drive_link, "RAW_LINK", raw_link)
    monkeypatch.setattr(check_drive_link, "DRIVE_PATH_FILE", repo / ".drive-path")
    monkeypatch.setattr(check_drive_link, "is_reparse_point", lambda p: p in {drive_link, raw_link})
    monkeypatch.setattr(
        check_drive_link,
        "resolve_link_target",
        lambda p: drive_target if p == drive_link else raw_target,
    )

    drive_ok, drive_msg = check_drive_link.check_drive()
    raw_ok, raw_msg = check_drive_link.check_raw()

    assert drive_ok, drive_msg
    assert "junction" in drive_msg.lower()
    assert raw_ok, raw_msg
    assert "inside drive" in raw_msg.lower()


def test_check_drive_path_file_fallback(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    drive_target = tmp_path / "A-Wiki-Data"
    drive_target.mkdir()
    cfg = repo / ".drive-path"
    cfg.write_text(str(drive_target), encoding="utf-8")

    monkeypatch.setattr(check_drive_link, "DRIVE_LINK", repo / "drive")
    monkeypatch.setattr(check_drive_link, "DRIVE_PATH_FILE", cfg)

    ok, msg = check_drive_link.check_drive()

    assert ok, msg
    assert ".drive-path" in msg


def test_drive_path_resolves_reparse_target(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    drive_link = repo / "drive"
    drive_link.mkdir()
    drive_target = tmp_path / "A-Wiki-Data"
    drive_target.mkdir()

    monkeypatch.setattr(drive_path, "REPO_ROOT", repo)
    monkeypatch.setattr(drive_path, "is_reparse_point", lambda p: p == drive_link)
    monkeypatch.setattr(drive_path, "resolve_link_target", lambda p: drive_target)

    assert drive_path.get_drive_root() == drive_target
