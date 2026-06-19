# Hermes + A-Wiki Live — Complete Setup Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  Any Device                      │
│  Web browser → awiki-live.html                  │
│  (opens HTML file directly, no server needed)   │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/HTTPS
    ┌──────────────┼──────────────┐
    │ LAN          │ Tailscale     │ Tailscale Funnel
    │ pi5-local    │ 100.x.x.x     │ pi5.xxx.ts.net
    └──────────────┼──────────────┘
                   ▼
┌─────────────────────────────────────────────────┐
│              Raspberry Pi 5 (UmbrelOS)            │
│  ┌───────────────────────────────────────────┐  │
│  │  Docker: hermes-agent                     │  │
│  │  ├── CLI interface (localhost)            │  │
│  │  ├── Chat API: localhost:8501             │  │
│  │  │   /health — health check                │  │
│  │  │   /v1/chat/completions — OpenAI-compat │  │
│  │  ├── Webhook: 0.0.0.0:8644               │  │
│  │  └── Telegram gateway                     │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │  ~/A-Wiki/ (cloned from GitHub)           │  │
│  │  ├── wiki/ — 605+ knowledge pages         │  │
│  │  └── scripts/ — search, index tools       │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### Port Map

| Port | Service | Scope |
|------|---------|-------|
| 8501 | Hermes Chat API (OpenAI-compatible) | Docker internal by default |
| 8644 | Hermes Webhook gateway | 0.0.0.0 (all interfaces) |

Note: Port 8501 is the API server exposed by the Hermes Umbrel Docker app — it is not a Hermes default. Native Hermes installs may use different ports.

---

## Pi 5 Setup (UmbrelOS)

### Prerequisites

- Raspberry Pi 5 running UmbrelOS
- SSH access (`ssh umbrel@pi5-local`)
- Tailscale installed (optional, for remote access)

### Step 1: Install Hermes via Umbrel App Store

1. Open Umbrel dashboard → App Store
2. Search "Hermes Agent" → Install
3. Wait for Docker container to start

### Step 2: Verify API Works Locally

```bash
# SSH into Pi 5
ssh umbrel@pi5-local

# Test health endpoint
curl http://localhost:8501/health
# Expected: {"status":"ok"} or similar success response

# Test chat endpoint
curl -X POST http://localhost:8501/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hi"}],"max_tokens":50}'
```

### Step 3: Fix Docker Port Forwarding

Umbrel Docker containers don't expose ports to external interfaces by default. Fix this:

```bash
# Locate Hermes docker-compose
ls ~/umbrel/app-data/hermes-agent/

# Edit docker-compose.yml
nano ~/umbrel/app-data/hermes-agent/docker-compose.yml
```

Ensure port mapping exists:
```yaml
services:
  hermes:
    ports:
      - "8501:8501"
```

Restart:
```bash
cd ~/umbrel
./scripts/app restart hermes-agent
```

If this doesn't work, use Tailscale Funnel as fallback.

### Step 4: Configure Tailscale (for remote access)

```bash
# Install if not already
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up

# Find your Tailscale IP
tailscale ip -4
# Example: 100.111.37.13

# Enable Funnel (workaround if Docker port forwarding fails)
tailscale funnel 8501
# Creates: https://pi5.tailnet-name.ts.net/
```

### Step 5: Clone A-Wiki Brain

```bash
git clone https://github.com/aase7en/A-Wiki.git ~/A-Wiki
cd ~/A-Wiki
bash scripts/setup-local.sh
```

### Step 6: Configure Hermes

```bash
# Copy Pi 5 config
cp ~/A-Wiki/hermes-config/pi5-config.yaml ~/.hermes/config.yaml

# Add API keys
echo 'DEEPSEEK_API_KEY=sk-...' >> ~/.hermes/.env
```

### Step 7: Start Gateway

```bash
hermes gateway start
```

---

## MacBook Setup (Secondary Device)

### Install Hermes (Native)

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.zshrc
hermes
```

### Clone A-Wiki

```bash
git clone https://github.com/aase7en/A-Wiki.git ~/A-Wiki
cd ~/A-Wiki
bash scripts/setup-local.sh
```

### Configure

```bash
# Copy config template
cp ~/A-Wiki/hermes-config/pi5-config.yaml ~/.hermes/config.yaml
# Edit terminal.cwd to ~/A-Wiki if different
nano ~/.hermes/config.yaml

# Add API keys
echo 'DEEPSEEK_API_KEY=sk-...' >> ~/.hermes/.env
```

### Test Connection to Pi 5

```bash
# LAN
curl http://pi5-local:8501/health

# Tailscale
curl http://100.111.37.13:8501/health

# Tailscale Funnel (if enabled)
curl https://pi5.tailnet-name.ts.net/health
```

---

## Access Modes

| Mode | URL | Requirements | Speed |
|------|-----|-------------|-------|
| LAN | `http://pi5-local:8501` | Same WiFi network | Fast |
| Tailscale | `http://100.111.37.13:8501` | Tailscale on both devices | Medium |
| Tailscale Funnel | `https://pi5.xxx.ts.net` | Funnel enabled on Pi 5 | Slow (via relay) |
| Cloudflare Tunnel | `https://awiki-hermes.yourdomain.com` | Cloudflare Tunnel on Pi 5 | Fast (HTTPS, global) |
| Custom | User-defined | Manual config | Varies |

### Cloudflare Tunnel Setup (Recommended for Team Access)

Cloudflare Tunnel ให้ทีมเข้าถึง Hermes จากทุกที่ผ่าน HTTPS โดยไม่ต้องติดตั้ง Tailscale บนทุกเครื่อง

**Quick Setup on Pi 5:**
```bash
# Install
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 \
  -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared

# Authenticate
cloudflared tunnel login
# (copy URL → open browser → select domain)

# Create tunnel
cloudflared tunnel create awiki-hermes
# (note the tunnel ID)

# Configure DNS (in Cloudflare dashboard)
# CNAME: awiki-hermes → <TUNNEL_ID>.cfargotunnel.com

# Copy and configure
cp ~/A-Wiki/hermes-config/cloudflared-config.yml ~/.cloudflared/config.yml
# Edit: replace <TUNNEL_ID> and yourdomain.com

# Install as service
cloudflared service install

# Verify
curl https://awiki-hermes.yourdomain.com/health
```

Full guide: `docs/cloudflare-tunnel-setup.md`

After setup, select "☁️ Cloudflare Tunnel" profile in A-Wiki Live settings.

---

## A-Wiki Live Setup

### Quick Start

1. Open `awiki-live.html` in any browser
2. Click ⚙️ → select your profile (LAN / Tailscale / Funnel)
3. Click "Auto-Detect" to find working connection
4. Click "Test" to verify
5. Save and start chatting

### Connection Profiles

The UI supports 5 profiles:

- **LAN (ที่บ้าน)**: Fastest — uses `pi5-local:8501`
- **Tailscale (นอกบ้าน)**: Remote — uses Tailscale IP `100.111.37.13:8501`
- **Tailscale Funnel**: Public HTTPS — requires `tailscale funnel 8501` on Pi 5
- **Cloudflare Tunnel**: Global HTTPS — requires Cloudflare Tunnel on Pi 5
- **Custom**: Any URL — for future Hermes instances

### Auto-Detect Logic

The auto-detect tries profiles in order: LAN → Tailscale → Funnel. Each attempt uses a 3-second timeout. The first successful `/health` response selects that profile.

---

## Testing

### From Pi 5 (localhost)

```bash
curl http://localhost:8501/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hello"}],"max_tokens":100}'
```

### From Same LAN

```bash
curl http://pi5-local:8501/health
```

### From Tailscale

```bash
curl http://100.111.37.13:8501/health
```

### From A-Wiki Live

1. Open `awiki-live.html`
2. Click ⚙️ → Auto-Detect
3. Send a test message

---

## Troubleshooting

### API Returns Empty Reply

**Cause**: Docker port not forwarded to external interfaces.  
**Fix**: Edit `~/umbrel/app-data/hermes-agent/docker-compose.yml` and add `ports: ["8501:8501"]`, then restart.

### Connection Refused on Tailscale IP

**Cause**: Hermes not running or Docker port issue.  
**Check**: 
```bash
ssh umbrel@pi5-local
docker ps | grep hermes
curl http://localhost:8501/health
```

### Tailscale Funnel Not Working

**Fix**: Re-enable funnel on Pi 5:
```bash
tailscale funnel 8501
```
Note the URL shown — update `awiki-live.html` Funnel profile with the actual URL.

### API Timeout (120s)

Hermes may take time to search wiki + reason. The client has a 120-second timeout. If Hermes times out:
- Try shorter, more specific questions
- Check Hermes is not stuck (`hermes status`)
- Reduce `max_tokens` in the request

### CORS Errors in Browser

If the browser blocks requests: Hermes API must include CORS headers. If using Tailscale Funnel, this is handled automatically. For direct IP access, open `awiki-live.html` from the same origin or use a browser extension to disable CORS.

---

## Related Files

| File | Purpose |
|------|---------|
| `awiki-live.html` | Web UI for Hermes chat |
| `hermes-config/pi5-config.yaml` | Hermes config for Pi 5 |
| `hermes-config/setup-pi5.sh` | One-time Pi 5 setup script |
| `wiki/entities/ai-tools/hermes-agent.md` | Entity documentation |
| `wiki/sources/hermes-agent-guide-th.md` | Thai language guide |
