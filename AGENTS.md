# Agent Instructions — mac-mini-server

## Before Starting Work

1. Check current branch: `git branch --show-current`
2. Check for uncommitted changes: `git status --short`
3. Report git state and ask where to work
4. Check open issues: `gh issue list --repo Gilbetrar/mac-mini-server`

## Git Conventions

- Work directly on `main` (no feature branches)
- Reference issues in commits: `feat: ... Part of #N` or `docs: ... Closes #N`
- Issues use the `migration` label, sequential numbering (#1–#13)

## Key References

- **LEARNINGS.md** — Source of truth for operational patterns. Read this first. Keep it under 100 lines.
- **SESSION_LOG.md** — Append-only history. Add an entry after substantial work.
- **docs/** — Service-specific docs. Update when service state changes.

## Mac Mini Access

- SSH: `ssh mac-mini` (user `ben`, key `~/.ssh/mac-mini`)
- Services root: `~/services/` on the Mac Mini
- Caddy config: `~/services/config/Caddyfile`
- Cloudflare token: `~/services/config/.cloudflare-token`

## Common Tasks

**Add a new service:** See LEARNINGS.md "Service Routing" section — add Caddy host route + Cloudflare CNAME.

**Deploy email worker changes:** `cd email-worker && npx wrangler deploy`

**Check service health:** `ssh mac-mini "curl -s localhost:<port>/health"`

## GitHub Account

This repo belongs to `Gilbetrar`. Before any GitHub operation:
```bash
gh auth switch -u Gilbetrar
```
