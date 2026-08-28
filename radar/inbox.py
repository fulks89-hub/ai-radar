from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

URL_RE = re.compile(r"https?://\S+")


@dataclass(frozen=True)
class Capture:
    issue_number: int
    url: str
    note: str
    created_at: str
    issue_url: str


def _github_json(url: str):
    token = os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AIRadar/0.1",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def parse_issue(issue: dict) -> Capture | None:
    title = issue.get("title", "")
    if not title.lower().startswith("[share]"):
        return None
    body = issue.get("body") or ""
    match = URL_RE.search(body)
    if not match:
        return None
    url = match.group(0).rstrip(").,]")
    note = body[match.end():].strip()
    note = re.sub(r"^note\s*:\s*", "", note, flags=re.IGNORECASE)
    return Capture(
        issue_number=int(issue["number"]),
        url=url,
        note=note,
        created_at=issue.get("created_at") or "",
        issue_url=issue.get("html_url") or "",
    )


def collect(repository: str) -> list[Capture]:
    owner, repo = repository.split("/", 1)
    query = urllib.parse.urlencode({"state": "open", "per_page": 100, "sort": "created", "direction": "desc"})
    issues = _github_json(f"https://api.github.com/repos/{owner}/{repo}/issues?{query}")
    captures = []
    seen = set()
    for issue in issues:
        # GitHub's issues endpoint also returns pull requests.
        if "pull_request" in issue:
            continue
        capture = parse_issue(issue)
        if capture and capture.url not in seen:
            seen.add(capture.url)
            captures.append(capture)
    return captures


def render(captures: list[Capture]) -> str:
    lines = [
        "# Shared AIRadar inbox",
        "",
        "> Owner-initiated captures from the iOS Share Sheet. These are scouting inputs, not durable knowledge.",
        "",
    ]
    if not captures:
        return "\n".join(lines + ["No open shared captures.", ""])
    for capture in captures:
        lines.extend([
            f"## Issue #{capture.issue_number}",
            "",
            f"- URL: {capture.url}",
            f"- Captured: `{capture.created_at}`",
            f"- Issue: {capture.issue_url}",
        ])
        if capture.note:
            lines.append(f"- Owner note: {capture.note}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    repository = (os.environ.get("GITHUB_REPOSITORY") or "").strip()
    captures = collect(repository) if repository else []
    out_dir = Path("reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "shared-inbox.json").write_text(
        json.dumps({"captures": [asdict(c) for c in captures]}, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "shared-inbox.md").write_text(render(captures), encoding="utf-8")
    status = f"Collected {len(captures)} owner-shared captures" if repository else "Share inbox disabled: GITHUB_REPOSITORY is not configured"
    print(status)


if __name__ == "__main__":
    main()
