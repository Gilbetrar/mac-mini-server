#!/bin/bash
# Issue #3: Install Caddy reverse proxy on Mac Mini
#
# Prerequisites: SSH access, Homebrew installed on Mac Mini
#
# What this does:
# 1. Installs Caddy via Homebrew
# 2. Deploys Caddyfile to ~/services/config/
# 3. Creates launchd service for auto-start
# 4. Configures log rotation

set -euo pipefail

REMOTE="mac-mini"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Installing Caddy ==="
ssh "$REMOTE" "brew install caddy"

echo "=== Deploying Caddyfile ==="
scp "$SCRIPT_DIR/config/Caddyfile" "$REMOTE:~/services/config/Caddyfile"

echo "=== Creating log directory ==="
ssh "$REMOTE" "mkdir -p ~/services/data/caddy"

echo "=== Validating Caddyfile ==="
ssh "$REMOTE" "caddy validate --config ~/services/config/Caddyfile"

echo "=== Installing launchd service ==="
scp "$SCRIPT_DIR/config/com.caddy.server.plist" "$REMOTE:~/Library/LaunchAgents/com.caddy.server.plist"
ssh "$REMOTE" "launchctl load ~/Library/LaunchAgents/com.caddy.server.plist"

echo "=== Waiting for Caddy to start ==="
sleep 3

echo "=== Verification ==="
echo "1. Caddy version:"
ssh "$REMOTE" "caddy version"
echo "2. Caddyfile exists:"
ssh "$REMOTE" "cat ~/services/config/Caddyfile"
echo "3. Caddyfile valid:"
ssh "$REMOTE" "caddy validate --config ~/services/config/Caddyfile 2>&1 | grep 'Valid'"
echo "4. Service loaded:"
ssh "$REMOTE" "launchctl list | grep caddy"
echo "5. HTTP response:"
ssh "$REMOTE" "curl -s http://localhost:80"

echo ""
echo "=== Caddy installation complete ==="
