#!/usr/bin/env python3
"""Batch-generate Thai skill metadata via LLM.

Reads skills-registry.json, finds skills missing one or more v2 fields
(default: th_description), calls DeepSeek (Tier 1) per skill, validates
each output via quality_gate_thai, and writes skills-registry.json.proposed
for human review before apply.

Usage:
    python scripts/skills_registry/batch_thai.py --estimate --limit 240
    python scripts/skills_registry/batch_thai.py --dry-run --limit 10
    python scripts/skills_registry/batch_thai.py --limit 50 --tier 1
    python scripts/skills_registry/batch_thai.py --limit 240 --resume
    python scripts/skills_registry/batch_thai.py --field process_steps --limit 80

Cost-First Pyramid compliance:
  - --estimate is required before a real run unless --i-know-the-cost is set
  - --max-cost-usd aborts mid-run if cumulative cost exceeds cap
  - quality_gate fail rate > 25% aborts (escalate to Tier 2 / OpenAI batch)

Output: skills-registry.json.proposed (merged with existing entries).
Apply via: python scripts/skills_registry/apply_thai_guide.py --from-proposed

Iron Law #3 (Senior Critic): the .proposed file is the review gate. Nothing
in here writes to skills-registry.json directly.
"""
from __future__ import annotations

import argparse
import configparser
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from drive_secrets import fetch_secret  # noqa: E402

from skills_registry.quality_gate_thai import validate as gate_validate  # noqa: E402
from skills_registry.quality_gate_thai import validate_invocation_hint as gate_validate_hint  # noqa: E402
from skills_registry.prompt_template_thai import (  # noqa: E402
    SYSTEM_PROMPT,
    build_user_message,
    INVOCATION_HINT_SYSTEM_PROMPT,
    build_invocation_hint_message,
)

REGISTRY = REPO_ROOT / "skills-registry.json"
PROPOSED = REPO_ROOT / "skills-registry.json.proposed"
COST_CONF = REPO_ROOT / "wiki" / "context" / "cost-routing.conf"

# Per-tier pricing (USD per million tokens). Read from cost-routing.conf.
# Falls back to seed values if conf is missing.
SEED_PRICING = {
    1: {"model": "deepseek-chat", "endpoint": "https://api.deepseek.com/v1",
        "secret_name": "DEEPSEEK_API_KEY", "in_per_mtok": 0.14, "out_per_mtok": 0.28},
    2: {"model": "gpt-4o-mini", "endpoint": "https://api.openai.com/v1",
        "secret_name": "OPENAI_API_KEY", "in_per_mtok": 0.15, "out_per_mtok": 0.60},
}

# Rough token estimate (chars / 3 for English+Thai mix).
CHARS_PER_TOKEN = 3
# Estimated input size per skill (prompt + skill context).
PROMPT_OVERHEAD_CHARS = 1800  # SYSTEM_PROMPT + user message wrapper
# Estimated output size by field (chars). th_description/full emit ~600;
# invocation_hint emits a tiny one-liner (~50).
EXPECTED_OUTPUT_CHARS = {
    "th_description": 600,
    "process_steps": 600,  # uses the same full prompt + gate
    "invocation_hint": 80,  # {"invocation_hint": "/<name>"} ≈ 40-60 chars
}

FAIL_RATE_ABORT_PCT = 25  # abort if quality_gate fail rate exceeds this


# ---------------------------------------------------------------------------
# Tier config
# ---------------------------------------------------------------------------

def load_tier_config(tier: int) -> dict[str, Any]:
    """Load tier config from cost-routing.conf; fall back to seeds."""
    cfg: dict[str, Any] = dict(SEED_PRICING.get(tier, SEED_PRICING[1]))
    if COST_CONF.exists():
        parser = configparser.ConfigParser()
        parser.read(COST_CONF)
        section = f"tier_{tier}"
        if parser.has_section(section):
            for key in ("model", "endpoint", "secret_name"):
                if parser.has_option(section, key):
                    cfg[key] = parser.get(section, key)
            for key in ("price_input_per_mtok", "price_output_per_mtok"):
                if parser.has_option(section, key):
                    cfg["in_per_mtok" if "input" in key else "out_per_mtok"] = parser.getfloat(section, key)
    return cfg


# ---------------------------------------------------------------------------
# Candidate selection
# ---------------------------------------------------------------------------

def select_candidates(
    skills: list[dict[str, Any]],
    *,
    field: str,
    limit: int,
    domain: str | None,
    resume_set: set[str],
) -> list[dict[str, Any]]:
    """Pick skills missing the target field, capped by limit."""
    out: list[dict[str, Any]] = []
    for s in skills:
        if s.get("status") != "canonical":
            continue
        if s["name"] in resume_set:
            continue
        if domain and domain not in (s.get("domain") or []):
            continue
        # `field=th_description` → missing th_description
        # `field=process_steps` → has th_description but missing process_steps
        if field == "process_steps":
            if not s.get("th_description"):
                continue  # need th first
            if s.get("process_steps"):
                continue
        else:
            if s.get(field):
                continue
        out.append(s)
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------------------
# LLM dispatch
# ---------------------------------------------------------------------------

def call_llm(
    skill: dict[str, Any],
    tier_cfg: dict[str, Any],
    field: str,
) -> tuple[str, int, int, str | None]:
    """One LLM call for one skill.

    Returns (content, tokens_in, tokens_out, error).
    """
    api_key = fetch_secret(tier_cfg["secret_name"])
    if not api_key:
        return "", 0, 0, f"missing secret {tier_cfg['secret_name']}"

    # Field-specific prompt selection.
    if field == "invocation_hint":
        system_prompt = INVOCATION_HINT_SYSTEM_PROMPT
        user_msg = build_invocation_hint_message(
            skill_name=skill["name"],
            en_description=skill.get("description", ""),
            domain=", ".join(skill.get("domain") or []),
            lifecycle_phase=skill.get("lifecycle_phase", ""),
            path_hint=skill.get("path", ""),
        )
        max_tokens = 120  # tiny output
    else:
        system_prompt = SYSTEM_PROMPT
        user_msg = build_user_message(
            skill_name=skill["name"],
            en_description=skill.get("description", ""),
            domain=", ".join(skill.get("domain") or []),
            lifecycle_phase=skill.get("lifecycle_phase", ""),
            category=skill.get("category", ""),
            path_hint=skill.get("path", ""),
        )
        # When targeting process_steps only, narrow the prompt.
        if field == "process_steps":
            user_msg += (
                "\n\nNote: this skill already has th_description and when_to_use. "
                "Focus on producing good process_steps ONLY IF this skill has a clear "
                "ordered workflow. If it does not, still emit valid JSON but you may "
                "omit process_steps. Re-emit th_description/when_to_use/examples as "
                "best you can so the gate passes."
            )
        max_tokens = 800

    payload = {
        "model": tier_cfg["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.3,
        "stream": False,
        "max_tokens": max_tokens,
    }
    url = tier_cfg["endpoint"].rstrip("/") + "/chat/completions"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
    except urllib.error.HTTPError as e:
        err = ""
        try:
            err = e.read().decode("utf-8")[:300]
        except Exception:
            pass
        return "", 0, 0, f"HTTP {e.code}: {err}"
    except urllib.error.URLError as e:
        return "", 0, 0, f"network error: {e}"

    try:
        choice = data["choices"][0]
        content = choice["message"]["content"] or ""
    except (KeyError, IndexError):
        return "", 0, 0, f"bad response shape: {str(data)[:200]}"

    usage = data.get("usage", {})
    return content, int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0)), None


# ---------------------------------------------------------------------------
# .proposed read/write
# ---------------------------------------------------------------------------

def load_proposed() -> dict[str, dict[str, Any]]:
    """Load existing .proposed file (name → field-dict). Empty dict if missing."""
    if not PROPOSED.exists():
        return {}
    try:
        with open(PROPOSED, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_proposed(proposed: dict[str, dict[str, Any]]) -> None:
    """Write .proposed atomically (tmp + rename)."""
    tmp = PROPOSED.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(proposed, f, ensure_ascii=False, indent=2)
    tmp.replace(PROPOSED)


# ---------------------------------------------------------------------------
# Estimate
# ---------------------------------------------------------------------------

def estimate(n_skills: int, tier_cfg: dict[str, Any], field: str = "th_description") -> dict[str, Any]:
    """Project token usage + cost for n skills."""
    in_chars = n_skills * (PROMPT_OVERHEAD_CHARS + 100)  # 100 ≈ skill context
    expected_out = EXPECTED_OUTPUT_CHARS.get(field, 600)
    out_chars = n_skills * expected_out
    in_tok = in_chars / CHARS_PER_TOKEN
    out_tok = out_chars / CHARS_PER_TOKEN
    cost = in_tok / 1_000_000 * tier_cfg["in_per_mtok"] + out_tok / 1_000_000 * tier_cfg["out_per_mtok"]
    return {
        "n_skills": n_skills,
        "field": field,
        "tier_model": tier_cfg["model"],
        "tokens_in_est": int(in_tok),
        "tokens_out_est": int(out_tok),
        "cost_usd_est": round(cost, 4),
        "price_in_per_mtok": tier_cfg["in_per_mtok"],
        "price_out_per_mtok": tier_cfg["out_per_mtok"],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch-generate Thai skill metadata via LLM")
    p.add_argument("--limit", type=int, default=50, help="Max skills to process")
    p.add_argument("--tier", type=int, default=1, choices=[1, 2], help="LLM tier (1=DeepSeek realtime, 2=OpenAI realtime)")
    p.add_argument("--domain", help="Filter by domain (e.g. ai-tools, code, security)")
    p.add_argument("--field", default="th_description", choices=["th_description", "process_steps", "invocation_hint"],
                   help="Which field to fill (th_description is the default)")
    p.add_argument("--estimate", action="store_true", help="Print cost estimate and exit (no API call)")
    p.add_argument("--dry-run", action="store_true", help="Plan + show first 3 prompts, no API call")
    p.add_argument("--resume", action="store_true", help="Skip skills already in .proposed")
    p.add_argument("--max-cost-usd", type=float, default=5.0, help="Abort if cumulative cost exceeds this")
    p.add_argument("--i-know-the-cost", action="store_true",
                   help="Skip the --estimate-first guardrail (ack you've seen the cost)")
    p.add_argument("--sleep", type=float, default=0.3, help="Seconds between API calls (rate-limit cushion)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not REGISTRY.exists():
        print(f"❌ {REGISTRY} not found", file=sys.stderr)
        return 1

    with open(REGISTRY, "r", encoding="utf-8") as f:
        data = json.load(f)
    skills = data.get("skills", [])

    tier_cfg = load_tier_config(args.tier)
    proposed = load_proposed() if args.resume else {}
    resume_set = set(proposed.keys())

    candidates = select_candidates(
        skills, field=args.field, limit=args.limit,
        domain=args.domain, resume_set=resume_set,
    )

    if not candidates:
        print(f"ℹ️  No candidates missing '{args.field}' "
              f"(limit={args.limit}, domain={args.domain or 'any'}, resume={len(resume_set)} skipped)")
        return 0

    est = estimate(len(candidates), tier_cfg, args.field)

    if args.estimate:
        print(json.dumps(est, indent=2, ensure_ascii=False))
        return 0

    if not args.i_know_the_cost and not args.dry_run:
        print("⚠️  Run with --estimate first to see cost. Then re-run with --i-know-the-cost.")
        print(f"    Estimated cost for {len(candidates)} skills: ${est['cost_usd_est']:.4f} "
              f"(model: {tier_cfg['model']}, in={est['tokens_in_est']}tok, out={est['tokens_out_est']}tok)")
        return 1

    print(f"🎯 Tier {args.tier} ({tier_cfg['model']}) — {len(candidates)} candidate(s) for '{args.field}'")
    print(f"   est cost: ${est['cost_usd_est']:.4f} | cap: ${args.max_cost_usd:.2f}")
    if args.dry_run:
        print("\n--- DRY-RUN: first 3 prompts ---")
        for s in candidates[:3]:
            print(f"\n[{s['name']}] ({', '.join(s.get('domain') or [])})")
            if args.field == "invocation_hint":
                msg = build_invocation_hint_message(
                    skill_name=s["name"], en_description=s.get("description", ""),
                    domain=", ".join(s.get("domain") or []),
                    lifecycle_phase=s.get("lifecycle_phase", ""),
                    path_hint=s.get("path", ""),
                )
            else:
                msg = build_user_message(
                    skill_name=s["name"], en_description=s.get("description", ""),
                    domain=", ".join(s.get("domain") or []),
                    lifecycle_phase=s.get("lifecycle_phase", ""),
                    category=s.get("category", ""), path_hint=s.get("path", ""),
                )
            print(msg[:300] + "...")
        print(f"\n(dry-run — would call LLM for {len(candidates)} skills, no API call made)")
        return 0

    # ----- real run -----
    api_key = fetch_secret(tier_cfg["secret_name"])
    if not api_key:
        print(f"❌ secret {tier_cfg['secret_name']} not found in drive/.secrets", file=sys.stderr)
        return 1

    cumulative_cost = 0.0
    passed = 0
    failed = 0
    errors: list[str] = []
    started = datetime.now(timezone.utc).isoformat()

    for i, s in enumerate(candidates, 1):
        content, tok_in, tok_out, err = call_llm(s, tier_cfg, args.field)
        if err:
            failed += 1
            errors.append(f"{s['name']}: {err}")
            print(f"  [{i}/{len(candidates)}] {s['name']} ❌ {err}")
            time.sleep(args.sleep)
            continue

        # Track cost
        call_cost = (tok_in / 1_000_000 * tier_cfg["in_per_mtok"]
                     + tok_out / 1_000_000 * tier_cfg["out_per_mtok"])
        cumulative_cost += call_cost

        # Field-specific validation dispatch.
        if args.field == "invocation_hint":
            ok, reason, parsed = gate_validate_hint(content, skill_name=s["name"])
        else:
            ok, reason, parsed = gate_validate(content, skill_name=s["name"])
        if not ok:
            failed += 1
            errors.append(f"{s['name']}: gate fail — {reason}")
            print(f"  [{i}/{len(candidates)}] {s['name']} ⚠️  gate fail ({reason[:80]})  [${cumulative_cost:.4f}]")
        else:
            # Field-specific: only keep the target field in .proposed
            # (avoids overwriting other fields edited elsewhere).
            if args.field == "process_steps":
                # When targeting process_steps, the LLM may legitimately omit
                # it (skill has no clear workflow). In that case, skip the
                # entry entirely — do NOT write the full dict back, which
                # would clobber existing th_description/when_to_use/examples.
                if "process_steps" in parsed:
                    proposed[s["name"]] = {"process_steps": parsed["process_steps"]}
                else:
                    # Legitimate "no workflow" — count as pass (gate passed)
                    # but don't add to proposed (nothing to apply).
                    passed += 1
                    print(f"  [{i}/{len(candidates)}] {s['name']} ⏭️  no workflow (omitted)  [${cumulative_cost:.4f}]")
                    if i % 5 == 0:
                        save_proposed(proposed)
                    if cumulative_cost > args.max_cost_usd:
                        print(f"\n🛑 Cost cap reached: ${cumulative_cost:.4f} > ${args.max_cost_usd:.2f}")
                        print(f"   {len(candidates) - i} skill(s) not processed. Re-run with --resume to continue.")
                        break
                    if i >= 10 and failed >= 3:
                        fail_pct = failed * 100 // i
                        if fail_pct >= FAIL_RATE_ABORT_PCT:
                            print(f"\n🛑 Fail rate {fail_pct}% (>= {FAIL_RATE_ABORT_PCT}%) after {i} skills — aborting.")
                            break
                    time.sleep(args.sleep)
                    continue
            elif args.field == "invocation_hint" and "invocation_hint" in parsed:
                proposed[s["name"]] = {"invocation_hint": parsed["invocation_hint"]}
            else:
                proposed[s["name"]] = parsed
            passed += 1
            print(f"  [{i}/{len(candidates)}] {s['name']} ✅  [${cumulative_cost:.4f}]")

        # Save progress every 5 skills (resumable)
        if i % 5 == 0:
            save_proposed(proposed)

        if cumulative_cost > args.max_cost_usd:
            print(f"\n🛑 Cost cap reached: ${cumulative_cost:.4f} > ${args.max_cost_usd:.2f}")
            print(f"   {len(candidates) - i} skill(s) not processed. Re-run with --resume to continue.")
            break

        # Abort if fail rate is too high (early warning)
        if i >= 10 and failed >= 3:
            fail_pct = failed * 100 // i
            if fail_pct >= FAIL_RATE_ABORT_PCT:
                print(f"\n🛑 Fail rate {fail_pct}% (>= {FAIL_RATE_ABORT_PCT}%) after {i} skills — aborting.")
                print(f"   Refine SYSTEM_PROMPT or escalate to Tier 2.")
                print(f"   First few errors:")
                for e in errors[:5]:
                    print(f"     - {e}")
                break

        time.sleep(args.sleep)

    # Final save
    save_proposed(proposed)

    print(f"\n{'=' * 60}")
    print(f"📊 Run summary (started {started})")
    print(f"   candidates: {len(candidates)}")
    print(f"   passed:     {passed}")
    print(f"   failed:     {failed}")
    print(f"   cost:       ${cumulative_cost:.4f}")
    print(f"   proposed:   {PROPOSED} ({len(proposed)} total entries)")
    if errors:
        print(f"\n   errors (first 10):")
        for e in errors[:10]:
            print(f"     - {e}")
    print(f"\nNext: review the .proposed file, then:")
    print(f"  python scripts/skills_registry/apply_thai_guide.py --from-proposed --review")
    return 0 if passed > 0 else 2


if __name__ == "__main__":
    sys.exit(main())
