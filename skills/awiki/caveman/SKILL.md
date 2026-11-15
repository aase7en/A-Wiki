---
name: caveman
description: "Compress agent OUTPUT for normal low-risk explanations: lead with the answer, cut preamble/recap/filler, bullets <=3 per section, tables >5 rows become compact artifacts. Style-only — never applies to code, security evidence, test/CI output, diffs, or anything where lossless detail matters."
version: 1.0.0
author: A-Wiki (adapted from community caveman-style skills; style guidance only, no upstream proxy/runtime)
domain: [ai-ops, productivity]
lifecycle_phase: build
category: style
agents: [all]
status: canonical
invocation: auto
invocation_hint: "/Caveman"
triggers:
  - "caveman"
  - "be brief"
  - "less tokens"
  - "shorter answers"
  - "สั้นๆ"
  - "ตอบกระชับ"
  - "พูดมากไป"
---

# Caveman — output style for low-risk communication

Style-only compression of what the agent SAYS. It never changes what the agent
DOES, never shortens inputs it reads, and never edits/summarizes artifacts that
must stay lossless.

## Where it applies

- Everyday explanations, status updates, Q&A, summaries of already-completed work
- Chat replies where the user already saw the tool calls and wants conclusions
- Option A/B recommendations with one-line reasons

## Where it NEVER applies (hard exclusions)

- Code, config, or any file content being written or reviewed
- Security evidence, audit findings, privacy scan results
- Test output, CI logs, error messages, stack traces — quote verbatim or not at all
- Numbers/metrics in measurement or billing contexts
- Anything the user or a downstream consumer re-reads as record

If excluded content must be conveyed, point to it by reference (file path, run
URL, receipt) instead of compressing it.

## The style

1. Answer first. One sentence. Then (only if needed) the reason.
2. No preamble ("I will now…", "Let me…"), no recap of what the user just watched.
3. <=3 bullets per section; break into subsections or emit compact JSON instead.
4. Tables over 5 rows become a compact artifact + 1-3 line summary with the path.
5. Yes/no questions get yes/no + one-line reason. Done.
6. When unsure whether content is "low-risk", do not compress — ask or quote.

Measured intent: ~60-65% output-token reduction on conversational replies
(community-reported range; A/B fixtures per A-Wiki #76 will record our own
numbers with UNKNOWN disclosed where billing data is unavailable).

## Relationship to other entries

- `token-optimization` handles INPUT/context economy (logs, diffs, search
  outputs). This skill handles conversational OUTPUT. Use both; do not
  conflate.
- The user can opt back into full prose per session; this skill never
  overrides an explicit user style request.
