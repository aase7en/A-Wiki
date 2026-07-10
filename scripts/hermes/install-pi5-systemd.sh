#!/usr/bin/env bash
# =============================================================================
# install-pi5-systemd.sh — Install/refresh the Pi5 timers (sync 6h + weekly reboot)
# =============================================================================
# Why systemd, not cron: the Umbrel Pi5 host has NO crontab binary at all
# (discovered live 2026-07-10) — every "cron 6h" line in older runbooks was
# aspiration. systemd 257 is present.
#
# Run ON THE PI5 HOST, as root:
#   sudo bash scripts/hermes/install-pi5-systemd.sh            # install/refresh
#   sudo bash scripts/hermes/install-pi5-systemd.sh --status   # timers + last runs
#   sudo bash scripts/hermes/install-pi5-systemd.sh --uninstall
#
# Renders @HOME@/@USER@ from the invoking (sudo) user so the repo carries no
# hardcoded personal paths (Iron Law #6). Idempotent — safe to re-run after
# every git pull that touches the unit templates.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_SRC="$SCRIPT_DIR/systemd"
UNIT_DST="/etc/systemd/system"
UNITS="awiki-hermes-sync.service awiki-hermes-sync.timer awiki-pi5-reboot.service awiki-pi5-reboot.timer"
TIMERS="awiki-hermes-sync.timer awiki-pi5-reboot.timer"

# ---- Platform guard (same idiom as awiki-pi5-sync.sh) ----
detect_pi5() {
  hostname 2>/dev/null | grep -qi "umbrel\|raspberry" && return 0
  [ -f /opt/umbreld/package.json ] && return 0
  [ -d /umbrel ] && return 0
  return 1
}
if ! detect_pi5; then
  echo "[X] This installer is for the Pi5 (Umbrel) host only." >&2
  exit 1
fi

case "${1:-install}" in
  --status)
    systemctl list-timers awiki-hermes-sync.timer awiki-pi5-reboot.timer --no-pager || true
    echo ""
    for t in $TIMERS; do
      systemctl is-enabled "$t" >/dev/null 2>&1 \
        && echo "  [ OK ] $t enabled" || echo "  [ -- ] $t NOT enabled"
    done
    echo ""
    echo "Last sync runs:  journalctl -u awiki-hermes-sync.service -n 30 --no-pager"
    exit 0
    ;;
  --uninstall)
    for t in $TIMERS; do systemctl disable --now "$t" 2>/dev/null || true; done
    for u in $UNITS; do rm -f "$UNIT_DST/$u"; done
    systemctl daemon-reload
    echo "[OK] timers removed"
    exit 0
    ;;
  install) ;;
  *) echo "usage: sudo bash $0 [--status|--uninstall]" >&2; exit 1 ;;
esac

if [ "$(id -u)" != "0" ]; then
  echo "[X] install needs root: sudo bash $0" >&2
  exit 1
fi

# Render for the real (sudo-invoking) user, not root
RUN_USER="${SUDO_USER:-umbrel}"
RUN_HOME="$(getent passwd "$RUN_USER" | cut -d: -f6)"
[ -z "$RUN_HOME" ] && { echo "[X] cannot resolve home for $RUN_USER" >&2; exit 1; }
[ -d "$RUN_HOME/A-Wiki" ] || { echo "[X] $RUN_HOME/A-Wiki not found — clone it first" >&2; exit 1; }

for u in $UNITS; do
  sed -e "s|@USER@|$RUN_USER|g" -e "s|@HOME@|$RUN_HOME|g" \
    "$UNIT_SRC/$u" > "$UNIT_DST/$u"
  echo "  rendered $u (user=$RUN_USER)"
done

systemctl daemon-reload
for t in $TIMERS; do
  systemctl enable --now "$t"
  echo "  [OK] $t enabled + started"
done

echo ""
systemctl list-timers awiki-hermes-sync.timer awiki-pi5-reboot.timer --no-pager || true
echo ""
echo "[OK] done. Verify a manual run: sudo systemctl start awiki-hermes-sync.service"
echo "     then: journalctl -u awiki-hermes-sync.service -n 30 --no-pager"
