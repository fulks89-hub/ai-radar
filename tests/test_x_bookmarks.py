import datetime as dt
import unittest

from radar.x_bookmarks import collect_bookmarks, disabled_payload, week_start


class XBookmarksTests(unittest.TestCase):
    def test_week_start_is_monday_utc(self):
        now = dt.datetime(2026, 8, 16, 23, tzinfo=dt.timezone.utc)  # Sunday
        self.assertEqual(week_start(now), "2026-08-10")

    def test_collect_dedupes_and_counts_conservative_owned_reads(self):
        calls = []

        def fetcher(url, token):
            calls.append((url, token))
            return {
                "data": [
                    {"id": "2", "text": "new", "created_at": "2026-08-16T10:00:00Z", "author_id": "7", "public_metrics": {"like_count": 4}},
                    {"id": "1", "text": "old refreshed", "created_at": "2026-08-15T10:00:00Z", "author_id": "7"},
                ],
                "includes": {"users": [{"id": "7", "username": "tester", "name": "Test User"}]},
                "meta": {},
            }

        now = dt.datetime(2026, 8, 16, 23, tzinfo=dt.timezone.utc)
        existing = {"bookmarks": [{"id": "1", "text": "old", "created_at": "2026-08-15T10:00:00Z"}]}
        payload, state = collect_bookmarks(
            user_id="123", access_token="secret", state={"week_start": "2026-08-10", "resources_read": 10},
            existing=existing, weekly_budget_usd=1.00, max_pages=1, now=now, fetcher=fetcher,
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(payload["resources_read_this_week"], 12)
        self.assertEqual(payload["estimated_spend_this_week_usd"], 0.012)
        self.assertEqual([row["id"] for row in payload["bookmarks"]], ["2", "1"])
        self.assertEqual(payload["bookmarks"][0]["author_username"], "tester")
        self.assertEqual(state["resources_read"], 12)

    def test_budget_prevents_request_when_exhausted(self):
        called = False

        def fetcher(url, token):
            nonlocal called
            called = True
            return {}

        now = dt.datetime(2026, 8, 16, tzinfo=dt.timezone.utc)
        payload, _ = collect_bookmarks(
            user_id="123", access_token="secret", state={"week_start": "2026-08-10", "resources_read": 1000},
            existing={}, weekly_budget_usd=1.00, now=now, fetcher=fetcher,
        )
        self.assertFalse(called)
        self.assertEqual(payload["status"], "weekly-budget-reached")
        self.assertEqual(payload["estimated_spend_this_week_usd"], 1.00)

    def test_disabled_payload_contains_no_secret_fields(self):
        payload = disabled_payload("credentials-not-configured", dt.datetime.now(dt.timezone.utc), 1.00)
        self.assertFalse(payload["enabled"])
        self.assertNotIn("access_token", payload)


if __name__ == "__main__":
    unittest.main()
