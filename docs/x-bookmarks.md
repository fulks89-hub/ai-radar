# Official X bookmark ingestion

AIRadar supports two X paths:

1. **Free/default:** iPhone Share Sheet -> AIRadar Shortcut -> private `[share]` GitHub issue.
2. **Optional official polling:** authenticated reads of the owner's X bookmarks using the X API.

The free path remains the lowest-friction default. Official bookmark polling is useful when you want AIRadar to notice bookmarks automatically without sharing each post manually.

## What the collector does

`python -m radar.x_bookmarks` calls `GET /2/users/{id}/bookmarks` only for the authenticated owner. It requests Post timestamps, authors, and public metrics, then writes:

- `reports/x-bookmarks.json` — private owner bookmark evidence for AIRadar reports/dashboard;
- `reports/x-bookmarks-state.json` — a small weekly resource-count budget state.

X bookmarks are **owner-intent evidence**, not external verification. They enter reports as `owner-priority-unverified` unless independent primary evidence corroborates the same trend.

External Post text remains untrusted data with zero instruction/tool authority.

## Cost guard

API pricing and terms can change. AI Radar therefore starts with a fail-closed software cap:

- default budget: **$0.00/week** (disabled);
- accounting estimate: configurable cost for every bookmark resource returned;
- default maximum: **2 pages / run**, up to 100 resources per page;
- the collector stops requesting pages when its local weekly budget counter is exhausted.

Before setting a nonzero budget, verify current official pricing and configure the per-resource estimate if needed. The counter intentionally ignores billing deduplication or discounts so it should overestimate rather than silently exceed its software budget.

## One-time X setup

The automated collector cannot create an X developer app or consent to X access on the owner's behalf. Complete this one-time setup in X's Developer Console:

1. Create/approve an X developer App.
2. Enable OAuth 2.0 Authorization Code with PKCE.
3. Authorize the owner account with at least `bookmark.read`, `tweet.read`, and `users.read`. Include `offline.access` if you want X to issue a refresh token for longer-lived access.
4. Obtain the authenticated owner's X user ID.
5. In a private `<YOUR_GITHUB_USERNAME>/ai-radar-template` GitHub repository, add Actions secrets:
   - `X_USER_ACCESS_TOKEN`
   - `X_USER_ID`
6. Set a reviewed, nonzero `X_WEEKLY_BUDGET_USD` in the workflow.
7. Run **Passive AI discovery** manually once and inspect `reports/x-bookmarks.json` and the dashboard artifact.

When those secrets are absent, the workflow succeeds with bookmark polling explicitly marked `credentials-not-configured`; the free Share Sheet path continues working.

## Token lifetime

The workflow never commits tokens or prints them. X OAuth access tokens can require renewal. AIRadar intentionally does not persist refresh tokens in Git or try to rewrite GitHub Secrets from Actions. If persistent automatic refresh becomes necessary, use a secret store capable of safe token rotation rather than committing credentials to this private repository.

## Privacy

Use a private repository when bookmark ingestion is enabled. Bookmark reports are private personal data. Do not publish `reports/x-bookmarks*.json` through a public static site or copy it into another knowledge system automatically.
