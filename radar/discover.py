from __future__ import annotations

import argparse
import datetime as dt
import json
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from radar.passive import (
    Signal,
    collect_agent_editions,
    collect_arxiv,
    collect_github_commits,
    collect_github_releases,
    collect_hacker_news,
    collect_official_pages,
    collect_rss_feeds,
    dedupe,
    render_markdown,
)
from radar.rank import rescore


def safe_extend(signals: list[Signal], errors: list[dict], source: str, collector: Callable[[], list[Signal]]) -> None:
    try:
        signals.extend(collector())
    except Exception as exc:
        errors.append({"source": source, "error": type(exc).__name__})


def collect_signals(config: dict) -> tuple[list[Signal], list[dict]]:
    keywords = config["keywords"]
    signals: list[Signal] = []
    errors: list[dict] = []
    collectors = [
        ("arxiv", lambda: collect_arxiv(config["arxiv_categories"], keywords)),
        ("official-rss", lambda: collect_rss_feeds(config.get("rss_feeds", []), keywords)),
        ("editorial-briefs", lambda: collect_agent_editions(config.get("agent_edition_feeds", []), keywords)),
        ("hacker-news", lambda: collect_hacker_news(keywords, config.get("hacker_news_limit", 100))),
        ("github-releases", lambda: collect_github_releases(config["github_repositories"], keywords)),
        ("github-commits", lambda: collect_github_commits(config.get("github_commit_repositories", []), keywords)),
        ("official-pages", lambda: collect_official_pages(config.get("official_pages", []), keywords)),
    ]
    for source, collector in collectors:
        safe_extend(signals, errors, source, collector)
    return signals, errors


def render_with_errors(signals: list[Signal], generated_at: str, errors: list[dict]) -> str:
    text = render_markdown(signals, generated_at)
    if not errors:
        return text
    lines = [text.rstrip(), "", "## Source availability notes", ""]
    lines.extend(f"- `{row['source']}` degraded this run (`{row['error']}`); other sources continued." for row in errors)
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/watchlist.json"))
    parser.add_argument("--json-output", type=Path, default=Path("reports/latest.json"))
    parser.add_argument("--markdown-output", type=Path, default=Path("reports/latest.md"))
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    signals, source_errors = collect_signals(config)
    now = dt.datetime.now(dt.timezone.utc)
    signals = dedupe([rescore(signal, now) for signal in signals])

    generated_at = now.isoformat()
    payload = {
        "generated_at": generated_at,
        "source_errors": source_errors,
        "signals": [asdict(signal) for signal in signals],
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_with_errors(signals, generated_at, source_errors), encoding="utf-8")

    history = args.json_output.parent / "history" / f"{now.date().isoformat()}.json"
    history.parent.mkdir(parents=True, exist_ok=True)
    history.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Collected {len(signals)} ranked unique passive signals; degraded sources: {len(source_errors)}")


if __name__ == "__main__":
    main()
