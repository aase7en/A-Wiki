"""
Resolve the external A-Wiki data storage path.

Resolution order:
1. A-Wiki/drive/ as symlink or Windows Junction/ReparsePoint.
2. A-Wiki/drive/ as a real directory.
3. A-Wiki/.drive-path fallback config.
4. ~/.a-wiki-data unsynced fallback.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def is_reparse_point(path: Path) -> bool:
    """Return True for Windows junctions/symlinks without target access."""
    try:
        attrs = path.stat(follow_symlinks=False).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def resolve_link_target(path: Path) -> Path:
    """Resolve symlinks and Windows junctions with a safe fallback."""
    try:
        return Path(os.path.realpath(str(path)))
    except OSError:
        return path


def path_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def get_drive_root() -> Path:
    """Return the personal data storage root path, always as an existing Path."""
    link = REPO_ROOT / "drive"
    if link.is_symlink() or is_reparse_point(link):
        target = resolve_link_target(link)
        if path_exists(target):
            return target

    try:
        is_dir = link.is_dir()
    except OSError:
        is_dir = False
    if is_dir and path_exists(link):
        return link

    cfg = REPO_ROOT / ".drive-path"
    if path_exists(cfg):
        p = Path(cfg.read_text(encoding="utf-8").strip())
        if path_exists(p):
            return p

    fallback = Path.home() / ".a-wiki-data"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def get_waste_reports_dir(year_month: str | None = None) -> Path:
    """Return drive/waste-reports/ or drive/waste-reports/YYYY-MM/ path."""
    base = get_drive_root() / "waste-reports"
    if year_month:
        base = base / year_month
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_ocr_feedback_dir() -> Path:
    """Return drive/ocr-feedback/ path."""
    p = get_drive_root() / "ocr-feedback"
    p.mkdir(parents=True, exist_ok=True)
    return p


if __name__ == "__main__":
    print(f"Drive root: {get_drive_root()}")
    print(f"Waste reports: {get_waste_reports_dir()}")
    print(f"OCR feedback: {get_ocr_feedback_dir()}")
