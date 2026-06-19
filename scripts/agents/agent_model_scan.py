#!/usr/bin/env python3
"""Weekly agent-model benchmark scanner with safe auto-apply.

Offline-first: uses committed scorecard (model-capability-scores.json) as the
durable floor, then best-effort refreshes from leaderboards via
model-capability-scout.py. Only auto-applies model changes within the same
cost class when capability gain >= min_gain.

Usage:
  python3 scripts/agents/agent_model_scan.py --dry-run      # report only
  python3 scripts/agents/agent_model_scan.py --apply         # write changes
  python3 scripts/agents/agent_model_scan.py --revert        # undo last scan
  python3 scripts/agents/agent_model_scan.py --offline       # skip network
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = REPO_ROOT / "wiki" / "context" / "agent-model-policy.json"
DEFAULT_SCORECARD = REPO_ROOT / "wiki" / "context" / "model-capability-scores.json"
SCOUT_PY = REPO_ROOT / "scripts" / "model-capability-scout.py"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        return json.loads(path.read_text("utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot load {label} at {path}: {exc}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Cost class helpers
# ---------------------------------------------------------------------------

def cost_rank(policy: dict[str, Any], class_name: str) -> int:
    return policy["cost_classes"][class_name]["rank"]


def is_safe_swap(policy: dict[str, Any], current_class: str, candidate_class: str) -> bool:
    current_rank = cost_rank(policy, current_class)
    candidate_rank = cost_rank(policy, candidate_class)
    return candidate_rank <= current_rank


# ---------------------------------------------------------------------------
# Capability scoring
# ---------------------------------------------------------------------------

def capability_for_model(scorecard: dict[str, Any], model_id: str, dimension: str) -> int:
    families = scorecard.get("families", {})
    neutral = scorecard.get("neutral_default", 50)
    low = model_id.lower()
    for fam_name, fam in families.items():
        if any(sub in low for sub in fam.get("match", [])):
            return fam.get(dimension, neutral)
    return neutral


def _derive_family_cost_class(agents: dict[str, Any], scorecard: dict[str, Any]) -> dict[str, str]:
    families = scorecard.get("families", {})
    mapping: dict[str, str] = {}
    for name, cfg in agents.items():
        model = cfg.get("current_model", "")
        cost_class = cfg.get("cost_class", "free")
        low = model.lower()
        for fam_key, fam in families.items():
            if any(sub in low for sub in fam.get("match", [])):
                mapping[fam_key] = cost_class
    return mapping


# ---------------------------------------------------------------------------
# Candidate selection
# ---------------------------------------------------------------------------

def decide_agent(agent_cfg: dict[str, Any], scorecard: dict[str, Any],
                 policy: dict[str, Any]) -> dict[str, Any]:
    current_model = agent_cfg.get("current_model", "")
    role = agent_cfg.get("role_dimension", "swe_bench")
    cost_class = agent_cfg.get("cost_class", "free")
    candidate_families = agent_cfg.get("candidate_families", [])
    managed = agent_cfg.get("managed", True)
    min_gain = policy.get("apply_policy", {}).get("min_capability_gain", 5)

    families = scorecard.get("families", {})
    neutral = scorecard.get("neutral_default", 50)
    family_cost_class = _derive_family_cost_class(policy.get("agents", {}), scorecard)

    # score current model
    current_score = capability_for_model(scorecard, current_model, role)

    # evaluate each candidate family
    best_family: str | None = None
    best_score = current_score
    best_action = "none"

    for fam_key in candidate_families:
        fam = families.get(fam_key, {})
        cand_score = fam.get(role, neutral)
        gain = cand_score - current_score
        if gain < min_gain:
            continue

        cand_cost_class = family_cost_class.get(fam_key, "free")
        safe = is_safe_swap(policy, cost_class, cand_cost_class)

        if not safe:
            # tier-up detected
            if cand_score > best_score:
                best_family = fam_key
                best_score = cand_score
                best_action = "propose"
            continue

        if cand_score > best_score:
            best_family = fam_key
            best_score = cand_score
            best_action = "apply"

    result: dict[str, Any] = {
        "action": best_action if managed else ("propose" if best_action == "propose" else "none"),
        "from": current_model,
        "to": f"agent-model-scan/auto/{best_family}" if best_family else "",
        "gain": best_score - current_score if best_family else 0,
        "agent_name": agent_cfg.get("name", agent_cfg.get("options", {}).get("id", "unknown")),
        "role_dimension": role,
        "cost_class": cost_class,
    }

    if best_action == "none" or (best_action == "propose" and not managed):
        result["action"] = "none"
    elif best_action == "propose" and managed:
        result["action"] = "propose"
    elif best_action == "apply" and managed:
        result["action"] = "apply"
    else:
        result["action"] = "none"

    if result["action"] == "none":
        result.update({"from": "", "to": "", "gain": 0})

    return result


# ---------------------------------------------------------------------------
# Frontmatter rewrite
# ---------------------------------------------------------------------------

def rewrite_frontmatter_model(text: str, new_model: str) -> str:
    lines = text.splitlines(keepends=True)
    in_frontmatter = False
    fm_start = -1
    fm_end = -1
    found_model = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "---":
            if not in_frontmatter:
                in_frontmatter = True
                fm_start = i
            else:
                fm_end = i
                break
        if in_frontmatter and line.startswith("model:"):
            lines[i] = f"model: {new_model}\n"
            found_model = True

    if found_model:
        return "".join(lines)

    # model not found in frontmatter -> insert after first ---
    if fm_start >= 0:
        insert_at = fm_start + 1
        lines.insert(insert_at, f"model: {new_model}\n")
        return "".join(lines)

    # no frontmatter at all -> wrap whole content
    return f"---\nmodel: {new_model}\n---\n{text}"


# ---------------------------------------------------------------------------
# Scan runner
# ---------------------------------------------------------------------------

def run_scan(policy: dict[str, Any], scorecard: dict[str, Any],
             apply_changes: bool, repo_root: Path) -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    applied = 0
    proposed = 0

    for name, agent_cfg in policy.get("agents", {}).items():
        if not agent_cfg.get("managed", True):
            continue
        decision = decide_agent(agent_cfg, scorecard, policy)
        decision["agent_name"] = name

        action = decision["action"]
        if action == "apply":
            applied += 1
            file_rel = agent_cfg.get("file", f".kilo/agents/{name}.md")
            file_path = repo_root / file_rel
            if file_path.exists():
                old_text = file_path.read_text("utf-8")
                new_text = rewrite_frontmatter_model(old_text, decision["to"])
                if apply_changes:
                    file_path.write_text(new_text, "utf-8")
                    # write revert log
                    log_path_str = policy.get("apply_policy", {}).get("revert_log", "")
                    if log_path_str:
                        log_path = repo_root / log_path_str
                        log_path.parent.mkdir(parents=True, exist_ok=True)
                        entry = {
                            "agent": name,
                            "from": decision["from"],
                            "to": decision["to"],
                            "timestamp": now_iso(),
                            "file": str(file_rel),
                        }
                        with log_path.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        elif action == "propose":
            proposed += 1

        decisions.append(decision)

    return {
        "decisions": decisions,
        "applied": applied,
        "proposed": proposed,
        "timestamp": now_iso(),
    }


def revert_last(policy: dict[str, Any], repo_root: Path) -> None:
    log_path_str = policy.get("apply_policy", {}).get("revert_log", "")
    if not log_path_str:
        print("ERROR: no revert_log configured in policy", file=sys.stderr)
        sys.exit(1)

    log_path = repo_root / log_path_str
    if not log_path.exists():
        print("ERROR: revert log not found", file=sys.stderr)
        sys.exit(1)

    lines = log_path.read_text("utf-8").strip().splitlines()
    if not lines:
        print("ERROR: revert log is empty", file=sys.stderr)
        sys.exit(1)

    last_line = lines[-1]
    entry = json.loads(last_line)
    file_path = repo_root / entry["file"]
    old_model = entry["from"]

    if not file_path.exists():
        print(f"ERROR: file {file_path} not found", file=sys.stderr)
        sys.exit(1)

    text = file_path.read_text("utf-8")
    new_text = rewrite_frontmatter_model(text, old_model)
    file_path.write_text(new_text, "utf-8")
    print(f"Reverted {entry['file']}: {entry['to']} -> {entry['from']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Weekly agent-model benchmark scanner")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="report what would change (default)")
    parser.add_argument("--apply", action="store_true",
                        help="apply safe model changes and log revert info")
    parser.add_argument("--revert", action="store_true",
                        help="undo last scan write (revert from log)")
    parser.add_argument("--offline", action="store_true",
                        help="skip network refresh of scorecard")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY,
                        help="path to agent-model-policy.json")
    parser.add_argument("--scorecard", type=Path, default=DEFAULT_SCORECARD,
                        help="path to model-capability-scores.json")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT,
                        help="repo root (default: auto)")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # resolve conflicting flags
    apply_changes = args.apply or False
    if args.dry_run and args.apply:
        # --apply overrides default --dry-run
        apply_changes = True

    if args.revert:
        policy = load_json(args.policy, "policy")
        revert_last(policy, args.repo_root)
        return 0

    policy = load_json(args.policy, "policy")
    scorecard = load_json(args.scorecard, "scorecard")

    # best-effort live refresh (reuse model-capability-scout.py)
    if not args.offline and SCOUT_PY.exists():
        try:
            spec = importlib.util.spec_from_file_location(
                "model_capability_scout", SCOUT_PY
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            cache = mod.build_cache(offline=False, timeout=8)
            if cache.get("families"):
                scorecard = cache
        except Exception:
            pass  # offline-first: keep committed

    report = run_scan(policy, scorecard, apply_changes, args.repo_root)

    action_label = "DRY-RUN" if not apply_changes else "APPLIED"
    summary_lines = [
        f"# Agent Model Scan [{action_label}]",
        f"",
        f"**Timestamp**: {report['timestamp']}",
        f"**Applied**: {report['applied']}",
        f"**Proposed**: {report['proposed']}",
        f"",
    ]

    for d in report["decisions"]:
        if d["action"] == "apply":
            summary_lines.append(f"- **{d['agent_name']}**: {d['from']} → {d['to']} (gain={d['gain']}, {d['role_dimension']})")
        elif d["action"] == "propose":
            summary_lines.append(f"- ⚠️ **{d['agent_name']}**: PROPOSE {d['from']} → {d['to']} (gain={d['gain']}, tier-up)")
        else:
            summary_lines.append(f"- **{d['agent_name']}**: no change")

    print("\n".join(summary_lines))
    return 0


if __name__ == "__main__":
    import importlib.util
    sys.exit(main())
