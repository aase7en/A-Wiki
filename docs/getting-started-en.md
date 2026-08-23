# Getting Started — A-Wiki Second Brain (English Quick Guide)

> Full Thai guide: `docs/getting-started.md` · Review workflow: `docs/runbooks/review-bus.md`

**The only rule: type what you want to happen.** Two entry points — `/A <objective>` for everything, 12 domain buttons for your own work.

## Install
```bash
git clone https://github.com/aase7en/A-Wiki.git && cd A-Wiki
bash scripts/setup-local.sh          # full brain, once per machine
# OR CLI only:
pip install git+https://github.com/aase7en/A-Wiki.git && awiki status
```

## Daily use
- `/A build a shop website` → routed automatically (trigger → description → full 7-phase spine: think → it asks YOU ≥3 questions → council review → implement → debug loop → review bus → READY)
- You only ever: answer questions + decide where asked
- Search the brain: `awiki search "..."` · status: `awiki status` · health: `awiki doctor`

## Adopt another repo
```bash
awiki adopt /path/to/any/repo        # brain gates + MCP + claims, one command
```

## Unlimited skills (you stay the critic)
```bash
awiki skill list                     # queued proposals
awiki skill scout "excel formula repair"   # search GitHub for a gap
awiki skill eval <id> && awiki skill approve <id>   # auto-tested, one button
```

## What runs underneath (no setup needed)
Memory auto-records every session (secret-redacted, cross-device) · 30 hooks guard raw/ secrets/registry/claims on every provider · CI runs 3,400+ tests + privacy scan on every push · nightly synthesis distills the day at 03:00.
