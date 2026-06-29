# UmbrelOS Container Recovery Plan

**Date:** 2026-06-28
**Target:** Raspberry Pi 5 (192.168.1.165) — UmbrelOS Debian 13

## Root Cause

`umbreld` (UmbrelOS app manager) auto-update process stopped Docker containers (lightning, portainer, tailscale) at 13:40 UTC but **failed to restart them**. Because Docker's restart policy (`on-failure` / `unless-stopped`) treats manual stops as intentional (`hasBeenManuallyStopped=true`), containers **never auto-recovered**. This cascaded to BitcoinNode and Hermes Agent due to shared network/infrastructure dependencies.

## Solution: 3-Layer Defense

### Layer 1: Disable Auto-Update (Prevent Cause)

- Umbrel Dashboard → Settings → System → Toggle **Auto-update OFF**
- No CLI needed; this is a one-time Web UI action
- Rationale: prevents `umbreld` from stopping containers for updates

### Layer 2: Docker Group Access

Add `umbrel` to `docker` group so recovery script doesn't need `sudo`:

```bash
sudo usermod -aG docker umbrel
```

Verification: `docker ps` should work without password after re-login.

### Layer 3: Recovery Daemon

#### 3a. Monitor Script

**Path:** `/home/umbrel/scripts/container-health.sh`

```bash
#!/bin/bash
# Container health monitor — restarts stopped critical containers
# Runs every 2 minutes via systemd user timer

CRITICAL_CONTAINERS=(
  hermes-agent_web_1
  hermes-agent_app_proxy_1
  bitcoin_app_1
  bitcoin_app_proxy_1
  bitcoin_tor_1
  bitcoin_i2pd_daemon_1
  lightning_lnd_1
  lightning_app_1
  lightning_app_proxy_1
  auth
  nextcloud_web_1
  portainer_portainer_1
  tailscale_web_1
)

for container in "${CRITICAL_CONTAINERS[@]}"; do
  status=$(docker inspect --format '{{.State.Status}}' "$container" 2>/dev/null)
  if [ "$status" = "exited" ] || [ "$status" = "paused" ] || [ "$status" = "dead" ]; then
    exit_code=$(docker inspect --format '{{.State.ExitCode}}' "$container" 2>/dev/null)
    logger -t container-health "WARN: $container status=$status exit=$exit_code — restarting"
    docker start "$container" 2>&1 | logger -t container-health
  fi
done
```

#### 3b. Systemd User Service

**Path:** `/home/umbrel/.config/systemd/user/container-health.service`

```ini
[Unit]
Description=Container Health Monitor

[Service]
Type=oneshot
ExecStart=/home/umbrel/scripts/container-health.sh
```

#### 3c. Systemd User Timer

**Path:** `/home/umbrel/.config/systemd/user/container-health.timer`

```ini
[Unit]
Description=Run Container Health Monitor every 2 minutes

[Timer]
OnBootSec=30s
OnUnitActiveSec=2min

[Install]
WantedBy=timers.target
```

#### 3d. Enable Timer

```bash
systemctl --user daemon-reload
systemctl --user enable --now container-health.timer
```

## Verification

1. **Test recovery:** `docker stop hermes-agent_web_1` → wait ≤2 min → verify it auto-restarts
2. **Test reboot persistence:** `sudo reboot` → after boot, `systemctl --user status container-health.timer` shows active
3. **Check logs:** `journalctl --user -u container-health --since "5 min ago"`

## Failure Modes

| Failure | Mitigation |
|---------|-----------|
| `docker start` fails (network gone) | Recovery script retries; if persistent, needs manual `docker-compose up -d` |
| systemd --user not enabled after boot | `sudo loginctl enable-linger umbrel` to persist user services |
| Docker daemon down | Monitor already can't run; fix Docker first |

## Notes

- systemd user services are **persisted in `/home/umbrel/.config/systemd/user/`** — NOT overwritten by UmbrelOS updates
- User services start automatically at login. `loginctl enable-linger umbrel` ensures timer starts at boot even without login
- The monitor logs to `journalctl` and uses `logger` which also shows in `dmesg` for alerting
