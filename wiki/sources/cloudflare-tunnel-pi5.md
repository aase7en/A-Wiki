---
title: "Cloudflare Tunnel on Raspberry Pi 5"
type: source
domain: infrastructure
original_file: raw/cloudflare-tunnel-pi5.html
source_url: https://ladvien.com/cloud-flare-raspberry-pi-home-server/
ingested: 2026-06-21
routed_via: harness@v1
tags: [cloudflare, tunnel, raspberry-pi, networking, security]
---

## Summary

Cloudflare Tunnel (cloudflared) securely exposes local services to the internet without port forwarding. Key steps:

1. **Install**: `curl -L <cloudflared-arm64.deb> | sudo dpkg -i`
2. **Auth**: `cloudflared tunnel login` → browser OAuth
3. **Create**: `cloudflared tunnel create <name>`
4. **Config**: YAML file mapping hostname → local service URL
5. **DNS**: `cloudflared tunnel route dns <name> <subdomain>`
6. **Run**: Systemd service for persistence

Prerequisites: Cloudflare account, domain on Cloudflare nameservers.

For containerized setup (like Umbrel/Hermes):
- Can install cloudflared inside container → forward to localhost
- Or install on host → forward to container IP (10.21.0.x)
- Container install preferred for self-contained deployment
- Use `/opt/data` for persistence across app updates

## Security

- Automatic HTTPS via Cloudflare
- Hides home IP address
- No port forwarding needed on router
- Cloudflare Access can add additional auth layers
