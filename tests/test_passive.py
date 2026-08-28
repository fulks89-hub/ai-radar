import unittest
from unittest.mock import patch

from radar.passive import Signal, collect_official_pages, collect_rss_feeds, dedupe, keyword_score, render_markdown


class PassiveDiscoveryTests(unittest.TestCase):
    def test_keyword_score_detects_relevant_terms(self):
        score, hits = keyword_score("New agent memory benchmark for RAG systems", ["agent", "memory", "rag", "robotics"])
        self.assertGreater(score, 0)
        self.assertEqual(set(hits), {"agent", "memory", "rag"})

    def test_dedupe_keeps_best_signal_for_same_url(self):
        signals = [
            Signal("a", "old", "https://example.com/x", "", score=1.0),
            Signal("b", "better", "https://example.com/x", "", score=4.0),
        ]
        result = dedupe(signals)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "better")

    def test_markdown_marks_output_untrusted(self):
        text = render_markdown([Signal("arxiv", "Test", "https://example.com", "2026-01-01", score=2.0)], "now")
        self.assertIn("zero", text.lower())
        self.assertIn("Test", text)

    @patch("radar.passive.fetch_text")
    def test_official_rss_collector_marks_primary_origin(self, fetch):
        fetch.return_value = """<rss><channel><item><title>Agent memory benchmark</title><link>https://lab.example/news/a</link><pubDate>Sun, 16 Aug 2026 12:00:00 GMT</pubDate><description>retrieval evaluation</description></item></channel></rss>"""
        rows = collect_rss_feeds([{"name": "Lab", "url": "https://lab.example/rss.xml"}], ["agent", "memory"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].authority, "primary")
        self.assertEqual(rows[0].origin, "official:lab")

    @patch("radar.passive.fetch_text")
    def test_official_page_collector_stays_on_origin(self, fetch):
        fetch.return_value = '<a href="/news/agent-memory">Agent memory research</a><a href="https://evil.example/x">agent leak</a>'
        rows = collect_official_pages([{"name": "Lab", "url": "https://lab.example/news/"}], ["agent", "memory"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].authority, "primary")
        self.assertTrue(rows[0].url.startswith("https://lab.example/"))


if __name__ == "__main__":
    unittest.main()
