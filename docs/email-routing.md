# Cloudflare Email Routing — bjblabs.com

## Overview

Cloudflare Email Routing handles inbound email for bjblabs.com. It replaces AWS SES email receiving.

- **Free tier** — no cost
- **No servers to manage** — Cloudflare handles all MX/SMTP
- **Forwards to Gmail** — all mail ultimately lands in ben.bateman.email@gmail.com

## Current Routes

| Address | Destination | Purpose |
|---------|-------------|---------|
| `podcast@bjblabs.com` | `ben.bateman.email@gmail.com` | Legal Podcast inbound email |
| `*@bjblabs.com` (catch-all) | `ben.bateman.email@gmail.com` | Catch all other addresses |

## Adding a New Email Route

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select **bjblabs.com** zone
3. Go to **Email** > **Email Routing** > **Routing Rules**
4. Click **Create address**
5. Enter the custom address (e.g., `notifications@bjblabs.com`)
6. Set the destination (e.g., `ben.bateman.email@gmail.com`)
7. Click **Save**

The route takes effect immediately — no DNS changes needed.

## Removing a Route

1. Go to **Email** > **Email Routing** > **Routing Rules**
2. Find the address
3. Click the three dots menu > **Delete**

## How It Works

Cloudflare Email Routing uses MX records pointing to Cloudflare's mail servers. When an email arrives:

1. Cloudflare receives the email via MX records
2. Matches the recipient against routing rules (specific addresses first, then catch-all)
3. Forwards the email to the configured destination

## MX Records (Managed by Cloudflare)

When Email Routing is enabled, Cloudflare automatically adds the required MX records:

| Type | Name | Value | Priority |
|------|------|-------|----------|
| MX | bjblabs.com | `isaac.mx.cloudflare.net` | 69 |
| MX | bjblabs.com | `linda.mx.cloudflare.net` | 12 |
| MX | bjblabs.com | `amir.mx.cloudflare.net` | 6 |

These take effect once bjblabs.com nameservers point to Cloudflare.

## Email Sending

Email **sending** is NOT handled by Cloudflare Email Routing. For outbound email, services use Resend (configured per-service). See each service's documentation for sending configuration.

## Troubleshooting

- **Email not arriving?** Check that nameservers have been changed to Cloudflare (DNS cutover). Email routing only works when Cloudflare controls the MX records.
- **Destination not verified?** The destination email must be verified in Cloudflare. A verification email is sent the first time you add a new destination address.
- **Catch-all not working?** Ensure the catch-all rule is enabled under Email Routing > Routing Rules.
