"""
Tests for scripts/hermes/systemd/ — Pi5 timer units + installer.

Why systemd and not cron: the Umbrel Pi5 host has NO crontab binary at all
(discovered live 2026-07-10) — every "cron 6h" reference in the runbooks was
aspiration. systemd 257 is present, so scheduling uses timer units.

Units are templates (@HOME@ / @USER@ placeholders) rendered by the installer
at install time — no hardcoded personal paths in the repo (Iron Law #6).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEMD_DIR = REPO_ROOT / "scripts" / "hermes" / "systemd"

SYNC_SERVICE = SYSTEMD_DIR / "awiki-hermes-sync.service"
SYNC_TIMER = SYSTEMD_DIR / "awiki-hermes-sync.timer"
REBOOT_SERVICE = SYSTEMD_DIR / "awiki-pi5-reboot.service"
REBOOT_TIMER = SYSTEMD_DIR / "awiki-pi5-reboot.timer"
INSTALLER = REPO_ROOT / "scripts" / "hermes" / "install-pi5-systemd.sh"


class TestSyncUnit:
    def test_service_template_exists(self) -> None:
        assert SYNC_SERVICE.is_file()

    def test_service_runs_auto_sync_as_templated_user(self) -> None:
        text = SYNC_SERVICE.read_text()
        assert "auto-sync-from-git.sh" in text
        assert "@HOME@" in text  # rendered at install time, not hardcoded
        assert "User=@USER@" in text
        assert "Type=oneshot" in text

    def test_service_waits_for_network_and_docker(self) -> None:
        text = SYNC_SERVICE.read_text()
        assert "network-online.target" in text
        assert "docker.service" in text

    def test_timer_every_6h_and_after_boot(self) -> None:
        text = SYNC_TIMER.read_text()
        assert "OnUnitActiveSec=6h" in text
        assert "OnBootSec=" in text
        assert "Persistent=true" in text  # catch up after downtime


class TestRebootUnit:
    def test_reboot_units_exist(self) -> None:
        assert REBOOT_SERVICE.is_file()
        assert REBOOT_TIMER.is_file()

    def test_reboot_is_weekly_offpeak_and_persistent_false(self) -> None:
        text = REBOOT_TIMER.read_text()
        assert "OnCalendar=" in text
        # Persistent=true on a reboot timer would reboot IMMEDIATELY on boot
        # after any downtime that skipped a window — must never catch up.
        assert "Persistent=true" not in text

    def test_reboot_calls_systemctl_reboot(self) -> None:
        text = REBOOT_SERVICE.read_text()
        assert "systemctl reboot" in text


class TestInstaller:
    def test_installer_exists(self) -> None:
        assert INSTALLER.is_file()

    def test_installer_renders_placeholders(self) -> None:
        text = INSTALLER.read_text()
        assert "@HOME@" in text and "@USER@" in text  # sed-render step

    def test_installer_enables_both_timers(self) -> None:
        text = INSTALLER.read_text()
        assert "daemon-reload" in text
        assert "awiki-hermes-sync.timer" in text
        assert "awiki-pi5-reboot.timer" in text
        assert "enable --now" in text

    def test_installer_is_pi5_guarded_and_has_uninstall(self) -> None:
        text = INSTALLER.read_text()
        assert "umbrel" in text  # platform guard
        assert "--uninstall" in text
        assert "--status" in text
