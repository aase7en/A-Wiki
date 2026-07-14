"""Prompt template for batch-generating Thai skill metadata.

Parallel to scripts/batch/prompt_template.py (source ingestion), but emits
JSON for skills-registry.json v2 fields:
    - th_description   (Thai, 2-3 sentences)
    - when_to_use      (Thai trigger, short)
    - examples         ([{scenario, how}, ...]) 1-2 concrete cases
    - process_steps    ([str, ...]) only if the skill has a clear workflow
    - invocation       ("manual" default; "auto" if hook-loaded; "both")
    - invocation_hint  (optional: "/foo", "bash scripts/...")

Used by scripts/skills_registry/batch_thai.py. Output is validated by
scripts/skills_registry/quality_gate_thai.py before being merged into the
registry's .proposed file.

Design principles:
  - One skill per LLM call (single-turn, no chat history).
  - Prompt is bilingual-aware: model may use English technical terms
    (deploy, API, commit, refactor) inline in Thai text — Thai developers
    use these naturally.
  - Output is strict JSON, no markdown fences, no preamble.
"""
from __future__ import annotations

SYSTEM_PROMPT = """You are A-Wiki's Thai skill-metadata generator. You produce Thai-language JSON describing one engineering/AI skill for a dashboard that helps Thai developers understand which skills their AI Agent can invoke.

Output contract (STRICT — quality_gate will REJECT violations):

1. Output is ONE JSON object, nothing else. No markdown fences, no preamble, no commentary. The first character MUST be '{' and the last '}'.

2. Exactly these keys:
   {
     "th_description": "<Thai, 2-3 sentences, 80-400 chars>",
     "when_to_use":    "<Thai trigger phrase, 20-150 chars>",
     "examples":       [{"scenario": "<Thai situation>", "how": "<Thai how to invoke>"}],
     "process_steps":  ["<Thai step 1>", "<Thai step 2>", "..."],   // OPTIONAL — only if this skill has a clear ordered workflow
     "invocation":     "manual"   // "manual" | "auto" | "both" — default "manual"
   }

3. Thai language rules:
   - th_description must be ≥30% Thai characters (Unicode range \\u0E00-\\u0E7F). Use Thai for meaning; keep technical terms (deploy, API, commit, hook, refactor, test, OAuth, CI/CD, MCP) in English where Thai devs use them.
   - Do NOT translate technical terms word-for-word. "deploy" stays "deploy", not "ปรับใช้". "hook" stays "hook".
   - Do NOT mention the skill's own name in th_description (it's redundant on the dashboard).
   - when_to_use = a short trigger: "เมื่อไหร่ใช้" — one phrase.

4. examples: 1 or 2 entries, each with "scenario" (concrete situation in Thai) and "how" (how to invoke: a slash command, a script path, or a one-liner). Be concrete, not abstract.

5. process_steps: include ONLY if the skill has a clear ordered workflow (e.g. lifecycle phases, debugging mantras, TDD red-green-refactor). Each step is a short Thai phrase (5-25 chars). 3-6 steps. If the skill is a one-shot lookup or static reference, OMIT process_steps entirely.

6. invocation: "manual" by default. Use "auto" if you know the skill is hook-loaded at session start (e.g. lifecycle-router, debug-mantra). Use "both" if it runs both ways. When unsure, output "manual".

7. Public-safe: never include real paths (/Users/<name>, C:\\Users\\<name>, API keys, account names, internal codenames). Examples should use generic placeholders.

8. The skill's English name, English description, domain, and lifecycle phase are given in the user message. Use them as context. Do not invent capabilities the skill does not have.
"""


def build_user_message(
    *,
    skill_name: str,
    en_description: str = "",
    domain: str = "",
    lifecycle_phase: str = "",
    category: str = "",
    path_hint: str = "",
) -> str:
    """Build the user message for one skill. Bilingual context is fine."""
    lines = [f"Generate Thai metadata for this A-Wiki skill:"]
    lines.append(f"")
    lines.append(f"skill_name: {skill_name}")
    if en_description:
        lines.append(f"english_description: {en_description}")
    if domain:
        lines.append(f"domain: {domain}")
    if lifecycle_phase:
        lines.append(f"lifecycle_phase: {lifecycle_phase}")
    if category:
        lines.append(f"category: {category}")
    if path_hint:
        lines.append(f"path_hint: {path_hint}")
    lines.append(f"")
    lines.append(f"Emit strict JSON per the contract. No fences, no preamble.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Field-specific: invocation_hint
# ---------------------------------------------------------------------------

INVOCATION_HINT_SYSTEM_PROMPT = """You are A-Wiki's skill-invocation generator. Given a skill's name, English description, file path, and lifecycle phase, you produce ONE short copyable invocation string that a Thai developer would paste into their AI agent to invoke this skill.

Output contract (STRICT):
1. Output is ONE JSON object on a single line: {"invocation_hint": "<string>"}
2. No markdown fences, no preamble. First char '{', last '}'.
3. invocation_hint rules (pick exactly ONE form):
   - "/<name>"               — if the skill is a slash command (most lifecycle skills, A-Wiki core commands, short prompt-style skills). Example: "/debug-mantra"
   - "python <script>.py"    — if the skill is backed by a Python script (path ends in .py). Use the registry's path value.
   - "bash <script>.sh"      — if the skill is backed by a shell script (path ends in .sh).
   - "<bare-name>"           — if the skill is prompt-only and has no command or script. Just the skill name as-is.
4. Keep it ≤ 80 chars. No newlines, no quotes inside.
5. Public-safe: never include /Users/<name>, C:\\Users\\<name>, API keys, or real account names.
6. Do NOT translate — invocation_hint is always in English/code form, even though the dashboard is Thai.
"""

INVOCATION_HINT_RULES_HINT = """Heuristic (use as a guide, not a strict rule):
- Names starting with "a-wiki-" or in {wiki, search, review, spec, plan, build, ship, today, lint, ingest} → "/<name>"
- Names like "debug-mantra", "tdd", "grill-me", "scrutinize", "post-mortem" (short, no spaces, all letters) → "/<name>"
- Paths ending in .py → "python <path>"
- Paths ending in .sh → "bash <path>"
- Otherwise → bare name
"""


def build_invocation_hint_message(
    *,
    skill_name: str,
    en_description: str = "",
    domain: str = "",
    lifecycle_phase: str = "",
    path_hint: str = "",
) -> str:
    """Build a field-specific prompt for invocation_hint only.

    Returns a short user message; pair with INVOCATION_HINT_SYSTEM_PROMPT.
    """
    lines = ["Generate the invocation_hint for this A-Wiki skill:"]
    lines.append("")
    lines.append(f"skill_name: {skill_name}")
    if en_description:
        lines.append(f"english_description: {en_description}")
    if domain:
        lines.append(f"domain: {domain}")
    if lifecycle_phase:
        lines.append(f"lifecycle_phase: {lifecycle_phase}")
    if path_hint:
        lines.append(f"path: {path_hint}")
    lines.append("")
    lines.append(INVOCATION_HINT_RULES_HINT)
    lines.append("Emit strict JSON: {\"invocation_hint\": \"...\"}. One line, no fences.")
    return "\n".join(lines)
