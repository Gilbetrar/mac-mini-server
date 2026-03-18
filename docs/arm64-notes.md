# ARM64 Deployment Notes — OpenClaw on Mac Mini

## Overview

OpenClaw was migrated from EC2 (x86_64) to Mac Mini (ARM64/Apple Silicon). Both the main
gateway image and sandbox-browser sidecar run natively on ARM64 — no QEMU emulation needed.

## Images Built

| Image | Tag | Base | Size |
|-------|-----|------|------|
| `openclaw` | `local` | `node:24-bookworm` | ~4.5 GB |
| `openclaw-sandbox-browser` | `bookworm-slim` | `debian:bookworm-slim` | ~1.5 GB |

## Build Commands

```bash
# Main gateway image (from cloned repo at ~/services/openclaw/repo)
cd ~/services/openclaw/repo
git checkout v2026.3.12
docker build -t openclaw:local --build-arg OPENCLAW_INSTALL_BROWSER=1 .

# Sandbox-browser image (custom build with CDP proxy)
cd ~/services/openclaw/sandbox-browser-custom
docker build -t openclaw-sandbox-browser:bookworm-slim .
```

## ARM64 Compatibility

- **Main Dockerfile**: Multi-stage build handles ARM64 natively. The `pnpm canvas:a2ui:bundle`
  step may fail under QEMU but succeeds natively on ARM64 — the Dockerfile stubs it gracefully.
- **Sandbox-browser**: Debian `chromium` package (v146) works on ARM64 without issues.
- **Playwright browsers**: The x86_64 Playwright browsers from EC2 export are incompatible.
  Deleted them from `.openclaw/.playwright-browsers`. The main image has ARM64 Playwright
  browsers installed via `OPENCLAW_INSTALL_BROWSER=1` build arg.
- **gog binary**: The x86_64 Linux `gog` binary from EC2 cannot be bind-mounted into the
  ARM64 container. The gogcli config directory is mounted instead; a Linux ARM64 gog binary
  will need to be installed for Gmail Pub/Sub (issue #33/#34).

## Version Pinning

Using `v2026.3.12` instead of latest `main` due to plugin validation regression on HEAD
(extension entries "escaping package directory" errors). The config from EC2 works correctly
with v2026.3.12.

## Sandbox-Browser Custom Build

The upstream sandbox-browser entrypoint uses `socat` for CDP port forwarding, which doesn't
rewrite Host headers. Chromium rejects non-localhost/non-IP Host headers on DevTools endpoints.
The custom build includes:

- `cdp-host-proxy.py` — Python TCP proxy that rewrites Host headers and CDP response URLs
- `entrypoint.sh` — Custom entrypoint with `--no-sandbox` flag and CDP proxy integration

Files in `~/services/openclaw/sandbox-browser-custom/`.

## Config Changes for v2026.3.12

The EC2 config required these updates for the new version:

1. `gateway.controlUi.dangerouslyAllowHostHeaderOriginFallback: true` — required when
   binding to LAN (not loopback)
2. `channels.telegram.streamMode` renamed to `channels.telegram.streaming` (doctor fix)
3. Disabled problematic extensions in `plugins.entries` (acpx, diagnostics-otel, etc.)

## Docker Desktop on Mac Mini

Docker Desktop must be running for containers to work. It auto-starts on GUI login but
not via SSH. To start without GUI:

```bash
nohup /Applications/Docker.app/Contents/MacOS/com.docker.backend --start-docker-desktop > /dev/null 2>&1 &
```

## Directory Layout (Mac Mini)

```
~/services/openclaw/
├── .openclaw/              # Config + data (restored from EC2 export)
├── .config/gogcli/         # Google OAuth keyring
├── .env                    # Environment variables
├── docker-compose.yml      # Container orchestration
├── repo/                   # Cloned OpenClaw source (build context)
└── sandbox-browser-custom/ # Custom sandbox-browser build files
```
