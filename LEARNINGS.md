# LEARNINGS.md — Mac Mini Server

Distilled patterns for autonomous agents. Keep under 100 lines.

## Project Overview

This repo manages the migration of Ben's services from AWS to a self-hosted M4 Mac Mini.
The Mac Mini is on the local network, accessible via `ssh mac-mini`.

## SSH Access

- **Host alias:** `ssh mac-mini` (configured in `~/.ssh/config` on Ben's laptop)
- **Remote user:** `ben` (home dir: `/Users/ben`)
- **Sudo:** available, use for system commands (`systemsetup`, `pmset`, `socketfilterfw`)

## Directory Structure (on Mac Mini)

- `~/services/` — root for all hosted services
- `~/services/config/` — service configuration files
- `~/services/data/` — persistent service data
- `~/services/backups/` — backup files

## macOS System Settings Applied

- Sleep disabled: `sudo systemsetup -setcomputersleep Never` + `sudo pmset -a displaysleep 0 sleep 0 disksleep 0`
- Auto-restart after power failure: `sudo systemsetup -setrestartpowerfailure on`
- Firewall enabled: `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on`

## Docker Desktop

- Installed at `/Applications/Docker.app`, CLI symlinks in `/usr/local/bin/`
- Settings file: `~/Library/Group Containers/group.com.docker/settings-store.json`
- Daemon config: `~/.docker/daemon.json` (log rotation configured)
- Resource limits: 4 CPUs, 8GB RAM (half the M4's resources)
- Auto-starts on login (login item + AutoStart setting)
- `credsStore` removed from `~/.docker/config.json` — required for SSH docker pulls to work

## Caddy Reverse Proxy

- Installed via Homebrew at `/opt/homebrew/bin/caddy` (v2.11.2)
- Caddyfile: `~/services/config/Caddyfile` (version-controlled in repo at `config/Caddyfile`)
- launchd service: `~/Library/LaunchAgents/com.caddy.server.plist` (version-controlled in `config/`)
- Data/logs: `~/services/data/caddy/` (XDG_DATA_HOME)
- Reload config: `caddy reload --config ~/services/config/Caddyfile`
- Validate config: `caddy validate --config ~/services/config/Caddyfile`

## Gotchas

- `systemsetup` commands emit `Error:-99` on modern macOS — this is cosmetic, settings still apply
- The firewall `--setglobalstate on` command produces no output on success
- Remote user is `ben` (lowercase), not `Ben` — despite the Mac hostname showing "Ben"
- SSH non-interactive sessions have minimal PATH — `~/.zshenv` adds `/usr/local/bin` and `/opt/homebrew/bin`
- Docker Desktop `credsStore: desktop` uses macOS keychain, fails in SSH sessions (keychain locked)
- Docker Desktop installer: `/Applications/Docker.app/Contents/MacOS/install --accept-license --user ben`

## Repo Conventions

- All work tracked via GitHub Issues with `migration` label
- Issues are numbered sequentially and should be worked in order
- Direct commits to `main` (no feature branches for autonomous work)
- Commit messages reference issue numbers: `feat: ... Part of #N` or `Closes #N`
