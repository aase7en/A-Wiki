# Cloudflare Tunnel Setup — A-Wiki Hermes

## Overview

Cloudflare Tunnel ให้ทีมเข้าถึง Hermes AI Chat จากทุกที่ผ่าน HTTPS โดยไม่ต้องเปิด port บน router หรือใช้ Tailscale

```
[Team Members] ──HTTPS──> [Cloudflare Edge] ──Tunnel──> [Pi 5] ──> Hermes API :8501
```

## Prerequisites

- Raspberry Pi 5 running UmbrelOS
- Domain name ที่ใช้ Cloudflare DNS (เช่น `yourdomain.com`)
- Hermes API รันอยู่ที่ `localhost:8501`
- SSH access (`ssh umbrel@pi5-local`)

## Step 1: Install cloudflared

```bash
ssh umbrel@pi5-local

# Download ARM64 binary
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 \
  -o /usr/local/bin/cloudflared

chmod +x /usr/local/bin/cloudflared

# Verify
cloudflared version
```

## Step 2: Authenticate with Cloudflare

```bash
cloudflared tunnel login
```

คัดลอก URL ที่แสดง → เปิดใน browser → เลือก domain → authorize

## Step 3: Create Tunnel

```bash
cloudflared tunnel create awiki-hermes
```

Output:
```
Created tunnel awiki-hermes with id <UUID>
```

จด Tunnel ID ไว้ (ใช้ใน config)

## Step 4: Configure DNS

1. ไปที่ Cloudflare Dashboard → DNS → Records
2. เพิ่ม CNAME record:
   - **Name**: `awiki-hermes` (หรือชื่อที่ต้องการ)
   - **Target**: `<TUNNEL_ID>.cfargotunnel.com`
   - **Proxy status**: Proxied (orange cloud)

## Step 5: Create Config File

```bash
mkdir -p ~/.cloudflared

# Copy template จาก A-Wiki
cp ~/A-Wiki/hermes-config/cloudflared-config.yml ~/.cloudflared/config.yml

# แก้ไข:
# - แทนที่ <TUNNEL_ID> ด้วย tunnel ID จริง
# - แทนที่ yourdomain.com ด้วย domain จริง
nano ~/.cloudflared/config.yml
```

## Step 6: Install as System Service

```bash
cloudflared service install
systemctl status cloudflared

# Check logs
journalctl -u cloudflared -f
```

## Step 7: Test

```bash
# From anywhere with internet
curl https://awiki-hermes.yourdomain.com/health
# Expected: {"status":"ok"}

# Test chat
curl -X POST https://awiki-hermes.yourdomain.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hello"}],"max_tokens":50}'
```

## Step 8: Add Cloudflare Profile to A-Wiki Live

1. Open `awiki-live.html` หรือ live-dashboard
2. Settings → เลือก "☁️ Cloudflare Tunnel"
3. ใส่ URL: `https://awiki-hermes.yourdomain.com`
4. ทดสอบ → บันทึก

## Optional: Tunnel Dashboard Server Too

ถ้าต้องการให้ `/api/auth/verify` endpoint ทำงานจากภายนอก (สำหรับ login team):

1. เพิ่ม DNS record: `awiki-dashboard.yourdomain.com` → tunnel CNAME
2. Uncomment dashboard section ใน `cloudflared-config.yml`
3. Restart: `systemctl restart cloudflared`
4. ตั้งค่า auth server ใน awiki-live.html settings

## Troubleshooting

### Tunnel won't start
```bash
# Check config syntax
cloudflared tunnel ingress validate

# Test manually
cloudflared tunnel run awiki-hermes
```

### DNS not resolving
- ตรวจสอบว่า CNAME record ถูกสร้างและ proxy (orange cloud) เปิดอยู่
- รอ DNS propagation (ปกติ 1-5 นาที)

### Hermes not responding through tunnel
- ตรวจสอบว่า Hermes API รันอยู่: `curl http://localhost:8501/health`
- ตรวจสอบ cloudflared logs: `journalctl -u cloudflared -n 50`

### Certificate errors
- Cloudflare จัดการ TLS certificate อัตโนมัติ
- ถ้าใช้ custom domain, รอให้ Cloudflare ออก Universal SSL certificate

## Resource Usage

- **CPU**: ~1-2% บน Pi 5
- **RAM**: ~50-100 MB
- **Bandwidth**: ฟรี (Cloudflare Zero Trust Free tier)
- **Latency**: +5-20ms จากตรง (ผ่าน Cloudflare edge)

## Security

- Cloudflare Tunnel เป็น outbound connection จาก Pi 5 เท่านั้น — ไม่ต้องเปิด port บน router
- HTTPS enforced — Cloudflare จัดการ TLS termination
- Authentication แยก layer (ดู `docs/hermes-setup-guide.md` § Authentication)
- Cloudflare WAF/DDoS protection อัตโนมัติ

## References

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [Zero Trust Free Tier](https://www.cloudflare.com/plans/zero-trust-services/)
- `hermes-config/pi5-config.yaml` — Hermes config
- `awiki-live.html` — Chat UI
