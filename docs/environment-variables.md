# Environment Variables — OpenClaw EC2 Deployment

Variables from `~/openclaw/.env` on EC2. These must be recreated on the Mac Mini.

## Required Variables

| Variable | Description | Sensitive | Notes |
|----------|-------------|-----------|-------|
| `OPENCLAW_CONFIG_DIR` | Path to .openclaw config directory | No | Update to Mac Mini path |
| `OPENCLAW_WORKSPACE_DIR` | Path to workspace directory | No | Update to Mac Mini path |
| `OPENCLAW_GATEWAY_TOKEN` | Token for gateway API authentication | **Yes** | Can reuse or regenerate |
| `OPENCLAW_GATEWAY_PORT` | Gateway HTTP port | No | Default: 18789 |
| `OPENCLAW_BRIDGE_PORT` | Bridge port | No | Default: 18790 |
| `OPENCLAW_GATEWAY_BIND` | Network bind mode | No | Set to `lan` |
| `OPENCLAW_IMAGE` | Docker image name | No | `openclaw:local` |
| `GH_TOKEN` | GitHub personal access token | **Yes** | For GitHub API access |

## Auth Variables (Require Regeneration)

These session keys expire and will need to be regenerated on the Mac Mini via `openclaw setup-token`.

| Variable | Description | Notes |
|----------|-------------|-------|
| `CLAUDE_AI_SESSION_KEY` | Claude AI session token | Empty at export — needs regeneration |
| `CLAUDE_WEB_SESSION_KEY` | Claude web session token | Empty at export — needs regeneration |
| `CLAUDE_WEB_COOKIE` | Claude web cookie | Empty at export — needs regeneration |

## Docker Compose Environment (set in docker-compose.yml)

These are set directly in `docker-compose.yml`, not in `.env`:

| Variable | Description | Notes |
|----------|-------------|-------|
| `GOG_KEYRING_PASSWORD` | Password for gogcli keyring | Hardcoded: `openclaw-gog` |
| `GOG_ACCOUNT` | Google account for gogcli | `ben.bateman.email@gmail.com` |
| `PLAYWRIGHT_BROWSERS_PATH` | Playwright browser install path | Maps to .openclaw/.playwright-browsers |
| `HOME` | Container home directory | `/home/node` |
| `TERM` | Terminal type | `xterm-256color` |
| `OPENCLAW_BROWSER_CDP_PORT` | Chrome DevTools Protocol port (sandbox) | `9222` |
| `OPENCLAW_BROWSER_HEADLESS` | Run browser headless (sandbox) | `1` |
| `OPENCLAW_BROWSER_ENABLE_NOVNC` | Enable noVNC (sandbox) | `0` |

## Unused Variables

| Variable | Description | Notes |
|----------|-------------|-------|
| `OPENCLAW_EXTRA_MOUNTS` | Additional volume mounts | Empty |
| `OPENCLAW_HOME_VOLUME` | Custom home volume | Empty |
| `OPENCLAW_DOCKER_APT_PACKAGES` | Extra apt packages for Docker | Empty |

## Migration Notes

1. **Path updates:** `OPENCLAW_CONFIG_DIR` and `OPENCLAW_WORKSPACE_DIR` must use Mac Mini paths (e.g., `/Users/ben/.openclaw/`)
2. **Token regeneration:** Claude session keys are empty and need `openclaw setup-token` (Issue #35)
3. **GH_TOKEN:** Existing PAT should work cross-platform; verify scope if issues arise
4. **Architecture:** Images are x86_64 on EC2 — must rebuild for ARM64 on Mac Mini
