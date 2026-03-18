# Claude Setup Token — OpenClaw on Mac Mini

## How Auth Works

OpenClaw stores Anthropic auth tokens in **auth-profiles.json**, not environment variables. The legacy env vars (`CLAUDE_AI_SESSION_KEY`, `CLAUDE_WEB_SESSION_KEY`, `CLAUDE_WEB_COOKIE`) are not used and were removed from `.env`.

Auth profile location (inside container):
```
~/.openclaw/agents/main/agent/auth-profiles.json
```

On host (via bind mount):
```
~/services/openclaw/.openclaw/agents/main/agent/auth-profiles.json
```

## Current Configuration

- **Default model:** `anthropic/claude-opus-4-6`
- **Fallback #1:** `anthropic/claude-sonnet-4-5-20250929`
- **Fallback #2:** `anthropic/claude-haiku-4-5`
- **Auth type:** Token (stored in auth-profiles.json)

## Checking Auth Status

```bash
ssh mac-mini "docker compose -f ~/services/openclaw/docker-compose.yml exec openclaw-gateway openclaw models status"
```

Look for `Auth: yes` next to each model in `openclaw models list`.

## Regenerating a Token

If the token expires or stops working:

```bash
# Interactive setup (requires TTY — run from SSH session, not via ssh <cmd>)
ssh -t mac-mini "docker compose -f ~/services/openclaw/docker-compose.yml exec -it openclaw-gateway openclaw models auth add"

# Or paste a token directly
ssh mac-mini "docker compose -f ~/services/openclaw/docker-compose.yml exec openclaw-gateway openclaw models auth paste-token"

# Or run the provider's CLI auth flow (requires TTY)
ssh -t mac-mini "docker compose -f ~/services/openclaw/docker-compose.yml exec -it openclaw-gateway openclaw models auth setup-token"
```

After regeneration, verify all tiers work:

```bash
# Test default model
ssh mac-mini "docker compose -f ~/services/openclaw/docker-compose.yml exec openclaw-gateway openclaw agent --agent main --message 'Reply PONG' --json" | head -15

# Or send a test via Telegram
```

## Managing Models

```bash
# List all available models
ssh mac-mini "docker compose -f ~/services/openclaw/docker-compose.yml exec openclaw-gateway openclaw models list --all"

# Set default
ssh mac-mini "docker compose -f ~/services/openclaw/docker-compose.yml exec openclaw-gateway openclaw models set <model-id>"

# Add/remove fallbacks
ssh mac-mini "docker compose -f ~/services/openclaw/docker-compose.yml exec openclaw-gateway openclaw models fallbacks add <model-id>"
ssh mac-mini "docker compose -f ~/services/openclaw/docker-compose.yml exec openclaw-gateway openclaw models fallbacks remove <model-id>"
```

## Verified Working (2026-03-18)

All three Claude tiers tested via `openclaw agent` CLI:
- `anthropic/claude-opus-4-6` — responded successfully
- `anthropic/claude-sonnet-4-5-20250929` — responded successfully
- `anthropic/claude-haiku-4-5` — responded successfully
