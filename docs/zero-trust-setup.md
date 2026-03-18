# Cloudflare Zero Trust Setup — bjblabs.com

## Overview

Cloudflare Zero Trust (free tier, up to 50 users) provides edge-level authentication for browser-facing services hosted on the Mac Mini. Users authenticate via One-Time PIN (email OTP) before reaching the service.

**When to set this up:** When the first browser-facing service is deployed (e.g., a web UI). Services that only expose webhooks or API endpoints with application-level auth (like OpenClaw) do NOT need Zero Trust.

## Architecture

```
Browser → Cloudflare Edge (Zero Trust auth check) → Cloudflare Tunnel → Caddy → Service
```

Zero Trust sits between Cloudflare's edge and the tunnel. If a request matches an Access policy, Cloudflare challenges the user for authentication before forwarding to the tunnel.

## Initial Setup (Dashboard — One Time)

These steps must be done in the Cloudflare dashboard by a human.

### 1. Enable Zero Trust

1. Go to https://one.dash.cloudflare.com/
2. Select account → **Zero Trust** in left sidebar
3. Choose **Free plan** (up to 50 users)
4. Set team domain: `bjblabs.cloudflareaccess.com`

### 2. Configure Authentication Method

1. In Zero Trust dashboard → **Settings** → **Authentication**
2. **One-time PIN** should be enabled by default (verify it's there)
3. No Google OAuth needed — OTP is simpler for single-user

### 3. Update API Token (Optional)

To allow agents to create Access applications and policies via API:

1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Edit the existing `mac-mini-server` token
3. Add permission: **Account** → **Access: Apps and Policies** → **Edit**
4. Save

## Adding a Protected Service

Once Zero Trust is enabled, follow these steps to protect a new service:

### Via Dashboard

1. Zero Trust dashboard → **Access** → **Applications**
2. Click **Add an application** → **Self-hosted**
3. Configure:
   - **Application name:** `<service-name>`
   - **Session duration:** 24 hours (or preferred)
   - **Application domain:** `<subdomain>.bjblabs.com`
4. Add policy:
   - **Policy name:** `Allow Ben`
   - **Action:** Allow
   - **Include rule:** Emails — `ben.bateman.email@gmail.com`
5. Save

### Via API (if token has Access permissions)

```bash
CF_TOKEN=$(cat ~/services/config/.cloudflare-token)
CF_ACCT="95f53250a929e155644f51e03fc7c910"

# Create Access application
curl -X POST "https://api.cloudflare.com/client/v4/accounts/${CF_ACCT}/access/apps" \
  -H "Authorization: Bearer ${CF_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "<service-name>",
    "domain": "<subdomain>.bjblabs.com",
    "type": "self_hosted",
    "session_duration": "24h",
    "auto_redirect_to_identity": true
  }'

# Create Access policy (use app_id from response above)
curl -X POST "https://api.cloudflare.com/client/v4/accounts/${CF_ACCT}/access/apps/<app_id>/policies" \
  -H "Authorization: Bearer ${CF_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Allow Ben",
    "decision": "allow",
    "include": [
      {
        "email": {
          "email": "ben.bateman.email@gmail.com"
        }
      }
    ]
  }'
```

### Service Tokens (Machine-to-Machine)

If a protected service also has endpoints consumed by other services (not browsers), create a service token:

1. Zero Trust dashboard → **Access** → **Service Auth** → **Service Tokens**
2. Create token, save `CF-Access-Client-Id` and `CF-Access-Client-Secret`
3. Calling services include these headers to bypass the auth challenge

## Testing

1. Navigate to the protected subdomain in a browser
2. You should see a Cloudflare login page at `bjblabs.cloudflareaccess.com`
3. Enter `ben.bateman.email@gmail.com`
4. Check email for the OTP code
5. Enter code → should be redirected to the service

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No login page appears | Check Access application domain matches DNS record |
| OTP email not received | Check spam; verify email address in policy |
| 403 after login | Check policy includes your email |
| Tunnel not reached after auth | Verify tunnel is running: `ssh mac-mini "pgrep cloudflared"` |

## Related Files

- Tunnel config: `~/services/config/cloudflared/config.yml`
- Caddyfile: `~/services/config/Caddyfile`
- Cloudflare API token: `~/services/config/.cloudflare-token`
