# Cloudflare Zero Trust Setup — bjblabs.com

## Overview

Cloudflare Zero Trust (free tier, up to 50 users) provides edge-level authentication for browser-facing services hosted on the Mac Mini. Users authenticate via One-Time PIN (email OTP) before reaching the service.

**Status:** Enabled 2026-03-21 (Free plan, up to 50 users). Team domain: `bjblabs.cloudflareaccess.com`.

### Protected Applications

| Application | Domain | App ID | Service Token |
|-------------|--------|--------|---------------|
| NocoDB | `data.bjblabs.com` | `c1b4abb1-0184-4e6b-b812-2b226dc41921` | `NocoDB MCP` (`4e9b0541-f78e-4fae-8765-793cff53ac91`) |

## Architecture

```
Browser → Cloudflare Edge (Zero Trust auth check) → Cloudflare Tunnel → Caddy → Service
```

Zero Trust sits between Cloudflare's edge and the tunnel. If a request matches an Access policy, Cloudflare challenges the user for authentication before forwarding to the tunnel.

## Initial Setup (COMPLETED 2026-03-21)

Setup was completed via the Cloudflare dashboard:
- Free plan selected ($0/month, up to 50 users)
- Team domain: `bjblabs.cloudflareaccess.com`
- Auth method: One-time PIN (email OTP, default)
- Billing: PayPal on file

**Optional:** To allow agents to create Access applications via API, edit the "Claude Code" API token at https://dash.cloudflare.com/profile/api-tokens and add **Account** → **Access: Apps and Policies** → **Edit**.

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

## NocoDB (data.bjblabs.com)

**Created:** 2026-03-21 via API.

- **Access App ID:** `c1b4abb1-0184-4e6b-b812-2b226dc41921`
- **Policy:** Allow Ben (`ben.bateman.email@gmail.com`, email OTP)
- **Policy ID:** `a669b73e-3d7d-45eb-adca-4c53f7308d08`
- **Session duration:** 24 hours
- **Service Token:** `NocoDB MCP` (non-expiring, ID: `4e9b0541-f78e-4fae-8765-793cff53ac91`)
- **Service Token Policy ID:** `8d8eb76a-4e31-4ff0-b8a7-e1cd032faa8a` (non_identity decision)
- **Credentials:** `~/services/nocodb/.cf-service-token` (chmod 600)

## Related Files

- Tunnel config: `~/services/config/cloudflared/config.yml`
- Caddyfile: `~/services/config/Caddyfile`
- Cloudflare API token: `~/services/config/.cloudflare-token`
