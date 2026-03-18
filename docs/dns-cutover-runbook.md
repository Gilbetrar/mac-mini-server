# DNS Cutover Runbook — bjblabs.com

## Overview

bjblabs.com DNS was migrated from AWS Route 53 to Cloudflare on 2026-03-17.

## What Was Done

### 1. Record Replication (2026-03-17)

All 14 active Route 53 records were replicated in Cloudflare DNS before the nameserver change. See `route53-export.json` for the full export (16 records including NS and SOA).

### 2. Nameserver Change (2026-03-17)

Nameservers updated at the domain registrar (AWS Route 53 Domains):

```
ximena.ns.cloudflare.com
yew.ns.cloudflare.com
```

Command used:
```bash
aws route53domains update-domain-nameservers --domain-name bjblabs.com \
  --nameservers Name=ximena.ns.cloudflare.com Name=yew.ns.cloudflare.com
```

### 3. Service CNAME Updates

| Subdomain | Old Target | New Target | Date |
|-----------|-----------|------------|------|
| openclaw.bjblabs.com | (new record) | tunnel CNAME, proxied | 2026-03-18 |
| anki-renderer.bjblabs.com | d25ba80ruv6hnq.cloudfront.net | tunnel CNAME, proxied | 2026-03-18 |

Tunnel CNAME target: `e4978b52-8394-4f5b-b715-ee96a5a9e641.cfargotunnel.com`

### 4. Email Routing (2026-03-18)

MX records switched from AWS SES to Cloudflare Email Routing:
- `podcast@bjblabs.com` → `ben.bateman.email@gmail.com`
- Catch-all → `ben.bateman.email@gmail.com`

## Verification

```bash
# Check nameservers
dig bjblabs.com NS +short

# Check tunnel routing
curl -s -o /dev/null -w "%{http_code}" https://anki-renderer.bjblabs.com
curl -s -o /dev/null -w "%{http_code}" https://openclaw.bjblabs.com

# Check email MX
dig MX bjblabs.com +short
```

## Rollback

Route 53 hosted zone `Z0806990T0ZB8GBKDCD9` is preserved. To roll back:

```bash
aws route53domains update-domain-nameservers --domain-name bjblabs.com \
  --nameservers Name=ns-1234.awsdns-12.org Name=ns-5678.awsdns-56.co.uk \
  Name=ns-9012.awsdns-90.com Name=ns-3456.awsdns-34.net
```

(Replace with actual Route 53 NS values from the hosted zone.)

Route 53 zone eligible for deletion after 2026-03-31 (2 weeks stable).
