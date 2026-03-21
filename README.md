# Mac Mini Server

Infrastructure repo for Ben's M4 Mac Mini — the self-hosted platform that replaced AWS for all services.

## Live Services

| Service | URL | Backend |
|---------|-----|---------|
| Anki Renderer | `anki-renderer.bjblabs.com` | Caddy file_server, CI/CD webhook |
| OpenClaw | `openclaw.bjblabs.com` | Docker (gateway + sandbox-browser) |
| Legal Podcast | `legalpodcast.bjblabs.com` | Docker (Express) + Caddy static |
| NocoDB | `data.bjblabs.com` | Docker, Zero Trust protected |

All traffic: Internet → Cloudflare (DNS + Zero Trust) → cloudflared tunnel → Caddy (:80) → service

## Key Files

| File | Purpose |
|------|---------|
| `LEARNINGS.md` | **Primary agent reference.** Operational patterns, service routing, gotchas. Keep under 100 lines. |
| `SESSION_LOG.md` | Chronological record of agent work sessions. Append-only. |
| `AGENTS.md` | How to work on this project (git conventions, issue workflow). |
| `docs/` | Service-specific documentation (email routing, Zero Trust, ARM64 notes, etc.) |
| `config/` | Caddyfile, cloudflared config, launchd plists, restore procedure |
| `scripts/` | Health checks, backups, deploy webhook |
| `email-worker/` | Cloudflare Email Worker source (Wrangler) |
| `services/` | Docker Compose templates for deployable services |

## Quick Start (Disaster Recovery)

See `config/restore-procedure.md` for full restore steps. Backups run daily (local + S3 offsite).
