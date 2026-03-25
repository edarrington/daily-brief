# daily-brief

A lightweight FastAPI + APScheduler service that delivers three automated email reports daily — a morning news brief, an evening news brief, and an Azure cost report — all sent via Microsoft Graph API.

---

## Scheduled Emails

| Email | Time (PT) | Description |
|---|---|---|
| Morning Brief | 7:00 AM | AI, cybersecurity, and world news from RSS feeds |
| Azure Cost Report | 8:00 AM | Month-to-date Azure spend by resource group |
| Evening Brief | 6:00 PM | AI, cybersecurity, and world news from RSS feeds |

---

## How the Daily Brief Works

### Overview

The morning and evening briefs aggregate headlines from nine RSS feeds across three categories and send them as a styled HTML email.

### RSS Sources

| Category | Sources |
|---|---|
| Artificial Intelligence | TechCrunch AI, The Verge AI, VentureBeat AI |
| Cybersecurity | Krebs on Security, Bleeping Computer, The Hacker News |
| World News | BBC World News, Reuters, NYT World |

### Flow

```
APScheduler (7am / 6pm PT)
  └─ build_brief("Morning" | "Evening")
       └─ rss_reader.fetch_category("ai" | "cybersecurity" | "world")
            └─ feedparser fetches each RSS feed
            └─ returns top 5 items per category (max 2 per feed)
       └─ Jinja2 renders templates/brief_email.html
  └─ mailer.send_email()
       └─ MSAL acquires Graph API token (client credentials)
       └─ POST /v1.0/users/{FROM_EMAIL}/sendMail
```

### Key Files

- `services/rss_reader.py` — fetches and parses RSS feeds, strips HTML from summaries
- `services/brief_builder.py` — assembles feed data and renders the email template
- `templates/brief_email.html` — styled HTML email template (inline CSS, table layout)
- `scheduler.py` — registers the 7am and 6pm cron jobs

---

## How the Azure Cost Report Works

### Overview

Every morning at 8am PT, the service queries the Azure Cost Management REST API for month-to-date spend, breaks it down by resource group, and emails a summary.

### Authentication

The service runs on Azure Container Apps with a **User-Assigned Managed Identity** (`id-daily-brief-prod`). It acquires an Azure management token directly from the Instance Metadata Service (IMDS) — no credentials stored in code or config.

```
IMDS endpoint (169.254.169.254)
  └─ returns short-lived Bearer token for management.azure.com
  └─ scoped to the managed identity's assigned roles
```

The managed identity has the **Cost Management Reader** role on the subscription, which allows it to query spend data but nothing else.

### Flow

```
APScheduler (8am PT)
  └─ azure_costs.fetch_costs()
       └─ GET IMDS → Bearer token
       └─ POST /subscriptions/{id}/providers/Microsoft.CostManagement/query
            └─ timeframe: current month (1st → today)
            └─ grouped by ResourceGroupName
            └─ returns cost rows sorted descending
  └─ scheduler.py renders templates/azure_cost_email.html
       └─ shows total spend + per-resource-group breakdown with progress bars
  └─ mailer.send_email()
       └─ MSAL acquires Graph API token
       └─ POST /v1.0/users/{FROM_EMAIL}/sendMail
```

### Key Files

- `services/azure_costs.py` — IMDS token fetch + Cost Management API query
- `templates/azure_cost_email.html` — styled HTML email with spend table and progress bars
- `scheduler.py` — registers the 8am cron job and renders the template

---

## Architecture

```
GitHub push to main
  └─ GitHub Actions (OIDC auth)
       └─ az acr build → acrdailybriefprod.azurecr.io/daily-brief:{sha}
       └─ az containerapp update → ca-daily-brief-prod
            └─ Managed Identity: id-daily-brief-prod
            └─ Secrets from Key Vault: kv-daily-brief
                 └─ GRAPH_CLIENT_ID
                 └─ GRAPH_CLIENT_SECRET
                 └─ GRAPH_TENANT_ID
```

## Environment Variables

| Variable | Source | Description |
|---|---|---|
| `GRAPH_CLIENT_ID` | Key Vault | AAD app registration for sending email |
| `GRAPH_CLIENT_SECRET` | Key Vault | App registration client secret |
| `GRAPH_TENANT_ID` | Key Vault | Azure AD tenant ID |
| `FROM_EMAIL` | Key Vault / default | Sender address (`erick@singularityai.tech`) |
| `TO_EMAIL` | Key Vault / default | Recipient address (`erickdarrington@gmail.com`) |

## Azure Resources

| Resource | Name |
|---|---|
| Container App | `ca-daily-brief-prod` |
| Container Registry | `acrdailybriefprod.azurecr.io` |
| Key Vault | `kv-daily-brief` |
| Managed Identity | `id-daily-brief-prod` |
| Resource Group | `rg-daily-brief-prod` |

## Manual Trigger

The app exposes a `/trigger/{period}` endpoint for on-demand sends:

```bash
curl -X POST https://<fqdn>/trigger/morning
curl -X POST https://<fqdn>/trigger/evening
```

## CI/CD

Push to `main` automatically builds and deploys via GitHub Actions (~90 seconds). Uses OIDC federated credentials — no long-lived secrets stored in GitHub.
