---
type: synthesis
title: "Design/Web Capability Hub"
slug: design-web-capability-hub
tags: [capability-lane, design-web, frontend, ui-ux, visual-qa, second-brain]
sources: [dashboard-design-best-practices, good-uiux-practices]
created: 2026-06-12
updated: 2026-06-12
---

# Design/Web Capability Hub

> [verified 2026-06-12] A-Wiki design/web lane routes website, dashboard, UI polish, and visual handoff work without turning design guidance into always-loaded context.

## Route

| Step | Tooling | Done when |
|---|---|---|
| Intent | Local wiki search + existing product docs | Audience, surface, and constraints are known |
| Design | `frontend-design`, `web-artifacts-builder` when complex React state is needed | UI has a clear visual direction and usable controls |
| Verify | `webapp-testing`, Playwright, in-app browser screenshot | Desktop/mobile render without overlap or blank states |
| Handoff | Canva connector only for brand/social/presentation assets | Design export is editable outside the repo |

## Safety Gate

- Do not put private brand analytics, customer screenshots, or unpublished campaign data in tracked wiki pages.
- Keep human-review HTML in `exports/html/`, not as durable source-of-truth.
- Time-sensitive design/tool claims must follow `docs/protocols/knowledge-currency.md`.

## Related

- [[concepts/iot/dashboard-design]]
- [[entities/ai-tools/frontend-slides]]
- [[entities/ai-tools/react-doctor]]
- `docs/runbooks/a-wiki-capability-upgrade-roadmap.md`
