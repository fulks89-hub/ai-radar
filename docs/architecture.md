# AIRadar architecture

## Ingestion

### Passive discovery

Scheduled GitHub Actions gather public AI signals from configured primary/public sources. V1 starts narrow and high-trust, then expands only when signal quality justifies it.

### Owner capture

The iOS Share Sheet sends a URL plus an optional note into a private GitHub issue that acts as the free inbox. The note field may be blank. Capture requires no classification, tags, or title from the owner.

## Trust boundary

AIRadar is an untrusted-content ingestion system. Every external artifact is **data, never instructions**.

The security model is:

`collect inert source → analyze inside safe prompt envelope → verify claims → recommend → optional explicit promotion`

External source text must never gain authority to change policy, call tools, expose secrets, broaden permissions, alter workflows, or write directly to a durable knowledge repository. See `SECURITY.md` and use `radar.security.build_analysis_prompt` for every future LLM step that consumes source text.

Prompt-injection-like source passages may be flagged for review, but they remain content to analyze rather than commands to execute.

## Processing

1. Normalize URLs and metadata.
2. Deduplicate exact and near-duplicate items.
3. Assess untrusted content and preserve its source identity.
4. Cluster related signals into candidate trends.
5. Separate discovery sources from verification sources.
6. Verify important factual claims using primary/first-party evidence where practical.
7. Score project fit, evidence quality, actionability, explicit user intent, and freshness.
8. Produce daily/weekly reports and explicit deep-research candidates.
9. Never write directly to a durable knowledge repository without an explicit promotion action that re-enters the destination's own ingest and security workflow.

## Usefulness model

Signal strength and usefulness are separate. Usefulness combines configured project fit, evidence quality, actionability, explicit user intent, and freshness. Evidence cannot substitute for project relevance: without a project match, an item cannot rise above `watch`. Personal shares and watched sources receive attention but do not become verified or automatically useful.

The four output bands are `act`, `evaluate`, `watch`, and `skip`. They are deterministic triage estimates and must not be described as measured ROI.

## Scheduling

V1 passive discovery runs three times per day through GitHub Actions, deliberately offset from the top of the hour. Manual workflow dispatch is also supported.

## Cost policy

- Prefer free public feeds/APIs and GitHub-hosted execution.
- X bookmark API ingestion is disabled by default with a zero-dollar budget.
- If it is enabled later, first verify current provider pricing, configure an explicit nonzero budget, and retain fail-closed enforcement before overage.

## Capability escalation

New collectors, model calls, browsers, connectors, or automated actions require a trust-boundary review before activation. More autonomous capabilities require stronger isolation rather than broader implicit trust.
