import unittest

from radar.inbox import parse_issue


class InboxTests(unittest.TestCase):
    def test_parse_shared_issue_with_note(self):
        issue = {
            "number": 12,
            "title": "[share] X post",
            "body": "https://x.com/example/status/123\n\nNote: compare this with agent memory work",
            "created_at": "2026-08-16T00:00:00Z",
            "html_url": "https://github.com/example/issues/12",
        }
        capture = parse_issue(issue)
        self.assertIsNotNone(capture)
        self.assertEqual(capture.url, "https://x.com/example/status/123")
        self.assertEqual(capture.note, "compare this with agent memory work")

    def test_non_share_issue_is_ignored(self):
        issue = {"number": 1, "title": "bug", "body": "https://example.com"}
        self.assertIsNone(parse_issue(issue))


if __name__ == "__main__":
    unittest.main()
