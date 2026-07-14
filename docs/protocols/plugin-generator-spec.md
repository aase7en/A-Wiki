# Plugin Generator Spec — adding a new agent to A-Wiki's skill system

> **Part of**: [USA-1 Universal Skill Architecture](../architecture/universal-skill-architecture.md) §3.
> **ADR**: [0008](../../decisions/0008-universal-skill-architecture.md).
> **Binding**: every current and future agent (Codex, Claude Code, Antigravity,
> ZCode, Hermes, Windsurf, OpenClaw, Kilo, Cline, + future).

This is the contract for the **plugin generator** layer — the mechanism that
lets a new agent be added to A-Wiki's skill system in **3 steps, ~44 lines**,
without touching any existing agent's surface.

---

## The contract

Every generator is a Python module at
`scripts/skills_registry/generators/gen_<agent>.py` exposing two names:

```python
filename = "<agent>.<ext>"   # the surface file the orchestrator writes

def render(registry: Registry) -> str:
    """Return the agent-specific surface as a string (JSON / JSONC / Markdown).

    MUST use registry.canonical_for_agent('<agent>') — never hardcode skill
    paths. The registry is the single source of truth (Iron Law #9).
    """
```

That's it. The orchestrator (`scripts/regen-skill-surfaces.py`) imports every
generator module, calls `render(registry)` on each, and writes the result to
`scripts/skills_registry/generated/<filename>`.

---

## The 3-step plugin workflow

To register a new agent (call it `acme`):

### Step 1 — create the generator

Copy the template
([`_TEMPLATE_gen_agent.py`](../../scripts/skills_registry/generators/_TEMPLATE_gen_agent.py))
to `scripts/skills_registry/generators/gen_acme.py`, then edit:

1. The docstring (agent name + how it discovers skills).
2. `filename` — e.g. `"acme.skills-paths.json"`.
3. The agent name passed to `registry.canonical_for_agent("acme")`.
4. The shape of the emitted payload — match what the agent's config expects
   (most agents scan a list of dirs; some want a manifest; AGENTS.md wants
   Markdown).

### Step 2 — register in `GENERATORS`

In `scripts/regen-skill-surfaces.py`:

```python
from skills_registry.generators import (  # noqa: E402
    ...
    gen_acme,        # ← add import
)

GENERATORS = {
    ...
    gen_acme.filename: gen_acme,   # ← add one line
}
```

### Step 3 — wire the linker + Drive rule

In `scripts/link-agent-configs.sh`, add `acme` to the agent list so the
linker creates the agent's skill dir + Drive `.~acme/` skeleton (see USA-1 §4).

Then run:

```bash
python scripts/regen-skill-surfaces.py        # regenerate all surfaces
python scripts/regen-skill-surfaces.py --check # verify no drift
```

The new agent now sees the same canonical skill set as every other agent.

---

## Generator patterns (when to use which)

| Pattern | Use when | Example |
|---|---|---|
| **Category-dirs** | agent scans dir trees for `SKILL.md` | kilo, cline, antigravity, codex, windsurf, openclaw |
| **Manifest** | agent needs explicit name→path mapping (e.g. to build symlinks) | zcode |
| **Full skill JSON** | agent wants the entire registry projection (paths + metadata) | hermes (`lifecycle-config.json`) |
| **Markdown fragment** | agent reads rules/docs (spliced into AGENTS.md or a config) | agents_md (`skills-index.md`) |

Pick the simplest pattern that satisfies the agent's discovery mechanism.

---

## Validation gates (mandatory before merge)

1. `python scripts/regen-skill-surfaces.py --validate` — registry schema valid.
2. `python scripts/regen-skill-surfaces.py` — surfaces regenerate without error.
3. `python scripts/regen-skill-surfaces.py --check` — no drift (CI mode).
4. Manually inspect the generated `<agent>.<ext>` file — paths resolve to real
   `SKILL.md` files in the repo.

Rollback if anything fails: `git revert <commit>` (each chunk is one commit).

---

## Rules (binding)

- **Never hardcode skill paths** in a generator. Always go through
  `registry.canonical_for_agent("<agent>")`.
- **Never edit a generated surface by hand.** Edit the registry, then regen.
  The `--check` drift gate enforces this in CI.
- **One agent per generator file.** No mega-generator.
- **Generators are pure functions** of the registry — no I/O, no network, no
  side effects. The orchestrator handles file writes.

---

## Reference

- [`gen_kilo.py`](../../scripts/skills_registry/generators/gen_kilo.py) — canonical 44-line example (category-dirs pattern).
- [`gen_zcode.py`](../../scripts/skills_registry/generators/gen_zcode.py) — manifest pattern (fixes symlink drift).
- [`gen_hermes.py`](../../scripts/skills_registry/generators/gen_hermes.py) — full-JSON pattern.
- [`_TEMPLATE_gen_agent.py`](../../scripts/skills_registry/generators/_TEMPLATE_gen_agent.py) — copy-and-edit starting point.
