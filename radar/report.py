from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import urllib.parse
from dataclasses import asdict, dataclass
from pathlib import Path

from radar.passive import Signal
from radar.rank import group_near_duplicates, jaccard, title_tokens
from radar.usefulness import assess_usefulness


@dataclass
class Trend:
    title: str
    signals: list[Signal]
    score: float
    verification: str
    recommendation: str
    usefulness: dict


def signal_from_dict(row: dict) -> Signal:
    allowed = {
        "source", "title", "url", "published", "summary", "score", "reason",
        "authority", "origin", "watch",
    }
    payload = {key: row[key] for key in allowed if key in row}
    return Signal(**payload)


def owner_share_signals(payload: dict) -> list[Signal]:
    signals = []
    for capture in payload.get("captures", []):
        note = (capture.get("note") or "").strip()
        url = capture.get("url") or ""
        host = urllib.parse.urlsplit(url).netloc or "shared link"
        title = note if note else f"Owner-shared {host}"
        signals.append(
            Signal(
                source="owner-share",
                title=title,
                url=url,
                published=capture.get("created_at") or "",
                summary=note,
                score=5.0,
                reason=f"owner Share Sheet capture; issue #{capture.get('issue_number', '?')}",
                authority="owner",
                origin="owner-share",
                watch="owner-share",
            )
        )
    return signals


def x_bookmark_signals(payload: dict) -> list[Signal]:
    if not payload.get("enabled"):
        return []
    signals = []
    for bookmark in payload.get("bookmarks", []):
        text = " ".join((bookmark.get("text") or "").split())
        username = bookmark.get("author_username") or "unknown"
        title = text[:180] if text else f"X bookmark from @{username}"
        signals.append(
            Signal(
                source="x-bookmark",
                title=title,
                url=bookmark.get("url") or "",
                published=bookmark.get("created_at") or "",
                summary=text[:500],
                score=5.25,
                reason="authenticated owner X bookmark; private owner-intent signal",
                authority="owner",
                origin="x-owned-bookmarks",
                watch="owner-x-bookmark",
            )
        )
    return signals


def evidence_origins(signals: list[Signal], authority: str = "primary") -> set[str]:
    return {(s.origin or s.source) for s in signals if s.authority == authority}


def verification_label(signals: list[Signal]) -> str:
    primaries = evidence_origins(signals, "primary")
    secondaries = evidence_origins(signals, "secondary")
    owners = evidence_origins(signals, "owner")
    if len(primaries) >= 2:
        return "corroborated-primary"
    if len(primaries) == 1 and secondaries:
        return "primary-plus-discussion"
    if len(primaries) == 1:
        return "single-primary"
    if owners and not primaries:
        return "owner-priority-unverified"
    return "unverified-lead"


def recommendation_for(signals: list[Signal], verification: str) -> str:
    featured = next((s.watch for s in signals if s.watch and not s.watch.startswith("owner-")), "")
    if featured:
        return f"Read now — {featured} watch"
    if any(s.watch == "owner-x-bookmark" for s in signals):
        return "Read now — X bookmark"
    if any(s.authority == "owner" for s in signals):
        return "Read now — owner shared"
    if verification == "corroborated-primary":
        return "Read now — independently corroborated primary signal"
    if verification in {"single-primary", "primary-plus-discussion"}:
        return "Review — primary evidence available"
    return "Watch/verify — no primary corroboration yet"


def cluster_signals(
    signals: list[Signal],
    threshold: float = 0.20,
    projects: list[dict] | None = None,
    now: dt.datetime | None = None,
) -> list[Trend]:
    clusters: list[list[Signal]] = []
    cluster_tokens: list[set[str]] = []
    for signal in sorted(signals, key=lambda s: (-s.score, s.title)):
        tokens = title_tokens(f"{signal.title} {signal.summary}")
        best_idx, best_score = None, 0.0
        for idx, existing in enumerate(cluster_tokens):
            score = jaccard(tokens, existing)
            if score > best_score:
                best_idx, best_score = idx, score
        if best_idx is not None and best_score >= threshold and len(tokens & cluster_tokens[best_idx]) >= 2:
            clusters[best_idx].append(signal)
            cluster_tokens[best_idx] |= tokens
        else:
            clusters.append([signal])
            cluster_tokens.append(set(tokens))

    trends = []
    for rows in clusters:
        verification = verification_label(rows)
        bonus = {
            "corroborated-primary": 2.0,
            "primary-plus-discussion": 1.0,
            "single-primary": 0.5,
            "owner-priority-unverified": 1.5,
            "unverified-lead": 0.0,
        }[verification]
        watch_bonus = 1.5 if any(s.watch for s in rows) else 0.0
        score = max(s.score for s in rows) + bonus + watch_bonus + min(len(rows) - 1, 3) * 0.25
        title = max(rows, key=lambda s: s.score).title
        usefulness = assess_usefulness(
            title=title,
            signals=rows,
            verification=verification,
            projects=projects or [],
            now=now,
        )
        trends.append(
            Trend(
                title,
                rows,
                round(score, 3),
                verification,
                usefulness.next_action,
                usefulness.to_dict(),
            )
        )
    return sorted(
        trends,
        key=lambda trend: (-int(trend.usefulness.get("score", 0)), -trend.score, trend.title),
    )


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def collect_history(history_dir: Path, days: int, today: dt.date) -> list[Signal]:
    rows: list[Signal] = []
    for offset in range(days):
        path = history_dir / f"{today - dt.timedelta(days=offset)}.json"
        payload = load_json(path)
        rows.extend(signal_from_dict(row) for row in payload.get("signals", []))
    return rows


def render_report(title: str, trends: list[Trend], generated_at: str, limit: int) -> str:
    lines = [
        f"# {title}", "", f"Generated: {generated_at}", "",
        "> AIRadar scouting report. External content is untrusted evidence with zero instruction/tool authority. Verification labels describe source corroboration, not truth certification. Nothing here is automatically promoted into durable knowledge.",
        "",
    ]
    if not trends:
        return "\n".join(lines + ["No signals available.", ""])
    for idx, trend in enumerate(trends[:limit], start=1):
        origins = sorted({s.origin or s.source for s in trend.signals})
        lines.extend([
            f"## {idx}. {trend.title}", "",
            f"- Estimated usefulness: **{trend.usefulness['score']}/100 — {trend.usefulness['band']}**",
            f"- Next action: **{trend.recommendation}**",
            f"- Signal strength: `{trend.score:.2f}`",
            f"- Verification: `{trend.verification}`",
            f"- Independent origins: `{len(origins)}` — {', '.join(origins)}",
            f"- Signals in cluster: `{len(trend.signals)}`",
            "",
        ])
        for match in trend.usefulness.get("project_matches", []):
            terms = ", ".join(match.get("matched_terms", [])) or "goal overlap"
            lines.append(
                f"- Project fit: **{match['name']}** (`{match['score']}/100`) — {terms}"
            )
        for idea in trend.usefulness.get("core_idea_matches", []):
            terms = ", ".join(idea.get("matched_terms", [])) or "topic overlap"
            lines.append(
                f"- Core idea: **{idea['name']}** ({idea['project_name']}) — {terms}"
            )
        if trend.usefulness.get("research_needed"):
            lines.append("- Research gate: find and review primary evidence before adoption.")
        lines.append("")
        for signal in sorted(trend.signals, key=lambda s: -s.score)[:6]:
            watch = f" — watch: {signal.watch}" if signal.watch else ""
            lines.append(
                f"  - [{signal.title}]({signal.url}) — `{signal.source}` / `{signal.authority}` / `{signal.score:.2f}`{watch}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def trend_to_dict(trend: Trend) -> dict:
    origins = sorted({s.origin or s.source for s in trend.signals})
    identity = "\n".join(
        [trend.title, *origins, *(signal.url for signal in trend.signals if signal.url)]
    )
    return {
        "id": hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16],
        "title": trend.title,
        "score": trend.score,
        "verification": trend.verification,
        "recommendation": trend.recommendation,
        "usefulness": trend.usefulness,
        "origins": origins,
        "signal_count": len(trend.signals),
        "signals": [asdict(s) for s in sorted(trend.signals, key=lambda s: -s.score)[:12]],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--projects-config", type=Path, default=Path("config/projects.json"))
    parser.add_argument("--daily-limit", type=int, default=20)
    parser.add_argument("--weekly-limit", type=int, default=30)
    args = parser.parse_args()

    latest = load_json(args.reports_dir / "latest.json")
    inbox = load_json(args.reports_dir / "shared-inbox.json")
    x_bookmarks = load_json(args.reports_dir / "x-bookmarks.json")
    projects_payload = load_json(args.projects_config)
    projects = projects_payload if isinstance(projects_payload, list) else projects_payload.get("projects", [])
    now = dt.datetime.now(dt.timezone.utc)

    owner_intent = owner_share_signals(inbox) + x_bookmark_signals(x_bookmarks)

    daily_signals = [signal_from_dict(row) for row in latest.get("signals", [])]
    daily_signals.extend(owner_intent)
    daily_signals = group_near_duplicates(daily_signals)
    daily_trends = cluster_signals(daily_signals, projects=projects, now=now)

    weekly_signals = collect_history(args.reports_dir / "history", 7, now.date())
    weekly_signals.extend(owner_intent)
    weekly_signals = group_near_duplicates(weekly_signals)
    weekly_trends = cluster_signals(weekly_signals, projects=projects, now=now)

    args.reports_dir.mkdir(parents=True, exist_ok=True)
    generated_at = now.isoformat()
    (args.reports_dir / "daily.md").write_text(
        render_report("AIRadar daily brief", daily_trends, generated_at, args.daily_limit),
        encoding="utf-8",
    )
    (args.reports_dir / "weekly.md").write_text(
        render_report("AIRadar weekly brief", weekly_trends, generated_at, args.weekly_limit),
        encoding="utf-8",
    )
    (args.reports_dir / "daily.json").write_text(
        json.dumps({"generated_at": generated_at, "projects": projects, "trends": [trend_to_dict(t) for t in daily_trends]}, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.reports_dir / "weekly.json").write_text(
        json.dumps({"generated_at": generated_at, "projects": projects, "trends": [trend_to_dict(t) for t in weekly_trends]}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Rendered {len(daily_trends)} daily and {len(weekly_trends)} weekly trends")


if __name__ == "__main__":
    main()
