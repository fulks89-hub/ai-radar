import unittest

from radar.passive import collect_agent_editions


class EditorialFeedTests(unittest.TestCase):
    def test_ai_daily_brief_is_collected_even_without_keyword_hit(self):
        payload = {
            "editions": [
                {
                    "date": "2026-08-18",
                    "title": "A practical operations episode",
                    "teaser": "A discussion that contains none of the configured terms.",
                    "tags": ["enterprise"],
                    "html": "https://www.aidailybrief.ai/e/2026-08-18",
                }
            ]
        }
        rows = collect_agent_editions(
            [{"name": "The AI Daily Brief", "url": "https://example.test/agent.json"}],
            ["agent memory"],
            fetcher=lambda _url: payload,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].authority, "secondary")
        self.assertIn("verify claims", rows[0].reason)
        self.assertEqual(rows[0].source, "editorial-brief")

    def test_episode_nuggets_become_separate_research_leads(self):
        feed = {
            "editions": [
                {
                    "date": "2026-08-18",
                    "title": "Agent operations",
                    "teaser": "A full episode.",
                    "html": "https://www.aidailybrief.ai/e/2026-08-18",
                    "json": "https://aidailybrief.ai/e/2026-08-18.json",
                }
            ]
        }
        detail = {
            "nuggets": [
                {
                    "id": "retrieval-evals",
                    "headline": "Retrieval evaluations become operational",
                    "body": "A segment to investigate against primary evidence.",
                    "category": "enterprise",
                    "functions": ["eng"],
                }
            ]
        }

        def fetcher(url):
            return detail if url.endswith(".json") and "/e/" in url else feed

        rows = collect_agent_editions(
            [{
                "name": "The AI Daily Brief",
                "url": "https://www.aidailybrief.ai/agent.json",
                "include_nuggets": True,
            }],
            ["retrieval"],
            fetcher=fetcher,
        )
        self.assertEqual(len(rows), 2)
        self.assertIn("research primary evidence", rows[1].reason)
        self.assertTrue(rows[1].url.endswith("?segment=retrieval-evals"))


if __name__ == "__main__":
    unittest.main()
