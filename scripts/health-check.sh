#!/bin/bash
# Health check script for Mac Mini services
# Checks all running services and sends Telegram alerts on failure.
# Idempotent: tracks failure state to avoid duplicate alerts.

set -euo pipefail

# --- Configuration ---
STATE_DIR="$HOME/services/data/health-check"
ALERT_ENV="$HOME/services/config/alerts/telegram.env"
LOG_FILE="$HOME/services/data/health-check/health-check.log"

# Create state directory if needed
mkdir -p "$STATE_DIR"

# Load Telegram credentials
if [[ ! -f "$ALERT_ENV" ]]; then
    echo "$(date -Iseconds) ERROR: Missing $ALERT_ENV" >> "$LOG_FILE"
    exit 1
fi
source "$ALERT_ENV"

# --- Helper functions ---

log() {
    echo "$(date -Iseconds) $1" >> "$LOG_FILE"
}

send_telegram() {
    local message="$1"
    curl -s -X POST \
        "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_CHAT_ID}" \
        -d text="${message}" \
        -d parse_mode="Markdown" \
        > /dev/null 2>&1
}

# Check a service and manage alert state.
# Args: $1=name, $2=check_command (eval'd), $3=description
check_service() {
    local name="$1"
    local check_cmd="$2"
    local description="$3"
    local state_file="$STATE_DIR/${name}.failing"

    if eval "$check_cmd" > /dev/null 2>&1; then
        # Service is healthy
        if [[ -f "$state_file" ]]; then
            # Was failing, now recovered
            local down_since
            down_since=$(cat "$state_file")
            rm -f "$state_file"
            send_telegram "✅ *RECOVERED:* ${description}
Was down since: ${down_since}"
            log "RECOVERED: $name"
        fi
        log "OK: $name"
    else
        # Service is down
        if [[ ! -f "$state_file" ]]; then
            # First failure — alert and record
            echo "$(date -Iseconds)" > "$state_file"
            send_telegram "🚨 *DOWN:* ${description}
Detected at: $(date '+%Y-%m-%d %H:%M:%S')"
            log "ALERT: $name is DOWN"
        else
            # Already alerted, skip duplicate
            log "STILL DOWN: $name (alerted at $(cat "$state_file"))"
        fi
    fi
}

# --- Service Checks ---

log "--- Health check started ---"

# 1. Caddy is running
check_service "caddy" \
    "pgrep -x caddy > /dev/null" \
    "Caddy reverse proxy is not running"

# 2. cloudflared is running
check_service "cloudflared" \
    "pgrep -x cloudflared > /dev/null" \
    "cloudflared tunnel is not running"

# 3. Caddy responds to HTTP requests
check_service "caddy-http" \
    "curl -sf -o /dev/null -m 5 http://localhost:80" \
    "Caddy is not responding on port 80"

# 4. Anki Renderer responds
check_service "anki-renderer" \
    "curl -sf -o /dev/null -m 10 -H 'Host: anki-renderer.bjblabs.com' http://localhost:80" \
    "Anki Renderer (anki-renderer.bjblabs.com) is not responding"

# 5. OpenClaw gateway responds
check_service "openclaw-gateway" \
    "curl -sf -o /dev/null -m 10 -H 'Host: openclaw.bjblabs.com' http://localhost:80" \
    "OpenClaw gateway (openclaw.bjblabs.com) is not responding"

# 6. OpenClaw Docker containers are running
check_service "openclaw-docker" \
    "docker ps --filter 'name=openclaw-openclaw-gateway' --filter 'status=running' -q | grep -q ." \
    "OpenClaw Docker containers are not running"

# 7. Legal Podcast service responds
check_service "legal-podcast" \
    "curl -sf -o /dev/null -m 10 http://localhost:9002/health" \
    "Legal Podcast service (port 9002) is not responding"

# 8. Legal Podcast Docker container is running
check_service "legal-podcast-docker" \
    "docker ps --filter 'name=legal-podcast' --filter 'status=running' -q | grep -q ." \
    "Legal Podcast Docker container is not running"

# 9. Deploy webhook is running (port 9001)
check_service "deploy-webhook" \
    "curl -sf -o /dev/null -m 5 http://localhost:9001 || [[ \$? -eq 22 ]]" \
    "Anki Renderer deploy webhook (port 9001) is not responding"

# 10. External check — verify Cloudflare tunnel is routing traffic
check_service "cloudflare-tunnel" \
    "curl -sf -o /dev/null -m 15 https://anki-renderer.bjblabs.com" \
    "Cloudflare tunnel not routing (anki-renderer.bjblabs.com unreachable externally)"

log "--- Health check complete ---"

# Trim log file if over 10000 lines
if [[ -f "$LOG_FILE" ]] && [[ $(wc -l < "$LOG_FILE") -gt 10000 ]]; then
    tail -5000 "$LOG_FILE" > "${LOG_FILE}.tmp"
    mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi
