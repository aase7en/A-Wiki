#!/bin/bash
# ============================================================
# A-Wiki + Hermes Pi 5 Setup Script
# รันบน Pi 5 (UmbrelOS) ครั้งเดียว
# ============================================================
set -e

echo "╔══════════════════════════════════════════╗"
echo "║   A-Wiki + HERMES Pi 5 Setup           ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ---------- Step 1: Add SSH Key ----------
echo "[1/7] Adding SSH key for remote access..."
mkdir -p ~/.ssh
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDqmBte0XHSblzJISd3GbNVG9Naz4Dr2e7CemcjZbBG+ awiki-hermes" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
echo "  ✓ SSH key added"

# ---------- Step 2: Install Hermes ----------
echo "[2/7] Installing Hermes Agent..."
if command -v hermes &>/dev/null; then
    echo "  ✓ Hermes already installed: $(hermes --version 2>&1 | head -1)"
else
    curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
    echo "  ✓ Hermes installed"
fi

# ---------- Step 3: Apply Config ----------
echo "[3/7] Applying Pi 5 config..."
mkdir -p ~/.hermes
# Copy config from A-Wiki repo (if cloned) or use bundled copy
if [ -f ~/A-Wiki/hermes-config/pi5-config.yaml ]; then
    cp ~/A-Wiki/hermes-config/pi5-config.yaml ~/.hermes/config.yaml
    echo "  ✓ Config copied from A-Wiki repo"
else
    echo "  ⚠ A-Wiki not cloned yet — config will be applied after clone"
fi

# ---------- Step 4: Clone A-Wiki ----------
echo "[4/7] Cloning A-Wiki brain..."
if [ -d ~/A-Wiki ]; then
    echo "  ✓ A-Wiki already exists"
    cd ~/A-Wiki && git pull origin main
else
    git clone https://github.com/aase7en/A-Wiki.git ~/A-Wiki
    echo "  ✓ A-Wiki cloned to ~/A-Wiki"
fi

# ---------- Step 5: A-Wiki Setup ----------
echo "[5/7] Running A-Wiki setup..."
cd ~/A-Wiki
bash scripts/setup-local.sh 2>&1 | tail -5
echo "  ✓ A-Wiki setup complete"

# Re-copy config after clone
if [ -f ~/A-Wiki/hermes-config/pi5-config.yaml ]; then
    cp ~/A-Wiki/hermes-config/pi5-config.yaml ~/.hermes/config.yaml
fi

# ---------- Step 6: .env ----------
echo "[6/7] Setting up API keys (.env)..."
if [ -f ~/A-Wiki-Data/.secrets ] || [ -f ~/drive/.secrets ]; then
    echo "  ✓ Secrets file found"
else
    echo "  ⚠ No .secrets file — create ~/.hermes/.env manually"
    echo "  Example: echo 'DEEPSEEK_API_KEY=sk-...' >> ~/.hermes/.env"
fi

# ---------- Step 7: Gateway ----------
echo "[7/7] Installing Hermes Gateway (auto-start)..."
hermes gateway install 2>&1 | tail -3 || echo "  ⚠ Gateway install skipped (run manually: hermes gateway install)"
echo "  ✓ Setup complete!"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   ✅ Pi 5 Setup Complete!              ║"
echo "║                                        ║"
echo "║   Start gateway: hermes gateway start  ║"
echo "║   Check status:  hermes status         ║"
echo "║   A-Wiki dir:    ~/A-Wiki             ║"
echo "╚══════════════════════════════════════════╝"
