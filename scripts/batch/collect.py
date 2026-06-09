"""
collect.py — Write validated adapter output to wiki/sources/<slug>.md.

For Tier-1 (realtime) results: called inline by route.py.
For Tier-2/3 (batch) results: invoked by user via CLI after poll.py
reports batch status=completed.

Always runs quality_gate.validate() before writing. Files that fail
validation are skipped and listed in the return summary so the user
can re-run on Tier 3 (escalation).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "batch"))

from adapters import IngestRequest, IngestResult  # noqa: E402
from quality_gate import validate  # noqa: E402
from router import get_adapter  # noqa: E402
from state import COLLECTED, FAILED, get_batch, update_status  # noqa: E402

SOURCES_DIR = REPO_ROOT / "wiki" / "sources"
LOG_PATH = REPO_ROOT / "log.md"
GEN_INDEX = REPO_ROOT / "scripts" / "gen-index.py"


def _strip_code_fence(content: str) -> str:
    """Some models wrap output in ```markdown — strip if present."""
    stripped = content.strip()
    if stripped.startswith("```"):
        first_nl = stripped.find("\n")
        if first_nl >= 0:
            stripped = stripped[first_nl + 1 :]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
    return stripped.strip()


def write_results(results: list[IngestResult], *, run_gen_index: bool = True) -> dict[str, Any]:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    skipped: list[dict] = []

    for r in results:
        if not r.success:
            skipped.append({"slug": r.slug, "reason": f"adapter error: {r.error}", "tier": r.tier})
            continue
        content = _strip_code_fence(r.content)
        ok, reason = validate(content, expected_slug=r.slug, expected_raw_path=r.raw_path)
        if not ok:
            skipped.append({"slug": r.slug, "reason": reason, "tier": r.tier})
            r.metadata["validated"] = False
            continue
        target = SOURCES_DIR / f"{r.slug}.md"
        if target.exists():
            skipped.append({"slug": r.slug, "reason": "target already exists (will not overwrite)", "tier": r.tier})
            continue
        target.write_text(content, encoding="utf-8")
        r.metadata["validated"] = True
        written.append(str(target.relative_to(REPO_ROOT)))

    if written and run_gen_index and GEN_INDEX.is_file():
        try:
            subprocess.run(
                [sys.executable, str(GEN_INDEX)],
                check=True,
                capture_output=True,
                timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            skipped.append({"slug": "_gen_index", "reason": f"gen-index.py failed: {e}", "tier": 0})

    _append_log(written, skipped, results)
    return {"written": written, "skipped": skipped, "total": len(results)}


def _append_log(written: list[str], skipped: list[dict], results: list[IngestResult]) -> None:
    if not written and not skipped:
        return
    in_tokens = sum(r.tokens_in for r in results)
    out_tokens = sum(r.tokens_out for r in results)
    tiers = {r.tier for r in results}
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = [
        f"\n## [{datetime.now().date().isoformat()}] batch ingest — tier {sorted(tiers)} | {ts}",
        f"- Written: {len(written)} sources",
        f"- Skipped: {len(skipped)}",
        f"- Tokens: in={in_tokens:,} out={out_tokens:,}",
    ]
    if skipped:
        entry.append("- Skipped reasons:")
        for s in skipped[:10]:
            entry.append(f"  - `{s['slug']}` — {s['reason']}")
    try:
        with LOG_PATH.open("a", encoding="utf-8") as fp:
            fp.write("\n".join(entry) + "\n")
    except OSError:
        pass


def collect_batch(batch_id: str, *, run_gen_index: bool = True) -> dict[str, Any]:
    """Fetch results for a tier-2/3 batch, validate, write, update state."""
    record = get_batch(batch_id)
    if record is None:
        raise ValueError(f"Unknown batch: {batch_id}")
    tier = int(record["tier"])
    adapter = get_adapter(tier)

    requests_index: dict[str, IngestRequest] = {}
    for f in record["files"]:
        requests_index[f["custom_id"]] = IngestRequest(
            raw_path=f["raw_path"],
            slug=f["slug"],
            custom_id=f["custom_id"],
            date_ingested="",  # not used at collect time
            tier=tier,
        )

    results = adapter.collect(batch_id, requests_index)
    summary = write_results(results, run_gen_index=run_gen_index)
    status = COLLECTED if summary["written"] else FAILED
    update_status(
        batch_id,
        status,
        n_written=len(summary["written"]),
        n_skipped=len(summary["skipped"]),
    )
    summary["batch_id"] = batch_id
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect and write ingested sources from a batch")
    parser.add_argument("--batch", required=True, help="batch_id (from state.jsonl)")
    parser.add_argument("--no-gen-index", action="store_true", help="Skip gen-index.py after writing")
    args = parser.parse_args()

    try:
        summary = collect_batch(args.batch, run_gen_index=not args.no_gen_index)
    except (ValueError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
