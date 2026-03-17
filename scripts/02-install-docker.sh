#!/bin/bash
# Issue #2: Install Docker Desktop on Mac Mini (ARM64)
#
# This script documents the Docker Desktop installation and configuration.
# It was executed remotely via SSH against the Mac Mini.
#
# Prerequisites: SSH access to mac-mini, macOS on Apple Silicon
#
# What this does:
# 1. Downloads and installs Docker Desktop for Apple Silicon
# 2. Runs the installer with --accept-license
# 3. Creates CLI symlinks in /usr/local/bin
# 4. Configures resource limits (4 CPUs, 8GB RAM)
# 5. Enables auto-start on login
# 6. Configures log rotation
# 7. Sets up .zshenv for SSH PATH compatibility

set -euo pipefail

REMOTE="mac-mini"

echo "=== Installing Docker Desktop ==="
# Download Docker Desktop for Apple Silicon
ssh "$REMOTE" "curl -L -o /tmp/Docker.dmg 'https://desktop.docker.com/mac/main/arm64/Docker.dmg'"

# Mount, copy, unmount
ssh "$REMOTE" "hdiutil attach /tmp/Docker.dmg -nobrowse -quiet"
ssh "$REMOTE" "cp -R /Volumes/Docker/Docker.app /Applications/"
ssh "$REMOTE" "hdiutil detach /Volumes/Docker -quiet"
ssh "$REMOTE" "rm /tmp/Docker.dmg"

echo "=== Running installer ==="
ssh "$REMOTE" "sudo /Applications/Docker.app/Contents/MacOS/install --accept-license --user ben"
ssh "$REMOTE" "sudo /Applications/Docker.app/Contents/MacOS/install config --user ben"

echo "=== Creating CLI symlinks ==="
ssh "$REMOTE" "sudo mkdir -p /usr/local/bin"
for bin in docker docker-credential-desktop docker-credential-ecr-login docker-credential-osxkeychain kubectl; do
    ssh "$REMOTE" "sudo ln -sf /Applications/Docker.app/Contents/Resources/bin/$bin /usr/local/bin/$bin"
done

echo "=== Setting up PATH for SSH sessions ==="
# .zshenv is sourced even by non-interactive SSH command execution
ssh "$REMOTE" 'echo "export PATH=\"/usr/local/bin:/opt/homebrew/bin:\$PATH\"" > ~/.zshenv'

echo "=== Launching Docker Desktop ==="
ssh "$REMOTE" "open -a 'Docker'"
echo "Waiting 30s for Docker engine to start..."
sleep 30

echo "=== Configuring resource limits ==="
# Stop Docker Desktop first
ssh "$REMOTE" "osascript -e 'tell application \"Docker\" to quit'"
sleep 10

# Set resource limits in Docker Desktop settings
ssh "$REMOTE" "python3 -c \"
import json
path = '/Users/ben/Library/Group Containers/group.com.docker/settings-store.json'
with open(path) as f:
    s = json.load(f)
s['AutoStart'] = True
s['CPUs'] = 4
s['MemoryMiB'] = 8192
s['DiskSizeMiB'] = 65536
with open(path, 'w') as f:
    json.dump(s, f, indent=2, sort_keys=True)
\""

echo "=== Configuring log rotation ==="
ssh "$REMOTE" 'cat > ~/.docker/daemon.json << '"'"'EOF'"'"'
{
  "builder": {
    "gc": {
      "defaultKeepStorage": "20GB",
      "enabled": true
    }
  },
  "experimental": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF'

echo "=== Configuring Docker for SSH compatibility ==="
# Remove credsStore to avoid keychain access issues in SSH sessions
ssh "$REMOTE" 'cat > ~/.docker/config.json << '"'"'EOF'"'"'
{
  "auths": {},
  "currentContext": "desktop-linux"
}
EOF'

echo "=== Adding Docker Desktop as login item ==="
ssh "$REMOTE" "osascript -e 'tell application \"System Events\" to make login item at end with properties {path:\"/Applications/Docker.app\", hidden:true}'"

echo "=== Restarting Docker Desktop ==="
ssh "$REMOTE" "open -a 'Docker'"
echo "Waiting 30s for Docker engine..."
sleep 30

echo "=== Verification ==="
echo "1. Docker version:"
ssh "$REMOTE" "docker --version"
echo "2. Architecture:"
ssh "$REMOTE" "docker info --format '{{.Architecture}}'"
echo "3. Hello-world test:"
ssh "$REMOTE" "docker run --rm hello-world 2>&1 | head -2"
echo "4. Resource limits:"
ssh "$REMOTE" "docker info --format '{{.NCPU}} CPUs, {{.MemTotal}}'"
echo "5. Logging driver:"
ssh "$REMOTE" "docker info --format '{{.LoggingDriver}}'"

echo ""
echo "=== Docker Desktop installation complete ==="
echo "Note: Reboot test (verification #5 from issue) should be done manually"
