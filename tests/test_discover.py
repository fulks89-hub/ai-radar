import unittest

from radar.discover import safe_extend
from radar.passive import Signal


class DiscoverReliabilityTests(unittest.TestCase):
    def test_failed_optional_source_does_not_abort_other_sources(self):
        signals, errors = [], []

        def broken():
            raise OSError("transient reset")

        safe_extend(signals, errors, "hacker-news", broken)
        safe_extend(signals, errors, "primary", lambda: [Signal("official-rss", "Agent update", "https://example.com", "")])

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].source, "official-rss")
        self.assertEqual(errors, [{"source": "hacker-news", "error": "OSError"}])


if __name__ == "__main__":
    unittest.main()
