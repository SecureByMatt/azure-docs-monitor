# Azure Docs Monitor

[![Azure Docs Monitor](https://github.com/SecureByMatt/azure-docs-monitor/actions/workflows/azure-docs-monitor.yml/badge.svg?branch=main)](https://github.com/SecureByMatt/azure-docs-monitor/actions/workflows/azure-docs-monitor.yml)

A Python and GitHub Actions pipeline that checks selected **official Microsoft Learn pages** for article-text changes, compares them with a versioned baseline, and sends change summaries to Discord.

> **Scope:** This monitors *documentation edits*, not Azure service telemetry, official security advisories, or confirmed feature releases. Review the linked Microsoft article before making operational changes.

## Documentation monitored

| Area | Source |
| --- | --- |
| Azure Virtual Desktop | [What's new](https://learn.microsoft.com/en-us/azure/virtual-desktop/whats-new) |
| Microsoft Defender for Cloud | [Release notes](https://learn.microsoft.com/en-us/azure/defender-for-cloud/release-notes) |
| Microsoft Entra | [What's new](https://learn.microsoft.com/en-us/entra/fundamentals/whats-new-overview) |
| Azure Policy | [Overview](https://learn.microsoft.com/en-us/azure/governance/policy/overview) |
| Azure Well-Architected Framework | [What's new](https://learn.microsoft.com/en-us/azure/well-architected/whats-new) |

Configure the monitored articles in [`sources.json`](sources.json). The script accepts HTTPS URLs on `learn.microsoft.com` only.

## How it works

1. GitHub Actions runs the Python monitor daily at **09:30 UTC** (scheduled execution can be delayed), or on manual dispatch.
2. The monitor fetches each page, extracts article headings and paragraphs, and removes selected navigation, code blocks, feedback/UI elements, and whitespace noise.
3. It compares the normalized article text against [`state/pages.json`](state/pages.json), using SHA-256 hashes and paragraph-level differences.
4. The first successful non-preview check establishes a baseline without notifications. Later detected changes generate Discord embeds containing the source link, an excerpt, and counts of added/revised and removed/revised paragraphs.
5. After successful processing and notification delivery, the workflow persists the updated state in Git.

A documentation rewording may still trigger an alert. Filtering is deliberately conservative to avoid discarding operationally relevant changes.

## Setup

1. Fork or clone this repository. Ensure GitHub Actions is enabled and that workflows have permission to update repository contents.
2. Create Discord webhooks and add GitHub **Settings → Secrets and variables → Actions → New repository secret**:
   - `DISCORD_WEBHOOK_URL` — production destination used on `main`.
   - `TEST_DISCORD_WEBHOOK_URL` — development destination used on `dev`.
3. Never commit webhook URLs or tokens. Both are passed through GitHub Actions secrets.
4. Run **Actions → Azure Docs Monitor → Run workflow** on `main` with **Preview only unchecked** to establish the initial baseline. For existing forks, review the checked-in baseline before replacing it.
5. Use **Preview only checked** for read-only validation. Preview runs do not post to Discord or write state.

### Development versus production

| Branch | Purpose | Normal notification destination |
| --- | --- | --- |
| `main` | Production monitoring and scheduled runs | `DISCORD_WEBHOOK_URL` |
| `dev` | Safe testing before pull requests | `TEST_DISCORD_WEBHOOK_URL` |

Manual runs are supported on either branch. The DEV test-alert checkbox is limited to manually triggered, preview-only `dev` runs and sends a clearly labeled synthetic notification. **Scheduled jobs execute on `main`**. Changes should be tested on `dev`, reviewed in a pull request, and merged only after validation.

### Local development

Requires Python 3.12 or compatible Python 3.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/monitor.py --preview
```

The workflow runs regression tests before checking documentation. Tests cover text extraction, change detection, feedback-noise filtering, and preserving technical changes.

## Failure safeguards and limitations

- Failed downloads or invalid/insufficient article extraction stop the run rather than advancing the baseline.
- HTTP requests use timeouts and retries; Discord delivery retries on rate limiting.
- If changes are detected but no webhook is configured, the monitor exits with an error instead of silently advancing state.
- The monitor depends on Microsoft Learn HTML structure. Page redesigns or editorial changes may require parser updates.
- The current monitor compares article text and does not classify severity, verify a product release, or assess customer impact.
- GitHub Actions schedules are best effort, not an exact-time guarantee. Review the [Actions history](https://github.com/SecureByMatt/azure-docs-monitor/actions) for failures.

## Project structure

```text
.github/workflows/azure-docs-monitor.yml  # scheduled/manual workflow
src/monitor.py                            # fetch, extract, compare, notify
tests/test_monitor.py                     # regression tests
sources.json                              # monitored Microsoft Learn URLs
state/pages.json                          # versioned documentation baseline
requirements.txt                          # Python dependencies
```

## Portfolio summary

Designed and deployed an automated Azure documentation-monitoring pipeline using Python, Microsoft Learn, and GitHub Actions. It performs scheduled source checks, normalized text comparisons, Git-versioned state management, regression testing, and Discord webhook notifications with separate development and production workflows.

**Project status (November 20, 2026):** Production execution validated on `main` (Run #10); five monitored articles checked and regression tests passed. A synthetic production webhook notification was successfully delivered. Real-change production alert delivery has not yet been observed.
