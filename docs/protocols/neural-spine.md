# Neural Spine — Cross-Session Memory + Multi-Agent Coordination

> **Status:** Phase 1 COMPLETE (2026-07-17). 9 chunks, 91 tests, 0 drift.
> **Goal:** Give A-Wiki brain persistent memory across sessions + ability for
> concurrent agents to coordinate without collision.

## What It Adds

| Primitive | File | Purpose |
|-----------|------|---------|
| **atomic_json** | `scripts/lib/atomic_json.py` | Cross-platform file lock + atomic write/update. Foundation for all stateful files. |
| **memory_ledger** | `scripts/lib/memory_ledger.py` | Event-sourced cross-session memory (decision/lesson/failure/outcome/idea). Survives context compaction. |
| **blackboard** | `scripts/lib/blackboard.py` | Async messaging channel between agents (question/answer/@mention/threads). |
| **task_board** | `scripts/lib/task_board.py` | Atomic task claim/release/update. Prevents concurrent-agent collisions. |
| **memory_capture** (hook) | `scripts/hooks/memory_capture.py` | Auto-captures commits as decisions; SessionStart replays ledger. |
| **task_lease_reaper** (hook) | `scripts/hooks/task_lease_reaper.py` | Releases expired task claims so crashed agents don't lock forever. |
| **neural_spine_mcp** | `scripts/lib/neural_spine_mcp.py` | 10 MCP tools so any MCP-aware agent can call the primitives. |

## How It Works (3 Layers)

### Layer 1: Atomicity (atomic_json)
All stateful writes go through file-lock-protected operations:
- `atomic_write()` — temp file + rename (no partial writes)
- `atomic_append_jsonl()` — one JSON line under exclusive lock
- `atomic_update()` — read-modify-write under lock (the claim pattern)
- `file_lock()` — msvcrt on Windows, fcntl on Unix, threading.Lock fallback

**Proven by:** 50-thread concurrent append = exactly 50 lines, all valid JSON.
10-thread concurrent claim = exactly 1 winner.

### Layer 2: Persistence (memory_ledger + blackboard + task_board)
Three append-only JSONL stores in `.tmp/` (gitignored, local-only like
`git-head-backup.jsonl`):

- **memory-ledger.jsonl** — every commit/lesson/failure auto-captured
- **blackboard.jsonl** — inter-agent messages, threaded
- **task-board.json** — atomic task coordination with TTL leases

Each survives:
- Context compaction (lives on disk, not context window)
- Session restart (new MemoryLedger/Blackboard/TaskBoard instance reads same file)
- Concurrent writes (atomic_json ensures no corruption)

### Layer 3: Wiring (hooks + MCP + dashboard)
The primitives are wired into the agent ecosystem three ways:
- **Hooks** (`.claude/settings.json` + `.codex/hooks.json`): memory_capture on
  PostToolUse Bash, replay + reaper on SessionStart
- **MCP server** (`awiki`): 10 tools — memory_recall/remember, bb_post/read/reply,
  task_add/claim/release/list/update
- **Dashboard** (`/api/bb` GET + POST): browser-renderable agent chat

## Verified End-to-End (3 Scenarios)

### ✅ Scenario 1: Memory Continuity
```
session A: commit "feat(x): implement authentication module"
         → memory_capture hook fires → ledger entry {type:decision}
session A: Stop → ledger entry {type:outcome}
session B (NEW): SessionStart → replay shows both entries
  → "session A decision visible to B? True"
  → "session A outcome visible to B?  True"
```

### ✅ Scenario 2: Concurrent Multi-Agent (no collision)
```
3 tasks on board. Claude + Codex race to claim TB26CAD simultaneously:
  → codex wins, claude loses (atomic lock held)
  → final state: each task has exactly 1 claimant
  → no collision, no corruption
```

### ✅ Scenario 3: Agent Chat (question → answer thread)
```
claude posts question → codex replies (different process simulation)
  → thread preserved across Blackboard instances
  → codex inbox shows 2 messages (Q + A) cross-session
```

## How to Use

### As an agent (automatic — nothing to do)
- Commit anything → decision auto-captured
- Open new session → recent decisions/outcomes auto-replayed
- Tasks claimed elsewhere → you can't re-claim (atomic lock)
- Your claim expires if you crash (TTL reaper releases it)

### Via MCP tools (for explicit calls)
```python
# Remember something
memory_remember(type="lesson", summary="always test concurrent access first")

# Recall past context
memory_recall(query="authentication")

# Ask another agent
bb_post(frm="claude", to="codex", body="can you review PR #42?", type="question")

# Read your inbox
bb_read(to_filter="claude")

# Decompose a goal into shared tasks
task_add(goal="refactor module X", files=["scripts/x.py"])
task_claim(task_id="T...", claimant="claude")
```

### Via dashboard (for humans)
```
GET  http://localhost:7790/api/bb?to_filter=codex   — see codex's inbox
POST http://localhost:7790/api/bb                    — post a message
```

## Privacy (Iron Law #6)
- All Neural Spine files live in `.tmp/` (gitignored, local-only)
- Ledger writer redacts obvious secrets (sk-, AIza, Bearer, generic tokens)
  before persisting — commit messages with stray keys cannot leak
- No secrets cross the MCP boundary in either direction

## Test Coverage
- `test_atomic_json.py` — 8 tests (incl. concurrent proof)
- `test_memory_ledger.py` — 12 tests (incl. cross-session recreation)
- `test_memory_capture.py` — 12 tests (incl. secret redaction)
- `test_blackboard.py` — 11 tests (incl. 50-message concurrent post)
- `test_task_board.py` — 16 tests (incl. 20-agent concurrent claim = 1 winner)
- `test_task_lease_reaper.py` — 8 tests (incl. corrupt-board graceful handling)
- `test_neural_spine_mcp.py` — 8 tests (full lifecycle via MCP tools)
- **Total: 91 tests, all GREEN**

## Phase 2 (Future — separate plan)
With these 2 primitives in place, the remaining 4 user capabilities become
thin skills on top:
- **Idea Distiller** = Stop hook + scan ledger for failure/outcome patterns
- **Goal Loop** = `/goal '<obj>'` → decompose → tasks on board → claim each →
  verify → retry → ship (checkpoint in task-board survives restart)
- **Failure→Skill** = count failure patterns, auto-invoke skill-creator
- **Multi-agent research** = Goal Loop where one task = external research,
  result written as wiki/sources, consumed by next task
