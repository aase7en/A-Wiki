# Model Routing Verification

- generated_at: 2026-06-12 01:42:53 +07
- repo: A-Wiki
- PASS count: 1/3
- threshold: FAIL

| Agent | Result | Evidence |
|---|---|---|
| claude | FAIL | You've hit your session limit · resets 5:30am (Asia/Bangkok) |
| codex | PASS | Reading additional input from stdin... 2026-06-11T18:42:05.960485Z ERROR codex_core::session::session: failed to load skill /Users/aase7en/Desktop/A-Wiki/skills/anthropic-skills/cl |
| gemini | FAIL | Warning: Basic terminal detected (TERM=dumb). Visual rendering will be limited. For the best experience, use a terminal emulator with truecolor support. Warning: 256-color support  |
