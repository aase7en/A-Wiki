# Plan — Fix & Activate Pi5 Container Recovery Daemon v2.0

> Status: **Finalized** (user authorized "use recommended answers → implement → test → commit/push to main", then went to sleep).
> Owner to execute: an **implementation-capable agent** (the planning agent cannot mutate). Follow steps in order; each chunk is independently committable.

## 0. Goal alignment
`drive/personal/journal/goals.md` is an empty template (no active goals). This work aligns to A-Wiki high-level principles only: **Cost-first** (free model restore), **survives-Umbrel-updates** (host systemd + persistent `/opt/data`), **public-safe** (secrets never committed), **package-when-reusable** (canonical files version-controlled in repo).

## 1. Hermes health verdict (verified on Pi5 this session)
- Real Hermes containers: `hermes-agent_app_proxy_1` (publishes `0.0.0.0:18790` → host) and `hermes-agent_web_1` (CLI + runtime). **No** `hermes-app_1`.
- Both: `status=running`, `restartCount=0`, `OOMKilled=false`. **Hermes is stable, not crashing.**
- `mode-switch.sh` requires `/opt/hermes/.venv/bin/hermes`, which exists **only in `hermes-agent_web_1`** → model-restore MUST `docker exec hermes-agent_web_1 …`.
- Current `check-hermes-api.sh` (`curl localhost:18790/health`) returns a redirect to Umbrel middleware → passes even when Hermes is down. **Weak/misleading.**
- Host memory: 7.9G total, 4.5G used, **3.2G swap used** → pressure (risk noted §9, not a blocker).
- `umbrel` user `uid=1000`, in `sudo` group, **NOT in `docker` group** → raw `docker` denied on host.

## 2. Architecture decision (resolved)
**Option H — host systemd `--user` daemon.** Reason: daemon needs docker + systemd (unavailable inside container), and keeping artifacts in `/opt/data` (persistent) + user systemd **survives Umbrel app updates** (the project requirement). Option C (mount socket into container) was rejected — Umbrel regenerates compose on app update, breaking the mount.

Canonical files live in repo: `scripts/hermes/container-recovery/`. Deployed (copied) to Pi5 persistent host path:
`HOST_RECOV_DIR=/home/umbrel/umbrel/app-data/hermes-agent/data/hermes/hermes`  (== container `/opt/data/hermes`).

## 3. Blocking bug inventory + exact fixes

| # | Bug | Fix |
|---|-----|-----|
| B1 | `BASE_DIR="/opt/data/hermes"` hardcoded (absent on host) | `readonly BASE_DIR="$SCRIPT_DIR"` (SCRIPT_DIR already computed, unused) |
| B2 | reads `/opt/data/.hermes-mode` (absent on host) → mode `unknown` | read mode from co-located `model-state.json`: `jq -r '.mode' "$BASE_DIR/model-state.json"` |
| B3 | `bash "$MODE_SWITCH_SCRIPT"` on host → hermes CLI missing | `docker exec hermes-agent_web_1 bash /opt/data/scripts/hermes/mode-switch.sh freeforall` + readiness poll first |
| B4 | `umbrel` not in `docker` group | `sudo usermod -aG docker umbrel` + restart user manager (`sudo systemctl restart user@1000`) |
| B5 | script mode `0600` (no +x) | `chmod +x`, and unit uses `ExecStart=/bin/bash <path>` for safety |
| B6 | systemd unit `WorkingDirectory`/`ExecStart` point to `/opt/data/hermes` | rewrite to `HOST_RECOV_DIR`; drop `User=` (user service); add `EnvironmentFile=-…/telegram.env` |
| B7 | `containers.conf` 7/10 names are non-installed; `hermes-app_1` doesn't exist | rebuild minimal correct set (§5) from real names |
| B8 | `check-hermes-api.sh` redirect passes always | verify API port listening inside container (§6) |
| B9 | no way to pass Telegram token to host service | extract token from web_1, write gitignored `telegram.env`, reference via `EnvironmentFile` |

## 4. Script edits — `container-recovery-v2.sh` (canonical: `scripts/hermes/container-recovery/container-recovery-v2.sh`)

```
# CONFIGURATION
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly BASE_DIR="$SCRIPT_DIR"                       # was "/opt/data/hermes"   (B1)
readonly HERMES_CLI_CONTAINER="hermes-agent_web_1"     # CLI lives here            (B3)
readonly MODE_SWITCH_IN_CONTAINER="/opt/data/scripts/hermes/mode-switch.sh"
# (LOG/DB/STATE/MODEL_STATE/CONTAINER_CONF/HEALTH_DIR all derive from BASE_DIR — already do)
```

`check_and_restore_hermes_model()` — replace body:
```
local expected_mode
expected_mode=$(jq -r '.mode // "unknown"' "$MODEL_STATE" 2>/dev/null || echo "unknown")   # B2
log INFO "Expected mode: $expected_mode"
if [[ "$expected_mode" != "freeforall" ]]; then return 0; fi

# readiness poll: wait until CLI container can exec mode-switch (max ~60s)        (B3)
for i in $(seq 1 30); do
  if docker exec "$HERMES_CLI_CONTAINER" test -f "$MODE_SWITCH_IN_CONTAINER" 2>/dev/null; then break; fi
  sleep 2
done

if docker exec "$HERMES_CLI_CONTAINER" bash "$MODE_SWITCH_IN_CONTAINER" freeforall >> "$LOG_FILE" 2>&1; then
  log INFO "Hermes model restored to FREE-FOR-ALL"; record_model_restore
  send_alert "Hermes model restored to FREE-FOR-ALL (free models)"
  log_model_event "restored" "freeforall" "freeforall" 1 "mode-switch via docker exec"
else
  log ERROR "mode-switch.sh failed"; log_model_event "restored" "freeforall" "unknown" 0 "exec failed"
fi
```

Model-restore trigger (in `main`): change `if [[ "$container" =~ hermes ]]` to fire only for the CLI container:
```
if [[ "$container" == "$HERMES_CLI_CONTAINER" ]]; then recovered_hermes=true; sleep 5; fi
```
(Keeps one mode-switch per cycle; harmless if proxy restarted alone.)

All other functions (tier scheduling, sqlite, jq state, send_alert, health dispatch) are correct — keep as-is.

## 5. Corrected `containers.conf` (minimal correct set — user choice)
```
# TIER|container_name|priority|description|health_check_script
CRITICAL|hermes-agent_web_1|100|Hermes Agent (CLI+runtime)|
CRITICAL|hermes-agent_app_proxy_1|95|Hermes API (port 18790)|check-hermes-api.sh
CRITICAL|bitcoin_app_1|90|Bitcoin Node|check-bitcoin-sync.sh
CRITICAL|lightning_lnd_1|80|Lightning LND|check-lightning-channels.sh
IMPORTANT|cloudflared_connector_1|70|Cloudflare Tunnel (remote access)|
```
Verified real names (from `docker-compose` + `docker ps`): `bitcoin_app_1`, `lightning_lnd_1`, `hermes-agent_app_proxy_1`, `hermes-agent_web_1`, `cloudflared_connector_1`. **Confirm at impl time via `sudo docker ps --format '{{.Names}}'`** before activating.

## 6. Health-check fixes — `recovery/health-checks/`
- `check-bitcoin-sync.sh`, `check-lightning-channels.sh`: unchanged (already `docker exec bitcoin_app_1` / `lightning_lnd_1`, correct; need docker group).
- `check-hermes-api.sh` — replace redirect-prone curl with a port-listening check **inside** the API container:
```
#!/bin/bash
docker exec hermes-agent_app_proxy_1 sh -c 'command -v ss >/dev/null && ss -ltn | grep -q ":18790" || (command -v nc >/dev/null && nc -z 127.0.0.1 18790)' 2>/dev/null \
  && { echo "Hermes API port listening"; exit 0; } \
  || { echo "Hermes API port NOT listening"; exit 1; }
```
(Impl note: if neither `ss` nor `nc` exists in the image, fall back to `docker exec … wget -T2 -qO- http://127.0.0.1:18790/ >/dev/null` — verify which tool is present first.)

## 7. Corrected systemd unit — `systemd/hermes-container-recovery.service`
```
[Unit]
Description=Hermes Container Recovery Daemon v2.0
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
Environment=PATH=/usr/local/bin:/usr/bin:/bin
WorkingDirectory=__HOST_RECOV_DIR__
EnvironmentFile=-__HOST_RECOV_DIR__/recovery/telegram.env
ExecStart=/bin/bash __HOST_RECOV_DIR__/container-recovery-v2.sh
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hermes-recovery

[Install]
WantedBy=default.target
```
`__HOST_RECOV_DIR__` = `/home/umbrel/umbrel/app-data/hermes-agent/data/hermes/hermes` (substitute at deploy; a `deploy-to-pi5.sh` will sed this from a placeholder, or keep two files: repo template + deployed copy). Timer (`OnBootSec=5min`, `OnUnitActiveSec=2min`, `Persistent=true`) is correct — keep unchanged.

## 8. Host activation runbook (on Pi5, ordered)
1. **Repo on Pi5:** ensure `~/A-Wiki` exists (`git clone https://github.com/aase7en/A-Wiki.git ~/A-Wiki` if absent; else `git pull`). Copy canonical files to host path:
   `cp ~/A-Wiki/scripts/hermes/container-recovery/{container-recovery-v2.sh,containers.conf,model-state.json} $HOST_RECOV_DIR/`
   `cp ~/A-Wiki/scripts/hermes/container-recovery/systemd/*.service *.timer ~/.config/systemd/user/`
   `cp -r ~/A-Wiki/scripts/hermes/container-recovery/recovery/health-checks/* $HOST_RECOV_DIR/recovery/health-checks/`
   `chmod +x $HOST_RECOV_DIR/container-recovery-v2.sh $HOST_RECOV_DIR/recovery/health-checks/*.sh`
2. **Docker group (B4):** `sudo usermod -aG docker umbrel && sudo systemctl restart user@1000` (uid 1000) so `--user` services inherit the group.
3. **Telegram env (B9):** locate token in web_1: `sudo docker exec hermes-agent_web_1 sh -c 'grep -E "TELEGRAM_(BOT_TOKEN|CHAT_ID)" /opt/data/.env /opt/data/.hermes/.env /opt/hermes/.env 2>/dev/null'` → write the two vars into `$HOST_RECOV_DIR/recovery/telegram.env` (chmod 600). **This file is gitignored / never committed.**
4. **Linger + enable:** `sudo loginctl enable-linger umbrel && systemctl --user daemon-reload && systemctl --user enable --now hermes-container-recovery.timer`.
5. **Sanity:** `systemctl --user list-timers | grep hermes`; run once manually `bash $HOST_RECOV_DIR/container-recovery-v2.sh`; `tail -50 $HOST_RECOV_DIR/recovery/recovery.log`; expect `=== Recovery cycle completed ===` and new rows in `recovery.db`.

## 9. Validation — controlled failover test (must pass before done)
- **T1 model-restore path:** `sudo docker stop hermes-agent_web_1` → within ≤2 min daemon `docker start`s it → waits → `docker exec … mode-switch.sh freeforall` → log line `Hermes model restored to FREE-FOR-ALL` + `model_events` row + **Telegram message received**.
- **T2 plain recovery:** `sudo docker stop bitcoin_app_1` → auto-restart ≤2 min; `recovery_events` row `recovered`.
- **T3 deep-check:** `sudo docker stop hermes-agent_app_proxy_1` → restart + `check-hermes-api.sh` re-evaluated next cycle (no false-positive spam).
- **No false alarms:** confirm no `recovery_failed`/`not_found` rows for the 5 monitored containers during 2 idle cycles.
- Queries: `sudo sqlite3 $HOST_RECOV_DIR/recovery/recovery.db "select timestamp,container,event_type,status from recovery_events order by id desc limit 10;"` and same for `model_events`.
- Leave all containers `running` at end.

## 10. Risks & notes
- **Memory pressure** (8GB, 3.2G swap) is the real long-term risk; the daemon masks restarts but not the cause. Out-of-scope follow-up: audit essential apps / schedule bitcoin sync / consider RAM upgrade. Optionally add a swap-pressure alert later.
- **API deep-check** is best-effort (depends on tools in the app_proxy image); running-status is always the primary signal.
- **Docker group** grants broad docker access to `umbrel`; acceptable on a single-user home node. Alternative (sudoers NOPASSWD for `/usr/bin/docker`) would require changing the script to `sudo docker` — not chosen.
- After any `usermod -aG docker`, a **user-manager restart or reboot** is required for `--user` services to see the group (step 2).
- Umbrel app updates regenerate compose but **not** `app-data/*/data/` user files, so `HOST_RECOV_DIR` + user systemd persist (satisfies "survives updates").

## 11. Commit / push (final step)
Public-safe canonical files only (script, conf, health-checks, unit+timer templates, README/runbook, deploy script). **Never** commit `telegram.env` or credentials.
- Commit msg: `feat(hermes): fix + activate Pi5 container recovery daemon v2 (host systemd)`
- Files: `scripts/hermes/container-recovery/**` + a runbook entry under `docs/runbooks/` (e.g. `docs/runbooks/hermes-container-recovery.md`) summarizing §8–§9.
- `git add scripts/hermes/container-recovery docs/runbooks/hermes-container-recovery.md && git commit && git push origin main` (per repo rule: commit directly to main, no branch/PR).

## 12. Open items / assumptions
- Exact Hermes Telegram-token path in web_1 — resolve at impl (step 3); candidates listed.
- Confirm `ss`/`nc`/`wget` availability in `hermes-agent_app_proxy_1` for the API check (step 6 fallback).
- Confirm `jq`/`sqlite3` are present on the Pi5 **host** (used by the daemon). If missing, `sudo apt-get install -y jq sqlite3`.
- SSH to `umbrel@umbrel.local` credentials are session-only; **must not** be written to the repo or any committed file.
