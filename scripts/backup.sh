#!/bin/bash
# Backup script for Mac Mini services
# Creates local backups with rotation, then syncs off-site to S3.
# Schedule: daily via launchd

set -euo pipefail

# --- Configuration ---
BACKUP_DIR="$HOME/services/backups"
CONFIG_DIR="$HOME/services/config"
DATA_DIR="$HOME/services/data"
LOG_FILE="$BACKUP_DIR/backup.log"
S3_BUCKET="s3://bjblabs-backups-719390918663/mac-mini"
ALERT_ENV="$HOME/services/config/alerts/telegram.env"

# Retention
DAILY_KEEP=7
WEEKLY_KEEP=4

# --- Helper functions ---

log() {
    echo "$(date -Iseconds) $1" >> "$LOG_FILE"
}

send_telegram() {
    if [[ -f "$ALERT_ENV" ]]; then
        source "$ALERT_ENV"
        curl -s -X POST \
            "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_CHAT_ID}" \
            -d text="$1" \
            -d parse_mode="Markdown" \
            > /dev/null 2>&1
    fi
}

# --- Main ---

mkdir -p "$BACKUP_DIR/daily" "$BACKUP_DIR/weekly"

log "--- Backup started ---"

DATE=$(date +%Y-%m-%d)
DAY_OF_WEEK=$(date +%u)  # 1=Monday, 7=Sunday
DAILY_FILE="$BACKUP_DIR/daily/backup-${DATE}.tar.gz"

# Skip if today's backup already exists
if [[ -f "$DAILY_FILE" ]]; then
    log "Daily backup already exists for $DATE, skipping"
    exit 0
fi

# Create backup tarball (config + data, excluding large transient files)
TEMP_FILE="$BACKUP_DIR/.backup-in-progress.tar.gz"
trap 'rm -f "$TEMP_FILE"' EXIT

if tar czf "$TEMP_FILE" \
    -C "$HOME/services" \
    --exclude='data/health-check/health-check.log' \
    --exclude='data/anki-renderer-deploy.log' \
    --exclude='data/caddy/*.log' \
    --exclude='data/cloudflared/*.log' \
    config/ data/ 2>> "$LOG_FILE"; then
    mv "$TEMP_FILE" "$DAILY_FILE"
    BACKUP_SIZE=$(du -h "$DAILY_FILE" | cut -f1)
    log "Daily backup created: $DAILY_FILE ($BACKUP_SIZE)"
else
    log "ERROR: Failed to create backup tarball"
    send_telegram "🚨 *BACKUP FAILED:* Could not create daily backup tarball"
    exit 1
fi

# Weekly backup: copy Sunday's daily to weekly/
if [[ "$DAY_OF_WEEK" -eq 7 ]]; then
    WEEKLY_FILE="$BACKUP_DIR/weekly/backup-${DATE}.tar.gz"
    cp "$DAILY_FILE" "$WEEKLY_FILE"
    log "Weekly backup created: $WEEKLY_FILE"
fi

# --- Rotation ---

# Remove daily backups older than DAILY_KEEP days
find "$BACKUP_DIR/daily" -name "backup-*.tar.gz" -mtime +${DAILY_KEEP} -delete 2>/dev/null
DAILY_COUNT=$(find "$BACKUP_DIR/daily" -name "backup-*.tar.gz" | wc -l | tr -d ' ')
log "Daily backups retained: $DAILY_COUNT"

# Remove weekly backups beyond WEEKLY_KEEP (keep newest N)
WEEKLY_COUNT=$(find "$BACKUP_DIR/weekly" -name "backup-*.tar.gz" | wc -l | tr -d ' ')
if [[ "$WEEKLY_COUNT" -gt "$WEEKLY_KEEP" ]]; then
    REMOVE_COUNT=$((WEEKLY_COUNT - WEEKLY_KEEP))
    find "$BACKUP_DIR/weekly" -name "backup-*.tar.gz" -print0 | \
        xargs -0 ls -t | tail -${REMOVE_COUNT} | xargs rm -f
    log "Removed $REMOVE_COUNT old weekly backups"
fi
WEEKLY_COUNT=$(find "$BACKUP_DIR/weekly" -name "backup-*.tar.gz" | wc -l | tr -d ' ')
log "Weekly backups retained: $WEEKLY_COUNT"

# --- Off-site sync to S3 ---

if command -v aws &> /dev/null; then
    if aws s3 sync "$BACKUP_DIR/" "$S3_BUCKET/" \
        --exclude "*.log" \
        --exclude ".backup-in-progress*" \
        --delete \
        >> "$LOG_FILE" 2>&1; then
        log "S3 sync complete"
    else
        log "ERROR: S3 sync failed"
        send_telegram "⚠️ *BACKUP WARNING:* Local backup succeeded but S3 sync failed"
    fi
else
    log "WARNING: aws CLI not found, skipping S3 sync"
fi

log "--- Backup complete ($BACKUP_SIZE) ---"

# Trim log file if over 5000 lines
if [[ -f "$LOG_FILE" ]] && [[ $(wc -l < "$LOG_FILE") -gt 5000 ]]; then
    tail -2500 "$LOG_FILE" > "${LOG_FILE}.tmp"
    mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi
