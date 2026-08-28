from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

API_ROOT = "https://api.x.com/2"
USER_AGENT = "AIRadar/0.3 (+research scout)"
OWNED_READ_COST_USD = 0.001
DEFAULT_WEEKLY_BUDGET_USD = 0.00
DEFAULT_MAX_PAGES_PER_RUN = 2


@dataclass(frozen=True)
class Bookmark:
    id: str
    url: str
    text: str
    created_at: str
    author_id: str = ""
    author_username: str = ""
    author_name: str = ""
    public_metrics: dict | None = None


def week_start(now: dt.datetime) -> str:
    day = now.astimezone(dt.timezone.utc).date()
    return (day - dt.timedelta(days=day.weekday())).isoformat()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fetch_json(url: str, access_token: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _authors(payload: dict) -> dict[str, dict]:
    return {row.get("id", ""): row for row in payload.get("includes", {}).get("users", [])}


def _bookmark_rows(payload: dict) -> list[Bookmark]:
    authors = _authors(payload)
    rows: list[Bookmark] = []
    for post in payload.get("data", []) or []:
        post_id = str(post.get("id", ""))
        if not post_id:
            continue
        author = authors.get(str(post.get("author_id", "")), {})
        username = author.get("username") or ""
        rows.append(
            Bookmark(
                id=post_id,
                url=(f"https://x.com/{username}/status/{post_id}" if username else f"https://x.com/i/web/status/{post_id}"),
                text=(post.get("text") or "").strip(),
                created_at=post.get("created_at") or "",
                author_id=str(post.get("author_id") or ""),
                author_username=username,
                author_name=author.get("name") or "",
                public_metrics=post.get("public_metrics") or {},
            )
        )
    return rows


def collect_bookmarks(
    *,
    user_id: str,
    access_token: str,
    state: dict,
    existing: dict,
    weekly_budget_usd: float = DEFAULT_WEEKLY_BUDGET_USD,
    max_pages: int = DEFAULT_MAX_PAGES_PER_RUN,
    now: dt.datetime | None = None,
    fetcher: Callable[[str, str], dict] = _fetch_json,
) -> tuple[dict, dict]:
    now = now or dt.datetime.now(dt.timezone.utc)
    current_week = week_start(now)
    if state.get("week_start") != current_week:
        state = {"week_start": current_week, "resources_read": 0}

    resources_read = int(state.get("resources_read", 0))
    max_weekly_resources = max(0, math.floor(weekly_budget_usd / OWNED_READ_COST_USD))
    remaining = max(0, max_weekly_resources - resources_read)
    prior_rows = {str(row.get("id")): row for row in existing.get("bookmarks", []) if row.get("id")}

    status = "ok"
    pages = 0
    returned_resources = 0
    pagination_token = None

    while pages < max_pages and remaining > 0:
        page_size = min(100, remaining)
        params = {
            "max_results": page_size,
            "tweet.fields": "created_at,author_id,public_metrics,entities",
            "expansions": "author_id",
            "user.fields": "username,name,verified",
        }
        if pagination_token:
            params["pagination_token"] = pagination_token
        url = f"{API_ROOT}/users/{urllib.parse.quote(user_id)}/bookmarks?{urllib.parse.urlencode(params)}"
        payload = fetcher(url, access_token)
        if payload.get("errors") and not payload.get("data"):
            status = "api-error"
            break

        rows = _bookmark_rows(payload)
        returned = len(rows)
        returned_resources += returned
        resources_read += returned
        remaining = max(0, max_weekly_resources - resources_read)
        for row in rows:
            prior_rows[row.id] = asdict(row)

        pages += 1
        pagination_token = (payload.get("meta") or {}).get("next_token")
        if not pagination_token or returned == 0:
            break

    if remaining <= 0:
        status = "weekly-budget-reached"

    bookmarks = sorted(
        prior_rows.values(),
        key=lambda row: (row.get("created_at") or "", row.get("id") or ""),
        reverse=True,
    )[:1000]
    spend = resources_read * OWNED_READ_COST_USD
    result = {
        "generated_at": now.isoformat(),
        "enabled": True,
        "status": status,
        "source": "x-owned-bookmarks",
        "weekly_budget_usd": round(weekly_budget_usd, 4),
        "owned_read_unit_cost_usd": OWNED_READ_COST_USD,
        "week_start": current_week,
        "resources_read_this_week": resources_read,
        "estimated_spend_this_week_usd": round(spend, 4),
        "resources_returned_this_run": returned_resources,
        "pages_fetched_this_run": pages,
        "bookmarks": bookmarks,
    }
    next_state = {"week_start": current_week, "resources_read": resources_read}
    return result, next_state


def disabled_payload(reason: str, now: dt.datetime, budget: float) -> dict:
    return {
        "generated_at": now.isoformat(),
        "enabled": False,
        "status": reason,
        "source": "x-owned-bookmarks",
        "weekly_budget_usd": round(budget, 4),
        "owned_read_unit_cost_usd": OWNED_READ_COST_USD,
        "resources_read_this_week": 0,
        "estimated_spend_this_week_usd": 0.0,
        "bookmarks": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect authenticated owner's X bookmarks safely")
    parser.add_argument("--output", type=Path, default=Path("reports/x-bookmarks.json"))
    parser.add_argument("--state", type=Path, default=Path("reports/x-bookmarks-state.json"))
    parser.add_argument("--weekly-budget-usd", type=float, default=float(os.environ.get("X_WEEKLY_BUDGET_USD", DEFAULT_WEEKLY_BUDGET_USD)))
    parser.add_argument("--max-pages", type=int, default=int(os.environ.get("X_MAX_PAGES_PER_RUN", DEFAULT_MAX_PAGES_PER_RUN)))
    args = parser.parse_args()

    now = dt.datetime.now(dt.timezone.utc)
    access_token = (os.environ.get("X_USER_ACCESS_TOKEN") or "").strip()
    user_id = (os.environ.get("X_USER_ID") or "").strip()
    if not access_token or not user_id:
        payload = disabled_payload("credentials-not-configured", now, args.weekly_budget_usd)
        save_json(args.output, payload)
        print("X bookmark polling disabled: X_USER_ACCESS_TOKEN and X_USER_ID are not both configured")
        return

    state = load_json(args.state)
    existing = load_json(args.output)
    payload, next_state = collect_bookmarks(
        user_id=user_id,
        access_token=access_token,
        state=state,
        existing=existing,
        weekly_budget_usd=args.weekly_budget_usd,
        max_pages=max(1, args.max_pages),
        now=now,
    )
    save_json(args.output, payload)
    save_json(args.state, next_state)
    print(
        f"X bookmarks: {payload['resources_returned_this_run']} resources this run; "
        f"estimated ${payload['estimated_spend_this_week_usd']:.3f}/${payload['weekly_budget_usd']:.2f} this week"
    )


if __name__ == "__main__":
    main()
