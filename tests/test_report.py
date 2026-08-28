import unittest

from radar.passive import Signal
from radar.report import cluster_signals, owner_share_signals, trend_to_dict, verification_label


class ReportTests(unittest.TestCase):
    def test_two_distinct_primary_origins_are_corroborated(self):
        rows = [
            Signal("official-page", "New agent memory benchmark", "https://openai.com/a", "", score=8, authority="primary", origin="official:openai"),
            Signal("github-release", "Agent memory benchmark released", "https://github.com/a/b", "", score=7, authority="primary", origin="github:a/b"),
        ]
        trends = cluster_signals(rows, threshold=0.1)
        self.assertEqual(len(trends), 1)
        self.assertEqual(trends[0].verification, "corroborated-primary")

    def test_same_origin_is_not_independent_corroboration(self):
        rows = [
            Signal("github-commit", "Agent memory change", "https://github.com/a/1", "", authority="primary", origin="github:a/b"),
            Signal("github-release", "Agent memory release", "https://github.com/a/2", "", authority="primary", origin="github:a/b"),
        ]
        self.assertEqual(verification_label(rows), "single-primary")

    def test_serialized_trend_has_stable_opaque_id(self):
        row = Signal("official-page", "Agent memory", "https://example.com/a", "", authority="primary", origin="official:example")
        payload = trend_to_dict(cluster_signals([row])[0])
        self.assertRegex(payload["id"], r"^[a-f0-9]{16}$")
        self.assertEqual(payload["id"], trend_to_dict(cluster_signals([row])[0])["id"])

    def test_owner_share_is_watchlisted_but_not_called_useful_or_verified(self):
        rows = owner_share_signals({"captures": [{"issue_number": 1, "url": "https://x.com/a/status/1", "note": "agent memory idea", "created_at": "now"}]})
        trends = cluster_signals(rows)
        self.assertEqual(trends[0].verification, "owner-priority-unverified")
        self.assertEqual(trends[0].usefulness["band"], "watch")
        self.assertTrue(trends[0].usefulness["research_needed"])

    def test_configured_watch_gets_attention_without_forcing_usefulness(self):
        row = Signal("github-commit", "example project: agent skill", "https://github.com/example-org/example-project/commit/x", "", score=8, authority="primary", origin="github:example-org/example-project", watch="Featured Project")
        trend = cluster_signals([row])[0]
        self.assertEqual(trend.usefulness["band"], "watch")
        self.assertLess(trend.usefulness["score"], 55)


if __name__ == "__main__":
    unittest.main()
