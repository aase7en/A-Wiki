# Plan: A-Wiki Live — Team AI System with Cloudflare Tunnel

## Vision
ต่อยอด A-Wiki Live ให้เป็นระบบ AI สำหรับทีม — เข้าถึงได้จากทุกที่ผ่าน Cloudflare Tunnel, มี authentication, รองรับการใช้งานพร้อมกันหลายคน

## Architecture

```
[Team Members] ──> [GitHub Pages: awiki-live.html]
                          │
                          │ (HTTPS)
                          ▼
                   [Cloudflare Tunnel]
                          │
                          ▼
                   [Pi 5 @ Home]
                   ├── Hermes API Server (port 8501)
                   ├── A-Wiki Brain (605+ wiki pages)
                   └── Bitcoin Node (sharing resources)
                          │
                          ▼
                   [DeepSeek / OpenRouter API]
```

## Current State

| Component | Status | Notes |
|-----------|--------|-------|
| `awiki-live.html` | ✅ Modified (uncommitted) | มี profile system แล้ว (LAN/Tailscale/Funnel/Custom) |
| `live-dashboard.html` | ✅ Modified (uncommitted) | มี Chat tab + dual-mode (proxy/direct) |
| Hermes API on Pi 5 | ✅ Running | Port 8501, OpenAI-compatible |
| Cloudflare Tunnel | ❌ Not set up | ต้องติดตั้งบน Pi 5 |
| Authentication | ❌ Not implemented | ต้องเพิ่ม token gate |
| GitHub Pages | ❌ Not configured | ต้องสร้าง repo + enable Pages |

## Implementation Plan

### Phase 1: Cloudflare Tunnel Setup (Pi 5)

**Files to create/modify:**
- `docs/cloudflare-tunnel-setup.md` — คู่มือติดตั้ง Cloudflare Tunnel บน Pi 5
- `hermes-config/cloudflared-config.yml` — config template

**Steps:**
1. ติดตั้ง `cloudflared` บน Pi 5 (UmbrelOS)
2. สร้าง tunnel: `cloudflared tunnel create awiki-hermes`
3. Config route: `awiki-hermes.yourdomain.com` → `http://localhost:8501`
4. เพิ่ม profile "Cloudflare" ใน `awiki-live.html` PROFILES
5. อัปเดต `docs/hermes-setup-guide.md`

**Profile addition in awiki-live.html:**
```javascript
cloudflare: { 
  name: 'Cloudflare Tunnel', 
  url: 'https://awiki-hermes.yourdomain.com',
  hint: 'ต้องติดตั้ง cloudflared บน Pi 5' 
}
```

### Phase 2: Authentication Layer

**Files to modify:**
- `awiki-live.html` — เพิ่ม auth gate + token validation
- `scripts/live-dashboard/server.py` — เพิ่ม `/api/auth/verify` endpoint

**Design:**
- Simple token stored in `drive/.secrets` (server-side)
- Client sends token in `Authorization: Bearer <token>` header
- Server validates before proxying to Hermes
- Token stored in localStorage after first login
- Login screen appears if no valid token

**UI Flow:**
```
[Open awiki-live.html]
        │
        ▼
[Login Screen] ← if no token in localStorage
  "Enter team access code"
        │
        ▼ (POST /api/auth/verify with token)
[Server validates]
        │
        ├── Valid → [Chat UI]
        └── Invalid → [Error message]
```

**Server-side validation:**
```python
# server.py
TEAM_TOKENS = load_tokens_from_secrets()  # ["token1", "token2", ...]

def _api_auth_verify(self):
    token = self.headers.get("Authorization", "").replace("Bearer ", "")
    if token in TEAM_TOKENS:
        self._json_response({"valid": True})
    else:
        self._json_response({"valid": False}, 401)
```

### Phase 3: GitHub Pages Deployment

**Files to create:**
- `.github/workflows/pages.yml` — auto-deploy workflow
- `README.md` — instructions for team members

**Steps:**
1. Enable GitHub Pages ใน repo settings
2. Configure workflow to deploy `awiki-live.html` as `index.html`
3. Add custom domain (optional): `team-ai.yourdomain.com`
4. Document access URL for team

**Workflow:**
```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
    paths: ['awiki-live.html']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cp awiki-live.html docs/index.html
      - uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

### Phase 4: Concurrency & Queue Management

**Files to modify:**
- `scripts/live-dashboard/server.py` — เพิ่ม queue system
- `hermes-config/pi5-config.yaml` — limit concurrent sessions

**Design:**
- Server-side queue with max 2 concurrent requests
- Return queue position to client
- Client shows "You are #N in queue" message
- Timeout after 5 minutes if stuck

**Server-side queue:**
```python
from collections import deque
import threading

chat_queue = deque()
active_requests = 0
MAX_CONCURRENT = 2
queue_lock = threading.Lock()

def _api_chat_post(self):
    global active_requests
    with queue_lock:
        if active_requests >= MAX_CONCURRENT:
            position = len(chat_queue) + 1
            self._json_response({"queued": True, "position": position}, 202)
            chat_queue.append(self)
            return
        active_requests += 1
    
    try:
        # ... existing proxy logic ...
    finally:
        with queue_lock:
            active_requests -= 1
            if chat_queue:
                next_req = chat_queue.popleft()
                # Process next request
```

**Client-side queue handling:**
```javascript
if (resp.status === 202) {
  const data = await resp.json();
  addMsg('hermes', `⏳ คุณอยู่ในคิวลำดับที่ ${data.position}\nระบบกำลังประมวลผล request อื่นอยู่`);
  // Poll for completion or retry after delay
}
```

### Phase 5: Team Features (Optional)

**Enhancements:**
- User identification (name/email in localStorage)
- Usage tracking per user (store in server memory)
- Shared conversation history (optional)
- Admin panel for managing tokens

---

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `awiki-live.html` | Modify | Add Cloudflare profile + auth gate + queue UI |
| `scripts/live-dashboard/server.py` | Modify | Add `/api/auth/verify` + queue system |
| `docs/cloudflare-tunnel-setup.md` | Create | คู่มือติดตั้ง Cloudflare Tunnel |
| `hermes-config/cloudflared-config.yml` | Create | Config template |
| `.github/workflows/pages.yml` | Create | Auto-deploy workflow |
| `hermes-config/pi5-config.yaml` | Modify | Limit concurrent sessions |
| `docs/hermes-setup-guide.md` | Modify | Add Cloudflare section |

## Execution Order

1. **Phase 1**: Cloudflare Tunnel — setup on Pi 5, add profile
2. **Phase 2**: Authentication — add token gate to UI + server
3. **Phase 3**: GitHub Pages — configure deployment
4. **Phase 4**: Concurrency — add queue system
5. **Phase 5**: Team features (optional)

## Testing Checklist

- [ ] Cloudflare Tunnel works from external network
- [ ] Auth gate blocks unauthorized access
- [ ] Valid token grants access
- [ ] GitHub Pages deploys correctly
- [ ] Queue system handles concurrent requests
- [ ] Mobile UI works with auth + queue messages
- [ ] Team members can access from different locations

## Security Considerations

- Token stored in `drive/.secrets` (gitignored)
- HTTPS enforced via Cloudflare
- Rate limiting: 10 requests/minute per token
- No sensitive data in client localStorage (only token)
- Server logs all auth attempts

## Cost & Resource Impact

- **Cloudflare Tunnel**: Free tier sufficient
- **GitHub Pages**: Free for public repos
- **Pi 5 resources**: ~200MB RAM for cloudflared
- **API costs**: Shared across team (monitor usage)
