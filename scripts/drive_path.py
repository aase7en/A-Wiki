"""
drive_path.py — Utility to resolve the personal data storage path.

Usage in other scripts:
    from scripts.drive_path import get_drive_root
    drive = get_drive_root()
    results_dir = drive / "waste-reports" / "2026-05"

Resolution order:
    1. A-Wiki/drive/  (symlink created by setup-drive-link.sh)
    2. A-Wiki/.drive-path  (fallback config when symlink not possible)
    3. ~/.a-wiki-data  (last resort — unsynced local folder)
"""

from __future__ import annotations
from pathlib import Path


def get_drive_root() -> Path:
    """Return the personal data storage root path, always as an existing Path."""
    repo_root = Path(__file__).resolve().parent.parent

    # 1. Symlink or real directory called drive/
    link = repo_root / "drive"
    if link.is_symlink() or link.is_dir():
        target = link.resolve() if link.is_symlink() else link
        if target.exists():
            return target

    # 2. .drive-path config file (fallback for Windows without symlink support)
    cfg = repo_root / ".drive-path"
    if cfg.exists():
        p = Path(cfg.read_text(encoding="utf-8").strip())
        if p.exists():
            return p

    # 3. Last-resort fallback
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
