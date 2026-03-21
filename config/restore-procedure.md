# Restore Procedure

## Quick Restore (from local backup)

```bash
# 1. List available backups
ls -la ~/services/backups/daily/
ls -la ~/services/backups/weekly/

# 2. Pick a backup (most recent daily, or specific date)
BACKUP=~/services/backups/daily/backup-2026-03-20.tar.gz

# 3. Preview contents
tar tzf "$BACKUP" | head -20

# 4. Restore to a temp directory first
mkdir -p /tmp/restore
tar xzf "$BACKUP" -C /tmp/restore

# 5. Compare and copy what you need
diff /tmp/restore/config/Caddyfile ~/services/config/Caddyfile
cp /tmp/restore/config/Caddyfile ~/services/config/Caddyfile

# 6. Or restore everything (CAUTION: overwrites current config/data)
# tar xzf "$BACKUP" -C ~/services/

# 7. Reload affected services
caddy reload --config ~/services/config/Caddyfile
```

## Restore from S3 (if Mac Mini local backups lost)

```bash
# 1. List available S3 backups
aws s3 ls s3://bjblabs-backups-719390918663/mac-mini/daily/
aws s3 ls s3://bjblabs-backups-719390918663/mac-mini/weekly/

# 2. Download a backup
aws s3 cp s3://bjblabs-backups-719390918663/mac-mini/daily/backup-2026-03-20.tar.gz /tmp/

# 3. Extract and restore (same as local steps 3-7 above)
mkdir -p /tmp/restore
tar xzf /tmp/backup-2026-03-20.tar.gz -C /tmp/restore
```

## Full Disaster Recovery (new Mac Mini)

1. Install Homebrew, Docker Desktop, Caddy, cloudflared, awscli
2. Create `~/services/{config,data,backups,scripts}` directories
3. Download latest backup from S3 (see above)
4. Extract to `~/services/`
5. Clone repos: `mac-mini-server`, `openclaw-deployment`
6. Deploy scripts from mac-mini-server repo to `~/services/scripts/`
7. Deploy launchd plists from mac-mini-server repo to `~/Library/LaunchAgents/`
8. Start services: Docker containers, Caddy, cloudflared
9. Update Cloudflare tunnel config if hostname changed

## What's Backed Up

| Directory | Contents |
|-----------|----------|
| `config/` | Caddyfile, cloudflared config, Telegram creds, docs |
| `data/` | OpenClaw data, health check state (logs excluded) |

## What's NOT Backed Up (by design)

- Log files (transient, regenerated)
- Docker images (pulled from registries)
- Git repos (re-cloned from GitHub)
- AWS credentials (`~/.aws/` — re-create from IAM)
- Secrets stored outside `~/services/`
