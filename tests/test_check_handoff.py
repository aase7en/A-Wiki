from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check-handoff.py"


def run_check(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SCRIPT), "--path", str(path), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def valid_handoff() -> str:
    return """# Cross-Agent Handoff

## Resume Here

- **Next action**: Run `python3 scripts/check-handoff.py --template --strict`.
- **Canonical source**: `docs/protocols/cross-agent-plan-handoff.md`
- **Verify**: `python3 scripts/check-handoff.py --template --strict`
- **Do not redo**: Template sections already reviewed.

## Exact Resume Command

```bash
python3 scripts/check-handoff.py --template --strict
```

## Suggested Skills

- model-cost-switching — choose the cheapest capable route.
- scrutinize — review protocol changes.
- debug-mantra — use only if a checker failure needs diagnosis.

## Cost Tier Snapshot

| Field | Value |
|---|---|
| Current tier | L1 |
| Cheapest next step | `python3 scripts/check-handoff.py --template --strict` |
| Model scout | unavailable |

## Task Board

| ID | Status | Goal | Files | Verify | Handoff note |
|---|---|---|---|---|---|
| P1.1 | todo | Validate handoff checker | `scripts/check-handoff.py` | `python3 scripts/check-handoff.py --template --strict` | Start with local validation before edits |

## Failed Approaches

None

## Key Decisions

| Decision | Rationale |
|---|---|
| Keep handoff local | Prevent private context from entering tracked git |

## Open Decisions

None

## Blocked

| Chunk | Blocker | Needed input |
|---|---|---|
| - | - | - |
"""


def test_valid_handoff_passes_strict(tmp_path: Path):
    handoff = tmp_path / "HANDOFF.md"
    handoff.write_text(valid_handoff(), encoding="utf-8")

    result = run_check(handoff, "--strict")

    assert result.returncode == 0, result.stderr


def test_placeholder_resume_fails_strict(tmp_path: Path):
    handoff = tmp_path / "HANDOFF.md"
    handoff.write_text(
        valid_handoff().replace(
            "Run `python3 scripts/check-handoff.py --template --strict`.",
            "Replace this line with the one next task.",
        ),
        encoding="utf-8",
    )

    result = run_check(handoff, "--strict")

    assert result.returncode == 1
    assert "placeholder" in result.stderr.lower()


def test_missing_failed_approaches_fails_strict(tmp_path: Path):
    handoff = tmp_path / "HANDOFF.md"
    text = valid_handoff().replace("\n## Failed Approaches\n\nNone\n", "\n")
    handoff.write_text(text, encoding="utf-8")

    result = run_check(handoff, "--strict")

    assert result.returncode == 1
    assert "Failed Approaches" in result.stderr


def test_blocked_row_without_blocker_fails_strict(tmp_path: Path):
    handoff = tmp_path / "HANDOFF.md"
    text = valid_handoff().replace(
        "| P1.1 | todo | Validate handoff checker | `scripts/check-handoff.py` | `python3 scripts/check-handoff.py --template --strict` | Start with local validation before edits |",
        "| P1.1 | blocked | Validate handoff checker | `scripts/check-handoff.py` | `python3 scripts/check-handoff.py --template --strict` | - |",
    )
    handoff.write_text(text, encoding="utf-8")

    result = run_check(handoff, "--strict")

    assert result.returncode == 1
    assert "blocked" in result.stderr.lower()


def test_secret_looking_token_always_fails(tmp_path: Path):
    handoff = tmp_path / "HANDOFF.md"
    secret_like = "sk-" + "realSecretTokenValue1234567890abcdef"
    handoff.write_text(valid_handoff() + f"\n{secret_like}\n", encoding="utf-8")

    result = run_check(handoff)

    assert result.returncode == 2
    assert "secret" in result.stderr.lower()
