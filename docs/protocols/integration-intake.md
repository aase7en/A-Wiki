# Integration Intake Protocol

> Normative gate for every EXTERNAL repo/tool/module entering A-Wiki
> (kernel contract §7 — `config/awiki.yaml → integration_registry.classification_gate`).
> For changes to A-Wiki's OWN brain capabilities use `brain-improvement-gate.md` instead;
> this protocol governs what comes IN from outside.
>
> Rule: **no integration before a decision record.** Registry entries without a
> classification decision are contract violations (`validate_integrations.py` enforces
> the registry shape; this checklist governs the decision itself).

## Classification vocabulary

```text
CORE      foundation of A-Wiki itself — remove and the system breaks
MODULE    optional add-on, default-off, lazy — e.g. an external MCP
PATTERN   adopt the principle/algorithm, not the framework
REFERENCE keep for study, no integration
REJECT    redundant / heavy / incompatible
```

Combinations are allowed within a single entry only when both apply honestly
(e.g. `MODULE + PATTERN`). `REJECT` never combines with another class.

## Intake checklist (answer ALL before integrating)

1. What problem does this repo solve, in one paragraph?
2. What % of it overlaps with what A-Wiki already has? (name the duplicates)
3. Full framework needed, or just a pattern?
4. Does it require running a service/daemon? Which resources?
5. How many MCP tools / context tokens does it add when active?
6. New dependencies (languages, runtimes, versions)? Windows/macOS/Linux parity?
7. Privacy implications — can private/project data flow to it? Under what trust level?
8. Security implications — supply chain, permissions, network egress?
9. Maintenance burden — who updates it when upstream moves?
10. Portability across the supported agent set (capability matrix)?
11. Measurable benefit — name at least one metric it improves (D-CTX-011)?
12. Storage contract — durable repo / private drive / local regenerable cache?
13. Classification decision: CORE / MODULE / PATTERN / REFERENCE / REJECT.

## Decision record

Record the outcome as an entry in `config/integrations.yaml` (schema
`awiki-integrations/v1`) plus, for non-trivial decisions, an ADR under
`decisions/`. The registry's `reference:` field must point at the
authoritative plan/doc (validator enforces existence).

## Hard intake rules

- External modules enter `default: false` + `lazy: true` — always.
- Cache-type storage is `commit: false` — always (runtime never churns git).
- No vendoring upstream sources into the kernel to "make it work".
- No secret/API-key material in the registry; trust constraints are declarative.
- Promotion to default-on requires an A-Wiki-owned benchmark (D-CTX-011), not
  upstream marketing claims.
- The A-Wiki wiki knowledge graph stays separate from any project code graph.
