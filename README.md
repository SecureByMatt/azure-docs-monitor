# Azure Docs Monitor

A GitHub Actions + Python documentation-monitoring project inspired by KEV Monitor.
It checks **official Microsoft Learn articles** daily, tracks a baseline, and sends
**Discord embeds only when monitored article text changes**. A change in documentation
is **not** automatically a new Azure feature, security advisory, or breaking change.

## Sources (edit `sources.json`)

- Azure Virtual Desktop — What's new
- Microsoft Defender for Cloud — Release notes
- Microsoft Entra — What's new
- Azure Policy — Overview
- Azure Well-Architected Framework — What's new

## Quick start

1. Create a *new* GitHub repository named `azure-docs-monitor`. Do not mix this with `kev-monitor`.
2. Upload these files, preserving `.github/workflows/azure-docs-monitor.yml`.
3. Create a dedicated Discord channel/webhook, then add the GitHub Actions repository
   secret `DISCORD_WEBHOOK_URL`. Never commit the webhook URL.
4. In GitHub Actions, run **Azure Docs Monitor** manually with `preview_only` **unchecked** to establish the initial baseline; the first run sends no alerts.
5. Run again with `preview_only` **checked** to inspect changes without sending or committing anything.
6. Scheduled runs execute daily. When a page changes, the bot posts an embed and commits the new baseline to `state/pages.json`.

### Local preview

```bash
python -m pip install -r requirements.txt
python src/monitor.py --preview
```

### Important behavior

- **First successful run** establishes a baseline, not an alert (avoids floods).
- If any source fails to download or parses incorrectly, the job fails and does not
  advance the baseline; this avoids treating bad responses as changed docs.
- If a page changes and Discord has not been configured, the workflow fails rather
  than discarding the alert.
- Normalizations reduce navigation noise, but editorial/formatting edits can still trigger alerts.
- Only `learn.microsoft.com` HTTPS URLs are accepted.
- Review Microsoft Learn documentation changes before taking operational action.
- The page-extraction approach depends on Microsoft's HTML layout. This is a starter
  version; later we can add MicrosoftDocs GitHub commit-based monitoring or release feeds.

## Portfolio / interview description

"I designed an automated Azure documentation change-monitoring pipeline using
GitHub Actions and Python. It tracks selected Microsoft Learn pages, detects
substantive article changes, preserves state in source control, and delivers
structured Discord alerts with source links. It includes safe previews,
validation, retry handling, and failure safeguards."

Use that description only once the project is running successfully.
