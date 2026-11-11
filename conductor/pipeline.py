"""Read-only knowledge-pipeline status projection (A-Conductor Inspector seam).

Brain-side half of the A-Wiki-Conductor Inspector integration (AWC #739),
following `docs/architecture/brain-vs-conductor-division.md`: capabilities for
A-Conductor are added brain-side, and this module only *projects* evidence.

Everything here is evidence-derived: values come from skills-registry.json,
git history, the filesystem and real module importability. The projection
never mutates files, never creates a parallel status store, and reports
UNKNOWN (with the evidence source) instead of inventing a value. Malformed
inputs degrade to UNKNOWN rather than raising (review finding R79-1/R79-4),
traversal is bounded with an explicit truncation marker (R79-2), and checker
failures are never presented as confirmed drift (R79-3).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "awiki-conductor/pipeline-status/1"

# Documented freshness policy: a wiki/sources history older than this is
# classified STALE. The threshold is exposed in the output so an operator
# can disagree with the classification instead of guessing it.
STALE_AFTER_DAYS = 30.0

_RAW_ENTRY_BOUND = 5000  # bound on visited entries (files AND directories)
_GIT_TIMEOUT_S = 10
_DRIFT_TIMEOUT_S = 180

_ROUTING_RULE = ("READY=registry parses + routing.py importable + skill_cards "
                 "importable; DEGRADED=registry parses but a discovery component "
                 "is missing; UNKNOWN=registry unreadable or malformed")
_INGESTION_RULE = ("STALE when last wiki/sources commit is older than "
                   "stale_after_days; UNKNOWN when no evidence")


def _parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _classify_freshness(value, stale_after_days=STALE_AFTER_DAYS):
    """Classify READY | STALE | UNKNOWN from a single timestamp.

    Timezone-naive input is UNKNOWN: guessing a zone would fabricate the
    age. Clock skew (future timestamps) also refuses classification.
    """
    stamp = _parse_iso(value)
    if stamp is None:
        return "UNKNOWN"
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        return "UNKNOWN"  # naive timestamp — refuse to guess a timezone
    try:
        age_days = (datetime.now(timezone.utc) - stamp).total_seconds() / 86400.0
    except TypeError:  # pragma: no cover — defensive: mixed naive/aware
        return "UNKNOWN"
    if age_days < 0:
        return "UNKNOWN"  # clock skew — refuse to classify from bad evidence
    return "STALE" if age_days > stale_after_days else "READY"


def _git_last_commit_iso(repo_root, pathspec):
    """Last commit ISO timestamp touching pathspec; None without git evidence."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "log", "-1", "--format=%cI", "--", pathspec],
            capture_output=True, text=True, timeout=_GIT_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _registry_counts(repo_root):
    """Count statuses straight from the canonical registry file (read-only).

    Malformed container shapes (non-dict root, non-list `skills`) make the
    evidence unavailable (None -> UNKNOWN) instead of crashing or counting
    string characters. Odd entries (non-dict, non-string status) count as
    "other" so a damaged registry is visible, never silent.
    """
    try:
        data = json.loads((repo_root / "skills-registry.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    skills = data.get("skills")
    if not isinstance(skills, list):
        return None
    counts = {"canonical": 0, "deprecated": 0, "alias": 0, "other": 0}
    for entry in skills:
        if not isinstance(entry, dict):
            counts["other"] += 1
            continue
        status = entry.get("status")
        if isinstance(status, str) and status in counts:
            counts[status] += 1
        else:
            counts["other"] += 1
    counts["total"] = len(skills)
    return counts


def _raw_tree_evidence(raw_root, bound=_RAW_ENTRY_BOUND):
    """(file_count, latest mtime ISO, truncated) under a gitignored raw/ tree.

    Traversal is bounded at the OS level: an explicit iterative walk over
    lazy os.scandir iterators counts AT MOST `bound` directory entries (files
    and directories combined) plus exactly one lookahead entry used only to
    detect truncation. No directory is ever enumerated eagerly (review
    finding R79-2 re-review: pathlib rglob materializes whole directories,
    so this function must not use it). When truncated, count/ts describe
    only the visited prefix — a sampled maximum is never presented as the
    whole-tree maximum.
    """
    if not raw_root.is_dir():
        return 0, None, False
    visited = 0
    count = 0
    latest = None
    truncated = False
    pending = [raw_root]
    while pending and not truncated:
        current = pending.pop()
        try:
            with os.scandir(current) as iterator:
                for entry in iterator:  # lazy: pulling is bounded by the budget
                    visited += 1
                    if visited > bound:
                        truncated = True  # lookahead entry — detected, not used
                        break
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(entry.path)
                            continue
                        if entry.is_file(follow_symlinks=False):
                            count += 1
                            mtime = entry.stat(follow_symlinks=False).st_mtime
                        else:
                            continue
                    except OSError:
                        continue
                    if latest is None or mtime > latest:
                        latest = mtime
        except OSError:
            continue
    if latest is None:
        return count, None, truncated
    stamp = datetime.fromtimestamp(latest, tz=timezone.utc).isoformat()
    return count, stamp, truncated


def _routing_capability(repo_root, query):
    """Importability probes + optional bounded routing sample (0 body loads)."""
    out = {
        "router_importable": False,
        "skill_cards_importable": False,
        "sample_query": query,
        "sample_decision": None,
        "sample_cards": None,
        "full_skill_bodies_loaded": None,
    }
    scripts_dir = repo_root / "scripts"
    if not (scripts_dir / "skills_registry" / "routing.py").is_file():
        return out
    saved_path = list(sys.path)
    try:
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        try:
            from skills_registry import routing  # noqa: F401
            out["router_importable"] = True
        except Exception:
            return out
        try:
            from skills_registry import Registry
            from skills_registry.skill_cards import build_cards
            out["skill_cards_importable"] = True
            if query:
                registry = Registry.load(repo_root / "skills-registry.json")
                cards = build_cards(registry, query=str(query), limit=3)
                out["sample_decision"] = cards.get("decision")
                out["sample_cards"] = [
                    {"name": c.get("name"), "match": c.get("match"),
                     "auto_load_candidate": c.get("auto_load_candidate")}
                    for c in cards.get("cards", [])][:3]
                out["full_skill_bodies_loaded"] = cards.get("full_skill_bodies_loaded")
        except Exception:
            pass  # probe result stays False/None — degrade, never crash
    finally:
        sys.path[:] = saved_path
    return out


def _classify_drift(returncode, tail_line):
    """Map a regen --check exit status to honest states (pure function).

    Upstream contract (scripts/regen-skill-surfaces.py docstring):
    0 = success / no drift · 1 = validation OR drift failure · 2 = unexpected
    error. Exit 1 cannot distinguish confirmed drift from a validation error,
    so it is reported as DRIFT_OR_VALIDATION — never as confirmed DRIFT.
    """
    if returncode == 0:
        return "CLEAN", "regen --check exit 0"
    if returncode == 1:
        return "DRIFT_OR_VALIDATION", (tail_line or "regen --check exit 1")
    return "UNKNOWN", "checker failed (exit %s): %s" % (
        returncode, tail_line or "no output")


def _surfaces_drift(repo_root, check):
    if not check:
        return {"state": "UNKNOWN", "reason": "not_checked (pass --check-drift)"}
    script = repo_root / "scripts" / "regen-skill-surfaces.py"
    if not script.is_file():
        return {"state": "UNKNOWN", "reason": "regen-skill-surfaces.py missing"}
    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--check"],
            capture_output=True, text=True, timeout=_DRIFT_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"state": "UNKNOWN", "reason": "run failed: %s" % exc}
    lines = (proc.stdout or proc.stderr or "").strip().splitlines()
    tail = lines[-1] if lines else ""
    state, reason = _classify_drift(proc.returncode, tail)
    return {"state": state, "reason": reason}


def pipeline_status(repo_root, *, query=None, check_drift=False):
    """Project knowledge-pipeline state from evidence only (read-only)."""
    repo_root = Path(repo_root)

    counts = _registry_counts(repo_root)
    routing_probe = _routing_capability(repo_root, query)
    if counts is None:
        routing_state = "UNKNOWN"
    elif counts.get("total") and routing_probe["router_importable"]:
        routing_state = ("READY" if routing_probe["skill_cards_importable"]
                         else "DEGRADED")
    else:
        routing_state = "DEGRADED"

    source_ts = _git_last_commit_iso(repo_root, "wiki/sources")
    sources_dir = repo_root / "wiki" / "sources"
    source_count = len(list(sources_dir.glob("*.md"))) if sources_dir.is_dir() else 0
    raw_count, raw_ts, raw_truncated = _raw_tree_evidence(repo_root / "raw")

    return {
        "schema": SCHEMA,
        "read_only": True,
        "routing": {
            "state": routing_state,
            "classification_rule": _ROUTING_RULE,
            "registry": counts,
            "router_importable": routing_probe["router_importable"],
            "skill_cards_importable": routing_probe["skill_cards_importable"],
            "mcp_skill_route_tool": (repo_root / "scripts" / "lib"
                                     / "neural_spine_mcp.py").is_file(),
            "sample_query": routing_probe["sample_query"],
            "sample_decision": routing_probe["sample_decision"],
            "sample_cards": routing_probe["sample_cards"],
            "full_skill_bodies_loaded": routing_probe["full_skill_bodies_loaded"],
        },
        "ingestion": {
            "state": _classify_freshness(source_ts),
            "classification_rule": _INGESTION_RULE,
            "stale_after_days": STALE_AFTER_DAYS,
            "source_notes": source_count,
            "last_source_ingest": {
                "ts": source_ts,
                "evidence": "git log -1 --format=%cI -- wiki/sources",
            },
            "raw_files": raw_count,
            "raw_truncated": raw_truncated,
            "last_raw_addition": {
                "ts": raw_ts,
                "evidence": ("max file mtime under raw/ (gitignored tree; "
                             "visit bounded — see raw_truncated)"),
            },
            "ingest_tools": {
                "ingest_source_py": (repo_root / "scripts" / "wiki"
                                     / "ingest-source.py").is_file(),
                "scrape_router_py": (repo_root / "scripts" / "wiki"
                                     / "scrape-advanced.py").is_file(),
            },
        },
        "verification": {
            "surfaces_drift": _surfaces_drift(repo_root, check_drift),
        },
    }
