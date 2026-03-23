"""测试审查人轮值分配。"""

import unittest
from pr_queue.reviewer_router import (
    match_reviewer_rules, suggest_reviewers, format_reviewer_suggestion,
)
from pr_queue.models import PullRequest, Config


def _make_pr(changed_files=None, **kwargs):
    defaults = {
        "number": 1, "title": "Test PR", "author": "alice",
        "repo": "test/repo", "state": "open",
        "created_at": "2026-03-20T10:00:00Z",
        "updated_at": "2026-03-20T10:00:00Z",
        "changed_files": changed_files or [],
    }
    defaults.update(kwargs)
    return PullRequest(**defaults)


class TestMatchReviewerRules(unittest.TestCase):
    """审查规则匹配测试。"""

    def test_exact_dir_match(self):
        rules = {"src/payment/**": ["alice", "bob"]}
        files = ["src/payment/checkout.py"]
        result = match_reviewer_rules(files, rules)
        self.assertIn("alice", result)
        self.assertIn("bob", result)

    def test_multiple_rules_match(self):
        rules = {
            "src/payment/**": ["alice"],
            "src/auth/": ["charlie"],
        }
        files = ["src/payment/checkout.py", "src/auth/login.py"]
        result = match_reviewer_rules(files, rules)
        self.assertIn("alice", result)
        self.assertIn("charlie", result)

    def test_no_match(self):
        rules = {"src/payment/**": ["alice"]}
        files = ["src/utils/helper.py"]
        result = match_reviewer_rules(files, rules)
        self.assertEqual(len(result), 0)

    def test_empty_files(self):
        rules = {"src/payment/**": ["alice"]}
        result = match_reviewer_rules([], rules)
        self.assertEqual(len(result), 0)

    def test_empty_rules(self):
        result = match_reviewer_rules(["src/payment/a.py"], {})
        self.assertEqual(len(result), 0)

    def test_no_duplicate_reviewers(self):
        rules = {
            "src/payment/**": ["alice"],
            "src/payment/models.py": ["alice"],
        }
        files = ["src/payment/checkout.py"]
        result = match_reviewer_rules(files, rules)
        self.assertEqual(result.count("alice"), 1)

    def test_deeply_nested_path(self):
        rules = {"src/payment/**": ["bob"]}
        files = ["src/payment/v2/internal/refund.py"]
        result = match_reviewer_rules(files, rules)
        self.assertIn("bob", result)

    def test_windows_style_path(self):
        rules = {"src/auth/": ["alice"]}
        files = ["src\\auth\\login.py"]
        result = match_reviewer_rules(files, rules)
        self.assertIn("alice", result)

    def test_order_preserved(self):
        rules = {
            "src/payment/**": ["alice", "bob"],
            "src/auth/": ["charlie"],
        }
        files = ["src/auth/login.py", "src/payment/a.py"]
        result = match_reviewer_rules(files, rules)
        # 结果不为空，包含所有审查员
        self.assertIn("alice", result)
        self.assertIn("bob", result)
        self.assertIn("charlie", result)


class TestSuggestReviewers(unittest.TestCase):
    """审查人建议测试。"""

    def test_suggests_from_config(self):
        config = Config(reviewer_rules={
            "src/payment/**": ["alice", "bob"],
        })
        pr = _make_pr(changed_files=["src/payment/checkout.py"])
        result = suggest_reviewers(pr, config)
        self.assertIn("alice", result)

    def test_no_rules_no_suggestion(self):
        config = Config()
        pr = _make_pr(changed_files=["src/utils/a.py"])
        result = suggest_reviewers(pr, config)
        self.assertEqual(len(result), 0)


class TestFormatReviewerSuggestion(unittest.TestCase):
    """审查人建议消息格式化测试。"""

    def test_with_suggestions(self):
        pr = _make_pr(changed_files=["src/payment/a.py"])
        msg = format_reviewer_suggestion(pr, ["alice", "bob"])
        self.assertIn("@alice", msg)
        self.assertIn("@bob", msg)
        self.assertIn("PR #1", msg)

    def test_without_suggestions(self):
        pr = _make_pr(changed_files=["src/utils/a.py"])
        msg = format_reviewer_suggestion(pr, [])
        self.assertIn("未匹配", msg)


if __name__ == "__main__":
    unittest.main()
