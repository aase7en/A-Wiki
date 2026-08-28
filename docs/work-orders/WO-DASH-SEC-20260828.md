# WO-DASH-SEC-20260828 — A-Wiki Live network/write-surface hardening

## Status

CLAIMED — owner: `ChatGPT-GPT-5.6-Sol`
Branch: `fix/wo-dash-sec-20260828-loopback`

## Goal

Make A-Wiki Live safe-by-default for a local desktop workflow without breaking its existing dashboard UX or read-only APIs.

## Verified incident

On 2026-08-28 the logged-in Windows machine started A-Wiki Live through `Startup/A-wikilive.bat`. The process listened on `0.0.0.0:7790`; `/api/admin/status` reported `password_set=false`; server POST dispatch had no global authentication gate; CORS allowed `*`.

This is a local-network/write-surface exposure, not an observed exploitation incident.

## Invariants

- Default server bind is loopback only.
- Remote/LAN bind is rejected until an authenticated remote transport exists.
- Same-origin dashboard usage keeps working.
- Existing `AWIKI_DASHBOARD_ALLOW_RUN=1` command-execution gate remains fail-closed.
- No secrets or private machine paths are committed.
- A-Wiki remains brain/knowledge authority; this work does not create runtime authority that belongs to A-Conductor.
## Micro-steps

| ID | Goal | Status | Verification |
|---|---|---|---|
| DASH-SEC-0 | Recover live startup/network state | VERIFIED | process chain, listener, API status, repo code |
| DASH-SEC-1 | Default loopback bind; reject remote/LAN | VERIFIED | RED 4/4 -> focused green; remote bind fails closed |
| DASH-SEC-2 | Reconcile CORS/CSRF + state-changing GET semantics | VERIFIED | evil Origin 403; state unchanged; 10x repeat stable |
| DASH-SEC-3 | Dashboard regression + reproducible bundle | VERIFIED (pre-PR) | 253 pytest; npm ci/build; 256.0 KB bundle |
| DASH-SEC-4 | Report, defect memory, PR, CI, re-audit | IN_PROGRESS | regression tests are Tier-1 executable memory; PR/CI next |

## Root-cause notes

The current `ThreadingHTTPServer(("0.0.0.0", PORT), Handler)` contradicts the product's localhost-oriented operator surface. `dashboard-ensure.sh` probes `127.0.0.1`, documentation prints localhost URLs, and A-Conductor/Serena contracts already treat localhost as the secure default.

Admin password endpoints currently authenticate only the `/api/admin/auth` call; they are not middleware protecting the other POST routes. Therefore password presence must not be treated as write authorization until a real authorization contract is implemented.

## Acceptance

1. Fresh default startup cannot listen beyond loopback.
2. Non-loopback host configuration fails closed even if the legacy remote opt-in variable is set.
3. Tests prove the network contract without relying on prose.
4. Existing dashboard autostart tests and relevant HTTP/API tests remain green.
5. Privacy/security checks report no new findings.
6. Final PR is independently reviewed at its exact head SHA before merge.

## Next safe action

Complete exact-SHA independent security review, then merge only after required gates and authorization are satisfied; rebuild/restart and verify the live listener afterward.

## Checkpoint — 2026-08-28 pre-PR

Verified root causes and repairs:

- Server bound to all interfaces while its operator model and documentation were localhost-oriented. Default is now loopback-only; non-loopback is rejected until authenticated remote serving exists.
- Wildcard CORS plus state-changing routes created a browser cross-origin risk. Browser POST/OPTIONS now accept only the dashboard's loopback origin and port; CLI requests without `Origin` remain supported.
- `GET /clear` and `GET /api/fixes/open` mutated local state. Both are POST-only and the shipped UI source uses POST.
- Windows can reset a rejected POST connection when unread body bytes remain. The reject path drains a bounded body before returning deterministic HTTP 403. Adversarial/local HTTP pair passed 10 consecutive repetitions.
- Dashboard package lock was stale at v8 while the manifest was v20 and included Playwright; `npm ci` failed. Lockfile was refreshed from the existing manifest; `npm ci` now passes.

Executable defect prevention: `tests/test_dashboard_security.py` pins loopback-only binding, exact local origin/port, cross-origin no-mutation, POST-only state changes, local CLI compatibility and package manifest/lock agreement.

Pre-PR evidence:

- dashboard security + autostart focused: 16 passed
- dashboard UI/API regression bundle: 253 passed
- security HTTP adversarial/local pair: 10 repetitions, 20/20 passed
- `npm ci`: pass, 0 vulnerabilities reported by npm audit step
- `npm run precheck` + `npm run size`: pass, bundle 256.0 KB (budget 280 KB)
- privacy: no personal data detected
- repository security scan: 6,310 tracked files, 51 baseline findings, 0 new
- `gen-index --check`: pass
- `git diff --check`: pass

Current live service note: the already-running dashboard process was started from the pre-fix main checkout. Do not treat the live listener as remediated until this PR is merged, main is refreshed, the local bundle is rebuilt, and the service is restarted/verified on loopback.

Next safe action: commit/push the bounded security slice, open a draft PR, inspect remote diff and CI, perform exact-SHA independent security re-review, then merge only after all gates pass and verify the restarted local service.


## Checkpoint — 2026-08-28 exact-SHA re-audit expansion

Review of PR #31 at `999bb7890e8581f8992da02c1c5e57c2293dd1b7` found two additional pre-existing upload defects in the same write surface:

- multipart `filename` was trusted directly, so `../escape.txt` could write outside `UPLOAD_DIR`;
- the handler read the declared request body into memory with no upload-size ceiling;
- happy-path verification also found multipart framing CRLF was being persisted into uploaded file bytes.

TDD evidence: traversal and oversize tests failed before the upload patch. The final handler rejects path components/NUL/overlong names, verifies resolved containment under `UPLOAD_DIR`, caps uploads at 10 MiB before body read, requires a boundary, and removes only the multipart separator CRLF.

Post-fix evidence:

- focused dashboard security: 17 passed;
- dashboard security/autostart/UI/API regression bundle: 246 passed;
- repository security scan: 6,312 tracked files, 51 baseline findings, 0 new;
- privacy: clean;
- `gen-index --check`: pass;
- `npm ci`: pass, 0 vulnerabilities reported;
- `npm run precheck` + `npm run size`: pass, bundle 256.0 KB;
- `git diff --check`: pass.

The PR head must change after this checkpoint. Any previous CI/review on `999bb789...` becomes stale for merge authorization. Next: commit/push, update Loop-Evidence to the new exact SHA, rerun CI, then obtain an independent security review pinned to that SHA.
