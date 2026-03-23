"""测试核心数据模型。"""

import unittest
from pr_queue.models import PullRequest, Review, Config


class TestReview(unittest.TestCase):
    """Review 数据模型测试。"""

    def test_create_review(self):
        r = Review(reviewer="alice", state="approved", body="LGTM", submitted_at="2026-03-22T10:00:00Z")
        self.assertEqual(r.reviewer, "alice")
        self.assertEqual(r.state, "approved")

    def test_review_with_empty_body(self):
        r = Review(reviewer="bob", state="approved", body="", submitted_at="2026-03-22T10:00:00Z")
        self.assertEqual(r.body, "")


class TestPullRequest(unittest.TestCase):
    """PullRequest 数据模型测试。"""

    def _make_pr(self, **kwargs):
        defaults = {
            "number": 1, "title": "Fix bug", "author": "alice",
            "repo": "test/repo", "state": "open",
            "created_at": "2026-03-20T10:00:00Z",
            "updated_at": "2026-03-20T10:00:00Z",
        }
        defaults.update(kwargs)
        return PullRequest(**defaults)

    def test_create_pr(self):
        pr = self._make_pr()
        self.assertEqual(pr.number, 1)
        self.assertTrue(pr.is_open)

    def test_total_changed_lines(self):
        pr = self._make_pr(added_lines=100, deleted_lines=50)
        self.assertEqual(pr.total_changed_lines, 150)

    def test_is_open_false_when_closed(self):
        pr = self._make_pr(state="closed")
        self.assertFalse(pr.is_open)

    def test_is_open_true_when_merged(self):
        pr = self._make_pr(state="merged")
        self.assertFalse(pr.is_open)

    def test_to_dict_and_from_dict_roundtrip(self):
        pr = self._make_pr(
            added_lines=10, deleted_lines=5,
            changed_files=["src/a.py", "src/b.py"],
            reviewers=["alice", "bob"],
            labels=["bugfix"],
            reviews=[Review("bob", "approved", "LGTM", "2026-03-21T10:00:00Z")],
        )
        d = pr.to_dict()
        restored = PullRequest.from_dict(d)
        self.assertEqual(restored.number, 1)
        self.assertEqual(restored.title, "Fix bug")
        self.assertEqual(restored.added_lines, 10)
        self.assertEqual(restored.reviewers, ["alice", "bob"])
        self.assertEqual(len(restored.reviews), 1)
        self.assertEqual(restored.reviews[0].reviewer, "bob")

    def test_from_dict_with_defaults(self):
        d = {"number": 5, "title": "T", "author": "a", "repo": "r",
             "state": "open", "created_at": "2026-03-22T10:00:00Z",
             "updated_at": "2026-03-22T10:00:00Z"}
        pr = PullRequest.from_dict(d)
        self.assertEqual(pr.changed_files, [])
        self.assertEqual(pr.reviews, [])
        self.assertEqual(pr.added_lines, 0)

    def test_default_lists_are_independent(self):
        pr1 = self._make_pr()
        pr2 = self._make_pr()
        pr1.reviewers.append("alice")
        self.assertNotIn("alice", pr2.reviewers)


class TestConfig(unittest.TestCase):
    """Config 数据模型测试。"""

    def test_default_config(self):
        config = Config()
        self.assertEqual(config.timeout_hours, 24)
        self.assertIn("payment", config.high_risk_dirs)
        self.assertIn("LGTM", config.superficial_patterns)

    def test_config_to_dict_and_from_dict(self):
        config = Config(timeout_hours=48, webhook_url="https://example.com")
        d = config.to_dict()
        restored = Config.from_dict(d)
        self.assertEqual(restored.timeout_hours, 48)
        self.assertEqual(restored.webhook_url, "https://example.com")

    def test_from_dict_missing_fields_use_defaults(self):
        d = {"timeout_hours": 12}
        config = Config.from_dict(d)
        self.assertEqual(config.timeout_hours, 12)
        self.assertTrue(len(config.high_risk_dirs) > 0)
        self.assertEqual(config.webhook_url, "")


if __name__ == "__main__":
    unittest.main()
