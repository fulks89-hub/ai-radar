# The AI Daily Brief source

AI Radar keeps The AI Daily Brief enabled as an always-on editorial discovery source through its official machine-readable `agent.json` endpoint.

The feed provides episode dates, titles, teasers, tags, listening links, and links to HTML, Markdown, JSON, and transcripts. AI Radar reads the five latest editions and expands their machine-readable episode segments into separate research leads. That makes the site a useful broad scanner rather than a single daily headline.

It is deliberately classified as **secondary editorial evidence**. An episode can raise a candidate's attention and contribute project-language matches, but it cannot create primary corroboration. If an episode produces an `act` or `evaluate` candidate without primary evidence, the report sets `research_needed: true`; review the episode's underlying first-party sources before adopting a claim or tool.

This separation lets the podcast stay always-on without making every episode automatically useful or verified.
