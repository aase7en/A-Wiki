# Hermes Container Recovery Daemon v2.0

> Container monitoring + auto-recovery + Hermes free-model restore for Pi5 Umbrel.
> Runs as a **host systemd `--user` timer** (survives Umbrel app updates).

## Architecture

```
Timer (2 min) ─► Oneshot Service ─► container-recovery-v2.sh
                                        ├── Checks 5 containers (tiered)
                                        ├── docker start if stopped
                                        ├── Deep health (API/sync/channels)
                                        └── docker exec mode-switch.sh if Hermes restarts
```

- **CRITICAL** (2 min): hermes-agent_web_1, hermes-agent_app_proxy_1, bitcoin_app_1, lightning_lnd_1
- **IMPORTANT** (10 min): cloudflared_connector_1
- Daemon lives at: `/home/umbrel/umbrel/app-data/hermes-agent/data/hermes/hermes/`
- State: SQLite + JSON in `recovery/` subdir
- Telegram alerts on recovery events

## Canonical files in repo

```
scripts/hermes/container-recovery/
├── container-recovery-v2.sh          # Main daemon (fixed)
├── containers.conf                   # Container roster (real names)
├── model-state.json                  # Expected freeforall model
├── deploy-to-pi5.sh                  # Deployment script
├── systemd/
│   ├── hermes-container-recovery.service  # systemd unit (__HOST_RECOV_DIR__ placeholder)
│   └── hermes-container-recovery.timer    # 2-min timer
└── recovery/health-checks/
    ├── check-hermes-api.sh           # Port-listening check (via docker exec)
    ├── check-bitcoin-sync.sh         # bitcoin-cli sync status
    └── check-lightning-channels.sh   # lncli channel count
```

## Activation on Pi5 host

```bash
# 1. Add umbrel to docker group (needed for docker start/inspect)
sudo usermod -aG docker umbrel
sudo systemctl restart user@1000

# 2. Set up Telegram env (token from Hermes container)
sudo docker exec hermes-agent_web_1 sh -c \
  'grep -E "TELEGRAM_(BOT_TOKEN|CHAT_ID)" /opt/data/.env /opt/data/.hermes/.env /opt/hermes/.env 2>/dev/null'
# Write the two vars to: /home/umbrel/.../hermes/recovery/telegram.env (chmod 600)

# 3. Install systemd user service
mkdir -p ~/.config/systemd/user
cp /home/umbrel/umbrel/app-data/hermes-agent/data/hermes/hermes/systemd/*.service *.timer ~/.config/systemd/user/
sudo loginctl enable-linger umbrel
systemctl --user daemon-reload
systemctl --user enable --now hermes-container-recovery.timer

# 4. Verify
systemctl --user list-timers | grep hermes
bash /home/umbrel/umbrel/app-data/hermes-agent/data/hermes/hermes/container-recovery-v2.sh
tail -50 /home/umbrel/umbrel/app-data/hermes-agent/data/hermes/hermes/recovery/recovery.log
```

## Fallover test

```bash
# T1: Hermes CLI container restart + model restore
sudo docker stop hermes-agent_web_1
# Wait ≤2 min → auto-restart + mode-switch.sh freeforall → Telegram alert

# T2: Bitcoin restart
sudo docker stop bitcoin_app_1
# Wait ≤2 min → auto-restart

# T3: Hermes API container restart + health check
sudo docker stop hermes-agent_app_proxy_1
# Wait ≤2 min → auto-restart, next cycle runs API health check

# Check state
sudo sqlite3 /home/umbrel/.../hermes/recovery/recovery.db \
  "select timestamp,container,event_type,status from recovery_events order by id desc limit 10;"
```

## Hermes health findings (2026-06-29)

| Container | Status | Restarts | OOM | CLI location |
|-----------|--------|----------|-----|-------------|
| hermes-agent_app_proxy_1 | running | 0 | false | no |
| hermes-agent_web_1 | running | 0 | false | yes (`/opt/hermes/.venv/bin/hermes`) |
| bitcoin_app_1 | running | - | - | - |
| lightning_lnd_1 | running | - | - | - |

**Critical**: `mode-switch.sh` runs via `docker exec hermes-agent_web_1` (not on host) because the Hermes CLI only exists inside the container at `/opt/hermes/.venv/bin/hermes`.

## Risks

- **Memory pressure**: Pi5 8GB uses 4.5G RAM + 3.2G swap → OOM risk long-term.
- **API deep-check**: Best-effort (depends on `ss`/`nc`/`wget` in `hermes-agent_app_proxy_1`). Running-status is the primary signal.
- **Docker group**: Broad access; acceptable for single-user home node.
