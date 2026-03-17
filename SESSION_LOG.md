# Session Log

Raw session history for the mac-mini-server project.

---

## Agent Session - Issue #1

**Worked on:** Issue #1 - macOS server hardening

**What I did:**
- Verified SSH connectivity to Mac Mini (`ssh mac-mini`)
- Disabled computer sleep via `systemsetup -setcomputersleep Never`
- Disabled display/disk sleep via `pmset -a displaysleep 0 sleep 0 disksleep 0`
- Enabled auto-restart after power failure via `systemsetup -setrestartpowerfailure on`
- Enabled macOS firewall via `socketfilterfw --setglobalstate on`
- Created directory structure: `~/services/`, `~/services/config/`, `~/services/data/`, `~/services/backups/`
- All 5 verification checks from the issue passed

**What I learned:**
- `systemsetup` emits Error:-99 on modern macOS (Sequoia 26.x) — cosmetic, settings apply correctly
- `socketfilterfw --setglobalstate on` produces no output on success
- The remote user is `ben` (lowercase) even though the Mac shows "Ben" in its hostname

**Codebase facts discovered:**
- Repo was completely empty (no commits) — this was the first session
- 13 open issues, all labeled `migration`, numbered 1-13
- Issues designed to be worked sequentially

**Mistakes made:**
- None

---

## Agent Session - Issue #2

**Worked on:** Issue #2 - Install Docker Desktop

**What I did:**
- Downloaded Docker Desktop ARM64 .dmg from Docker's website
- Installed to /Applications via cp -R from mounted .dmg
- Ran the installer with `--accept-license --user ben` to complete first-run setup
- Created CLI symlinks in /usr/local/bin (docker, kubectl, credential helpers)
- Created `~/.zshenv` with PATH export so SSH non-interactive sessions can find docker
- Configured resource limits: 4 CPUs, 8GB RAM, 64GB disk via settings-store.json
- Configured log rotation via daemon.json (json-file, 10MB max, 3 files)
- Added Docker Desktop as macOS login item for auto-start on boot
- Removed `credsStore: desktop` from Docker config.json to fix keychain issues in SSH
- Erased stored Docker Hub credentials from keychain credential store
- Verified: docker --version, aarch64 architecture, hello-world runs, resource limits applied

**What I learned:**
- Docker Desktop for Mac uses `~/Library/Group Containers/group.com.docker/settings-store.json` for settings
- SSH non-interactive sessions don't source .zshrc — need .zshenv for PATH
- Docker Desktop's `credsStore: desktop` uses macOS keychain, which is locked in SSH sessions
- Must erase stored keychain credentials AND remove credsStore from config for SSH docker pull to work
- The Docker Desktop installer at `/Applications/Docker.app/Contents/MacOS/install` has useful subcommands: `config`, `socket-symlink-on-startup`, etc.
- `AutoStart: true` in settings-store.json plus macOS login item ensures Docker starts after reboot
- Docker Desktop settings key names are case-sensitive: `Cpus` (not `CPUs`) is what gets written to settings

**Codebase facts discovered:**
- Previous agent created scripts/01-*.sh pattern — following with scripts/02-install-docker.sh
- No package.json/build system — this is pure infrastructure/documentation repo

**Mistakes made:**
- Initially tried to run docker before the install completed — Docker Desktop needs GUI-based first run or `install --accept-license`
- Credential helper keychain issue took several attempts to diagnose — the fix was removing stored credentials AND the credsStore config
