"""
router.py — Core engine: pick tier, build IngestRequests, dispatch to adapter.

Pure functions where possible; side-effects isolated to dispatch().
Called from route.py (CLI) and mcp_tools.py (MCP).
"""
from __future__ import annotations

import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "batch"))

from adapters import IngestRequest  # noqa: E402
from config import (  # noqa: E402
    get_default,
    get_tier_config,
    load_conf,
)
from prompt_template import derive_slug  # noqa: E402
from state import add_batch, make_local_id  # noqa: E402

RAW_DIR = REPO_ROOT / "raw"
SOURCES_DIR = REPO_ROOT / "wiki" / "sources"


def _is_ingested(slug: str) -> bool:
    """True if wiki/sources/<slug>.md already exists (flat layout)."""
    return (SOURCES_DIR / f"{slug}.md").is_file()


def discover_backlog(
    *,
    domain_hint: str | None = None,
    limit: int | None = None,
    slugs: list[str] | None = None,
    file: str | None = None,
) -> list[Path]:
    """Scan raw/ for files not yet under wiki/sources/<slug>.md.

    `slugs` restricts to specific derived slugs. `file` overrides with one
    explicit raw path. Uses prompt_template.derive_slug() for consistency
    with what build_requests() / write_results() will use later.
    """
    if file:
        p = Path(file)
        if not p.is_absolute():
            p = REPO_ROOT / p
        if not p.is_file():
            raise FileNotFoundError(f"raw file not found: {file}")
        return [p]

    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"raw/ symlink not set up — run scripts/setup-cloud-link.sh first ({RAW_DIR})"
        )

    found: list[Path] = []
    for p in sorted(RAW_DIR.glob("*.md")):
        slug = derive_slug(p)
        if slugs and slug not in slugs:
            continue
        if _is_ingested(slug):
            continue
        found.append(p)
        if limit and len(found) >= limit:
            break
    return found


def select_tier(
    backlog: list[Path],
    *,
    cli_tier: int | None = None,
    cli_backend: str | None = None,
    conf=None,
    requests: list[IngestRequest] | None = None,
) -> tuple[int, str]:
    """Tier selection per plan §Backend selection logic.

    Order: CLI > ENV > complexity_classifier (Tier 0 gate) > backlog-size
    heuristic > config default.

    Returns (tier, reason) — reason is logged so the user can audit *why*
    a tier was picked (especially Tier 0 for trivial work or Tier 2 for
    large backlogs).
    """
    from config import resolve_tier

    if cli_tier is not None or cli_backend is not None:
        return resolve_tier(cli_tier=cli_tier, cli_backend=cli_backend, conf=conf), "cli override"

    import os
    env_tier = os.environ.get("A_WIKI_ROUTE_TIER")
    env_backend = os.environ.get("A_WIKI_BACKEND")
    if env_tier or env_backend:
        return resolve_tier(conf=conf), f"env override ({env_tier or env_backend})"

    if conf is None:
        conf = load_conf()

    # Tier 0 gate — only when classifier says trivial AND tier_0 is configured.
    if requests and conf.has_section("tier_0"):
        from complexity_classifier import is_trivial
        trivial, reason = is_trivial(requests, conf=conf)
        if trivial:
            return 0, f"trivial: {reason}"

    threshold = int(get_default(conf, "escalation_threshold_files"))
    if len(backlog) > threshold:
        return 2, f"backlog {len(backlog)} > {threshold} → batch tier"
    default = int(get_default(conf, "ingest_tier"))
    return default, f"default tier {default}"


def build_requests(backlog: list[Path], tier: int, *, domain_hint: str | None = None) -> list[IngestRequest]:
    today = date.today().isoformat()
    base_id = make_local_id("req")
    out: list[IngestRequest] = []
    for i, p in enumerate(backlog):
        out.append(
            IngestRequest(
                raw_path=f"raw/{p.name}",
                slug=derive_slug(p),
                custom_id=f"{base_id}-{i:04d}",
                date_ingested=today,
                tier=tier,
                domain_hint=domain_hint,
            )
        )
    return out


def estimate_cost(requests: list[IngestRequest], tier: int, conf=None) -> dict[str, Any]:
    """Rough cost estimate per tier — input tokens from raw file sizes (≈ chars/4)."""
    if conf is None:
        conf = load_conf()
    tier_cfg = get_tier_config(conf, tier)
    input_chars = 0
    for req in requests:
        try:
            input_chars += (REPO_ROOT / req.raw_path).stat().st_size
        except OSError:
            pass
    input_tokens = input_chars // 4  # crude proxy
    output_tokens_est = len(requests) * 1500  # ~1.5K tokens per summary
    in_cost = input_tokens / 1_000_000 * tier_cfg.get("price_input_per_mtok", 0.0)
    out_cost = output_tokens_est / 1_000_000 * tier_cfg.get("price_output_per_mtok", 0.0)
    return {
        "tier": tier,
        "provider": tier_cfg.get("provider"),
        "model": tier_cfg.get("model"),
        "mode": tier_cfg.get("mode"),
        "n_files": len(requests),
        "est_input_tokens": input_tokens,
        "est_output_tokens": output_tokens_est,
        "est_input_usd": round(in_cost, 4),
        "est_output_usd": round(out_cost, 4),
        "est_total_usd": round(in_cost + out_cost, 4),
    }


def get_adapter(tier: int, conf=None):
    if conf is None:
        conf = load_conf()
    tier_cfg = get_tier_config(conf, tier)
    if tier == 0:
        from adapters.openrouter_free import OpenRouterFreeAdapter
        return OpenRouterFreeAdapter(tier_cfg)
    if tier == 1:
        from adapters.deepseek import DeepSeekAdapter
        return DeepSeekAdapter(tier_cfg)
    if tier == 2:
        from adapters.openai_batch import OpenAIBatchAdapter
        return OpenAIBatchAdapter(tier_cfg)
    if tier == 3:
        from adapters.anthropic_batch import AnthropicBatchAdapter
        return AnthropicBatchAdapter(tier_cfg)
    raise ValueError(f"Unknown tier: {tier}")


def dispatch(requests: list[IngestRequest], tier: int) -> dict[str, Any]:
    """Run adapter.submit(). For tier 1 returns realtime results; for 2/3 returns batch_id."""
    adapter = get_adapter(tier)
    submitted = adapter.submit(requests)
    if submitted.get("mode") == "realtime":
        return submitted
    # Batch — persist state so poll/collect can resume.
    batch_id = submitted["batch_id"]
    add_batch(
        batch_id=batch_id,
        backend=adapter.name,
        tier=tier,
        files=[{"slug": r.slug, "raw_path": r.raw_path, "custom_id": r.custom_id} for r in requests],
        input_path=submitted.get("input_path"),
    )
    return submitted
