---
name: post-mortem
description: Write the canonical engineering record of a fixed bug — root cause, mechanism, fix, validation, and how it slipped through. Enforces IRON LAW #2 via the debug-mantra steps that MUST precede it.
---

# Post-mortem

> ⚠️ **IRON LAW #2 ENFORCEMENT**: A post-mortem MUST NOT be written unless:
> 1. Root cause is identified (not a hypothesis).
> 2. Fix is validated with a failing test that now passes.
> 3. The debug-mantra 4-step process was completed.
>
> If these are not satisfied → REFUSE to draft. List what's missing.

The canonical engineering record of a bug fix. Written **after** debugging lands a real fix, **for** other engineers (and future-you, who will have forgotten everything in 6 months). Code identifiers are welcome here — this is the artifact that lets the next person recover the mental model fast.

## When to invoke

- "/post-mortem"
- "write the post-mortem / postmortem / RCA / root-cause analysis"
- "document this fix" / "write up the root cause" / "close out this bug with a writeup"
- After a debug session has clearly landed a fix, proactively offer to draft one.

## Required inputs — refuse to draft without these

Before writing a single line, confirm all four. If any are missing, list what's missing and stop:

- [ ] **Reliable repro** exists (not "happens sometimes" — a deterministic or high-rate-flake repro the next person can run).
- [ ] **Root cause is known** (the mechanism is identified, not a hypothesis).
- [ ] **Fix is identified** (PR / commit / branch pointer).
- [ ] **Fix is validated** (the original repro now passes; **a failing test exists that proves the fix**).

## Structure

Use these blocks in this order. **Summary, Root cause, Fix, and Validation are mandatory.**

### 1. Summary *(mandatory)*
### 2. Symptom
### 3. Root cause *(mandatory)*
### 4. Why it produced the symptom
### 5. Fix *(mandatory)*
### 6. How it was found
### 7. Why it slipped through
### 8. Validation *(mandatory)*
### 9. Action items / follow-ups

## Tone

Engineer-to-engineer. Code identifiers are first-class. Blameless. No hedging.

## Rules

- **Refuse to draft without all four required inputs.**
- **Never invent root cause, owner, validation runs, or action items.**
- **Never strip code identifiers** in the engineering record.
- **Blameless** — describe gaps and bugs, never people.
- **State validation coverage honestly.**
- **Get sign-off before posting to JIRA.**
