# Prompt Placement Header — Universal Cross-Agent Protocol

Status: binding for A-Wiki-managed agents and bootstrapped project repos
Purpose: eliminate ambiguity about where a generated prompt/instruction must be placed.

## When this protocol applies

Use this header whenever an agent gives the user a prompt, continuation packet,
goal text, steer instruction, subgoal, CLI command sequence, or UI action that is
intended to be pasted or executed in another AI-agent/session surface.

Ordinary explanatory answers that are not meant to be pasted elsewhere do not
need the header.

## Required header

```text
PLACEMENT: <exact destination>
MODE: <one canonical mode>
PURPOSE: <one-line purpose>
REPLACE GOAL?: YES/NO
APPEND TO GOAL?: YES/NO
INTERRUPT CURRENT WORK?: YES/NO
SUBGOAL/QUEUE?: YES/NO
WHEN TO SEND: <timing / gate>
```

If CLI/UI action is intended instead of a pasted prompt, state that explicitly
in PLACEMENT and MODE.

## Canonical modes

### GOAL — REPLACE ALL
Use when the new text becomes the entire durable Goal.
Do not imply durable project state resets unless explicitly intended.

### GOAL — APPEND
Use when the current Goal remains authoritative and the new text is an additive
durable requirement.

### CHAT — SUBGOAL / QUEUE
Use when the instruction should enter chat as follow-up work after the current
goal/lane reaches the appropriate gate.

### CHAT — STEER NOW
Use when the instruction must change the direction of work that is currently
running.

### CHAT — NORMAL
Use for a fresh-session continuation or bounded instruction that should be sent
as a normal chat message without steering or replacing the Goal.

### CLI / TERMINAL
Use when commands belong in a terminal/CLI rather than an AI chat.
State the exact shell/app and whether this is a human security/trust action or
ordinary automation.

### UI ACTION
Use when the user must click/select/configure something in a graphical
interface. Do not wrap UI actions in a fake prompt.

## Selection rule

Choose exactly one primary placement/mode.
Do not tell the user only "paste this" without naming the destination.

If multiple stages are required, split them into separate labeled blocks in
execution order.

If a prior prompt is superseded, explicitly state:

`SUPERSEDES: <prior prompt/goal>`

and whether the prior text should be removed, retained, or ignored.

## Safety / continuity

Prompt placement never grants mutation authority.
Changing Goal text does not erase durable Git/task/claim/runtime state.
New session does not mean new task.
Steer does not authorize bypassing claims, reviews, secret gates, or
destructive-operation gates.
Repository/runtime evidence outranks stale prompt text.

## Standard examples

```text
PLACEMENT: Codex Desktop → Project ENV → Goal
MODE: GOAL — REPLACE ALL
PURPOSE: replace the old marathon goal with consolidated V2
REPLACE GOAL?: YES
APPEND TO GOAL?: NO
INTERRUPT CURRENT WORK?: NO
SUBGOAL/QUEUE?: NO
WHEN TO SEND: before starting the next run
```

```text
PLACEMENT: ENV Luna current chat
MODE: CHAT — STEER NOW
PURPOSE: add a newly discovered safety constraint to active implementation
REPLACE GOAL?: NO
APPEND TO GOAL?: NO
INTERRUPT CURRENT WORK?: YES
SUBGOAL/QUEUE?: NO
WHEN TO SEND: now, while the affected lane is active
```

```text
PLACEMENT: A-Sunday Conductor Luna chat
MODE: CHAT — SUBGOAL / QUEUE
PURPOSE: perform follow-up cleanup after the current merge/post-main gate
REPLACE GOAL?: NO
APPEND TO GOAL?: NO
INTERRUPT CURRENT WORK?: NO
SUBGOAL/QUEUE?: YES
WHEN TO SEND: after the current accepted lane reaches post-main
```

## Cross-agent requirement

Every A-Wiki-managed agent should preserve these labels when handing prompts to
another model, IDE, agent, or user-operated surface. Agents may translate prose
values into the user's language, but placement semantics must remain explicit.
