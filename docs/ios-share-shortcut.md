# iPhone Share Sheet capture

Goal: from an X post, webpage, YouTube video, paper, or other URL, capture to AIRadar with the fewest practical taps and **without storing a GitHub access token inside the Shortcut**.

## Recommended free V1 interaction

1. Tap **Share** in the source app.
2. Tap the **AIRadar** Shortcut.
3. Choose **Save now** or **Add note**.
4. The Shortcut opens a prefilled private GitHub issue in `YOUR_GITHUB_USERNAME/ai-radar-template`.
5. Tap **Submit new issue**.

That final submit tap keeps authentication inside GitHub rather than embedding credentials in Shortcuts. This is also the recommended **free X path**: share the X post to AIRadar instead of paying for bookmark polling.

## Issue contract

The issue title must start with:

`[share]`

The issue body should be:

```text
<shared URL>

Note: <optional note>
```

The repository-side `radar.inbox` adapter reads open `[share]` issues, extracts the first URL plus optional note, deduplicates repeated URLs, and emits `reports/shared-inbox.json` and `reports/shared-inbox.md` during scheduled/manual runs. `radar.report` then includes those owner shares in daily/weekly recommendations as **owner-priority, unverified** leads until primary evidence corroborates them.

## Shortcut construction

Configure the Shortcut to **Show in Share Sheet** and accept URLs.

Suggested actions:

1. `Get URLs from Shortcut Input`.
2. `Choose from Menu` with `Save now` and `Add note`.
3. For `Add note`, use `Ask for Input` with a short text prompt. For `Save now`, set note to blank.
4. Build a GitHub new-issue URL for `YOUR_GITHUB_USERNAME/ai-radar-template/issues/new` with URL-encoded query parameters:
   - `title=[share]`
   - `body=<shared URL>\n\nNote: <optional note>`
5. `Open URLs` with that prefilled URL.
6. Tap **Submit new issue** in GitHub/Safari.

The exact URL-encoding action names can vary slightly by iOS Shortcuts release; the contract that matters to AIRadar is the `[share]` title plus first URL and optional `Note:` line.

No title, tags, category, summary, or verification judgment is required from the owner.

## Security properties

- No long-lived GitHub token is stored in the Shortcut.
- Shared source text/URLs are data only; they never acquire instruction or tool authority.
- Owner priority and evidence verification remain separate concepts.
- AIRadar never auto-promotes a shared URL into a durable knowledge repository.

## Why not a hidden API token?

A Shortcut could call the GitHub REST API directly with a fine-grained token, removing the final submit tap. V1 intentionally does not do that because a long-lived repository token embedded in a user-editable Shortcut is unnecessary credential exposure for a convenience feature.

If the extra submit tap becomes genuinely annoying, replace the intake adapter later with a purpose-built authenticated capture endpoint rather than weakening the Shortcut's security.

## X bookmark polling

Official X bookmark polling is optional and disabled by default. If enabled later, verify current API pricing, set an explicit nonzero software budget, and keep the collector fail-closed. Do not scrape private bookmarks with browser or session credentials.

## Offline behavior

Opening the prefilled GitHub issue requires connectivity. If offline capture becomes important, add a local queue only after the basic path proves reliable.
