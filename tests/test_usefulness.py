import datetime as dt
import unittest

from radar.passive import Signal
from radar.usefulness import assess_usefulness


PROJECTS = [
    {
        "id": "brain",
        "name": "Research Workspace",
        "goals": ["Improve retrieval quality and reusable research"],
        "keywords": ["agent memory", "retrieval", "knowledge graph"],
        "core_ideas": [
            {
                "id": "evidence-memory",
                "name": "Evidence-linked memory",
                "description": "Recall with provenance.",
                "keywords": ["agent memory", "retrieval"],
            }
        ],
    }
]


class UsefulnessTests(unittest.TestCase):
    def test_strong_project_fit_and_primary_evidence_can_be_actionable(self):
        signal = Signal(
            "github-release",
            "Agent memory retrieval benchmark release",
            "https://example.com/release",
            "2026-08-18T00:00:00+00:00",
            summary="A knowledge graph SDK with a reproducible benchmark and integration guide.",
            authority="primary",
            origin="github:example/release",
        )
        result = assess_usefulness(
            title=signal.title,
            signals=[signal],
            verification="single-primary",
            projects=PROJECTS,
            now=dt.datetime(2026, 8, 18, tzinfo=dt.timezone.utc),
        )
        self.assertIn(result.band, {"act", "evaluate"})
        self.assertGreaterEqual(result.score, 55)
        self.assertEqual(result.project_matches[0].name, "Research Workspace")
        self.assertEqual(result.core_idea_matches[0].name, "Evidence-linked memory")

    def test_strong_news_signal_without_project_fit_is_not_called_useful(self):
        signal = Signal(
            "official-page",
            "Robotics financing announcement",
            "https://example.com/robotics",
            "2026-08-18T00:00:00+00:00",
            summary="A large financing round for warehouse robots.",
            authority="primary",
            origin="official:robotics-company",
        )
        result = assess_usefulness(
            title=signal.title,
            signals=[signal],
            verification="corroborated-primary",
            projects=PROJECTS,
            now=dt.datetime(2026, 8, 18, tzinfo=dt.timezone.utc),
        )
        self.assertIn(result.band, {"skip", "watch"})
        self.assertLess(result.score, 55)
        self.assertEqual(result.project_matches, [])
        self.assertEqual(result.core_idea_matches, [])

    def test_owner_intent_never_becomes_external_verification(self):
        signal = Signal(
            "owner-share", "Interesting idea", "https://example.com", "",
            authority="owner", origin="owner-share", watch="owner-share",
        )
        result = assess_usefulness(
            title=signal.title,
            signals=[signal],
            verification="owner-priority-unverified",
            projects=PROJECTS,
        )
        self.assertEqual(result.band, "watch")
        self.assertTrue(result.research_needed)

    def test_project_noise_exclusion_blocks_false_positive(self):
        projects = [{**PROJECTS[0], "exclude_keywords": ["crypto trading"]}]
        signal = Signal(
            "official-page",
            "Retrieval tooling for crypto trading",
            "https://example.com/crypto",
            "2026-08-18T00:00:00+00:00",
            summary="A knowledge graph retrieval SDK for crypto trading desks.",
            authority="primary",
            origin="official:example",
        )
        result = assess_usefulness(
            title=signal.title,
            signals=[signal],
            verification="single-primary",
            projects=projects,
            now=dt.datetime(2026, 8, 18, tzinfo=dt.timezone.utc),
        )
        self.assertEqual(result.project_matches, [])
        self.assertEqual(result.core_idea_matches, [])
        self.assertIn("Excluded from Research Workspace: crypto trading", result.reasons)


if __name__ == "__main__":
    unittest.main()
