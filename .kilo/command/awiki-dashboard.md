---
description: Start or stop the A-Wiki Live Dashboard (real-time AI monitor on :7790)
---

Manage the A-Wiki Live Dashboard — the real-time monitor that shows the swarm
(models, delegations, hooks, parallel lanes) as you work.

Start it (idempotent — no-op if already running; opens the browser on first start):

!`bash scripts/dashboard-ensure.sh && echo "---" && curl -s localhost:7790/status || echo "(server not reachable yet — retry in 2s)"`

Then open: http://localhost:7790

To stop it later: `bash scripts/dashboard-stop.sh`

The dashboard also auto-starts (a) on folder open in VS Code (works for Kilo/Cline),
and (b) lazily on the first `delegate.sh` swarm delegation — so this command is only
needed if you want it up before any delegation.
