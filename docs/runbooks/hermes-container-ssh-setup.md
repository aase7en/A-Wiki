# Hermes Agent Container — SSH Key Setup (Umbrel)

## Overview
SSH key pair generated inside the Hermes Agent Umbrel container for direct git push to GitHub.

## Key Location
- **Private key:** `/opt/data/.ssh/id_ed25519` (persistent across app updates)
- **Public key:** `/opt/data/.ssh/id_ed25519.pub`
- **SSH config:** `/opt/data/.ssh/config` → GitHub host mapping

## Setup Date
2026-06-20

## Notes
- Key type: ed25519
- Container runs on Raspberry Pi 5 (aarch64)
- This key is separate from the host-level `aas7en-raspberry-pi5-at-home` key
- `/opt/data` is persistent — key survives Umbrel app updates
