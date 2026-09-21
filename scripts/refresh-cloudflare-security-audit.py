#!/usr/bin/env python3
"""Refresh the tracked Cloudflare security-audit upstream snapshot.

This updates skills/_upstream/cloudflare-security-audit only.
It never overwrites the adapted skills/awiki/a-security package.
"""
from __future__ import annotations

import io
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = REPO_ROOT / "skills" / "_upstream" / "cloudflare-security-audit"
REMOTE = "cloudflare-security-audit"
URL = "https://github.com/cloudflare/security-audit-skill.git"
BRANCH = "main"
SOURCE_PREFIX = PurePosixPath("skills/security-audit")


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def ensure_remote() -> None:
    current = git("remote", "get-url", REMOTE, check=False)
    if current.returncode == 0:
        actual = current.stdout.strip()
        if actual != URL:
            raise SystemExit(
                f"Refusing to replace existing remote {REMOTE!r}: {actual!r}"
            )
        return
    print(f"-> adding remote {REMOTE} -> {URL}")
    git("remote", "add", REMOTE, URL)


def safe_members(tf: tarfile.TarFile):
    prefix_parts = SOURCE_PREFIX.parts
    for member in tf.getmembers():
        path = PurePosixPath(member.name)
        if path.parts[: len(prefix_parts)] != prefix_parts:
            continue
        rel_parts = path.parts[len(prefix_parts) :]
        if not rel_parts:
            continue
        if any(part in {"", ".", ".."} for part in rel_parts):
            raise SystemExit(f"Unsafe archive member: {member.name}")
        if member.issym() or member.islnk() or member.isdev():
            raise SystemExit(f"Unsupported archive member: {member.name}")
        yield member, Path(*rel_parts)


def extract_snapshot(archive_bytes: bytes) -> None:
    if SNAPSHOT_DIR.exists():
        shutil.rmtree(SNAPSHOT_DIR)
    SNAPSHOT_DIR.mkdir(parents=True)

    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as tf:
        for member, relative in safe_members(tf):
            destination = SNAPSHOT_DIR / relative
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise SystemExit(f"Unsupported archive entry: {member.name}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            source = tf.extractfile(member)
            if source is None:
                raise SystemExit(f"Could not read archive member: {member.name}")
            with source, destination.open("wb") as out:
                shutil.copyfileobj(source, out)


def main() -> int:
    ensure_remote()
    print(f"-> fetching {REMOTE}/{BRANCH}")
    git("fetch", REMOTE, BRANCH)
    upstream_sha = git("rev-parse", f"{REMOTE}/{BRANCH}").stdout.strip()

    with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as tmp:
        archive_path = Path(tmp.name)

    try:
        git(
            "archive",
            "--format=tar",
            f"--output={archive_path}",
            f"{REMOTE}/{BRANCH}",
            str(SOURCE_PREFIX),
        )
        extract_snapshot(archive_path.read_bytes())
    finally:
        archive_path.unlink(missing_ok=True)

    license_text = git("show", f"{REMOTE}/{BRANCH}:LICENSE").stdout
    (SNAPSHOT_DIR / "LICENSE.cloudflare").write_text(license_text, encoding="utf-8")
    (SNAPSHOT_DIR / "UPSTREAM-COMMIT").write_text(
        upstream_sha + "\n", encoding="utf-8"
    )

    print(f"Upstream snapshot ready: {SNAPSHOT_DIR.relative_to(REPO_ROOT)}")
    print(f"Commit: {upstream_sha}")
    print(
        "Compare adapted skill: diff -ruN "
        "skills/_upstream/cloudflare-security-audit/ skills/awiki/a-security/"
    )
    print(
        "Review the complete upstream instruction delta before adopting changes; "
        "preserve A-Wiki authority/privacy overlays and rerun all verification gates."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
