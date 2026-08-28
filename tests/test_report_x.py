import unittest

from radar.report import trend_to_dict, x_bookmark_signals, cluster_signals


class ReportXTests(unittest.TestCase):
    def test_x_bookmark_becomes_owner_intent_not_verification(self):
        rows = x_bookmark_signals({
            "enabled": True,
            "bookmarks": [{
                "id": "123", "url": "https://x.com/example/status/123",
                "text": "Interesting agent memory paper", "created_at": "2026-08-16T12:00:00Z",
                "author_username": "example",
            }],
        })
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].authority, "owner")
        trend = cluster_signals(rows)[0]
        self.assertEqual(trend.verification, "owner-priority-unverified")
        self.assertEqual(trend.usefulness["band"], "watch")
        self.assertTrue(trend.usefulness["research_needed"])

    def test_trend_json_keeps_signal_provenance_for_dashboard(self):
        rows = x_bookmark_signals({
            "enabled": True,
            "bookmarks": [{"id": "123", "url": "https://x.com/e/status/123", "text": "AI agent update", "created_at": "2026-08-16T12:00:00Z"}],
        })
        payload = trend_to_dict(cluster_signals(rows)[0])
        self.assertEqual(payload["signal_count"], 1)
        self.assertEqual(payload["signals"][0]["source"], "x-bookmark")
        self.assertEqual(payload["origins"], ["x-owned-bookmarks"])


if __name__ == "__main__":
    unittest.main()
