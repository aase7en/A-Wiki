from __future__ import annotations

import importlib.util
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
