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

## Gotchas

- `systemsetup` commands emit `Error:-99` on modern macOS — this is cosmetic, settings still apply
- The firewall `--setglobalstate on` command produces no output on success
- Remote user is `ben` (lowercase), not `Ben` — despite the Mac hostname showing "Ben"

## Repo Conventions

- All work tracked via GitHub Issues with `migration` label
- Issues are numbered sequentially and should be worked in order
- Direct commits to `main` (no feature branches for autonomous work)
- Commit messages reference issue numbers: `feat: ... Part of #N` or `Closes #N`
