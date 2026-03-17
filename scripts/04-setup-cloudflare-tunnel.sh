#!/bin/bash
# Issue #4: Cloudflare setup + Tunnel
#
# This script completes the tunnel setup AFTER the interactive login
# has been done (see HANDOFF.md for login instructions).
#
# Prerequisites:
# - cloudflared installed (brew install cloudflared)
# - cloudflared login completed (cloudflared tunnel login)
# - bjblabs.com added to Cloudflare dashboard
#
# Usage: ./scripts/04-setup-cloudflare-tunnel.sh

set -euo pipefail

REMOTE="mac-mini"
TUNNEL_NAME="mac-mini"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Checking cloudflared login ==="
ssh "$REMOTE" "ls ~/.cloudflared/cert.pem" || { echo "ERROR: Run 'cloudflared tunnel login' first"; exit 1; }

echo "=== Creating tunnel ==="
ssh "$REMOTE" "cloudflared tunnel create $TUNNEL_NAME"

echo "=== Getting tunnel UUID ==="
TUNNEL_UUID=$(ssh "$REMOTE" "cloudflared tunnel list --output json | python3 -c 'import sys,json; tunnels=json.load(sys.stdin); print([t[\"id\"] for t in tunnels if t[\"name\"]==\"$TUNNEL_NAME\"][0])'")
echo "Tunnel UUID: $TUNNEL_UUID"

echo "=== Deploying config ==="
ssh "$REMOTE" "mkdir -p ~/services/config/cloudflared ~/services/data/cloudflared"
scp "$SCRIPT_DIR/config/cloudflared/config.yml" "$REMOTE:~/services/config/cloudflared/config.yml"
ssh "$REMOTE" "sed -i '' 's/TUNNEL_UUID/$TUNNEL_UUID/g' ~/services/config/cloudflared/config.yml"

echo "=== Creating DNS route ==="
ssh "$REMOTE" "cloudflared tunnel route dns $TUNNEL_NAME test.bjblabs.com"

echo "=== Installing launchd service ==="
scp "$SCRIPT_DIR/config/com.cloudflare.cloudflared.plist" "$REMOTE:~/Library/LaunchAgents/com.cloudflare.cloudflared.plist"
ssh "$REMOTE" "launchctl load ~/Library/LaunchAgents/com.cloudflare.cloudflared.plist"

echo "=== Waiting for tunnel to connect ==="
sleep 5

echo "=== Verification ==="
echo "1. cloudflared version:"
ssh "$REMOTE" "cloudflared --version"
echo "2. Tunnel list:"
ssh "$REMOTE" "cloudflared tunnel list"
echo "3. Tunnel info:"
ssh "$REMOTE" "cloudflared tunnel info $TUNNEL_NAME"
echo "4. Service loaded:"
ssh "$REMOTE" "launchctl list | grep cloudflare"
echo "5. Config:"
ssh "$REMOTE" "cat ~/services/config/cloudflared/config.yml"

echo ""
echo "=== Tunnel setup complete ==="
echo "Manual verification: check Cloudflare dashboard for tunnel health"
echo "After DNS cutover: curl https://test.bjblabs.com should return Caddy response"
