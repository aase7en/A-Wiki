"""
prompt_template.py — Identical prompt across all 3 adapters.

This is the single place that defines what we ask the model to produce for
each raw/ source. Adapters wrap this with provider-specific request shape
but the textual content is the same — keeping output schema portable across
tiers and ensuring `quality_gate.py` checks apply uniformly.
"""
from __future__ import annotations

import hashlib
import re
import sys
import unicodedata
from pathlib import Path

# Import shared domain constants from lib (F8 dedup — was inline tuple)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))
from lib.wiki_domains import VALID_DOMAINS  # noqa: E402

SYSTEM_PROMPT = """You are A-Wiki's source ingestion agent. Your job: read one source document and emit ONE markdown file that summarizes it for a Thai-first technical knowledge base.

Output requirements (strict — file will be REJECTED by hooks if violated):

1. Start with YAML frontmatter, exactly these keys:
   type: source
   title: "<full title from the source>"
   slug: <kebab-case-english-slug>
   date_ingested: <YYYY-MM-DD from user message>
   original_file: raw/<exact filename given in the user message>
   tags: [tag1, tag2, ...]
   domain: <one of: iot | env | ai-tools | pharmacy | it | general | trader>
   routed_via: harness@v1
   tier: <integer 1, 2, or 3 — given in user message>

2. After frontmatter, a body in Thai with these H2 sections in order:
   # <title>
   **ประเภท**: article | paper | video | podcast | book-chapter | documentation | datasheet
   **วันที่**: <publish date or "unknown">
   **ผู้เขียน**: <author or "unknown">

   ## ประเด็นหลัก
   <numbered list, 3-7 items>

   ## ข้อมูลที่น่าสนใจ
   <bulleted list of facts, numbers, quotes>

   ## ข้อโต้แย้งหรือความขัดแย้ง
   <Thai paragraph or "ไม่พบความขัดแย้งกับ wiki ปัจจุบัน">

   ## หน้า Wiki ที่ได้รับการอัปเดต
   <bulleted [[entities/...]] and [[concepts/...]] suggestions; if none, "(none — new domain)">

3. Do NOT wrap the output in triple backticks. Do NOT add commentary before the frontmatter or after the last section. The first three characters MUST be "---".

4. `original_file:` MUST be the exact raw path the user gives you — do not normalize, do not invent.
"""


def build_user_message(
    *,
    raw_path: str,
    raw_text: str,
    slug: str,
    date_ingested: str,
    tier: int,
    domain_hint: str | None = None,
) -> str:
    domain_clause = (
        f"\nDomain hint (use unless source is clearly a different domain): {domain_hint}"
        if domain_hint
        else ""
    )
    return f"""Ingest this source.

raw_path: {raw_path}
slug: {slug}
date_ingested: {date_ingested}
tier: {tier}{domain_clause}

--- BEGIN SOURCE ---
{raw_text}
--- END SOURCE ---

Emit the wiki/sources/{slug}.md file content per the system prompt. First three chars MUST be "---"."""


def read_raw(raw_path: str | Path) -> str:
    """Read a raw/ source file with permissive encoding."""
    p = Path(raw_path)
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="utf-8", errors="replace")


def derive_slug(raw_path: str | Path) -> str:
    """Deterministic kebab-case slug from a raw filename.

    Handles Thai / non-ASCII names by stripping to ASCII; falls back to a
    short hash suffix if the result is empty or too short. This is what
    becomes wiki/sources/<slug>.md.
    """
    stem = Path(raw_path).stem
    text = unicodedata.normalize("NFKD", stem.lower()).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s_]+", "-", text).strip("-")
    if len(text) < 3:
        digest = hashlib.sha1(stem.encode("utf-8")).hexdigest()[:8]
        text = (text + "-" if text else "src-") + digest
    return text[:80]
