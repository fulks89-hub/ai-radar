# AI Radar interview

Ask one related group at a time and explain that every answer is optional.

## Round 1: relevance

- Which active projects or decisions should Radar help with?
- What outcomes and core ideas make a discovery useful?
- Which broad terms create false positives?

Map approved answers to `config/projects.json`: project name, description, goals, discriminating keywords, optional `exclude_keywords`, and optional core ideas with their own keywords.

## Round 2: people and assets

Ask which of these deserve explicit coverage and why:

- researchers, builders, writers, hosts, or other people;
- companies, labs, communities, or standards bodies;
- tools, products, models, datasets, or benchmarks;
- GitHub repositories and release/commit streams;
- podcasts, newsletters, RSS feeds, official blogs, papers, and websites;
- topics, methods, capabilities, risks, and competitors.

For every target capture: display name, category, official identifier or URL when known, reason to watch, related projects/core ideas, priority, and desired source format. Verify official URLs rather than guessing when network research is authorized.

Map unambiguous names/topics to `keywords`; release streams to `github_repositories`; commit streams to `github_commit_repositories`; feeds to `rss_feeds` or `agent_edition_feeds`; and first-party sites to `official_pages`. Do not pretend Radar can directly follow a person or private account when no supported official source is configured.

## Round 3: boundaries

- What should Radar ignore or de-prioritize?
- Which sources are editorial leads versus primary evidence?
- Are private captures allowed? Who can access generated artifacts?
- Are paid APIs allowed? If so, what explicit budget and review gate applies?
- How often should discovery run, and what would justify an alert?

Keep private-source collection and paid polling disabled by default. Do not request credentials during the interview; provide a separate, scoped setup step only after approval.

## Configuration preview

Propose changes to `config/watchlist.json` and `config/projects.json`. Preserve The AI Daily Brief as an always-on editorial lead. Show additions, removals, retained defaults, and exclusions before editing. A watch target raises attention, not verification or usefulness; project fit and evidence must still earn those labels.
