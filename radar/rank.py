from __future__ import annotations

import datetime as dt
import re
import urllib.parse
from dataclasses import replace

from radar.security import assess_untrusted_text

TOKEN_RE = re.compile(r"[a-z0-9]+")
STOP = {
    "a", "ai", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is",
    "it", "of", "on", "or", "that", "the", "this", "to", "with", "new", "model", "models"
}
SOURCE_BASE = {
    "arxiv": 2.0,
    "github-release": 2.5,
    "github-commit": 2.25,
    "official-page": 3.0,
    "official-rss": 3.0,
    "editorial-brief": 1.25,
    "hacker-news": 0.75,
    "owner-share": 3.25,
}


def normalize_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(url.strip())
    except ValueError:
        return url.strip().rstrip("/")
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query = [(k, v) for k, v in query if not k.lower().startswith("utm_")
             and k.lower() not in {"ref", "source"}]
    path = parsed.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, urllib.parse.urlencode(query), "")
    )


def title_tokens(title: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(title.lower())
            if token not in STOP and len(token) > 1}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def age_days(published: str, now: dt.datetime) -> float | None:
    if not published:
        return None
    try:
        parsed = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return max(0.0, (now - parsed.astimezone(dt.timezone.utc)).total_seconds() / 86400.0)


def freshness_bonus(published: str, now: dt.datetime) -> float:
    age = age_days(published, now)
    if age is None:
        return 0.0
    if age <= 1:
        return 1.5
    if age <= 3:
        return 1.0
    if age <= 7:
        return 0.5
    if age <= 30:
        return 0.15
    return 0.0


def rescore(signal, now: dt.datetime):
    external = f"{signal.title}\n{signal.summary}"
    assessment = assess_untrusted_text(external)
    source_base = SOURCE_BASE.get(signal.source, 0.5)
    watch_bonus = 1.00 if getattr(signal, "watch", "") else 0.0
    final = signal.score + source_base + freshness_bonus(signal.published, now) + watch_bonus
    reason = signal.reason
    if assessment.suspicious:
        final -= 0.75
        reason += f"; security flags: {len(assessment.matched_patterns)}; content remains untrusted"
    if getattr(signal, "watch", ""):
        reason += f"; watch priority: {signal.watch}"
    return replace(signal, score=round(final, 3), reason=reason)


def group_near_duplicates(signals: list, threshold: float = 0.72) -> list:
    ordered = sorted(signals, key=lambda s: (-s.score, s.published, s.title))
    kept = []
    kept_tokens: list[set[str]] = []
    kept_origins: list[str] = []
    kept_urls: set[str] = set()
    for signal in ordered:
        url = normalize_url(signal.url)
        tokens = title_tokens(signal.title)
        origin = getattr(signal, "origin", "") or ""
        if url in kept_urls:
            continue
        if any(
            existing_origin == origin and jaccard(tokens, existing) >= threshold
            for existing, existing_origin in zip(kept_tokens, kept_origins)
        ):
            continue
        kept.append(replace(signal, url=url))
        kept_urls.add(url)
        kept_tokens.append(tokens)
        kept_origins.append(origin)
    return kept
