#!/usr/bin/env python3
"""
auto-synthesize.py — Automated raw-source-to-synthesis pipeline.

Monitors the raw ingestion flow: when new source files are detected or
quality thresholds are met, automatically triggers synthesis generation
to keep the knowledge graph fresh.

Usage:
    python3 scripts/auto-synthesize.py                              # run full pipeline
    python3 scripts/auto-synthesize.py --check                      # check what needs updating
    python3 scripts/auto-synthesize.py --watch                      # watch mode (poll every 30s)
    python3 scripts/auto-synthesize.py --interval 60                # custom poll interval
    python3 scripts/auto-synthesize.py --force                      # force rebuild all
    python3 scripts/auto-synthesize.py --index                      # also rebuild FAISS index
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_DIR = REPO_ROOT / "wiki" / "sources"
SYNTHESIS_DIR = REPO_ROOT / "wiki" / "synthesis"
STATE_FILE = REPO_ROOT / ".auto-synthesize-state.json"
INDEX_DIR = REPO_ROOT / ".rag-index"

# Minimum sources per domain to trigger auto-synthesis
MIN_SOURCES_FOR_SYNTHESIS = 2

# Quality thresholds
QUALITY_ORDER = ["seed", "draft", "curated", "reviewed"]

# Domain aliases for synthesis filename matching
DOMAIN_ALIASES = {
    "synthesis-iot": "iot",
    "synthesis-env": "env",
    "synthesis-ai-tools": "ai-tools",
    "synthesis-pharmacy": "pharmacy",
    "synthesis-it": "it",
    "synthesis-general": "general",
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def log(msg: str) -> None:
    ts = dt.datetime.now().strftime("%H:%M:%S")
    print(f"[auto-synth {ts}] {msg}")


# ─── State Management ────────────────────────────────────────────────

def load_state() -> dict[str, Any]:
    """Load pipeline state from disk."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            pass
    return {
        "last_run": None,
        "source_counts": {},
        "last_source_hashes": {},
        "synthesis_timestamps": {},
    }


def save_state(state: dict[str, Any]) -> None:
    """Persist pipeline state to disk."""
    state["last_run"] = dt.datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def get_file_hash(filepath: Path) -> str:
    """Simple content hash for change detection."""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    return str(hash(text))


# ─── Source Analysis ─────────────────────────────────────────────────

def analyze_sources() -> dict[str, Any]:
    """Analyze all source files and return metadata."""
    result: dict[str, Any] = {
        "by_domain": defaultdict(list),
        "total": 0,
        "new_files": [],
        "changed_files": [],
        "quality_distribution": defaultdict(int),
    }

    state = load_state()
    last_hashes = state.get("last_source_hashes", {})

    if not SOURCES_DIR.is_dir():
        return result

    for domain_dir in sorted(SOURCES_DIR.iterdir()):
        if not domain_dir.is_dir():
            continue
        domain = domain_dir.name
        for md_file in sorted(domain_dir.glob("*.md")):
            result["total"] += 1
            rel_path = str(md_file.relative_to(REPO_ROOT))

            # Parse basic metadata
            text = md_file.read_text(encoding="utf-8")
            quality = "seed"
            title = md_file.stem.replace("-", " ").title()
            tags = []

            for line in text.splitlines():
                line_s = line.strip()
                kv = re.match(r">\s*\*\*(\w+):\*\*\s*(.+)", line_s)
                if kv:
                    key = kv.group(1).lower()
                    val = kv.group(2).strip()
                    if key == "quality":
                        quality = val.lower()
                    elif key == "title":
                        title = val
                    elif key == "tags":
                        tags = [t.strip() for t in val.split(",")]

            entry = {
                "path": rel_path,
                "domain": domain,
                "quality": quality,
                "title": title,
                "tags": tags,
            }
            result["by_domain"][domain].append(entry)
            result["quality_distribution"][quality] += 1

            # Change detection
            file_hash = get_file_hash(md_file)
            if rel_path not in last_hashes:
                result["new_files"].append(entry)
            elif last_hashes[rel_path] != file_hash:
                result["changed_files"].append(entry)

            # Update hash
            last_hashes[rel_path] = file_hash

    return result


def check_synthesis_status(analysis: dict[str, Any]) -> dict[str, Any]:
    """Check which domains need synthesis updates."""
    state = load_state()
    needs_update: list[str] = []
    up_to_date: list[str] = []
    insufficient: list[str] = []

    for domain, sources in analysis["by_domain"].items():
        if len(sources) < MIN_SOURCES_FOR_SYNTHESIS:
            insufficient.append(domain)
            continue

        # Check if synthesis file exists and is current
        synth_path = SYNTHESIS_DIR / f"synthesis-{domain}.md"
        synth_mtime = state.get("synthesis_timestamps", {}).get(domain)

        if not synth_path.exists():
            needs_update.append(domain)
            continue

        if synth_mtime:
            # Check if any source is newer than last synthesis
            latest_source_mtime = max(
                dt.datetime.fromtimestamp(Path(s["path"]).stat().st_mtime)
                for s in sources
            )
            synth_mtime_dt = dt.datetime.fromisoformat(synth_mtime)
            if latest_source_mtime > synth_mtime_dt:
                needs_update.append(domain)
                continue

        up_to_date.append(domain)

    return {
        "needs_update": needs_update,
        "up_to_date": up_to_date,
        "insufficient": insufficient,
    }


# ─── Synthesis Triggers ──────────────────────────────────────────────

def run_synthesis(domains: list[str] | None = None, force: bool = False) -> int:
    """Run the synthesize.py script for specified domains or all."""
    import subprocess

    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "wiki" / "synthesize.py")]
    if force:
        cmd.append("--rebuild")

    if domains:
        for domain in domains:
            log(f"triggering synthesis for domain '{domain}'...")
            full_cmd = cmd + ["--domain", domain]
            result = subprocess.run(full_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                log(f"synthesis for '{domain}' FAILED: {result.stderr.strip()}")
            else:
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        log(line.strip())
    else:
        log("triggering full synthesis regeneration...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"synthesis FAILED: {result.stderr.strip()}")
            return 0
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                log(line.strip())

    return 1


def run_index_rebuild() -> bool:
    """Rebuild the FAISS RAG index."""
    import subprocess

    log("rebuilding RAG index...")
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "wiki" / "query-rag.py"), "build"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            log(line.strip())
    if result.returncode != 0:
        log(f"index rebuild FAILED: {result.stderr.strip()}")
        return False
    return True


# ─── Watch Mode ──────────────────────────────────────────────────────

def watch_loop(interval: int = 30, rebuild_index: bool = False) -> None:
    """Continuously poll for changes and auto-synthesize."""
    log(f"watch mode started (poll interval: {interval}s, rebuild index: {rebuild_index})")
    log(f"watching: {SOURCES_DIR}")

    try:
        while True:
            analysis = analyze_sources()
            status = check_synthesis_status(analysis)

            if analysis["new_files"]:
                log(f"new files detected: {len(analysis['new_files'])}")
                for f in analysis["new_files"]:
                    log(f"  + {f['path']} ({f['domain']})")

            if analysis["changed_files"]:
                log(f"changed files detected: {len(analysis['changed_files'])}")
                for f in analysis["changed_files"][:5]:
                    log(f"  ~ {f['path']}")

            if status["needs_update"]:
                log(f"domains needing synthesis update: {', '.join(status['needs_update'])}")
                run_synthesis(status["needs_update"])
                if rebuild_index:
                    run_index_rebuild()

                # Update state timestamps
                state = load_state()
                for domain in status["needs_update"]:
                    state["synthesis_timestamps"][domain] = dt.datetime.now().isoformat()
                state["last_source_hashes"] = {
                    Path(p).relative_to(REPO_ROOT).as_posix(): get_file_hash(Path(p))
                    for p in [REPO_ROOT / analysis["by_domain"][d][i]["path"]
                              for d in analysis["by_domain"]
                              for i in range(len(analysis["by_domain"][d]))]
                }
                save_state(state)
            else:
                if analysis["total"] > 0:
                    log(f"all {analysis['total']} sources up to date ({', '.join(status['up_to_date'])})")

            time.sleep(interval)

    except KeyboardInterrupt:
        log("watch mode stopped")


# ─── Report ──────────────────────────────────────────────────────────

def print_report(analysis: dict[str, Any], status: dict[str, Any]) -> None:
    """Print a human-readable status report."""
    print(f"\n{'=' * 60}")
    print(f"  Auto-Synthesis Status Report")
    print(f"  {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    print(f"  Total sources:  {analysis['total']}")
    print(f"  New files:      {len(analysis['new_files'])}")
    print(f"  Changed files:  {len(analysis['changed_files'])}\n")

    print(f"  Quality distribution:")
    for q in QUALITY_ORDER:
        count = analysis["quality_distribution"].get(q, 0)
        if count > 0:
            print(f"    {q:12s}: {count}")

    print(f"\n  Domains:")
    for domain in sorted(analysis["by_domain"].keys()):
        sources = analysis["by_domain"][domain]
        print(f"    {domain:20s}: {len(sources)} sources")

    print(f"\n  Synthesis status:")
    if status["needs_update"]:
        print(f"    ⚠  Needs update: {', '.join(status['needs_update'])}")
    else:
        print(f"    ✅ All up to date")
    if status["insufficient"]:
        print(f"    ⏳ Insufficient sources: {', '.join(status['insufficient'])}")
    if status["up_to_date"]:
        print(f"    ✅ Up to date: {', '.join(status['up_to_date'])}")

    print(f"\n{'=' * 60}\n")


# ─── CLI ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Automated source-to-synthesis pipeline")
    parser.add_argument("--check", action="store_true", help="Check status without generating")
    parser.add_argument("--watch", action="store_true", help="Watch mode (continuous polling)")
    parser.add_argument("--interval", type=int, default=30, help="Poll interval in seconds (default: 30)")
    parser.add_argument("--force", action="store_true", help="Force rebuild all syntheses")
    parser.add_argument("--index", action="store_true", help="Also rebuild FAISS index")
    args = parser.parse_args()

    if args.watch:
        watch_loop(args.interval, args.index)
        return

    # Analyze
    analysis = analyze_sources()
    status = check_synthesis_status(analysis)

    if args.check:
        print_report(analysis, status)
        return

    # Run pipeline
    log(f"analyzed {analysis['total']} sources across {len(analysis['by_domain'])} domains")

    if args.force:
        log("force mode: regenerating all syntheses")
        run_synthesis(force=True)
    elif status["needs_update"]:
        log(f"regenerating syntheses for: {', '.join(status['needs_update'])}")
        run_synthesis(status["needs_update"])
    else:
        log("all syntheses up to date")
        if not analysis["total"]:
            log("WARNING: no sources found to synthesize")
        print_report(analysis, status)
        return

    # Update timestamps
    state = load_state()
    for domain in (status["needs_update"] if not args.force else list(analysis["by_domain"].keys())):
        state["synthesis_timestamps"][domain] = dt.datetime.now().isoformat()

    # Save hashes
    state["last_source_hashes"] = {}
    for domain, sources in analysis["by_domain"].items():
        for s in sources:
            state["last_source_hashes"][s["path"]] = get_file_hash(Path(REPO_ROOT / s["path"]))

    save_state(state)

    if args.index:
        run_index_rebuild()

    print_report(analysis, status)
    log("pipeline complete")


if __name__ == "__main__":
    main()